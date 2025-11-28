# CollabIQ Deployment Scripts

Utility scripts for deploying and managing CollabIQ on Google Cloud Run.

## Overview

These scripts automate common deployment tasks for running CollabIQ as a Cloud Run Job on Google Cloud Platform.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- Docker installed (for building images)
- Active Google Cloud project with required APIs enabled:
  - Cloud Run API
  - Artifact Registry API
  - Secret Manager API
- Appropriate IAM permissions for your account

## Scripts

### 1. `deploy.sh` - Build and Deploy

Builds the Docker image, pushes to Artifact Registry, and deploys/updates the Cloud Run Job.

**Usage:**
```bash
PROJECT_ID=my-project ./deploy.sh
PROJECT_ID=my-project IMAGE_TAG=v1.0.0 ./deploy.sh
```

**Environment Variables:**
- `PROJECT_ID` (required) - Google Cloud project ID
- `REGION` (optional, default: asia-northeast1) - GCP region
- `REPO_NAME` (optional, default: collabiq-repo) - Artifact Registry repository name
- `IMAGE_TAG` (optional, default: latest) - Docker image tag
- `JOB_NAME` (optional, default: collabiq-processor) - Cloud Run Job name
- `SERVICE_ACCOUNT` (optional) - Service account email for the job
- `MEMORY` (optional, default: 512Mi) - Memory allocation
- `CPU` (optional, default: 1) - CPU allocation
- `TIMEOUT` (optional, default: 3600) - Job timeout in seconds
- `MAX_RETRIES` (optional, default: 3) - Maximum retry attempts

**What it does:**
1. Validates environment and tools
2. Builds Docker image from project root
3. Pushes image to Artifact Registry
4. Creates or updates Cloud Run Job with specified configuration

### 2. `status.sh` - Check Job Status

Shows current job configuration, recent executions, and logs.

**Usage:**
```bash
PROJECT_ID=my-project ./status.sh
PROJECT_ID=my-project LOG_LINES=100 ./status.sh --verbose
```

**Environment Variables:**
- `PROJECT_ID` (required) - Google Cloud project ID
- `REGION` (optional, default: asia-northeast1) - GCP region
- `JOB_NAME` (optional, default: collabiq-processor) - Cloud Run Job name
- `LOG_LINES` (optional, default: 50) - Number of log lines to display

**Options:**
- `-v, --verbose` - Show detailed job configuration

**What it displays:**
1. Current job configuration (image, resources, timeout)
2. Last 10 executions with status
3. Latest execution details
4. Recent logs from Cloud Logging

### 3. `execute.sh` - Run the Job

Executes the Cloud Run Job with optional command arguments and log streaming.

**Usage:**
```bash
# Execute with default command (daemon start)
PROJECT_ID=my-project ./execute.sh

# Execute and follow logs
PROJECT_ID=my-project ./execute.sh --follow

# Execute with custom command
PROJECT_ID=my-project ./execute.sh -- process --batch-size 10

# Execute, wait, and follow logs
PROJECT_ID=my-project ./execute.sh --wait --follow -- daemon start --max-cycles 5
```

**Environment Variables:**
- `PROJECT_ID` (required) - Google Cloud project ID
- `REGION` (optional, default: asia-northeast1) - GCP region
- `JOB_NAME` (optional, default: collabiq-processor) - Cloud Run Job name

**Options:**
- `-f, --follow` - Stream logs in real-time after execution
- `-w, --wait` - Wait for execution to complete
- `--` - Separator before command arguments (passed to CollabIQ CLI)

**Default command:** `daemon start`

### 4. `delete.sh` - Delete Job Resources

Deletes the Cloud Run Job and associated Cloud Scheduler job. Use this before deploying to a new region.

**Usage:**
```bash
# Delete job from current region (default: asia-northeast1)
PROJECT_ID=my-project ./delete.sh

# Delete from specific region
PROJECT_ID=my-project REGION=us-central1 ./delete.sh

# Skip confirmation prompt
PROJECT_ID=my-project ./delete.sh --yes

# Delete only the scheduler job
PROJECT_ID=my-project ./delete.sh --scheduler-only

# Delete only the Cloud Run job
PROJECT_ID=my-project ./delete.sh --job-only
```

**Environment Variables:**
- `PROJECT_ID` (required) - Google Cloud project ID
- `REGION` (optional, default: asia-northeast1) - GCP region
- `JOB_NAME` (optional, default: collabiq-processor) - Cloud Run Job name

**Options:**
- `-y, --yes` - Skip confirmation prompt
- `--scheduler-only` - Only delete the Cloud Scheduler job
- `--job-only` - Only delete the Cloud Run job

