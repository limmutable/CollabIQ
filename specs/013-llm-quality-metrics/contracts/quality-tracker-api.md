# API Contract: QualityTracker

**Module**: `src/llm_orchestrator/quality_tracker.py`
**Version**: 1.0.0
**Date**: 2025-11-09

## Overview

The `QualityTracker` class provides quality metrics tracking for LLM providers, following the established pattern of `HealthTracker` and `CostTracker`. It records extraction quality metrics, calculates aggregate statistics, and enables cross-provider comparison.

---

## Class: QualityTracker

### Constructor

```python
def __init__(
    self,
    data_dir: str | Path = "data/llm_health",
    evaluation_window_size: int = 50,
) -> None:
    """Initialize QualityTracker.

    Args:
        data_dir: Directory for quality metrics JSON storage
        evaluation_window_size: Number of recent extractions for trend calculation (default: 50)

    Side Effects:
        - Creates data_dir if it doesn't exist
        - Loads existing metrics from quality_metrics.json if present
        - Initializes empty metrics dict if file doesn't exist
    """
```

**Preconditions**:
- `data_dir` must be a valid directory path or creatable path
- `evaluation_window_size` must be ≥10

**Postconditions**:
- `self.data_dir` exists as a directory
- `self.metrics_file` points to `{data_dir}/quality_metrics.json`
- `self.metrics` contains loaded or empty provider summaries

---

### Method: record_extraction

```python
def record_extraction(
    self,
    provider_name: str,
    extracted_entities: ExtractedEntities,
    validation_passed: bool,
    validation_failure_reasons: list[str] | None = None,
) -> None:
    """Record quality metrics for a single extraction attempt.

    Args:
        provider_name: Provider identifier ("gemini", "claude", "openai")
        extracted_entities: Extraction result with confidence scores
        validation_passed: True if extraction passed validation
        validation_failure_reasons: List of failure reasons if validation failed

    Side Effects:
        - Updates provider quality summary statistics
        - Increments total_extractions counter
        - Recalculates averages, std deviation, and trend
        - Persists updated metrics to quality_metrics.json atomically

    Raises:
        ValueError: If provider_name not in ["gemini", "claude", "openai"]
        ValueError: If validation_passed is False but validation_failure_reasons is None/empty
    """
```

**Preconditions**:
- `provider_name` must be valid provider identifier
- `extracted_entities.confidence` must exist and contain valid ConfidenceScores
- If `validation_passed` is False, `validation_failure_reasons` must be non-empty list

**Postconditions**:
- Provider summary updated with new extraction data
- All aggregate statistics recalculated
- Metrics persisted to disk
- Quality trend updated if sufficient data (≥50 extractions)

**Example**:
```python
tracker = QualityTracker()
tracker.record_extraction(
    provider_name="claude",
    extracted_entities=entities,  # Has confidence scores
    validation_passed=True,
    validation_failure_reasons=None,
)
```

---

### Method: get_metrics

```python
def get_metrics(self, provider_name: str) -> ProviderQualitySummary:
    """Get current quality metrics for a provider.

    Args:
        provider_name: Provider identifier ("gemini", "claude", "openai")

    Returns:
        ProviderQualitySummary for the specified provider

    Side Effects:
        - Initializes default metrics if provider not yet tracked
        - Persists new default metrics to disk if created
    """
```

**Preconditions**:
- `provider_name` must be valid provider identifier

**Postconditions**:
- Returns existing or newly-initialized ProviderQualitySummary
- If new provider, metrics file updated with default summary

**Example**:
```python
tracker = QualityTracker()
summary = tracker.get_metrics("gemini")
print(f"Average confidence: {summary.average_overall_confidence:.2f}")
```

---

### Method: get_all_metrics

```python
def get_all_metrics(self) -> dict[str, ProviderQualitySummary]:
    """Get quality metrics for all tracked providers.

    Returns:
        Dictionary mapping provider_name → ProviderQualitySummary

    Side Effects:
        None (returns copy of internal state)
    """
```

**Preconditions**: None

**Postconditions**:
- Returns shallow copy of metrics dict
- Original metrics remain unmodified

**Example**:
```python
tracker = QualityTracker()
all_metrics = tracker.get_all_metrics()
for provider, summary in all_metrics.items():
    print(f"{provider}: {summary.validation_success_rate:.1f}% success")
```

---

### Method: compare_providers

