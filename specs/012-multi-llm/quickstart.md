# Quick Start: Multi-LLM Provider Support

**Feature**: Multi-LLM Provider Support
**Branch**: `011-multi-llm`
**Date**: 2025-11-08

## Overview

This guide provides step-by-step instructions for configuring and using the multi-LLM provider support feature in CollabIQ.

---

## Prerequisites

1. **Python Environment**
   - Python 3.12+ installed
   - UV package manager installed

2. **API Keys**
   - Gemini API key (existing)
   - Claude (Anthropic) API key
   - OpenAI API key

3. **CollabIQ Installation**
   - CollabIQ project cloned and set up
   - Basic email processing working

---

## Installation

### Step 1: Install Dependencies

```bash
# Navigate to project root
cd /path/to/CollabIQ

# Add new LLM SDK dependencies
uv add anthropic  # Claude SDK
uv add openai     # OpenAI SDK
```

### Step 2: Configure API Keys

Add the new API keys to your `.env` file:

```bash
# Edit .env file
nano .env
```

Add these lines:

```bash
# Existing
GEMINI_API_KEY=your_gemini_api_key_here

# New - Claude (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# New - OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

**Security Note**: Never commit `.env` to version control. Ensure `.env` is in `.gitignore`.

### Step 3: Verify Installation

```bash
# Test imports
python -c "import anthropic; import openai; print('SDKs installed successfully')"
```

---

## Basic Usage

### Scenario 1: Using Failover Strategy (Default)

The failover strategy tries providers in priority order until one succeeds.

```python
from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.config import OrchestrationConfig
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.llm_adapters.claude_adapter import ClaudeAdapter
from src.llm_adapters.openai_adapter import OpenAIAdapter
from src.llm_adapters.health_tracker import HealthTracker
from src.llm_orchestrator.cost_tracker import CostTracker
import os

# Initialize providers
providers = {
    "gemini": GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY")),
    "claude": ClaudeAdapter(api_key=os.getenv("ANTHROPIC_API_KEY")),
    "openai": OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))
}

