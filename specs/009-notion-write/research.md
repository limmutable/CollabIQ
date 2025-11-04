# Phase 2d - Notion Write Operations: Research Document

**Created**: 2025-11-03
**Status**: Phase 0 Research Complete
**Research Focus**: Notion API write operations, duplicate detection, DLQ patterns, field mapping, and retry logic

---

## 1. Notion API Write Operations Best Practices

### Decision

Use the `POST https://api.notion.com/v1/pages` endpoint to create pages in the CollabIQ database. Implement writes through a new `NotionWriter` class that:
- Extends the existing `NotionClient` pattern (rate limiting, error handling, retry logic)
- Formats extracted data (ExtractedEntitiesWithClassification) into Notion property format
- Validates field types before API calls
- Uses async/await for non-blocking operations

### Rationale

The existing codebase already has:
1. **NotionClient** with rate limiting (3 req/sec token bucket) and retry logic (tenacity with exponential backoff)
2. **Pydantic models** for data validation (ExtractedEntitiesWithClassification)
3. **Schema discovery** via NotionIntegrator (can fetch database schema for field type validation)

By following the established pattern, Phase 2d integrates seamlessly with existing infrastructure and reuses battle-tested error handling.

### Key API Characteristics

**Rate Limiting**:
- Official limit: Average of 3 requests per second
- Burst allowance: Occasional spikes above 3 req/sec are tolerated
- Response on limit: HTTP 429 with `Retry-After` header (milliseconds)
- **Already handled** by existing `RateLimiter` class (token bucket algorithm)

**Required Capabilities**:
- Integration must have "Insert Content" capabilities on target database
- Missing capability returns HTTP 403
- **Verified during setup** (database is already shared with integration)

**Parent Selection**:
- For database pages: `parent: {"database_id": "database_id_here"}`
- Properties must match parent database schema
- **Use existing schema discovery** to validate field types before write

**Auto-Generated Properties**:
- Notion generates: `created_time`, `created_by`, `last_edited_time`, `last_edited_by`, `rollup`
- Sending these in the request returns an error
- **Filter them out** during property formatting

### Alternatives Considered

1. **Use `pages.update()` for all operations**: Rejected because we need `pages.create()` for new entries. Update will be used only for duplicate handling (see Section 2).

2. **Batch writes with `pages.create_batch()`**: No such endpoint exists in Notion API. Must write pages one-by-one. However, we can process multiple emails concurrently using `asyncio.gather()` while respecting rate limits.

3. **Use templates for default values**: Not needed. All fields are provided by extraction pipeline. Templates add complexity without value for our use case.

### Code Examples

#### Basic Page Creation (Notion API Format)

```python
# Notion API expects this format
{
  "parent": {"database_id": "abc123"},
  "properties": {
    "담당자": {
      "rich_text": [
        {"text": {"content": "김주영"}}
      ]
    },
    "스타트업명": {
      "relation": [{"id": "startup-page-id"}]
    },
    "협업형태": {
      "select": {"name": "[A]PortCoXSSG"}
    },
    "날짜": {
      "date": {"start": "2025-10-28"}
    }
  }
}
```

#### Integration with Existing Client

```python
from notion_integrator import NotionClient
from notion_integrator.exceptions import NotionAPIError
from typing import Dict, Any

class NotionWriter:
    """Handles writing extracted email data to Notion databases."""

    def __init__(self, client: NotionClient):
        self.client = client

    async def create_page(
        self,
        database_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new page in a Notion database.

        Uses existing client infrastructure for:
        - Rate limiting (3 req/sec)
        - Error translation
        - Retry logic
        """
        # Rate limiting handled by client
        async with self.client.rate_limiter:
            try:
                response = await self._create_page_with_retry(
                    database_id=database_id,
                    properties=properties
                )
                return response
            except APIResponseError as e:
                raise self.client._translate_api_error(e, database_id=database_id)

    @retry(
        retry=retry_if_exception_type(APIResponseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _create_page_with_retry(
        self,
        database_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create page with retry logic (reuses existing pattern)."""
        return await self.client.client.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
```

---

## 2. Duplicate Detection Strategies

### Decision

Use **pre-write query** to check for duplicates by querying the CollabIQ database for existing entries with the same `email_id` field. If a duplicate exists, skip the write (log + continue) or update the existing page based on configuration.

### Rationale

