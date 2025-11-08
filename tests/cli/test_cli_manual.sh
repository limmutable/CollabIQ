#!/bin/bash
# Manual CLI Testing Script for CollabIQ Admin CLI
# Run this to test all implemented commands interactively

set -e

echo "==================================================================="
echo "CollabIQ Admin CLI - Manual Testing Script"
echo "==================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function
run_test() {
    echo -e "${BLUE}▶ Testing: $1${NC}"
    echo -e "${YELLOW}Command: $2${NC}"
    echo ""
    eval "$2"
    echo ""
    echo -e "${GREEN}✓ Test complete${NC}"
    echo "-------------------------------------------------------------------"
    echo ""
}

# Main CLI Help
echo "==================================================================="
echo "1. MAIN CLI HELP"
echo "==================================================================="
run_test "Main app help text" "uv run collabiq --help"

# Global Options
echo "==================================================================="
echo "2. GLOBAL OPTIONS"
echo "==================================================================="
run_test "Debug flag" "uv run collabiq --debug email --help"
run_test "No-color flag" "uv run collabiq --no-color email --help"
run_test "Quiet flag" "uv run collabiq --quiet --help"

# Email Commands
echo "==================================================================="
echo "3. EMAIL COMMANDS"
echo "==================================================================="
run_test "Email group help" "uv run collabiq email --help"
run_test "Email fetch help" "uv run collabiq email fetch --help"
run_test "Email clean help" "uv run collabiq email clean --help"
run_test "Email list help" "uv run collabiq email list --help"
run_test "Email verify help" "uv run collabiq email verify --help"
run_test "Email process help" "uv run collabiq email process --help"

echo "--- Testing Email Commands with JSON Output ---"
run_test "Email list (JSON mode)" "uv run collabiq email list --json --limit 5"
run_test "Email verify (JSON mode)" "uv run collabiq email verify --json"

# Notion Commands
echo "==================================================================="
echo "4. NOTION COMMANDS"
echo "==================================================================="
run_test "Notion group help" "uv run collabiq notion --help"
run_test "Notion verify help" "uv run collabiq notion verify --help"
run_test "Notion schema help" "uv run collabiq notion schema --help"
run_test "Notion test-write help" "uv run collabiq notion test-write --help"
run_test "Notion cleanup-tests help" "uv run collabiq notion cleanup-tests --help"

echo "--- Testing Notion Commands (if credentials available) ---"
echo "Note: These will fail gracefully if Notion is not configured"
run_test "Notion verify (JSON mode)" "uv run collabiq notion verify --json || true"

# LLM Commands
echo "==================================================================="
echo "5. LLM COMMANDS"
echo "==================================================================="
run_test "LLM group help" "uv run collabiq llm --help"
run_test "LLM status help" "uv run collabiq llm status --help"
run_test "LLM test help" "uv run collabiq llm test --help"
run_test "LLM policy help" "uv run collabiq llm policy --help"
run_test "LLM set-policy help" "uv run collabiq llm set-policy --help"
run_test "LLM usage help" "uv run collabiq llm usage --help"
run_test "LLM disable help" "uv run collabiq llm disable --help"
run_test "LLM enable help" "uv run collabiq llm enable --help"

echo "--- Testing LLM Commands with JSON Output ---"
run_test "LLM status (normal output)" "uv run collabiq llm status"
run_test "LLM status (JSON mode)" "uv run collabiq llm status --json"
run_test "LLM policy" "uv run collabiq llm policy"
run_test "LLM usage" "uv run collabiq llm usage"

echo "--- Testing LLM Test Command ---"
run_test "LLM test gemini" "uv run collabiq llm test gemini || true"

# Stub Commands (Not Yet Implemented)
echo "==================================================================="
echo "6. STUB COMMANDS (Not Yet Implemented)"
echo "==================================================================="
run_test "Test group help" "uv run collabiq test --help"
run_test "Errors group help" "uv run collabiq errors --help"
run_test "Status group help" "uv run collabiq status --help"
run_test "Config group help" "uv run collabiq config --help"

echo "==================================================================="
echo "ALL TESTS COMPLETE!"
echo "==================================================================="
echo ""
echo "Summary:"
echo "- Phase 1-3: Setup, Foundation, Single Entry Point ✓"
echo "- Phase 4: Email Pipeline Commands ✓"
echo "- Phase 5: Notion Integration Commands ✓"
echo "- Phase 6: LLM Provider Management ✓"
echo "- Phase 7-11: Not yet implemented (stub commands only)"
echo ""
echo "Next steps:"
echo "- Review the output above for any errors"
echo "- Test with real data if Notion/Gmail credentials are configured"
echo "- Continue with Phase 7 (E2E Testing) implementation"
echo ""
