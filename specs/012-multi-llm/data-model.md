# Data Model: Multi-LLM Provider Support

**Feature**: Multi-LLM Provider Support
**Branch**: `012-multi-llm`
**Date**: 2025-11-08

## Overview

This document defines the data entities required for multi-LLM provider support, including provider configuration, health metrics, cost tracking, and extraction results with provider metadata.

---

## Entity 1: LLM Provider Configuration

### Description
Represents the configuration for a specific LLM service (Gemini, Claude, OpenAI) including authentication, API settings, and priority.

### Attributes

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `provider_name` | string | Yes | Unique provider identifier | One of: "gemini", "claude", "openai" |
| `display_name` | string | Yes | Human-readable name | e.g., "Claude Sonnet 4.5", "GPT-5 Mini" |
| `model_id` | string | Yes | Specific model identifier | e.g., "claude-sonnet-4-5", "gpt-5-mini" |
| `api_key_env_var` | string | Yes | Environment variable name for API key | e.g., "ANTHROPIC_API_KEY" |
| `enabled` | boolean | Yes | Whether provider is active | Default: true |
| `priority` | integer | Yes | Priority order (1 = highest) | >= 1, unique per provider |
| `timeout_seconds` | float | Yes | Request timeout | Default: 60.0, range: 5.0-300.0 |
| `max_retries` | integer | Yes | Maximum retry attempts | Default: 3, range: 0-5 |
| `input_token_price` | float | Yes | Cost per 1M input tokens (USD) | e.g., 3.00 for Claude |
| `output_token_price` | float | Yes | Cost per 1M output tokens (USD) | e.g., 15.00 for Claude |

### Relationships
- One provider config → many health metrics (time series)
- One provider config → one cost metrics summary
- One provider config → many extraction results

### Example (JSON)
```json
{
  "provider_name": "claude",
  "display_name": "Claude Sonnet 4.5",
  "model_id": "claude-sonnet-4-5-20250929",
  "api_key_env_var": "ANTHROPIC_API_KEY",
  "enabled": true,
  "priority": 2,
  "timeout_seconds": 60.0,
  "max_retries": 3,
  "input_token_price": 3.00,
  "output_token_price": 15.00
}
```

---

## Entity 2: Provider Health Metrics

### Description
Contains health tracking data for a provider including success/failure counts, response times, and current health status.

### Attributes

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `provider_name` | string | Yes | Provider identifier | Foreign key to LLM Provider Configuration |
| `health_status` | string | Yes | Current health state | One of: "healthy", "unhealthy" |
| `success_count` | integer | Yes | Total successful requests | >= 0 |
| `failure_count` | integer | Yes | Total failed requests | >= 0 |
| `consecutive_failures` | integer | Yes | Current failure streak | >= 0 |
| `average_response_time_ms` | float | Yes | Rolling average response time | >= 0.0 |
| `last_success_timestamp` | datetime | No | UTC timestamp of last success | ISO 8601 format |
| `last_failure_timestamp` | datetime | No | UTC timestamp of last failure | ISO 8601 format |
| `last_error_message` | string | No | Most recent error description | Max 500 characters |
| `circuit_breaker_state` | string | Yes | Circuit breaker status | One of: "closed", "open", "half_open" |
| `updated_at` | datetime | Yes | Last metrics update timestamp | ISO 8601 format, UTC |

### Derived Fields
- **Success rate**: `success_count / (success_count + failure_count)`
- **Is healthy**: `health_status == "healthy" AND consecutive_failures < threshold`

### Validation Rules
- `consecutive_failures` resets to 0 on success
- `health_status` changes to "unhealthy" when `consecutive_failures >= 5` (configurable)
- `circuit_breaker_state` = "open" when unhealthy

### State Transitions

```
healthy (consecutive_failures < 5)
  ↓ [5th consecutive failure]
unhealthy (consecutive_failures >= 5)
  ↓ [successful request]
healthy (consecutive_failures reset to 0)
```

### Example (JSON)
```json
{
  "provider_name": "claude",
  "health_status": "healthy",
  "success_count": 1247,
  "failure_count": 23,
  "consecutive_failures": 0,
  "average_response_time_ms": 1834.5,
  "last_success_timestamp": "2025-11-08T14:32:18Z",
  "last_failure_timestamp": "2025-11-08T09:15:42Z",
  "last_error_message": "Rate limit exceeded (429)",
  "circuit_breaker_state": "closed",
  "updated_at": "2025-11-08T14:32:18Z"
}
```

---

## Entity 3: Extraction Result with Provider Metadata

### Description
Extends the existing `ExtractedEntities` model with provider-specific metadata including which provider was used, token usage, and cost.

### Attributes

