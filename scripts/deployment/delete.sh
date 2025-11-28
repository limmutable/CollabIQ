#!/bin/bash

################################################################################
# CollabIQ Cloud Run Job Deletion Script
#
# This script deletes the Cloud Run Job and optionally the associated
# Cloud Scheduler job. Use this before deploying to a new region.
#
# Usage:
#   ./delete.sh [options]
#
# Required Environment Variables:
#   PROJECT_ID       - Google Cloud project ID
#
# Optional Environment Variables:
#   REGION           - GCP region (default: asia-northeast1)
#   JOB_NAME         - Cloud Run Job name (default: collabiq-processor)
#
# Examples:
#   PROJECT_ID=my-project ./delete.sh
#   PROJECT_ID=my-project REGION=us-central1 ./delete.sh
#   ./delete.sh --help
#
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

usage() {
    cat << EOF
CollabIQ Cloud Run Job Deletion Script

Usage: $0 [options]

Options:
    -h, --help              Show this help message
    -y, --yes               Skip confirmation prompt
    --scheduler-only        Only delete the scheduler job
    --job-only              Only delete the Cloud Run job

Required Environment Variables:
    PROJECT_ID              Google Cloud project ID

Optional Environment Variables:
    REGION                  GCP region (default: asia-northeast1)
    JOB_NAME                Cloud Run Job name (default: collabiq-processor)

Examples:
    PROJECT_ID=my-project $0
    PROJECT_ID=my-project REGION=us-central1 $0
    PROJECT_ID=my-project $0 --yes              # Skip confirmation
EOF
    exit 0
}

# Flags
SKIP_CONFIRM=false
SCHEDULER_ONLY=false
JOB_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -y|--yes)
            SKIP_CONFIRM=true
            ;;
        --scheduler-only)
            SCHEDULER_ONLY=true
            ;;
        --job-only)
            JOB_ONLY=true
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
    shift
done

################################################################################
# Configuration & Validation
################################################################################

# Check required environment variables
if [ -z "$PROJECT_ID" ]; then
    error "PROJECT_ID environment variable is required"
fi

# Set defaults for optional variables
REGION="${REGION:-asia-northeast1}"
JOB_NAME="${JOB_NAME:-collabiq-processor}"
SCHEDULER_JOB_NAME="${JOB_NAME}-scheduler"

info "Deletion Configuration:"
echo "  Project ID:       $PROJECT_ID"
echo "  Region:           $REGION"
echo "  Job Name:         $JOB_NAME"
echo "  Scheduler Name:   $SCHEDULER_JOB_NAME"
echo ""

# Check for required tools
command -v gcloud >/dev/null 2>&1 || error "gcloud is required but not installed"

# Verify gcloud authentication
info "Verifying gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "No active gcloud authentication. Run: gcloud auth login"
fi

# Set the gcloud project
gcloud config set project "$PROJECT_ID" --quiet || error "Failed to set project"

################################################################################
# Confirmation
################################################################################

if [ "$SKIP_CONFIRM" = false ]; then
    echo ""
    warning "This will delete the following resources:"
    if [ "$SCHEDULER_ONLY" = false ]; then
        echo "  - Cloud Run Job: $JOB_NAME (region: $REGION)"
    fi
    if [ "$JOB_ONLY" = false ]; then
        echo "  - Cloud Scheduler Job: $SCHEDULER_JOB_NAME (location: $REGION)"
    fi
    echo ""
    read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Deletion cancelled."
        exit 0
    fi
fi

################################################################################
# Delete Cloud Scheduler Job
################################################################################

if [ "$JOB_ONLY" = false ]; then
    info "Checking for Cloud Scheduler job..."
    if gcloud scheduler jobs describe "$SCHEDULER_JOB_NAME" --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
        info "Deleting Cloud Scheduler job: $SCHEDULER_JOB_NAME"
        gcloud scheduler jobs delete "$SCHEDULER_JOB_NAME" --location="$REGION" --quiet || \
            warning "Failed to delete scheduler job (may not exist)"
        success "Cloud Scheduler job deleted"
    else
        info "Cloud Scheduler job not found: $SCHEDULER_JOB_NAME (skipping)"
    fi
fi

################################################################################
# Delete Cloud Run Job
################################################################################

if [ "$SCHEDULER_ONLY" = false ]; then
    info "Checking for Cloud Run job..."
    if gcloud run jobs describe "$JOB_NAME" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
        info "Deleting Cloud Run job: $JOB_NAME"
        gcloud run jobs delete "$JOB_NAME" --region="$REGION" --quiet || \
            error "Failed to delete Cloud Run job"
        success "Cloud Run job deleted"
    else
        info "Cloud Run job not found: $JOB_NAME (skipping)"
    fi
fi

################################################################################
# Summary
################################################################################

echo ""
success "Deletion completed!"
echo ""
info "To deploy to a new region, run:"
echo "  PROJECT_ID=$PROJECT_ID REGION=NEW_REGION ./scripts/deployment/deploy.sh"
echo ""
info "To list all jobs across regions:"
echo "  gcloud run jobs list"
echo ""
