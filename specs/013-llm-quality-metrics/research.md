# Research: LLM Quality Metrics & Tracking

**Feature**: 013-llm-quality-metrics
**Date**: 2025-11-09
**Status**: Complete

## Research Tasks

### 1. Confidence Score Extraction from LLM Adapters

**Question**: How do existing LLM adapters (Gemini, Claude, OpenAI) return confidence scores for the 5 key entities?

**Investigation**:
- Reviewed `src/llm_provider/types.py` - Found `ConfidenceScores` pydantic model with 5 fields:
  - `person`: confidence for person_in_charge (0.0-1.0)
  - `startup`: confidence for startup_name (0.0-1.0)
  - `partner`: confidence for partner_org (0.0-1.0)
  - `details`: confidence for details (0.0-1.0)
  - `date`: confidence for date (0.0-1.0)
- Each adapter (gemini_adapter.py, claude_adapter.py, openai_adapter.py) returns `ExtractedEntities` which includes a `confidence: ConfidenceScores` field
- `ConfidenceScores` model includes validation to ensure 0.0-1.0 range and a `has_low_confidence(threshold)` utility method

**Decision**: Use existing `ConfidenceScores` model from `llm_provider.types` as the source for quality metrics. No modifications needed to adapters - they already return per-field confidence scores.

**Rationale**:
- Existing infrastructure already captures the required data
- Consistent with current extraction workflow
- No breaking changes to adapters required

**Alternatives Considered**:
- Adding new confidence scoring mechanisms → Rejected: existing scores are sufficient and battle-tested
- Calculating confidence post-extraction → Rejected: LLMs already provide confidence during generation

---

### 2. Field Completeness Calculation

**Question**: How should field completeness be calculated when fields are optional?

**Investigation**:
- Reviewed `ExtractedEntities` model in `src/llm_provider/types.py`
- All 5 entity fields are `Optional[str]` - can be None if not extracted
- Need to determine: completeness = (non-null fields) / (total fields)?

**Decision**: Field completeness = (count of non-null fields) / 5 total fields, expressed as percentage (0-100%).

**Rationale**:
- Simple, unambiguous metric
- Aligns with user expectation: "did the LLM extract all 5 entities?"
- Does not penalize legitimate cases where fields don't exist in email (e.g., no date mentioned)

**Alternatives Considered**:
- Required vs optional field distinction → Rejected: spec doesn't distinguish, all 5 entities are tracked equally
- Weighted completeness (e.g., startup_name more important than person) → Rejected: premature optimization, can be added later if needed

---

### 3. Statistical Calculations for Quality Trends

**Question**: How to calculate quality trends (improving/degrading/stable) over time?

**Investigation**:
- Reviewed existing `health_tracker.py` pattern - uses rolling average with smoothing factor (alpha = 0.2) for response times
- Need approach for discrete extractions over time

**Decision**: Use sliding window approach with statistical comparison:
- Track last N extractions (default: 50)
- Compare average confidence of last 25 vs previous 25
- Trend = "improving" if recent avg > previous avg by threshold (e.g., 5%)
- Trend = "degrading" if recent avg < previous avg by threshold
- Trend = "stable" otherwise

**Rationale**:
- Simple statistical approach without complex time-series analysis
- Threshold prevents noise from small fluctuations
- Sliding window auto-adapts to recent behavior
- Consistent with health_tracker's rolling average philosophy

**Alternatives Considered**:
- Linear regression over time → Rejected: overkill for MVP, harder to explain to administrators
- Fixed time windows (e.g., last 7 days) → Rejected: doesn't work with variable extraction volume
- Moving average with exponential smoothing → Rejected: harder to detect sharp degradation

---

### 4. Quality-to-Cost Ratio Calculation

**Question**: How to combine quality metrics with cost metrics to produce actionable "value score"?

**Investigation**:
- Reviewed `src/llm_orchestrator/cost_tracker.py` - tracks `total_cost_usd` and `average_cost_per_email`
- Reviewed `src/llm_orchestrator/types.py` - `CostMetricsSummary` model exists
- Need formula that makes sense to administrators

