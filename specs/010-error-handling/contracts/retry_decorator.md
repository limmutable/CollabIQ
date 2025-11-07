# Contract: Retry Decorator

**Component**: `src/error_handling/retry.py`
**Purpose**: Provide retry logic with exponential backoff for external API calls

---

## Interface

### `@retry_with_backoff(config: RetryConfig)`

Decorator that wraps functions with automatic retry logic using exponential backoff with jitter.

**Parameters**:
- `config: RetryConfig` - Retry configuration (max attempts, backoff settings, retryable exceptions)

**Returns**:
- Decorated function with retry behavior

**Raises**:
- Original exception after max retry attempts exhausted
- `CircuitBreakerOpen` if circuit breaker is open

---

## Contract Specifications

### 1. **Successful Execution (No Retry Needed)**

**Given**: Function succeeds on first attempt
**When**: Decorated function is called
**Then**:
- Function executes once
- Result is returned immediately
- No retry attempts made
- Circuit breaker records success

**Test**:
```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails():
    return ["email1", "email2"]

result = fetch_emails()
assert result == ["email1", "email2"]
assert attempt_count == 1
```

---

### 2. **Transient Failure Recovers (Retry Succeeds)**

**Given**: Function fails twice, then succeeds on third attempt
**When**: Decorated function is called
**Then**:
- Function executes 3 times total
- Exponential backoff applied between attempts (1s, 2s)
- Success result returned on third attempt
- Circuit breaker records success (failure count reset)

**Test**:
```python
attempt = 0

@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails_flaky():
    nonlocal attempt
    attempt += 1
    if attempt < 3:
        raise socket.timeout("Connection timeout")
    return ["email1"]

result = fetch_emails_flaky()
assert result == ["email1"]
assert attempt == 3
assert wait_times == [~1s, ~2s]  # With jitter variance
```

---

### 3. **Exhausted Retries (All Attempts Fail)**

**Given**: Function fails on all 3 attempts
**When**: Decorated function is called
**Then**:
- Function executes 3 times (max_attempts)
- Exponential backoff applied between attempts
- Original exception re-raised after final attempt
- Circuit breaker records failure (increments failure_count)
- ErrorRecord logged for each attempt

**Test**:
```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails_always_fails():
    raise socket.timeout("Connection timeout")

with pytest.raises(socket.timeout):
    fetch_emails_always_fails()

assert attempt_count == 3
assert circuit_breaker.failure_count == 3
```

---

### 4. **Rate Limit Handling (Respect Retry-After)**

**Given**: API returns 429 with `Retry-After: 5` header
**When**: Decorated function is called
**Then**:
- Function executes, raises rate limit error
- Retry waits 5 seconds (from Retry-After header, not backoff)
- Function retries after wait
- If succeeds, returns result

**Test**:
```python
attempt = 0

@retry_with_backoff(NOTION_RETRY_CONFIG)
def write_to_notion():
    nonlocal attempt
    attempt += 1
    if attempt == 1:
        raise APIResponseError(status_code=429, headers={"Retry-After": "5"})
    return {"id": "page_123"}

result = write_to_notion()
assert result == {"id": "page_123"}
assert wait_times[0] == 5.0  # Respected Retry-After
```

---

### 5. **Non-Retryable Error (Fail Fast)**

**Given**: Function raises non-retryable exception (e.g., 401 auth error)
**When**: Decorated function is called
**Then**:
- Function executes once
- Exception raised immediately (no retry)
- Circuit breaker records failure
- ErrorRecord logged as CRITICAL category

**Test**:
```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails_auth_error():
    raise HttpError(resp={"status": "401"}, content=b"Unauthorized")

with pytest.raises(HttpError) as exc_info:
    fetch_emails_auth_error()

assert exc_info.value.resp.status == 401
assert attempt_count == 1  # No retries
assert circuit_breaker.failure_count == 1
```

---

### 6. **Circuit Breaker Open (Reject Request)**

**Given**: Circuit breaker is OPEN (5 consecutive failures)
**When**: Decorated function is called
**Then**:
- Function does NOT execute (no HTTP call)
- `CircuitBreakerOpen` exception raised immediately
- DLQ entry created for failed request
- ErrorRecord logged

**Test**:
```python
# Trigger circuit breaker to open
for _ in range(5):
    try:
        fetch_emails_always_fails()
    except socket.timeout:
        pass

assert circuit_breaker.state == CircuitState.OPEN

# Next request rejected
with pytest.raises(CircuitBreakerOpen):
    fetch_emails()

assert actual_function_call_count == 0  # Function never executed
```

