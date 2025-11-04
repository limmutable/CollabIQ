# Contract: NotionWriter

**Feature**: Phase 2d - Notion Write Operations
**Created**: 2025-11-03
**Status**: Phase 1 Design

---

## Overview

The `NotionWriter` interface defines the contract for writing extracted email data to Notion databases with duplicate detection, field mapping, error handling, and DLQ management.

---

## Interface Definition

### Class: NotionWriter

**Purpose**: Orchestrates write operations to Notion CollabIQ database with full error handling and retry logic.

**Dependencies**:
- `NotionClient`: Existing Notion API client (from Phase 2a) with rate limiting and error translation
- `DLQManager`: Dead letter queue manager for failed writes
- `FieldMapper`: Schema-aware field mapping service
- `DatabaseSchema`: Notion database schema (cached from Phase 2a discovery)

**Initialization**:
```python
class NotionWriter:
    """Handles writing extracted email data to Notion databases."""

    def __init__(
        self,
        client: NotionClient,
        dlq_manager: Optional[DLQManager] = None,
        duplicate_behavior: str = "skip"
    ):
        """
        Initialize NotionWriter.

        Args:
            client: NotionClient instance with rate limiting
            dlq_manager: DLQ manager for failed writes (default: auto-created)
            duplicate_behavior: "skip" or "update" (default: "skip")

        Raises:
            ValueError: If duplicate_behavior not in ["skip", "update"]
        """
```

---

## Core Methods

### 1. create_collabiq_entry()

**Purpose**: Create a new CollabIQ database entry with extracted and classified data.

**Signature**:
```python
async def create_collabiq_entry(
    self,
    database_id: str,
    extracted_data: ExtractedEntitiesWithClassification,
    duplicate_behavior: Optional[str] = None
) -> WriteResult:
    """
    Create a new entry in the CollabIQ database.

    This is the primary public method for Phase 2d write operations.
    Orchestrates the full write workflow:
    1. Check for duplicates (based on email_id)
    2. Map fields to Notion format (schema-aware)
    3. Create page via Notion API (with retry)
    4. Validate response and return result
    5. On failure: save to DLQ and return error result

    Args:
        database_id: Notion database ID (CollabIQ database)
        extracted_data: Full extracted entity data with classification
        duplicate_behavior: Override default behavior ("skip" or "update")

    Returns:
        WriteResult with success status, page_id, or error details

    Raises:
        ValueError: If database_id is invalid or extracted_data is incomplete
        NotionAPIError: Only if critical unrecoverable error (shouldn't happen)

    Example:
        >>> writer = NotionWriter(client)
        >>> result = await writer.create_collabiq_entry(
        ...     database_id="abc123def456",
        ...     extracted_data=extracted_entities_with_classification
        ... )
        >>> if result.success:
        ...     print(f"Created page: {result.page_id}")
        ... else:
        ...     print(f"Failed: {result.error_message}")
    """
```

**Input Validation**:
- `database_id`: Non-empty string, 32 or 36 characters (Notion database ID format)
- `extracted_data.email_id`: Must be present (required for duplicate detection)
- `duplicate_behavior`: If provided, must be "skip" or "update"

**Output Types**:

**Success** (new entry created):
```python
WriteResult(
    success=True,
    page_id="abc123def456ghi789jkl012mno345pq",
    email_id="msg_001",
    error_type=None,
    error_message=None,
    status_code=None,
    retry_count=0,
    is_duplicate=False,
    existing_page_id=None
)
```

**Duplicate (skipped)**:
```python
WriteResult(
    success=False,
    page_id=None,
    email_id="msg_001",
    error_type=None,
    error_message="Duplicate entry found, skipping",
    status_code=None,
    retry_count=0,
    is_duplicate=True,
    existing_page_id="xyz789uvw012abc345def678ghi901jk"
)
```

**Error (saved to DLQ)**:
```python
WriteResult(
    success=False,
    page_id=None,
    email_id="msg_001",
    error_type="APIResponseError",
    error_message="validation_error: body.properties.협업형태...",
    status_code=400,
    retry_count=3,
    is_duplicate=False,
    existing_page_id=None
)
```

**Error Conditions**:
- **Duplicate Detected** (behavior="skip"): Returns WriteResult with `is_duplicate=True`, logs skip action
- **Notion API Error** (400/403/404): Saves to DLQ, returns WriteResult with error details
- **Transient Error** (429/500/502/503): Retries 3x, then saves to DLQ if all retries fail
- **Network Timeout**: Retries 3x, then saves to DLQ if all retries fail
- **Invalid Field Format**: Saves to DLQ with validation error details

