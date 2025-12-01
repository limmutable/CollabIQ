#!/bin/bash
# Check for running Cloud Run executions in a specific region

# Set region (default to asia-northeast1 if not provided via env var)
REGION="${REGION:-asia-northeast1}"

echo "🔍 Checking for running Cloud Run executions in $REGION..."

# Get running executions (Completed condition is Unknown)
RUNNING=$(gcloud run jobs executions list \
  --region=$REGION \
  --filter="status.conditions[0].status=Unknown" \
  --format="value(name)")

if [ -z "$RUNNING" ]; then
  echo "✅ No jobs are currently running."
else
  echo "🚀 Found running executions:"
  gcloud run jobs executions list \
    --region=$REGION \
    --filter="status.conditions[0].status=Unknown" \
    --format="table(name,metadata.creationTimestamp,status.conditions[0].message)"
fi

