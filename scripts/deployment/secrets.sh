#!/bin/bash

################################################################################
# CollabIQ Secret Manager Script
#
# This script manages Google Cloud Secret Manager secrets for CollabIQ,
# including creating, updating, listing, and importing secrets from files.
#
# Usage:
#   ./secrets.sh [command] [options]
#
# Commands:
#   list                    List all CollabIQ-related secrets
#   create-from-env         Create/update secrets from .env file
#   create-from-file        Create/update secret from a specific file
#   grant-access            Grant Cloud Run Job access to secrets
#   show                    Show details of a specific secret
#
# Required Environment Variables:
#   PROJECT_ID              - Google Cloud project ID
#
# Optional Environment Variables:
#   REGION                  - GCP region (default: us-central1)
#   SERVICE_ACCOUNT         - Service account email to grant access to
#
# Examples:
#   PROJECT_ID=my-project ./secrets.sh list
#   PROJECT_ID=my-project ./secrets.sh create-from-env
#   PROJECT_ID=my-project ./secrets.sh create-from-file credentials.json GMAIL_CREDENTIALS_JSON
#   PROJECT_ID=my-project SERVICE_ACCOUNT=sa@project.iam.gserviceaccount.com ./secrets.sh grant-access
#   ./secrets.sh --help
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
CollabIQ Secret Manager Script

Usage: $0 <command> [options]

Commands:
    list                        List all CollabIQ-related secrets
    create-from-env             Create/update secrets from .env file
    create-from-file <file> <secret-name>
                                Create/update secret from specific file
    grant-access                Grant Cloud Run Job access to secrets
    show <secret-name>          Show details of a specific secret
    help                        Show this help message

Required Environment Variables:
    PROJECT_ID                  Google Cloud project ID

Optional Environment Variables:
    REGION                      GCP region (default: us-central1)
    SERVICE_ACCOUNT             Service account email to grant access to

Examples:
    # List all secrets
    PROJECT_ID=my-project $0 list

    # Create secrets from .env file
    PROJECT_ID=my-project $0 create-from-env

    # Create secret from credentials file
    PROJECT_ID=my-project $0 create-from-file credentials.json GMAIL_CREDENTIALS_JSON

    # Grant access to service account
    PROJECT_ID=my-project SERVICE_ACCOUNT=sa@project.iam.gserviceaccount.com $0 grant-access

    # Show specific secret
    PROJECT_ID=my-project $0 show NOTION_API_KEY
EOF
    exit 0
}

################################################################################
# Configuration & Validation
################################################################################

# Check command
if [ $# -lt 1 ]; then
    usage
fi

COMMAND=$1
shift

# Check required environment variables
if [ -z "$PROJECT_ID" ]; then
    error "PROJECT_ID environment variable is required"
fi

# Set defaults
REGION="${REGION:-asia-northeast1}"

# Check for required tools
command -v gcloud >/dev/null 2>&1 || error "gcloud is required but not installed"

# Verify gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    error "No active gcloud authentication. Run: gcloud auth login"
fi

# Set the gcloud project
gcloud config set project "$PROJECT_ID" --quiet || error "Failed to set project"

################################################################################
# Helper Functions
################################################################################

# Create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2

    if gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
        info "Updating existing secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=- || \
            error "Failed to update secret $secret_name"
        success "Updated secret: $secret_name"
    else
        info "Creating new secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create "$secret_name" \
            --replication-policy="automatic" \
            --data-file=- || \
            error "Failed to create secret $secret_name"
        success "Created secret: $secret_name"
    fi
}

# Create or update a secret from file
create_or_update_secret_from_file() {
    local file_path=$1
    local secret_name=$2

    if [ ! -f "$file_path" ]; then
        error "File not found: $file_path"
    fi

    if gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
        info "Updating existing secret: $secret_name from file: $file_path"
        gcloud secrets versions add "$secret_name" --data-file="$file_path" || \
            error "Failed to update secret $secret_name"
        success "Updated secret: $secret_name from $file_path"
    else
        info "Creating new secret: $secret_name from file: $file_path"
        gcloud secrets create "$secret_name" \
            --replication-policy="automatic" \
            --data-file="$file_path" || \
            error "Failed to create secret $secret_name"
        success "Created secret: $secret_name from $file_path"
    fi
}

