# Quickstart: Error Handling & Retry Logic

**Feature**: 010-error-handling
**Target Audience**: Developers integrating retry logic and error handling into CollabIQ components
**Time to Complete**: ~30 minutes

---

## Prerequisites

- Python 3.12+ installed via UV
- CollabIQ repository cloned
- Basic familiarity with Python decorators
- Understanding of exception handling

---

## Setup

### 1. Install Dependencies

```bash
cd /Users/jlim/Projects/CollabIQ

# Install tenacity (retry logic library)
uv add tenacity

# Install dev dependencies for testing
uv add --dev pytest pytest-mock pytest-asyncio
```

### 2. Verify Installation

```bash
uv run python -c "import tenacity; print(tenacity.__version__)"
# Expected: 8.x.x or higher
```

---

## Basic Usage

### Example 1: Add Retry to Gmail API Call

**File**: `src/email_receiver/gmail_receiver.py`

```python
from error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG
from error_handling.circuit_breaker import gmail_circuit_breaker

class GmailReceiver:
    @retry_with_backoff(GMAIL_RETRY_CONFIG)
    def fetch_messages(self, max_results: int = 10) -> List[Dict]:
        """Fetch messages with automatic retry on transient failures."""

        # Circuit breaker check
        if not gmail_circuit_breaker.should_allow_request():
            raise CircuitBreakerOpen(service_name="gmail")

        try:
            # Actual Gmail API call
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()

            # Record success
            gmail_circuit_breaker.record_success()
            return results.get('messages', [])

        except Exception as e:
            # Record failure
            gmail_circuit_breaker.record_failure()
            raise
```

**What this does**:
- Retries up to 3 times on transient errors (timeouts, 5xx)
- Uses exponential backoff (1s, 2s, 4s) with jitter
- Checks circuit breaker before making request
- Records success/failure for circuit breaker state

---

### Example 2: Add Retry to Gemini LLM Call

**File**: `src/llm_adapters/gemini_adapter.py`

```python
from error_handling.retry import retry_with_backoff, GEMINI_RETRY_CONFIG
from error_handling.circuit_breaker import gemini_circuit_breaker

class GeminiAdapter:
    @retry_with_backoff(GEMINI_RETRY_CONFIG)
    async def extract_entities(self, email_content: str) -> Dict[str, Any]:
        """Extract entities with automatic retry on rate limits."""

        # Circuit breaker check
        if not gemini_circuit_breaker.should_allow_request():
            raise CircuitBreakerOpen(service_name="gemini")

        try:
            # Actual Gemini API call
            response = await self.model.generate_content_async(
                prompt=self.build_prompt(email_content),
                generation_config=self.config
            )

            # Record success
            gemini_circuit_breaker.record_success()
            return self.parse_response(response)

        except Exception as e:
            # Record failure
            gemini_circuit_breaker.record_failure()
            raise
```

**What this does**:
- Retries on rate limits (429) and timeouts
- Respects `Retry-After` headers from Gemini API
- Longer timeout (60s) for LLM processing
- Works with async/await syntax

---

### Example 3: Handle DLQ for Failed Operations

**File**: `src/email_receiver/gmail_receiver.py`

```python
from error_handling.dlq_manager import dlq_manager
from error_handling.structured_logger import logger

def process_email_with_dlq(email_id: str):
    """Process email with DLQ fallback for unrecoverable failures."""

    try:
        # Try to fetch email with retries
        email = gmail_receiver.fetch_messages()

    except Exception as e:
        # After exhausting retries → DLQ
        dlq_id = dlq_manager.enqueue(
            email_id=email_id,
            operation_type="gmail_fetch",
            original_payload={"user_email": "user@example.com"},
            error_details={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "retry_count": 3
            }
        )

        logger.error(
            f"Gmail fetch failed after retries, added to DLQ: {dlq_id}",
            context={"email_id": email_id, "operation": "gmail_fetch"}
        )

        # Continue processing other emails (graceful degradation)
        return None
```

**What this does**:
- Preserves failed operations in DLQ with full context
- Logs structured error for monitoring
- Allows pipeline to continue processing other emails

---

### Example 4: Replay DLQ Entries

**File**: `scripts/replay_dlq.py`

