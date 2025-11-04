# Quickstart: Notion Write Operations (Phase 2d)

**Feature**: Phase 2d - Notion Write Operations
**Created**: 2025-11-03
**Status**: Phase 1 Design

---

## Overview

This quickstart guide walks you through using Phase 2d Notion Write Operations to create CollabIQ database entries from extracted email data. You'll learn how to write entries, handle duplicates, manage errors, and retry failed writes.

**What Phase 2d Does**:
- Writes extracted email data to Notion CollabIQ database
- Detects and skips duplicate entries (based on email_id)
- Maps Pydantic model fields to Notion property format (Korean field names)
- Handles errors with Dead Letter Queue (DLQ) for manual retry
- Preserves Korean text encoding throughout the pipeline

---

## Prerequisites

Before starting, ensure you have:

1. **Phase 2a Complete**: Notion Read Operations (schema discovery, database access)
2. **Phase 2b Complete**: Company Matching (matched company IDs available)
3. **Phase 2c Complete**: Classification & Summarization (classification data available)
4. **Notion API Write Permissions**: Integration must have "Insert Content" capability on CollabIQ database
5. **Environment Variables Set**:
   - `NOTION_TOKEN`: Notion integration token
   - `COLLABIQ_DB_ID`: CollabIQ database ID
   - `GEMINI_API_KEY`: Gemini API key (from Phase 2c)

### Verify Prerequisites

```bash
# Check environment variables
echo $NOTION_TOKEN
echo $COLLABIQ_DB_ID
echo $GEMINI_API_KEY

# Verify CollabIQ database access
uv run python tests/manual/test_phase2a_notion_read.py
```

---

## 1. Installation

Phase 2d uses existing dependencies from Phase 2a/2b/2c. No new packages required.

```bash
# Ensure all dependencies are installed
cd /Users/jlim/Projects/CollabIQ
uv sync

# Verify Notion client is available
uv run python -c "from src.notion_integrator import NotionIntegrator; print('✓ Notion client available')"
```

---

## 2. Configuration

### Environment Variables

Add these to your `.env` file (or set in environment):

```bash
# Required (should already be set from Phase 2a/2b/2c)
NOTION_TOKEN=secret_...
COLLABIQ_DB_ID=abc123def456ghi789jkl012mno345pq
GEMINI_API_KEY=...

# Optional (Phase 2d specific)
DUPLICATE_BEHAVIOR=skip  # "skip" or "update" (default: "skip")
DLQ_DIR=data/dlq         # Dead letter queue directory (default: "data/dlq")
```

### Database Schema Verification

Verify that the CollabIQ database has all required fields:

```python
from src.notion_integrator import NotionIntegrator
import os

integrator = NotionIntegrator()
schema = await integrator.discover_database_schema(os.getenv("COLLABIQ_DB_ID"))

# Check for required fields
required_fields = ["email_id", "담당자", "스타트업명", "협업기관", "협업형태", "협업강도", "요약", "날짜"]
for field in required_fields:
    if field in schema.property_names:
        print(f"✓ {field}")
    else:
        print(f"✗ {field} - MISSING!")
```

---

## 3. Basic Usage

### Write a Single Email to Notion

The simplest use case: write one extracted email to Notion.

