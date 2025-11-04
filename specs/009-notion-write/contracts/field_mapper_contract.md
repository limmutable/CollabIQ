# Contract: FieldMapper

**Feature**: Phase 2d - Notion Write Operations
**Created**: 2025-11-03
**Status**: Phase 1 Design

---

## Overview

The `FieldMapper` interface defines the contract for mapping ExtractedEntitiesWithClassification Pydantic model fields to Notion property format. Provides schema-aware type conversion, null handling, and validation.

---

## Interface Definition

### Class: FieldMapper

**Purpose**: Schema-aware field mapping service that converts Pydantic model fields to Notion API property format.

**Dependencies**:
- `DatabaseSchema`: Notion database schema (from Phase 2a discovery)
- `ExtractedEntitiesWithClassification`: Source data model

**Initialization**:
```python
class FieldMapper:
    """Maps ExtractedEntitiesWithClassification to Notion property format."""

    def __init__(self, schema: DatabaseSchema):
        """
        Initialize FieldMapper with database schema.

        Args:
            schema: Notion database schema with property types

        Raises:
            ValueError: If schema is invalid or missing required properties
        """
```

---

## Core Methods

### 1. map_to_notion_properties()

**Purpose**: Map full ExtractedEntitiesWithClassification object to Notion properties dict.

**Signature**:
```python
def map_to_notion_properties(
    self,
    extracted_data: ExtractedEntitiesWithClassification
) -> Dict[str, Any]:
    """
    Map extracted data to Notion property format.

    Orchestrates field-by-field mapping using schema-aware formatters.
    Handles null fields by omission (returns dict without null entries).
    Validates Korean text encoding (UTF-8).

    Args:
        extracted_data: Full extracted entity data with classification

    Returns:
        Dictionary of Notion properties in API format

    Raises:
        ValueError: If email_id is missing (required field)
        TypeError: If field value doesn't match expected type

    Example:
        >>> mapper = FieldMapper(schema)
        >>> properties = mapper.map_to_notion_properties(extracted_data)
        >>> print(properties.keys())
        dict_keys(['email_id', '담당자', '스타트업명', ...])
    """
```

**Input Validation**:
- `extracted_data.email_id`: Must be present (required for duplicate detection)
- `extracted_data`: Must be valid ExtractedEntitiesWithClassification instance

**Output Format**:
```python
{
    "email_id": {"rich_text": [{"text": {"content": "msg_001"}}]},
    "담당자": {"rich_text": [{"text": {"content": "김주영"}}]},
    "스타트업명": {"relation": [{"id": "abc123..."}]},
    "협업기관": {"relation": [{"id": "xyz789..."}]},
    "협업형태": {"select": {"name": "[A]PortCoXSSG"}},
    "협업강도": {"select": {"name": "협력"}},
    "날짜": {"date": {"start": "2025-10-28"}},
    "협업내용": {"rich_text": [{"text": {"content": "..."}}]},
    "요약": {"rich_text": [{"text": {"content": "..."}}]},
    "타입신뢰도": {"number": 0.95},
    "강도신뢰도": {"number": 0.88}
}
```

**Field Mapping Table**:

| Source Field (Pydantic) | Notion Property (Korean) | Type | Formatter | Required |
|-------------------------|--------------------------|------|-----------|----------|
| `email_id` | email_id | rich_text | `_format_rich_text` | Yes |
| `person_in_charge` | 담당자 | rich_text | `_format_rich_text` | No |
| `matched_company_id` | 스타트업명 | relation | `_format_relation` | No |
| `matched_partner_id` | 협업기관 | relation | `_format_relation` | No |
| `details` | 협업내용 | rich_text | `_format_rich_text` | No |
| `date` | 날짜 | date | `_format_date` | No |
| `collaboration_type` | 협업형태 | select | `_format_select` | No |
| `collaboration_intensity` | 협업강도 | select | `_format_select` | No |
| `collaboration_summary` | 요약 | rich_text | `_format_rich_text` | No |
| `type_confidence` | 타입신뢰도 | number | `_format_number` | No |
| `intensity_confidence` | 강도신뢰도 | number | `_format_number` | No |

**Null Handling Contract**:
- If field value is `None`, omit from output dict
- If field value is empty string `""`, omit from output dict
- If field value is `0` or `0.0` (number), include (valid value)
- If field value is empty list `[]`, omit from output dict

**Error Conditions**:
- **Missing email_id**: Raises `ValueError("email_id is required")`
- **Invalid Type**: Raises `TypeError(f"Expected {expected_type}, got {actual_type}")`
- **Invalid Relation ID**: Logs warning, omits field (graceful degradation)

**Side Effects**:
- Logs debug messages for omitted fields (null/empty)
- Logs warnings for invalid field values (type mismatches, invalid IDs)

