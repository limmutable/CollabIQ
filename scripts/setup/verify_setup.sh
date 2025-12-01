#!/usr/bin/env bash
# Quickstart verification script for Email Reception and Normalization feature
# Checks all prerequisites per quickstart.md
#
# Usage:
#   ./scripts/verify_setup.sh
#   ./scripts/verify_setup.sh --verbose

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VERBOSE=false
if [[ "${1:-}" == "--verbose" ]]; then
    VERBOSE=true
fi

ERRORS=0
WARNINGS=0

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_header() {
    echo
    echo -e "${BLUE}═══ $1 ═══${NC}"
}

# ================================
# Check Python 3.12
# ================================
log_header "Python 3.12"

if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [[ "$PYTHON_MAJOR" == "3" ]] && [[ "$PYTHON_MINOR" == "12" ]]; then
        log_success "Python $PYTHON_VERSION found"
    else
        log_warning "Python $PYTHON_VERSION found (expected 3.12.x)"
        log_info "This project requires Python 3.12"
    fi
else
    log_error "Python not found in PATH"
    log_info "Install Python 3.12: https://www.python.org/downloads/"
fi

# ================================
# Check UV package manager
# ================================
log_header "UV Package Manager"

if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1 | awk '{print $2}')
    log_success "UV $UV_VERSION found"
else
    log_error "UV not found in PATH"
    log_info "Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# ================================
# Check Git
# ================================
log_header "Git"

if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version 2>&1 | awk '{print $3}')
    log_success "Git $GIT_VERSION found"
else
    log_error "Git not found in PATH"
fi

# ================================
# Check Google Cloud CLI (optional)
# ================================
log_header "Google Cloud CLI (Optional)"

if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud --version 2>&1 | head -n1 | awk '{print $4}')
    log_success "gcloud $GCLOUD_VERSION found"
else
    log_warning "gcloud not found in PATH"
    log_info "Optional for Pub/Sub features: https://cloud.google.com/sdk/docs/install"
fi

# ================================
# Check Project Structure
# ================================
log_header "Project Structure"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "pyproject.toml" ]]; then
    log_success "pyproject.toml found"
else
    log_error "pyproject.toml not found"
fi

if [[ -d "src" ]]; then
    log_success "src/ directory found"
else
    log_error "src/ directory not found"
fi

if [[ -d "tests" ]]; then
    log_success "tests/ directory found"
else
    log_warning "tests/ directory not found"
fi

# ================================
# Check Gmail Credentials
# ================================
log_header "Gmail API Credentials"

if [[ -f "credentials.json" ]]; then
    log_success "credentials.json found"

    # Check if it's valid JSON
    if command -v python &> /dev/null; then
        if python -c "import json; json.load(open('credentials.json'))" 2>/dev/null; then
            log_success "credentials.json is valid JSON"
        else
            log_error "credentials.json is not valid JSON"
        fi
    fi
else
    log_error "credentials.json not found"
    log_info "Download OAuth2 credentials from Google Cloud Console"
    log_info "Place in project root as credentials.json"
fi

if [[ -f "token.json" ]]; then
    log_success "token.json found (OAuth already completed)"
else
    log_warning "token.json not found (OAuth flow will run on first use)"
fi

# ================================
# Check Virtual Environment
# ================================
log_header "Virtual Environment"

if [[ -d ".venv" ]]; then
    log_success ".venv/ directory found"

    # Check if UV is managing the venv
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        log_success "Virtual environment is configured"
    fi
else
    log_warning ".venv/ not found"
    log_info "Run: uv sync"
fi

# ================================
# Check Dependencies
# ================================
log_header "Python Dependencies"

if command -v uv &> /dev/null; then
    if [[ -f "pyproject.toml" ]]; then
        # Check critical dependencies
        DEPS=("pydantic" "pydantic-settings" "google-api-python-client" "google-auth")

        for dep in "${DEPS[@]}"; do
            if uv pip list 2>/dev/null | grep -q "$dep"; then
                log_success "$dep installed"
            else
                log_error "$dep not installed"
                log_info "Run: uv sync"
            fi
        done
    fi
fi

# ================================
# Check Directory Permissions
# ================================
log_header "Directory Permissions"

DIRS=("data" "data/raw" "data/cleaned" "logs")

for dir in "${DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        if [[ -w "$dir" ]]; then
            log_success "$dir/ is writable"
        else
            log_error "$dir/ is not writable"
        fi
    else
        # Try to create directory
        if mkdir -p "$dir" 2>/dev/null; then
            log_success "$dir/ created successfully"
        else
            log_error "Cannot create $dir/ (permission denied)"
        fi
    fi
done

# ================================
# Check .env File
# ================================
log_header "Environment Configuration"

if [[ -f ".env" ]]; then
    log_success ".env file found"

    # Check for common variables
    if grep -q "GMAIL_CREDENTIALS_PATH" .env 2>/dev/null; then
        log_success "GMAIL_CREDENTIALS_PATH configured"
    else
        log_warning "GMAIL_CREDENTIALS_PATH not in .env (will use default)"
    fi
else
    log_warning ".env file not found (will use defaults)"
    log_info "Create .env file for custom configuration"
fi

# ================================
# Run Python Configuration Check
# ================================
log_header "Python Configuration Validation"

if command -v uv &> /dev/null && [[ -f "pyproject.toml" ]]; then
    if uv run python -c "from src.config.settings import get_settings; get_settings()" 2>/dev/null; then
        log_success "Pydantic settings load successfully"
    else
        log_error "Failed to load Pydantic settings"
        if [[ "$VERBOSE" == true ]]; then
            log_info "Error details:"
            uv run python -c "from src.config.settings import get_settings; get_settings()" 2>&1 | sed 's/^/  /'
        fi
    fi

    if uv run python -c "from src.config.validation import validate_configuration; result = validate_configuration(); exit(0 if result.is_valid else 1)" 2>/dev/null; then
        log_success "Configuration validation passed"
    else
        log_error "Configuration validation failed"
        if [[ "$VERBOSE" == true ]]; then
            log_info "Running detailed validation:"
            uv run python -c "from src.config.validation import validate_on_startup; validate_on_startup()" 2>&1 | sed 's/^/  /' || true
        fi
    fi
else
    log_warning "Skipping Python configuration check (dependencies not installed)"
fi

# ================================
# Summary
# ================================
log_header "Summary"

echo
if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo
    echo "You're ready to run the email reception pipeline:"
    echo "  uv run python src/cli.py fetch --max-results 10"
    echo
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}Note: $WARNINGS warning(s) detected${NC}"
    fi
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) detected${NC}"
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) detected${NC}"
    fi
    echo
    echo "Please fix the errors above before proceeding."
    echo
    echo "Common fixes:"
    echo "  1. Install dependencies: uv sync"
    echo "  2. Download Gmail credentials: credentials.json"
    echo "  3. Verify Python 3.12 is installed"
    echo
    exit 1
fi
