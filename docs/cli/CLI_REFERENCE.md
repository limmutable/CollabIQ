# CollabIQ CLI Reference

Complete command-line interface reference for CollabIQ administration and operations.

**Last Updated**: November 9, 2025
**Version**: 1.0 (includes Quality Metrics features)

---

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [LLM Commands](#llm-commands)
- [Email Commands](#email-commands)
- [Notion Commands](#notion-commands)
- [Test Commands](#test-commands)
- [Error Commands](#error-commands)
- [Status Commands](#status-commands)
- [Config Commands](#config-commands)

---

## Overview

The CollabIQ CLI (`collabiq`) provides a unified interface for managing all system operations:

```bash
collabiq [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]
```

### Installation

```bash
# Ensure UV is installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run commands via UV
uv run collabiq <command>
```

---

## Global Options

Available for all commands:

```bash
--debug              Enable debug logging
--quiet              Suppress non-error output
--no-color           Disable color output (also honors NO_COLOR env var)
--help               Show help message
```

**Example**:
```bash
uv run collabiq --debug llm status
```

---

## Run Command

Execute the main processing pipeline.

### `run`

Execute the CollabIQ pipeline (fetch -> extract -> write). Can run once or in daemon mode.

**Usage**:
```bash
collabiq run [OPTIONS]
```

**Options**:
```bash
--daemon, -d          Run in daemon mode (continuous background processing)
--interval, -i INT    Check interval in minutes (daemon mode only) [default: 15]
```

**Examples**:
```bash
# Run a single processing cycle
uv run collabiq run

# Run in daemon mode (check every 15 mins)
uv run collabiq run --daemon

# Run in daemon mode with custom interval (e.g., every 5 mins)
uv run collabiq run --daemon --interval 5
```

---

## LLM Commands

Manage LLM providers, view metrics, and configure orchestration strategies.

### `llm status`

View health status and performance metrics for all LLM providers.

**Usage**:
```bash
collabiq llm status [OPTIONS]
```

**Options**:
```bash
--detailed    Show detailed metrics (cost, quality, orchestration config)
```

**Examples**:
```bash
# Basic status
uv run collabiq llm status

# Detailed view with quality metrics
uv run collabiq llm status --detailed
```

**Output**:
- Provider health status (HEALTHY/UNHEALTHY)
- Circuit breaker state (CLOSED/OPEN/HALF_OPEN)
- Success rate and error count
- Average response time
- Last success/failure timestamps
- **[Detailed]** Cost metrics (tokens, USD per email)
- **[Detailed]** Quality metrics (confidence, completeness, validation rate)
- **[Detailed]** Per-field confidence breakdown
- **[Detailed]** Orchestration configuration

---

### `llm compare`

Compare LLM provider performance across quality and value metrics.

**Usage**:
```bash
collabiq llm compare [OPTIONS]
```

**Options**:
```bash
--detailed, -d    Show detailed per-metric breakdown
```

**Examples**:
```bash
# Basic comparison
uv run collabiq llm compare

# Detailed comparison with per-metric breakdown
uv run collabiq llm compare --detailed
```

**Output**:
- **Quality Rankings**: Providers ranked by composite quality score
  - Formula: `(0.4 × confidence) + (0.3 × completeness) + (0.3 × validation)`
- **Value Rankings**: Providers ranked by quality-to-cost ratio
  - Free tier: `quality_score × 1.5`
  - Paid: `quality_score / (1 + cost_per_email × 1000)`
- **Recommendation**: Best provider with explanation
- **[Detailed]** Per-provider metrics (confidence, completeness, validation, cost)

**Requirements**:
- At least one provider must have quality metrics (processed at least 1 email)

---

### `llm set-quality-routing`

Configure quality-based provider routing.

**Usage**:
```bash
collabiq llm set-quality-routing [OPTIONS]
```

**Options**:
```bash
--enable / --disable              Enable or disable quality-based routing (required)
--min-confidence FLOAT            Minimum average confidence (0.0-1.0)
--min-completeness FLOAT          Minimum field completeness (0.0-100.0)
--max-validation-failures FLOAT   Maximum validation failure rate (0.0-100.0)
```

**Examples**:
```bash
# Enable quality routing with defaults
uv run collabiq llm set-quality-routing --enable

# Disable quality routing
uv run collabiq llm set-quality-routing --disable

# Enable with custom thresholds
uv run collabiq llm set-quality-routing --enable \
  --min-confidence 0.85 \
  --min-completeness 90.0

# Enable with strict quality requirements
uv run collabiq llm set-quality-routing --enable \
  --min-confidence 0.90 \
  --min-completeness 95.0 \
  --max-validation-failures 5.0
```

**How Quality Routing Works**:
1. System evaluates provider quality metrics
2. Providers meeting thresholds are ranked by quality score
3. Highest quality provider is tried first
4. Falls back to priority order if quality routing fails

**Note**: Quality routing requires at least one provider to have historical quality metrics.

---

### `llm test`

Test specific LLM provider connectivity and health.

**Usage**:
```bash
collabiq llm test [PROVIDER]
```

**Arguments**:
```bash
PROVIDER    Provider name (gemini, claude, openai)
```

**Examples**:
```bash
# Test Claude connectivity
uv run collabiq llm test claude

# Test all providers
uv run collabiq llm test gemini
uv run collabiq llm test claude
uv run collabiq llm test openai
```

**Output**:
- ✓ Healthy / ✗ Unhealthy status
- Circuit breaker state
- Recent error messages (if any)

---

### `llm set-strategy`

Set LLM orchestration strategy.

**Usage**:
```bash
collabiq llm set-strategy [STRATEGY]
```

**Arguments**:
```bash
STRATEGY    failover | consensus | best_match
```

**Strategies**:
- **failover**: Try providers sequentially in priority order (default)
- **consensus**: Query multiple providers and use majority vote
- **best_match**: Query all providers and select highest confidence result

**Examples**:
```bash
# Set to failover (default)
uv run collabiq llm set-strategy failover

# Set to consensus
uv run collabiq llm set-strategy consensus

# Set to best_match
uv run collabiq llm set-strategy best_match
```

---

## Email Commands

Manage email fetching, cleaning, and processing.

### `email fetch`

Fetch emails from Gmail with deduplication.

**Usage**:
```bash
collabiq email fetch [OPTIONS]
```

**Options**:
```bash
--limit INTEGER       Maximum number of emails to fetch [default: 10]
--query TEXT          Gmail search query
--label TEXT          Filter by Gmail label
--since TEXT          Fetch emails since date (YYYY-MM-DD)
```

**Examples**:
```bash
# Fetch latest 10 emails
uv run collabiq email fetch

# Fetch 50 emails
uv run collabiq email fetch --limit 50

# Fetch emails from last week
uv run collabiq email fetch --since 2025-11-01
```

---

### `email clean`

Normalize raw emails by removing signatures and quoted content.

**Usage**:
```bash
collabiq email clean [OPTIONS]
```

**Examples**:
```bash
# Clean all fetched emails
uv run collabiq email clean
```

---

### `email list`

Display recent emails with filtering options.

**Usage**:
```bash
collabiq email list [OPTIONS]
```

**Options**:
```bash
--limit INTEGER    Number of emails to display [default: 20]
--status TEXT      Filter by status (pending, processed, failed)
```

**Examples**:
```bash
# List recent 20 emails
uv run collabiq email list

# List 50 emails
uv run collabiq email list --limit 50

# List only pending emails
uv run collabiq email list --status pending
```

---

### `email process`

Run full email pipeline: fetch → clean → extract → validate → write.

**Usage**:
```bash
collabiq email process [OPTIONS]
```

**Options**:
```bash
--limit INTEGER           Maximum emails to process [default: 10]
--debug / --no-debug      Enable debug logging [default: no-debug]
--json                    Output as JSON
--quiet / --no-quiet      Suppress non-error output [default: no-quiet]
```

**Examples**:
```bash
# Process 10 emails
uv run collabiq email process

# Process 5 emails with debug logging
uv run collabiq email process --limit 5 --debug

# Process with JSON output
uv run collabiq email process --json
```

**Pipeline Stages**:
1. Fetch emails from Gmail
2. Clean and normalize content
3. Extract entities using LLM
4. Validate extracted data
5. Write to Notion

---

### `email verify`

Check Gmail connectivity and configuration.

**Usage**:
```bash
collabiq email verify
```

**Examples**:
```bash
uv run collabiq email verify
```

---

## Notion Commands

Manage Notion integration and database operations.

### `notion verify`

Verify Notion API connectivity and database access.

**Usage**:
```bash
collabiq notion verify [OPTIONS]
```

**Options**:
```bash
--json    Output as JSON
```

**Examples**:
```bash
# Verify Notion connectivity
uv run collabiq notion verify

# Verify with JSON output
uv run collabiq notion verify --json
```

---

### `notion schema`

Display Notion database schema.

**Usage**:
```bash
collabiq notion schema [DATABASE]
```

**Arguments**:
```bash
DATABASE    startups | partners | collaborations
```

**Examples**:
```bash
# View startups database schema
uv run collabiq notion schema startups

# View collaborations schema
uv run collabiq notion schema collaborations
```

---

### `notion test-write`

Test write operations to Notion database.

**Usage**:
```bash
collabiq notion test-write [OPTIONS]
```

**Examples**:
```bash
# Test write with sample data
uv run collabiq notion test-write
```

---

### `notion cleanup`

Clean up test data from Notion databases.

**Usage**:
```bash
collabiq notion cleanup [OPTIONS]
```

**Options**:
```bash
--confirm    Skip confirmation prompt
```

**Examples**:
```bash
# Clean up test data (with confirmation)
uv run collabiq notion cleanup

# Clean up without confirmation
uv run collabiq notion cleanup --confirm
```

---

## Test Commands

Testing and validation operations.

### `test validate`

Quick health checks for all system components (<10s).

**Usage**:
```bash
collabiq test validate
```

**Examples**:
```bash
uv run collabiq test validate
```

**Checks**:
- Gmail connectivity
- Notion connectivity
- LLM provider health
- Configuration validity

---

### `test select-emails`

Select test emails from Gmail for E2E testing.

**Usage**:
```bash
collabiq test select-emails [OPTIONS]
```

**Options**:
```bash
--count INTEGER    Number of emails to select [default: 5]
```

**Examples**:
```bash
# Select 5 test emails
uv run collabiq test select-emails

# Select 10 test emails
uv run collabiq test select-emails --count 10
```

---

### `test e2e`

Run end-to-end pipeline tests on selected emails.

**Usage**:
```bash
collabiq test e2e [OPTIONS]
```

**Options**:
```bash
--report    Generate detailed test report
```

**Examples**:
```bash
# Run E2E tests
uv run collabiq test e2e

# Run with detailed report
uv run collabiq test e2e --report
```

---

## Error Commands

Error management and dead-letter queue operations.

### `errors list`

List recent errors from the dead-letter queue.

**Usage**:
```bash
collabiq errors list [OPTIONS]
```

**Options**:
```bash
--limit INTEGER       Number of errors to display [default: 20]
--severity TEXT       Filter by severity (critical, high, medium, low)
--component TEXT      Filter by component
```

**Examples**:
```bash
# List recent errors
uv run collabiq errors list

# List critical errors
uv run collabiq errors list --severity critical

# List 50 recent errors
uv run collabiq errors list --limit 50
```

---

### `errors retry`

Retry failed operations from the DLQ.

**Usage**:
```bash
collabiq errors retry [ERROR_ID]
```

**Examples**:
```bash
# Retry specific error
uv run collabiq errors retry error_12345

# Retry all high-priority errors
uv run collabiq errors retry --severity high
```

---

### `errors clear`

Clear resolved errors from the DLQ.

**Usage**:
```bash
collabiq errors clear [OPTIONS]
```

**Options**:
```bash
--before TEXT    Clear errors before date (YYYY-MM-DD)
--confirm        Skip confirmation prompt
```

**Examples**:
```bash
# Clear old errors (with confirmation)
uv run collabiq errors clear --before 2025-10-01

# Clear without confirmation
uv run collabiq errors clear --before 2025-10-01 --confirm
```

---

## Status Commands

System health monitoring.

### `status`

Display overall system health status.

**Usage**:
```bash
collabiq status [OPTIONS]
```

**Options**:
```bash
--detailed    Show detailed component status
--json        Output as JSON
```

**Examples**:
```bash
# Basic system status
uv run collabiq status

# Detailed status
uv run collabiq status --detailed

# JSON output
uv run collabiq status --json
```

---

## Config Commands

Configuration management.

### `config show`

Display current configuration.

**Usage**:
```bash
collabiq config show [OPTIONS]
```

**Options**:
```bash
--secrets    Show secrets (⚠️ sensitive)
```

**Examples**:
```bash
# Show configuration
uv run collabiq config show

# Show with secrets (careful!)
uv run collabiq config show --secrets
```

---

### `config test`

Test configuration validity.

**Usage**:
```bash
collabiq config test
```

**Examples**:
```bash
uv run collabiq config test
```

---

## Common Workflows

### Initial Setup

```bash
# 1. Verify all connections
uv run collabiq test validate

# 2. Check LLM provider status
uv run collabiq llm status

# 3. Test Notion connectivity
uv run collabiq notion verify

# 4. Fetch and process sample emails
uv run collabiq email process --limit 5
```

### Daily Operations

```bash
# 1. Process new emails
uv run collabiq email process --limit 20

# 2. Check for errors
uv run collabiq errors list

# 3. View provider performance
uv run collabiq llm status --detailed
```

### Quality Metrics Workflow

```bash
# 1. Process emails to build quality metrics
uv run collabiq email process --limit 50

# 2. View quality metrics
uv run collabiq llm status --detailed

# 3. Compare provider performance
uv run collabiq llm compare --detailed

# 4. Enable quality-based routing
uv run collabiq llm set-quality-routing --enable

# 5. Process more emails with quality routing
uv run collabiq email process --limit 20
```

### Troubleshooting

```bash
# Check system health
uv run collabiq status --detailed

# Test specific provider
uv run collabiq llm test claude

# View recent errors
uv run collabiq errors list --limit 50

# Enable debug logging
uv run collabiq --debug email process --limit 5
```

---

## Environment Variables

Configuration via environment variables:

```bash
# API Keys (use Infisical secrets management in production)
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
NOTION_API_KEY=your_notion_key

# Gmail OAuth
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Notion Database IDs
NOTION_STARTUPS_DB_ID=your_db_id
NOTION_PARTNERS_DB_ID=your_db_id
NOTION_COLLABORATIONS_DB_ID=your_db_id

# Infisical (recommended for production)
INFISICAL_CLIENT_ID=your_client_id
INFISICAL_CLIENT_SECRET=your_secret
INFISICAL_PROJECT_ID=your_project_id
INFISICAL_ENVIRONMENT=development|production

# Disable color output
NO_COLOR=1
```

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - API error (Gmail, Notion, LLM)
- `4` - Validation error

---

## Getting Help

```bash
# Global help
uv run collabiq --help

# Command help
uv run collabiq llm --help
uv run collabiq email --help

# Subcommand help
uv run collabiq llm status --help
uv run collabiq llm compare --help
```

---

## Version Information

To check the CLI version:

```bash
uv run collabiq --version
```

---

## Support

- **Issues**: https://github.com/your-org/collabiq/issues
- **Documentation**: See `/docs` directory
- **Quality Metrics**: See `/docs/QUALITY_METRICS.md`