**Performance Expectations**:
- Mapping time: <10ms for full ExtractedEntitiesWithClassification object
- Memory: <1MB (Pydantic model + output dict)

---

## Field-Specific Formatters

### 2. _format_rich_text()

**Purpose**: Format string value as Notion rich_text property.

**Signature**:
```python
def _format_rich_text(self, text: str) -> Dict[str, Any]:
    """
    Format text as Notion rich_text property.

    Handles Korean text (UTF-8), truncates if exceeds 2000 chars,
    preserves whitespace and line breaks.

    Args:
        text: Text content (any Unicode string)

    Returns:
        Notion rich_text property format

    Example:
        >>> mapper._format_rich_text("김주영")
        {'rich_text': [{'text': {'content': '김주영'}}]}

        >>> mapper._format_rich_text("a" * 2001)  # Truncated
        {'rich_text': [{'text': {'content': 'aaa...aaa...'}}]}
    """
```

**Input Validation**:
- `text`: Must be string (unicode)
- Length: If >2000 chars, truncate to 1997 + "..."

**Output Format**:
```python
{
    "rich_text": [
        {
            "text": {"content": text}
        }
    ]
}
```

**Truncation Logic**:
```python
if len(text) > 2000:
    text = text[:1997] + "..."
```

**Type Conversion Rules**:
- String → rich_text: Direct mapping
- Korean text (UTF-8): No special encoding needed
- Newlines: Preserved (use `\n`)
- Emojis: Preserved (Notion supports Unicode)

**Error Conditions**:
- **Non-string input**: Raises `TypeError("Expected str, got {type(text)}")`

---

### 3. _format_select()

**Purpose**: Format string value as Notion select property.

**Signature**:
```python
def _format_select(self, value: str) -> Dict[str, Any]:
    """
    Format value as Notion select property.

    Does NOT validate against schema options (Notion API handles validation).
    If value doesn't exist in select options, Notion returns 400 error.

    Args:
        value: Select option name (exact match required)

    Returns:
        Notion select property format

    Example:
        >>> mapper._format_select("협력")
        {'select': {'name': '협력'}}

        >>> mapper._format_select("[A]PortCoXSSG")
        {'select': {'name': '[A]PortCoXSSG'}}
    """
```

**Input Validation**:
- `value`: Must be non-empty string
- No validation against schema options (deferred to Notion API)

**Output Format**:
```python
{
    "select": {"name": value}
}
```

**Type Conversion Rules**:
- String → select: Direct mapping (exact match)
- Case-sensitive: "협력" ≠ "협력 " (trailing space)
- Special characters: Preserved (e.g., "[A]", "-", "_")

**Error Conditions**:
- **Non-string input**: Raises `TypeError("Expected str, got {type(value)}")`
- **Empty string**: Raises `ValueError("Select value cannot be empty")`
- **Invalid option**: Notion API returns 400 (handled by NotionWriter)

---

### 4. _format_relation()

**Purpose**: Format Notion page ID as relation property.

**Signature**:
```python
def _format_relation(self, page_id: str) -> Dict[str, Any]:
    """
    Format page ID as Notion relation property.

    Validates page ID format (32 or 36 characters, UUID).
    Supports single relation only (not multi-relation).

    Args:
        page_id: Notion page ID (32 or 36 chars)

    Returns:
        Notion relation property format

    Raises:
        ValueError: If page_id length not in (32, 36)

    Example:
        >>> mapper._format_relation("abc123def456ghi789jkl012mno345pq")
        {'relation': [{'id': 'abc123def456ghi789jkl012mno345pq'}]}
    """
```

**Input Validation**:
- `page_id`: Must be 32 or 36 characters (Notion page ID format)
- Format: Alphanumeric (UUID format, dashes optional)

**Output Format**:
```python
{
    "relation": [{"id": page_id}]
}
```

**Type Conversion Rules**:
- String (32 chars) → relation: Direct mapping (dashes removed)
- String (36 chars) → relation: Direct mapping (dashes included)
- Multiple relations: Not supported in Phase 2d (single relation only)

**Error Conditions**:
- **Invalid length**: Raises `ValueError(f"Invalid page ID length: {len(page_id)}, expected 32 or 36")`
- **Non-string input**: Raises `TypeError("Expected str, got {type(page_id)}")`
- **Empty string**: Raises `ValueError("Page ID cannot be empty")`

**Note**: Notion API does NOT validate relation target existence. Invalid page IDs are accepted but will appear as broken links in Notion UI.

---

### 5. _format_date()

**Purpose**: Format datetime as Notion date property (ISO 8601).