**Why email_id as the primary duplicate key?**
- Email_id is unique per email (generated in Phase 1a duplicate tracker)
- Guaranteed to be present in all extracted data
- Avoids false positives from similar collaboration details

**Why query before write instead of catching errors?**
- Notion API doesn't enforce unique constraints (no built-in duplicate detection)
- Write succeeds even if duplicate data exists
- Pre-write query prevents actual duplicates from being created
- Performance impact is acceptable (1 extra API call per write, mitigated by rate limiting already in place)

**Why skip instead of update by default?**
- Extracted data doesn't change between processing runs (idempotent)
- Update logic adds complexity (merge strategies, conflict resolution)
- Skip is safer and simpler for Phase 2d (update can be added in Phase 2e if needed)

### Query Pattern

Notion API supports filtering by property values:

```python
{
  "filter": {
    "property": "email_id",  # Assuming email_id field exists in CollabIQ DB
    "rich_text": {
      "equals": "msg_abc123"
    }
  },
  "page_size": 1  # Only need to know if it exists
}
```

If `results` array is non-empty, duplicate exists.

### Performance Implications

**Cost per write**:
- 1 query API call (duplicate check)
- 1 create API call (if not duplicate)
- Total: 2 API calls per email (worst case)

**Rate limit impact**:
- At 3 req/sec: ~1.5 emails/sec (2 calls per email)
- For 100 emails: ~67 seconds (acceptable for Phase 2d)
- Can be optimized in Phase 2e with batch queries (query all email_ids at once, cache results)

