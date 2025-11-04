# Data Model: Notion Write Operations (Phase 2d)

**Feature**: Phase 2d - Notion Write Operations
**Created**: 2025-11-03
**Status**: Phase 1 Design

---

## Overview

This document defines the entities and data models used in Phase 2d for writing extracted email data to Notion databases. All models extend existing Phase 2a/2b/2c patterns and maintain backward compatibility.

---

## Core Entities

### 1. NotionCollabIQEntry

**Purpose**: Represents a single collaboration record in the Notion CollabIQ database with Korean field names mapped to English concepts.

**Description**: The CollabIQ database entry is the primary output of the entire pipeline (extraction → matching → classification → summarization → write). Each entry corresponds to one email and contains all extracted entities, matched company relations, and classification results.

**Fields**:

| Field Name (Korean) | Field Name (English) | Type | Source | Constraints | Description |
|---------------------|---------------------|------|--------|-------------|-------------|
| email_id | email_id | rich_text | Phase 1a | Required, unique | Unique email identifier for duplicate detection |
| 담당자 | person_in_charge | rich_text | Phase 1b | Optional | Person responsible for collaboration |
| 스타트업명 | startup_name | relation | Phase 2b | Optional | Relation to Companies database (startup) |
| 협업기관 | partner_org | relation | Phase 2b | Optional | Relation to Companies database (partner) |
| 협력주체 | collaboration_subject | title | Phase 2d | Required (title field) | Concatenated: "{startup_name}-{partner_org}" |
| 협업내용 | details | rich_text | Phase 1b | Optional, max 2000 chars | Original collaboration description |
| 날짜 | date | date | Phase 1b | Optional | Collaboration date (ISO 8601) |
| 협업형태 | collaboration_type | select | Phase 2c | Optional | Type classification (e.g., "[A]PortCoXSSG") |
| 협업강도 | collaboration_intensity | select | Phase 2c | Optional | Intensity: 이해, 협력, 투자, 인수 |
| 요약 | collaboration_summary | rich_text | Phase 2c | Optional, max 750 chars | 3-5 sentence summary |
| 타입신뢰도 | type_confidence | number | Phase 2c | Optional, 0.0-1.0 | Type classification confidence |
| 강도신뢰도 | intensity_confidence | number | Phase 2c | Optional, 0.0-1.0 | Intensity classification confidence |
| 검토필요 | needs_manual_review | checkbox | Computed | Auto-calculated | True if confidence < 0.85 threshold |
| 분류일시 | classification_timestamp | date | Phase 2c | Optional | When classification occurred |

**Relationships**:
- **Many-to-One** with Companies database (via 스타트업명 relation field)
- **Many-to-One** with Companies database (via 협업기관 relation field)
- **One-to-One** with original email (via email_id reference)

**Validation Rules**:
- `email_id`: Must be non-empty, used for duplicate detection
- `스타트업명`, `협업기관`: If provided, must be valid 32 or 36 character Notion page IDs
- `협업형태`: If provided, must match format `[X].*` where X is a letter/number
- `협업강도`: If provided, must be one of: 이해, 협력, 투자, 인수
- `타입신뢰도`, `강도신뢰도`: If provided, must be 0.0-1.0
- Rich text fields: Max 2000 characters per block (Notion API limit)

**State Transitions**:
1. **Non-existent** → **Created**: Write operation creates new entry
2. **Created** → **Updated**: Duplicate detection with update behavior (optional in Phase 2d)
3. **Created** → **Manually Edited**: User edits entry in Notion (tracked by `last_edited_time`)

**Special Handling**:
- **협력주체** (collaboration_subject): Database title field. System auto-generates value by concatenating startup name + partner org with hyphen separator. Sent via API using title format: `{"title": [{"text": {"content": "startup-partner"}}]}`
- **검토필요** (needs_manual_review): Computed field based on confidence thresholds, can be implemented as formula or checkbox

---

### 2. WriteResult

**Purpose**: The return value from write operations indicating success/failure status.

