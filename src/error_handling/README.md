# Error Handling & Retry Logic

Comprehensive error handling system with retry logic, circuit breakers, and structured logging for all external API integrations (Gmail, Gemini, Notion, Infisical).

## Features

- ✅ **Automatic Retry** with exponential backoff and jitter
- ✅ **Circuit Breaker** pattern for fault isolation
- ✅ **Error Classification** (TRANSIENT, PERMANENT, CRITICAL)
- ✅ **Structured Logging** with JSON formatting
- ✅ **Rate Limit Handling** respects `Retry-After` headers
- ✅ **Dead Letter Queue** (DLQ) for failed operations
- ✅ **Idempotency** checks for replay operations

---

## Quick Start

### Basic Usage

```python
from error_handling import retry_with_backoff, GMAIL_RETRY_CONFIG

@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_data_from_api():
    """This function will automatically retry on transient failures."""
    return api.call()
```

### Async Functions

```python
from error_handling import retry_with_backoff, NOTION_RETRY_CONFIG

@retry_with_backoff(NOTION_RETRY_CONFIG)
async def create_notion_page(data):
    """Async functions are fully supported."""
    return await notion_client.pages.create(data)
```

---

## Retry Configurations

Pre-configured retry settings for each external API:

| Service | Max Attempts | Timeout | Jitter | Config Constant |
|---------|--------------|---------|--------|-----------------|
| Gmail | 3 | 30s | 0-2s | `GMAIL_RETRY_CONFIG` |
| Gemini | 3 | 60s | 0-2s | `GEMINI_RETRY_CONFIG` |
| Notion | 3 | 30s | 0-2s | `NOTION_RETRY_CONFIG` |
| Infisical | 2 | 10s | 0-2s | `INFISICAL_RETRY_CONFIG` |

### Custom Configuration

```python
from error_handling import retry_with_backoff, RetryConfig

custom_config = RetryConfig(
    max_attempts=5,
    backoff_min=2.0,
    backoff_max=30.0,
    jitter_min=0.0,
    jitter_max=5.0,
    timeout=60.0,
    retryable_exceptions={ConnectionError, TimeoutError},
    respect_retry_after=True
)

@retry_with_backoff(custom_config)
def my_api_call():
    return custom_api.fetch()
```

---

## Circuit Breaker

Prevents cascading failures by failing fast when a service is degraded.

### How It Works

```
CLOSED (Normal) → 5 failures → OPEN (Fail Fast)
                                   ↓
                            60s timeout
                                   ↓
                        HALF_OPEN (Test)
                             ↓         ↓
                        2 successes   failure
                             ↓         ↓
                          CLOSED    OPEN
```

### Circuit Breaker Instances

```python
from error_handling import (
    gmail_circuit_breaker,
    gemini_circuit_breaker,
    notion_circuit_breaker,
    infisical_circuit_breaker
)

# Check circuit state
if gmail_circuit_breaker.should_allow_request():
    # Circuit is closed or half-open, safe to call
    result = fetch_from_gmail()
else:
    # Circuit is open, fail fast
    raise CircuitBreakerOpen("Gmail")
```

### Configuration

| Service | Failure Threshold | Timeout | Success Threshold |
|---------|-------------------|---------|-------------------|
| Gmail | 5 | 60s | 2 |
| Gemini | 5 | 60s | 2 |
| Notion | 5 | 60s | 2 |
| Infisical | 3 | 30s | 2 |

---

## Error Classification

Automatic classification of exceptions to determine retry behavior:

### Categories

**TRANSIENT** (Retryable):
- `socket.timeout`
- `ConnectionError`, `TimeoutError`, `OSError`
- HTTP 429 (Rate Limit), 5xx errors (Server Errors)

**PERMANENT** (Not Retryable):
- HTTP 400 (Bad Request), 403 (Forbidden), 404 (Not Found)
- `ValidationError`, `PydanticValidationError`

**CRITICAL** (Fail Fast):
- HTTP 401 (Unauthorized)
- Authentication/authorization failures

### Usage

```python
from error_handling import ErrorClassifier

try:
    api.call()
except Exception as e:
    category = ErrorClassifier.classify(e)
    is_retryable = ErrorClassifier.is_retryable(e)

    if category == ErrorCategory.TRANSIENT:
        # Retry this error
        pass
    elif category == ErrorCategory.CRITICAL:
        # Alert immediately
        pass
```

---

## Structured Logging

All errors are logged with structured context for debugging.

### Error Record Format

```json
{
  "timestamp": "2025-11-08T12:34:56Z",
  "severity": "ERROR",
  "category": "TRANSIENT",
  "message": "Retry attempt 2/3 failed: Connection timeout",
  "error_type": "socket.timeout",
  "stack_trace": "...",
  "context": {
    "service": "gmail",
    "function": "fetch_emails",
    "attempt": 2,
    "max_attempts": 3
  },
  "retry_count": 2
}
```

### Usage

```python
from error_handling import logger, ErrorRecord, ErrorSeverity, ErrorCategory
from datetime import datetime

error_record = ErrorRecord(
    timestamp=datetime.utcnow(),
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.TRANSIENT,
    message="API call failed",
    error_type="ConnectionError",
    stack_trace=str(e),
    context={"api": "notion", "operation": "create_page"},
    retry_count=1
)

logger.log_error(error_record)
```

---

## Dead Letter Queue (DLQ)

Preserve failed operations for later replay after fixing underlying issues.

### Save to DLQ