**Important Notes:**
- You cannot have two Cloud Run jobs with the same name in different regions
- Delete the old job before creating in a new region
- Scheduler jobs are also region-specific

### 5. `secrets.sh` - Manage Secrets

Manages Google Cloud Secret Manager secrets for CollabIQ.

**Usage:**
```bash
# List all secrets
PROJECT_ID=my-project ./secrets.sh list

# Create/update secrets from .env file
PROJECT_ID=my-project ./secrets.sh create-from-env

# Create secret from credentials file
PROJECT_ID=my-project ./secrets.sh create-from-file credentials.json GMAIL_CREDENTIALS_JSON

# Grant service account access to secrets
PROJECT_ID=my-project SERVICE_ACCOUNT=sa@project.iam.gserviceaccount.com ./secrets.sh grant-access

# Show specific secret details
PROJECT_ID=my-project ./secrets.sh show NOTION_API_KEY
```

**Environment Variables:**
- `PROJECT_ID` (required) - Google Cloud project ID
- `REGION` (optional, default: asia-northeast1) - GCP region
- `SERVICE_ACCOUNT` (optional) - Service account email for grant-access command

**Commands:**
- `list` - List all secrets in the project
- `create-from-env` - Create/update secrets from .env file in project root
- `create-from-file <file> <secret-name>` - Create/update secret from file
- `grant-access` - Grant service account access to all secrets
- `show <secret-name>` - Show details of a specific secret

## Typical Workflow

### Initial Setup

1. **Create secrets from .env file:**
   ```bash
   PROJECT_ID=my-project ./secrets.sh create-from-env
   ```

2. **Create secrets from credential files:**
   ```bash
   PROJECT_ID=my-project ./secrets.sh create-from-file credentials.json GMAIL_CREDENTIALS_JSON
   PROJECT_ID=my-project ./secrets.sh create-from-file token.json GMAIL_TOKEN_JSON
   ```

3. **Grant service account access:**
   ```bash
   PROJECT_ID=my-project SERVICE_ACCOUNT=collabiq-runner@my-project.iam.gserviceaccount.com ./secrets.sh grant-access
   ```

4. **Deploy the job:**
   ```bash
   PROJECT_ID=my-project SERVICE_ACCOUNT=collabiq-runner@my-project.iam.gserviceaccount.com ./deploy.sh
   ```

### Regular Use

1. **Check current status:**
   ```bash
   PROJECT_ID=my-project ./status.sh
   ```

2. **Execute the job:**
   ```bash
   PROJECT_ID=my-project ./execute.sh --follow
   ```

3. **Deploy updates:**
   ```bash
   PROJECT_ID=my-project IMAGE_TAG=v1.1.0 ./deploy.sh
   ```

### Troubleshooting

1. **Check recent executions and logs:**
   ```bash
   PROJECT_ID=my-project ./status.sh --verbose
   ```

2. **Test with a custom command:**
   ```bash
   PROJECT_ID=my-project ./execute.sh --follow -- config validate
   ```

3. **Verify secrets:**
   ```bash
   PROJECT_ID=my-project ./secrets.sh list
   PROJECT_ID=my-project ./secrets.sh show NOTION_API_KEY
   ```

## Security Best Practices

1. **Never commit secrets** - Keep .env and credential files in .gitignore
2. **Use Secret Manager** - Store all sensitive data in Google Secret Manager
3. **Limit service account permissions** - Grant only necessary IAM roles
4. **Rotate secrets regularly** - Update secrets periodically using `create-from-env` or `create-from-file`
5. **Use specific image tags** - Avoid `:latest` in production, use version tags

## Common Issues

### Authentication Errors

**Problem:** `No active gcloud authentication`

**Solution:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Docker Push Failures

**Problem:** `Permission denied` when pushing to Artifact Registry

**Solution:**
```bash
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

### Job Execution Failures

**Problem:** Job fails immediately after execution

**Solution:**
1. Check logs: `PROJECT_ID=my-project ./status.sh`
2. Verify secrets are accessible: `PROJECT_ID=my-project ./secrets.sh list`
3. Test locally first: `uv run collabiq config validate`

### Secret Access Denied

**Problem:** Job can't access secrets

**Solution:**
```bash
# Grant access to the service account
PROJECT_ID=my-project SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com ./secrets.sh grant-access
```

## Additional Resources

- [Cloud Run Jobs Documentation](https://cloud.google.com/run/docs/create-jobs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [CollabIQ CLI Reference](../../docs/cli/CLI_REFERENCE.md)

## Support

For CollabIQ-specific issues, see the main project documentation in `/docs`.
For Google Cloud issues, consult the official GCP documentation or support channels.