```python
def compare_providers(
    self,
    cost_tracker: CostTracker,
) -> ProviderQualityComparison:
    """Generate cross-provider quality comparison with cost analysis.

    Args:
        cost_tracker: CostTracker instance for cost metric lookup

    Returns:
        ProviderQualityComparison with rankings and recommendations

    Side Effects:
        None (read-only operation)

    Raises:
        ValueError: If no providers have metrics tracked
    """
```

**Preconditions**:
- At least one provider must have quality metrics
- `cost_tracker` must have cost metrics for providers being compared

**Postconditions**:
- Returns comparison with provider rankings by quality and value
- Recommended provider identified based on quality-to-cost ratio
- Human-readable recommendation reason generated

**Example**:
```python
quality_tracker = QualityTracker()
cost_tracker = CostTracker()
comparison = quality_tracker.compare_providers(cost_tracker)
print(f"Recommended: {comparison.recommended_provider}")
print(f"Reason: {comparison.recommendation_reason}")
```

---

### Method: check_quality_threshold

```python
def check_quality_threshold(
    self,
    provider_name: str,
    threshold_config: QualityThresholdConfig,
) -> tuple[bool, list[str]]:
    """Check if provider meets quality thresholds.

    Args:
        provider_name: Provider identifier to check
        threshold_config: Quality threshold configuration

    Returns:
        Tuple of (passes: bool, failures: list[str])
        - passes: True if all thresholds met, False otherwise
        - failures: List of specific threshold failures (empty if passes is True)

    Side Effects:
        None (read-only operation)

    Raises:
        ValueError: If provider has no metrics (total_extractions == 0)
    """
```

**Preconditions**:
- Provider must have at least 1 extraction tracked
- `threshold_config.enabled` must be True

**Postconditions**:
- Returns pass/fail status with specific failure reasons
- No state modified

**Example**:
```python
tracker = QualityTracker()
config = QualityThresholdConfig(
    threshold_name="production",
    minimum_average_confidence=0.85,
    minimum_field_completeness=90.0,
    maximum_validation_failure_rate=5.0,
)
passes, failures = tracker.check_quality_threshold("claude", config)
if not passes:
    print(f"Quality issues: {', '.join(failures)}")
```

---

### Method: reset_metrics

```python
def reset_metrics(self, provider_name: str) -> None:
    """Reset quality metrics for a provider (for testing or manual reset).

    Args:
        provider_name: Provider identifier to reset

    Side Effects:
        - Resets all counters to 0
        - Resets all averages to 0.0
        - Sets quality_trend to "stable"
        - Updates updated_at timestamp
        - Persists reset metrics to disk
    """
```

**Preconditions**:
- `provider_name` must be valid provider identifier

**Postconditions**:
- Provider metrics reset to default state
- Metrics file updated atomically

**Example**:
```python
tracker = QualityTracker()
tracker.reset_metrics("gemini")  # Clean slate for testing
```

---

## Internal Methods (Private)

### _calculate_trend

```python
def _calculate_trend(
    self,
    provider_name: str,
    recent_extractions: list[QualityMetricsRecord],
) -> str:
    """Calculate quality trend (improving/stable/degrading).

    Args:
        provider_name: Provider identifier
        recent_extractions: List of recent extraction records (last 50)

    Returns:
        "improving", "stable", or "degrading"

    Algorithm:
        1. Require at least 50 extractions for trend calculation
        2. Split into two windows: recent 25 vs previous 25
        3. Compare average overall_confidence of both windows
        4. Return "improving" if recent > previous by ≥5%
        5. Return "degrading" if recent < previous by ≥5%
        6. Return "stable" otherwise
    """
```

---

### _calculate_statistics

```python
def _calculate_statistics(
    self,
    extractions: list[QualityMetricsRecord],
) -> tuple[float, float, dict[str, float]]:
    """Calculate aggregate statistics from extraction records.

    Args:
        extractions: List of extraction records to analyze

    Returns:
        Tuple of (mean_confidence, std_deviation, per_field_averages)

    Algorithm:
        1. Calculate mean of overall_confidence values
        2. Calculate standard deviation of overall_confidence
        3. Calculate per-field confidence averages (person, startup, partner, details, date)
    """
```

---

### _load_metrics

```python
def _load_metrics(self) -> dict[str, ProviderQualitySummary]:
    """Load quality metrics from JSON file.

    Returns:
        Dictionary mapping provider_name → ProviderQualitySummary

    Side Effects:
        - Logs info message if file doesn't exist
        - Logs error if file is corrupted (returns empty dict)

    Error Handling:
        - Returns {} if file doesn't exist
        - Returns {} if JSON is malformed or validation fails
        - Converts ISO timestamp strings to datetime objects
    """
```

