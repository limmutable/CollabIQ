# Data Model: LLM Quality Metrics & Tracking

**Feature**: 013-llm-quality-metrics
**Date**: 2025-11-09

## Overview

This document defines the data structures for tracking LLM extraction quality metrics. The models follow the established pattern of health_tracker.py and cost_tracker.py, using Pydantic for validation and file-based JSON persistence.

## Core Entities

### QualityMetricsRecord

Represents quality measurements for a single email extraction attempt.

**Attributes**:
- `email_id` (str): Unique email identifier (reference to original email)
- `provider_name` (str): Provider identifier ("gemini", "claude", "openai")
- `extraction_timestamp` (datetime): UTC timestamp when extraction occurred
- `per_field_confidence` (dict[str, float]): Confidence scores for the 5 key entities
  - `person` (float): 0.0-1.0 confidence for person_in_charge
  - `startup` (float): 0.0-1.0 confidence for startup_name
  - `partner` (float): 0.0-1.0 confidence for partner_org
  - `details` (float): 0.0-1.0 confidence for details
  - `date` (float): 0.0-1.0 confidence for date
- `overall_confidence` (float): Average of the 5 per-field confidence scores (0.0-1.0)
- `field_completeness_percentage` (float): (count of non-null fields / 5) * 100 (0.0-100.0)
- `fields_extracted` (int): Count of non-null fields (0-5)
- `validation_passed` (bool): True if extraction passed validation, False otherwise
- `validation_failure_reasons` (list[str] | None): List of specific failure reasons if validation failed (e.g., ["date field: invalid format", "startup_name: missing required field"])
- `notion_matching_attempted` (bool): True if Notion entity matching was attempted
- `notion_matching_success` (bool | None): True if matching succeeded, False if failed, None if not attempted

**Validation Rules**:
- All confidence scores must be 0.0-1.0
- `fields_extracted` must be 0-5
- `field_completeness_percentage` must be 0.0-100.0
- `validation_failure_reasons` must be non-empty list if `validation_passed` is False
- `notion_matching_success` can only be non-None if `notion_matching_attempted` is True

**Example**:
```json
{
  "email_id": "msg_12345",
  "provider_name": "gemini",
  "extraction_timestamp": "2025-11-09T10:30:45.123Z",
  "per_field_confidence": {
    "person": 0.95,
    "startup": 0.92,
    "partner": 0.88,
    "details": 0.90,
    "date": 0.85
  },
  "overall_confidence": 0.90,
  "field_completeness_percentage": 100.0,
  "fields_extracted": 5,
  "validation_passed": true,
  "validation_failure_reasons": null,
  "notion_matching_attempted": true,
  "notion_matching_success": true
}
```

---

### ProviderQualitySummary

Aggregate quality statistics for a provider over a time period.

**Attributes**:
- `provider_name` (str): Provider identifier ("gemini", "claude", "openai")
- `total_extractions` (int): Total number of extraction attempts tracked (≥0)
- `successful_validations` (int): Count of extractions that passed validation (≥0)
- `failed_validations` (int): Count of extractions that failed validation (≥0)
- `validation_success_rate` (float): (successful_validations / total_extractions) * 100 (0.0-100.0)
- `average_overall_confidence` (float): Mean of all overall_confidence scores (0.0-1.0)
- `confidence_std_deviation` (float): Standard deviation of overall_confidence scores (≥0.0)
- `average_field_completeness` (float): Mean of all field_completeness_percentage values (0.0-100.0)
- `average_fields_extracted` (float): Mean of all fields_extracted counts (0.0-5.0)
- `per_field_confidence_averages` (dict[str, float]): Average confidence per entity field
  - `person` (float): Average confidence for person_in_charge extractions
  - `startup` (float): Average confidence for startup_name extractions
  - `partner` (float): Average confidence for partner_org extractions
  - `details` (float): Average confidence for details extractions
  - `date` (float): Average confidence for date extractions
