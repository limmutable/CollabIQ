# Contract: Health Tracker Interface

**Feature**: Multi-LLM Provider Support
**Branch**: `012-multi-llm`
**Date**: 2025-11-08

## Overview

This contract defines the interface for the HealthTracker, which monitors provider health status, implements circuit breaking, and provides recovery testing. The HealthTracker maintains state across application restarts using file-based persistence.

---

## Interface Definition

### Class: `HealthTracker`

**Module**: `src/llm_adapters/health_tracker.py` (new)

**Purpose**: Track provider health, implement circuit breaking, and detect recovery

**Persistence**: File-based JSON storage in `data/llm_health/health_metrics.json`

---

## Method: `is_healthy`

### Signature

```python
def is_healthy(self, provider_name: str) -> bool:
    pass
```

### Purpose
Check if a provider is currently healthy and available for use.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `provider_name` | str | Yes | Provider identifier | Must be configured provider |

### Return Value

**Type**: `bool`

- `True` if provider is healthy (consecutive_failures < threshold AND circuit_breaker = "closed")
- `False` if provider is unhealthy or circuit breaker is "open"

### Behavior

```python
metrics = self.get_metrics(provider_name)

if metrics.circuit_breaker_state == "open":
    # Check if timeout elapsed → transition to HALF_OPEN
    if time_since_last_failure > circuit_breaker_timeout:
        self._transition_to_half_open(provider_name)
        return True  # Allow limited testing
    return False

if metrics.consecutive_failures >= unhealthy_threshold:
    return False

return True
```

---

## Method: `record_success`

### Signature

```python
def record_success(
    self,
    provider_name: str,
    response_time_ms: float
) -> None:
    pass
```

### Purpose
Record a successful API call and update health metrics.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `provider_name` | str | Yes | Provider identifier | Must be configured provider |
| `response_time_ms` | float | Yes | API response time | >= 0.0 |

### Side Effects

1. Increment `success_count`
2. Reset `consecutive_failures` to 0
3. Update `average_response_time_ms` (rolling average)
4. Set `last_success_timestamp` to current UTC time
5. Set `health_status` to "healthy"
6. Transition circuit breaker:
   - If `circuit_breaker_state == "half_open"` AND enough successes → "closed"
   - Otherwise keep "closed"
7. Persist metrics to JSON file

### Example

```python
health_tracker.record_success(
    provider_name="claude",
    response_time_ms=1834.5
)
```

---

## Method: `record_failure`

### Signature

```python
def record_failure(
    self,
    provider_name: str,
    error_message: str
) -> None:
    pass
```

### Purpose
Record a failed API call and update health metrics.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `provider_name` | str | Yes | Provider identifier | Must be configured provider |
| `error_message` | str | Yes | Error description | Max 500 characters |

### Side Effects

1. Increment `failure_count`
2. Increment `consecutive_failures`
3. Set `last_failure_timestamp` to current UTC time
4. Set `last_error_message` to truncated error message (500 chars max)
5. If `consecutive_failures >= unhealthy_threshold`:
   - Set `health_status` to "unhealthy"
   - Set `circuit_breaker_state` to "open"
6. If `circuit_breaker_state == "half_open"`:
   - Transition back to "open" (recovery failed)
7. Persist metrics to JSON file

### Example

```python
try:
    result = provider.extract_entities(email_text)
except LLMAPIError as e:
    health_tracker.record_failure(
        provider_name="claude",
        error_message=str(e)
    )
```

---

## Method: `get_metrics`

### Signature

```python
def get_metrics(self, provider_name: str) -> ProviderHealthMetrics:
    pass
```

### Purpose
Get current health metrics for a provider.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `provider_name` | str | Yes | Provider identifier | Must be configured provider |

### Return Value

**Type**: `ProviderHealthMetrics` (Pydantic model)

**Structure**:
```python
class ProviderHealthMetrics(BaseModel):
    provider_name: str
    health_status: str                 # "healthy" or "unhealthy"
    success_count: int                # >= 0
    failure_count: int                # >= 0
    consecutive_failures: int         # >= 0
    average_response_time_ms: float   # >= 0.0
    last_success_timestamp: datetime | None
    last_failure_timestamp: datetime | None
    last_error_message: str | None
    circuit_breaker_state: str        # "closed", "open", or "half_open"
    updated_at: datetime
```

### Example

```python
metrics = health_tracker.get_metrics("claude")
print(f"Status: {metrics.health_status}")
print(f"Success rate: {metrics.success_count / (metrics.success_count + metrics.failure_count)}")
```