```python
from error_handling.dlq_manager import dlq_manager

def replay_notion_writes():
    """Replay failed Notion writes after service recovers."""

    # Get all pending Notion write entries
    pending = dlq_manager.list_pending(operation_type="notion_write")
    print(f"Found {len(pending)} pending Notion writes")

    # Replay batch of 10
    results = dlq_manager.replay_batch(
        operation_type="notion_write",
        max_count=10
    )

    print(f"Success: {results['success']}, Failed: {results['failed']}")

if __name__ == "__main__":
    replay_notion_writes()
```

**Usage**:
```bash
uv run python scripts/replay_dlq.py
```

---

## Configuration

### Retry Configs

**File**: `src/error_handling/retry.py`

```python
from dataclasses import dataclass

@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_multiplier: float = 1.0
    backoff_min: float = 1.0
    backoff_max: float = 10.0
    jitter_min: float = 0.0
    jitter_max: float = 2.0
    timeout: float = 30.0
    retryable_exceptions: Set[Type[Exception]] = field(default_factory=set)
    respect_retry_after: bool = True

# Gmail API
GMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    timeout=30.0,
    retryable_exceptions={socket.timeout, ConnectionError, HttpError}
)

# Gemini API
GEMINI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    timeout=60.0,  # Longer for LLM
    retryable_exceptions={ResourceExhausted, DeadlineExceeded}
)

# Notion API
NOTION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    timeout=30.0,
    retryable_exceptions={APIResponseError}
)

# Infisical API
INFISICAL_RETRY_CONFIG = RetryConfig(
    max_attempts=2,  # Fewer attempts (has .env fallback)
    backoff_max=5.0,
    timeout=10.0,
    retryable_exceptions={socket.timeout, ConnectionError}
)
```

### Circuit Breaker Configs

**File**: `src/error_handling/circuit_breaker.py`

```python
# Gmail, Gemini, Notion (critical services)
gmail_circuit_breaker = CircuitBreaker(
    service_name="gmail",
    failure_threshold=5,
    success_threshold=2,
    timeout=60.0
)

# Infisical (has .env fallback, fail faster)
infisical_circuit_breaker = CircuitBreaker(
    service_name="infisical",
    failure_threshold=3,
    success_threshold=2,
    timeout=30.0
)
```

---

## Testing

### Unit Test Example

**File**: `tests/unit/test_retry_decorator.py`

```python
import pytest
from error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

def test_retry_succeeds_on_second_attempt():
    """Test that function succeeds after one retry."""
    attempt_count = 0

    @retry_with_backoff(GMAIL_RETRY_CONFIG)
    def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise socket.timeout("Connection timeout")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert attempt_count == 2  # Failed once, succeeded on retry
```

### Integration Test Example

**File**: `tests/integration/test_gmail_retry_flow.py`

```python
import pytest
from unittest.mock import Mock, patch
from error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

@patch('email_receiver.gmail_receiver.build_gmail_service')
def test_gmail_fetch_with_retry(mock_build_service):
    """Test Gmail fetch with retry on transient failure."""

    # Mock service to fail once, then succeed
    mock_service = Mock()
    mock_service.users().messages().list().execute.side_effect = [
        socket.timeout("Timeout"),
        {"messages": [{"id": "msg_123"}]}
    ]
    mock_build_service.return_value = mock_service

    receiver = GmailReceiver()
    messages = receiver.fetch_messages()

    assert len(messages) == 1
    assert messages[0]["id"] == "msg_123"
    assert mock_service.users().messages().list().execute.call_count == 2
```

### Run Tests

```bash
# Run all error handling tests
uv run pytest tests/contract/test_retry_contract.py -v

# Run with coverage
uv run pytest tests/contract/ --cov=src/error_handling --cov-report=html

# Run integration tests
uv run pytest tests/integration/test_gmail_retry_flow.py -v
```

---

## Debugging

### View Error Logs

**Structured JSON logs** are saved to `data/logs/{severity}/`

```bash
# View ERROR logs
cat data/logs/ERROR/error_*.json | jq .

# Filter by operation type
cat data/logs/ERROR/error_*.json | jq 'select(.context.operation == "gmail_fetch")'

# View retry attempts
cat data/logs/WARNING/error_*.json | jq 'select(.context.retry_count > 0)'
```