################################################################################
# Command: List Secrets
################################################################################

cmd_list() {
    header "CollabIQ Secrets"

    # List all secrets (filter for CollabIQ-related ones)
    info "Fetching secrets from Secret Manager..."

    gcloud secrets list \
        --format="table(
            name:label='Secret Name',
            createTime.date('%Y-%m-%d %H:%M:%S'):label='Created',
            labels:label='Labels'
        )" || warning "Failed to list secrets"

    echo ""
    info "Total secrets: $(gcloud secrets list --format='value(name)' | wc -l | tr -d ' ')"
}

################################################################################
# Command: Create from .env
################################################################################

cmd_create_from_env() {
    header "Creating Secrets from .env File"

    # Find .env file
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    ENV_FILE="$PROJECT_ROOT/.env"

    if [ ! -f "$ENV_FILE" ]; then
        error ".env file not found at $ENV_FILE"
    fi

    info "Reading secrets from: $ENV_FILE"
    echo ""

    # Read .env file and create secrets
    # Skip comments and empty lines
    local count=0
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ -z "$key" || "$key" =~ ^#.* ]]; then
            continue
        fi

        # Remove leading/trailing whitespace and quotes
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        # Skip if value is empty
        if [ -z "$value" ]; then
            warning "Skipping $key (empty value)"
            continue
        fi

        # Create or update the secret
        create_or_update_secret "$key" "$value"
        ((count++))

    done < "$ENV_FILE"

    echo ""
    success "Processed $count secrets from .env file"
}

################################################################################
# Command: Create from File
################################################################################

cmd_create_from_file() {
    if [ $# -lt 2 ]; then
        error "Usage: $0 create-from-file <file-path> <secret-name>"
    fi

    local file_path=$1
    local secret_name=$2

    header "Creating Secret from File"

    info "File:        $file_path"
    info "Secret Name: $secret_name"
    echo ""

    create_or_update_secret_from_file "$file_path" "$secret_name"
}

################################################################################
# Command: Grant Access
################################################################################

cmd_grant_access() {
    header "Granting Secret Access to Service Account"

    if [ -z "$SERVICE_ACCOUNT" ]; then
        error "SERVICE_ACCOUNT environment variable is required for this command"
    fi

    info "Service Account: $SERVICE_ACCOUNT"
    echo ""

    # Get all secrets
    SECRETS=$(gcloud secrets list --format="value(name)")

    if [ -z "$SECRETS" ]; then
        warning "No secrets found"
        exit 0
    fi

    local count=0
    while IFS= read -r secret_name; do
        info "Granting access to: $secret_name"

        gcloud secrets add-iam-policy-binding "$secret_name" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet || warning "Failed to grant access to $secret_name"

        ((count++))
    done <<< "$SECRETS"

    echo ""
    success "Granted access to $count secrets"
}

################################################################################
# Command: Show Secret
################################################################################

cmd_show() {
    if [ $# -lt 1 ]; then
        error "Usage: $0 show <secret-name>"
    fi

    local secret_name=$1

    header "Secret Details: $secret_name"

    # Show secret metadata
    gcloud secrets describe "$secret_name" || error "Secret not found: $secret_name"

    echo ""
    info "Recent Versions:"
    gcloud secrets versions list "$secret_name" \
        --limit=5 \
        --format="table(
            name.basename():label='Version',
            createTime.date('%Y-%m-%d %H:%M:%S'):label='Created',
            state:label='State'
        )" || warning "Failed to list versions"

    echo ""
    warning "To view the secret value:"
    echo "  gcloud secrets versions access latest --secret=\"$secret_name\""
}

################################################################################
# Command Dispatcher
################################################################################

case "$COMMAND" in
    list)
        cmd_list
        ;;
    create-from-env)
        cmd_create_from_env
        ;;
    create-from-file)
        cmd_create_from_file "$@"
        ;;
    grant-access)
        cmd_grant_access
        ;;
    show)
        cmd_show "$@"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        error "Unknown command: $COMMAND. Use 'help' for usage information."
        ;;
esac