**Decision**: Value score = (average_confidence_score * 100) / (average_cost_per_email * 1000)

This produces a "quality points per dollar-cent" metric:
- Example: 90% confidence at $0.005/email → 90 / 5 = 18 points per cent
- Higher score = better value
- Normalizes quality (0-100) and cost (in cent-fractions) to comparable scales

**Rationale**:
- Simple division makes value score intuitive
- Scaling factors (100 for quality, 1000 for cost) produce human-readable numbers (typically 10-100 range)
- Directly comparable across providers
- Favors high-quality-low-cost providers

**Alternatives Considered**:
- Quality / cost (no scaling) → Rejected: produces unwieldy decimal numbers (e.g., 180.5)
- (Quality - cost penalty) additive approach → Rejected: mixing percentages and dollars is semantically confusing
- Bucketing approach (high/medium/low value) → Rejected: loses granularity for comparison

---

### 5. Atomic File Writes Pattern

**Question**: What atomic write pattern should be used for quality_metrics.json to prevent corruption?

**Investigation**:
- Reviewed `health_tracker.py` `_save_metrics()` method (lines 364-403)
- Uses tempfile.mkstemp() → write to temp → shutil.move() for atomic rename
- Ensures no partial writes if process crashes

**Decision**: Replicate exact pattern from health_tracker.py:
```python
temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")
with os.fdopen(temp_fd, "w") as f:
    json.dump(data, f, indent=2)
shutil.move(temp_path, self.metrics_file)  # Atomic on POSIX
```

**Rationale**:
- Battle-tested pattern already in codebase
- Prevents corruption from concurrent writes or crashes
- Consistent with existing health and cost tracking
- POSIX atomic rename guarantees (Linux/macOS)

**Alternatives Considered**:
- File locking (fcntl) → Rejected: more complex, not used elsewhere in codebase
- Database transactions → Rejected: introduces database dependency, violates file-based persistence pattern
- Write-ahead log → Rejected: excessive complexity for this use case

---

### 6. Integration with Existing Orchestrator

**Question**: Where in the orchestrator flow should quality metrics be recorded?

**Investigation**:
- Reviewed `src/llm_orchestrator/orchestrator.py` structure
- Orchestrator calls adapters → receives `ExtractedEntities` → returns to caller
- health_tracker.record_success/failure called around adapter invocation
- cost_tracker.record_usage called after successful extraction

**Decision**: Record quality metrics immediately after cost tracking in successful extraction path:
```python
# Existing pattern:
health_tracker.record_success(provider, response_time_ms)
cost_tracker.record_usage(provider, input_tokens, output_tokens)
# NEW:
quality_tracker.record_extraction(provider, extracted_entities, validation_result)
```

**Rationale**:
- Quality metrics require successful extraction (ExtractedEntities object exists)
- Natural ordering: health (availability) → cost (resource usage) → quality (output accuracy)
- Consistent with layered observability model
- Fails gracefully if quality tracking fails (doesn't block extraction)

**Alternatives Considered**:
- Recording quality in adapters themselves → Rejected: mixes concerns, adapters shouldn't know about tracking
- Recording quality before cost → Rejected: illogical ordering (cost is incurred before quality assessment)
- Recording quality in separate background thread → Rejected: unnecessary complexity, adds latency uncertainty

---

## Summary

All technical uncertainties resolved. The feature will:

1. **Leverage existing confidence scores** from ConfidenceScores model (no adapter changes)
2. **Calculate completeness** as (non-null fields / 5) percentage
3. **Detect trends** using 50-extraction sliding window with 25/25 comparison
4. **Compute value score** as (confidence% * 100) / (cost * 1000) for intuitive comparison
5. **Use atomic writes** mirroring health_tracker.py pattern
6. **Integrate** into orchestrator after cost tracking, before returning results

**No NEEDS CLARIFICATION items remain.** Ready for Phase 1 (Design & Contracts).