```python
#!/usr/bin/env python3
"""Basic example: Write a single email to Notion."""

import asyncio
import os
from src.notion_integrator import NotionIntegrator
from src.notion_writer import NotionWriter
from src.llm_provider.types import ExtractedEntitiesWithClassification

async def main():
    # Initialize services
    integrator = NotionIntegrator()
    writer = NotionWriter(client=integrator.client)

    # Load extracted data (from Phase 2c)
    # In production, this comes from your extraction pipeline
    extracted_data = ExtractedEntitiesWithClassification(
        email_id="msg_001",
        person_in_charge="김주영",
        startup_name="브레이크앤컴퍼니",
        partner_org="신세계푸드",
        details="AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅",
        date="2025-10-28T00:00:00Z",
        confidence={
            "person": 0.95,
            "startup": 0.92,
            "partner": 0.88,
            "details": 0.90,
            "date": 0.85
        },
        matched_company_id="abc123def456ghi789jkl012mno345pq",
        matched_partner_id="xyz789uvw012abc345def678ghi901jk",
        collaboration_type="[A]PortCoXSSG",
        collaboration_intensity="협력",
        type_confidence=0.95,
        intensity_confidence=0.88,
        collaboration_summary="브레이크앤컴퍼니와 신세계푸드가 AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅을 진행했습니다."
    )

    # Write to Notion
    result = await writer.create_collabiq_entry(
        database_id=os.getenv("COLLABIQ_DB_ID"),
        extracted_data=extracted_data
    )

    # Check result
    if result.success:
        print(f"✓ Created entry: {result.page_id}")
        print(f"  View in Notion: https://notion.so/{result.page_id}")
    elif result.is_duplicate:
        print(f"⊙ Duplicate detected, skipped: {result.email_id}")
        print(f"  Existing entry: {result.existing_page_id}")
    else:
        print(f"✗ Write failed: {result.error_message}")
        print(f"  Error type: {result.error_type}")
        print(f"  Check DLQ: data/dlq/{result.email_id}_*.json")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run**:
```bash
uv run python tests/manual/test_phase2d_write_basic.py
```

**Expected Output**:
```
✓ Created entry: abc123def456ghi789jkl012mno345pq
  View in Notion: https://notion.so/abc123def456ghi789jkl012mno345pq
```

---

## 4. Duplicate Handling

### Configure Skip vs Update Behavior

By default, Phase 2d **skips** duplicate entries (same `email_id`). You can configure update behavior:

#### Option 1: Environment Variable (Global)

```bash
# Set in .env or environment
DUPLICATE_BEHAVIOR=skip   # Skip duplicates (default)
DUPLICATE_BEHAVIOR=update # Update existing entries
```

#### Option 2: Per-Write Override

```python
# Override per write operation
result = await writer.create_collabiq_entry(
    database_id=os.getenv("COLLABIQ_DB_ID"),
    extracted_data=extracted_data,
    duplicate_behavior="update"  # Override default
)
```

### Check for Duplicates Manually

```python
# Check if email already exists in Notion
page_id = await writer.check_duplicate(
    database_id=os.getenv("COLLABIQ_DB_ID"),
    email_id="msg_001"
)

if page_id:
    print(f"Duplicate found: {page_id}")
else:
    print("No duplicate, safe to create")
```

### Duplicate Detection Logic

Phase 2d uses `email_id` (from Phase 1a duplicate tracker) as the unique key:

1. Before write: Query Notion database for existing entry with same `email_id`
2. If found: Skip write (or update if configured)
3. If not found: Create new entry

**Why email_id?**
- Guaranteed unique per email
- Avoids false positives from similar collaboration details
- Prevents duplicates when emails are reprocessed (testing, errors)

---

## 5. Error Handling

### Understanding the Dead Letter Queue (DLQ)

When a write operation fails (API error, validation error, network timeout), Phase 2d automatically saves the failed write to a **Dead Letter Queue (DLQ)** for manual review and retry.

**DLQ Location**: `data/dlq/`

**DLQ File Format**: `{email_id}_{timestamp}.json`

**Example DLQ File**:
```json
{
  "email_id": "msg_001",
  "failed_at": "2025-11-03T14:30:52Z",
  "retry_count": 0,
  "error": {
    "type": "APIResponseError",
    "message": "validation_error: body.properties.협업형태.select.name: '[A]PortCoXSSG' does not exist in select options",
    "status_code": 400,
    "response_body": "{...}"
  },
  "extracted_data": {
    "person_in_charge": "김주영",
    "startup_name": "브레이크앤컴퍼니",
    ...
  }
}
```

### Check DLQ for Failed Writes

```python
from src.notion_writer.dlq_manager import DLQManager

# Initialize DLQ manager
dlq = DLQManager()

# List all failed writes
dlq_files = dlq.list_failed_writes()
print(f"Found {len(dlq_files)} failed writes")

for filepath in dlq_files:
    entry = dlq.load_entry(filepath)
    print(f"\nEmail ID: {entry.email_id}")
    print(f"Failed at: {entry.failed_at}")
    print(f"Error: {entry.error['message']}")
    print(f"Retry count: {entry.retry_count}")
