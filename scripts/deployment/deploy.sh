#!/bin/bash

################################################################################
# CollabIQ Cloud Run Job Deployment Script
#
# This script builds a Docker image, pushes it to Google Artifact Registry,
# and deploys/updates the Cloud Run Job for CollabIQ email processing.
#
# Usage:
#   ./deploy.sh [options]
#
# Required Environment Variables:
#   PROJECT_ID       - Google Cloud project ID
#
# Optional Environment Variables:
#   REGION           - GCP region (default: us-central1)
#   REPO_NAME        - Artifact Registry repository name (default: collabiq-repo)
#   IMAGE_TAG        - Docker image tag (default: latest)
#   JOB_NAME         - Cloud Run Job name (default: collabiq-processor)
#   SERVICE_ACCOUNT  - Service account email for the job
#   MEMORY           - Memory allocation (default: 512Mi)
#   CPU              - CPU allocation (default: 1)
#   TIMEOUT          - Job timeout in seconds (default: 3600)
#   MAX_RETRIES      - Maximum retry attempts (default: 3)
#
# Examples:
#   PROJECT_ID=my-project ./deploy.sh
#   PROJECT_ID=my-project IMAGE_TAG=v1.0.0 ./deploy.sh
#   ./deploy.sh --help
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
CollabIQ Cloud Run Job Deployment Script

Usage: $0 [options]

Options:
    -h, --help              Show this help message

Required Environment Variables:
    PROJECT_ID              Google Cloud project ID

Optional Environment Variables:
    REGION                  GCP region (default: us-central1)
    REPO_NAME               Artifact Registry repository (default: collabiq-repo)
    IMAGE_TAG               Docker image tag (default: latest)
    JOB_NAME                Cloud Run Job name (default: collabiq-processor)
    SERVICE_ACCOUNT         Service account email for the job
    MEMORY                  Memory allocation (default: 512Mi)
    CPU                     CPU allocation (default: 1)
    TIMEOUT                 Job timeout in seconds (default: 3600)
    MAX_RETRIES             Maximum retry attempts (default: 3)

Examples:
    PROJECT_ID=my-project $0
    PROJECT_ID=my-project IMAGE_TAG=v1.0.0 $0
EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
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
REPO_NAME="${REPO_NAME:-collabiq-repo}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
JOB_NAME="${JOB_NAME:-collabiq-processor}"
MEMORY="${MEMORY:-512Mi}"
CPU="${CPU:-1}"
TIMEOUT="${TIMEOUT:-3600}"
MAX_RETRIES="${MAX_RETRIES:-3}"

# Construct image name
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/collabiq:${IMAGE_TAG}"

info "Deployment Configuration:"
echo "  Project ID:       $PROJECT_ID"
echo "  Region:           $REGION"
echo "  Repository:       $REPO_NAME"
echo "  Image Tag:        $IMAGE_TAG"
echo "  Job Name:         $JOB_NAME"
echo "  Image Name:       $IMAGE_NAME"
echo "  Memory:           $MEMORY"
echo "  CPU:              $CPU"
echo "  Timeout:          ${TIMEOUT}s"
echo "  Max Retries:      $MAX_RETRIES"
if [ -n "$SERVICE_ACCOUNT" ]; then
    echo "  Service Account:  $SERVICE_ACCOUNT"
fi
echo ""

# Check for required tools
command -v docker >/dev/null 2>&1 || error "docker is required but not installed"
command -v gcloud >/dev/null 2>&1 || error "gcloud is required but not installed"

# Verify gcloud authentication
info "Verifying gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "No active gcloud authentication. Run: gcloud auth login"
fi

# Set the gcloud project
info "Setting gcloud project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID" || error "Failed to set project"

################################################################################
# Docker Build
################################################################################

info "Building Docker image..."
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT" || error "Failed to change to project root"

# Verify Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    error "Dockerfile not found in $PROJECT_ROOT"
fi

# Build the image
docker build -t "$IMAGE_NAME" . || error "Docker build failed"
success "Docker image built successfully"

################################################################################
# Push to Artifact Registry
################################################################################

info "Configuring Docker for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet || \
    error "Failed to configure Docker authentication"

info "Pushing image to Artifact Registry..."
docker push "$IMAGE_NAME" || error "Failed to push image"
success "Image pushed to Artifact Registry"

################################################################################
# Deploy Cloud Run Job
################################################################################

info "Checking if Cloud Run Job exists..."
if gcloud run jobs describe "$JOB_NAME" --region="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    info "Updating existing Cloud Run Job..."
    UPDATE_ARGS=(
        jobs update "$JOB_NAME"
        --region="$REGION"
        --image="$IMAGE_NAME"
        --memory="$MEMORY"
        --cpu="$CPU"
        --task-timeout="${TIMEOUT}s"
        --max-retries="$MAX_RETRIES"
    )

    # Add service account if specified
    if [ -n "$SERVICE_ACCOUNT" ]; then
        UPDATE_ARGS+=(--service-account="$SERVICE_ACCOUNT")
    fi

    gcloud run "${UPDATE_ARGS[@]}" || error "Failed to update Cloud Run Job"
    success "Cloud Run Job updated successfully"
else
    info "Creating new Cloud Run Job..."
    CREATE_ARGS=(
        jobs create "$JOB_NAME"
        --region="$REGION"
        --image="$IMAGE_NAME"
        --memory="$MEMORY"
        --cpu="$CPU"
        --task-timeout="${TIMEOUT}s"
        --max-retries="$MAX_RETRIES"
    )

    # Add service account if specified
    if [ -n "$SERVICE_ACCOUNT" ]; then
        CREATE_ARGS+=(--service-account="$SERVICE_ACCOUNT")
    fi

    gcloud run "${CREATE_ARGS[@]}" || error "Failed to create Cloud Run Job"
    success "Cloud Run Job created successfully"
fi

################################################################################
# Summary
################################################################################

echo ""
success "Deployment completed successfully!"
echo ""
info "Next steps:"
echo "  1. Test the job: ./scripts/deployment/execute.sh"
echo "  2. Check status:  ./scripts/deployment/status.sh"
echo "  3. View logs:     gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit 50 --format json"
echo ""
info "Job URL: https://console.cloud.google.com/run/jobs/details/${REGION}/${JOB_NAME}?project=${PROJECT_ID}"
