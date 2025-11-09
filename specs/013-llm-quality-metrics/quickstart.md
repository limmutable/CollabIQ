# Quickstart Guide: LLM Quality Metrics & Tracking

**Feature**: 013-llm-quality-metrics
**Audience**: System administrators and developers
**Time to Complete**: 10-15 minutes

## Overview

This guide walks you through using the LLM quality metrics tracking system to monitor provider performance, compare quality across providers, and implement quality-based routing decisions.

---

## Prerequisites

- CollabIQ system running with at least one LLM provider configured (Gemini, Claude, or OpenAI)
- Email extractions have been processed (at least 10-20 emails recommended for meaningful metrics)
- Access to the admin CLI (`collabiq` command)

---

## Step 1: View Quality Metrics for a Provider

Check the quality metrics for a specific LLM provider:

```bash
collabiq status --provider gemini
```

**Expected Output**:
```
📊 Quality Metrics for Gemini
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Extractions:        150
Validation Success Rate:  94.7%
Average Confidence:       89.0%
Field Completeness:       96.0%
Quality Trend:            ↗ improving

Per-Field Confidence:
  • person_in_charge:     91%
  • startup_name:         93%
  • partner_org:          87%
  • details:              89%
  • date:                 85%

Notion Matching Success:  88.5%
Last Updated:             2025-11-09 12:00:00 UTC
```

**What This Tells You**:
- **Validation Success Rate**: Percentage of extractions that passed validation (no missing required fields, valid formats)
- **Average Confidence**: Mean confidence score across all extractions (0-100%)
- **Field Completeness**: Percentage of extractions where all 5 entities were extracted
- **Quality Trend**: Whether quality is improving (↗), stable (→), or degrading (↘) over recent extractions
- **Per-Field Confidence**: How confident the LLM is for each specific entity type
- **Notion Matching Success**: How often extracted entities successfully matched to existing Notion database records

---

## Step 2: Compare All Providers

Generate a cross-provider quality comparison:

```bash
collabiq status --compare
```

**Expected Output**:
```
🏆 Provider Quality Comparison
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quality Rankings:
  1. Claude      92.0%  (142/150 validated, 0.89 avg confidence)
  2. Gemini      88.5%  (135/148 validated, 0.86 avg confidence)
  3. OpenAI      85.3%  (128/152 validated, 0.83 avg confidence)

Value Rankings (Quality per Cost):
  1. Claude      18.4   (92% quality at $0.005/email)
  2. Gemini      16.2   (88.5% quality at $0.0055/email)
  3. OpenAI      12.8   (85.3% quality at $0.0067/email)

💡 Recommendation: Claude
   Provides 92% confidence at $0.005/email (value score: 18.4),
   outperforming Gemini (16.2) and OpenAI (12.8)
```

**What This Tells You**:
- **Quality Rankings**: Providers sorted by overall extraction quality (validation success + confidence)
- **Value Rankings**: Providers sorted by quality-to-cost ratio (best value for money)
- **Recommendation**: System's suggested provider based on balancing quality and cost

**Decision Making**:
- If quality is paramount: Choose top quality-ranked provider
- If budget is constrained: Choose top value-ranked provider
- If both matter: Follow system recommendation

---

## Step 3: Set Quality Thresholds

Configure minimum acceptable quality levels for automated provider selection:

```bash
collabiq config quality-thresholds set \
  --min-confidence 0.85 \
  --min-completeness 90.0 \
  --max-validation-failure-rate 5.0 \
  --window-size 100
```

**Parameters**:
- `--min-confidence`: Minimum average confidence score (0.0-1.0)
- `--min-completeness`: Minimum field completeness percentage (0-100)
- `--max-validation-failure-rate`: Maximum validation failure percentage (0-100)
- `--window-size`: Number of recent extractions to evaluate (default: 100)

**Expected Output**:
```
✅ Quality thresholds configured:
   • Minimum confidence:         85%
   • Minimum completeness:       90%
   • Max validation failures:    5%
   • Evaluation window:          100 extractions

💾 Saved to config file: config/quality_thresholds.json
```

---

## Step 4: Check if Provider Meets Thresholds

Verify whether a provider's quality metrics meet your configured thresholds:

```bash
collabiq quality check claude
```

**Expected Output (Passing)**:
```
✅ Claude meets all quality thresholds

Threshold Check Results:
  ✅ Average confidence:        89.0% (threshold: 85%)
  ✅ Field completeness:        96.0% (threshold: 90%)
  ✅ Validation failure rate:   5.3%  (threshold: 5%)
  ✅ Evaluation window:         100 extractions (sufficient data)

Status: PASS - Provider is eligible for automated selection
```

**Expected Output (Failing)**:
```
❌ Gemini fails quality thresholds

Threshold Check Results:
  ✅ Average confidence:        86.0% (threshold: 85%)
  ✅ Field completeness:        94.0% (threshold: 90%)
  ❌ Validation failure rate:   8.5%  (threshold: 5%)
  ✅ Evaluation window:         100 extractions (sufficient data)

Failures:
  • Validation failure rate (8.5%) exceeds maximum (5%)
  • 8 of last 100 extractions failed validation
  • Common failures: date field (4), startup_name missing (3), invalid format (1)

Status: FAIL - Provider not eligible for automated selection
💡 Suggestion: Review recent failed extractions and adjust prompts or validation rules
```

