# CLI Interface Contracts

**Feature**: Admin CLI Enhancement | **Branch**: `011-admin-cli` | **Date**: 2025-11-08

## Overview

This document defines the complete interface contracts for all `collabiq` CLI commands. These contracts specify command signatures, argument types, output formats, exit codes, and expected behaviors. Contract tests must verify these specifications are maintained.

## Global Contracts

### Entry Point

**Command**: `collabiq`

**Installation**:
```bash
# Via pyproject.toml [project.scripts]
collabiq = "collabiq:app"
```

**Global Options** (available on all commands):
- `--help`: Display help text and exit with code 0
- `--debug`: Enable debug logging with verbose output
- `--quiet`: Suppress non-error output
- `--no-color`: Disable ANSI color codes (also honors NO_COLOR environment variable)

**Exit Codes**:
- `0`: Success
- `1`: Command failed or validation error
- `2`: Invalid command or arguments (typer default)

### Output Modes

All commands support two output modes:

1. **Interactive Mode** (default):
   - Rich formatted output with colors
   - Tables with aligned columns
   - Progress indicators (spinners, bars)
   - Human-readable messages

2. **JSON Mode** (`--json` flag):
   - Valid JSON output only
   - Structured data for parsing
   - No color codes or progress indicators
   - Format: `{"status": "success"|"failure", "data": {...}, "errors": [...]}`

**Contract**: JSON mode must always produce parseable JSON, even on errors

## Command Group: email

### collabiq email fetch

**Purpose**: Fetch emails from Gmail with deduplication

**Signature**:
```bash
collabiq email fetch [OPTIONS]
```

**Options**:
- `--limit INTEGER` (default: 10): Maximum emails to fetch
- `--debug BOOL` (flag): Enable debug logging
- `--json BOOL` (flag): Output as JSON
- `--quiet BOOL` (flag): Suppress non-error output

**Exit Codes**:
- `0`: Emails fetched successfully (including 0 emails if none available)
- `1`: Gmail authentication failed, network error, or fetch error

**Output (Interactive)**:
```
✓ Fetched 10 emails successfully (2 duplicates skipped)
Duration: 1.2s
```

**Output (JSON)**:
```json
{
  "status": "success",
  "data": {
    "fetched": 10,
    "duplicates_skipped": 2,
    "duration_ms": 1200
  },
  "errors": []
}
```

**Contract Tests**:
- ✓ Accepts --limit flag with integer value
- ✓ Default limit is 10 if not specified
- ✓ --json produces parseable JSON
- ✓ Exit code 0 on success, 1 on failure
- ✓ Help text includes example usage

---

### collabiq email clean

**Purpose**: Normalize raw emails (remove signatures, clean content)