**Description**: Provides structured feedback from Notion write operations for logging, error handling, and DLQ management.

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| success | bool | Required | Whether write operation succeeded |
| page_id | Optional[str] | 32 or 36 chars if present | Notion page ID if created successfully |
| email_id | str | Required | Email identifier for tracking |
| error_type | Optional[str] | None if success=True | Exception class name if failed |
| error_message | Optional[str] | None if success=True | Human-readable error message |
| status_code | Optional[int] | None if success=True | HTTP status code from Notion API |
| retry_count | int | Default: 0, max: 3 | Number of retry attempts made |
| is_duplicate | bool | Default: False | Whether write was skipped due to duplicate |
| existing_page_id | Optional[str] | Present if is_duplicate=True | Page ID of existing duplicate entry |

**Relationships**:
- **One-to-One** with extracted email data (via `email_id`)
- **One-to-One** with Notion page (via `page_id` if success=True)
- **One-to-One** with DLQ entry (via `email_id` if success=False)

**Validation Rules**:
- If `success=True`: `page_id` must be present, error fields must be None
- If `success=False`: `error_type` and `error_message` must be present
- If `is_duplicate=True`: `existing_page_id` must be present
- `retry_count`: Must be 0-3 (Phase 2d retry limit)

**State Transitions**:
1. **Initial attempt** (retry_count=0)
2. **Retry attempt** (retry_count=1-2)
3. **Final attempt** (retry_count=3) → **Success** or **Failure**

**Example Usage**:
```python
# Success case
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

# Duplicate case
WriteResult(
    success=False,
    page_id=None,
    email_id="msg_001",
    error_type=None,
    error_message="Duplicate entry found",
    status_code=None,
    retry_count=0,
    is_duplicate=True,
    existing_page_id="xyz789uvw012abc345def678ghi901jk"
)

# Error case
WriteResult(
    success=False,
    page_id=None,
    email_id="msg_001",
    error_type="APIResponseError",
    error_message="validation_error: body.properties.협업형태.select.name: Invalid value",
    status_code=400,
    retry_count=3,
    is_duplicate=False,
    existing_page_id=None
)
```

---

### 3. DLQEntry

**Purpose**: Dead letter queue record for failed writes requiring manual intervention or retry.

**Description**: Captures full context of failed write operations for debugging, retry, or manual data recovery. Stored as JSON files in `data/dlq/` directory.

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| email_id | str | Required | Email identifier for reference |
| failed_at | datetime | Required, UTC | When the write operation failed |
| retry_count | int | Default: 0 | Number of automatic retries attempted (0 in Phase 2d) |
| error | dict | Required | Error details (type, message, status, response) |
| extracted_data | ExtractedEntitiesWithClassification | Required | Full extracted entity data as Pydantic model |
| original_email_content | Optional[str] | Optional | Original email text for re-extraction if needed |
| dlq_file_path | Optional[str] | Set on save | Path to DLQ JSON file |

**Error Field Structure**:
```python
{
    "type": str,              # Exception class name (e.g., "APIResponseError")
    "message": str,           # Human-readable error message
    "status_code": Optional[int],  # HTTP status code if available
    "response_body": Optional[str] # Full Notion API response if available
}
```

**Relationships**:
- **One-to-One** with original email (via `email_id`)
- **One-to-One** with ExtractedEntitiesWithClassification (embedded)
- **One-to-One** with DLQ file on disk (via `dlq_file_path`)

**Validation Rules**:
- `email_id`: Must match `extracted_data.email_id`
- `failed_at`: Must be valid UTC datetime
- `retry_count`: Must be >= 0 (incremented on each manual retry)
- `error.type`: Must be non-empty exception class name
- `extracted_data`: Must be valid ExtractedEntitiesWithClassification model

**State Transitions**:
1. **Created**: Write operation fails, DLQ entry created
2. **Retry Pending**: Entry exists in DLQ, awaiting manual retry
3. **Retry Attempted**: Manual retry script processes entry
4. **Resolved (Success)**: Retry succeeds, DLQ file deleted
5. **Resolved (Abandoned)**: Entry archived or manually removed

**File Naming Convention**:
```
data/dlq/{email_id}_{timestamp}.json
```
Example: `data/dlq/msg_abc123_20251103_143052.json`

