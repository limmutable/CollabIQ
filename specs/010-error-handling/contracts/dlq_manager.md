# Contract: Dead Letter Queue (DLQ) Manager

**Component**: `src/error_handling/dlq_manager.py` (extends existing from Feature 006)
**Purpose**: Preserve failed operations with full context for manual review or replay

---

## Interface

### `class DLQManager`

Manages dead letter queue entries for failed operations.

**Methods**:

```python
def enqueue(
    self,
    email_id: str,
    operation_type: str,
    original_payload: Dict[str, Any],
    error_details: Dict[str, Any]
) -> str:
    """Add failed operation to DLQ. Returns dlq_id."""
    pass

def dequeue(self, dlq_id: str) -> Optional[DLQEntry]:
    """Retrieve DLQ entry by ID."""
    pass

def list_pending(self, operation_type: Optional[str] = None) -> List[DLQEntry]:
    """List all pending DLQ entries, optionally filtered by operation type."""
    pass

def replay(self, dlq_id: str) -> bool:
    """Replay DLQ entry. Returns True if successful."""
    pass

def replay_batch(self, operation_type: str, max_count: int = 10) -> Dict[str, int]:
    """Replay multiple DLQ entries. Returns success/failure counts."""
    pass

def mark_completed(self, dlq_id: str) -> bool:
    """Mark DLQ entry as completed."""
    pass

def is_processed(self, dlq_id: str) -> bool:
    """Check if DLQ entry already processed (idempotency check)."""
    pass
```

---

## Contract Specifications

### 1. **Enqueue Failed Operation**

**Given**: Email processing fails after exhausting retries
**When**: `enqueue()` is called with error details
**Then**:
- DLQ entry created with unique ID (format: `dlq_{timestamp}_{email_id}`)
- Entry saved to `data/dlq/{operation_type}/{dlq_id}.json`
- Status set to "pending"
- Returns dlq_id for tracking

**Test**:
```python
dlq_manager = DLQManager()

dlq_id = dlq_manager.enqueue(
    email_id="19a3f3f856f0b4d4",
    operation_type="notion_write",
    original_payload={"database_id": "db_123", "properties": {...}},
    error_details={
        "error_type": "CircuitBreakerOpen",
        "error_message": "Notion service degraded",
        "retry_count": 3
    }
)

assert dlq_id.startswith("dlq_")
assert Path(f"data/dlq/notion_write/{dlq_id}.json").exists()

entry = dlq_manager.dequeue(dlq_id)
assert entry.status == DLQStatus.PENDING
assert entry.email_id == "19a3f3f856f0b4d4"
```

---

### 2. **Dequeue by ID**

**Given**: DLQ entry exists with ID "dlq_123"
**When**: `dequeue("dlq_123")` is called
**Then**:
- Returns DLQEntry object with all fields populated
- Entry remains in DLQ (not deleted)
- Returns None if ID doesn't exist

**Test**:
```python
# Create entry
dlq_id = dlq_manager.enqueue(...)

# Retrieve entry
entry = dlq_manager.dequeue(dlq_id)
assert entry is not None
assert entry.dlq_id == dlq_id
assert entry.original_payload == {...}

# Entry still exists
assert dlq_manager.dequeue(dlq_id) is not None

# Non-existent ID
assert dlq_manager.dequeue("dlq_nonexistent") is None
```

---

### 3. **List Pending Entries**

**Given**: DLQ has 3 pending entries (2 notion_write, 1 gmail_fetch)
**When**: `list_pending()` is called
**Then**:
- Returns list of all 3 pending entries
- Entries sorted by created_at (oldest first)

**When**: `list_pending(operation_type="notion_write")` is called
**Then**:
- Returns list of 2 notion_write entries only

**Test**:
```python
dlq_manager.enqueue(email_id="1", operation_type="notion_write", ...)
dlq_manager.enqueue(email_id="2", operation_type="notion_write", ...)
dlq_manager.enqueue(email_id="3", operation_type="gmail_fetch", ...)

# List all
all_pending = dlq_manager.list_pending()
assert len(all_pending) == 3

# Filter by operation type
notion_pending = dlq_manager.list_pending(operation_type="notion_write")
assert len(notion_pending) == 2
assert all(e.operation_type == "notion_write" for e in notion_pending)
```

