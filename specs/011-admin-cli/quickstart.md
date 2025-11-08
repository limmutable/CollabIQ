# Quickstart Guide: Admin CLI Enhancement

**Feature**: Admin CLI Enhancement | **Branch**: `011-admin-cli` | **Date**: 2025-11-08

## Overview

This guide provides step-by-step instructions for using the unified `collabiq` CLI command to manage the CollabIQ system. All admin operations are accessible through a single, intuitive interface.

## Prerequisites

- CollabIQ installed and configured
- Python 3.12+ environment activated
- Gmail, Notion, and Gemini credentials configured (via Infisical or .env)
- `collabiq` command installed (via `uv pip install -e .`)

## Installation

### 1. Install CLI Dependencies

```bash
# Navigate to project root
cd /path/to/CollabIQ

# Add typer and rich dependencies
uv add "typer[all]" rich

# Install in development mode
uv pip install -e .
```

### 2. Verify Installation

```bash
# Check that collabiq command is available
collabiq --help

# Expected output:
# CollabIQ Admin CLI - Unified command interface for all operations
#
# Usage: collabiq [OPTIONS] COMMAND [ARGS]...
#
# Commands:
#   email   Email pipeline operations
#   notion  Notion integration management
#   test    Testing and validation
#   errors  Error management and DLQ operations
#   status  System health monitoring
#   llm     LLM provider management
#   config  Configuration management
```

## Quick Start (5 Minutes)

### Step 1: Verify System Health

Check that all components are working:

```bash
collabiq status
```

**Expected Output**:
```
CollabIQ System Status

Overall Health: ✓ Healthy

Component Status
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Component             ┃ Status    ┃ Response Time ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Gmail                 │ ✓ Healthy │ 145ms        │
│ Notion                │ ✓ Healthy │ 230ms        │
│ Gemini                │ ✓ Healthy │ 850ms        │
└───────────────────────┴───────────┴──────────────┘
```

**If any component fails**, check configuration:

```bash
collabiq config show
```

### Step 2: Verify Connections

Check Gmail connectivity:

```bash
collabiq email verify
```

Check Notion integration:

```bash
collabiq notion verify
```

### Step 3: Fetch and Process Emails

Fetch a few test emails:

```bash
collabiq email fetch --limit 5
```

Clean the fetched emails:

```bash
collabiq email clean
```

List recent emails:

```bash
collabiq email list --limit 10
```

### Step 4: Run Quick Validation

Validate system setup (< 10 seconds):

```bash
collabiq test validate
```

**Success!** You're now ready to use the CollabIQ CLI for all admin operations.

## Common Workflows

### Workflow 1: Daily Email Processing

Process new emails from Gmail:

```bash
# Option A: Fetch and process in one command
collabiq email process --limit 20

# Option B: Step-by-step with inspection
collabiq email fetch --limit 20
collabiq email list --status raw  # Inspect what was fetched
collabiq email clean
collabiq email process --limit 20
```

**With progress tracking**:
```bash
collabiq email process --limit 50
# Shows real-time progress:
# Pipeline Execution
# ├─ Fetching emails... ✓ 50 fetched
# ├─ Cleaning content... ✓ 50 cleaned
# ├─ Extracting entities... ✓ 48 extracted (2 failed)
# ├─ Validating data... ✓ 48 validated
# └─ Writing to Notion... ✓ 47 written (1 failed)
```

### Workflow 2: Error Management

List recent errors:

```bash
collabiq errors list --limit 20
```

Filter by severity:

```bash
collabiq errors list --severity high --since yesterday
```

Inspect specific error:

```bash
collabiq errors show err_20251108_001
```

Retry failed operations:

```bash
# Retry all retriable errors
collabiq errors retry --all

# Retry specific error
collabiq errors retry --id err_20251108_001

# Retry errors from today
collabiq errors retry --since today
```

Clear resolved errors:

```bash
collabiq errors clear --resolved --yes
```

### Workflow 3: Notion Testing

Verify Notion schema:

```bash
collabiq notion schema
```

Test write capability:

```bash
collabiq notion test-write
```

Clean up test entries:

```bash
collabiq notion cleanup-tests
```

### Workflow 4: End-to-End Testing

Select test emails:

```bash
collabiq test select-emails
```

Run E2E test on all configured test emails:

```bash
collabiq test e2e --all
```

Run E2E test on limited set:

```bash
collabiq test e2e --limit 5
```

Test specific email:

```bash
collabiq test e2e --email-id email_007
```

**If interrupted**, resume from last checkpoint:

```bash
# Test starts, processes 5 emails, then interrupted (Ctrl+C)
# CLI saves progress and shows:
# ⚠ Operation interrupted - saving progress...
# Resume with: collabiq test e2e --resume test_20251108_123456

# Resume the test
collabiq test e2e --resume test_20251108_123456
```

### Workflow 5: System Monitoring

Quick status check:

```bash
collabiq status
```

Detailed metrics:

```bash
collabiq status --detailed
```

Continuous monitoring (refreshes every 30s):

```bash
collabiq status --watch
# Press Ctrl+C to stop
```

### Workflow 6: LLM Provider Management

**Phase 3a (before Phase 3b implemented)**:

```bash
collabiq llm status
# Output:
# ⚠ Multi-LLM support coming in Phase 3b
# Currently using: Gemini (primary)
#
# Gemini Status
#   Health: ✓ Online
#   Response Time: 850ms
#   Success Rate: 98.5%
```

**Phase 3b (multi-LLM implemented)**:

```bash
# View all providers
collabiq llm status

# Test specific provider
collabiq llm test gemini
collabiq llm test claude

# View orchestration policy
collabiq llm policy

# Change policy
collabiq llm set-policy consensus

# View usage and costs
collabiq llm usage --since yesterday

# Disable/enable providers
collabiq llm disable openai
collabiq llm enable openai
```

### Workflow 7: Configuration Management

View all configuration:

```bash
collabiq config show
```

**Output** (secrets masked):
```
Configuration (by category)

Gmail
  GMAIL_CREDENTIALS_PATH: /path/to/creds.json (env)
  GMAIL_QUERY: is:unread (default)

Notion
  NOTION_API_KEY: ntn_...XXX (infisical) 🔒
  NOTION_DATABASE_ID: abc123...xyz (infisical) 🔒

Gemini
  GEMINI_API_KEY: AIza...XXX (infisical) 🔒
  GEMINI_MODEL: gemini-pro (default)
```

Validate configuration:

```bash
collabiq config validate
```

Test Infisical connectivity:

```bash
collabiq config test-secrets
```

Get specific config value:

```bash
collabiq config get GEMINI_API_KEY
```

## JSON Output Mode

All commands support `--json` flag for scripting and automation:

```bash
# Status as JSON
collabiq status --json

# Output:
# {
#   "status": "success",
#   "data": {
#     "overall_health": "healthy",
#     "components": [
#       {"name": "Gmail", "status": "healthy", "response_time_ms": 145},
#       {"name": "Notion", "status": "healthy", "response_time_ms": 230},
#       {"name": "Gemini", "status": "healthy", "response_time_ms": 850}
#     ],
#     "recent_activity": {
#       "emails_processed_today": 25,
#       "success_rate_percent": 92,
#       "error_count": 2
#     }
#   },
#   "errors": []
# }

# Parse with jq
collabiq status --json | jq '.data.overall_health'
# Output: "healthy"

# Email list as JSON
collabiq email list --limit 5 --json | jq '.data.emails[] | .subject'
```

## Global Options

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
collabiq --debug email fetch --limit 5
```

**Output includes**:
- API request/response details
- Stack traces on errors
- Timing information for each operation

### Quiet Mode

Suppress non-error output (for automation):

```bash
collabiq --quiet email process --limit 10
# Only errors printed, exit code indicates success/failure
```

**Check exit code**:
```bash
collabiq --quiet test validate
echo $?  # 0 = success, 1 = failure
```

### Disable Colors

For non-interactive environments:

```bash
# Via flag
collabiq --no-color status

# Via environment variable
NO_COLOR=1 collabiq status
```

## Help and Discovery

### Get help for any command

```bash
# Main help
collabiq --help

# Command group help
collabiq email --help
collabiq notion --help
collabiq test --help

# Specific command help
collabiq email fetch --help
collabiq test e2e --help
collabiq errors retry --help
```

**Help output includes**:
- Command description
- All options with types and defaults
- Usage examples

### Example help output

```bash
collabiq email fetch --help
```

**Output**:
```
Usage: collabiq email fetch [OPTIONS]

  Fetch emails from Gmail with deduplication.

  Example: collabiq email fetch --limit 20

Options:
  --limit INTEGER   Maximum emails to fetch  [default: 10]
  --debug           Enable debug logging
  --json            Output as JSON
  --quiet           Suppress non-error output
  --help            Show this message and exit