### View DLQ Entries

```bash
# List all pending DLQ entries
ls data/dlq/*/

# View specific DLQ entry
cat data/dlq/notion_write/dlq_20251106_101522_abc123.json | jq .

# Count pending by operation type
for dir in data/dlq/*/; do
    echo "$(basename $dir): $(ls $dir/*.json 2>/dev/null | wc -l) entries"
done
```

### Check Circuit Breaker State

**Add health check endpoint** (optional):

```python
# src/error_handling/circuit_breaker.py

def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers."""
    return {
        "gmail": {
            "state": gmail_circuit_breaker.get_state().value,
            "failure_count": gmail_circuit_breaker.failure_count,
            "last_failure": gmail_circuit_breaker.last_failure_time
        },
        "gemini": {
            "state": gemini_circuit_breaker.get_state().value,
            "failure_count": gemini_circuit_breaker.failure_count
        },
        # ... other services
    }
```

---

## Troubleshooting

### Problem: Retries exhausted too quickly

**Symptom**: Function fails after 3 attempts in < 10 seconds

**Solution**: Increase `backoff_max` or `max_attempts` in RetryConfig

```python
GMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=5,  # More attempts
    backoff_max=20.0  # Longer max wait
)
```

---

### Problem: Circuit breaker opens too aggressively

**Symptom**: Circuit opens after only a few failures, blocking legitimate requests

**Solution**: Increase `failure_threshold`

```python
gmail_circuit_breaker = CircuitBreaker(
    service_name="gmail",
    failure_threshold=10,  # More lenient
    timeout=60.0
)
```

---

### Problem: DLQ entries not replaying

**Symptom**: `replay()` returns False, but no clear error

**Solution**: Check logs for detailed error, verify service is healthy

```bash
# Check circuit breaker state
uv run python -c "from error_handling.circuit_breaker import gmail_circuit_breaker; print(gmail_circuit_breaker.get_state())"

# Check DLQ entry details
cat data/dlq/gmail_fetch/dlq_*.json | jq '.error_details'
```

---

### Problem: Rate limit errors still occurring

**Symptom**: Gemini API returns 429 even after implementing retry

**Solution**: Verify `Retry-After` header parsing

```python
# Add debug logging
@retry_with_backoff(GEMINI_RETRY_CONFIG)
def extract_entities(self, email_content: str):
    try:
        response = self.model.generate_content(...)
    except ResourceExhausted as e:
        retry_after = ErrorClassifier.extract_retry_after(e)
        logger.debug(f"Rate limited, retry after: {retry_after}s")
        raise
```

---

## Best Practices

### ✅ DO

1. **Use circuit breakers for all external API calls** (Gmail, Gemini, Notion, Infisical)
2. **Log structured errors with context** (email_id, operation, retry_count)
3. **Preserve failed operations in DLQ** for recovery
4. **Test retry logic with mocked failures** (unit + integration tests)
5. **Monitor circuit breaker state** in production
6. **Respect rate limit headers** (Retry-After)

### ❌ DON'T

1. **Don't retry permanent errors** (401, 403, 404, validation errors)
2. **Don't ignore circuit breaker state** (always check before requests)
3. **Don't lose context in DLQ** (include full payload + error details)
4. **Don't retry infinitely** (always set `max_attempts`)
5. **Don't use fixed backoff** (always use exponential + jitter)
6. **Don't skip idempotency checks** (prevent duplicate DLQ replay)

---

## Next Steps

1. ✅ Complete quickstart tutorial
2. → Read contract specifications in `specs/010-error-handling/contracts/`
3. → Implement retry decorators in your components
4. → Write unit tests for retry behavior
5. → Run E2E tests to verify error handling
6. → Monitor error logs and DLQ in production

---

## Reference Documentation

- [Spec](spec.md) - Full feature specification
- [Plan](plan.md) - Implementation plan
- [Data Model](data-model.md) - Entity definitions
- [Contracts](contracts/) - API contracts
- [Research](research.md) - Technical research findings

---

## Support

**Questions?** Open an issue in the CollabIQ repository with tag `010-error-handling`

**Found a bug?** Check error logs in `data/logs/ERROR/` and DLQ entries in `data/dlq/`
