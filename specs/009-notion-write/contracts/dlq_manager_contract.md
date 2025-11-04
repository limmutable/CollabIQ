# Contract: DLQManager

**Feature**: Phase 2d - Notion Write Operations
**Created**: 2025-11-03
**Status**: Phase 1 Design

---

## Overview

The `DLQManager` (Dead Letter Queue Manager) interface defines the contract for capturing, storing, and retrying failed Notion write operations. Provides file-based JSON storage with full context for debugging and manual intervention.

---

## Interface Definition

### Class: DLQManager

**Purpose**: Manages dead letter queue for failed Notion writes with file-based storage, retry tracking, and manual recovery support.

**Dependencies**:
- `pathlib.Path`: File system operations
- `pydantic`: DLQEntry model serialization
- `ExtractedEntitiesWithClassification`: Captured data model

**Initialization**:
```python
class DLQManager:
    """Manages dead letter queue for failed Notion writes."""

    def __init__(self, dlq_dir: str = "data/dlq"):
        """
        Initialize DLQManager with storage directory.

        Args:
            dlq_dir: Directory for DLQ files (default: "data/dlq")

        Side Effects:
            Creates dlq_dir if it doesn't exist (mkdir -p)

        Example:
            >>> dlq = DLQManager()  # Uses default data/dlq
            >>> dlq = DLQManager("custom/dlq/path")
        """
```

---

## Core Methods

### 1. save_failed_write()

**Purpose**: Capture failed write operation and save to DLQ with full context.

**Signature**:
```python
def save_failed_write(
    self,
    email_id: str,
    extracted_data: ExtractedEntitiesWithClassification,
    error: Exception,
    original_email_content: Optional[str] = None
) -> Path:
    """
    Save failed write to DLQ.

    Creates a JSON file with full context for retry or debugging.
    File naming: {email_id}_{timestamp}.json

    Args:
        email_id: Email identifier (must match extracted_data.email_id)
        extracted_data: Full extracted entity data that failed to write
        error: Exception that caused the failure
        original_email_content: Optional original email text for re-extraction

    Returns:
        Path to the saved DLQ file

    Raises:
        ValueError: If email_id doesn't match extracted_data.email_id
        OSError: If file write fails (permissions, disk full)

    Example:
        >>> try:
        ...     await writer.create_page(...)
        ... except APIResponseError as e:
        ...     dlq_path = dlq_manager.save_failed_write(
        ...         email_id="msg_001",
        ...         extracted_data=extracted_data,
        ...         error=e
        ...     )
        ...     logger.error(f"Write failed, saved to {dlq_path}")
    """
```

**Input Validation**:
- `email_id`: Must be non-empty string
- `email_id`: Must match `extracted_data.email_id`
- `extracted_data`: Must be valid ExtractedEntitiesWithClassification instance
- `error`: Must be Exception instance

**File Naming Convention**:
```
data/dlq/{email_id}_{timestamp}.json
```

**Timestamp Format**: `YYYYMMDD_HHMMSS` (UTC)

**Example Filenames**:
- `msg_abc123_20251103_143052.json`
- `msg_def456_20251103_150230.json`

**DLQ Entry Structure**:
```json
{
  "email_id": "msg_abc123",
  "failed_at": "2025-11-03T14:30:52Z",
  "retry_count": 0,
  "error": {
    "type": "APIResponseError",
    "message": "validation_error: body.properties.협업형태...",
    "status_code": 400,
    "response_body": "{...}"
  },
  "extracted_data": {
    "person_in_charge": "김주영",
    "startup_name": "브레이크앤컴퍼니",
    ...
  },
  "original_email_content": null,
  "dlq_file_path": "data/dlq/msg_abc123_20251103_143052.json"
}
```

**Error Context Captured**:
- `error.type`: Exception class name (e.g., "APIResponseError", "NotionAPIError")
- `error.message`: Human-readable error message
- `error.status_code`: HTTP status code if API error (e.g., 400, 403, 404)
- `error.response_body`: Full Notion API response if available

**Side Effects**:
- Creates DLQ file in `dlq_dir`
- Logs error with DLQ file path (error level)
- Increments DLQ metrics (if monitoring enabled)

**Performance Expectations**:
- Save time: <50ms (file write + JSON serialization)
- File size: ~2-5KB per entry (depending on extracted data size)

---

### 2. list_failed_writes()

**Purpose**: List all DLQ entries for manual review or batch retry.

