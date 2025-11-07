# Data Model: Error Handling & Retry Logic

**Feature**: 010-error-handling
**Date**: 2025-11-06
**Status**: Phase 1 (Design)

---

## Overview

This document defines the data structures for error handling, retry logic, circuit breaker state management, and dead letter queue (DLQ) entries in the CollabIQ email processing pipeline.

---

## Core Entities

### 1. ErrorRecord

Represents a logged error with full context for debugging and monitoring.

**Purpose**: Structured error logging to enable monitoring, debugging, and post-mortem analysis of failures.

**Storage**: JSON Lines format in `data/logs/{severity}/error_{timestamp}_{email_id}.json`

**Schema**:

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class ErrorSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    TRANSIENT = "TRANSIENT"      # Network timeouts, 5xx errors, rate limits
    PERMANENT = "PERMANENT"      # 4xx errors (except 429), validation errors
    CRITICAL = "CRITICAL"        # Auth failures, token expiration

@dataclass
class ErrorRecord:
    """Structured error log entry with contextual information."""

    # Core fields
    timestamp: datetime                    # ISO 8601 format
    severity: ErrorSeverity               # Log level
    category: ErrorCategory               # Error classification
    message: str                          # Human-readable error message

    # Error details
    error_type: str                       # Exception class name (e.g., "socket.timeout")
    stack_trace: Optional[str]            # Full stack trace for debugging

    # Context
    context: Dict[str, Any]               # Email ID, operation type, retry count

    # Optional API-specific fields
    http_status: Optional[int] = None     # HTTP status code if applicable
    retry_count: int = 0                  # Number of retry attempts made

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "http_status": self.http_status,
            "retry_count": self.retry_count
        }
```

**Example**:

```json
{
  "timestamp": "2025-11-06T10:15:22.123Z",
  "severity": "ERROR",
  "category": "TRANSIENT",
  "message": "Gmail API timeout during email fetch",
  "error_type": "socket.timeout",
  "stack_trace": "Traceback (most recent call last):\n  File...",
  "context": {
    "email_id": "19a3f3f856f0b4d4",
    "operation": "gmail_fetch",
    "user": "jlim@example.com"
  },
  "http_status": null,
  "retry_count": 2
}
```

**Validation Rules**:
- `timestamp` must be valid ISO 8601 datetime
- `severity` must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `category` must be one of: TRANSIENT, PERMANENT, CRITICAL
- `message` must be non-empty string
- `context` must include `email_id` and `operation` keys
- `retry_count` must be non-negative integer

**Relationships**:
- One ErrorRecord per logged error
- ErrorRecord.context.email_id → references Gmail message ID
- Multiple ErrorRecords can reference same email_id (retries)

---

### 2. DLQEntry

Represents a failed operation preserved in the Dead Letter Queue for manual review or replay.

**Purpose**: Preserve failed operations with full context to enable recovery after fixing underlying issues.

**Storage**: JSON files in `data/dlq/{operation_type}/{dlq_id}.json`

**Schema**:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class DLQStatus(Enum):
    PENDING = "pending"           # Awaiting replay
    REPLAYING = "replaying"       # Currently being reprocessed
    COMPLETED = "completed"       # Successfully replayed
    FAILED = "failed"             # Replay failed (after multiple attempts)

@dataclass
class DLQEntry:
    """Dead Letter Queue entry for failed operations."""

    # Identifiers
    dlq_id: str                           # Unique ID (format: dlq_{timestamp}_{email_id})
    email_id: str                         # Gmail message ID
    operation_type: str                   # e.g., "gmail_fetch", "gemini_extract", "notion_write"

    # Status
    status: DLQStatus                     # Current status

    # Original data
    original_payload: Dict[str, Any]      # Full payload for replay (email content, extraction data)

    # Error details
    error_details: Dict[str, Any]         # Error type, message, stack trace, retry count

    # Timestamps
    created_at: datetime                  # When failure occurred
    last_attempt: datetime                # Last retry attempt
    replayed_at: Optional[datetime] = None  # When successfully replayed

    # Idempotency
    processed: bool = False               # Prevents duplicate replay

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON for storage."""
        return {
            "dlq_id": self.dlq_id,
            "email_id": self.email_id,
            "operation_type": self.operation_type,
            "status": self.status.value,
            "original_payload": self.original_payload,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat(),
            "last_attempt": self.last_attempt.isoformat(),
            "replayed_at": self.replayed_at.isoformat() if self.replayed_at else None,
            "processed": self.processed
        }
```

**Example**:

```json
{
  "dlq_id": "dlq_20251106_101522_abc123",
  "email_id": "19a3f3f856f0b4d4",
  "operation_type": "notion_write",
  "status": "pending",
  "original_payload": {
    "database_id": "db_123",
    "properties": {
      "Title": {"title": [{"text": {"content": "Meeting with Acme Corp"}}]},
      "Company": {"relation": [{"id": "company_uuid_456"}]}
    }
  },
  "error_details": {
    "error_type": "CircuitBreakerOpen",
    "error_message": "Notion service degraded after 5 consecutive failures",
    "stack_trace": "Traceback...",
    "retry_count": 3
  },
  "created_at": "2025-11-06T10:15:22.123Z",
  "last_attempt": "2025-11-06T10:15:45.789Z",
  "replayed_at": null,
  "processed": false
}
```

**Validation Rules**:
- `dlq_id` must be unique across all DLQ entries
- `email_id` must be non-empty string (Gmail message ID format)
- `operation_type` must be one of: "gmail_fetch", "gemini_extract", "notion_write", "infisical_fetch"
- `status` must be one of: pending, replaying, completed, failed
- `original_payload` must be non-empty dict
- `error_details` must include: error_type, error_message, retry_count
- `created_at` <= `last_attempt` <= `replayed_at` (temporal ordering)

**Relationships**:
- One DLQEntry per failed operation
- DLQEntry.email_id → references Gmail message ID
- DLQEntry tracks in `.processed_ids.json` for idempotency

---

### 3. RetryConfig

Configuration for retry behavior (exponential backoff, max attempts, timeouts).

**Purpose**: Centralized retry configuration to ensure consistent behavior across all API integrations.

**Storage**: Python config in `src/error_handling/retry.py` (not persisted to disk)

**Schema**:

```python
from dataclasses import dataclass
from typing import Set, Type

@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""

    # Retry limits
    max_attempts: int                     # Maximum retry attempts (default: 3)

    # Backoff configuration
    backoff_multiplier: float             # Exponential multiplier (default: 1.0)
    backoff_min: float                    # Minimum wait time in seconds (default: 1.0)
    backoff_max: float                    # Maximum wait time in seconds (default: 10.0)

    # Jitter
    jitter_min: float                     # Minimum jitter in seconds (default: 0.0)
    jitter_max: float                     # Maximum jitter in seconds (default: 2.0)

    # Timeout
    timeout: float                        # Request timeout in seconds (default: 30.0)

    # Retryable exceptions
    retryable_exceptions: Set[Type[Exception]]  # Exception types to retry

    # API-specific
    respect_retry_after: bool = True      # Honor Retry-After headers (default: True)
```

**Per-API Configurations**:

```python
# Gmail API
GMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=30.0,
    retryable_exceptions={socket.timeout, ConnectionError, HttpError},
    respect_retry_after=True
)

# Gemini API
GEMINI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=60.0,  # Longer timeout for LLM processing
    retryable_exceptions={ResourceExhausted, DeadlineExceeded, ConnectionError},
    respect_retry_after=True
)

# Notion API
NOTION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=30.0,
    retryable_exceptions={APIResponseError},
    respect_retry_after=True
)

# Infisical API
INFISICAL_RETRY_CONFIG = RetryConfig(
    max_attempts=2,  # Fewer attempts (has .env fallback)
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=5.0,  # Shorter max wait
    jitter_min=0.0,
    jitter_max=1.0,
    timeout=10.0,  # Shorter timeout
    retryable_exceptions={socket.timeout, ConnectionError},
    respect_retry_after=False  # No rate limiting expected
)
```

**Validation Rules**:
- `max_attempts` must be >= 1
- `backoff_min` < `backoff_max`
- `jitter_min` < `jitter_max`
- `timeout` must be positive float
- `retryable_exceptions` must be non-empty set

**Relationships**:
- One RetryConfig per API integration (Gmail, Gemini, Notion, Infisical)
- Used by retry decorator in `src/error_handling/retry.py`

---

### 4. CircuitBreakerState

State of circuit breaker for each external service (closed/open/half-open).

**Purpose**: Prevent cascading failures by stopping requests to failing services after threshold is reached.

**Storage**: In-memory state (not persisted between restarts)

**Schema**:

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class CircuitState(Enum):
    CLOSED = "CLOSED"           # Normal operation (requests pass through)
    OPEN = "OPEN"               # Fail-fast mode (reject all requests)
    HALF_OPEN = "HALF_OPEN"     # Testing recovery (allow test request)

