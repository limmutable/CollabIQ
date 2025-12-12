#!/bin/bash

################################################################################
# CollabIQ Daemon State Reset Script
#
# This script resets the daemon state stored in GCS. Use this when:
# - You need to clear error counters (validation_failures, etc.)
# - You want to reprocess emails from scratch
# - The state has become corrupted
#
# Usage:
#   ./reset-state.sh [options]
#
# Required Environment Variables:
#   PROJECT_ID       - Google Cloud project ID
#
# Options:
#   -h, --help       Show this help message
#   -y, --yes        Skip confirmation prompt
#   --show-only      Only show current state, don't delete
#
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

error() { echo -e "${RED}ERROR: $1${NC}" >&2; exit 1; }
info() { echo -e "${BLUE}INFO: $1${NC}"; }
success() { echo -e "${GREEN}SUCCESS: $1${NC}"; }
warning() { echo -e "${YELLOW}WARNING: $1${NC}"; }

usage() {
    cat << EOF
CollabIQ Daemon State Reset Script

Usage: $0 [options]

Options:
    -h, --help       Show this help message
    -y, --yes        Skip confirmation prompt
    --show-only      Only show current state, don't delete

Required Environment Variables:
    PROJECT_ID       Google Cloud project ID

Examples:
    PROJECT_ID=my-project $0              # Interactive reset
    PROJECT_ID=my-project $0 --yes        # Non-interactive reset
    PROJECT_ID=my-project $0 --show-only  # View current state
EOF
    exit 0
}

# Parse arguments
SKIP_CONFIRM=false
SHOW_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) usage ;;
        -y|--yes) SKIP_CONFIRM=true ;;
        --show-only) SHOW_ONLY=true ;;
        *) error "Unknown option: $1" ;;
    esac
    shift
done

# Validate
if [ -z "$PROJECT_ID" ]; then
    error "PROJECT_ID environment variable is required"
fi

STATE_BUCKET="${PROJECT_ID}-state"
STATE_PATH="gs://${STATE_BUCKET}/daemon/state.json"

info "Project ID: $PROJECT_ID"
info "State Path: $STATE_PATH"
echo ""

# Check if state file exists
if ! gcloud storage ls "$STATE_PATH" >/dev/null 2>&1; then
    warning "No state file found at $STATE_PATH"
    info "Daemon will start with fresh state on next run"
    exit 0
fi

# Show current state
info "Current daemon state:"
echo "----------------------------------------"
gcloud storage cat "$STATE_PATH" 2>/dev/null || warning "Could not read state file"
echo "----------------------------------------"
echo ""

if [ "$SHOW_ONLY" = true ]; then
    exit 0
fi

# Confirmation
if [ "$SKIP_CONFIRM" = false ]; then
    warning "This will delete the daemon state file!"
    warning "The daemon will:"
    echo "  - Start with fresh counters (validation_failures=0, etc.)"
    echo "  - May reprocess some recent emails (duplicate detection will prevent duplicates)"
    echo ""
    read -p "Are you sure you want to reset the state? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Cancelled"
        exit 0
    fi
fi

# Delete state file
info "Deleting state file..."
gcloud storage rm "$STATE_PATH" || error "Failed to delete state file"

success "Daemon state has been reset!"
info "The daemon will start fresh on the next execution"
