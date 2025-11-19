# Quality-Based Routing - Manual Test Results

**Date**: 2025-11-09
**Phase**: 013 - Quality Metrics & Intelligent Routing
**Tester**: Manual verification
**Status**: ✅ **PASSED**

---

## Test Objectives

Verify that quality-based routing:
1. ✅ Selects providers based on historical quality metrics
2. ✅ Updates quality metrics for all providers (when using all-providers strategy)
3. ✅ Uses quality score calculation (40% confidence + 30% completeness + 30% validation)
4. ✅ Logs provider selection decisions with rationale

---

## Test 1: Quality-Based Provider Selection

### Setup
- **Quality Routing**: Enabled
- **Strategy**: Failover
- **Available Providers**: gemini, claude, openai
- **Historical Metrics**: Yes (populated)

### Historical Quality Scores

| Provider | Total Extractions | Avg Confidence | Field Completeness | Validation Rate | Quality Score |
|----------|-------------------|----------------|-------------------|-----------------|---------------|
| **Claude** | 12 | 74.35% | 81.7% | 100% | **84.24** ⭐ |
| **OpenAI** | 2 | 72.40% | 80.0% | 100% | 83.00 |
| **Gemini** | 3 | 62.00% | 73.3% | 100% | 76.80 |

### Test Execution

```bash
python -c "
from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.types import OrchestrationConfig

config = OrchestrationConfig(
    default_strategy='failover',
    enable_quality_routing=True
)

orchestrator = LLMOrchestrator.from_config(config)
selected = orchestrator.quality_tracker.select_provider_by_quality(
    ['gemini', 'claude', 'openai']
)
print(f'Selected provider: {selected}')
"
```

### Results

```
✅ Quality-based selection result: claude
   (Expected: Provider with highest quality score)
```

**Log Output:**
```
llm_orchestrator.quality_tracker - INFO - Quality-based provider selection:
  claude (score=84.24/100, confidence=0.74, validation=100.0%, completeness=81.7%)
  from 3 providers with metrics
```

### ✅ PASSED
- Claude correctly selected as it has the highest quality score (84.24)
- Selection logged with detailed rationale
- Quality score correctly calculated from historical metrics

---

## Test 2: All-Providers Strategy with Quality Selection

### Setup
- **Strategy**: All-Providers
- **Selection Mode**: quality_based
- **Test Data**: Simple partnership email

### Test Execution

```bash
python -c "
config = OrchestrationConfig(
    default_strategy='all_providers',
    enable_quality_routing=True,
    all_providers_selection_mode='quality_based'
)

orchestrator = LLMOrchestrator.from_config(config)
result = orchestrator.extract_entities(
    email_text='Partnership email...',
    strategy='all_providers'
)
"
```

### Results

**Provider Execution:**
```
INFO - Executing AllProvidersStrategy with 3 providers
INFO - Provider gemini succeeded (confidence: 54.00%)
INFO - Provider claude succeeded (confidence: 49.40%)
INFO - Provider openai succeeded (confidence: 54.00%)
INFO - Results: 3 succeeded, 0 failed
```

**Provider Selection:**
```
INFO - Selected claude by quality (score: 0.84)
INFO - Selected result from claude out of 3 successful providers
```

**Metrics Recording:**
```
INFO - Recorded quality metrics for gemini: confidence=0.54, completeness=60.0%, validation=PASS
INFO - Recorded quality metrics for claude: confidence=0.49, completeness=60.0%, validation=PASS
INFO - Recorded quality metrics for openai: confidence=0.54, completeness=60.0%, validation=PASS
```

### Key Observations

1. **All Providers Called** ✅
   - Gemini, Claude, and OpenAI all processed the email
   - All 3 succeeded with varying confidence levels

2. **Quality-Based Selection** ✅
   - Claude selected despite having LOWER confidence (49.40%) on this specific extraction
   - Selection based on historical quality score (84.24), not current confidence
   - Demonstrates intelligence: prefers provider with proven track record

3. **Metrics Updated for ALL Providers** ✅
   - Quality metrics recorded for gemini (not selected)
   - Quality metrics recorded for claude (selected)
   - Quality metrics recorded for openai (not selected)
   - Continuous learning from all providers

### ✅ PASSED
- All providers executed in parallel
- Claude selected based on historical quality (not current confidence)
- Quality metrics updated for ALL providers (essential for continuous learning)

---

## Test 3: Quality Metrics Persistence

### Before Test
```bash
$ cat data/llm_health/quality_metrics.json
{
    "claude": {"total_extractions": 12, ...},
    "gemini": {"total_extractions": 3, ...},
    "openai": {"total_extractions": 2, ...}
}
```