```

### Common Error Types

| Error Type | Status Code | Cause | Action |
|------------|-------------|-------|--------|
| `validation_error` | 400 | Schema mismatch, invalid field value | Fix schema or field mapping |
| `unauthorized` | 403 | Missing write permissions | Grant integration "Insert Content" capability |
| `object_not_found` | 404 | Database doesn't exist | Verify `COLLABIQ_DB_ID` is correct |
| `rate_limited` | 429 | Too many requests | Wait and retry (handled automatically) |
| `internal_server_error` | 500 | Notion API error | Retry (handled automatically) |

### Automatic Retry Logic

Phase 2d retries transient errors (429, 500, 502, 503) **3 times** automatically before saving to DLQ:

- **Retry 1**: Immediate retry
- **Retry 2**: Immediate retry
- **Retry 3**: Immediate retry
- **After 3 failures**: Save to DLQ for manual review

**Non-transient errors** (400, 403, 404) are **not retried** and go directly to DLQ.

---

## 6. Retry Failed Writes

### Manual Retry (Command Line)

Use the provided retry script to manually retry failed writes:

```bash
# Retry all DLQ entries
python scripts/retry_dlq.py --all

# Retry specific file
python scripts/retry_dlq.py --file data/dlq/msg_001_20251103_143052.json

# Show DLQ statistics
python scripts/retry_dlq.py --stats

# List DLQ entries without retrying
python scripts/retry_dlq.py --list
```

**Example Output**:
```
Retrying DLQ entries...
  ✓ msg_001_20251103_143052.json - Success
  ✗ msg_002_20251103_150230.json - Failed: validation_error
  ✓ msg_003_20251103_151500.json - Success

Summary:
  Total: 3
  Success: 2
  Failed: 1
```

### Manual Retry (Python)

```python
from src.notion_writer.dlq_manager import DLQManager
from src.notion_writer import NotionWriter
from src.notion_integrator import NotionIntegrator
import os
from pathlib import Path

async def retry_dlq():
    # Initialize services
    integrator = NotionIntegrator()
    writer = NotionWriter(client=integrator.client)
    dlq = DLQManager()

    # Retry a specific DLQ entry
    dlq_file = Path("data/dlq/msg_001_20251103_143052.json")

    result = await dlq.retry_failed_write(
        filepath=dlq_file,
        writer=writer,
        database_id=os.getenv("COLLABIQ_DB_ID")
    )

    if result.success:
        print(f"✓ Retry succeeded: {result.page_id}")
        # DLQ file automatically deleted on success
    else:
        print(f"✗ Retry failed: {result.error_message}")
        # DLQ file updated with incremented retry_count
```

### Batch Retry All Failed Writes

```python
async def retry_all_dlq():
    integrator = NotionIntegrator()
    writer = NotionWriter(client=integrator.client)
    dlq = DLQManager()

    dlq_files = dlq.list_failed_writes()
    print(f"Found {len(dlq_files)} failed writes")

    for filepath in dlq_files:
        result = await dlq.retry_failed_write(
            filepath=filepath,
            writer=writer,
            database_id=os.getenv("COLLABIQ_DB_ID")
        )

        if result.success:
            print(f"✓ {filepath.name}")
        else:
            print(f"✗ {filepath.name}: {result.error_message}")
```

---

## 7. Testing

### Run Integration Tests

Phase 2d includes integration tests that verify:
- Write operations with real Notion API
- Duplicate detection
- Korean text encoding preservation
- DLQ capture on errors
- Relation field linking (company IDs)

```bash
# Run Phase 2d integration tests
uv run pytest tests/integration/test_notion_write.py -v

# Run with coverage
uv run pytest tests/integration/test_notion_write.py --cov=src.notion_writer --cov-report=html
```

### Manual Testing Script

Use the provided manual test script (similar to Phase 2c pattern):

```bash
# Run Phase 2d manual test
uv run python tests/manual/test_phase2d_notion_write.py
```

**What the test does**:
1. Loads sample email from `tests/fixtures/sample_emails/sample-001.txt`
2. Extracts entities (Phase 1b)
3. Matches companies (Phase 2b)
4. Classifies and summarizes (Phase 2c)
5. Writes to Notion (Phase 2d)
6. Verifies entry created successfully
7. Tests duplicate detection (second write)

**Expected Output**:
```
===============================================================================
Phase 2d: Notion Write Operations - Demo Script
===============================================================================

Step 1: Loading dependencies...
✓ Environment variables loaded

Step 2: Initializing services...
✓ NotionIntegrator initialized
✓ NotionWriter initialized
✓ DLQManager initialized