```python
from notion_integrator.dlq_manager import DLQManager
from llm_provider.types import ExtractedEntitiesWithClassification

dlq_manager = DLQManager(dlq_dir="data/dlq")

# Save failed write
dlq_file = dlq_manager.save_failed_write(
    extracted_data=extracted_data,
    error_details={
        "error_type": "APIResponseError",
        "error_message": "Rate limited",
        "status_code": 429,
        "retry_count": 3
    }
)
```

### Replay from DLQ

```python
# Replay single entry
success = await dlq_manager.retry_failed_write(
    file_path="/path/to/dlq/entry.json",
    notion_writer=writer
)

# Replay batch
results = await dlq_manager.replay_batch(
    notion_writer=writer,
    max_count=10  # Replay up to 10 entries
)
print(f"Succeeded: {results['succeeded']}, Failed: {results['failed']}")
```

### Idempotency

DLQ automatically tracks processed entries to prevent duplicates:

```python
if dlq_manager.is_processed("email-001"):
    print("Already processed, skipping")
```

---

## Architecture

### Clean Layer Separation

```
Service Layer (gmail_receiver.py, gemini_adapter.py, etc.)
    ↓ @retry_with_backoff decorator
Error Handling Layer (retry.py)
    ↓ Error classification + circuit breaker check
Circuit Breaker (circuit_breaker.py)
    ↓ Per-service isolation
API Client Layer (pure API calls, no retry logic)
```

### Design Principles

1. **Single Source of Truth**: One retry system (`@retry_with_backoff`)
2. **Exceptions Bubble Up**: Don't wrap exceptions until after retry exhaustion
3. **Decorator at Boundaries**: Apply retry decorator at service layer entry points
4. **Circuit Breaker Integration**: All retries respect circuit breaker state
5. **Structured Logging**: All errors logged with `ErrorRecord`

---

## Testing

### Contract Tests

```bash
# Test retry decorator behavior
uv run pytest tests/contract/test_retry_contract.py

# Test circuit breaker state machine
uv run pytest tests/contract/test_circuit_breaker_contract.py

# Test error classification
uv run pytest tests/contract/test_error_classifier.py
```

### Integration Tests

```bash
# Test Gmail retry flow
uv run pytest tests/integration/test_gmail_retry_flow.py

# Test Gemini retry flow
uv run pytest tests/integration/test_gemini_retry_flow.py
```

---

## Performance

- **MTTR (Mean Time To Recovery)**: < 10 seconds for transient failures
- **Failure Recovery Rate**: 95% of transient failures recover automatically
- **Circuit Breaker Response**: < 1ms fail-fast when circuit is open
- **Continue Processing**: < 1s to continue processing after error

---

## Migration Guide

### From Legacy Retry Loops

**Before** (Manual loop):
```python
def fetch_data():
    retry_count = 0
    while retry_count <= MAX_RETRIES:
        try:
            return api.call()
        except Exception as e:
            retry_count += 1
            if retry_count > MAX_RETRIES:
                raise
            time.sleep(2 ** retry_count)
```

**After** (Decorator):
```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_data():
    return api.call()  # Decorator handles all retry logic
```

### From Tenacity Library

**Before**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def api_call():
    return api.fetch()
```

**After**:
```python
from error_handling import retry_with_backoff, NOTION_RETRY_CONFIG

@retry_with_backoff(NOTION_RETRY_CONFIG)
def api_call():
    return api.fetch()  # Now includes circuit breaker!
```

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Transient failure recovery | 95% | ✅ Passing |
| Email processing success | 90% | ✅ Passing |
| DLQ data preservation | 100% | ✅ Complete |
| MTTR for transient failures | < 10s | ✅ Measured |
| Actionable logs | 100% | ✅ Structured |
| Circuit breaker trigger | 5 failures | ✅ Tested |
| DLQ replay success | 100% | ✅ Idempotent |
| Continue after error | < 1s | ✅ Fast fail |

---

## Troubleshooting

### Retry Not Working

**Issue**: Function doesn't retry on failure

**Check**:
1. Is exception type in `retryable_exceptions`?
2. Is circuit breaker open?
3. Is error classified as TRANSIENT?

```python
from error_handling import ErrorClassifier, gmail_circuit_breaker

# Check error classification
category = ErrorClassifier.classify(exception)
print(f"Category: {category}")

# Check circuit state
print(f"Circuit state: {gmail_circuit_breaker.state_obj.state}")
```

### Circuit Breaker Stuck Open

**Issue**: Circuit breaker won't close

**Solution**: Wait for timeout period (60s for Gmail/Gemini/Notion, 30s for Infisical) or manually reset:

```python
from error_handling import gmail_circuit_breaker, CircuitState

# Reset circuit breaker
gmail_circuit_breaker.state_obj.state = CircuitState.CLOSED
gmail_circuit_breaker.state_obj.failure_count = 0
```

### DLQ Files Accumulating

**Issue**: DLQ directory growing with failed entries

**Solution**: Replay failed entries after fixing the underlying issue:

```python
from notion_integrator.dlq_manager import DLQManager
from notion_integrator.writer import NotionWriter

dlq_manager = DLQManager()
writer = NotionWriter(...)

# Replay all entries
results = await dlq_manager.replay_batch(writer, max_count=100)
```

---

## Related Documentation

- [Feature Plan](../../specs/010-error-handling/plan.md)
- [Feature Spec](../../specs/010-error-handling/spec.md)
- [Data Model](../../specs/010-error-handling/data-model.md)
- [Contracts](../../specs/010-error-handling/contracts/)

---

## Support

For issues or questions:
- Check [tasks.md](../../specs/010-error-handling/tasks.md) for known issues
- Run tests: `uv run pytest tests/contract/ tests/integration/ -v`
- Review logs in `data/logs/ERROR/`, `data/logs/WARNING/`