### After All-Providers Test
```bash
$ cat data/llm_health/quality_metrics.json
{
    "claude": {"total_extractions": 13, ...},  # +1
    "gemini": {"total_extractions": 4, ...},   # +1
    "openai": {"total_extractions": 3, ...}    # +1
}
```

### ✅ PASSED
- Quality metrics persisted to disk
- All provider metrics updated (not just selected provider)
- Extraction counts incremented correctly

---

## Test 4: Provider Selection Logging

### Log Analysis

**Quality tracker initialization:**
```
llm_orchestrator.quality_tracker - INFO - Loaded quality metrics for 3 provider(s)
llm_orchestrator.quality_tracker - INFO - QualityTracker initialized with data_dir=data/llm_health
```

**Provider selection with rationale:**
```
llm_orchestrator.quality_tracker - INFO - Quality-based provider selection:
  claude (score=84.24/100, confidence=0.74, validation=100.0%, completeness=81.7%)
  from 3 providers with metrics
```

**Strategy execution:**
```
llm_orchestrator.strategies.all_providers - INFO - Selected claude by quality (score: 0.84)
llm_orchestrator.strategies.all_providers - INFO - Selected result from claude out of 3 successful providers
```

### ✅ PASSED
- Clear logging of quality-based decisions
- Detailed metrics shown in logs (score, confidence, validation, completeness)
- Rationale provided for provider selection

---

## Test 5: Quality Score Calculation Verification

### Formula
```
Quality Score = (0.4 × confidence) + (0.3 × completeness/100) + (0.3 × validation/100)
```

### Manual Verification for Claude

**Input Metrics:**
- Average confidence: 0.7435 (74.35%)
- Field completeness: 81.7%
- Validation rate: 100%

**Calculation:**
```
Quality Score = (0.4 × 0.7435) + (0.3 × 0.817) + (0.3 × 1.0)
             = 0.2974 + 0.2451 + 0.3000
             = 0.8425
             = 84.25/100
```

**Logged Score:** 84.24/100 ✅

**Difference:** 0.01 (rounding)

### ✅ PASSED
- Quality score calculation matches expected formula
- Weights correctly applied (40% confidence, 30% completeness, 30% validation)

---

## Summary

### Test Results

| Test | Status | Details |
|------|--------|---------|
| Quality-Based Selection | ✅ PASSED | Claude selected based on highest quality score (84.24) |
| All-Providers Strategy | ✅ PASSED | All 3 providers called, metrics recorded for all |
| Metrics Persistence | ✅ PASSED | Quality metrics saved to disk after extraction |
| Provider Selection Logging | ✅ PASSED | Clear rationale logged for provider selection |
| Quality Score Calculation | ✅ PASSED | Formula correctly implemented and applied |

### Success Criteria

- ✅ **SC-1**: Quality-based routing selects best provider based on historical metrics
- ✅ **SC-2**: All-providers strategy collects metrics from ALL providers
- ✅ **SC-3**: Quality metrics persist across sessions
- ✅ **SC-4**: Provider selection logged with detailed rationale
- ✅ **SC-5**: Quality score calculation accurate and consistent

### Key Findings

1. **Intelligent Selection**: Quality routing prefers provider with best historical performance, even if current extraction has lower confidence
   - Claude selected with 49.40% confidence (historical: 84.24 quality)
   - Over Gemini with 54.00% confidence (historical: 76.80 quality)
   - Demonstrates learning from past performance

2. **Continuous Learning**: All-providers strategy enables continuous quality improvement
   - All 3 providers tested on same email
   - Metrics updated for all providers (not just selected one)
   - Enables data-driven provider comparison

3. **Observable Decisions**: Clear logging provides transparency
   - Quality scores shown in logs
   - Selection rationale documented
   - Enables debugging and optimization

### Recommendations

1. ✅ **Use all-providers strategy in testing**: Collect comprehensive quality data
2. ✅ **Monitor quality scores**: Track provider performance over time
3. ✅ **Review selection logs**: Understand why providers are selected
4. ✅ **Enable quality routing in production**: Leverage historical performance data

---

## Related Documentation

- [E2E Testing Guide](E2E_TESTING.md) - Multi-LLM E2E testing
- [All-Providers Strategy](../architecture/ALL_PROVIDERS_STRATEGY.md) - Strategy details
- [CLI Reference](../CLI_REFERENCE.md) - Complete CLI commands

---

**Version**: 1.0.0
**Last Updated**: 2025-11-09
**Phase**: 013 Complete ✅
