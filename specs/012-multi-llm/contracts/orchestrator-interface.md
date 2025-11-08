# Contract: LLM Orchestrator Interface

**Feature**: Multi-LLM Provider Support
**Branch**: `012-multi-llm`
**Date**: 2025-11-08

## Overview

This contract defines the interface for the LLM Orchestrator, which coordinates multiple LLM providers using different strategies (failover, consensus, best-match). The orchestrator abstracts away the complexity of multi-provider coordination and presents a single unified interface to callers.

---

## Interface Definition

### Class: `LLMOrchestrator`

**Module**: `src/llm_orchestrator/orchestrator.py` (new)

**Purpose**: Coordinate multiple LLM providers using configurable strategies

**Dependencies**:
- `LLMProvider` interface (for provider instances)
- `OrchestrationStrategy` interface (for strategy implementations)
- `HealthTracker` (for provider health monitoring)
- `CostTracker` (for cost tracking)

---

## Method: `extract_entities`

### Signature

```python
def extract_entities(
    self,
    email_text: str,
    strategy: str | None = None
) -> ExtractedEntities:
    pass
```

### Purpose
Extract entities from email text using the configured orchestration strategy.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `email_text` | str | Yes | Cleaned email body | Non-empty string, max 10,000 characters |
| `strategy` | str \| None | No | Override default strategy | One of: "failover", "consensus", "best_match", or None (use default) |

### Return Value

**Type**: `ExtractedEntities`

Same structure as LLMProvider interface, with additional provider metadata populated.

### Exceptions

| Exception | When Raised | Retry Recommended? |
|-----------|-------------|-------------------|
| `AllProvidersFailedError` | All enabled providers failed | No (check provider health) |
| `NoHealthyProvidersError` | No healthy providers available | No (wait for recovery) |
| `OrchestrationTimeoutError` | Overall timeout exceeded | Yes (with increased timeout) |
| `InvalidStrategyError` | Unknown strategy specified | No (fix strategy name) |
| `LLMAPIError` | Single provider error (in failover mode) | Yes (if transient) |

### Behavior

**Failover Strategy**:
1. Try primary provider first
2. If fails, try next provider in priority order
3. Return first successful result
4. If all fail, raise `AllProvidersFailedError`

**Consensus Strategy**:
1. Query all healthy providers in parallel
2. Merge results using weighted voting
3. Apply fuzzy matching for conflicts
4. Return merged result
5. If all fail, raise `AllProvidersFailedError`

**Best-Match Strategy**:
1. Query all healthy providers in parallel
2. Calculate aggregate confidence for each result
3. Return result with highest confidence
4. If all fail, raise `AllProvidersFailedError`

---

## Method: `get_provider_status`

### Signature

```python
def get_provider_status(self) -> dict[str, ProviderStatus]:
    pass
```

### Purpose
Get current status of all configured providers.

### Parameters
None

### Return Value

**Type**: `dict[str, ProviderStatus]`

**Structure**:
```python
class ProviderStatus(BaseModel):
    provider_name: str
    health_status: str                 # "healthy" or "unhealthy"
    enabled: bool
    success_rate: float               # 0.0-1.0
    average_response_time_ms: float
    total_api_calls: int
    last_success: datetime | None
    last_failure: datetime | None
    circuit_breaker_state: str        # "closed", "open", or "half_open"
```

### Example Return Value
```python
{
    "gemini": ProviderStatus(
        provider_name="gemini",
        health_status="healthy",
        enabled=True,
        success_rate=0.98,
        average_response_time_ms=1234.5,
        total_api_calls=1500,
        last_success=datetime(2025, 11, 8, 14, 30),
        last_failure=datetime(2025, 11, 8, 9, 15),
        circuit_breaker_state="closed"
    ),
    "claude": ProviderStatus(...),
    "openai": ProviderStatus(...)
}
```

---

## Method: `set_strategy`

### Signature

```python
def set_strategy(self, strategy_type: str) -> None:
    pass
```

### Purpose
Change the active orchestration strategy.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `strategy_type` | str | Yes | Strategy to activate | One of: "failover", "consensus", "best_match" |