---

## Step 5: Enable Quality-Based Routing

Configure the system to automatically select providers based on quality thresholds:

```bash
collabiq config routing set \
  --strategy quality-based \
  --fallback-to-cost true
```

**Parameters**:
- `--strategy quality-based`: Use quality metrics for provider selection
- `--fallback-to-cost true`: Fall back to cost-based selection if no providers meet quality thresholds

**How It Works**:
1. When an email needs extraction, system checks quality metrics for all providers
2. Filters out providers that don't meet quality thresholds
3. Among qualifying providers, selects the one with lowest cost per email
4. If no providers qualify, falls back to lowest-cost provider (if fallback enabled)

**Expected Output**:
```
✅ Routing strategy configured: quality-based

Configuration:
  • Strategy:              quality-based
  • Fallback to cost:      enabled
  • Quality thresholds:    min_confidence=0.85, min_completeness=90%, max_failures=5%

Next extraction will use quality-based provider selection.
```

---

## Step 6: Monitor Quality Degradation

Set up alerts when provider quality degrades below acceptable levels:

```bash
collabiq quality watch --interval 3600
```

**Parameters**:
- `--interval`: Check interval in seconds (default: 3600 = 1 hour)

**What It Does**:
- Periodically checks all provider quality metrics
- Compares against configured thresholds
- Logs warnings when providers degrade below thresholds
- Sends alerts (if alerting configured - see alerting setup guide)

**Expected Output**:
```
🔍 Quality Monitoring Started
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Monitoring 3 providers: Gemini, Claude, OpenAI
Check interval: 3600 seconds (1 hour)
Thresholds: confidence ≥85%, completeness ≥90%, failures ≤5%

[2025-11-09 12:00:00] All providers meet quality thresholds ✅
[2025-11-09 13:00:00] ⚠️  WARNING: Gemini quality degradation detected
                          Validation failure rate: 8.5% (threshold: 5%)
                          Recent failures: date field (4), startup_name missing (3)
[2025-11-09 14:00:00] All providers meet quality thresholds ✅

Press Ctrl+C to stop monitoring
```

---

## Step 7: Export Quality Report

Generate a detailed quality metrics report for analysis or sharing:

```bash
collabiq quality export --format csv --output quality_report.csv
```

**Parameters**:
- `--format`: Output format (csv, json, html)
- `--output`: Output file path
- `--providers`: Specific providers to include (default: all)
- `--date-range`: Date range filter (e.g., "last-7-days", "2025-11-01:2025-11-09")

**Expected Output (CSV)**:
```csv
provider,total_extractions,validation_success_rate,avg_confidence,avg_completeness,quality_trend,last_updated
claude,150,94.67,0.89,96.0,improving,2025-11-09T12:00:00Z
gemini,148,91.22,0.86,94.0,stable,2025-11-09T12:05:00Z
openai,152,84.21,0.83,91.5,degrading,2025-11-09T12:10:00Z
```

**Use Cases**:
- Share with team for decision-making
- Track quality trends over time (export weekly)
- Import into data analysis tools (Excel, Tableau, etc.)
- Include in stakeholder reports

---

## Troubleshooting

### Problem: "No quality metrics found for provider X"

**Cause**: Provider hasn't processed any emails yet, or quality tracking wasn't enabled.

**Solution**:
1. Verify provider is configured: `collabiq status --providers`
2. Process some emails: `collabiq process --provider X`
3. Check metrics again: `collabiq status --provider X`

---

### Problem: Quality trend shows "N/A" or "insufficient data"

**Cause**: Provider has fewer than 50 extractions (required for trend calculation).

**Solution**: Process more emails. Trend calculation requires at least 50 extractions to compare recent vs previous performance.

---

### Problem: Value score seems incorrect

**Cause**: Cost metrics may not be tracked, or cost_tracker not initialized.

**Solution**:
1. Verify cost tracking is enabled: `collabiq status --cost`
2. If cost metrics are missing, re-process emails to populate cost data
3. Cost tracker and quality tracker must both have data for value score calculation

---

### Problem: Validation failure rate is high but extractions look correct

**Cause**: Validation rules may be too strict, or extraction format doesn't match validation expectations.

**Solution**:
1. Review validation failure reasons: `collabiq quality failures --provider X --last 20`
2. Check specific failed extractions: `collabiq extractions list --failed --provider X`
3. Adjust validation rules if they're unnecessarily strict (see validation configuration guide)
4. Or adjust LLM prompts to better match validation requirements

---

## Next Steps

- **Set up automated alerts**: Configure email/Slack notifications for quality degradation (see alerting guide)
- **Integrate with CI/CD**: Add quality threshold checks to deployment pipeline
- **A/B testing**: Use quality metrics to evaluate prompt changes or new LLM models
- **Historical analysis**: Export quality reports weekly to track long-term trends

---

## Related Documentation

- [Quality Tracker API Contract](contracts/quality-tracker-api.md)
- [Data Model Reference](data-model.md)
- [Research Findings](research.md)
- [Feature Specification](spec.md)

---

## Support

For questions or issues:
- Check the [Feature Specification](spec.md) for requirements and assumptions
- Review [Research Findings](research.md) for design decisions and rationale
- Consult [API Contract](contracts/quality-tracker-api.md) for technical integration details