---

## Method: `get_all_metrics`

### Signature

```python
def get_all_metrics(self) -> dict[str, ProviderHealthMetrics]:
    pass
```

### Purpose
Get health metrics for all configured providers.

### Parameters
None

### Return Value

**Type**: `dict[str, ProviderHealthMetrics]`

Map of provider_name → metrics

### Example

```python
all_metrics = health_tracker.get_all_metrics()
for provider_name, metrics in all_metrics.items():
    print(f"{provider_name}: {metrics.health_status}")
```

---

## Method: `reset_metrics`

### Signature

```python
def reset_metrics(self, provider_name: str) -> None:
    pass
```

### Purpose
Reset health metrics for a provider (for testing or manual recovery).

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `provider_name` | str | Yes | Provider identifier | Must be configured provider |

### Side Effects

1. Reset all counters to 0 (`success_count`, `failure_count`, `consecutive_failures`)
2. Set `health_status` to "healthy"
3. Set `circuit_breaker_state` to "closed"
4. Clear timestamps and error message
5. Persist to JSON file

### Use Case

Manual recovery after fixing provider API issues or for testing purposes.

---

## Constructor

### Signature

```python
def __init__(
    self,
    data_dir: str | Path = "data/llm_health",
    unhealthy_threshold: int = 5,
    circuit_breaker_timeout_seconds: float = 60.0,
    half_open_max_calls: int = 3
):
    pass
```

### Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `data_dir` | str \| Path | No | Directory for health metrics JSON | "data/llm_health" |
| `unhealthy_threshold` | int | No | Consecutive failures before unhealthy | 5 |
| `circuit_breaker_timeout_seconds` | float | No | Time in OPEN before HALF_OPEN | 60.0 |
| `half_open_max_calls` | int | No | Max calls in HALF_OPEN state | 3 |

### Initialization Behavior

1. Create `data_dir` if it doesn't exist
2. Load existing metrics from `{data_dir}/health_metrics.json` if file exists
3. If file doesn't exist, initialize with empty metrics for all providers
4. Validate loaded metrics (check schema, fix corrupted data)

### Example

```python
health_tracker = HealthTracker(
    data_dir="data/llm_health",
    unhealthy_threshold=5,
    circuit_breaker_timeout_seconds=60.0
)
```

---

## Circuit Breaker State Machine

### States

1. **CLOSED** (normal operation)
   - Requests pass through to provider
   - Failures tracked
   - Transition to OPEN after `unhealthy_threshold` consecutive failures

2. **OPEN** (provider unhealthy)
   - All requests immediately fail without calling provider
   - Wait for `circuit_breaker_timeout_seconds`
   - Transition to HALF_OPEN after timeout

3. **HALF_OPEN** (testing recovery)
   - Limited number of requests allowed (`half_open_max_calls`)
   - If requests succeed → transition to CLOSED
   - If requests fail → transition back to OPEN

### State Diagram

```
    [CLOSED]
       ↓ (consecutive_failures >= threshold)
    [OPEN]
       ↓ (timeout elapsed)
    [HALF_OPEN]
       ↓ (success)
    [CLOSED]

    [HALF_OPEN]
       ↓ (failure)
    [OPEN]
```

### Implementation

```python
def _update_circuit_breaker_state(self, provider_name: str, success: bool):
    metrics = self.get_metrics(provider_name)

    if success:
        if metrics.circuit_breaker_state == "half_open":
            # Successful recovery test
            if self._half_open_success_count >= 2:  # 2 successes needed
                self._transition_to_closed(provider_name)
        elif metrics.circuit_breaker_state == "open":
            # Should not happen (OPEN blocks calls)
            pass

    else:  # Failure
        if metrics.consecutive_failures >= self.unhealthy_threshold:
            self._transition_to_open(provider_name)
        elif metrics.circuit_breaker_state == "half_open":
            # Recovery test failed
            self._transition_to_open(provider_name)
```

---

## Persistence

### File Format

**Path**: `data/llm_health/health_metrics.json`

**Structure**:
```json
{
  "gemini": {
    "provider_name": "gemini",
    "health_status": "healthy",
    "success_count": 1500,
    "failure_count": 30,
    "consecutive_failures": 0,
    "average_response_time_ms": 1234.5,
    "last_success_timestamp": "2025-11-08T14:32:18Z",
    "last_failure_timestamp": "2025-11-08T09:15:42Z",
    "last_error_message": "Rate limit exceeded (429)",
    "circuit_breaker_state": "closed",
    "updated_at": "2025-11-08T14:32:18Z"
  },
  "claude": { /* ... */ },
  "openai": { /* ... */ }
}
```