### Return Value
None

### Exceptions
- `InvalidStrategyError` if strategy_type not recognized

### Side Effects
- Updates active strategy configuration
- Future `extract_entities` calls use new strategy (unless overridden)

---

## Method: `test_provider`

### Signature

```python
def test_provider(self, provider_name: str) -> bool:
    pass
```

### Purpose
Test connectivity and health of a specific provider.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `provider_name` | str | Yes | Provider to test | One of configured provider names |

### Return Value
**Type**: `bool`

- `True` if provider is healthy and responsive
- `False` if provider is unavailable or unhealthy

### Behavior
1. Make lightweight test API call to provider
2. Verify response is valid
3. Update health metrics
4. Return success/failure status

### Exceptions
- `InvalidProviderError` if provider_name not configured

---

## Constructor

### Signature

```python
def __init__(
    self,
    providers: dict[str, LLMProvider],
    config: OrchestrationConfig,
    health_tracker: HealthTracker,
    cost_tracker: CostTracker
):
    pass
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `providers` | dict[str, LLMProvider] | Yes | Map of provider_name → provider instance |
| `config` | OrchestrationConfig | Yes | Orchestration configuration |
| `health_tracker` | HealthTracker | Yes | Health tracking instance |
| `cost_tracker` | CostTracker | Yes | Cost tracking instance |

### Example

```python
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.llm_adapters.claude_adapter import ClaudeAdapter
from src.llm_adapters.openai_adapter import OpenAIAdapter
from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.config import OrchestrationConfig
from src.llm_adapters.health_tracker import HealthTracker
from src.llm_orchestrator.cost_tracker import CostTracker

# Initialize providers
providers = {
    "gemini": GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY")),
    "claude": ClaudeAdapter(api_key=os.getenv("ANTHROPIC_API_KEY")),
    "openai": OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))
}

# Configure orchestration
config = OrchestrationConfig(
    default_strategy="failover",
    provider_priority=["gemini", "claude", "openai"],
    timeout_seconds=90.0,
    unhealthy_threshold=5
)

# Initialize tracking
health_tracker = HealthTracker(data_dir="data/llm_health")
cost_tracker = CostTracker(data_dir="data/llm_health")

# Create orchestrator
orchestrator = LLMOrchestrator(
    providers=providers,
    config=config,
    health_tracker=health_tracker,
    cost_tracker=cost_tracker
)

# Use orchestrator
email_text = "어제 신세계와 본봄 파일럿 킥오프"
entities = orchestrator.extract_entities(email_text)
```

---

## Orchestration Strategies

### Strategy Interface

All strategy implementations MUST implement this interface:

```python
class OrchestrationStrategy(ABC):
    @abstractmethod
    def execute(
        self,
        providers: dict[str, LLMProvider],
        email_text: str,
        health_tracker: HealthTracker
    ) -> ExtractedEntities:
        pass
```

### Failover Strategy

**Class**: `FailoverStrategy`
**Module**: `src/llm_orchestrator/strategies/failover.py`

**Algorithm**:
```python
for provider_name in priority_order:
    if health_tracker.is_healthy(provider_name):
        try:
            return provider.extract_entities(email_text)
        except LLMAPIError:
            health_tracker.record_failure(provider_name)
            continue  # Try next provider
raise AllProvidersFailedError()
```

**Contract**:
- MUST try providers in priority order
- MUST skip unhealthy providers
- MUST record failures in health tracker
- MUST raise `AllProvidersFailedError` if all fail
- MUST complete failover in < 2 seconds per provider

### Consensus Strategy

**Class**: `ConsensusStrategy`
**Module**: `src/llm_orchestrator/strategies/consensus.py`

**Algorithm**:
```python
# Query all healthy providers in parallel
results = await asyncio.gather(*[
    provider.extract_entities(email_text)
    for name, provider in providers.items()
    if health_tracker.is_healthy(name)
])