- `quality_trend` (str): "improving", "degrading", or "stable" based on recent vs previous extractions
- `last_50_avg_confidence` (float | None): Average confidence of last 50 extractions (None if <50 extractions)
- `notion_matching_success_rate` (float | None): (successful matches / attempted matches) * 100, None if no matching attempted
- `updated_at` (datetime): UTC timestamp of last update

**Validation Rules**:
- All counts must be ≥0
- `successful_validations + failed_validations ≤ total_extractions` (some extractions may not have validation data)
- `validation_success_rate` must be 0.0-100.0
- `average_overall_confidence` must be 0.0-1.0
- `quality_trend` must be one of: "improving", "degrading", "stable"
- `last_50_avg_confidence` is None if total_extractions < 50

**Example**:
```json
{
  "provider_name": "claude",
  "total_extractions": 150,
  "successful_validations": 142,
  "failed_validations": 8,
  "validation_success_rate": 94.67,
  "average_overall_confidence": 0.89,
  "confidence_std_deviation": 0.08,
  "average_field_completeness": 96.0,
  "average_fields_extracted": 4.8,
  "per_field_confidence_averages": {
    "person": 0.91,
    "startup": 0.93,
    "partner": 0.87,
    "details": 0.89,
    "date": 0.85
  },
  "quality_trend": "stable",
  "last_50_avg_confidence": 0.90,
  "notion_matching_success_rate": 88.5,
  "updated_at": "2025-11-09T12:00:00.000Z"
}
```

---

### QualityThresholdConfig

Configuration defining acceptable quality levels for automated decision-making.

**Attributes**:
- `threshold_name` (str): Descriptive name for this threshold configuration (e.g., "production_default", "high_accuracy_mode")
- `minimum_average_confidence` (float): Minimum acceptable average overall confidence (0.0-1.0, default: 0.80)
- `minimum_field_completeness` (float): Minimum acceptable field completeness percentage (0.0-100.0, default: 80.0)
- `maximum_validation_failure_rate` (float): Maximum acceptable validation failure rate percentage (0.0-100.0, default: 10.0)
- `minimum_notion_matching_success_rate` (float | None): Minimum Notion matching success rate percentage (0.0-100.0), None if not applicable
- `evaluation_window_size` (int): Number of recent extractions to evaluate (default: 100, must be ≥10)
- `enabled` (bool): Whether this threshold configuration is active (default: True)

**Validation Rules**:
- All percentage thresholds must be 0.0-100.0
- Confidence thresholds must be 0.0-1.0
- `evaluation_window_size` must be ≥10

**Example**:
```json
{
  "threshold_name": "production_default",
  "minimum_average_confidence": 0.85,
  "minimum_field_completeness": 90.0,
  "maximum_validation_failure_rate": 5.0,
  "minimum_notion_matching_success_rate": 85.0,
  "evaluation_window_size": 100,
  "enabled": true
}
```

---

### ProviderQualityComparison

Cross-provider quality analysis for decision-making.

**Attributes**:
- `comparison_timestamp` (datetime): UTC timestamp when comparison was generated
- `providers_compared` (list[str]): List of provider names included in comparison (e.g., ["gemini", "claude", "openai"])
- `provider_rankings` (list[dict]): Providers ranked by overall quality (best to worst)
  - Each dict contains:
    - `provider_name` (str): Provider identifier
    - `quality_score` (float): Composite quality score (0.0-100.0)
    - `rank` (int): Ranking position (1 = best)
- `quality_to_cost_rankings` (list[dict]): Providers ranked by value score (best to worst)
  - Each dict contains:
    - `provider_name` (str): Provider identifier
    - `value_score` (float): (average_confidence * 100) / (cost_per_email * 1000)
    - `rank` (int): Ranking position (1 = best value)
- `recommended_provider` (str): Provider name with best overall quality-to-cost ratio
- `recommendation_reason` (str): Human-readable explanation of recommendation (e.g., "Claude provides 92% confidence at $0.005/email (value score: 18.4), outperforming Gemini (16.2) and OpenAI (12.8)")