**Side Effects**:
- Creates new page in Notion database (if not duplicate)
- Writes DLQ file to `data/dlq/` (if error occurs)
- Logs info/warning/error messages to structured logger
- Increments rate limiter token bucket counter

**Performance Expectations**:
- Duplicate check: ~500ms (1 database query)
- Field mapping: <10ms (in-memory operation)
- API call: ~1000ms (network + Notion processing)
- Total: <2 seconds per email (target: SC-005 from spec)

---

### 2. check_duplicate()

**Purpose**: Query Notion database for existing entry with same email_id.

**Signature**:
```python
async def check_duplicate(
    self,
    database_id: str,
    email_id: str
) -> Optional[str]:
    """
    Check if an entry with the given email_id already exists.

    Uses Notion database query API to search for matching email_id.
    This is a lightweight query (page_size=1, only fetch page ID).

    Args:
        database_id: Notion database ID to query
        email_id: Email identifier to check (from Phase 1a)

    Returns:
        Notion page ID if duplicate exists, None otherwise

    Raises:
        ValueError: If database_id or email_id is empty
        NotionAPIError: If query fails (logged but doesn't raise)

    Example:
        >>> page_id = await writer.check_duplicate(
        ...     database_id="abc123def456",
        ...     email_id="msg_001"
        ... )
        >>> if page_id:
        ...     print(f"Duplicate found: {page_id}")
        ... else:
        ...     print("No duplicate, safe to create")
    """
```

**Input Validation**:
- `database_id`: Non-empty string
- `email_id`: Non-empty string

**Output Types**:
- `str`: Notion page ID (32 or 36 characters) if duplicate exists
- `None`: No duplicate found

**Query Format** (Notion API):
```python
{
    "filter": {
        "property": "email_id",
        "rich_text": {
            "equals": email_id
        }
    },
    "page_size": 1  # Only need to know if exists
}
```

**Error Conditions**:
- **Query Fails**: Logs error, returns None (assume no duplicate, safer to attempt write)
- **Multiple Results**: Takes first result (should never happen if email_id is unique)

**Side Effects**:
- Logs duplicate detection result (info level)
- Increments rate limiter token bucket counter

**Performance Expectations**:
- Query time: ~500ms (Notion API query)
- Total: <1 second

---

### 3. _build_properties()

**Purpose**: Map ExtractedEntitiesWithClassification fields to Notion property format.

**Signature**:
```python
def _build_properties(
    self,
    extracted_data: ExtractedEntitiesWithClassification
) -> Dict[str, Any]:
    """
    Build Notion properties dict from extracted data.

    Uses FieldMapper to dynamically format fields based on database schema.
    Handles null fields by omission (don't send to Notion API).
    Truncates long text fields to 2000 characters (Notion limit).

    Args:
        extracted_data: Full extracted entity data

    Returns:
        Dictionary of Notion properties in API format

    Raises:
        ValueError: If required field (email_id) is missing

    Example:
        >>> properties = writer._build_properties(extracted_data)
        >>> print(properties.keys())
        dict_keys(['email_id', '담당자', '스타트업명', '협업기관', ...])
    """
```

**Input Validation**:
- `extracted_data.email_id`: Must be present (required field)

**Output Format**:
```python
{
    "email_id": {
        "rich_text": [{"text": {"content": "msg_001"}}]
    },
    "담당자": {
        "rich_text": [{"text": {"content": "김주영"}}]
    },
    "스타트업명": {
        "relation": [{"id": "abc123def456ghi789jkl012mno345pq"}]
    },
    "협업기관": {
        "relation": [{"id": "xyz789uvw012abc345def678ghi901jk"}]
    },
    "협업형태": {
        "select": {"name": "[A]PortCoXSSG"}
    },
    "협업강도": {
        "select": {"name": "협력"}
    },
    "날짜": {
        "date": {"start": "2025-10-28"}
    },
    "협업내용": {
        "rich_text": [{"text": {"content": "AI 기반 재고 최적화..."}}]
    },
    "요약": {
        "rich_text": [{"text": {"content": "브레이크앤컴퍼니와..."}}]
    },
    "타입신뢰도": {
        "number": 0.95
    },
    "강도신뢰도": {
        "number": 0.88
    }
}
```

