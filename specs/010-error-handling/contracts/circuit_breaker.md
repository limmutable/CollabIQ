# Contract: Circuit Breaker

**Component**: `src/error_handling/circuit_breaker.py`
**Purpose**: Prevent cascading failures by stopping requests to failing services

---

## Interface

### `class CircuitBreaker`

Implements circuit breaker pattern with CLOSED → OPEN → HALF_OPEN state machine.

**Constructor**:
```python
def __init__(
    self,
    service_name: str,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 60.0
)
```

**Methods**:
- `call(func, *args, **kwargs)` - Execute function through circuit breaker
- `should_allow_request() -> bool` - Check if request should be allowed
- `record_success()` - Record successful request
- `record_failure()` - Record failed request
- `get_state() -> CircuitState` - Get current circuit state

---

## Contract Specifications

### 1. **Normal Operation (CLOSED State)**

**Given**: Circuit breaker is CLOSED (initial state)
**When**: Request is made
**Then**:
- Request passes through to underlying function
- Function executes normally
- Result returned to caller
- Failure count remains 0 (assuming success)

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5)
result = cb.call(fetch_emails)

assert result == ["email1", "email2"]
assert cb.get_state() == CircuitState.CLOSED
assert cb.failure_count == 0
```

---

### 2. **Record Consecutive Failures (CLOSED → OPEN)**

**Given**: Circuit breaker is CLOSED with 4 failures
**When**: 5th consecutive failure occurs
**Then**:
- Circuit transitions to OPEN state
- `open_timestamp` recorded
- All subsequent requests rejected immediately (no function execution)
- `CircuitBreakerOpen` exception raised

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5)

# Trigger 5 consecutive failures
for i in range(5):
    try:
        cb.call(lambda: raise_exception(socket.timeout()))
    except socket.timeout:
        pass

assert cb.get_state() == CircuitState.OPEN
assert cb.failure_count == 5
assert cb.open_timestamp is not None

# Next request rejected
with pytest.raises(CircuitBreakerOpen):
    cb.call(fetch_emails)

assert fetch_emails_call_count == 0  # Function never executed
```

---

### 3. **Timeout Elapsed (OPEN → HALF_OPEN)**

**Given**: Circuit breaker is OPEN for 60 seconds
**When**: New request arrives after timeout
**Then**:
- Circuit transitions to HALF_OPEN state
- Test request allowed through
- If test succeeds, increment success_count
- If test fails, transition back to OPEN

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5, timeout=60.0)

# Open circuit
for _ in range(5):
    try:
        cb.call(lambda: raise_exception(socket.timeout()))
    except socket.timeout:
        pass

assert cb.get_state() == CircuitState.OPEN

# Wait for timeout
time.sleep(61)

# Next request transitions to HALF_OPEN
result = cb.call(fetch_emails)
assert cb.get_state() == CircuitState.HALF_OPEN
assert result == ["email1"]
```

---

### 4. **Recovery (HALF_OPEN → CLOSED)**

**Given**: Circuit breaker is HALF_OPEN with 1 success
**When**: 2nd consecutive success occurs
**Then**:
- Circuit transitions to CLOSED state
- success_count reset to 0
- failure_count reset to 0
- Normal operation resumes

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5, success_threshold=2)

# Manually set to HALF_OPEN (after timeout elapsed)
cb.state = CircuitState.HALF_OPEN

# First success
cb.call(fetch_emails)
assert cb.get_state() == CircuitState.HALF_OPEN
assert cb.success_count == 1

# Second success → CLOSED
cb.call(fetch_emails)
assert cb.get_state() == CircuitState.CLOSED
assert cb.success_count == 0
assert cb.failure_count == 0
```

---

### 5. **Failed Test Request (HALF_OPEN → OPEN)**

**Given**: Circuit breaker is HALF_OPEN (testing recovery)
**When**: Test request fails
**Then**:
- Circuit transitions back to OPEN state
- `open_timestamp` updated to current time
- success_count reset to 0
- Must wait another 60 seconds before next test

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5, timeout=60.0)

# Manually set to HALF_OPEN
cb.state = CircuitState.HALF_OPEN

# Test request fails
try:
    cb.call(lambda: raise_exception(socket.timeout()))
except socket.timeout:
    pass

assert cb.get_state() == CircuitState.OPEN
assert cb.success_count == 0
old_timestamp = cb.open_timestamp

# Next request rejected
with pytest.raises(CircuitBreakerOpen):
    cb.call(fetch_emails)

assert cb.open_timestamp > old_timestamp  # Updated
```

---

### 6. **Partial Failures Don't Trigger Opening**

**Given**: Circuit breaker has 4 failures, then 1 success
**When**: Request succeeds
**Then**:
- failure_count reset to 0
- Circuit remains CLOSED
- Does NOT transition to OPEN

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5)

# 4 failures
for _ in range(4):
    try:
        cb.call(lambda: raise_exception(socket.timeout()))
    except socket.timeout:
        pass

assert cb.failure_count == 4

# 1 success resets counter
cb.call(fetch_emails)
assert cb.failure_count == 0
assert cb.get_state() == CircuitState.CLOSED
```

---

### 7. **Per-Service Isolation**

**Given**: Multiple circuit breakers for different services
**When**: One service fails repeatedly
**Then**:
- Only that service's circuit breaker opens
- Other services continue operating normally