**Signature**:
```python
def _format_date(self, date: datetime) -> Dict[str, Any]:
    """
    Format datetime as Notion date property.

    Converts Python datetime to ISO 8601 date string (YYYY-MM-DD).
    Timezone info is discarded (Notion stores dates only, no time).

    Args:
        date: Python datetime object (timezone-aware or naive)

    Returns:
        Notion date property format

    Example:
        >>> from datetime import datetime
        >>> mapper._format_date(datetime(2025, 10, 28))
        {'date': {'start': '2025-10-28'}}

        >>> mapper._format_date(datetime(2025, 10, 28, 14, 30, 0))
        {'date': {'start': '2025-10-28'}}  # Time discarded
    """
```

**Input Validation**:
- `date`: Must be Python `datetime` object
- Timezone: Ignored (Notion date properties are timezone-agnostic)

**Output Format**:
```python
{
    "date": {"start": "YYYY-MM-DD"}
}
```

**Type Conversion Rules**:
- `datetime` → ISO 8601 date: `date.strftime("%Y-%m-%d")`
- Time component: Discarded (Notion date field, not datetime)
- Timezone: Discarded (Notion stores dates only)

**Error Conditions**:
- **Non-datetime input**: Raises `TypeError("Expected datetime, got {type(date)}")`
- **None value**: Omit field (handled by `map_to_notion_properties`)

---

### 6. _format_number()

**Purpose**: Format float/int as Notion number property.

**Signature**:
```python
def _format_number(self, value: float) -> Dict[str, Any]:
    """
    Format numeric value as Notion number property.

    Supports both int and float. Validates range for confidence scores (0.0-1.0).

    Args:
        value: Numeric value (int or float)

    Returns:
        Notion number property format

    Example:
        >>> mapper._format_number(0.95)
        {'number': 0.95}

        >>> mapper._format_number(42)
        {'number': 42}
    """
```

**Input Validation**:
- `value`: Must be `int` or `float`
- Range: No validation (accepts any numeric value)

**Output Format**:
```python
{
    "number": value
}
```

**Type Conversion Rules**:
- `int` → number: Direct mapping
- `float` → number: Direct mapping
- `0` or `0.0`: Included (valid value, not treated as null)
- Infinity/NaN: Not supported (raises ValueError)

**Error Conditions**:
- **Non-numeric input**: Raises `TypeError("Expected int or float, got {type(value)}")`
- **Infinity/NaN**: Raises `ValueError("Cannot format infinity or NaN as Notion number")`

---

## Helper Methods

### 7. validate_field_value()

**Purpose**: Validate field value against expected type and constraints.

**Signature**:
```python
def validate_field_value(
    self,
    field_name: str,
    value: Any,
    expected_type: Type
) -> bool:
    """
    Validate field value against expected type.

    Used for pre-mapping validation to catch type errors early.

    Args:
        field_name: Pydantic field name (for error messages)
        value: Field value to validate
        expected_type: Expected Python type

    Returns:
        True if valid, False otherwise

    Example:
        >>> mapper.validate_field_value("person_in_charge", "김주영", str)
        True

        >>> mapper.validate_field_value("type_confidence", "0.95", float)
        False  # String, not float
    """
```

**Validation Rules**:
- Type check: `isinstance(value, expected_type)`
- Range check: For confidence scores (0.0-1.0)
- Length check: For Notion page IDs (32 or 36 chars)

---

### 8. get_property_type()

**Purpose**: Get Notion property type for a given field name.

**Signature**:
```python
def get_property_type(self, notion_property_name: str) -> Optional[str]:
    """
    Get Notion property type from schema.

    Args:
        notion_property_name: Notion property name (e.g., "담당자")

    Returns:
        Property type (e.g., "rich_text", "relation", "select") or None

    Example:
        >>> mapper.get_property_type("담당자")
        'rich_text'

        >>> mapper.get_property_type("스타트업명")
        'relation'
    """
```

**Usage**:
- Schema lookup for dynamic mapping
- Validation during field mapping

---

## Null Handling Contract

### Rules

1. **Null/None values**: Omit from properties dict
2. **Empty strings**: Omit from properties dict
3. **Empty lists**: Omit from properties dict
4. **Zero values (0, 0.0)**: Include (valid numeric value)
5. **False values**: Include (valid boolean, if supported)

### Example

```python
extracted_data = ExtractedEntitiesWithClassification(
    email_id="msg_001",
    person_in_charge="김주영",
    startup_name=None,  # Will be omitted
    partner_org="",     # Will be omitted
    details="...",
    date=None,          # Will be omitted
    collaboration_type="[A]PortCoXSSG",
    type_confidence=0.0,  # Will be INCLUDED (valid value)
    ...
)

properties = mapper.map_to_notion_properties(extracted_data)
# Output: Only includes email_id, person_in_charge, details, collaboration_type, type_confidence
```

---

## Korean Text Encoding

### UTF-8 Handling