# Merge results using weighted voting
merged = merge_results_with_fuzzy_matching(
    results,
    fuzzy_threshold=0.85
)
return merged
```

**Contract**:
- MUST query providers in parallel
- MUST skip unhealthy providers
- MUST use fuzzy matching (Jaro-Winkler threshold 0.85)
- MUST merge conflicts using weighted voting
- MUST require at least 2 providers to respond
- MUST improve accuracy by 10% over single provider

### Best-Match Strategy

**Class**: `BestMatchStrategy`
**Module**: `src/llm_orchestrator/strategies/best_match.py`

**Algorithm**:
```python
# Query all healthy providers in parallel
results = await asyncio.gather(*[
    provider.extract_entities(email_text)
    for name, provider in providers.items()
    if health_tracker.is_healthy(name)
])

# Calculate aggregate confidence for each result
best_result = max(
    results,
    key=lambda r: calculate_aggregate_confidence(r)
)
return best_result
```

**Aggregate confidence calculation**:
```python
def calculate_aggregate_confidence(result: ExtractedEntities) -> float:
    scores = [
        result.confidence.person,
        result.confidence.startup,
        result.confidence.partner,
        result.confidence.details,
        result.confidence.date
    ]
    return sum(scores) / len(scores)  # Average
```

**Contract**:
- MUST query providers in parallel
- MUST skip unhealthy providers
- MUST calculate aggregate confidence correctly
- MUST return result with highest aggregate confidence
- MUST handle tie-breaking (prefer first in priority order)

---

## Health Integration

The orchestrator MUST integrate with the HealthTracker:

### On Success
```python
health_tracker.record_success(
    provider_name=provider_name,
    response_time_ms=response_time
)
```

### On Failure
```python
health_tracker.record_failure(
    provider_name=provider_name,
    error_message=str(exception)
)
```

### Before Querying
```python
if not health_tracker.is_healthy(provider_name):
    # Skip this provider
    continue
```

---

## Cost Tracking Integration

The orchestrator MUST integrate with the CostTracker:

### After Successful Extraction
```python
cost_tracker.record_usage(
    provider_name=provider_name,
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    cost_usd=calculated_cost
)
```

---

## Testing Requirements

### Contract Tests

**File**: `tests/contract/test_orchestrator_contract.py`

**Required test cases**:

1. `test_orchestrator_failover_tries_providers_in_order`
```python
def test_orchestrator_failover_tries_providers_in_order():
    # Mock providers where first fails, second succeeds
    # Verify second provider is called
    pass
```

2. `test_orchestrator_consensus_queries_parallel`
```python
def test_orchestrator_consensus_queries_parallel():
    # Verify all healthy providers queried simultaneously
    pass
```

3. `test_orchestrator_best_match_selects_highest_confidence`
```python
def test_orchestrator_best_match_selects_highest_confidence():
    # Mock multiple results with different confidences
    # Verify highest confidence selected
    pass
```

4. `test_orchestrator_skips_unhealthy_providers`
```python
def test_orchestrator_skips_unhealthy_providers():
    # Mark provider as unhealthy
    # Verify it's not called
    pass
```

5. `test_orchestrator_records_health_metrics`
```python
def test_orchestrator_records_health_metrics():
    # Extract entities
    # Verify health_tracker.record_success called
    pass
```

6. `test_orchestrator_records_cost_metrics`
```python
def test_orchestrator_records_cost_metrics():
    # Extract entities
    # Verify cost_tracker.record_usage called
    pass
```

7. `test_orchestrator_raises_all_providers_failed`
```python
def test_orchestrator_raises_all_providers_failed():
    # Mock all providers to fail
    # Verify AllProvidersFailedError raised
    pass
```

### Integration Tests

**Files**:
- `tests/integration/test_failover_strategy.py`
- `tests/integration/test_consensus_strategy.py`
- `tests/integration/test_best_match_strategy.py`

---

## Summary

This contract ensures:
- ✅ Unified interface for multi-provider coordination
- ✅ Pluggable orchestration strategies
- ✅ Health tracking integration
- ✅ Cost tracking integration
- ✅ Proper error handling and recovery
- ✅ Testable and verifiable behavior