**Test**:
```python
gmail_cb = CircuitBreaker("gmail", failure_threshold=5)
notion_cb = CircuitBreaker("notion", failure_threshold=5)

# Gmail fails 5 times
for _ in range(5):
    try:
        gmail_cb.call(lambda: raise_exception(socket.timeout()))
    except socket.timeout:
        pass

assert gmail_cb.get_state() == CircuitState.OPEN
assert notion_cb.get_state() == CircuitState.CLOSED

# Notion still works
result = notion_cb.call(write_to_notion)
assert result == {"id": "page_123"}
```

---

### 8. **Fast Failure Detection (< 1ms decision)**

**Given**: Circuit breaker is OPEN
**When**: New request arrives
**Then**:
- `should_allow_request()` returns False in < 1ms
- No network call made (fail fast)
- Meets SC-008 performance requirement

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5)

# Open circuit
for _ in range(5):
    try:
        cb.call(lambda: raise_exception(socket.timeout()))
    except socket.timeout:
        pass

# Measure decision time
start = time.perf_counter()
allowed = cb.should_allow_request()
elapsed = time.perf_counter() - start

assert not allowed
assert elapsed < 0.001  # < 1ms
```

---

### 9. **State Transitions Logged**

**Given**: Circuit breaker changes state
**When**: State transition occurs
**Then**:
- ErrorRecord logged with state change details
- Log includes: service_name, old_state, new_state, failure_count

**Test**:
```python
cb = CircuitBreaker("gmail", failure_threshold=5)

# Trigger state change
for _ in range(5):
    try:
        cb.call(lambda: raise_exception(socket.timeout()))
    except socket.timeout:
        pass

# Check logs
state_change_logs = [log for log in error_logs if log["message"].startswith("Circuit breaker")]
assert len(state_change_logs) == 1
assert state_change_logs[0]["context"]["old_state"] == "CLOSED"
assert state_change_logs[0]["context"]["new_state"] == "OPEN"
assert state_change_logs[0]["context"]["failure_count"] == 5
```

---

## State Transition Matrix

| Current State | Event | Next State | Action |
|--------------|-------|------------|--------|
| CLOSED | success | CLOSED | failure_count = 0 |
| CLOSED | failure (count < threshold) | CLOSED | failure_count += 1 |
| CLOSED | failure (count >= threshold) | OPEN | Record open_timestamp |
| OPEN | request before timeout | OPEN | Reject with CircuitBreakerOpen |
| OPEN | request after timeout | HALF_OPEN | Allow test request |
| HALF_OPEN | success (count < threshold) | HALF_OPEN | success_count += 1 |
| HALF_OPEN | success (count >= threshold) | CLOSED | Reset counters |
| HALF_OPEN | failure | OPEN | Update open_timestamp |

---

## Error Handling

| Scenario | Circuit Action | Exception Raised |
|----------|---------------|-----------------|
| Circuit CLOSED, function succeeds | Record success | None |
| Circuit CLOSED, function fails (< threshold) | Record failure | Original exception |
| Circuit CLOSED, function fails (>= threshold) | Transition to OPEN | Original exception |
| Circuit OPEN | Reject request | `CircuitBreakerOpen` |
| Circuit HALF_OPEN, test succeeds | Record success | None |
| Circuit HALF_OPEN, test fails | Transition to OPEN | Original exception |

---

## Configuration Contracts

### Per-Service Thresholds

**Gmail, Gemini, Notion** (critical services):
- `failure_threshold=5` (Netflix Hystrix standard)
- `success_threshold=2` (conservative recovery)
- `timeout=60s` (AWS default)

**Infisical** (has .env fallback):
- `failure_threshold=3` (fail faster)
- `success_threshold=2`
- `timeout=30s` (shorter recovery window)

---

## Performance Contracts

- **SC-006**: Circuit breaker stops requests after 5 consecutive failures
  - ✅ Validated by Contract #2

- **SC-008**: Continue processing next email < 1 second after non-critical error
  - ✅ `should_allow_request()` decision < 1ms (Contract #8)

---

## Integration with Retry Layer

```python
@retry_with_backoff(GMAIL_RETRY_CONFIG)
def fetch_emails_with_circuit_breaker():
    # Circuit breaker check BEFORE retry logic
    if not gmail_circuit_breaker.should_allow_request():
        raise CircuitBreakerOpen(service_name="gmail")

    # If allowed, proceed with actual API call
    try:
        result = gmail_api.fetch()
        gmail_circuit_breaker.record_success()
        return result
    except Exception as e:
        gmail_circuit_breaker.record_failure()
        raise
```

**Order of Operations**:
1. Circuit Breaker: Check if request allowed
2. Retry Logic: Execute with retries (if circuit allows)
3. Circuit Breaker: Update state based on result

---

## Dependencies

- `CircuitBreakerState` dataclass from `data-model.md`
- `StructuredLogger` for logging state transitions
- `DLQManager` for enqueueing rejected requests

---

## Test Coverage Requirements

- ✅ Unit tests for all 9 contract scenarios
- ✅ State transition matrix tests (all paths)
- ✅ Performance tests to verify < 1ms decision time
- ✅ Integration tests with retry decorator
- ✅ Multi-service isolation tests