---

### _save_metrics

```python
def _save_metrics(self) -> None:
    """Save quality metrics to JSON file using atomic write.

    Side Effects:
        - Creates temp file in data_dir
        - Writes JSON with indent=2
        - Atomically renames temp file to quality_metrics.json
        - Converts datetime objects to ISO format strings

    Error Handling:
        - Cleans up temp file on write failure
        - Logs error and raises exception on atomic rename failure
        - Ensures POSIX atomic rename semantics (Linux/macOS)
    """
```

---

## Error Handling

### Expected Exceptions

| Exception | Condition | Caller Responsibility |
|-----------|-----------|----------------------|
| `ValueError` | Invalid provider_name | Validate provider before calling |
| `ValueError` | validation_passed=False without reasons | Always provide failure reasons |
| `ValueError` | No metrics for comparison | Check metrics exist before comparing |
| `ValueError` | Provider has 0 extractions in threshold check | Ensure extractions recorded before checking |
| `IOError` | File system errors during persistence | Handle gracefully, log error, retry |

### Error Recovery

- **File corruption**: Logs error, returns empty metrics, allows system to continue
- **Atomic write failure**: Cleans up temp file, raises exception (caller handles retry)
- **Invalid data**: Validates on load, skips invalid records, logs warning

---

## Performance Characteristics

| Operation | Time Complexity | Space Complexity | Notes |
|-----------|----------------|------------------|-------|
| `record_extraction` | O(1) | O(1) | Incremental statistics update |
| `get_metrics` | O(1) | O(1) | Dict lookup |
| `get_all_metrics` | O(n) | O(n) | n = number of providers (3) |
| `compare_providers` | O(n) | O(n) | n = number of providers (3) |
| `check_quality_threshold` | O(1) | O(1) | Simple comparisons |
| `_load_metrics` | O(n*m) | O(n*m) | n = providers, m = JSON parse |
| `_save_metrics` | O(n*m) | O(n*m) | n = providers, m = JSON serialize |

**File Size Growth**: O(1) - metrics file size constant (only summaries stored, not individual records)

---

## Thread Safety

**Not thread-safe by design** - follows same pattern as HealthTracker and CostTracker:
- Atomic file writes prevent corruption
- Concurrent writes may lose updates (last-write-wins)
- For concurrent environments, external synchronization required (file locking or queue)

**Note**: Current CollabIQ architecture is single-threaded (synchronous email processing), so thread safety is not a concern for MVP.

---

## Integration Points

### With LLM Orchestrator

```python
# In orchestrator.py, after successful extraction:
health_tracker.record_success(provider, response_time_ms)
cost_tracker.record_usage(provider, input_tokens, output_tokens)
# NEW:
validation_result = validate_extraction(entities)
quality_tracker.record_extraction(
    provider,
    entities,
    validation_result.passed,
    validation_result.failure_reasons,
)
```

### With Admin CLI

```python
# In cli/commands/status.py:
@app.command()
def status():
    """Show system status including quality metrics."""
    health_tracker = HealthTracker()
    cost_tracker = CostTracker()
    quality_tracker = QualityTracker()  # NEW

    # Display quality metrics alongside health and cost
    comparison = quality_tracker.compare_providers(cost_tracker)
    console.print(f"Recommended provider: {comparison.recommended_provider}")
```

---

## Testing Contract

### Contract Tests (Required)

1. **test_record_extraction_updates_summary**: Verify aggregates updated correctly
2. **test_get_metrics_creates_default**: Verify new provider initialization
3. **test_compare_providers_ranking**: Verify correct ranking by quality and value
4. **test_check_threshold_passes**: Verify threshold passing logic
5. **test_check_threshold_failures**: Verify failure reason generation
6. **test_atomic_write_no_corruption**: Verify file integrity after concurrent writes
7. **test_trend_calculation_improving**: Verify trend detection (recent > previous)
8. **test_trend_calculation_degrading**: Verify trend detection (recent < previous)
9. **test_trend_calculation_stable**: Verify trend detection (difference < 5%)

### Integration Tests (Required)

1. **test_end_to_end_quality_tracking**: Extract email → record quality → retrieve summary
2. **test_quality_based_routing**: Configure thresholds → route based on quality metrics

---

## Version History

- **1.0.0** (2025-11-09): Initial API contract definition