**Serialization**:
Uses Pydantic `model_dump_json()` for automatic JSON serialization:
- UTF-8 encoding for Korean text
- ISO 8601 datetime formatting
- Pretty-printed (indent=2) for human readability

**Example DLQ File**:
```json
{
  "email_id": "msg_abc123",
  "failed_at": "2025-11-03T14:30:52Z",
  "retry_count": 0,
  "error": {
    "type": "APIResponseError",
    "message": "validation_error: body.properties.협업형태.select.name: '[A]PortCoXSSG' does not exist in select options",
    "status_code": 400,
    "response_body": "{\"object\":\"error\",\"status\":400,\"code\":\"validation_error\",\"message\":\"...\"}"
  },
  "extracted_data": {
    "person_in_charge": "김주영",
    "startup_name": "브레이크앤컴퍼니",
    "partner_org": "신세계푸드",
    "details": "AI 기반 재고 최적화 솔루션 PoC 킥오프",
    "date": "2025-10-28T00:00:00Z",
    "confidence": {
      "person": 0.95,
      "startup": 0.92,
      "partner": 0.88,
      "details": 0.90,
      "date": 0.85
    },
    "email_id": "msg_abc123",
    "extracted_at": "2025-11-03T10:30:00Z",
    "matched_company_id": "abc123def456ghi789jkl012mno345pq",
    "matched_partner_id": "xyz789uvw012abc345def678ghi901jk",
    "collaboration_type": "[A]PortCoXSSG",
    "collaboration_intensity": "협력",
    "type_confidence": 0.95,
    "intensity_confidence": 0.88,
    "collaboration_summary": "브레이크앤컴퍼니와 신세계푸드가 AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅을 진행했습니다.",
    "summary_word_count": 42,
    "classification_timestamp": "2025-11-03T10:30:00Z"
  },
  "original_email_content": null,
  "dlq_file_path": "data/dlq/msg_abc123_20251103_143052.json"
}
```

---

### 4. FieldMapping

**Purpose**: Internal representation mapping Pydantic model fields to Notion property format.

**Description**: Schema-aware mapping layer that dynamically formats ExtractedEntitiesWithClassification fields into Notion API property format based on database schema.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| source_field | str | Pydantic model field name (e.g., "person_in_charge") |
| notion_property_name | str | Notion property name (e.g., "담당자") |
| notion_property_type | str | Notion property type (e.g., "rich_text", "relation", "select") |
| formatter_function | Callable | Function to format value for Notion API |
| is_required | bool | Whether field is required for write operation |
| fallback_value | Optional[Any] | Default value if source field is None |

**Relationships**:
- **Many-to-One** with DatabaseSchema (field mappings belong to a schema)
- **One-to-One** with Pydantic field (source_field)
- **One-to-One** with Notion property (notion_property_name)

**Validation Rules**:
- `source_field`: Must exist in ExtractedEntitiesWithClassification model
- `notion_property_name`: Must exist in database schema (validated at runtime)
- `notion_property_type`: Must be valid Notion property type
- `formatter_function`: Must accept source value and return Notion property format

**Format Functions**:

| Notion Type | Format Function | Output Example |
|-------------|-----------------|----------------|
| rich_text | `_format_rich_text(text: str)` | `{"rich_text": [{"text": {"content": "..."}}]}` |
| select | `_format_select(value: str)` | `{"select": {"name": "협력"}}` |
| relation | `_format_relation(page_id: str)` | `{"relation": [{"id": "abc123..."}]}` |
| date | `_format_date(dt: datetime)` | `{"date": {"start": "2025-10-28"}}` |
| number | `_format_number(num: float)` | `{"number": 0.95}` |

**Built-in Mappings**:

```python
FIELD_MAPPINGS = [
    FieldMapping(
        source_field="email_id",
        notion_property_name="email_id",
        notion_property_type="rich_text",
        formatter_function=_format_rich_text,
        is_required=True,
        fallback_value=None
    ),
    FieldMapping(
        source_field="person_in_charge",
        notion_property_name="담당자",
        notion_property_type="rich_text",
        formatter_function=_format_rich_text,
        is_required=False,
        fallback_value=None
    ),
    FieldMapping(
        source_field="matched_company_id",
        notion_property_name="스타트업명",
        notion_property_type="relation",
        formatter_function=_format_relation,
        is_required=False,
        fallback_value=None
    ),
    # ... additional mappings
]
```

