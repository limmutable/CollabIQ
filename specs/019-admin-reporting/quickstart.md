# Quickstart: Automated Admin Reporting

**Feature**: 019-admin-reporting
**Date**: 2025-11-29

## Overview

This feature adds automated daily reporting and critical alert notifications to CollabIQ. Administrators receive email summaries of system health, processing metrics, errors, LLM usage, and Notion statistics.

## Prerequisites

- Existing CollabIQ installation with working Gmail OAuth
- Configured Notion integration
- Python 3.12+ with UV package manager

## Quick Setup

### 1. Configure Recipients

Add reporting configuration to your `.env` file:

```bash
# Default recipient (can be overridden)
ADMIN_REPORT_RECIPIENTS=jeffreylim@signite.co

# Optional: Customize schedule (defaults shown)
ADMIN_REPORT_TIME=07:00
ADMIN_REPORT_TIMEZONE=Asia/Seoul                # Korea Standard Time (KST)
ADMIN_ERROR_RATE_THRESHOLD=0.05
ADMIN_COST_LIMIT_DAILY=10.0
ADMIN_REPORT_ARCHIVE_DIR=data/reports
ADMIN_REPORT_RETENTION_DAYS=30
```

**Note**: The default recipient is `jeffreylim@signite.co`. To add multiple recipients, use comma-separated values:
```bash
ADMIN_REPORT_RECIPIENTS=jeffreylim@signite.co,ops@signite.co
```

### 2. Verify Configuration

```bash
# Check current configuration
uv run collabiq report config

# Validate and send test email
uv run collabiq report config --validate
```

### 3. Generate First Report

```bash
# Generate report (display only)
uv run collabiq report generate

# Generate and send via email
uv run collabiq report generate --send
```

## CLI Commands

### Report Generation

```bash
# Generate and display report
uv run collabiq report generate

# Generate and email to recipients
uv run collabiq report generate --send

# Generate specific format
uv run collabiq report generate --format html -o report.html
uv run collabiq report generate --format json -o report.json
```

### Report History

```bash
# List recent reports
uv run collabiq report list

# Show specific report
uv run collabiq report show 2025-11-28
uv run collabiq report show latest

# Show specific section
uv run collabiq report show latest --section errors
uv run collabiq report show latest --section llm
```

### Alert Management

```bash
# List active alerts
uv run collabiq report alerts list

# Filter by severity
uv run collabiq report alerts list --severity critical

# Acknowledge an alert
uv run collabiq report alerts acknowledge <alert-id>

# Send test alert
uv run collabiq report alerts test --severity warning
```

### Configuration

```bash
# View current config
uv run collabiq report config

# Update settings
uv run collabiq report config --set recipients=admin@example.com,ops@example.com
uv run collabiq report config --set time=08:00
uv run collabiq report config --set timezone=America/New_York

# Validate and test
uv run collabiq report config --validate
```

## Report Contents

### Daily Summary Email

The daily report includes:

1. **System Health Status**
   - Gmail API: operational/degraded/unavailable
   - Notion API: operational/degraded/unavailable
   - LLM Providers: status per provider (Gemini, Claude, OpenAI)

2. **Processing Metrics**
   - Emails received vs. processed
   - Success rate percentage
   - Average processing time
   - Processing cycles completed

3. **Error Summary**
   - Critical errors (full details)
   - High-severity errors (details)
   - Low-severity error count
   - Top error categories

4. **LLM Usage**
   - API calls by provider
   - Estimated costs by provider
   - Total daily cost

5. **Notion Statistics**
   - Entries created
   - Entries updated
   - Validation failures

6. **Actionable Alerts**
   - Credential expiration warnings
   - Error rate threshold breaches
   - Cost limit warnings
   - Component availability issues

### Example Report Output

```
╔══════════════════════════════════════════════════════════════════╗
║              CollabIQ Daily Report - 2025-11-29                  ║
╚══════════════════════════════════════════════════════════════════╝

📊 SYSTEM HEALTH
├─ Gmail:        ✅ Operational
├─ Notion:       ✅ Operational
├─ Gemini:       ✅ Operational
├─ Claude:       ✅ Operational
└─ Overall:      ✅ All Systems Operational

📬 PROCESSING METRICS
├─ Emails Received:    45
├─ Emails Processed:   44
├─ Success Rate:       97.8%
├─ Avg. Process Time:  4.2s
└─ Processing Cycles:  96

❌ ERRORS (Period: 24h)
├─ Critical:    0
├─ High:        1
├─ Low:         3
└─ Error Rate:  2.2%

💡 LLM USAGE
├─ Gemini:      38 calls ($0.12)
├─ Claude:       6 calls ($0.08)
├─ OpenAI:       0 calls ($0.00)
└─ Total Cost:  $0.20

📝 NOTION STATS
├─ Entries Created:   42
├─ Entries Updated:    2
└─ Validation Errors:  1

⚠️ ACTIONABLE ALERTS
├─ [WARNING] Error rate (2.2%) approaching threshold (5%)
└─ [INFO] Gmail token expires in 14 days

Generated: 2025-11-29 07:00:00 UTC
```

## Critical Alerts

Critical errors trigger immediate notification (within 5 minutes):

- Gmail authentication failure
- Notion API unreachable
- All LLM providers unavailable
- Error rate exceeds threshold for 5+ minutes

Alerts are batched within a 15-minute window to prevent notification fatigue.

## Archive Location

Reports are archived to:

```
data/reports/
├── 2025-11-29_daily_report.json
├── 2025-11-29_daily_report.html
├── 2025-11-28_daily_report.json
└── 2025-11-28_daily_report.html
```

Archives are automatically cleaned up after the retention period (default: 30 days).

## Integration with Daemon

When running in daemon mode, reports are generated automatically:

```bash
# Daemon automatically sends daily reports at configured time
uv run collabiq run --daemon
```

The daemon:
- Collects metrics during each processing cycle
- Generates and sends daily report at scheduled time
- Sends immediate alerts for critical errors
- Archives all reports

## Troubleshooting

### Report Not Sending

```bash
# Check configuration
uv run collabiq report config

# Validate email delivery
uv run collabiq report config --validate

# Check Gmail token
uv run collabiq config validate
```

### Missing Metrics

Metrics are collected by the daemon. If running in single-cycle mode, historical metrics may be limited:

```bash
# Check daemon state
cat data/daemon/state.json
```

### Email Delivery Issues

The system uses Gmail API for sending (same credentials as receiving):

```bash
# Test Gmail connection
uv run collabiq email test

# Check token expiry
uv run collabiq config show
```

## Next Steps

1. Configure recipients in `.env`
2. Run `collabiq report config --validate` to test
3. Generate first report with `collabiq report generate --send`
4. Start daemon for automatic daily reports

For detailed configuration options, see `docs/cli/CLI_REFERENCE.md`.