---

### 4. **Replay Single Entry (Success)**

**Given**: DLQ entry exists for failed Notion write
**When**: `replay(dlq_id)` is called after Notion service recovers
**Then**:
- Entry status updated to "replaying"
- Original operation re-executed with original_payload
- If succeeds, status updated to "completed", replayed_at timestamp set
- Entry moved to `.processed_ids.json` for idempotency
- Returns True

**Test**:
```python
# Create failed entry
dlq_id = dlq_manager.enqueue(
    email_id="19a3f3f856f0b4d4",
    operation_type="notion_write",
    original_payload={"database_id": "db_123", "properties": {...}}
)

# Service recovers
notion_api.circuit_breaker.state = CircuitState.CLOSED

# Replay
success = dlq_manager.replay(dlq_id)
assert success is True

# Check status
entry = dlq_manager.dequeue(dlq_id)
assert entry.status == DLQStatus.COMPLETED
assert entry.replayed_at is not None

# Idempotency check
assert dlq_manager.is_processed(dlq_id) is True
```

---

### 5. **Replay Single Entry (Failure)**

**Given**: DLQ entry exists for failed Notion write
**When**: `replay(dlq_id)` is called but operation fails again
**Then**:
- Entry status updated to "failed"
- Error details appended with replay failure info
- Entry remains in DLQ for manual investigation
- Returns False

**Test**:
```python
dlq_id = dlq_manager.enqueue(...)

# Service still down
notion_api.circuit_breaker.state = CircuitState.OPEN

# Replay fails
success = dlq_manager.replay(dlq_id)
assert success is False

# Check status
entry = dlq_manager.dequeue(dlq_id)
assert entry.status == DLQStatus.FAILED
assert "Replay failed" in entry.error_details["error_message"]
```

---

### 6. **Replay Batch**

**Given**: DLQ has 5 pending Notion write entries
**When**: `replay_batch(operation_type="notion_write", max_count=3)` is called
**Then**:
- Replays up to 3 entries (oldest first)
- Returns dict with success/failure counts: `{"success": 2, "failed": 1}`
- Completed entries marked as processed
- Failed entries remain in DLQ with status "failed"

**Test**:
```python
# Create 5 DLQ entries
for i in range(5):
    dlq_manager.enqueue(
        email_id=f"email_{i}",
        operation_type="notion_write",
        original_payload={...}
    )

# Replay batch of 3
results = dlq_manager.replay_batch(operation_type="notion_write", max_count=3)

assert results["success"] >= 0
assert results["failed"] >= 0
assert results["success"] + results["failed"] == 3

# 2 entries remain pending
pending = dlq_manager.list_pending(operation_type="notion_write")
assert len([e for e in pending if e.status == DLQStatus.PENDING]) == 2
```

---

### 7. **Mark Completed Manually**

**Given**: DLQ entry manually resolved outside system
**When**: `mark_completed(dlq_id)` is called
**Then**:
- Entry status updated to "completed"
- Entry added to `.processed_ids.json` for idempotency
- Returns True

**Test**:
```python
dlq_id = dlq_manager.enqueue(...)

# Manual resolution
success = dlq_manager.mark_completed(dlq_id)
assert success is True

# Check status
entry = dlq_manager.dequeue(dlq_id)
assert entry.status == DLQStatus.COMPLETED
assert dlq_manager.is_processed(dlq_id) is True
```

---

### 8. **Idempotency Check (Prevent Duplicate Replay)**

**Given**: DLQ entry already replayed successfully
**When**: `replay(dlq_id)` is called again
**Then**:
- `is_processed()` returns True
- Replay skipped (no duplicate operation)
- Returns False with warning log