**State Transitions**:
1. **Schema Discovered**: Database schema fetched from Notion
2. **Mappings Created**: FieldMapping instances created based on schema
3. **Value Formatted**: Source field value formatted for Notion API
4. **Validation Applied**: Output validated against schema constraints

**Special Cases**:
- **Null Handling**: If source field is None, omit from properties dict (don't send to Notion)
- **Text Truncation**: Rich text fields truncated to 2000 chars (Notion API limit)
- **Relation Validation**: Relation IDs validated as 32 or 36 character UUIDs
- **Korean Text**: UTF-8 encoding preserved throughout formatting

---

## Data Flow

```
ExtractedEntitiesWithClassification (Pydantic model)
    ↓
FieldMapper (schema-aware mapping)
    ↓
Notion Properties Dict (API format)
    ↓
NotionWriter.create_page() (API call)
    ↓
WriteResult (success/failure)
    ↓ (if failure)
DLQEntry (saved to data/dlq/)
```

---

## Schema Evolution

**Adding New Fields**:
1. Add field to `ExtractedEntitiesWithClassification` model (optional for backward compatibility)
2. Add corresponding Notion property to database schema (optional fields only)
3. Add FieldMapping to `FIELD_MAPPINGS` list
4. No code changes required if field is optional (dynamic mapping handles it)

**Changing Field Types**:
1. Update Notion property type in database (requires database migration)
2. Update `notion_property_type` and `formatter_function` in FieldMapping
3. Test with existing extraction data to ensure compatibility
4. Consider fallback logic for old data format

**Removing Fields**:
1. Mark field as deprecated in Pydantic model (keep for backward compatibility)
2. Remove from `FIELD_MAPPINGS` (field will be omitted from writes)
3. Notion property can remain in database (no data loss)

---

## Error Handling Patterns

**Missing Required Fields**:
```python
if extracted_data.email_id is None:
    raise ValueError("email_id is required for write operation")
```

**Invalid Relation IDs**:
```python
if matched_company_id and len(matched_company_id) not in (32, 36):
    logger.warning(f"Invalid company ID format: {matched_company_id}, omitting from write")
    matched_company_id = None  # Graceful degradation
```

**Korean Text Encoding**:
```python
# No special handling needed - Python 3.12 uses UTF-8 by default
# JSON serialization with ensure_ascii=False preserves Korean characters
```

**Notion API Errors**:
- **400 (Validation)**: Save to DLQ, log error details (schema mismatch)
- **403 (Permission)**: Save to DLQ, log error (integration lacks write access)
- **404 (Not Found)**: Save to DLQ, log error (database doesn't exist)
- **429 (Rate Limit)**: Retry with backoff (handled by NotionClient rate limiter)
- **500/502/503 (Server)**: Retry 3x, then save to DLQ

---

## Testing Considerations

**Unit Tests**:
- Field mapping validation (all Pydantic fields → Notion properties)
- Format function correctness (each Notion property type)
- Korean text encoding preservation (UTF-8 round-trip)
- Null handling (omit fields, don't send empty strings)

**Integration Tests**:
- Write operation with full extraction data
- Duplicate detection (same email_id)
- DLQ capture on API errors
- Relation field linking (valid Notion page IDs)

**Edge Cases**:
- Very long text fields (truncation at 2000 chars)
- Missing optional fields (graceful omission)
- Invalid relation IDs (graceful degradation)
- Special characters in Korean text (emojis, punctuation)

---

## References

- [ExtractedEntitiesWithClassification Model](/Users/jlim/Projects/CollabIQ/src/llm_provider/types.py)
- [Notion API Property Objects](https://developers.notion.com/reference/property-object)
- [Pydantic BaseModel](https://docs.pydantic.dev/latest/api/base_model/)
- [Phase 2d Spec](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/spec.md)