**Optimization strategy**:
- Use `page_size=1` to minimize response payload
- Only fetch page ID (don't fetch all properties)
- Cache schema to avoid schema discovery on every write

### Alternatives Considered

1. **Generate unique ID from content hash**: Rejected because emails can be identical in content but represent different events (e.g., weekly updates with same format).

2. **Use compound key (startup + partner + date)**: Rejected because it creates false positives (two different emails about the same collaboration on the same day would be considered duplicates).

3. **No duplicate detection**: Rejected because reprocessing emails (common during development and debugging) would create duplicates.

4. **Database-level unique constraint**: Not supported by Notion API. Notion is a no-code tool, not a traditional database.

### Code Examples

```python
async def check_duplicate(
    self,
    database_id: str,
    email_id: str
) -> Optional[str]:
    """
    Check if an entry with the given email_id already exists.

    Returns:
        Page ID if duplicate exists, None otherwise
    """
    try:
        # Query for existing entry
        response = await self.client.query_database(
            database_id=database_id,
            filter_conditions={
                "property": "email_id",
                "rich_text": {"equals": email_id}
            },
            page_size=1
        )

        # Check if results exist
        results = response.get("results", [])
        if results:
            page_id = results[0]["id"]
            logger.info(
                "Duplicate entry found",
                extra={"email_id": email_id, "page_id": page_id}
            )
            return page_id

        return None

    except NotionAPIError as e:
        # Log error but don't fail the write
        logger.error(
            "Error checking for duplicate",
            extra={"email_id": email_id, "error": str(e)}
        )
        return None  # Assume no duplicate if query fails
```

---

## 3. Dead Letter Queue (DLQ) Patterns

### Decision

Implement a **simple file-based DLQ** that:
- Saves failed writes to `data/dlq/{email_id}_{timestamp}.json`
- Captures full context: extracted data (JSON), error details, timestamp
- Uses Pydantic models for serialization (ExtractedEntitiesWithClassification → JSON)
- Provides manual retry script (`scripts/retry_dlq.py`)

### Rationale

**Why file-based instead of queue service (SQS, Kafka)?**
- CollabIQ is a single-instance application (no distributed processing)
- File-based is simpler (no infrastructure dependencies)
- Easy to inspect failed records (JSON files are human-readable)
- Sufficient for Phase 2d volume (< 100 emails/day)
- Can migrate to queue service in Phase 2e if volume increases

**What context to capture?**
- **Full extracted data** (ExtractedEntitiesWithClassification as JSON)
- **Error details** (exception type, message, Notion API response if available)
- **Metadata** (email_id, timestamp, retry_count)
- **Original email content** (optional, for re-extraction if needed)

**Why manual retry instead of automatic?**
- Failed writes often indicate schema changes or permission issues
- Automatic retry without fixing root cause wastes API calls
- Manual review allows fixing the issue before retry (update schema, adjust field mapping)
- Simple for Phase 2d (can add automatic retry with alerting in Phase 2e)

### DLQ Structure

```
data/dlq/
├── msg_abc123_20251103_103045.json
├── msg_def456_20251103_103120.json
└── ...
```

Each file contains:

```json
{
  "email_id": "msg_abc123",
  "failed_at": "2025-11-03T10:30:45Z",
  "retry_count": 0,
  "error": {
    "type": "NotionAPIError",
    "message": "validation_error: body failed validation: body.properties...",
    "status_code": 400,
    "response_body": "{...}"
  },
  "extracted_data": {
    // Full ExtractedEntitiesWithClassification as JSON
    "person_in_charge": "김주영",
    "startup_name": "브레이크앤컴퍼니",
    // ... all fields
  }
}
```

### Pydantic Serialization

ExtractedEntitiesWithClassification already extends Pydantic BaseModel, so serialization is built-in:

```python
from src.llm_provider.types import ExtractedEntitiesWithClassification
import json

# Serialize to JSON
extracted_data = ExtractedEntitiesWithClassification(...)
json_str = extracted_data.model_dump_json(indent=2)

# Deserialize from JSON
extracted_data = ExtractedEntitiesWithClassification.model_validate_json(json_str)
```

### Alternatives Considered

1. **Store only email_id and retry later from original extraction files**: Rejected because extraction files may not exist if cleanup has run. DLQ should be self-contained.

2. **Use database (SQLite, PostgreSQL) for DLQ**: Rejected because it adds complexity without benefit. File-based is sufficient and easier to inspect.

3. **Automatic retry with exponential backoff**: Deferred to Phase 2e. Phase 2d focuses on capturing failures, not automatic recovery.

### Code Examples

#### DLQ Data Model

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
from src.llm_provider.types import ExtractedEntitiesWithClassification

class DLQEntry(BaseModel):
    """Dead letter queue entry for failed Notion writes."""

    email_id: str
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = 0
    error: Dict[str, Any]
    extracted_data: ExtractedEntitiesWithClassification
    original_email_content: Optional[str] = None  # Optional: for re-extraction

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

#### DLQ Writer

```python
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from src.llm_provider.types import ExtractedEntitiesWithClassification

class DLQManager:
    """Manages dead letter queue for failed Notion writes."""

    def __init__(self, dlq_dir: str = "data/dlq"):
        self.dlq_dir = Path(dlq_dir)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def save_to_dlq(
        self,
        extracted_data: ExtractedEntitiesWithClassification,
        error: Exception,
        original_email_content: Optional[str] = None
    ) -> Path:
        """
        Save failed write to DLQ.

        Args:
            extracted_data: Full extracted entity data
            error: Exception that caused the failure
            original_email_content: Optional original email text

        Returns:
            Path to the saved DLQ file
        """
        email_id = extracted_data.email_id
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{email_id}_{timestamp}.json"
        filepath = self.dlq_dir / filename

        # Build DLQ entry
        dlq_entry = DLQEntry(
            email_id=email_id,
            failed_at=datetime.utcnow(),
            retry_count=0,
            error={
                "type": type(error).__name__,
                "message": str(error),
                "status_code": getattr(error, "status_code", None),
                "response_body": getattr(error, "response_body", None),
            },
            extracted_data=extracted_data,
            original_email_content=original_email_content
        )

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(dlq_entry.model_dump_json(indent=2))

        logger.error(
            "Failed write saved to DLQ",
            extra={
                "email_id": email_id,
                "dlq_file": str(filepath),
                "error_type": type(error).__name__
            }
        )

        return filepath

    def list_failed_entries(self) -> list[Path]:
        """List all DLQ entries."""
        return sorted(self.dlq_dir.glob("*.json"))

    def load_entry(self, filepath: Path) -> DLQEntry:
        """Load a DLQ entry from file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return DLQEntry.model_validate_json(f.read())
```

#### Manual Retry Script (scripts/retry_dlq.py)

```python
#!/usr/bin/env python3
"""
Manual retry script for DLQ entries.

Usage:
    python scripts/retry_dlq.py --all
    python scripts/retry_dlq.py --file data/dlq/msg_abc123_20251103_103045.json
"""

import asyncio
import argparse
from pathlib import Path
from src.notion_writer import NotionWriter, DLQManager
from src.notion_integrator import NotionIntegrator

async def retry_entry(
    writer: NotionWriter,
    dlq_manager: DLQManager,
    filepath: Path
):
    """Retry a single DLQ entry."""
    entry = dlq_manager.load_entry(filepath)

    print(f"Retrying {entry.email_id}...")

    try:
        # Attempt write
        await writer.write_extraction_to_notion(
            database_id="...",
            extracted_data=entry.extracted_data
        )

        # Success - delete DLQ file
        filepath.unlink()
        print(f"✓ Success: {entry.email_id}")

    except Exception as e:
        print(f"✗ Failed again: {entry.email_id} - {e}")
        # Increment retry count
        entry.retry_count += 1
        # Save back to DLQ
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(entry.model_dump_json(indent=2))

async def main():
    parser = argparse.ArgumentParser(description="Retry DLQ entries")
    parser.add_argument("--all", action="store_true", help="Retry all entries")
    parser.add_argument("--file", type=str, help="Retry specific file")
    args = parser.parse_args()

    # Initialize services
    integrator = NotionIntegrator()
    writer = NotionWriter(integrator.client)
    dlq_manager = DLQManager()

    if args.all:
        entries = dlq_manager.list_failed_entries()
        print(f"Found {len(entries)} DLQ entries")
        for filepath in entries:
            await retry_entry(writer, dlq_manager, filepath)
    elif args.file:
        await retry_entry(writer, dlq_manager, Path(args.file))
    else:
        print("Use --all or --file <path>")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Field Mapping Best Practices

### Decision

Implement a **schema-aware field mapper** that:
1. Fetches database schema once per write session (using existing `discover_database_schema`)
2. Maps ExtractedEntitiesWithClassification fields to Notion property format based on property type
3. Handles optional/null fields gracefully (omit from properties dict instead of sending null)
4. Validates Korean text encoding (UTF-8) for rich_text fields

### Rationale

**Why schema-aware instead of hard-coded mapping?**
- Notion database schema can change (fields added/removed, types changed)
- Schema discovery already exists in Phase 2a (NotionIntegrator.discover_database_schema)
- Dynamic mapping prevents write failures when schema changes

**Why omit null fields instead of sending null values?**
- Notion API accepts missing properties (uses default values)
- Sending `null` for some property types causes validation errors
- Simpler to omit than to handle per-type null semantics

**Korean text (UTF-8) handling**:
- Python 3.12 strings are Unicode by default
- No special encoding needed for Korean text
- Notion API expects UTF-8 (default for JSON)
- Test with actual Korean text to verify (브레이크앤컴퍼니, 신세계푸드)

### Field Type Mapping

| Pydantic Field | Notion Property Type | Format | Example |
|---|---|---|---|
| `person_in_charge: str` | rich_text | `{"rich_text": [{"text": {"content": "김주영"}}]}` |담당자 |
| `startup_name: str` | title | `{"title": [{"text": {"content": "브레이크앤컴퍼니"}}]}` | 스타트업명 (if title) |
| `matched_company_id: str` | relation | `{"relation": [{"id": "page-id"}]}` | 스타트업명 (if relation) |
| `matched_partner_id: str` | relation | `{"relation": [{"id": "page-id"}]}` | 협업기관 |
| `collaboration_type: str` | select | `{"select": {"name": "[A]PortCoXSSG"}}` | 협업형태 |
| `collaboration_intensity: str` | select | `{"select": {"name": "협력"}}` | 협업강도 |
| `date: datetime` | date | `{"date": {"start": "2025-10-28"}}` | 날짜 |
| `details: str` | rich_text | `{"rich_text": [{"text": {"content": "..."}}]}` | 협업내용 |
| `collaboration_summary: str` | rich_text | `{"rich_text": [{"text": {"content": "..."}}]}` | 요약 |
| `confidence: ConfidenceScores` | number | `{"number": 0.95}` | If tracking confidence in Notion |

**Special Cases**:
- **협력주체** (collaboration subject): Database title field. System auto-generates "{startup_name}-{partner_org}" concatenation and sends as title property via API
- **email_id**: Rich text field for duplicate detection (hidden in Notion UI)

### Handling Relation Fields

Relation fields require **Notion page IDs** (32 or 36 character UUIDs):

```python
# If matched_company_id exists (Phase 2b matching succeeded)
if extracted_data.matched_company_id:
    properties["스타트업명"] = {
        "relation": [{"id": extracted_data.matched_company_id}]
    }
else:
    # Fallback: create as text or omit
    # Decision: omit and flag for manual review
    logger.warning(
        "No matched company ID, omitting startup relation",
        extra={"email_id": extracted_data.email_id}
    )
```

**Graceful degradation**:
- If company matching fails (matched_company_id is None), omit the relation field
- Mark the entry for manual review (add to review queue or tag in Notion)
- Don't fail the entire write due to missing relation

### Alternatives Considered

1. **Hard-coded field mapping**: Rejected because schema changes would break the system. Dynamic mapping is more robust.

2. **Send null for missing fields**: Rejected because Notion API validation is strict. Omitting fields is safer.

3. **Validate relation IDs before write**: Deferred to Phase 2e. Phase 2d trusts company matching results. If relation ID is invalid, Notion API returns error, write goes to DLQ.

### Code Examples

#### Schema-Aware Field Mapper

```python
from typing import Dict, Any, Optional
from src.llm_provider.types import ExtractedEntitiesWithClassification
from src.notion_integrator.models import DatabaseSchema

class FieldMapper:
    """Maps ExtractedEntitiesWithClassification to Notion property format."""

    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
        self.property_types = {
            prop.name: prop.type
            for prop in schema.database.properties.values()
        }

    def map_to_notion_properties(
        self,
        extracted_data: ExtractedEntitiesWithClassification
    ) -> Dict[str, Any]:
        """
        Map extracted data to Notion property format.

        Returns:
            Dictionary of Notion properties ready for API call
        """
        properties = {}

        # email_id (rich_text) - for duplicate detection
        if extracted_data.email_id:
            properties["email_id"] = self._format_rich_text(extracted_data.email_id)

        # 담당자 (person_in_charge) - rich_text
        if extracted_data.person_in_charge:
            properties["담당자"] = self._format_rich_text(extracted_data.person_in_charge)

        # 스타트업명 (matched_company_id) - relation
        if extracted_data.matched_company_id:
            properties["스타트업명"] = self._format_relation(extracted_data.matched_company_id)

        # 협업기관 (matched_partner_id) - relation
        if extracted_data.matched_partner_id:
            properties["협업기관"] = self._format_relation(extracted_data.matched_partner_id)

        # 협업형태 (collaboration_type) - select
        if extracted_data.collaboration_type:
            properties["협업형태"] = self._format_select(extracted_data.collaboration_type)

        # 협업강도 (collaboration_intensity) - select
        if extracted_data.collaboration_intensity:
            properties["협업강도"] = self._format_select(extracted_data.collaboration_intensity)

        # 날짜 (date) - date
        if extracted_data.date:
            properties["날짜"] = self._format_date(extracted_data.date)

        # 협업내용 (details) - rich_text
        if extracted_data.details:
            properties["협업내용"] = self._format_rich_text(extracted_data.details)

        # 요약 (collaboration_summary) - rich_text
        if extracted_data.collaboration_summary:
            properties["요약"] = self._format_rich_text(extracted_data.collaboration_summary)

        return properties

    def _format_rich_text(self, text: str) -> Dict[str, Any]:
        """Format text as Notion rich_text property."""
        # Truncate if too long (Notion limit: 2000 chars per rich_text block)
        if len(text) > 2000:
            text = text[:1997] + "..."

        return {
            "rich_text": [
                {
                    "text": {"content": text}
                }
            ]
        }

    def _format_select(self, value: str) -> Dict[str, Any]:
        """Format value as Notion select property."""
        return {
            "select": {"name": value}
        }

    def _format_relation(self, page_id: str) -> Dict[str, Any]:
        """Format page ID as Notion relation property."""
        return {
            "relation": [{"id": page_id}]
        }

    def _format_date(self, date: datetime) -> Dict[str, Any]:
        """Format datetime as Notion date property (ISO 8601)."""
        return {
            "date": {"start": date.strftime("%Y-%m-%d")}
        }
```

#### UTF-8 Korean Text Handling (Test)

```python
import pytest
from src.notion_writer.field_mapper import FieldMapper

def test_korean_text_encoding():
    """Test that Korean text is correctly encoded in rich_text format."""
    mapper = FieldMapper(schema=mock_schema)

    # Korean text
    korean_text = "브레이크앤컴퍼니와 신세계푸드가 AI 기반 재고 최적화 솔루션 PoC 킥오프"

    # Format as rich_text
    result = mapper._format_rich_text(korean_text)

    # Verify structure
    assert result == {
        "rich_text": [
            {
                "text": {"content": korean_text}
            }
        ]
    }

    # Verify JSON serialization (UTF-8)
    import json
    json_str = json.dumps(result, ensure_ascii=False)
    assert korean_text in json_str

    # Verify round-trip
    parsed = json.loads(json_str)
    assert parsed["rich_text"][0]["text"]["content"] == korean_text
```

---

## 5. Retry Logic for Phase 2d

### Decision

Implement a **simple 3-attempt retry pattern** for transient errors:
- Retry on specific error types: `APIResponseError` (Notion SDK exception)
- No delay between retries (immediate retry)
- After 3 failed attempts, save to DLQ and continue
- Use custom retry decorator (not tenacity) to avoid exponential backoff complexity

### Rationale

**Why 3 attempts?**
- Covers transient network issues (connection drops, timeouts)
- Balances recovery success vs API waste
- Consistent with existing NotionClient retry pattern (already uses 3 attempts)

**Why no delay (exponential backoff)?**
- NotionClient already has rate limiting (token bucket), which prevents bursts
- Write operations are idempotent (retrying immediately is safe)
- Simplifies implementation (no asyncio.sleep management)
- If error persists after 3 immediate retries, it's likely not transient (schema error, permission issue) → send to DLQ

**When to retry vs when to send to DLQ?**

| Error Type | Action | Reason |
|---|---|---|
| Network timeout (500, 502, 503) | Retry 3x | Transient |
| Rate limit (429) | Retry 3x | Transient (rate limiter should prevent this) |
| Validation error (400) | DLQ immediately | Schema mismatch, not transient |
| Permission error (403) | DLQ immediately | Access issue, not transient |
| Not found (404) | DLQ immediately | Database doesn't exist, not transient |

**Why custom retry decorator instead of tenacity?**
- Existing codebase uses tenacity for NotionClient (exponential backoff for reads)
- Write operations have different requirements (immediate retry, simpler logic)
- Custom decorator gives full control over error handling and DLQ integration
- Avoids mixing retry strategies (tenacity for reads, custom for writes)

### Alternatives Considered

1. **Use tenacity with exponential backoff**: Rejected because writes don't benefit from exponential backoff (rate limiter already controls burst). Adds unnecessary complexity.

2. **Retry all errors**: Rejected because non-transient errors (validation, permission) waste API calls. Send to DLQ for manual review.

3. **No retry, send directly to DLQ**: Rejected because transient network errors should be retried automatically.

### Code Examples

#### Simple Retry Decorator (No Backoff)

```python
import asyncio
from functools import wraps
from typing import Callable, Type, Tuple
from notion_client.errors import APIResponseError

def simple_retry(
    max_attempts: int = 3,
    retry_on: Tuple[Type[Exception], ...] = (APIResponseError,)
):
    """
    Simple retry decorator for async functions.

    Retries immediately without delay (no exponential backoff).
    Suitable for write operations where rate limiting is already applied.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        retry_on: Tuple of exception types to retry on
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    # Don't retry on non-transient errors
                    if hasattr(e, 'status') and e.status in (400, 403, 404):
                        # Validation, permission, not found → don't retry
                        raise

                    if attempt == max_attempts:
                        # Last attempt failed
                        raise

                    # Log retry
                    logger.warning(
                        f"Retry attempt {attempt}/{max_attempts}",
                        extra={
                            "function": func.__name__,
                            "error": str(e),
                            "attempt": attempt
                        }
                    )

                    # No delay - immediate retry
                    continue

            # Should never reach here
            raise last_exception

        return wrapper
    return decorator
```

#### Integration with NotionWriter

```python
class NotionWriter:
    """Handles writing extracted email data to Notion databases."""

    def __init__(self, client: NotionClient, dlq_manager: DLQManager):
        self.client = client
        self.dlq = dlq_manager

    async def write_extraction_to_notion(
        self,
        database_id: str,
        extracted_data: ExtractedEntitiesWithClassification,
        skip_duplicate: bool = True
    ) -> Optional[str]:
        """
        Write extracted data to Notion database.

        Args:
            database_id: Notion database ID
            extracted_data: Full extracted entity data
            skip_duplicate: If True, skip write if duplicate exists

        Returns:
            Page ID if created, None if skipped (duplicate)
        """
        try:
            # Check for duplicate
            if skip_duplicate:
                existing_page_id = await self.check_duplicate(
                    database_id=database_id,
                    email_id=extracted_data.email_id
                )
                if existing_page_id:
                    logger.info(
                        "Skipping duplicate",
                        extra={
                            "email_id": extracted_data.email_id,
                            "existing_page_id": existing_page_id
                        }
                    )
                    return None

            # Map fields to Notion format
            properties = self.field_mapper.map_to_notion_properties(extracted_data)

            # Create page (with retry)
            page = await self._create_page_with_retry(
                database_id=database_id,
                properties=properties
            )

            page_id = page["id"]
            logger.info(
                "Write successful",
                extra={
                    "email_id": extracted_data.email_id,
                    "page_id": page_id
                }
            )

            return page_id

        except Exception as e:
            # All retries failed or non-retryable error
            logger.error(
                "Write failed, saving to DLQ",
                extra={
                    "email_id": extracted_data.email_id,
                    "error": str(e)
                }
            )

            # Save to DLQ
            self.dlq.save_to_dlq(
                extracted_data=extracted_data,
                error=e
            )

            # Don't re-raise - continue processing other emails
            return None

    @simple_retry(max_attempts=3)
    async def _create_page_with_retry(
        self,
        database_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create page with simple retry logic (no backoff).

        Retries 3 times immediately on transient errors.
        Raises immediately on non-transient errors (validation, permission).
        """
        # Rate limiting handled by client
        async with self.client.rate_limiter:
            return await self.client.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
```

#### Error Classification

```python
def is_transient_error(error: APIResponseError) -> bool:
    """
    Determine if an error is transient (should retry) or permanent (send to DLQ).

    Transient errors:
    - 429 (rate limit)
    - 500, 502, 503 (server errors)
    - Connection timeouts

    Permanent errors:
    - 400 (validation error)
    - 403 (permission error)
    - 404 (not found)
    """
    if not hasattr(error, 'status'):
        # Unknown error - assume transient
        return True

    status = error.status

    # Transient errors
    if status in (429, 500, 502, 503):
        return True

    # Permanent errors
    if status in (400, 403, 404):
        return False

    # Default: assume transient
    return True
```

---

## Summary of Decisions

| Component | Decision | Key Points |
|---|---|---|
| **Write Operations** | Use `POST /pages` with NotionWriter class | Reuses existing rate limiting, error handling, retry infrastructure |
| **Duplicate Detection** | Pre-write query by email_id | 1 extra API call per write, skip duplicates by default |
| **Dead Letter Queue** | File-based JSON storage in `data/dlq/` | Simple, human-readable, Pydantic serialization, manual retry script |
| **Field Mapping** | Schema-aware mapper with UTF-8 support | Dynamic based on schema discovery, omit null fields, graceful degradation |
| **Retry Logic** | 3 immediate retries for transient errors | No backoff (rate limiter already controls burst), send to DLQ after failures |

---

## Next Steps (Implementation Phase)

1. **Create data models** (Phase 1):
   - `DLQEntry` (Pydantic model for DLQ storage)
   - `WriteResult` (return type for write operations)

2. **Implement core classes** (Phase 2):
   - `FieldMapper` (schema-aware field mapping)
   - `DLQManager` (file-based DLQ operations)
   - `NotionWriter` (orchestrates write + duplicate check + DLQ)

3. **Add retry decorator** (Phase 3):
   - `simple_retry` decorator (3 attempts, no backoff)
   - Error classification logic (transient vs permanent)

4. **Write integration tests** (Phase 4):
   - Test with real Notion API (CollabIQ database)
   - Test Korean text encoding
   - Test duplicate detection
   - Test DLQ capture

5. **Create manual retry script** (Phase 5):
   - `scripts/retry_dlq.py` (manual retry for DLQ entries)
   - CLI interface (--all, --file)

6. **Update documentation** (Phase 6):
   - Update CLAUDE.md with Phase 2d technologies
   - Update README with DLQ retry instructions

---

## References

- [Notion API - Create a page](https://developers.notion.com/reference/post-page)
- [Notion API - Query a database](https://developers.notion.com/reference/post-database-query)
- [Notion API - Property objects](https://developers.notion.com/reference/property-object)
- [Notion API - Rich text](https://developers.notion.com/reference/rich-text)
- [Tenacity - Python retry library](https://tenacity.readthedocs.io/)
- [Pydantic v2 - Data validation](https://docs.pydantic.dev/latest/)

---

**End of Research Document**
