#!/bin/bash

################################################################################
# CollabIQ Cloud Run Job Status Script
#
# This script shows the current configuration and execution status of the
# CollabIQ Cloud Run Job, including recent executions and logs.
#
# Usage:
#   ./status.sh [options]
#
# Required Environment Variables:
#   PROJECT_ID       - Google Cloud project ID
#
# Optional Environment Variables:
#   REGION           - GCP region (default: us-central1)
#   JOB_NAME         - Cloud Run Job name (default: collabiq-processor)
#   LOG_LINES        - Number of log lines to show (default: 50)
#
# Examples:
#   PROJECT_ID=my-project ./status.sh
#   PROJECT_ID=my-project LOG_LINES=100 ./status.sh
#   ./status.sh --help
#
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

header() {
    echo -e "${CYAN}=== $1 ===${NC}"
}

usage() {
    cat << EOF
CollabIQ Cloud Run Job Status Script

Usage: $0 [options]

Options:
    -h, --help              Show this help message
    -v, --verbose           Show detailed job configuration

Required Environment Variables:
    PROJECT_ID              Google Cloud project ID

Optional Environment Variables:
    REGION                  GCP region (default: us-central1)
    JOB_NAME                Cloud Run Job name (default: collabiq-processor)
    LOG_LINES               Number of log lines to show (default: 50)

Examples:
    PROJECT_ID=my-project $0
    PROJECT_ID=my-project LOG_LINES=100 $0
EOF
    exit 0
}

# Parse command line arguments
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
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
LOG_LINES="${LOG_LINES:-50}"

# Check for required tools
command -v gcloud >/dev/null 2>&1 || error "gcloud is required but not installed"

# Verify gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "No active gcloud authentication. Run: gcloud auth login"
fi

# Set the gcloud project
gcloud config set project "$PROJECT_ID" --quiet || error "Failed to set project"

################################################################################
# Job Status
################################################################################

header "Job Configuration"

# Check if job exists
if ! gcloud run jobs describe "$JOB_NAME" --region="$REGION" --format=json >/dev/null 2>&1; then
    error "Job '$JOB_NAME' not found in region '$REGION'"
fi

# Get job details
if [ "$VERBOSE" = true ]; then
    gcloud run jobs describe "$JOB_NAME" --region="$REGION" || error "Failed to get job details"
else
    # Show summary
    echo "Job Name:    $JOB_NAME"
    echo "Region:      $REGION"
    echo "Project:     $PROJECT_ID"
    echo ""

    # Get key configuration values
    gcloud run jobs describe "$JOB_NAME" --region="$REGION" \
        --format="table[no-heading](
            spec.template.spec.containers[0].image:label='Image',
            spec.template.spec.containers[0].resources.limits.memory:label='Memory',
            spec.template.spec.containers[0].resources.limits.cpu:label='CPU',
            spec.template.spec.taskCount:label='Tasks',
            spec.template.spec.template.spec.taskTimeout:label='Timeout'
        )" || warning "Failed to get job configuration"
fi

echo ""

################################################################################
# Recent Executions
################################################################################

header "Recent Executions (Last 10)"

# List recent executions
gcloud run jobs executions list \
    --job="$JOB_NAME" \
    --region="$REGION" \
    --limit=10 \
    --format="table(
        name.basename():label='Execution ID',
        status.completionTime.date('%Y-%m-%d %H:%M:%S'):label='Completed',
        status.succeededCount:label='Succeeded',
        status.failedCount:label='Failed',
        status.runningCount:label='Running',
        status.conditions[0].type:label='Status'
    )" || warning "Failed to list executions"

echo ""

# Get the latest execution
LATEST_EXECUTION=$(gcloud run jobs executions list \
    --job="$JOB_NAME" \
    --region="$REGION" \
    --limit=1 \
    --format="value(name.basename())" 2>/dev/null || echo "")

if [ -n "$LATEST_EXECUTION" ]; then
    header "Latest Execution Details"
    echo "Execution ID: $LATEST_EXECUTION"
    echo ""

    # Get execution status
    gcloud run jobs executions describe "$LATEST_EXECUTION" \
        --region="$REGION" \
        --format="table[no-heading](
            status.startTime.date('%Y-%m-%d %H:%M:%S'):label='Started',
            status.completionTime.date('%Y-%m-%d %H:%M:%S'):label='Completed',
            status.conditions[0].message:label='Message'
        )" || warning "Failed to get execution details"

    echo ""
fi

################################################################################
# Recent Logs
################################################################################

header "Recent Logs (Last $LOG_LINES lines)"

# Fetch recent logs
info "Fetching logs from Cloud Logging..."
gcloud logging read \
    "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
    --limit="$LOG_LINES" \
    --format="table(
        timestamp.date('%Y-%m-%d %H:%M:%S'),
        severity,
        textPayload
    )" \
    --project="$PROJECT_ID" 2>/dev/null || warning "No recent logs found or failed to fetch logs"

echo ""

################################################################################
# Summary
################################################################################

header "Quick Actions"
echo "View in Console:  https://console.cloud.google.com/run/jobs/details/${REGION}/${JOB_NAME}?project=${PROJECT_ID}"
echo "Execute Job:      ./scripts/deployment/execute.sh"
echo "View More Logs:   gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit 100"
echo ""

if [ -n "$LATEST_EXECUTION" ]; then
    # Check latest execution status
    LATEST_STATUS=$(gcloud run jobs executions describe "$LATEST_EXECUTION" \
        --region="$REGION" \
        --format="value(status.conditions[0].type)" 2>/dev/null || echo "Unknown")

    case "$LATEST_STATUS" in
        "Completed")
            success "Latest execution completed successfully"
            ;;
        "Running")
            info "Latest execution is currently running"
            ;;
        "Failed")
            error "Latest execution failed - check logs for details"
            ;;
        *)
            warning "Latest execution status: $LATEST_STATUS"
            ;;
    esac
fi