Step 3: Loading sample email...
✓ Loaded sample email: sample-001.txt

Step 4: Running full extraction pipeline...
✓ Entities extracted
✓ Companies matched
✓ Classification complete

Step 5: Writing to Notion...
✓ Write successful
  Page ID: abc123def456ghi789jkl012mno345pq
  View in Notion: https://notion.so/abc123def456ghi789jkl012mno345pq

Step 6: Testing duplicate detection...
⊙ Duplicate detected, skipped (as expected)
  Existing entry: abc123def456ghi789jkl012mno345pq

===============================================================================
DEMO COMPLETE
===============================================================================

✓ Phase 2d write operations completed successfully!

Key Features Demonstrated:
  1. Schema-aware field mapping (Pydantic → Notion properties)
  2. Korean text encoding preservation (UTF-8)
  3. Duplicate detection (email_id based)
  4. Relation field linking (company IDs)
  5. Error handling with DLQ capture

Next Steps:
  - Review the created entry in Notion
  - Test with your own email samples
  - Integrate into your email processing pipeline (Phase 3a)
```

### Test with Real Email Data

```bash
# Test with real emails from Phase 1a/1b
uv run python scripts/test_phase2d_real_emails.py
```

This script:
1. Loads processed emails from `data/extractions/`
2. Filters for emails with Phase 2c classification complete
3. Writes each to Notion (skips duplicates)
4. Reports summary (success/duplicate/error counts)

---

## 8. Troubleshooting

### Problem: Write fails with "unauthorized" (403)

**Cause**: Notion integration lacks write permissions.

**Solution**:
1. Go to Notion → Settings → Integrations
2. Find your integration
3. Check "Insert Content" capability is enabled
4. Re-share CollabIQ database with integration

### Problem: Write fails with "validation_error" (400)

**Cause**: Field value doesn't match database schema (e.g., select option doesn't exist).

**Solution**:
1. Check DLQ file for error details: `data/dlq/{email_id}_*.json`
2. Look at `error.message` for specific field causing error
3. Verify select options in Notion database match classification values
4. Update schema or fix classification logic

**Example**:
```
"error": {
  "message": "validation_error: body.properties.협업형태.select.name: '[A]PortCoXSSG' does not exist in select options"
}
```

**Action**: Add "[A]PortCoXSSG" to the "협업형태" select field in Notion.

### Problem: Korean text appears corrupted

**Cause**: Encoding issue in JSON serialization.

**Solution**:
Phase 2d uses UTF-8 by default. Verify:
1. Python 3.12+ is being used (UTF-8 default)
2. JSON serialization uses `ensure_ascii=False`
3. Notion field type is `rich_text` (not `title` for most fields)

**Test encoding**:
```python
import json
from src.notion_writer.field_mapper import FieldMapper

korean_text = "브레이크앤컴퍼니"
formatted = mapper._format_rich_text(korean_text)

# Should output Korean characters, not \uXXXX escapes
json_str = json.dumps(formatted, ensure_ascii=False)
print(json_str)  # Should contain actual Korean characters
```

### Problem: Duplicate detection not working

**Cause**: `email_id` field missing or not unique.

**Solution**:
1. Verify `email_id` is present in extracted data: `print(extracted_data.email_id)`
2. Check email_id field exists in Notion database (rich_text type)
3. Verify email_id is being written to Notion: check created entry

**Debug**:
```python
# Check if duplicate detection is working
page_id = await writer.check_duplicate(
    database_id=os.getenv("COLLABIQ_DB_ID"),
    email_id="msg_001"
)
print(f"Duplicate check result: {page_id}")  # Should return page_id if exists
```

### Problem: Relation fields not linking

**Cause**: Invalid company ID or company page doesn't exist.

**Solution**:
1. Verify company IDs are 32 or 36 characters (Notion page ID format)
2. Check company pages exist in Companies database
3. Test relation link manually in Notion UI

**Debug**:
```python
# Verify company IDs
print(f"Startup ID: {extracted_data.matched_company_id}")
print(f"Partner ID: {extracted_data.matched_partner_id}")

# Check length (should be 32 or 36)
if extracted_data.matched_company_id:
    print(f"ID length: {len(extracted_data.matched_company_id)}")
```

### Problem: DLQ file saved but no error visible

**Cause**: Error was caught and logged, but not raised.

**Solution**:
Check logs for error details:
```bash
# Check logs for error messages
grep "Write failed" logs/collabiq.log