**Example**:
```json
{
  "comparison_timestamp": "2025-11-09T12:00:00.000Z",
  "providers_compared": ["gemini", "claude", "openai"],
  "provider_rankings": [
    {"provider_name": "claude", "quality_score": 92.0, "rank": 1},
    {"provider_name": "gemini", "quality_score": 88.5, "rank": 2},
    {"provider_name": "openai", "quality_score": 85.3, "rank": 3}
  ],
  "quality_to_cost_rankings": [
    {"provider_name": "claude", "value_score": 18.4, "rank": 1},
    {"provider_name": "gemini", "value_score": 16.2, "rank": 2},
    {"provider_name": "openai", "value_score": 12.8, "rank": 3}
  ],
  "recommended_provider": "claude",
  "recommendation_reason": "Claude provides 92% confidence at $0.005/email (value score: 18.4), outperforming Gemini (16.2) and OpenAI (12.8)"
}
```

---

## Persistence Schema

### File Structure

```
data/llm_health/
├── health_metrics.json          # Existing health tracking
├── cost_metrics.json            # Existing cost tracking
└── quality_metrics.json         # NEW: Quality tracking
```

### quality_metrics.json Schema

```json
{
  "gemini": {
    "provider_name": "gemini",
    "total_extractions": 150,
    "successful_validations": 142,
    "failed_validations": 8,
    "validation_success_rate": 94.67,
    "average_overall_confidence": 0.89,
    "confidence_std_deviation": 0.08,
    "average_field_completeness": 96.0,
    "average_fields_extracted": 4.8,
    "per_field_confidence_averages": {
      "person": 0.91,
      "startup": 0.93,
      "partner": 0.87,
      "details": 0.89,
      "date": 0.85
    },
    "quality_trend": "stable",
    "last_50_avg_confidence": 0.90,
    "notion_matching_success_rate": 88.5,
    "updated_at": "2025-11-09T12:00:00.000Z"
  },
  "claude": { /* ProviderQualitySummary */ },
  "openai": { /* ProviderQualitySummary */ }
}
```

**Notes**:
- Top-level keys are provider names
- Each provider has a `ProviderQualitySummary` object
- Timestamps stored as ISO 8601 strings
- File written atomically using tempfile + rename pattern
- Individual `QualityMetricsRecord` objects are aggregated into the summary (not stored individually to save space)

---

## Relationships

```
ExtractedEntities (existing)
    ↓ (has embedded)
ConfidenceScores (existing: person/startup/partner/details/date)
    ↓ (extracted to create)
QualityMetricsRecord (per extraction attempt)
    ↓ (aggregated into)
ProviderQualitySummary (per provider)
    ↓ (combined with)
CostMetricsSummary (existing cost data)
    ↓ (produces)
ProviderQualityComparison (cross-provider analysis)
```

---

## State Transitions

### Quality Trend State Machine

```
Initial State: "stable" (when first created or insufficient data)

Transitions:
1. stable → improving: When (last 25 avg) > (previous 25 avg) by ≥5%
2. stable → degrading: When (last 25 avg) < (previous 25 avg) by ≥5%
3. improving → stable: When difference between windows < 5%
4. degrading → stable: When difference between windows < 5%
5. improving → degrading: When trend reverses by ≥5%
6. degrading → improving: When trend reverses by ≥5%

Note: Requires at least 50 extractions for trend calculation
```

---

## Index & Query Patterns

### Primary Queries

1. **Get provider quality summary**: O(1) lookup by provider_name in quality_metrics.json
2. **Compare all providers**: O(n) scan of all provider summaries where n = 3 (gemini, claude, openai)
3. **Check quality threshold**: O(1) comparison of summary metrics vs threshold config
4. **Calculate value score**: O(1) lookup of quality summary + O(1) lookup of cost summary + O(1) division

### Performance Targets

- Query any provider summary: <100ms (file read + JSON parse)
- Generate cross-provider comparison: <500ms (read 2 files: quality + cost)
- Update summary after extraction: <50ms (incremental statistics update + atomic write)

**Note**: Individual extraction records are not persisted (only aggregates) to minimize file size and optimize query performance. If detailed extraction-level quality analysis is needed in the future, a separate quality_records/ directory can be added with per-extraction JSON files.