Python 3.12 strings are Unicode by default. No special encoding needed:

```python
# Korean text preserved throughout
korean_text = "브레이크앤컴퍼니와 신세계푸드가 협력"
formatted = mapper._format_rich_text(korean_text)
# Output: {'rich_text': [{'text': {'content': '브레이크앤컴퍼니와 신세계푸드가 협력'}}]}

# JSON serialization preserves Korean characters
import json
json_str = json.dumps(formatted, ensure_ascii=False)
# ensure_ascii=False prevents Unicode escape sequences
```

### Testing

```python
def test_korean_text_round_trip():
    """Test Korean text encoding preservation."""
    korean_text = "담당자: 김주영, 스타트업: 브레이크앤컴퍼니"
    formatted = mapper._format_rich_text(korean_text)

    # Verify structure
    assert formatted["rich_text"][0]["text"]["content"] == korean_text

    # Verify JSON round-trip
    json_str = json.dumps(formatted, ensure_ascii=False)
    parsed = json.loads(json_str)
    assert parsed["rich_text"][0]["text"]["content"] == korean_text
```

---

## Configuration

### No Configuration Required

FieldMapper is stateless except for schema dependency. Configuration is handled at NotionWriter level.

---

## Usage Examples

### Basic Field Mapping

```python
from src.notion_writer.field_mapper import FieldMapper
from src.notion_integrator import NotionIntegrator

# Initialize with schema
integrator = NotionIntegrator()
schema = await integrator.discover_database_schema(database_id)
mapper = FieldMapper(schema)

# Map extracted data
properties = mapper.map_to_notion_properties(extracted_data)

# Use in API call
await client.pages.create(
    parent={"database_id": database_id},
    properties=properties
)
```

### Individual Field Formatting

```python
# Format specific fields
rich_text_prop = mapper._format_rich_text("김주영")
select_prop = mapper._format_select("협력")
relation_prop = mapper._format_relation("abc123def456ghi789jkl012mno345pq")
date_prop = mapper._format_date(datetime(2025, 10, 28))
number_prop = mapper._format_number(0.95)
```

### Null Handling

```python
extracted_data = ExtractedEntitiesWithClassification(
    email_id="msg_001",
    person_in_charge=None,  # Omitted
    startup_name="브레이크앤컴퍼니",
    partner_org="",  # Omitted
    details="...",
    date=None,  # Omitted
)

properties = mapper.map_to_notion_properties(extracted_data)
# Only includes: email_id, startup_name, details
```

---

## Testing Contract

### Unit Tests Required

1. **Field Type Formatters**:
   - Test `_format_rich_text` with Korean text
   - Test `_format_rich_text` with long text (>2000 chars)
   - Test `_format_select` with valid values
   - Test `_format_relation` with 32 and 36 char IDs
   - Test `_format_date` with datetime objects
   - Test `_format_number` with int and float

2. **Null Handling**:
   - Test None values omitted
   - Test empty strings omitted
   - Test zero values included
   - Test empty lists omitted

3. **Validation**:
   - Test invalid types raise TypeError
   - Test invalid relation IDs raise ValueError
   - Test email_id required validation

### Integration Tests Required

1. **Full Mapping Workflow**:
   - Test mapping full ExtractedEntitiesWithClassification
   - Test output dict structure matches Notion API format
   - Test Korean text preserved in output

2. **Schema Compatibility**:
   - Test mapping against real database schema
   - Test handling of new optional fields (backward compatibility)

---

## Performance Guarantees

- **Single Field**: <1ms per field
- **Full Mapping**: <10ms for ExtractedEntitiesWithClassification
- **Memory**: <500KB per mapping operation

---

## Error Handling

### Exception Types

- `ValueError`: Invalid field value (missing required field, invalid format)
- `TypeError`: Wrong type (expected str, got int)
- `AttributeError`: Field doesn't exist in Pydantic model

### Error Messages

Clear, actionable error messages:
```python
# Good
raise ValueError(f"email_id is required for write operation, got None")

# Good
raise TypeError(f"Expected str for person_in_charge, got {type(value).__name__}")

# Good
raise ValueError(f"Invalid page ID length: {len(page_id)}, expected 32 or 36")
```

---

## Dependencies

- `pydantic>=2.0.0`: ExtractedEntitiesWithClassification model
- `typing`: Type hints (built-in)
- `datetime`: Date formatting (built-in)
- Python 3.12+: Unicode string support

---

## References

- [Data Model](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/data-model.md)
- [NotionWriter Contract](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/contracts/notion_writer_contract.md)
- [Notion API Property Objects](https://developers.notion.com/reference/property-object)
- [ExtractedEntitiesWithClassification Model](/Users/jlim/Projects/CollabIQ/src/llm_provider/types.py)