# Or check DLQ file directly
cat data/dlq/{email_id}_*.json | jq '.error'
```

---

## 9. Production Deployment

### End-to-End Pipeline Integration

Integrate Phase 2d into your full email processing pipeline:

```python
async def process_email_pipeline(email_content: str, email_id: str):
    """Full pipeline: extraction → matching → classification → write."""

    # Phase 1b: Extract entities
    extracted = await extractor.extract_entities(email_content, email_id)

    # Phase 2b: Match companies
    matched = await matcher.match_companies(extracted)

    # Phase 2c: Classify and summarize
    classified = await classifier.classify_and_summarize(matched)

    # Phase 2d: Write to Notion
    result = await writer.create_collabiq_entry(
        database_id=os.getenv("COLLABIQ_DB_ID"),
        extracted_data=classified
    )

    return result
```

### Monitoring and Alerting

Monitor DLQ for failed writes:

```python
# Check DLQ stats periodically
dlq = DLQManager()
stats = dlq.get_stats()

if stats['total_entries'] > 0:
    print(f"⚠️  {stats['total_entries']} failed writes in DLQ")
    print(f"Oldest failure: {stats['oldest_entry']}")
    # Send alert (email, Slack, etc.)
```

### Performance Optimization

Phase 2d is rate-limited to **1.5 emails/sec** (due to duplicate check + write = 2 API calls per email, 3 req/sec limit).

**For batch processing**:
```python
# Process emails in parallel (respecting rate limit)
import asyncio

emails = load_emails()  # List[ExtractedEntitiesWithClassification]

# Process with rate limiting (handled by NotionClient)
results = await asyncio.gather(*[
    writer.create_collabiq_entry(
        database_id=os.getenv("COLLABIQ_DB_ID"),
        extracted_data=email_data
    )
    for email_data in emails
])

# Summary
success_count = sum(1 for r in results if r.success)
print(f"Processed {len(results)} emails, {success_count} successful")
```

---

## 10. Next Steps

### Phase 2e: Enhanced Retry Logic (Coming Soon)

Phase 2d provides basic retry (3 immediate attempts) and file-based DLQ. Phase 2e will add:
- Exponential backoff for retries
- Scheduled automatic retry (cron-based)
- DLQ processing with priority queue
- Rate limit detection and adaptive backoff
- Monitoring dashboard for DLQ metrics

### Phase 3a: Async Queue-Based Processing (Coming Soon)

Phase 2d uses synchronous writes (blocking). Phase 3a will add:
- Async queue for write operations (Celery, Redis Queue)
- Background worker for processing queue
- Webhook notifications for write confirmations
- Bulk write operations (batch multiple emails)

---

## Reference

### Key Files

- **NotionWriter**: `/Users/jlim/Projects/CollabIQ/src/notion_writer/notion_writer.py`
- **FieldMapper**: `/Users/jlim/Projects/CollabIQ/src/notion_writer/field_mapper.py`
- **DLQManager**: `/Users/jlim/Projects/CollabIQ/src/notion_writer/dlq_manager.py`
- **DLQ Directory**: `/Users/jlim/Projects/CollabIQ/data/dlq/`
- **Manual Test**: `/Users/jlim/Projects/CollabIQ/tests/manual/test_phase2d_notion_write.py`
- **Retry Script**: `/Users/jlim/Projects/CollabIQ/scripts/retry_dlq.py`

### Documentation

- [Data Model](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/data-model.md)
- [NotionWriter Contract](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/contracts/notion_writer_contract.md)
- [FieldMapper Contract](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/contracts/field_mapper_contract.md)
- [DLQManager Contract](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/contracts/dlq_manager_contract.md)
- [Phase 2d Spec](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/spec.md)
- [Phase 2d Research](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/research.md)

### API References

- [Notion API - Create Page](https://developers.notion.com/reference/post-page)
- [Notion API - Property Objects](https://developers.notion.com/reference/property-object)
- [Notion API - Query Database](https://developers.notion.com/reference/post-database-query)

---

**Need Help?**

- Check [Troubleshooting](#8-troubleshooting) section above
- Review DLQ files for error details: `data/dlq/`
- Check logs: `logs/collabiq.log`
- Run manual test: `uv run python tests/manual/test_phase2d_notion_write.py`