# Configure failover strategy
config = OrchestrationConfig(
    default_strategy="failover",
    provider_priority=["gemini", "claude", "openai"],  # Try Gemini first
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

# Extract entities from email
email_text = "어제 신세계와 본봄 파일럿 킥오프 미팅이 있었습니다."
entities = orchestrator.extract_entities(email_text)

print(f"Startup: {entities.startup_name}")          # "본봄"
print(f"Partner: {entities.partner_org}")           # "신세계"
print(f"Details: {entities.details}")               # "파일럿 킥오프 미팅"
print(f"Confidence (startup): {entities.confidence.startup}")
```

**What happens**:
1. Orchestrator tries Gemini first (highest priority)
2. If Gemini succeeds → return result
3. If Gemini fails → automatically try Claude
4. If Claude fails → try OpenAI
5. If all fail → raise `AllProvidersFailedError`

**Failover time**: <2 seconds per provider switch

---

### Scenario 2: Using Consensus Strategy

The consensus strategy queries multiple providers and merges their results for improved accuracy.

```python
# Change strategy to consensus
config = OrchestrationConfig(
    default_strategy="consensus",
    enabled_providers=["gemini", "claude"],  # Use 2 providers
    fuzzy_match_threshold=0.85,
    consensus_min_agreement=2,
    timeout_seconds=120.0
)

orchestrator = LLMOrchestrator(
    providers=providers,
    config=config,
    health_tracker=health_tracker,
    cost_tracker=cost_tracker
)

# Extract with consensus
entities = orchestrator.extract_entities(email_text)
```

**What happens**:
1. Queries Gemini and Claude in parallel
2. Receives two sets of extraction results
3. For each entity:
   - If values match → use agreed value
   - If values similar (Jaro-Winkler ≥ 0.85) → use more complete value
   - If values conflict → use higher confidence value
4. Return merged result

**Expected improvement**: 10% higher accuracy vs single provider

---

### Scenario 3: Using Best-Match Strategy

The best-match strategy queries multiple providers and selects the result with highest overall confidence.

```python
# Change strategy to best-match
config = OrchestrationConfig(
    default_strategy="best_match",
    enabled_providers=["gemini", "claude", "openai"],  # Use all 3
    timeout_seconds=120.0
)

orchestrator = LLMOrchestrator(
    providers=providers,
    config=config,
    health_tracker=health_tracker,
    cost_tracker=cost_tracker
)

# Extract with best-match
entities = orchestrator.extract_entities(email_text)
```

**What happens**:
1. Queries all 3 providers in parallel
2. Calculates aggregate confidence for each result:
   ```
   aggregate = (conf.person + conf.startup + conf.partner + conf.details + conf.date) / 5
   ```
3. Selects and returns the result with highest aggregate confidence

---

## CLI Usage

### View Provider Status

```bash
collabiq llm status
```

**Output**:
```
LLM Provider Status:

Provider: gemini
  Status: healthy
  Success Rate: 98.2% (1,473/1,500 calls)
  Avg Response Time: 1,234ms
  Circuit Breaker: closed
  Last Success: 2025-11-08 14:32:18 UTC
  Last Failure: 2025-11-08 09:15:42 UTC

Provider: claude
  Status: healthy
  Success Rate: 96.5% (1,158/1,200 calls)
  Avg Response Time: 1,834ms
  Circuit Breaker: closed
  Last Success: 2025-11-08 14:30:05 UTC

Provider: openai
  Status: unhealthy (5 consecutive failures)
  Success Rate: 85.0% (425/500 calls)
  Avg Response Time: 2,145ms
  Circuit Breaker: open (recovery in 45 seconds)
  Last Failure: 2025-11-08 14:31:30 UTC
  Last Error: Rate limit exceeded (429)
```

### View Detailed Status with Costs

```bash
collabiq llm status --detailed
```

**Additional output**:
```
Cost Metrics:

Provider: gemini
  Total Calls: 1,500
  Input Tokens: 635,000
  Output Tokens: 127,000
  Total Cost: $85.73
  Avg Cost/Email: $0.057

Provider: claude
  Total Calls: 1,200
  Input Tokens: 527,000
  Output Tokens: 108,000
  Total Cost: $3,201.00
  Avg Cost/Email: $2.668

Provider: openai
  Total Calls: 500
  Input Tokens: 215,000
  Output Tokens: 43,000
  Total Cost: $139.75
  Avg Cost/Email: $0.280

Orchestration:
  Active Strategy: failover
  Priority Order: gemini → claude → openai
```

### Test Provider Connectivity

```bash
# Test specific provider
collabiq llm test gemini
```

**Output**:
```
Testing gemini connectivity...
✓ API key valid
✓ Model accessible
✓ Response time: 1,234ms
✓ gemini is healthy
```

```bash
# Test all providers
collabiq llm test --all
```

**Output**:
```
Testing all providers...

gemini:  ✓ healthy (1,234ms)
claude:  ✓ healthy (1,834ms)
openai:  ✗ unhealthy (Rate limit exceeded)
```

### Change Orchestration Strategy

```bash
# Switch to consensus mode
collabiq llm set-strategy consensus
```

**Output**:
```
Orchestration strategy changed to: consensus
Enabled providers: gemini, claude
```

```bash
# Switch to best-match mode
collabiq llm set-strategy best-match
```

```bash
# Switch back to failover (default)
collabiq llm set-strategy failover
```

---

## Configuration

### Provider Configuration File

Location: `data/llm_health/provider_config.json`

```json
{
  "gemini": {
    "provider_name": "gemini",
    "display_name": "Gemini 2.0 Flash",
    "model_id": "gemini-2.0-flash-exp",
    "api_key_env_var": "GEMINI_API_KEY",
    "enabled": true,
    "priority": 1,
    "timeout_seconds": 60.0,
    "max_retries": 3,
    "input_token_price": 0.075,
    "output_token_price": 0.30
  },
  "claude": {
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
  },
  "openai": {
    "provider_name": "openai",
    "display_name": "GPT-5 Mini",
    "model_id": "gpt-5-mini",
    "api_key_env_var": "OPENAI_API_KEY",
    "enabled": true,
    "priority": 3,
    "timeout_seconds": 60.0,
    "max_retries": 3,
    "input_token_price": 0.25,
    "output_token_price": 2.00
  }
}
```

**To disable a provider**: Set `"enabled": false`
**To change priority**: Adjust `"priority"` numbers (1 = highest)

### Orchestration Strategy Configuration

Location: `data/llm_health/orchestration_config.json`

```json
{
  "active_strategy": "failover",
  "strategies": {
    "failover": {
      "strategy_type": "failover",
      "enabled_providers": ["gemini", "claude", "openai"],
      "provider_priority_order": ["gemini", "claude", "openai"],
      "unhealthy_threshold": 5,
      "parallel_queries": false,
      "timeout_seconds": 90.0
    },
    "consensus": {
      "strategy_type": "consensus",
      "enabled_providers": ["gemini", "claude"],
      "unhealthy_threshold": 5,
      "consensus_min_agreement": 2,
      "fuzzy_match_threshold": 0.85,
      "abstention_confidence_threshold": 0.25,
      "parallel_queries": true,
      "timeout_seconds": 120.0
    },
    "best_match": {
      "strategy_type": "best_match",
      "enabled_providers": ["gemini", "claude", "openai"],
      "unhealthy_threshold": 5,
      "parallel_queries": true,
      "timeout_seconds": 120.0
    }
  }
}
```

---

## Monitoring

### Health Metrics File

Location: `data/llm_health/health_metrics.json`

Automatically updated after each API call. Contains:
- Success/failure counts
- Consecutive failures
- Circuit breaker state
- Last success/failure timestamps
- Error messages

**View live health data**:
```bash
cat data/llm_health/health_metrics.json | python -m json.tool
```

### Cost Metrics File

Location: `data/llm_health/cost_metrics.json`

Tracks cumulative costs per provider.

**View cost summary**:
```bash
cat data/llm_health/cost_metrics.json | python -m json.tool
```

---

## Troubleshooting

### Problem: All providers failing

**Symptoms**: `AllProvidersFailedError` raised

**Diagnosis**:
```bash
collabiq llm status
```

**Solutions**:
1. Check API keys in `.env`
2. Verify internet connectivity
3. Check provider status pages:
   - Gemini: https://status.cloud.google.com/
   - Claude: https://status.anthropic.com/
   - OpenAI: https://status.openai.com/
4. Review error messages in `data/llm_health/health_metrics.json`

### Problem: Provider marked unhealthy

**Symptoms**: Provider shows "unhealthy" in status, circuit breaker "open"

**Diagnosis**:
```bash
collabiq llm status --detailed
# Check "Last Error" field
```

**Solutions**:
1. **Rate limit (429)**:
   - Wait for rate limit to reset
   - Circuit breaker will auto-recover after timeout
   - Consider reducing request volume

2. **Authentication error (401/403)**:
   - Verify API key in `.env` is correct
   - Check API key hasn't expired
   - Manually reset: `collabiq llm reset <provider>`

3. **Timeout errors**:
   - Increase timeout in config
   - Check network latency
   - Verify provider service status

### Problem: Consensus mode showing same results as single provider

**Symptoms**: No accuracy improvement with consensus

**Possible causes**:
1. Providers returning very similar outputs (expected for well-formed emails)
2. Fuzzy matching threshold too low
3. Only one provider responding (check health status)

**Diagnosis**:
```bash
# Enable debug logging to see individual provider responses
export LOG_LEVEL=DEBUG
python -m src.llm_orchestrator.orchestrator
```

### Problem: Costs higher than expected

**Symptoms**: High costs in `cost_metrics.json`

**Diagnosis**:
```bash
collabiq llm status --detailed
# Review "Avg Cost/Email" per provider
```

**Solutions**:
1. **Using expensive models**: Claude Sonnet 4.5 is ~40x more expensive than Gemini
   - Consider using failover with cheaper providers first
   - Reserve expensive providers for fallback only

2. **Consensus mode querying multiple providers**:
   - Switch to failover mode for normal operation
   - Use consensus only for critical/high-value emails

3. **High token usage**:
   - Review prompt templates (ensure not too verbose)
   - Check email preprocessing (remove unnecessary content)

---

## Best Practices

### 1. Failover for Production

Use failover as default strategy for production:
- Lowest latency (sequential, not parallel)
- Lowest cost (tries cheap providers first)
- High availability (automatic fallback)

### 2. Consensus for Critical Emails

Use consensus mode selectively:
- Flag high-value emails for consensus processing
- 10% accuracy improvement worth the extra cost
- Parallel queries keep latency reasonable (~2-3x single provider)

### 3. Provider Priority Order

Order providers by cost:
1. Gemini 2.0 Flash ($0.075 input / $0.30 output)
2. OpenAI GPT-5 Mini ($0.25 input / $2.00 output)
3. Claude Sonnet 4.5 ($3.00 input / $15.00 output)

**Rationale**: Gemini cheapest, so try first. Claude most expensive, so use as last resort.

### 4. Monitor Health Regularly

```bash
# Add to cron for daily monitoring
0 9 * * * /usr/bin/collabiq llm status --detailed >> /var/log/collabiq/llm_health.log
```

### 5. Set Budget Alerts

Track costs daily and set alerts:

```python
# Example: Alert if daily cost exceeds threshold
from src.llm_orchestrator.cost_tracker import CostTracker

tracker = CostTracker()
daily_cost = tracker.get_daily_cost()

if daily_cost > 100.00:  # $100/day threshold
    send_alert(f"LLM costs exceeded threshold: ${daily_cost:.2f}")
```

---

## Next Steps

1. **Test with real emails**: Process sample emails through orchestrator
2. **Monitor performance**: Track accuracy, latency, and costs
3. **Tune configuration**: Adjust timeouts, thresholds based on observed behavior
4. **Set up alerts**: Monitor health and cost metrics
5. **Review logs**: Check for patterns in failures or high costs

For implementation details, see:
- [plan.md](plan.md) - Implementation plan
- [data-model.md](data-model.md) - Entity definitions
- [contracts/](contracts/) - API contracts

For issues or questions, refer to the feature specification: [spec.md](spec.md)