**Test**:
```python
dlq_id = dlq_manager.enqueue(...)

# First replay succeeds
dlq_manager.replay(dlq_id)
assert dlq_manager.is_processed(dlq_id) is True

# Attempt duplicate replay
success = dlq_manager.replay(dlq_id)
assert success is False

# Check logs
assert "already processed" in error_logs[-1]["message"]
```

---

### 9. **Preserve Full Context (FR-016)**

**Given**: Email processing fails at Gemini extraction step
**When**: `enqueue()` is called
**Then**:
- DLQ entry includes: email_id, email content (truncated), extraction data (if partial), error details, stack trace, retry count
- All fields meet FR-016 requirements

**Test**:
```python
dlq_id = dlq_manager.enqueue(
    email_id="19a3f3f856f0b4d4",
    operation_type="gemini_extract",
    original_payload={
        "email_content": "Meeting with Acme Corp on Friday...",
        "partial_extraction": {"companies": ["Acme Corp"]}
    },
    error_details={
        "error_type": "ResourceExhausted",
        "error_message": "Quota exceeded",
        "stack_trace": "Traceback...",
        "retry_count": 3
    }
)

entry = dlq_manager.dequeue(dlq_id)
assert "email_content" in entry.original_payload
assert "partial_extraction" in entry.original_payload
assert entry.error_details["retry_count"] == 3
assert entry.error_details["stack_trace"] is not None
```

---

### 10. **DLQ Storage Organization**

**Given**: DLQ entries for multiple operation types
**When**: Entries saved to disk
**Then**:
- Files organized by operation type: `data/dlq/{operation_type}/{dlq_id}.json`
- One JSON file per entry
- `.processed_ids.json` tracks completed entries

**Test**:
```python
dlq_manager.enqueue(email_id="1", operation_type="gmail_fetch", ...)
dlq_manager.enqueue(email_id="2", operation_type="notion_write", ...)

# Check directory structure
assert Path("data/dlq/gmail_fetch/").exists()
assert Path("data/dlq/notion_write/").exists()
assert len(list(Path("data/dlq/gmail_fetch/").glob("*.json"))) == 1
assert len(list(Path("data/dlq/notion_write/").glob("*.json"))) == 1
```

---

## Error Handling

| Scenario | DLQ Action | Logged Error |
|----------|-----------|--------------|
| Enqueue fails (disk full) | Raise exception, log CRITICAL | Yes (system failure) |
| Dequeue fails (file missing) | Return None | Yes (WARNING) |
| Replay fails (operation error) | Mark as failed, return False | Yes (ERROR) |
| Duplicate replay attempt | Skip, return False | Yes (WARNING) |
| Invalid dlq_id format | Return None | Yes (WARNING) |

---

## Performance Contracts

- **SC-003**: 100% data preservation for critical failures
  - ✅ All enqueued entries persisted to disk with full context

- **SC-007**: 100% DLQ replay success rate (after fixing underlying issues)
  - ✅ Idempotency prevents duplicates, full payload enables replay

---

## Integration with Error Handling Pipeline

```python
# In retry decorator (after exhausted retries)
try:
    result = fetch_emails()
except Exception as e:
    if retry_attempts >= max_attempts:
        # Exhausted retries → DLQ
        dlq_id = dlq_manager.enqueue(
            email_id=email_id,
            operation_type="gmail_fetch",
            original_payload={"user_email": user_email},
            error_details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "retry_count": retry_attempts
            }
        )
        logger.error(f"Operation failed, added to DLQ: {dlq_id}")
        raise
```

---

## Dependencies

- `DLQEntry` dataclass from `data-model.md`
- `DLQStatus` enum from `data-model.md`
- Existing DLQ implementation from Feature 006 (`src/dlq/`)
- `json` for file I/O
- `pathlib` for file operations

---

## Test Coverage Requirements

- ✅ Unit tests for all 10 contract scenarios
- ✅ Integration tests with actual file I/O
- ✅ Idempotency tests (prevent duplicate replay)
- ✅ Batch replay tests with mixed success/failure
- ✅ Storage organization tests (directory structure)
- ✅ Error handling tests (disk full, file missing)
