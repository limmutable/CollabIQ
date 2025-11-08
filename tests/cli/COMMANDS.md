# CollabIQ Admin CLI - Demo Guide

Quick guide to test the implemented CLI commands.

## Status

**Completed Phases:**
- ✅ Phase 1-3: Setup, Foundation, Single Entry Point
- ✅ Phase 4: Email Pipeline Management (5 commands)
- ✅ Phase 5: Notion Integration Management (4 commands)
- ✅ Phase 6: LLM Provider Management (7 commands)

**Progress:** 69/132 tasks complete (52%)

## Quick Start

### 1. Main CLI Help
```bash
uv run collabiq --help
```

Shows all 7 command groups: email, notion, test, errors, status, llm, config

### 2. Command Group Help
```bash
uv run collabiq email --help
uv run collabiq notion --help
uv run collabiq llm --help
```

## Email Commands (Phase 4)

### List Emails
```bash
# Interactive table format
uv run collabiq email list

# JSON output (for automation)
uv run collabiq email list --json

# With limit and filtering
uv run collabiq email list --limit 10 --since "2025-11-01"
```

### Other Email Commands
```bash
# Verify Gmail connectivity
uv run collabiq email verify

# Fetch emails (requires Gmail credentials)
uv run collabiq email fetch --limit 5

# Clean emails
uv run collabiq email clean

# Full pipeline
uv run collabiq email process --limit 3
```

## Notion Commands (Phase 5)

### Verify Notion Connection
```bash
# Interactive output
uv run collabiq notion verify

# JSON output
uv run collabiq notion verify --json
```

### View Database Schema
```bash
# Table format
uv run collabiq notion schema

# JSON format
uv run collabiq notion schema --json
```

### Test Write/Cleanup
```bash
# Create and auto-cleanup test entry
uv run collabiq notion test-write

# Remove all test entries
uv run collabiq notion cleanup-tests

# Skip confirmation
uv run collabiq notion cleanup-tests --yes
```

## LLM Commands (Phase 6)

### View Provider Status
```bash
# Interactive table
uv run collabiq llm status

# JSON output
uv run collabiq llm status --json
```

**Note:** These commands require `GEMINI_API_KEY` to be set. Without it, you'll see helpful configuration instructions.

### Other LLM Commands
```bash
# Test provider connectivity
uv run collabiq llm test gemini

# View orchestration policy (Phase 3a: shows "Gemini only")
uv run collabiq llm policy

# View usage statistics
uv run collabiq llm usage
```

### Phase 3b Commands (Not Yet Available)
```bash
# These will show helpful messages about Phase 3b:
uv run collabiq llm set-policy failover
uv run collabiq llm disable claude
uv run collabiq llm enable openai
```

## Global Options

### Debug Mode
```bash
uv run collabiq --debug email list
```
Enables debug logging to `data/logs/cli_audit.log`

### Quiet Mode
```bash
uv run collabiq --quiet email list
```
Suppresses non-error output

### No Color Mode
```bash
uv run collabiq --no-color email list
```
Disables colored output (also honors `NO_COLOR` env var)

### Combine Options
```bash
uv run collabiq --debug --no-color email fetch --limit 5
```

## JSON Mode (for automation)

All commands support `--json` flag for structured output:

```bash
# Email list as JSON
uv run collabiq email list --json | jq '.data.emails'

# LLM status as JSON
uv run collabiq llm status --json | jq '.data'

# Notion schema as JSON
uv run collabiq notion schema --json | jq '.data.properties'
```

## Test Scripts

### Quick Smoke Test (~10 seconds)
```bash
./tests/cli/test_cli_quick.sh
```
Fast test of the most important commands

### Comprehensive Test (~2-3 minutes)
```bash
./tests/cli/test_cli_manual.sh
```
Thorough testing of all help text and features

### Usage Examples
```bash
./tests/cli/test_cli_examples.sh
```
Shows all available commands with copy/paste examples

## Configuration

### Gmail (for email commands)
Set in `.env` file:
```
GMAIL_CREDENTIALS_FILE=path/to/credentials.json
GMAIL_TOKEN_FILE=path/to/token.json
```

### Notion (for notion commands)
Set in `.env` file:
```
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID_COLLABIQ=your_collabiq_database_id
NOTION_DATABASE_ID_COMPANIES=your_companies_database_id
```

### Gemini (for llm commands)
Set in `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key
```

Get API key from: https://makersuite.google.com/app/apikey

## What's NOT Yet Implemented

These command groups show help but have no commands yet:

```bash
uv run collabiq test --help      # Phase 7: E2E Testing
uv run collabiq errors --help    # Phase 8: Error Management
uv run collabiq status --help    # Phase 9: System Health
uv run collabiq config --help    # Phase 10: Configuration
```

## Next Steps

- Phase 7: E2E Testing (14 tasks)
- Phase 8: Error Management (12 tasks)
- Phase 9: System Health (12 tasks)
- Phase 10: Configuration (13 tasks)
- Phase 11: Polish & Cross-Cutting (12 tasks)

## Troubleshooting

### "Gemini provider not configured"
Set the `GEMINI_API_KEY` environment variable. See configuration section above.

### "Notion integration error"
Ensure `NOTION_API_KEY` and `NOTION_DATABASE_ID_COLLABIQ` are set in `.env` file.

### "Gmail authentication failed"
Run the Gmail authentication flow to generate credentials and token files.

### Logging
All CLI operations are logged to `data/logs/cli_audit.log` for troubleshooting.
Enable `--debug` flag for verbose logging.