---

### 7. **Exponential Backoff with Jitter**

**Given**: Function fails on attempts 1 and 2
**When**: Decorated function is called
**Then**:
- Wait times increase exponentially: 2^0, 2^1, 2^2 (base)
- Jitter added: random(0, 2) seconds
- Wait times capped at backoff_max (10s)
- Total wait time ~15 seconds (meets SC-004: <10s MTTR per retry)

**Test**:
```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails_with_retries():
    if attempt < 3:
        raise socket.timeout()
    return []

# Expected backoff schedule (with jitter range):
# Attempt 1: fails → wait 1-3s (2^0 + jitter)
# Attempt 2: fails → wait 2-4s (2^1 + jitter)
# Attempt 3: succeeds

assert 1.0 <= wait_times[0] <= 3.0
assert 2.0 <= wait_times[1] <= 4.0
```

---

### 8. **Async Function Support**

**Given**: Decorated function is async
**When**: Function is awaited
**Then**:
- Retry logic works correctly with async/await
- Backoff waits use `asyncio.sleep()` (not `time.sleep()`)
- Circuit breaker state updates correctly

**Test**:
```python
@retry_with_backoff(NOTION_RETRY_CONFIG)
async def async_write_to_notion():
    if attempt == 1:
        raise ConnectionError()
    return {"id": "page_123"}

result = await async_write_to_notion()
assert result == {"id": "page_123"}
assert attempt_count == 2
```

---

### 9. **Logging Integration**

**Given**: Function fails and retries
**When**: Each retry attempt occurs
**Then**:
- ErrorRecord logged for each failure
- Log includes: email_id, operation, attempt_number, error_type
- Final failure (after exhausted retries) logged as ERROR severity

**Test**:
```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails_with_logging():
    raise socket.timeout()

with pytest.raises(socket.timeout):
    fetch_emails_with_logging()

# Check logs
assert len(error_logs) == 3
assert error_logs[0]["context"]["attempt_number"] == 1
assert error_logs[1]["context"]["attempt_number"] == 2
assert error_logs[2]["severity"] == "ERROR"  # Final failure
```

---

## Error Handling

| Scenario | Exception Raised | Retry? | DLQ? | Circuit Breaker |
|----------|-----------------|--------|------|----------------|
| Network timeout | `socket.timeout` | Yes (3x) | After exhausted | Increment failure |
| Rate limit | `APIResponseError(429)` | Yes (respect Retry-After) | After exhausted | No (rate limit != failure) |
| Auth error | `HttpError(401)` | No | Immediately | Increment failure |
| Server error | `HttpError(5xx)` | Yes (3x) | After exhausted | Increment failure |
| Circuit open | `CircuitBreakerOpen` | No | Immediately | N/A (already open) |
| Validation error | `ValidationError` | No | No (log only) | No |

---

## Configuration Contracts

### Per-API Retry Configs

**Gmail**:
- `max_attempts=3`, `timeout=30s`, retries: `socket.timeout`, `HttpError(5xx)`, `HttpError(429)`

**Gemini**:
- `max_attempts=3`, `timeout=60s`, retries: `ResourceExhausted`, `DeadlineExceeded`

**Notion**:
- `max_attempts=3`, `timeout=30s`, retries: `APIResponseError(5xx)`, `APIResponseError(429)`

**Infisical**:
- `max_attempts=2`, `timeout=10s`, retries: `socket.timeout`, `ConnectionError`
- Special: Falls back to `.env` if all retries fail

---

## Performance Contracts

- **SC-004**: MTTR for transient failures < 10 seconds per retry
  - Exponential backoff max: 10s
  - Total retry duration: ~25s for 3 attempts (acceptable for async processing)

- **SC-008**: Continue processing next email < 1 second after non-critical error
  - Circuit breaker decision: < 1ms (in-memory check)
  - No retry delay for permanent errors

---

## Dependencies

- `tenacity` library (already in project)
- `CircuitBreaker` from `src/error_handling/circuit_breaker.py`
- `ErrorClassifier` from `src/error_handling/error_classifier.py`
- `StructuredLogger` from `src/error_handling/structured_logger.py`

---

## Test Coverage Requirements

- ✅ Unit tests for all 9 contract scenarios
- ✅ Integration tests with real API mocks
- ✅ Property-based tests for backoff timing variance (jitter)
- ✅ Performance tests to verify MTTR < 10s
