# Quick API Test Guide

This guide will help you test the LLM Orchestrator with real Claude and OpenAI APIs.

## Prerequisites

You need API keys for the providers you want to test. At minimum, you should already have:
- ✓ `GEMINI_API_KEY` (from Phase 004)

For Phase 3b testing, you'll also want:
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `OPENAI_API_KEY` - Get from https://platform.openai.com/

## Step 1: Add API Keys to .env

1. Copy `.env.example` to `.env` if you haven't already:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # LLM API Configuration
   GEMINI_API_KEY=your_actual_gemini_api_key
   GEMINI_MODEL=gemini-2.5-flash
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key
   OPENAI_API_KEY=your_actual_openai_api_key
   ```

3. **IMPORTANT**: Make sure `.env` is in your `.gitignore` (it should already be there)

## Step 2: Run the Quick Test Script

```bash
python test_real_apis.py
```

This script will:
1. ✓ Check which API keys are available
2. ✓ Initialize the orchestrator with available providers
3. ✓ Test failover strategy (sequential provider attempts)
4. ✓ Test consensus strategy (parallel queries with voting)
5. ✓ Test best-match strategy (highest confidence selection)
6. ✓ Display cost tracking metrics
7. ✓ Display provider health status

**Expected output:**
```
================================================================================
LLM Orchestrator - Real API Integration Test
================================================================================
API Key Status:
  GEMINI_API_KEY: ✓ Available
  ANTHROPIC_API_KEY: ✓ Available
  OPENAI_API_KEY: ✓ Available

Initializing LLMOrchestrator...
✓ Orchestrator initialized with 3 providers: gemini, claude, openai

================================================================================
TEST 1: Failover Strategy
================================================================================
Email text: 어제 신세계와 본봄 킥오프 미팅 진행했습니다...

✓ Extraction successful!
  Provider used: gemini
  Person: 김민수 (confidence: 0.95)
  Startup: 본봄 (confidence: 0.92)
  ...
```

## Step 3: Test CLI Commands

After running the test script, try these CLI commands:

### View provider status
```bash
python -m src.collabiq.cli llm status
```

### View detailed status with cost metrics
```bash
python -m src.collabiq.cli llm status --detailed
```

### Test individual provider connectivity
```bash
python -m src.collabiq.cli llm test gemini
python -m src.collabiq.cli llm test claude
python -m src.collabiq.cli llm test openai
```

### Change orchestration strategy
```bash
python -m src.collabiq.cli llm set-strategy consensus
python -m src.collabiq.cli llm set-strategy best_match
python -m src.collabiq.cli llm set-strategy failover
```

## What to Look For

### 1. Extraction Accuracy
- Korean text should be correctly identified
- Person names, company names, dates should be extracted
- Confidence scores should be reasonable (0.7+)

### 2. Failover Behavior
- If Gemini fails, it should automatically try Claude
- If Claude fails, it should try OpenAI
- Health status should reflect failures

### 3. Consensus Results
- Should query all available providers in parallel
- Should use fuzzy matching for Korean text
- Should select the most agreed-upon result

### 4. Cost Tracking
- Should show token usage for each provider
- Should calculate costs correctly:
  - Gemini: $0 (free tier)
  - Claude: $3/1M input tokens, $15/1M output tokens
  - OpenAI: $0.15/1M input tokens, $0.60/1M output tokens

### 5. Health Monitoring
- Success rate should be tracked
- Response times should be recorded
- Circuit breaker should open after 3+ consecutive failures

## Troubleshooting

### Issue: "No providers available"
**Solution**: Check that at least one API key is set in `.env`

### Issue: "API Error" from provider
**Solution**:
1. Verify your API key is correct
2. Check your API quota/billing
3. Check provider status page

### Issue: "Consensus requires at least 2 providers"
**Solution**: Add API keys for at least 2 providers to test consensus

### Issue: Import errors
**Solution**: Make sure you're running from the project root directory

## Cost Estimate

Each test run makes approximately:
- Failover: 1 API call (Gemini only, unless it fails)
- Consensus: 3 API calls (all providers in parallel)
- Best-match: 3 API calls (all providers in parallel)

**Total**: ~7 API calls per test run

**Estimated cost per run**:
- Gemini: $0.00 (free)
- Claude: ~$0.0001 (assuming ~500 tokens)
- OpenAI: ~$0.00002 (assuming ~500 tokens)
- **Total**: < $0.01 per test run

## Next Steps

After confirming the quick test works:

1. **Integrate with email pipeline** - Test with real emails from Gmail
2. **Phase 3c** - Implement quality metrics and historical tracking
3. **Benchmark accuracy** - Compare single-provider vs consensus
4. **Optimize costs** - Fine-tune provider priority based on cost/accuracy

## Files Generated

The test will create these files:
- `data/llm_health/health_metrics.json` - Provider health data
- `data/llm_health/cost_metrics.json` - Cost tracking data
- Logs in console output

You can inspect these JSON files to see detailed metrics.

---

**Estimated time**: 5-10 minutes
**Prerequisites**: API keys for at least 1 provider (Gemini recommended)
**Cost**: < $0.01 per test run
