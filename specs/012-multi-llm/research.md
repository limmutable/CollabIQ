# Research: Multi-LLM Provider Support

**Feature**: Multi-LLM Provider Support
**Branch**: `012-multi-llm`
**Date**: 2025-11-08

## Overview

This document consolidates technical research for implementing multi-LLM provider support in CollabIQ. The research covers integration patterns for Claude (Anthropic) and OpenAI SDKs, consensus algorithms for merging conflicting outputs, and provider health management strategies.

---

## Research Task 1: Claude (Anthropic) SDK Integration

### Decision

Use `anthropic` Python SDK with **Tool Calling** (forced tool choice) for structured JSON extraction with Claude Sonnet 4.5.

### Rationale

- **Official SDK**: Maintained by Anthropic with active development
- **Built-in reliability**: Automatic retry logic with exponential backoff (2 retries default)
- **Structured output reliability**: Tool calling provides ~14-20% fewer failures compared to simple JSON prompting
- **Token tracking**: Built-in usage tracking in response objects
- **Best model**: Claude Sonnet 4.5 excels at structured extraction (80-84% accuracy, 9.5/10 benchmark score)
- **Cost-effective**: $3/M input tokens, $15/M output tokens (balanced cost/performance)

### Key Implementation Details

**Package & Version**:
- Package: `anthropic` (PyPI)
- Installation: `uv add anthropic`
- Python requirement: 3.7+ (compatible with project's Python 3.12)

**Model Selection**:
- Primary: `claude-sonnet-4-5-20250929` (alias: `claude-sonnet-4-5`)
- Supports 64K output tokens
- Alternative: `claude-haiku-4-5` for cost optimization (5x cheaper)

**Authentication**:
```python
from anthropic import Anthropic
client = Anthropic()  # Auto-reads ANTHROPIC_API_KEY env var
```
Store API key in `.env` as `ANTHROPIC_API_KEY` (matches existing Gemini pattern)

**Structured Output Method**:
```python
# Define extraction schema as a tool
tools = [{
    "name": "extract_entities",
    "description": "Extract 5 entities from email text",
    "input_schema": {
        "type": "object",
        "properties": {
            "person_in_charge": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                },
                "required": ["value", "confidence"]
            },
            # ... other entities
        }
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_entities"},  # Force tool use
    messages=[{"role": "user", "content": prompt}]
)

# Extract structured data
tool_input = response.content[0].input  # Returns dict matching schema
```

**Token Tracking**:
```python
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens

# Cost calculation
input_cost = (input_tokens / 1_000_000) * 3.00
output_cost = (output_tokens / 1_000_000) * 15.00
```

**Timeout & Retry**:
```python
import httpx
client = Anthropic(
    timeout=60.0,         # Match GeminiAdapter
    max_retries=3        # SDK built-in retries
)

# Granular control (optional)
client = Anthropic(
    timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
)
```

**Error Handling**:
- SDK automatically retries: 408 Timeout, 409 Conflict, 429 Rate Limit, >=500 Server errors
- Respects `retry-after` header from API
- Exponential backoff with short delays

**Confidence Scores**:
- **Important**: Claude does NOT provide native confidence scores
- **Solution**: Prompt the LLM to generate confidence scores (0.0-1.0) as part of structured output
- **Implementation**: Include confidence in tool schema, provide calibration guidelines in prompt
- **Validation**: Use Pydantic to enforce 0.0 <= confidence <= 1.0

### Alternatives Considered

1. **Simple JSON Prompting** (no tool calling)
   - Rejected: 14-20% higher failure rate
   - Tool calling is more reliable for production

2. **Claude Agent SDK** (`claude-agent-sdk`)
   - Rejected: Overkill for entity extraction
   - Designed for autonomous agents with file operations, not structured extraction

3. **Helper Libraries** (Instructor, jsonformer-claude)
   - Rejected: Adds dependency overhead
   - Native `anthropic` SDK tool calling is sufficient

4. **Claude Opus 4.1**
   - Rejected: 5x more expensive ($15 input / $75 output)
   - Marginal accuracy gains not worth cost for entity extraction

### References

- **Anthropic Python SDK**: https://github.com/anthropics/anthropic-sdk-python
- **Tool Use Implementation**: https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use
- **Models Overview**: https://docs.claude.com/en/docs/about-claude/models/overview
- **Structured JSON Extraction Cookbook**: https://github.com/anthropics/anthropic-cookbook/blob/main/tool_use/extracting_structured_json.ipynb
- **Claude Sonnet 4.5 Announcement**: https://www.anthropic.com/news/claude-sonnet-4-5
- **Pricing**: https://docs.anthropic.com/en/docs/about-claude/pricing

---

## Research Task 2: OpenAI SDK Integration

### Decision

Use `openai` Python SDK (v1.102.0+) with **GPT-5 Mini** and **Structured Outputs** (`response_format` with `json_schema`) for entity extraction, using prompt-based confidence scores.

### Rationale

- **Best cost/performance balance**: GPT-5 Mini ($0.25/M input, $2.00/M output) is 8-10x cheaper than GPT-5
- **Native structured output**: 100% schema adherence reliability (eliminates JSON parsing errors)
- **Consistent architecture**: Integrates cleanly with existing Pydantic models and retry patterns
- **Production-ready**: Clear exception types, built-in retry mechanisms
- **Confidence strategy**: Prompt-based confidence (like Gemini) works with Structured Outputs

### Key Implementation Details

**Package & Version**:
- Package: `openai` (PyPI)
- Installation: `uv add openai`
- Minimum version: 1.0.0+ (current: 1.102.0 as of 2025)
- Python requirement: 3.8+ (compatible with Python 3.12)

**Model Selection**:
- Primary: `gpt-5-mini` (formerly gpt-4o-mini)
- Pricing: $0.25/M input, $2.00/M output
- Alternatives:
  - `gpt-5` for higher accuracy (4x more expensive: $1.25 input / $10.00 output)
  - `gpt-5-nano` for lower cost (5x cheaper but lower quality)

**Authentication**:
```python
from openai import OpenAI
client = OpenAI()  # Auto-reads OPENAI_API_KEY env var
```
Store API key in `.env` as `OPENAI_API_KEY`

**Structured Output Method**:
```python
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{"role": "user", "content": prompt}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "entity_extraction",
            "strict": True,
            "schema": {/* JSON Schema matching ExtractedEntities */}
        }
    }
)
```
**Note**: Use `strict: True` to enforce 100% schema adherence

**Token Tracking**:
```python
response.usage.prompt_tokens      # Input tokens
response.usage.completion_tokens  # Output tokens
response.usage.total_tokens       # Sum

# Cost calculation
cost = (prompt_tokens / 1_000_000 * 0.25) + (completion_tokens / 1_000_000 * 2.00)
```

**Timeout Configuration**:
```python
import httpx
client = OpenAI(
    timeout=60.0,        # Match GeminiAdapter
    max_retries=0        # Disable SDK retries, use custom retry_with_backoff
)

# Granular control (optional)
client = OpenAI(
    timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=10.0)
)
```

**Rate Limiting & Retry**:
- OpenAI rate limits vary by tier (Free/Pay-as-you-go/Tier 1-5)
- Example (Tier 1): 500 RPM, 200K TPM for GPT-5 Mini
- HTTP 429 errors include `Retry-After` header
- **Recommendation**: Use CollabIQ's existing `retry_with_backoff` decorator with custom config:

```python
OPENAI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=60.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=60.0,
    retryable_exceptions={
        socket.timeout,
        ConnectionError,
        TimeoutError,
        # OpenAI-specific:
        # openai.RateLimitError,
        # openai.APITimeoutError,
        # openai.APIConnectionError,
    },
    respect_retry_after=True
)
```

**Exception Mapping**:
Map OpenAI exceptions to existing `LLMAPIError` hierarchy:
- `openai.RateLimitError` → `LLMRateLimitError`
- `openai.APITimeoutError` → `LLMTimeoutError`
- `openai.AuthenticationError` / `PermissionDeniedError` → `LLMAuthenticationError`
- `json.JSONDecodeError`, `pydantic.ValidationError` → `LLMValidationError`
- `openai.APIError` → `LLMAPIError`

**Confidence Scores**:
- **Challenge**: GPT models don't natively provide confidence scores
- **Solution**: Use prompt-based confidence (same as Gemini approach)
  - Add `"confidence": {"type": "number"}` to each entity in schema
  - Rely on model's self-assessment (GPT models are reasonably well-calibrated)
- **Alternative (not recommended for MVP)**: Use logprobs with function calling (requires switching from Structured Outputs to `tools` parameter)

### Alternatives Considered

1. **GPT-5 (Full Model)**
   - Rejected: 4x more expensive, not justified for entity extraction

2. **GPT-5 Nano**
   - Rejected: 5x cheaper but lower quality, accuracy critical for CollabIQ

3. **o-series Models (o3, o3-mini)**
   - Rejected: Overkill for entity extraction, higher latency

4. **Function Calling vs Structured Outputs**
   - Function calling supports logprobs but more complex
   - Structured Outputs simpler and faster
   - **Decision**: Use Structured Outputs with prompt-based confidence (matches Gemini)

5. **Batch API**
   - 50% discount but asynchronous (24-hour processing)
   - Rejected: CollabIQ needs near-real-time extraction

### References

- **OpenAI Platform Docs**: https://platform.openai.com/docs/
- **Python SDK**: https://platform.openai.com/docs/api-reference/introduction?lang=python
- **GitHub**: https://github.com/openai/openai-python
- **Structured Outputs Guide**: https://platform.openai.com/docs/guides/structured-outputs
- **Rate Limits Guide**: https://platform.openai.com/docs/guides/rate-limits
- **Pricing**: https://openai.com/api/pricing/

---

## Research Task 3: Consensus Algorithms for Multi-LLM Outputs

### Decision

Implement **Weighted Confidence Voting** with Dawid-Skene-inspired aggregation for merging conflicting LLM outputs.

### Rationale

- **Proven in production**: Successfully deployed at Walmart for product attribute extraction
- **Handles model diversity**: Different LLMs excel at different entity types
- **Mathematically optimal**: Iterative weight-learning approach converges efficiently
- **Superior accuracy**: Ensemble methods improve F1 scores to 94.88% vs individual models
- **Better than alternatives**: Outperforms simple majority voting by 10-15% on entity extraction

### Key Strategies

#### 1. Same Entity, Different Confidence

Use weighted aggregation where each model's prediction is multiplied by:
- Learned weight (historical accuracy for that entity type)
- Calibrated confidence score

Formula:
```
final_confidence = Σ(weight_i × calibrated_confidence_i × vote_i) / Σ(weight_i × vote_i)
```

Apply **temperature scaling** to calibrate raw confidence scores across different LLMs.

#### 2. Different Values (Conflicting Extractions)

**First pass**: Fuzzy string similarity using Jaro-Winkler distance
- Threshold ≥ 0.85-0.90 for partial matches
- Jaro-Winkler preferred over Levenshtein for entity matching (prioritizes prefix similarity)
- Example: "John Smith" vs "John" → Partial match if Jaro-Winkler ≥ 0.85

**Second pass**: If no fuzzy match, apply weighted voting
- Select value with highest `weight × confidence` product
- Formula: `value = argmax(weight_i × confidence_i)` where `i ∈ {Gemini, Claude, OpenAI}`

**Third pass (optional)**: Iterative Consensus Ensemble (ICE) for complex cases
- Loop models to critique each other's outputs for 2-3 rounds
- Improves accuracy by 7-15 points over single best model
- Trade-off: Higher latency (~6-18s vs ~2s) and cost (3-9x API calls)

#### 3. Equal Confidence Conflicts (Tie-Breaking)

Priority order:
1. **Majority voting**: If 2 out of 3 models agree, select majority value
2. **Historical performance**: Choose model with highest accuracy for specific entity field
3. **Abstention**: If ensemble confidence < 0.25-0.30 threshold, return `null` or flag for review
4. **Fallback**: Default to most capable model (GPT-5 or Claude Sonnet) as last resort

#### 4. Partial Matches (Fuzzy Similarity)

**Primary metric**: Jaro-Winkler distance
- Above 0.90: Strong match, merge values
- 0.85-0.90: Moderate match, prefer longer/more complete value
- Below 0.85: Consider different entities

**For names**: Use Jaro-Winkler (better for "John" vs "John Smith")
**For organizations**: Combined approach:
- Jaro-Winkler for overall similarity
- Check substring containment ("Stanford" vs "Stanford University")

**Normalization**: When partial match detected, select more complete value

### Implementation Approach

**Phase 1 (P1 - Failover)**: Simple strategy selection
- No consensus needed for failover
- Select first successful provider response

**Phase 2 (P2 - Consensus)**: Weighted voting implementation
1. Query multiple providers in parallel
2. Apply Jaro-Winkler fuzzy matching (threshold 0.85)
3. For conflicts, use weighted voting: `argmax(weight_i × confidence_i)`
4. Initialize all weights to 1.0 (equal weighting)

**Phase 3 (Future optimization)**: Weight learning
1. Collect labeled examples over time
2. Implement Dawid-Skene EM algorithm to learn optimal weights
3. Track per-entity-type accuracy for each model

**Phase 4 (P3 - Best-Match)**: Confidence-based selection
- Calculate aggregate confidence: average across all entities
- Select provider with highest aggregate confidence

### Alternatives Considered

1. **Simple Majority Voting**
   - Rejected: Treats all models equally, ignoring different strengths
   - Weighted voting outperforms by 10-15%

2. **Highest Single Confidence Selection**
   - Rejected: Over-relies on one model, doesn't benefit from ensemble
   - Single models achieve only 72-81% vs 94%+ for ensembles

3. **Pure Iterative Consensus Ensemble (ICE)**
   - Rejected as primary: High latency (2-3+ rounds), 3-9x cost
   - Use case: Reserve for high-value cases or initial consensus failures

4. **Soft Voting (Average Probabilities)**
   - Rejected: Requires token-level probabilities not exposed by all APIs

5. **Cascade Strategy** (try cheap model first, escalate if low confidence)
   - Not rejected, deferred: Could reduce costs by 50%
   - Recommendation: Implement weighted voting first, add cascading later

6. **Learn-to-Ensemble Neural Approach**
   - Rejected for MVP: Requires 10,000+ labeled examples with ground truth
   - Reconsider when sufficient training data accumulated

### References

**Academic Papers**:
- **LLM-Ensemble for E-commerce**: https://arxiv.org/abs/2403.00863 (Walmart production deployment)
- **Iterative Consensus Ensemble**: https://www.sciencedirect.com/science/article/abs/pii/S0010482525010820
- **Label with Confidence**: https://www.amazon.science/publications/label-with-confidence-effective-confidence-calibration-and-ensembles-in-llm-powered-classification
- **Harnessing Multiple LLMs Survey**: https://arxiv.org/html/2502.18036v1

**Technical Resources**:
- **Dawid-Skene Model**: https://michaelpjcamilleri.wordpress.com/2020/06/22/reaching-a-consensus-in-crowdsourced-data-using-the-dawid-skene-model/
- **String Similarity Metrics**: https://www.cs.cmu.edu/~wcohen/postscript/ijcai-ws-2003.pdf
- **Temperature Scaling**: https://github.com/gpleiss/temperature_scaling
- **Abstention in LLMs**: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00754/131566/

---

## Research Task 4: Circuit Breaker Patterns

### Decision

Implement **State-based Circuit Breaker** with consecutive failure threshold and periodic health checks.

### Rationale

- **Proven pattern**: Widely used in microservices architectures
- **Fast failure**: Prevents cascading failures and timeout accumulation
- **Automatic recovery**: Periodic testing detects when provider recovers
- **Existing implementation**: CollabIQ already has circuit breaker infrastructure for Gmail, Gemini, Notion

### Implementation Pattern

Follow existing `error_handling/circuit_breaker.py` pattern:

```python
from error_handling import CircuitBreaker, CircuitBreakerConfig

# Create provider-specific circuit breakers
claude_circuit_breaker = CircuitBreaker(
    name="claude_api",
    config=CircuitBreakerConfig(
        failure_threshold=5,        # Consecutive failures before OPEN
        success_threshold=2,        # Successes needed to close from HALF_OPEN
        timeout=60.0,               # Seconds in OPEN before HALF_OPEN
        half_open_max_calls=3       # Max calls allowed in HALF_OPEN state
    )
)

openai_circuit_breaker = CircuitBreaker(
    name="openai_api",
    config=CircuitBreakerConfig(/* same config */)
)
```

**States**:
1. **CLOSED** (normal): Requests pass through, failures tracked
2. **OPEN** (failing): All requests immediately fail without calling API
3. **HALF_OPEN** (testing): Limited requests allowed to test recovery

**Integration with Health Tracker**:
- Circuit breaker failure/success events update health metrics
- Health tracker marks provider as unhealthy when circuit OPEN
- Periodic health checks use HALF_OPEN state to test recovery

### Alternatives Considered

1. **Time-window based breaker**
   - Rejected: More complex, consecutive failures simpler for LLM APIs

2. **No circuit breaker**
   - Rejected: Would accumulate timeouts, slow down failover

3. **Third-party library** (e.g., `pybreaker`)
   - Rejected: CollabIQ already has custom implementation matching requirements

---

## Research Task 5: Cost Calculation Patterns

### Decision

Track token usage per provider using **provider-specific pricing models** with cost calculated as:
```
cost = (input_tokens × input_price) + (output_tokens × output_price)
```

### Pricing Models (as of 2025)

**Gemini 2.0 Flash**:
- Input: $0.075 / 1M tokens
- Output: $0.30 / 1M tokens

**Claude Sonnet 4.5**:
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens

**GPT-5 Mini**:
- Input: $0.25 / 1M tokens
- Output: $2.00 / 1M tokens

### Implementation Approach

**Cost Tracker Class**:
```python
class CostTracker:
    def __init__(self):
        self.provider_costs = {
            "gemini": {"input": 0.000075, "output": 0.0003},
            "claude": {"input": 0.003, "output": 0.015},
            "openai": {"input": 0.00025, "output": 0.002}
        }

    def calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.provider_costs[provider]
        return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
```

**Persistence**:
- Store in `data/llm_health/cost_metrics.json`
- Track: total_api_calls, total_input_tokens, total_output_tokens, total_cost per provider
- Update after each API call

### Alternatives Considered

1. **Database storage**
   - Rejected: File-based JSON sufficient for MVP, matches existing patterns

2. **Per-request pricing**
   - Rejected: All three providers use per-token pricing

3. **Batching cost calculations**
   - Rejected: Calculate immediately to ensure accuracy

---

## Research Task 6: File-based Persistence Patterns

### Decision

Use **JSON files** in `data/llm_health/` directory with atomic writes and file locking.

### Implementation Pattern

**File Structure**:
```
data/llm_health/
├── health_metrics.json    # Provider health status
└── cost_metrics.json      # Cost tracking data
```

**Atomic Write Pattern**:
```python
import json
import tempfile
import shutil
from pathlib import Path

def atomic_write_json(file_path: Path, data: dict):
    """Write JSON atomically using temp file + rename"""
    temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, suffix='.tmp')
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(data, f, indent=2)
        shutil.move(temp_path, file_path)
    except Exception:
        if Path(temp_path).exists():
            Path(temp_path).unlink()
        raise
```

**File Locking** (optional for multi-process scenarios):
```python
import fcntl

with open(file_path, 'r+') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
    data = json.load(f)
    # Modify data
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
```

### Rationale

- **Simplicity**: No database dependency
- **Consistency**: Matches existing file-based patterns in CollabIQ (`data/extractions/`, `data/notion_cache/`)
- **Atomicity**: Temp file + rename ensures no partial writes
- **Human-readable**: JSON format easily inspected for debugging

### Alternatives Considered

1. **SQLite database**
   - Rejected: Overkill for simple metrics tracking

2. **In-memory only**
   - Rejected: Metrics lost on restart, violates requirement

3. **CSV files**
   - Rejected: JSON more flexible for nested structure (health metrics per provider)

---

## Summary

All research tasks complete with decisions made:

1. **Claude SDK**: Use `anthropic` package with tool calling, Claude Sonnet 4.5, prompt-based confidence
2. **OpenAI SDK**: Use `openai` package with Structured Outputs, GPT-5 Mini, prompt-based confidence
3. **Consensus**: Weighted confidence voting with Jaro-Winkler fuzzy matching (threshold 0.85)
4. **Circuit Breaker**: State-based pattern with 5 consecutive failures threshold
5. **Cost Tracking**: Per-token pricing, provider-specific rates, calculate after each call
6. **Persistence**: JSON files in `data/llm_health/` with atomic writes

All decisions align with existing CollabIQ architecture patterns and can be implemented incrementally per user story priorities (P1 → P2 → P3).