### Atomic Writes

Use atomic file writes to prevent corruption:

```python
import tempfile
import shutil
from pathlib import Path

def _save_metrics(self, metrics: dict[str, ProviderHealthMetrics]):
    metrics_file = Path(self.data_dir) / "health_metrics.json"
    temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix='.tmp')

    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        shutil.move(temp_path, metrics_file)
    except Exception:
        if Path(temp_path).exists():
            Path(temp_path).unlink()
        raise
```

### Load on Startup

```python
def _load_metrics(self) -> dict[str, ProviderHealthMetrics]:
    metrics_file = Path(self.data_dir) / "health_metrics.json"

    if not metrics_file.exists():
        return self._initialize_default_metrics()

    with open(metrics_file, 'r') as f:
        data = json.load(f)

    return {
        name: ProviderHealthMetrics(**metrics)
        for name, metrics in data.items()
    }
```

---

## Testing Requirements

### Unit Tests

**File**: `tests/unit/test_health_tracker.py`

**Required test cases**:

1. `test_is_healthy_returns_true_for_healthy_provider`
```python
def test_is_healthy_returns_true_for_healthy_provider():
    tracker = HealthTracker()
    # Record some successes
    tracker.record_success("gemini", 1000.0)
    assert tracker.is_healthy("gemini") == True
```

2. `test_is_healthy_returns_false_after_threshold_failures`
```python
def test_is_healthy_returns_false_after_threshold_failures():
    tracker = HealthTracker(unhealthy_threshold=3)
    for _ in range(3):
        tracker.record_failure("gemini", "Error")
    assert tracker.is_healthy("gemini") == False
```

3. `test_consecutive_failures_reset_on_success`
```python
def test_consecutive_failures_reset_on_success():
    tracker = HealthTracker()
    tracker.record_failure("gemini", "Error")
    tracker.record_failure("gemini", "Error")
    tracker.record_success("gemini", 1000.0)
    metrics = tracker.get_metrics("gemini")
    assert metrics.consecutive_failures == 0
```

4. `test_circuit_breaker_opens_after_threshold`
```python
def test_circuit_breaker_opens_after_threshold():
    tracker = HealthTracker(unhealthy_threshold=3)
    for _ in range(3):
        tracker.record_failure("gemini", "Error")
    metrics = tracker.get_metrics("gemini")
    assert metrics.circuit_breaker_state == "open"
```

5. `test_circuit_breaker_transitions_to_half_open`
```python
def test_circuit_breaker_transitions_to_half_open():
    tracker = HealthTracker(
        unhealthy_threshold=3,
        circuit_breaker_timeout_seconds=1.0
    )
    # Open circuit
    for _ in range(3):
        tracker.record_failure("gemini", "Error")

    # Wait for timeout
    time.sleep(1.1)

    # Check should transition to HALF_OPEN
    assert tracker.is_healthy("gemini") == True
    metrics = tracker.get_metrics("gemini")
    assert metrics.circuit_breaker_state == "half_open"
```

6. `test_metrics_persist_across_instances`
```python
def test_metrics_persist_across_instances(tmp_path):
    tracker1 = HealthTracker(data_dir=tmp_path)
    tracker1.record_success("gemini", 1000.0)

    tracker2 = HealthTracker(data_dir=tmp_path)
    metrics = tracker2.get_metrics("gemini")
    assert metrics.success_count == 1
```

7. `test_average_response_time_calculation`
```python
def test_average_response_time_calculation():
    tracker = HealthTracker()
    tracker.record_success("gemini", 1000.0)
    tracker.record_success("gemini", 2000.0)
    tracker.record_success("gemini", 3000.0)
    metrics = tracker.get_metrics("gemini")
    assert metrics.average_response_time_ms == 2000.0
```

### Integration Tests

**File**: `tests/integration/test_provider_health_tracking.py`

**Test scenarios**:
- Provider failure → recovery flow
- Circuit breaker state transitions with real timing
- Multi-provider health tracking
- Health metrics display in CLI

---

## Summary

This contract ensures:
- ✅ Consistent health monitoring across all providers
- ✅ Automatic circuit breaking on failures
- ✅ Recovery testing via HALF_OPEN state
- ✅ Persistent state across application restarts
- ✅ Thread-safe file-based storage
- ✅ Configurable thresholds and timeouts
- ✅ Comprehensive testing coverage
