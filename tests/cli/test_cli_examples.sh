#!/bin/bash
# CLI Usage Examples - Real-world command examples
# Copy and paste these commands to test specific features

cat << 'EOF'
=================================================================
CollabIQ Admin CLI - Usage Examples
=================================================================

Copy and paste these commands to test the CLI interactively.

-------------------------------------------------------------------
BASIC HELP
-------------------------------------------------------------------

# Show all available commands
uv run collabiq --help

# Show help for a specific command group
uv run collabiq email --help
uv run collabiq notion --help
uv run collabiq llm --help

-------------------------------------------------------------------
EMAIL COMMANDS (Phase 4)
-------------------------------------------------------------------

# List emails (interactive table format)
uv run collabiq email list

# List emails with limit
uv run collabiq email list --limit 10

# List emails in JSON format (for automation)
uv run collabiq email list --json

# List emails since a specific date
uv run collabiq email list --since "2025-11-01"

# Fetch emails from Gmail
uv run collabiq email fetch --limit 5

# Verify Gmail connection
uv run collabiq email verify

# Clean emails (remove signatures, quoted content)
uv run collabiq email clean

# Full pipeline (fetch → clean → extract → write)
uv run collabiq email process --limit 3

-------------------------------------------------------------------
NOTION COMMANDS (Phase 5)
-------------------------------------------------------------------

# Verify Notion connection and schema
uv run collabiq notion verify

# Display database schema
uv run collabiq notion schema

# Create a test entry (auto-cleanup)
uv run collabiq notion test-write

# Remove all test entries
uv run collabiq notion cleanup-tests

# Skip confirmation prompt
uv run collabiq notion cleanup-tests --yes

# JSON output
uv run collabiq notion verify --json
uv run collabiq notion schema --json

-------------------------------------------------------------------
LLM COMMANDS (Phase 6)
-------------------------------------------------------------------

# View LLM provider status
uv run collabiq llm status

# View LLM status in JSON format
uv run collabiq llm status --json

# Test specific provider connectivity
uv run collabiq llm test gemini

# View current orchestration policy
uv run collabiq llm policy

# View usage statistics
uv run collabiq llm usage

# Set orchestration policy (requires Phase 3b)
uv run collabiq llm set-policy failover

# Disable/enable providers (requires Phase 3b)
uv run collabiq llm disable claude
uv run collabiq llm enable openai

-------------------------------------------------------------------
GLOBAL OPTIONS
-------------------------------------------------------------------

# Enable debug logging
uv run collabiq --debug email list

# Quiet mode (suppress non-error output)
uv run collabiq --quiet email list

# Disable color output
uv run collabiq --no-color email list

# Combine options
uv run collabiq --debug --no-color email fetch --limit 5

-------------------------------------------------------------------
JSON MODE (for automation/scripting)
-------------------------------------------------------------------

# Get email list as JSON
uv run collabiq email list --json | jq '.'

# Get LLM status as JSON
uv run collabiq llm status --json | jq '.data'

# Get Notion schema as JSON
uv run collabiq notion schema --json | jq '.data.properties'

-------------------------------------------------------------------
STUB COMMANDS (Not Yet Implemented - Phase 7-11)
-------------------------------------------------------------------

# These will show help but commands are not yet implemented:
uv run collabiq test --help        # E2E testing (Phase 7)
uv run collabiq errors --help      # Error management (Phase 8)
uv run collabiq status --help      # System health (Phase 9)
uv run collabiq config --help      # Configuration (Phase 10)

=================================================================
EOF
