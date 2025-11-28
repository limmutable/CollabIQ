#!/bin/bash

################################################################################
# CollabIQ Cloud Run Job Execution Script
#
# This script executes the CollabIQ Cloud Run Job with optional command
# arguments and can stream logs in real-time.
#
# Usage:
#   ./execute.sh [options] [-- command args...]
#
# Required Environment Variables:
#   PROJECT_ID       - Google Cloud project ID
#
# Optional Environment Variables:
#   REGION           - GCP region (default: us-central1)
#   JOB_NAME         - Cloud Run Job name (default: collabiq-processor)
#
# Examples:
#   PROJECT_ID=my-project ./execute.sh
#   PROJECT_ID=my-project ./execute.sh --follow
#   PROJECT_ID=my-project ./execute.sh -- daemon start
#   PROJECT_ID=my-project ./execute.sh --follow -- process --batch-size 10
#   ./execute.sh --help
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

usage() {
    cat << EOF
CollabIQ Cloud Run Job Execution Script

Usage: $0 [options] [-- command args...]

Options:
    -h, --help              Show this help message
    -f, --follow            Stream logs in real-time after execution
    -w, --wait              Wait for execution to complete
    --                      Separator before command arguments

Required Environment Variables:
    PROJECT_ID              Google Cloud project ID

Optional Environment Variables:
    REGION                  GCP region (default: us-central1)
    JOB_NAME                Cloud Run Job name (default: collabiq-processor)

Command Arguments:
    Arguments after '--' are passed to the CollabIQ CLI inside the container.
    Default: daemon start

Examples:
    # Execute with default command (daemon start)
    PROJECT_ID=my-project $0

    # Execute and follow logs
    PROJECT_ID=my-project $0 --follow

    # Execute with custom command
    PROJECT_ID=my-project $0 -- process --batch-size 10

    # Execute, wait for completion, and follow logs
    PROJECT_ID=my-project $0 --wait --follow -- daemon start --max-cycles 5
EOF
    exit 0
}

# Parse command line arguments
FOLLOW_LOGS=false
WAIT_FOR_COMPLETION=false
COMMAND_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -f|--follow)
            FOLLOW_LOGS=true
            shift
            ;;
        -w|--wait)
            WAIT_FOR_COMPLETION=true
            shift
            ;;
        --)
            shift
            # Everything after -- is command arguments
            COMMAND_ARGS=("$@")
            break
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

# Default command if none provided
if [ ${#COMMAND_ARGS[@]} -eq 0 ]; then
    COMMAND_ARGS=("daemon" "start")
    info "Using default command: daemon start"
fi

info "Execution Configuration:"
echo "  Project ID:       $PROJECT_ID"
echo "  Region:           $REGION"
echo "  Job Name:         $JOB_NAME"
echo "  Command:          ${COMMAND_ARGS[*]}"
echo "  Follow Logs:      $FOLLOW_LOGS"
echo "  Wait:             $WAIT_FOR_COMPLETION"
echo ""

# Check for required tools
command -v gcloud >/dev/null 2>&1 || error "gcloud is required but not installed"

# Verify gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "No active gcloud authentication. Run: gcloud auth login"
fi

# Set the gcloud project
gcloud config set project "$PROJECT_ID" --quiet || error "Failed to set project"

################################################################################
# Execute Job
################################################################################

info "Executing Cloud Run Job..."

# Build the gcloud command
EXECUTE_ARGS=(
    run jobs execute "$JOB_NAME"
    --region="$REGION"
)

# Add command arguments as container args
if [ ${#COMMAND_ARGS[@]} -gt 0 ]; then
    EXECUTE_ARGS+=(--args="${COMMAND_ARGS[*]}")
fi

# Add wait flag if requested
if [ "$WAIT_FOR_COMPLETION" = true ]; then
    EXECUTE_ARGS+=(--wait)
fi

# Execute the job and capture the execution name
EXECUTION_OUTPUT=$(gcloud "${EXECUTE_ARGS[@]}" 2>&1) || error "Failed to execute job"
echo "$EXECUTION_OUTPUT"

# Extract execution ID from output
EXECUTION_ID=$(echo "$EXECUTION_OUTPUT" | grep -oE 'collabiq-processor-[a-z0-9]+' | head -n 1)

if [ -z "$EXECUTION_ID" ]; then
    warning "Could not extract execution ID from output"
    EXECUTION_ID=$(gcloud run jobs executions list \
        --job="$JOB_NAME" \
        --region="$REGION" \
        --limit=1 \
        --format="value(name.basename())" 2>/dev/null || echo "")
fi

if [ -n "$EXECUTION_ID" ]; then
    success "Job execution started: $EXECUTION_ID"
    echo ""
    info "Console URL: https://console.cloud.google.com/run/jobs/executions/details/${REGION}/${EXECUTION_ID}?project=${PROJECT_ID}"
    echo ""
else
    warning "Could not determine execution ID"
fi

################################################################################
# Follow Logs
################################################################################

if [ "$FOLLOW_LOGS" = true ]; then
    if [ -z "$EXECUTION_ID" ]; then
        warning "Cannot follow logs without execution ID"
        exit 0
    fi

    info "Following logs for execution: $EXECUTION_ID"
    echo "Press Ctrl+C to stop following logs"
    echo ""

    # Wait a moment for logs to start appearing
    sleep 2

    # Stream logs
    gcloud logging tail \
        "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME AND labels.\"run.googleapis.com/execution_name\"=$EXECUTION_ID" \
        --format="value(textPayload)" \
        --project="$PROJECT_ID" 2>/dev/null || {
            warning "Failed to stream logs"
            info "Try viewing logs manually:"
            echo "  gcloud logging read \"resource.type=cloud_run_job AND labels.\\\"run.googleapis.com/execution_name\\\"=$EXECUTION_ID\" --limit 100"
        }
fi

################################################################################
# Summary
################################################################################

echo ""
info "Job execution initiated successfully"

if [ -n "$EXECUTION_ID" ]; then
    echo ""
    info "Next steps:"
    echo "  Check status:     ./scripts/deployment/status.sh"
    echo "  View logs:        gcloud logging read \"resource.type=cloud_run_job AND labels.\\\"run.googleapis.com/execution_name\\\"=$EXECUTION_ID\" --limit 100"
    echo "  Follow logs:      gcloud logging tail \"resource.type=cloud_run_job AND labels.\\\"run.googleapis.com/execution_name\\\"=$EXECUTION_ID\""
fi
