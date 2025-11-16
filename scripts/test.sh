#!/usr/bin/env bash
#
# CollabIQ Test Runner Script
# Provides convenient shortcuts for running tests
#
# Usage: ./scripts/test.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${GREEN}===> $1${NC}\n"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_usage() {
    cat << EOF
CollabIQ Test Runner

Usage: ./scripts/test.sh [command] [options]

Commands:
    all             Run all tests (default)
    unit            Run unit tests only
    integration     Run integration tests only
    contract        Run contract tests only
    e2e             Run E2E tests only
    quick           Run quick smoke test (unit tests, quiet mode)
    coverage        Run tests with coverage report
    watch           Run tests, re-run on file changes (requires pytest-watch)
    failed          Re-run only failed tests from last run
    slow            Show slowest tests
    help            Show this help message

Options:
    -v, --verbose   Verbose output
    -q, --quiet     Quiet output
    -s, --stdout    Show stdout (don't capture)
    -k PATTERN      Run tests matching PATTERN
    --pdb           Drop into debugger on failure
    --maxfail=N     Stop after N failures
    --durations=N   Show N slowest tests

Examples:
    ./scripts/test.sh                          # Run all tests
    ./scripts/test.sh unit -v                  # Run unit tests verbosely
    ./scripts/test.sh integration -k duplicate # Run integration tests matching "duplicate"
    ./scripts/test.sh coverage                 # Run with coverage report
    ./scripts/test.sh quick                    # Quick smoke test
    ./scripts/test.sh failed                   # Re-run last failures

EOF
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "UV is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Parse command
COMMAND="${1:-all}"
shift || true  # Remove command from args, ignore error if no args

# Build pytest command based on command
case "$COMMAND" in
    all)
        print_header "Running all tests"
        uv run pytest "$@"
        ;;
    unit)
        print_header "Running unit tests"
        uv run pytest tests/unit/ "$@"
        ;;
    integration)
        print_header "Running integration tests"
        uv run pytest tests/integration/ "$@"
        ;;
    contract)
        print_header "Running contract tests"
        uv run pytest tests/contract/ "$@"
        ;;
    e2e)
        print_header "Running E2E tests"
        print_warning "E2E tests require API credentials (Gmail, Notion, LLM APIs)"
        uv run pytest tests/e2e/ "$@"
        ;;
    quick)
        print_header "Running quick smoke test (unit tests only)"
        uv run pytest tests/unit/ -q "$@"
        ;;
    coverage)
        print_header "Running tests with coverage"
        uv run pytest --cov=src --cov-report=term-missing --cov-report=html "$@"
        echo -e "\n${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;
    watch)
        if ! uv pip show pytest-watch &> /dev/null; then
            print_error "pytest-watch not installed. Install it with: uv add --dev pytest-watch"
            exit 1
        fi
        print_header "Watching for changes..."
        uv run ptw --runner "pytest $*"
        ;;
    failed)
        print_header "Re-running failed tests from last run"
        uv run pytest --lf "$@"
        ;;
    slow)
        print_header "Showing slowest tests"
        DURATIONS="${1:-20}"
        uv run pytest --durations="$DURATIONS" -q
        ;;
    help|--help|-h)
        print_usage
        exit 0
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        print_usage
        exit 1
        ;;
esac

# Print summary
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ Tests passed${NC}\n"
else
    echo -e "\n${RED}✗ Tests failed${NC}\n"
fi

exit $EXIT_CODE