```

## Troubleshooting

### Problem: Command not found

**Solution**: Ensure package is installed in development mode

```bash
uv pip install -e .
```

### Problem: Authentication failed

**Solution**: Verify credentials are configured

```bash
collabiq config validate
collabiq config test-secrets
```

**Check specific credential**:

```bash
collabiq config get GMAIL_CREDENTIALS_PATH
collabiq config get NOTION_API_KEY
```

### Problem: Component status shows "degraded" or "offline"

**Solution**: Run detailed status to see specific issues

```bash
collabiq status --detailed
```

**Verify each component**:

```bash
collabiq email verify
collabiq notion verify
collabiq test validate
```

### Problem: Errors during processing

**Solution**: Check error records

```bash
# List recent errors
collabiq errors list --limit 10

# Get details on specific error
collabiq errors show <error-id>

# Error output includes:
# - Error type and severity
# - Full error message
# - Stack trace (if available)
# - Suggested remediation
```

### Problem: Rate limits

**Solution**: Reduce processing rate

```bash
# Use smaller batches
collabiq email fetch --limit 5
collabiq email process --limit 5

# Check API usage
collabiq status --detailed
```

### Problem: Interrupted operation

**Solution**: Resume from saved state (for long operations)

```bash
# E2E tests support resume
collabiq test e2e --resume <run-id>

# Email processing doesn't duplicate work
collabiq email fetch  # Skips duplicates automatically
```

## Advanced Usage

### Automation with JSON Mode

**Example**: Daily processing script

```bash
#!/bin/bash
# daily_process.sh

# Process emails and capture result
RESULT=$(collabiq email process --limit 50 --json)

# Check if successful
if echo "$RESULT" | jq -e '.status == "success"' > /dev/null; then
    echo "Processing successful"
    WRITTEN=$(echo "$RESULT" | jq '.data.written')
    echo "Wrote $WRITTEN emails to Notion"
else
    echo "Processing failed"
    echo "$RESULT" | jq '.errors'
    exit 1
fi
```

**Example**: Health check monitoring

```bash
#!/bin/bash
# health_check.sh

STATUS=$(collabiq status --json | jq -r '.data.overall_health')

if [ "$STATUS" != "healthy" ]; then
    echo "System degraded or offline: $STATUS"
    collabiq status --detailed --json | jq '.data.components[] | select(.status != "healthy")'
    exit 1
fi

echo "System healthy"
```

### Combining Commands

```bash
# Verify, test, and process in sequence
collabiq email verify && \
collabiq notion verify && \
collabiq test validate && \
collabiq email process --limit 20
```

### Watch Mode for Monitoring

```bash
# Continuous monitoring (refreshes every 30s)
collabiq status --watch

# Output updates in place:
# CollabIQ System Status
# Overall Health: ✓ Healthy
# [Updates every 30 seconds]
# Press Ctrl+C to stop
```

## Performance Tips

1. **Use --limit for large operations**
   ```bash
   collabiq email fetch --limit 100  # Instead of fetching all
   ```

2. **Use --quiet for automation**
   ```bash
   collabiq --quiet email process  # Faster, less output
   ```

3. **JSON mode is faster than interactive**
   ```bash
   collabiq email list --json  # No table rendering overhead
   ```

4. **Use test validate for quick checks**
   ```bash
   collabiq test validate  # Under 10 seconds vs full E2E test
   ```

## Next Steps

After completing this quickstart:

1. **Explore command groups**: Use `--help` to discover all available commands
2. **Set up test emails**: Run `collabiq test select-emails` to configure E2E tests
3. **Configure monitoring**: Use `collabiq status --watch` or integrate JSON mode into monitoring tools
4. **Automate workflows**: Create scripts using `--json` output mode
5. **Review errors regularly**: Use `collabiq errors list` to catch issues early

## Reference

**Command Groups**:
- `email` - Email pipeline operations (fetch, clean, list, verify, process)
- `notion` - Notion integration (verify, schema, test-write, cleanup-tests)
- `test` - Testing and validation (e2e, select-emails, validate)
- `errors` - Error management (list, show, retry, clear)
- `status` - System health monitoring
- `llm` - LLM provider management (status, test, policy, usage, enable/disable)
- `config` - Configuration (show, validate, test-secrets, get)

**Global Options**:
- `--help` - Show help
- `--debug` - Enable verbose logging
- `--quiet` - Suppress non-error output
- `--no-color` - Disable color output

**Common Options** (available on most commands):
- `--json` - JSON output mode
- `--limit` - Limit items processed/displayed
- `--since` - Filter by date

**Exit Codes**:
- `0` - Success
- `1` - Command failed
- `2` - Invalid arguments

For more detailed information, see:
- [CLI Interface Contracts](contracts/cli-interface.md) - Complete command specifications
- [Command Groups](contracts/command-groups.md) - Command organization details
- [Data Model](data-model.md) - CLI entity definitions
