#!/bin/bash

################################################################################
# CollabIQ Cloud Monitoring Alert Setup
#
# This script sets up Cloud Monitoring alerts for:
# 1. Cloud Run Job Failures (Result != success)
# 2. Critical/Error Logs (Severity >= ERROR)
#
# Usage:
#   ./setup_alerts.sh [options]
#
# Required Environment Variables:
#   PROJECT_ID       - Google Cloud project ID
#
# Optional Environment Variables:
#   EMAIL_ADDRESS    - Email for notifications (default: jeffreylim@signite.co)
#
################################################################################

set -e  # Exit on error

# Configuration
EMAIL_ADDRESS="${EMAIL_ADDRESS:-jeffreylim@signite.co}"
REGION="${REGION:-asia-northeast1}"

# Helper functions
error() { echo -e "\033[0;31mERROR: $1\033[0m" >&2; exit 1; }
success() { echo -e "\033[0;32mSUCCESS: $1\033[0m"; }
info() { echo -e "\033[0;34mINFO: $1\033[0m"; }

# Validation
if [ -z "$PROJECT_ID" ]; then
    error "PROJECT_ID environment variable is required"
fi

info "Setting up alerts for project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID" --quiet

################################################################################
# 1. Notification Channel
################################################################################

info "Checking notification channels..."

# Check if channel exists
EXISTING_CHANNEL=$(gcloud alpha monitoring channels list \
    --filter="type=\"email\" AND labels.email_address=\"$EMAIL_ADDRESS\"" \
    --format="value(name)" \
    --limit=1)

if [ -n "$EXISTING_CHANNEL" ]; then
    CHANNEL_ID="$EXISTING_CHANNEL"
    success "Found existing notification channel: $CHANNEL_ID"
else
    info "Creating new email notification channel for $EMAIL_ADDRESS..."
    CHANNEL_ID=$(gcloud alpha monitoring channels create \
        --display-name="CollabIQ Admin ($EMAIL_ADDRESS)" \
        --description="Primary admin email for CollabIQ alerts" \
        --type=email \
        --channel-labels=email_address="$EMAIL_ADDRESS" \
        --format="value(name)")
    
    if [ -z "$CHANNEL_ID" ]; then
        error "Failed to create notification channel"
    fi
    success "Created notification channel: $CHANNEL_ID"
fi

################################################################################
# 2. Alert Policies
################################################################################

# Create temporary directory for policy files
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# --- Policy 1: Job Failure ---
# Alert when a job execution completes with status 'failed'
cat > "$TMP_DIR/job_failure_policy.json" <<EOF
{
  "displayName": "CollabIQ: Job Failure Alert",
  "documentation": {
    "content": "The CollabIQ Cloud Run Job failed to complete successfully. Check Cloud Run logs for details.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Job Failure Count",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_job\" AND metric.type = \"run.googleapis.com/job/completed_execution_count\" AND metric.label.result = \"failed\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "crossSeriesReducer": "REDUCE_SUM",
            "perSeriesAligner": "ALIGN_COUNT"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "0s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [
    "$CHANNEL_ID"
  ]
}
EOF

# --- Policy 2: Critical Logs ---
# Alert when error logs occur
cat > "$TMP_DIR/error_log_policy.json" <<EOF
{
  "displayName": "CollabIQ: Critical/Error Logs",
  "documentation": {
    "content": "Critical or Error logs detected in CollabIQ. This may indicate application errors or system issues.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Error Log Count",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_job\" AND metric.type = \"logging.googleapis.com/log_entry_count\" AND (metric.label.severity = \"ERROR\" OR metric.label.severity = \"CRITICAL\" OR metric.label.severity = \"ALERT\" OR metric.label.severity = \"EMERGENCY\")",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "crossSeriesReducer": "REDUCE_SUM",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "0s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [
    "$CHANNEL_ID"
  ]
}
EOF

# Apply Policies
info "Applying Alert Policies..."

# Helper to create or update policy
# Note: 'create' creates duplicate if name exists. For idempotency, we'd need to check existing names.
# For simplicity in this script, we'll check if a policy with the exact Display Name exists.

create_if_missing() {
    local policy_file=$1
    local display_name=$2
    
    EXISTING_POLICY=$(gcloud alpha monitoring policies list \
        --filter="displayName=\"$display_name\"" \
        --format="value(name)" \
        --limit=1)

    if [ -n "$EXISTING_POLICY" ]; then
        info "Policy '$display_name' already exists ($EXISTING_POLICY). Updating..."
        gcloud alpha monitoring policies update "$EXISTING_POLICY" --policy-from-file="$policy_file"
        success "Updated policy: $display_name"
    else
        info "Creating policy '$display_name'..."
        gcloud alpha monitoring policies create --policy-from-file="$policy_file"
        success "Created policy: $display_name"
    fi
}

create_if_missing "$TMP_DIR/job_failure_policy.json" "CollabIQ: Job Failure Alert"
create_if_missing "$TMP_DIR/error_log_policy.json" "CollabIQ: Critical/Error Logs"

echo ""
success "Alert setup completed successfully!"
info "Notifications will be sent to: $EMAIL_ADDRESS"
info "You may need to verify your email address if this is the first time using it with Cloud Monitoring."
