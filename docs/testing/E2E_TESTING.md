# End-to-End Testing with Multi-LLM Support

**Status**: ✅ Updated for Phase 013 (Quality Metrics & Intelligent Routing)
**Last Updated**: 2025-11-09

---

## Overview

The E2E testing framework validates the complete CollabIQ pipeline from email ingestion through Notion write operations. As of Phase 013, E2E tests now support **multi-LLM orchestration** and **quality metrics tracking**, ensuring tests mirror production behavior.

## Key Features

### Multi-LLM Orchestration

E2E tests now use `LLMOrchestrator` instead of a single Gemini adapter, enabling:
- **Multiple providers**: Test with Gemini, Claude, and OpenAI
- **Orchestration strategies**: Validate different selection approaches
- **Quality-based routing**: Test intelligent provider selection
- **Automatic metrics collection**: Track quality data during testing

### Quality Metrics Tracking

Quality metrics are automatically collected and reported:
- Per-provider confidence scores
- Field completeness percentages
- Validation success rates
- Per-field confidence averages

## Usage

### Basic Usage

```bash
# Run E2E tests with all emails (default: failover strategy)
uv run python scripts/run_e2e_tests.py --all

# Process single email
uv run python scripts/run_e2e_tests.py --email-id msg_001
```

### Multi-LLM Strategies

Test different orchestration strategies:

```bash
# Failover strategy (sequential provider attempts)
uv run python scripts/run_e2e_tests.py --all --strategy failover

# Consensus strategy (majority voting across providers)
uv run python scripts/run_e2e_tests.py --all --strategy consensus

# Best-match strategy (select highest confidence result)
uv run python scripts/run_e2e_tests.py --all --strategy best_match

# All-providers strategy (collect metrics from ALL providers)
uv run python scripts/run_e2e_tests.py --all --strategy all_providers
```

### Quality-Based Routing

Enable intelligent provider selection based on historical performance:

```bash
# Enable quality-based routing
uv run python scripts/run_e2e_tests.py --all --quality-routing

# Combine with specific strategy
uv run python scripts/run_e2e_tests.py --all --strategy consensus --quality-routing
```

### Generating Reports

```bash
# Generate detailed error report
uv run python scripts/run_e2e_tests.py --all --report

# Resume interrupted test run
uv run python scripts/run_e2e_tests.py --resume 20251109_143000
```

## Orchestration Strategies

### Failover (Default)
- **Behavior**: Try providers sequentially until success
- **Use Case**: Fastest execution, prioritizes speed
- **Best For**: Regular testing, CI/CD pipelines
- **Metrics**: Only tracks metrics from successful provider

```bash
uv run python scripts/run_e2e_tests.py --all --strategy failover
```

### Consensus
- **Behavior**: Query multiple providers, use majority vote
- **Use Case**: High-accuracy requirements
- **Best For**: Critical extractions, validation testing
- **Metrics**: Tracks metrics from all providers queried

```bash
uv run python scripts/run_e2e_tests.py --all --strategy consensus
```

### Best-Match
- **Behavior**: Query all providers, select highest confidence
- **Use Case**: Quality optimization
- **Best For**: Testing confidence scoring, provider comparison
- **Metrics**: Tracks metrics from all providers

```bash
uv run python scripts/run_e2e_tests.py --all --strategy best_match
```

### All-Providers (Recommended for Testing)
- **Behavior**: Query ALL providers in parallel
- **Use Case**: Comprehensive quality data collection
- **Best For**: Provider comparison, quality metrics validation
- **Metrics**: Tracks metrics from ALL providers (essential for quality-based routing)

```bash
uv run python scripts/run_e2e_tests.py --all --strategy all_providers
```

## Quality Metrics Output

After test completion, quality metrics are automatically:

1. **Displayed in console output**:
   ```
   ======================================================================
   Quality Metrics Summary
   ======================================================================

   GEMINI:
     Extractions: 10
     Avg Confidence: 88.00%
     Field Completeness: 100.0%
     Validation Rate: 100.0%

   CLAUDE:
     Extractions: 10
     Avg Confidence: 74.35%
     Field Completeness: 81.7%
     Validation Rate: 100.0%

   OPENAI:
     Extractions: 10
     Avg Confidence: 72.40%
     Field Completeness: 80.0%
     Validation Rate: 100.0%
   ======================================================================
   ```

2. **Saved to JSON report**:
   ```
   data/e2e_test/reports/{run_id}_quality_metrics.json
   ```

3. **Persisted to global metrics**:
   ```
   data/llm_health/quality_metrics.json
   ```

## Test Run Outputs

E2E tests generate multiple output files:

```
data/e2e_test/
├── runs/
│   └── {run_id}.json                      # Test run metadata
├── reports/
│   ├── {run_id}_summary.md                # Human-readable summary
│   ├── {run_id}_errors.md                 # Detailed error report (--report flag)
│   └── {run_id}_quality_metrics.json      # Quality metrics summary
└── test_email_ids.json                    # Test email selection
```

## Integration with Production

E2E tests now use the same components as production:

| Component | Test | Production |
|-----------|------|------------|
| LLM Orchestration | ✅ `LLMOrchestrator` | ✅ `LLMOrchestrator` |
| Quality Tracking | ✅ Automatic | ✅ Automatic |
| Cost Tracking | ✅ Automatic | ✅ Automatic |
| Health Monitoring | ✅ Enabled | ✅ Enabled |
| Strategies | ✅ All supported | ✅ All supported |
| Quality Routing | ✅ Optional | ✅ Configurable |

## Backward Compatibility

The legacy `gemini_adapter` parameter is still supported but deprecated:

```python
# Deprecated (still works)
runner = E2ERunner(gemini_adapter=gemini_adapter)

# Recommended (new approach)
runner = E2ERunner(
    llm_orchestrator=None,  # Auto-initialized
    orchestration_strategy="failover",
    enable_quality_routing=False
)
```

## Testing Quality-Based Routing

To test quality-based routing, you need historical metrics:

1. **Populate metrics first**:
   ```bash
   uv run python scripts/populate_quality_metrics.py
   ```

2. **Run E2E tests with quality routing**:
   ```bash
   uv run python scripts/run_e2e_tests.py --all --quality-routing
   ```

3. **Verify provider selection**:
   - Check logs for "Selected provider: {name}"
   - Review quality metrics report
   - Compare against expected provider rankings

## Performance Considerations

### Strategy Performance

| Strategy | Speed | Cost | Quality Data |
|----------|-------|------|--------------|
| Failover | Fast | Low | Single provider |
| Consensus | Slow | High | Multiple providers |
| Best-Match | Slow | High | All providers |
| All-Providers | Slow | Highest | ALL providers (recommended for testing) |

### Recommendations

- **CI/CD**: Use `failover` for speed
- **Quality validation**: Use `all_providers` to collect comprehensive metrics
- **Cost-sensitive**: Use `failover` with single provider
- **Accuracy testing**: Use `consensus` or `best_match`

## Common Issues

### No Quality Metrics Available

**Problem**: Quality metrics report is empty

**Solution**:
- Ensure `llm_orchestrator` is initialized (not using legacy mode)
- Check that at least one extraction succeeded
- Verify quality tracker is enabled

### Quality Routing Not Working

**Problem**: Quality routing doesn't select expected provider

**Solution**:
- Populate metrics first: `python scripts/populate_quality_metrics.py`
- Verify `--quality-routing` flag is set
- Check `data/llm_health/quality_metrics.json` has data
- Review logs for provider selection reasoning

### Strategy Failures

**Problem**: All providers fail with certain strategy

**Solution**:
- Check API keys are configured for all providers
- Verify provider health status
- Try `failover` strategy to identify failing provider
- Review `data/e2e_test/reports/{run_id}_errors.md`

## Examples

### Complete Workflow

```bash
# 1. Populate quality metrics (one-time setup)
uv run python scripts/populate_quality_metrics.py

# 2. Run E2E tests with all-providers strategy (collect metrics)
uv run python scripts/run_e2e_tests.py --all --strategy all_providers --report

# 3. Test quality-based routing
uv run python scripts/run_e2e_tests.py --all --quality-routing --report

# 4. Compare provider performance
uv run collabiq llm compare --detailed

# 5. Review quality metrics from E2E test
cat data/e2e_test/reports/*/quality_metrics.json
```

### Testing Specific Scenarios

```bash
# Test with single email and consensus
uv run python scripts/run_e2e_tests.py --email-id msg_001 --strategy consensus

# Test quality routing with best-match
uv run python scripts/run_e2e_tests.py --all --strategy best_match --quality-routing

# Resume interrupted run
uv run python scripts/run_e2e_tests.py --resume 20251109_143000
```

## Next Steps

After running E2E tests with quality metrics:

1. Review quality metrics report
2. Compare provider performance with `collabiq llm compare`
3. Adjust quality thresholds if needed
4. Enable quality routing in production config
5. Monitor production metrics vs test metrics

## Related Documentation

- [CLI Reference](../CLI_REFERENCE.md) - Complete CLI command documentation
- [All-Providers Strategy](../architecture/ALL_PROVIDERS_STRATEGY.md) - Strategy details
- [Quality Metrics Demo](../validation/QUALITY_METRICS_DEMO_RESULTS.md) - Example results
- [Quickstart Guide](../setup/quickstart.md) - Quality metrics testing section

---

**Version**: 2.0.0
**Last Updated**: 2025-11-09 (Phase 013 complete)