@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker pattern."""

    # Service identifier
    service_name: str                     # e.g., "gmail", "gemini", "notion", "infisical"

    # Current state
    state: CircuitState                   # CLOSED, OPEN, HALF_OPEN

    # Failure tracking
    failure_count: int                    # Consecutive failures in CLOSED state
    success_count: int                    # Consecutive successes in HALF_OPEN state

    # Timestamps
    last_failure_time: Optional[datetime] # Last failure timestamp
    open_timestamp: Optional[datetime]    # When circuit opened

    # Configuration
    failure_threshold: int                # Failures before opening (default: 5)
    success_threshold: int                # Successes before closing (default: 2)
    timeout: float                        # Seconds before attempting HALF_OPEN (default: 60.0)

    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit breaker."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self.open_timestamp:
                elapsed = (datetime.utcnow() - self.open_timestamp).total_seconds()
                if elapsed >= self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True

    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def record_failure(self):
        """Record failed request."""
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.open_timestamp = datetime.utcnow()

        elif self.state == CircuitState.HALF_OPEN:
            # Failed during test -> back to OPEN
            self.state = CircuitState.OPEN
            self.open_timestamp = datetime.utcnow()
            self.success_count = 0
```

**Per-Service Configurations**:

```python
# Gmail, Gemini, Notion (critical services)
STANDARD_CIRCUIT_CONFIG = {
    "failure_threshold": 5,
    "success_threshold": 2,
    "timeout": 60.0
}

# Infisical (has .env fallback, fail faster)
INFISICAL_CIRCUIT_CONFIG = {
    "failure_threshold": 3,
    "success_threshold": 2,
    "timeout": 30.0
}
```

**Validation Rules**:
- `service_name` must be one of: "gmail", "gemini", "notion", "infisical"
- `state` must be one of: CLOSED, OPEN, HALF_OPEN
- `failure_count` >= 0
- `success_count` >= 0
- `failure_threshold` > 0
- `success_threshold` > 0
- `timeout` > 0

**State Transitions**:

```
CLOSED → OPEN: failure_count >= failure_threshold
OPEN → HALF_OPEN: (current_time - open_timestamp) >= timeout
HALF_OPEN → CLOSED: success_count >= success_threshold
HALF_OPEN → OPEN: any failure during test
```

**Relationships**:
- One CircuitBreakerState per external service
- State checked before every API call via `should_allow_request()`
- State updated after every API call via `record_success()` or `record_failure()`

---

## Data Flow Diagram

```
Email Processing Pipeline
    │
    ├─ Gmail API Call
    │  ├─ CircuitBreakerState: Check if allowed
    │  ├─ RetryConfig: Apply retry with backoff
    │  ├─ Success → CircuitBreakerState.record_success()
    │  └─ Failure → ErrorRecord logged → retry → DLQEntry if exhausted
    │
    ├─ Gemini API Call
    │  ├─ CircuitBreakerState: Check if allowed
    │  ├─ RetryConfig: Apply retry with backoff
    │  ├─ Success → CircuitBreakerState.record_success()
    │  └─ Failure → ErrorRecord logged → retry → DLQEntry if exhausted
    │
    └─ Notion API Call
       ├─ CircuitBreakerState: Check if allowed
       ├─ RetryConfig: Apply retry with backoff
       ├─ Success → CircuitBreakerState.record_success()
       └─ Failure → ErrorRecord logged → retry → DLQEntry if exhausted
```

---

## Storage Locations

| Entity | Storage Type | Path | Format |
|--------|-------------|------|--------|
| ErrorRecord | File (JSON Lines) | `data/logs/{severity}/error_{timestamp}_{email_id}.json` | JSON |
| DLQEntry | File (JSON) | `data/dlq/{operation_type}/{dlq_id}.json` | JSON |
| RetryConfig | In-memory (Python) | `src/error_handling/retry.py` | Python dataclass |
| CircuitBreakerState | In-memory (Python) | `src/error_handling/circuit_breaker.py` | Python dataclass |

---

## Validation Summary

All entities enforce validation rules via:
1. Python `dataclasses` with type hints
2. Custom `__post_init__()` validation methods
3. Pydantic models (if stricter validation needed)
4. Enum types for categorical fields (ErrorSeverity, ErrorCategory, DLQStatus, CircuitState)

---

## Next Steps

1. ✅ Data model complete (this document)
2. → Generate API contracts in `contracts/`
3. → Generate `quickstart.md` for developers
4. → Implement entities in `src/error_handling/`
5. → Write contract tests in `tests/contract/`