**Field Mapping Rules**:

| Source Field | Notion Property | Type | Handling |
|--------------|-----------------|------|----------|
| `email_id` | email_id | rich_text | Required, always included |
| `person_in_charge` | 담당자 | rich_text | Optional, omit if None |
| `matched_company_id` | 스타트업명 | relation | Optional, omit if None |
| `matched_partner_id` | 협업기관 | relation | Optional, omit if None |
| `details` | 협업내용 | rich_text | Optional, truncate if >2000 chars |
| `date` | 날짜 | date | Optional, format as ISO 8601 |
| `collaboration_type` | 협업형태 | select | Optional, omit if None |
| `collaboration_intensity` | 협업강도 | select | Optional, omit if None |
| `collaboration_summary` | 요약 | rich_text | Optional, truncate if >2000 chars |
| `type_confidence` | 타입신뢰도 | number | Optional, omit if None |
| `intensity_confidence` | 강도신뢰도 | number | Optional, omit if None |

**Special Handling**:
- **Null Fields**: Omit from properties dict (don't send `null` or empty string)
- **Long Text**: Truncate to 1997 chars + "..." if exceeds 2000 chars
- **Invalid Relation IDs**: Log warning, omit field (graceful degradation)
- **Korean Text**: No special encoding needed (UTF-8 by default)

**Error Conditions**:
- **Missing email_id**: Raises ValueError
- **Invalid Notion ID Format**: Logs warning, omits field

**Side Effects**:
- Logs warnings for omitted fields (debug level)

**Performance Expectations**:
- Mapping time: <10ms (in-memory operation)

---

## Private/Internal Methods

### 4. _create_page_with_retry()

**Purpose**: Create page via Notion API with simple retry logic (3 attempts).

**Signature**:
```python
@simple_retry(max_attempts=3)
async def _create_page_with_retry(
    self,
    database_id: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create page with retry logic (3 immediate retries).

    Decorated with @simple_retry for automatic retry on transient errors.
    Does NOT retry on non-transient errors (400/403/404).

    Args:
        database_id: Notion database ID
        properties: Notion properties dict (pre-formatted)

    Returns:
        Notion API response (page object)

    Raises:
        APIResponseError: If all 3 attempts fail or non-transient error
    """
```

**Retry Strategy**:
- **Max Attempts**: 3 (including initial attempt)
- **Backoff**: None (immediate retry)
- **Retry On**: Transient errors only (429, 500, 502, 503, network timeouts)
- **No Retry On**: Validation/permission errors (400, 403, 404)

**Error Classification**:

| Status Code | Error Type | Action |
|-------------|------------|--------|
| 400 | Validation Error | Don't retry, save to DLQ |
| 403 | Permission Error | Don't retry, save to DLQ |
| 404 | Not Found | Don't retry, save to DLQ |
| 429 | Rate Limit | Retry 3x (shouldn't happen due to rate limiter) |
| 500 | Server Error | Retry 3x |
| 502 | Bad Gateway | Retry 3x |
| 503 | Service Unavailable | Retry 3x |
| Timeout | Network Timeout | Retry 3x |

**Rate Limiting**:
```python
async with self.client.rate_limiter:
    response = await self.client.client.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )
```

**Side Effects**:
- Logs retry attempts (warning level)
- Increments rate limiter token bucket counter on each attempt

---

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NOTION_TOKEN` | str | Required | Notion integration token |
| `COLLABIQ_DB_ID` | str | Required | CollabIQ database ID |
| `DUPLICATE_BEHAVIOR` | str | "skip" | "skip" or "update" |
| `DLQ_DIR` | str | "data/dlq" | Dead letter queue directory |

### Constructor Parameters

```python
NotionWriter(
    client: NotionClient,           # Required: Notion API client
    dlq_manager: Optional[DLQManager] = None,  # Optional: auto-created if None
    duplicate_behavior: str = "skip"  # Optional: "skip" or "update"
)
```

---

## Usage Examples

### Basic Usage

```python
from src.notion_integrator import NotionIntegrator
from src.notion_writer import NotionWriter
from src.llm_provider.types import ExtractedEntitiesWithClassification

# Initialize services
integrator = NotionIntegrator()
writer = NotionWriter(client=integrator.client)

# Write extracted data to Notion
extracted_data = ExtractedEntitiesWithClassification(...)
result = await writer.create_collabiq_entry(
    database_id=os.getenv("COLLABIQ_DB_ID"),
    extracted_data=extracted_data
)

if result.success:
    print(f"✓ Created entry: {result.page_id}")
else:
    print(f"✗ Failed: {result.error_message}")
```

### Batch Processing

```python
# Process multiple emails
emails = load_emails()  # List[ExtractedEntitiesWithClassification]

results = []
for email_data in emails:
    result = await writer.create_collabiq_entry(
        database_id=os.getenv("COLLABIQ_DB_ID"),
        extracted_data=email_data
    )
    results.append(result)

# Summary
success_count = sum(1 for r in results if r.success)
duplicate_count = sum(1 for r in results if r.is_duplicate)
error_count = len(results) - success_count - duplicate_count

print(f"Success: {success_count}, Duplicates: {duplicate_count}, Errors: {error_count}")
```

### Custom Duplicate Behavior

```python
# Override default behavior to update existing entries
writer = NotionWriter(
    client=integrator.client,
    duplicate_behavior="update"  # Update instead of skip
)

result = await writer.create_collabiq_entry(
    database_id=os.getenv("COLLABIQ_DB_ID"),
    extracted_data=extracted_data
)
```

### Error Handling

```python
try:
    result = await writer.create_collabiq_entry(
        database_id=os.getenv("COLLABIQ_DB_ID"),
        extracted_data=extracted_data
    )

    if result.success:
        logger.info(f"Created page {result.page_id}")
    elif result.is_duplicate:
        logger.info(f"Skipped duplicate {result.email_id}")
    else:
        logger.error(
            f"Write failed: {result.error_message}",
            extra={
                "email_id": result.email_id,
                "error_type": result.error_type,
                "status_code": result.status_code,
                "retry_count": result.retry_count
            }
        )
        # DLQ file already created automatically
        print(f"Check DLQ for details: data/dlq/{result.email_id}_*.json")

except ValueError as e:
    logger.error(f"Invalid input: {e}")
    # Handle validation error
```

---

## Testing Contract

### Unit Tests Required

1. **Field Mapping**:
   - Test all field types map correctly
   - Test null field omission
   - Test long text truncation (>2000 chars)
   - Test Korean text preservation

2. **Duplicate Detection**:
   - Test query construction
   - Test result parsing (existing page found)
   - Test no results (no duplicate)
   - Test error handling (query fails)

3. **Error Classification**:
   - Test transient error detection (429, 500, 502, 503)
   - Test non-transient error detection (400, 403, 404)
   - Test retry behavior (retry vs immediate DLQ)

### Integration Tests Required

1. **Full Write Workflow**:
   - Test creating new entry with all fields
   - Test duplicate skip behavior
   - Test DLQ capture on API error
   - Test rate limiting (multiple writes)

2. **Korean Text Encoding**:
   - Test Korean text in all rich_text fields
   - Test UTF-8 round-trip (write → read back)

3. **Relation Field Linking**:
   - Test valid company ID linking
   - Test invalid company ID handling (graceful degradation)

---

## Performance Guarantees

- **Single Write**: <2 seconds (including duplicate check)
- **Batch Write**: 1.5 emails/sec (limited by rate limiter: 3 req/sec, 2 calls per email)
- **Memory Usage**: <10MB per write operation (Pydantic model + API response)

---

## Backward Compatibility

- **ExtractedEntities** (Phase 1b): Supported, classification fields optional
- **ExtractedEntitiesWithClassification** (Phase 2c): Full support
- New optional fields: Will be automatically omitted if not present (dynamic mapping)

---

## Security Considerations

- **Notion Token**: Must have "Insert Content" capability on database
- **Sensitive Data**: Email content not stored in Notion (only extracted entities)
- **DLQ Files**: May contain sensitive data, secure file permissions recommended
- **Logging**: Sanitize log output (no full email content, no API tokens)

---

## Dependencies

- `notion-client>=2.0.0`: Official Notion Python SDK
- `pydantic>=2.0.0`: Data validation and serialization
- `tenacity>=8.0.0`: Retry logic (used by NotionClient)
- Python 3.12+: Required for modern async/await syntax

---

## References

- [Data Model](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/data-model.md)
- [NotionClient Contract](/Users/jlim/Projects/CollabIQ/src/notion_integrator/client.py)
- [ExtractedEntitiesWithClassification Model](/Users/jlim/Projects/CollabIQ/src/llm_provider/types.py)
- [Notion API - Create Page](https://developers.notion.com/reference/post-page)