**Signature**:
```python
def list_failed_writes(
    self,
    sort_by: str = "timestamp",
    ascending: bool = False
) -> List[Path]:
    """
    List all DLQ entries.

    Returns sorted list of DLQ file paths for iteration or reporting.

    Args:
        sort_by: Sort key ("timestamp", "email_id") (default: "timestamp")
        ascending: Sort order (default: False = newest first)

    Returns:
        List of Path objects for DLQ files

    Example:
        >>> dlq_files = dlq_manager.list_failed_writes()
        >>> print(f"Found {len(dlq_files)} failed writes")
        >>> for filepath in dlq_files:
        ...     print(f"  - {filepath.name}")
    """
```

**Input Validation**:
- `sort_by`: Must be "timestamp" or "email_id"

**Output**:
- List of `pathlib.Path` objects
- Sorted by modification time (default: newest first)
- Empty list if no DLQ entries

**Sorting Behavior**:
- `sort_by="timestamp"`: Sort by file modification time
- `sort_by="email_id"`: Sort alphabetically by filename (email_id)
- `ascending=False`: Newest/highest first (default)
- `ascending=True`: Oldest/lowest first

**Example Output**:
```python
[
    Path("data/dlq/msg_abc123_20251103_143052.json"),
    Path("data/dlq/msg_def456_20251103_142030.json"),
    Path("data/dlq/msg_ghi789_20251103_141500.json")
]
```

**Side Effects**:
- No side effects (read-only operation)

**Performance Expectations**:
- List time: <100ms for 1000 files
- Memory: ~50KB per 1000 entries

---

### 3. load_entry()

**Purpose**: Load and deserialize a DLQ entry from file.

**Signature**:
```python
def load_entry(self, filepath: Path) -> DLQEntry:
    """
    Load a DLQ entry from file.

    Deserializes JSON file to DLQEntry Pydantic model.

    Args:
        filepath: Path to DLQ JSON file

    Returns:
        DLQEntry model instance

    Raises:
        FileNotFoundError: If filepath doesn't exist
        ValueError: If JSON is invalid or model validation fails
        OSError: If file read fails (permissions)

    Example:
        >>> dlq_files = dlq_manager.list_failed_writes()
        >>> entry = dlq_manager.load_entry(dlq_files[0])
        >>> print(f"Email ID: {entry.email_id}")
        >>> print(f"Error: {entry.error['message']}")
    """
```

**Input Validation**:
- `filepath`: Must exist and be readable
- File content: Must be valid JSON
- JSON structure: Must match DLQEntry schema

**Output**:
- `DLQEntry` Pydantic model instance
- Includes deserialized `ExtractedEntitiesWithClassification`

**Deserialization**:
```python
with open(filepath, "r", encoding="utf-8") as f:
    return DLQEntry.model_validate_json(f.read())
```

**Error Conditions**:
- **File not found**: Raises `FileNotFoundError`
- **Invalid JSON**: Raises `ValueError("Invalid JSON in DLQ file")`
- **Schema mismatch**: Raises `ValueError("DLQ entry validation failed")`

**Side Effects**:
- No side effects (read-only operation)

**Performance Expectations**:
- Load time: <10ms per entry
- Memory: ~2-5KB per loaded entry

---

### 4. retry_failed_write()

**Purpose**: Retry a single DLQ entry with updated retry count.

**Signature**:
```python
async def retry_failed_write(
    self,
    filepath: Path,
    writer: NotionWriter,
    database_id: str
) -> WriteResult:
    """
    Retry a failed write operation.

    Loads DLQ entry, attempts write via NotionWriter, and:
    - On success: Deletes DLQ file
    - On failure: Updates retry_count in DLQ file

    Args:
        filepath: Path to DLQ JSON file
        writer: NotionWriter instance to use for retry
        database_id: Notion database ID

    Returns:
        WriteResult indicating success or failure

    Raises:
        FileNotFoundError: If DLQ file doesn't exist
        ValueError: If DLQ entry is invalid

    Example:
        >>> result = await dlq_manager.retry_failed_write(
        ...     filepath=Path("data/dlq/msg_001_20251103_143052.json"),
        ...     writer=notion_writer,
        ...     database_id="abc123def456"
        ... )
        >>> if result.success:
        ...     print("Retry succeeded, DLQ entry deleted")
        ... else:
        ...     print(f"Retry failed: {result.error_message}")
    """
```

**Workflow**:
1. Load DLQ entry from file
2. Attempt write via `NotionWriter.create_collabiq_entry()`
3. **If success**:
   - Delete DLQ file (`filepath.unlink()`)
   - Log success
   - Return WriteResult (success=True)
4. **If failure**:
   - Increment `retry_count` in DLQEntry
   - Save updated DLQEntry back to file
   - Log failure
   - Return WriteResult (success=False)

