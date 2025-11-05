# Contract: PerformanceTracker

**Module**: `src/e2e_test/performance_tracker.py`
**Purpose**: Track timing and resource usage for pipeline stages

## Interface

### Method: `track_stage`

**Description**: Context manager for tracking performance of a pipeline stage

**Signature**:
```python
@contextmanager
def track_stage(
    run_id: str,
    email_id: str,
    stage: str
) -> Generator[PerformanceContext, None, None]
```

**Usage**:
```python
tracker = PerformanceTracker(output_dir="data/e2e_test")

with tracker.track_stage("2025-11-04T14:30:00", "msg_001", "extraction") as ctx:
    result = gemini_adapter.extract(email_body)
    ctx.record_api_call("gemini", tokens={"input": 1250, "output": 180})

# Performance metric automatically written after context exits
```

**Behavior**:
1. Record `start_time` when entering context
2. Yield `PerformanceContext` object for recording API calls/tokens
3. Record `end_time` when exiting context
4. Calculate `duration_seconds = end_time - start_time`
5. Create `PerformanceMetric` with all collected data
6. Persist metric to `{output_dir}/metrics/{run_id}/{email_id}_{stage}.json`

**Success Criteria**:
- Timing accurate to millisecond precision (using `time.perf_counter()`)
- API calls and token usage captured correctly
- Metric persisted even if exception occurs in context

---

### Method: `get_stage_statistics`

**Description**: Get aggregated performance statistics for a stage across all emails in a test run

**Signature**:
```python
def get_stage_statistics(run_id: str, stage: str) -> dict
```

**Returns**:
```python
{
    "stage": "extraction",
    "email_count": 50,
    "average_duration": 3.45,
    "median_duration": 3.20,
    "p95_duration": 5.80,
    "p99_duration": 7.20,
    "min_duration": 1.80,
    "max_duration": 8.50,
    "total_api_calls": {"gemini": 50, "notion": 0},
    "total_tokens": {"input": 62500, "output": 9000},
    "success_rate": 0.98
}
```

**Behavior**:
1. Load all Performance Metrics for `{run_id}` and `{stage}`
2. Calculate aggregate statistics (mean, median, percentiles)
3. Sum API calls and token usage
4. Calculate success rate (successful metrics / total metrics)
5. Return dictionary with statistics

---

### Method: `export_metrics_csv`

**Description**: Export performance metrics to CSV for analysis in spreadsheets

**Signature**:
```python
def export_metrics_csv(run_id: str, output_path: str) -> None
```

**Behavior**:
1. Load all Performance Metrics for `{run_id}`
2. Flatten nested data (API calls, tokens) into columns
3. Write CSV with headers: run_id, email_id, stage, duration_seconds, gemini_calls, gemini_input_tokens, gemini_output_tokens, status
4. Save to `output_path`

---

## Dependencies

- `data_model.PerformanceMetric`: Pydantic model for metrics
- `time.perf_counter()`: High-resolution timing
- `statistics` module: Calculate median, percentiles

---

## Contract Tests

**Test 1: track_stage records timing**
- **Given**: Pipeline stage executes for 3 seconds
- **When**: `with tracker.track_stage(...) as ctx: time.sleep(3)`
- **Then**: Metric has `duration_seconds ≈ 3.0` (within 0.1s tolerance)

**Test 2: track_stage records API calls**
- **Given**: Stage makes 1 Gemini API call
- **When**: `ctx.record_api_call("gemini", tokens={...})`
- **Then**: Metric has `api_calls={"gemini": 1}` and `gemini_tokens={...}`

**Test 3: get_stage_statistics aggregates correctly**
- **Given**: 50 metrics with durations [1.0, 2.0, ..., 50.0]
- **When**: `get_stage_statistics(run_id, "extraction")`
- **Then**: Returns `average_duration=25.5, median_duration=25.5, p95_duration=47.75`