**Existing fields** (from `ExtractedEntities`):
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_in_charge` | string | No | Extracted person name |
| `startup_name` | string | No | Extracted startup/company name |
| `partner_org` | string | No | Extracted partner organization |
| `details` | string | Yes | Collaboration details |
| `date` | datetime | No | Extracted date |
| `confidence` | ConfidenceScores | Yes | Confidence scores per field |
| `email_id` | string | Yes | Email identifier |
| `extracted_at` | datetime | Yes | Extraction timestamp (UTC) |

**New fields** (provider metadata):
| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `provider_name` | string | Yes | Provider that generated this result | One of: "gemini", "claude", "openai" |
| `model_id` | string | Yes | Specific model used | e.g., "claude-sonnet-4-5" |
| `input_tokens` | integer | Yes | Input token count | >= 0 |
| `output_tokens` | integer | Yes | Output token count | >= 0 |
| `total_tokens` | integer | Yes | Sum of input + output tokens | >= 0 |
| `extraction_cost_usd` | float | Yes | Cost for this extraction | >= 0.0 |
| `response_time_ms` | float | Yes | API response time | >= 0.0 |
| `orchestration_strategy` | string | No | Strategy used if multi-provider | One of: "failover", "consensus", "best_match", null |
| `fallback_used` | boolean | Yes | Whether this was a fallback attempt | Default: false |

### Relationships
- One extraction result → one provider (via `provider_name`)
- One email → one or more extraction results (if using consensus/best-match)

### Example (JSON)
```json
{
  "person_in_charge": "김철수",
  "startup_name": "본봄",
  "partner_org": "신세계인터내셔널",
  "details": "파일럿 킥오프",
  "date": "2025-11-07T00:00:00Z",
  "confidence": {
    "person": 0.95,
    "startup": 0.92,
    "partner": 0.88,
    "details": 0.90,
    "date": 0.85
  },
  "email_id": "msg_12345",
  "extracted_at": "2025-11-08T14:32:18Z",
  "provider_name": "claude",
  "model_id": "claude-sonnet-4-5-20250929",
  "input_tokens": 423,
  "output_tokens": 87,
  "total_tokens": 510,
  "extraction_cost_usd": 0.002574,
  "response_time_ms": 1834.5,
  "orchestration_strategy": "failover",
  "fallback_used": true
}
```

---

## Entity 4: Orchestration Strategy Configuration

### Description
Defines how multiple providers are coordinated, including strategy type, enabled providers, and configuration parameters.

### Attributes

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `strategy_type` | string | Yes | Orchestration strategy | One of: "failover", "consensus", "best_match" |
| `enabled_providers` | list[string] | Yes | Providers to use in this strategy | Min length: 1, valid provider names |
| `provider_priority_order` | list[string] | Yes (failover) | Failover sequence | Only for failover strategy |
| `unhealthy_threshold` | integer | Yes | Consecutive failures before unhealthy | Default: 5, range: 1-10 |
| `consensus_min_agreement` | integer | No | Minimum providers that must agree | Only for consensus, default: 2 |
| `fuzzy_match_threshold` | float | No | Jaro-Winkler threshold for fuzzy matching | Only for consensus, default: 0.85, range: 0.0-1.0 |
| `abstention_confidence_threshold` | float | No | Min confidence to avoid abstention | Only for consensus, default: 0.25, range: 0.0-1.0 |
| `parallel_queries` | boolean | Yes | Whether to query providers in parallel | Default: true for consensus/best-match |
| `timeout_seconds` | float | Yes | Overall orchestration timeout | Default: 90.0, range: 10.0-300.0 |

### Strategy-Specific Rules

**Failover**:
- Requires `provider_priority_order` (e.g., ["gemini", "claude", "openai"])
- `parallel_queries` must be false
- Tries providers sequentially until success

**Consensus**:
- Requires `enabled_providers` with 2+ providers
- `parallel_queries` should be true
- Uses `fuzzy_match_threshold` and `consensus_min_agreement`

**Best-Match**:
- Requires `enabled_providers` with 2+ providers
- `parallel_queries` should be true
- Selects result with highest aggregate confidence

### Example (JSON - Failover Strategy)
```json
{
  "strategy_type": "failover",
  "enabled_providers": ["gemini", "claude", "openai"],
  "provider_priority_order": ["gemini", "claude", "openai"],
  "unhealthy_threshold": 5,
  "parallel_queries": false,
  "timeout_seconds": 90.0
}
```

### Example (JSON - Consensus Strategy)
```json
{
  "strategy_type": "consensus",
  "enabled_providers": ["gemini", "claude"],
  "unhealthy_threshold": 5,
  "consensus_min_agreement": 2,
  "fuzzy_match_threshold": 0.85,
  "abstention_confidence_threshold": 0.25,
  "parallel_queries": true,
  "timeout_seconds": 120.0
}
```

---

## Entity 5: Cost Metrics Summary

### Description
Tracks financial cost per provider including total API calls, token usage, and cumulative cost.

### Attributes

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `provider_name` | string | Yes | Provider identifier | Foreign key to LLM Provider Configuration |
| `total_api_calls` | integer | Yes | Total number of API requests | >= 0 |
| `total_input_tokens` | integer | Yes | Cumulative input tokens | >= 0 |
| `total_output_tokens` | integer | Yes | Cumulative output tokens | >= 0 |
| `total_tokens` | integer | Yes | Sum of input + output tokens | >= 0 |
| `total_cost_usd` | float | Yes | Cumulative cost (USD) | >= 0.0 |
| `average_cost_per_email` | float | Yes | Average cost per extraction | >= 0.0 |
| `last_updated` | datetime | Yes | Last metrics update timestamp | ISO 8601 format, UTC |

### Derived Fields
- **Average input tokens per call**: `total_input_tokens / total_api_calls`
- **Average output tokens per call**: `total_output_tokens / total_api_calls`
- **Average cost per call**: `total_cost_usd / total_api_calls`

### Update Pattern
- Increment counters after each successful API call
- Recalculate `average_cost_per_email` based on new totals

### Example (JSON)
```json
{
  "provider_name": "claude",
  "total_api_calls": 1247,
  "total_input_tokens": 527891,
  "total_output_tokens": 108453,
  "total_tokens": 636344,
  "total_cost_usd": 3.209619,
  "average_cost_per_email": 0.002574,
  "last_updated": "2025-11-08T14:32:18Z"
}
```

---

## File Storage Structure

### Location
`data/llm_health/`

### Files

#### `health_metrics.json`
```json
{
  "gemini": { /* Provider Health Metrics */ },
  "claude": { /* Provider Health Metrics */ },
  "openai": { /* Provider Health Metrics */ }
}
```

#### `cost_metrics.json`
```json
{
  "gemini": { /* Cost Metrics Summary */ },
  "claude": { /* Cost Metrics Summary */ },
  "openai": { /* Cost Metrics Summary */ }
}
```

#### `provider_config.json`
```json
{
  "gemini": { /* LLM Provider Configuration */ },
  "claude": { /* LLM Provider Configuration */ },
  "openai": { /* LLM Provider Configuration */ }
}
```

#### `orchestration_config.json`
```json
{
  "active_strategy": "failover",
  "strategies": {
    "failover": { /* Orchestration Strategy Configuration */ },
    "consensus": { /* Orchestration Strategy Configuration */ },
    "best_match": { /* Orchestration Strategy Configuration */ }
  }
}
```

---

## Validation Rules Summary

### Provider Health
- Consecutive failures threshold: 5 (configurable)
- Circuit breaker opens when threshold reached
- Success resets consecutive_failures to 0

### Cost Tracking
- Calculate immediately after API response
- Use provider-specific pricing from config
- Update both per-call and cumulative metrics

### Extraction Results
- Must include provider metadata for cost attribution
- Token counts must match API response
- Cost calculation: `(input_tokens × input_price) + (output_tokens × output_price)` per 1M tokens

### Orchestration Strategy
- Failover: Sequential provider attempts, first success wins
- Consensus: Parallel queries, merge using weighted voting
- Best-match: Parallel queries, select highest aggregate confidence

---

## State Management

### Provider Health State Machine
```
[CLOSED] ──failure──> [increment consecutive_failures]
            └──> if consecutive_failures >= 5 ──> [OPEN]