**Input Validation**:
- `filepath`: Must exist
- `writer`: Must be initialized NotionWriter
- `database_id`: Must be non-empty

**Output**:
- `WriteResult` with success/failure status
- Side effect: DLQ file deleted on success, updated on failure

**Retry Count Management**:
```python
entry = self.load_entry(filepath)
entry.retry_count += 1  # Increment before retry

# After retry attempt
if success:
    filepath.unlink()  # Delete DLQ file
else:
    # Save updated entry with incremented retry_count
    self.save_entry(filepath, entry)
```

**Error Conditions**:
- **Write fails again**: Updates DLQ file, doesn't raise exception
- **DLQ file missing**: Raises `FileNotFoundError`
- **Write succeeds but delete fails**: Logs warning, returns success

**Side Effects**:
- Deletes DLQ file on success
- Updates DLQ file on failure (incremented retry_count)
- Logs retry attempt and result

**Performance Expectations**:
- Retry time: <2 seconds (includes write operation)

---

### 5. delete_entry()

**Purpose**: Manually delete a DLQ entry (for resolved/abandoned failures).

**Signature**:
```python
def delete_entry(self, filepath: Path) -> bool:
    """
    Delete a DLQ entry file.

    Used for manual cleanup of resolved or abandoned failures.

    Args:
        filepath: Path to DLQ JSON file

    Returns:
        True if deleted, False if file didn't exist

    Example:
        >>> dlq_manager.delete_entry(
        ...     Path("data/dlq/msg_001_20251103_143052.json")
        ... )
        True
    """
```

**Input Validation**:
- `filepath`: Must be Path object

**Output**:
- `True`: File existed and was deleted
- `False`: File didn't exist (no-op)

**Error Conditions**:
- **Permission denied**: Raises `OSError`

**Side Effects**:
- Deletes file from filesystem
- Logs deletion (info level)

---

## Helper Methods

### 6. save_entry()

**Purpose**: Internal method to save/update DLQEntry to file.

**Signature**:
```python
def save_entry(self, filepath: Path, entry: DLQEntry) -> None:
    """
    Save DLQEntry to file (internal use).

    Used by save_failed_write() and retry_failed_write() to persist entries.

    Args:
        filepath: Path to DLQ JSON file
        entry: DLQEntry model to save
    """
```

**Serialization**:
```python
with open(filepath, "w", encoding="utf-8") as f:
    f.write(entry.model_dump_json(indent=2))
```

---

### 7. get_stats()

**Purpose**: Get DLQ statistics for monitoring.

**Signature**:
```python
def get_stats(self) -> Dict[str, Any]:
    """
    Get DLQ statistics.

    Returns:
        Dictionary with stats (total_entries, oldest_entry, newest_entry)

    Example:
        >>> stats = dlq_manager.get_stats()
        >>> print(f"Total failed writes: {stats['total_entries']}")
        >>> print(f"Oldest failure: {stats['oldest_entry']}")
    """
```

**Output Format**:
```python
{
    "total_entries": 15,
    "oldest_entry": "2025-11-01T10:30:00Z",
    "newest_entry": "2025-11-03T14:30:52Z",
    "dlq_dir": "data/dlq",
    "total_size_bytes": 73524
}
```

---

## DLQ Entry Model

### DLQEntry (Pydantic Model)

**Definition**:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional

class DLQEntry(BaseModel):
    """Dead letter queue entry for failed Notion writes."""

    email_id: str = Field(
        ...,
        description="Email identifier (must match extracted_data.email_id)"
    )

    failed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when failure occurred"
    )

    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts (0 = initial failure)"
    )

    error: Dict[str, Any] = Field(
        ...,
        description="Error details (type, message, status_code, response_body)"
    )

    extracted_data: ExtractedEntitiesWithClassification = Field(
        ...,
        description="Full extracted entity data"
    )

    original_email_content: Optional[str] = Field(
        None,
        description="Original email text for re-extraction (optional)"
    )

    dlq_file_path: Optional[str] = Field(
        None,
        description="Path to DLQ file (set on save)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Validation**:
- `email_id` must match `extracted_data.email_id`
- `retry_count` must be >= 0
- `error` must contain at least `type` and `message` keys

---

## File Format Specification

### JSON Structure

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
    "details": "AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅",
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

### Encoding

- **Character Encoding**: UTF-8 (preserves Korean text)
- **JSON Format**: Pretty-printed (indent=2) for human readability
- **Datetime Format**: ISO 8601 (e.g., "2025-11-03T14:30:52Z")

---

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DLQ_DIR` | str | "data/dlq" | Dead letter queue directory |

### Constructor Parameters

```python
DLQManager(dlq_dir: str = "data/dlq")
```

---

## Usage Examples

### Basic Usage

```python
from src.notion_writer.dlq_manager import DLQManager
from src.notion_writer import NotionWriter

# Initialize DLQ manager
dlq = DLQManager()

# Save failed write
try:
    await writer.create_collabiq_entry(...)
except Exception as e:
    dlq_path = dlq.save_failed_write(
        email_id="msg_001",
        extracted_data=extracted_data,
        error=e
    )
    logger.error(f"Write failed, saved to {dlq_path}")
```

### List and Review DLQ Entries

```python
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

### Manual Retry

```python
# Retry a specific DLQ entry
dlq_file = Path("data/dlq/msg_001_20251103_143052.json")

result = await dlq.retry_failed_write(
    filepath=dlq_file,
    writer=notion_writer,
    database_id=os.getenv("COLLABIQ_DB_ID")
)

if result.success:
    print(f"✓ Retry succeeded: {result.page_id}")
else:
    print(f"✗ Retry failed: {result.error_message}")
```

### Batch Retry

```python
# Retry all DLQ entries
dlq_files = dlq.list_failed_writes()

for filepath in dlq_files:
    result = await dlq.retry_failed_write(
        filepath=filepath,
        writer=notion_writer,
        database_id=os.getenv("COLLABIQ_DB_ID")
    )

    if result.success:
        print(f"✓ {filepath.name}")
    else:
        print(f"✗ {filepath.name}: {result.error_message}")
```

### DLQ Statistics

```python
# Get DLQ stats for monitoring
stats = dlq.get_stats()

print(f"Total failed writes: {stats['total_entries']}")
print(f"Oldest failure: {stats['oldest_entry']}")
print(f"DLQ size: {stats['total_size_bytes'] / 1024:.1f} KB")
```

---

## Retry Script Contract

### Manual Retry Script (scripts/retry_dlq.py)

**Purpose**: Command-line tool for manual retry of DLQ entries.

**Usage**:
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

**Exit Codes**:
- `0`: All retries succeeded
- `1`: Some retries failed (check output)
- `2`: Invalid arguments or environment error

**Output Format**:
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

---

## Testing Contract

### Unit Tests Required

1. **Save Failed Write**:
   - Test DLQ file creation
   - Test filename format (email_id + timestamp)
   - Test JSON serialization (Korean text preservation)
   - Test error context capture

2. **List Failed Writes**:
   - Test sorting (timestamp, email_id)
   - Test empty directory (no DLQ entries)
   - Test sorting order (ascending/descending)

3. **Load Entry**:
   - Test valid DLQ file loading
   - Test invalid JSON handling
   - Test schema validation

4. **Retry Failed Write**:
   - Test successful retry (DLQ file deleted)
   - Test failed retry (retry_count incremented)
   - Test retry_count persistence

5. **Delete Entry**:
   - Test file deletion
   - Test delete non-existent file (no error)

### Integration Tests Required

1. **Full DLQ Workflow**:
   - Test save → list → load → retry → delete
   - Test retry with real NotionWriter
   - Test Korean text round-trip

2. **Error Scenarios**:
   - Test disk full (OSError)
   - Test permission denied (OSError)
   - Test corrupt JSON file (ValueError)

---

## Performance Guarantees

- **Save**: <50ms per entry
- **List**: <100ms for 1000 entries
- **Load**: <10ms per entry
- **Retry**: <2 seconds (includes write operation)
- **Memory**: <5KB per loaded entry

---

## Error Handling

### Exception Types

- `FileNotFoundError`: DLQ file doesn't exist
- `ValueError`: Invalid JSON or schema validation failure
- `OSError`: File I/O error (permissions, disk full)

### Error Recovery

- **Save fails**: Log error, don't crash (write operation continues)
- **Load fails**: Log error, skip entry (manual review needed)
- **Retry fails**: Update DLQ file, don't crash (retry later)

---

## Dependencies

- `pathlib`: File system operations (built-in)
- `json`: JSON serialization (built-in)
- `pydantic>=2.0.0`: DLQEntry model
- `typing`: Type hints (built-in)
- Python 3.12+: Modern pathlib and datetime support

---

## References

- [Data Model](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/data-model.md)
- [NotionWriter Contract](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/contracts/notion_writer_contract.md)
- [ExtractedEntitiesWithClassification Model](/Users/jlim/Projects/CollabIQ/src/llm_provider/types.py)
- [Research Document - DLQ Patterns](/Users/jlim/Projects/CollabIQ/specs/009-notion-write/research.md#3-dead-letter-queue-dlq-patterns)