**Signature**:
```bash
collabiq email clean [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)
- `--quiet BOOL` (flag)

**Exit Codes**:
- `0`: Emails cleaned successfully
- `1`: Cleaning error

**Output (Interactive)**:
```
Processing emails... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Cleaned 10 emails successfully
Duration: 0.8s
```

**Output (JSON)**:
```json
{
  "status": "success",
  "data": {
    "cleaned": 10,
    "duration_ms": 800
  },
  "errors": []
}
```

---

### collabiq email list

**Purpose**: Display recent emails with filtering

**Signature**:
```bash
collabiq email list [OPTIONS]
```

**Options**:
- `--limit INTEGER` (default: 20): Maximum emails to display
- `--since TEXT`: Filter by date (e.g., "yesterday", "2025-11-01")
- `--status TEXT`: Filter by processing status (raw, cleaned, extracted, written)
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: List displayed successfully (including empty list)
- `1`: Error listing emails

**Output (Interactive)**:
```
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID       ┃ Sender               ┃ Subject                         ┃ Status    ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ email001 │ alice@example.com    │ Meeting notes from today        │ written   │
│ email002 │ bob@company.org      │ Project update                  │ extracted │
└──────────┴──────────────────────┴─────────────────────────────────┴───────────┘
Showing 2 of 10 emails
```

**Output (JSON)**:
```json
{
  "status": "success",
  "data": {
    "emails": [
      {"id": "email001", "sender": "alice@example.com", "subject": "Meeting notes", "status": "written"},
      {"id": "email002", "sender": "bob@company.org", "subject": "Project update", "status": "extracted"}
    ],
    "total": 10,
    "displayed": 2
  },
  "errors": []
}
```

---

### collabiq email verify

**Purpose**: Check Gmail connectivity and configuration

**Signature**:
```bash
collabiq email verify [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Gmail connection verified successfully
- `1`: Connection failed or configuration invalid

**Output (Interactive)**:
```
Gmail Connection Status
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Check                 ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Authentication        │ ✓ Pass    │
│ API Access            │ ✓ Pass    │
│ Credential Validity   │ ✓ Pass    │
│ Recent Email Count    │ 125       │
└───────────────────────┴───────────┘
```

---

### collabiq email process

**Purpose**: Run full pipeline (fetch → clean → extract → validate → write)

**Signature**:
```bash
collabiq email process [OPTIONS]
```

**Options**:
- `--limit INTEGER` (default: 10): Maximum emails to process
- `--debug BOOL` (flag)
- `--json BOOL` (flag)
- `--quiet BOOL` (flag)

**Exit Codes**:
- `0`: All emails processed successfully
- `1`: Some or all emails failed processing

**Output (Interactive)**:
```
Pipeline Execution
├─ Fetching emails... ✓ 10 fetched
├─ Cleaning content... ✓ 10 cleaned
├─ Extracting entities... ✓ 9 extracted (1 failed)
├─ Validating data... ✓ 9 validated
└─ Writing to Notion... ✓ 8 written (1 failed)

Summary: 8 successful, 2 failed
Duration: 2m 15s
```

## Command Group: notion

### collabiq notion verify

**Purpose**: Check Notion connection, auth, database access, schema

**Signature**:
```bash
collabiq notion verify [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: All checks passed
- `1`: Any check failed

**Output (Interactive)**:
```
Notion Verification
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Check                 ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Connection            │ ✓ Pass    │
│ Authentication        │ ✓ Pass    │
│ Database Access       │ ✓ Pass    │
│ Schema Compatibility  │ ✓ Pass    │
└───────────────────────┴───────────┘
```

---

### collabiq notion schema

**Purpose**: Display Notion database schema

**Signature**:
```bash
collabiq notion schema [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Schema retrieved successfully
- `1`: Failed to retrieve schema

**Output (Interactive)**:
```
Notion Database Schema
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property        ┃ Type        ┃ Required  ┃ Validation           ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ Title           │ title       │ Yes       │ -                    │
│ Sender          │ rich_text   │ Yes       │ Email format         │
│ Date            │ date        │ Yes       │ -                    │
│ Entities        │ multi_select│ No        │ -                    │
└─────────────────┴─────────────┴───────────┴──────────────────────┘
```

---

### collabiq notion test-write

**Purpose**: Create test entry, verify, and cleanup automatically

**Signature**:
```bash
collabiq notion test-write [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Test write successful and cleaned up
- `1`: Write failed or cleanup failed

**Output (Interactive)**:
```
Test Write Execution
├─ Creating test entry... ✓ Created (ID: test_12345)
├─ Verifying entry exists... ✓ Verified
└─ Cleaning up test entry... ✓ Removed

Test write successful
```

---

### collabiq notion cleanup-tests

**Purpose**: Remove all test entries from Notion database

**Signature**:
```bash
collabiq notion cleanup-tests [OPTIONS]
```

**Options**:
- `--yes BOOL` (flag): Skip confirmation prompt
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Test entries cleaned up successfully
- `1`: Cleanup failed

**Output (Interactive)**:
```
Found 5 test entries. Delete all? [y/N]: y
Removing test entries... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Removed 5 test entries
```

## Command Group: test

### collabiq test e2e

**Purpose**: Run end-to-end pipeline tests

**Signature**:
```bash
collabiq test e2e [OPTIONS]
```

**Options**:
- `--all BOOL` (flag): Test all configured test emails
- `--limit INTEGER`: Limit number of emails to test
- `--email-id TEXT`: Test specific email by ID
- `--resume TEXT`: Resume from run ID after interruption
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: All tests passed
- `1`: Some or all tests failed

**Output (Interactive)**:
```
E2E Test Run: test_20251108_123456
Testing 10 emails... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Stage Results
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Stage           ┃ Passed  ┃ Failed  ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ Reception       │ 10      │ 0       │
│ Extraction      │ 10      │ 0       │
│ Matching        │ 9       │ 1       │
│ Classification  │ 9       │ 1       │
│ Validation      │ 8       │ 2       │
│ Write           │ 8       │ 2       │
└─────────────────┴─────────┴─────────┘

Overall: 8 passed, 2 failed
Duration: 2m 30s
Report saved: data/e2e_test/reports/test_20251108_123456.json
```

---

### collabiq test select-emails

**Purpose**: Analyze and configure test email candidates

**Signature**:
```bash
collabiq test select-emails [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Test emails selected and saved
- `1`: Selection failed

---

### collabiq test validate

**Purpose**: Quick health checks (under 10 seconds)

**Signature**:
```bash
collabiq test validate [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: All validation checks passed
- `1`: Any check failed

**Output (Interactive)**:
```
Quick Validation
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Component             ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Gmail Auth            │ ✓ Pass    │
│ Notion Access         │ ✓ Pass    │
│ Gemini API            │ ✓ Pass    │
│ Configuration         │ ✓ Pass    │
└───────────────────────┴───────────┘
Duration: 3.2s
```

## Command Group: errors

### collabiq errors list

**Purpose**: List failed operations with filtering

**Signature**:
```bash
collabiq errors list [OPTIONS]
```

**Options**:
- `--severity TEXT`: Filter by severity (critical, high, medium, low)
- `--since TEXT`: Filter by date
- `--limit INTEGER` (default: 20): Maximum errors to display
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Error list displayed (including empty list)
- `1`: Failed to retrieve errors

**Output (Interactive)**:
```
Error Records
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID                 ┃ Timestamp           ┃ Severity  ┃ Type         ┃ Retry Count┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ err_20251108_001   │ 2025-11-08 12:34:56 │ high      │ api_limit    │ 0          │
│ err_20251108_002   │ 2025-11-08 13:15:22 │ medium    │ validation   │ 2          │
└────────────────────┴─────────────────────┴───────────┴──────────────┴────────────┘
```

---

### collabiq errors show

**Purpose**: Display full error details

**Signature**:
```bash
collabiq errors show <ERROR_ID> [OPTIONS]
```

**Arguments**:
- `error_id` (TEXT, required): Error ID to display

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Error details displayed
- `1`: Error ID not found or retrieval failed

**Output (Interactive)**:
```
Error Details: err_20251108_001

Type: api_limit
Severity: high
Timestamp: 2025-11-08 12:34:56
Retry Count: 0
Retriable: Yes

Message:
Gemini API rate limit exceeded

Context:
  Email ID: email_007
  Operation: entity_extraction

Suggested Remediation:
  - Wait 60 seconds before retrying
  - Reduce --limit flag to lower request rate
  - Check API quota usage with: collabiq status --detailed
```

---

### collabiq errors retry

**Purpose**: Retry failed operations

**Signature**:
```bash
collabiq errors retry [OPTIONS]
```

**Options**:
- `--all BOOL` (flag): Retry all retriable errors
- `--id TEXT`: Retry specific error by ID
- `--since TEXT`: Retry errors since date
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: All retries successful
- `1`: Some or all retries failed

**Output (Interactive)**:
```
Retrying 5 errors... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ 4 succeeded
✗ 1 failed (permanent error, cannot retry)
```

---

### collabiq errors clear

**Purpose**: Clear resolved errors

**Signature**:
```bash
collabiq errors clear [OPTIONS]
```

**Options**:
- `--resolved BOOL` (flag): Clear only resolved errors
- `--before TEXT`: Clear errors before date
- `--yes BOOL` (flag): Skip confirmation
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Errors cleared successfully
- `1`: Clear operation failed

## Command Group: status

### collabiq status

**Purpose**: Display overall system health and component status

**Signature**:
```bash
collabiq status [OPTIONS]
```

**Options**:
- `--detailed BOOL` (flag): Show extended metrics
- `--watch BOOL` (flag): Continuous monitoring (30s refresh)
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Status retrieved successfully
- `1`: Failed to retrieve status

**Output (Interactive)**:
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

Recent Activity
  Emails processed today: 25
  Success rate: 92%
  Error count: 2
  Last run: 2025-11-08 10:30:00

Last updated: 2025-11-08 14:25:00
```

**Output (JSON)**:
```json
{
  "status": "success",
  "data": {
    "overall_health": "healthy",
    "components": [
      {"name": "Gmail", "status": "healthy", "response_time_ms": 145},
      {"name": "Notion", "status": "healthy", "response_time_ms": 230},
      {"name": "Gemini", "status": "healthy", "response_time_ms": 850}
    ],
    "recent_activity": {
      "emails_processed_today": 25,
      "success_rate_percent": 92,
      "error_count": 2,
      "last_run": "2025-11-08T10:30:00"
    }
  },
  "errors": []
}
```

## Command Group: llm

### collabiq llm status

**Purpose**: Display all LLM providers with health metrics

**Signature**:
```bash
collabiq llm status [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Status retrieved successfully
- `1`: Failed to retrieve status

**Output (Phase 3a - before Phase 3b)**:
```
⚠ Multi-LLM support coming in Phase 3b
Currently using: Gemini (primary)

Gemini Status
  Health: ✓ Online
  Response Time: 850ms
  Success Rate: 98.5%
  Last Check: 2025-11-08 14:30:00
```

**Output (Phase 3b - multi-LLM implemented)**:
```
LLM Provider Status
┏━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Provider      ┃ Status    ┃ Response Time ┃ Success Rate ┃ Priority  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Gemini        │ ✓ Online  │ 850ms        │ 98.5%       │ 1         │
│ Claude 3.5    │ ✓ Online  │ 1200ms       │ 97.2%       │ 2         │
│ GPT-4         │ ⚠ Degraded│ 2500ms       │ 85.0%       │ 3         │
└───────────────┴───────────┴──────────────┴─────────────┴───────────┘

Current Policy: failover
```

---

### collabiq llm test

**Purpose**: Test connectivity and run sample extraction

**Signature**:
```bash
collabiq llm test <PROVIDER> [OPTIONS]
```

**Arguments**:
- `provider` (TEXT, required): Provider name (gemini, claude, openai)

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Test successful
- `1`: Test failed

---

### collabiq llm policy

**Purpose**: Display current orchestration strategy

**Signature**:
```bash
collabiq llm policy [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Policy displayed
- `1`: Failed to retrieve policy

---

### collabiq llm set-policy

**Purpose**: Change orchestration strategy

**Signature**:
```bash
collabiq llm set-policy <STRATEGY> [OPTIONS]
```

**Arguments**:
- `strategy` (TEXT, required): Strategy name (failover, consensus, best-match)

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Policy updated
- `1`: Invalid strategy or update failed

---

### collabiq llm usage

**Purpose**: View API usage and costs

**Signature**:
```bash
collabiq llm usage [OPTIONS]
```

**Options**:
- `--provider TEXT`: Filter by provider
- `--since TEXT`: Show usage since date
- `--until TEXT`: Show usage until date
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Usage displayed
- `1`: Failed to retrieve usage

---

### collabiq llm disable / enable

**Purpose**: Disable or enable LLM provider

**Signature**:
```bash
collabiq llm disable <PROVIDER> [OPTIONS]
collabiq llm enable <PROVIDER> [OPTIONS]
```

**Arguments**:
- `provider` (TEXT, required): Provider name (gemini, claude, openai)

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Provider status updated
- `1`: Update failed

## Command Group: config

### collabiq config show

**Purpose**: Display all configuration with secrets masked

**Signature**:
```bash
collabiq config show [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Configuration displayed
- `1`: Failed to retrieve configuration

**Output (Interactive)**:
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

Source Legend: (infisical) | (env) | (default)
🔒 = Secret (masked)
```

---

### collabiq config validate

**Purpose**: Check for missing/invalid required settings

**Signature**:
```bash
collabiq config validate [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: All required settings valid
- `1`: Missing or invalid settings found

**Output (Interactive)**:
```
Configuration Validation

✓ All required settings present
✓ All values pass validation

Configuration is valid
```

---

### collabiq config test-secrets

**Purpose**: Verify Infisical connectivity and secret access

**Signature**:
```bash
collabiq config test-secrets [OPTIONS]
```

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Secrets accessible
- `1`: Infisical connection failed or secrets unavailable

---

### collabiq config get

**Purpose**: Display specific configuration value

**Signature**:
```bash
collabiq config get <KEY> [OPTIONS]
```

**Arguments**:
- `key` (TEXT, required): Configuration key

**Options**:
- `--debug BOOL` (flag)
- `--json BOOL` (flag)

**Exit Codes**:
- `0`: Value displayed
- `1`: Key not found

**Output (Interactive)**:
```
GEMINI_API_KEY
  Value: AIza...XXX 🔒
  Source: infisical
  Category: Gemini
  Valid: Yes
```

## Contract Testing Requirements

All commands must have contract tests verifying:

1. **Help Text**: `--help` produces expected output and exits with code 0
2. **Argument Parsing**: Required arguments are enforced, optional arguments have defaults
3. **Option Validation**: Invalid option values produce error and exit code 1
4. **JSON Output**: `--json` produces valid, parseable JSON
5. **Exit Codes**: Commands return documented exit codes
6. **Global Options**: All commands support --debug, --quiet, --no-color
7. **Error Messages**: Failures produce actionable error messages

**Example Contract Test**:
```python
def test_email_fetch_contract():
    """Contract: email fetch command interface"""
    result = runner.invoke(app, ["email", "fetch", "--help"])
    assert result.exit_code == 0
    assert "--limit" in result.stdout
    assert "INTEGER" in result.stdout  # Type hint present

    result = runner.invoke(app, ["email", "fetch", "--limit", "invalid"])
    assert result.exit_code == 2  # Typer validation error

    result = runner.invoke(app, ["email", "fetch", "--json"])
    assert result.exit_code in [0, 1]
    if result.exit_code == 0:
        data = json.loads(result.stdout)  # Must be valid JSON
        assert "status" in data
        assert "data" in data
```