[OPEN] ──after timeout──> [HALF_OPEN]

[HALF_OPEN] ──success──> [CLOSED, reset consecutive_failures]
             └──failure──> [OPEN]
```

### Metrics Update Flow
```
API Call Success:
1. Increment success_count
2. Reset consecutive_failures to 0
3. Update average_response_time_ms
4. Set last_success_timestamp
5. Update cost metrics (tokens + cost)
6. Persist to JSON files

API Call Failure:
1. Increment failure_count
2. Increment consecutive_failures
3. Set last_failure_timestamp
4. Set last_error_message
5. If consecutive_failures >= threshold:
   - Set health_status = "unhealthy"
   - Set circuit_breaker_state = "open"
6. Persist to JSON files
```

---

## Implementation Notes

### Pydantic Models
All entities should be implemented as Pydantic models for validation:
- `ProviderConfig` (Entity 1)
- `ProviderHealthMetrics` (Entity 2)
- `ExtractedEntitiesWithMetadata` (Entity 3, extends existing `ExtractedEntities`)
- `OrchestrationStrategyConfig` (Entity 4)
- `CostMetricsSummary` (Entity 5)

### Persistence
- Use atomic file writes (temp file + rename)
- File locking optional (if multi-process access needed)
- JSON format for human-readability and debugging

### Backward Compatibility
- Existing `ExtractedEntities` model remains unchanged
- Provider metadata added as optional extension
- Existing Gemini adapter continues to work without modifications
