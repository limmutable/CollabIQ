#!/bin/bash
# Check the status of the Cloud Scheduler job and the triggered Cloud Run execution

REGION="asia-northeast1"
SCHEDULER_JOB="collabiq-scheduled"
RUN_JOB="collabiq-processor"

echo "========================================================"
echo " 🕒 Cloud Scheduler Status ($REGION)"
echo "========================================================"

# List scheduler jobs to see status and last attempt
gcloud scheduler jobs list --location=$REGION --filter="name:$SCHEDULER_JOB"

echo ""
echo "========================================================"
echo " 🚀 Latest Cloud Run Execution Triggered"
echo "========================================================"

# Get the most recent execution ID
LATEST_EXECUTION=$(gcloud run jobs executions list --job=$RUN_JOB --region=$REGION --limit=1 --sort-by="~creationTimestamp" --format="value(name)")

if [ -z "$LATEST_EXECUTION" ]; then
  echo "No executions found for job: $RUN_JOB"
else
  echo "Latest Execution ID: $LATEST_EXECUTION"
  
  # Get execution details
  gcloud run jobs executions describe $LATEST_EXECUTION --region=$REGION --format="table(status.completionTime,status.conditions[0].status,status.conditions[0].message)"

  echo ""
  echo "--- Recent Logs (Last 10 lines) ---"
  # Fetch recent logs for this execution
  gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$RUN_JOB AND labels.\"run.googleapis.com/execution_name\"=$LATEST_EXECUTION" \
    --limit=10 \
    --format="table(timestamp,jsonPayload.message,textPayload)"
fi
