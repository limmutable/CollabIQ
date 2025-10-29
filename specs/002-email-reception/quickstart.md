# Quickstart Guide: Email Reception and Normalization

**Feature**: `002-email-reception`
**Branch**: `002-email-reception`
**Created**: 2025-10-30
**Prerequisites**: Python 3.12, UV package manager, Google Cloud account

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Gmail API Setup](#gmail-api-setup)
4. [Local Development Setup](#local-development-setup)
5. [Running the Email Receiver](#running-the-email-receiver)
6. [Testing](#testing)
7. [Deployment (Cloud Run)](#deployment-cloud-run)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks you through setting up the Email Reception and Normalization feature, which:

1. **Receives emails** from `portfolioupdates@signite.co` using Gmail API with Cloud Pub/Sub webhooks
2. **Cleans emails** by removing signatures, quoted threads, and disclaimers
3. **Saves emails** to file storage for downstream LLM processing

**Estimated setup time**: 30-45 minutes

---

## Prerequisites

### Required Software

- **Python 3.12**: `python --version` should show 3.12.x
- **UV package manager**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Git**: For cloning and branch management
- **Google Cloud CLI** (`gcloud`): Install from https://cloud.google.com/sdk/docs/install

### Required Accounts

- **Google Cloud Account**: For Gmail API and Cloud Pub/Sub
- **Gmail account**: `portfolioupdates@signite.co` (or test account)

### Verify Prerequisites

```bash
# Check Python version
python --version  # Should be 3.12.x

# Check UV installation
uv --version

# Check gcloud CLI
gcloud --version

# Check current directory
pwd  # Should be /Users/jlim/Projects/CollabIQ
```

---

## Gmail API Setup

### Step 1: Enable Gmail API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project (e.g., `collabiq-project`)
3. Navigate to **APIs & Services > Library**
4. Search for "Gmail API" and click **Enable**
5. Search for "Cloud Pub/Sub API" and click **Enable**

### Step 2: Create OAuth2 Credentials

1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Application type: **Desktop app** (for local development) or **Web application** (for Cloud Run)
4. Name: `CollabIQ Email Receiver`
5. Click **Create**
6. Download credentials JSON file
7. Save as `/Users/jlim/Projects/CollabIQ/config/gmail_credentials.json`

**Important**: Add `config/gmail_credentials.json` to `.gitignore` (already done in project setup)

### Step 3: Create Cloud Pub/Sub Topic

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set project
gcloud config set project collabiq-project

# Create Pub/Sub topic for Gmail notifications
gcloud pubsub topics create gmail-notifications

# Grant Gmail permission to publish to topic
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher

# Verify topic was created
gcloud pubsub topics list
```

### Step 4: Configure Environment Variables

Add the following to `/Users/jlim/Projects/CollabIQ/.env`:

```bash
# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=/Users/jlim/Projects/CollabIQ/config/gmail_credentials.json
GMAIL_TOKEN_PATH=/Users/jlim/Projects/CollabIQ/config/gmail_token.json
GMAIL_PUBSUB_TOPIC=projects/collabiq-project/topics/gmail-notifications
GMAIL_INBOX_LABEL=INBOX
GMAIL_API_SCOPES=https://www.googleapis.com/auth/gmail.readonly

# Email Storage
EMAIL_STORAGE_PATH=/Users/jlim/Projects/CollabIQ/data
EMAIL_RETENTION_DAYS=90

# Logging
LOG_LEVEL=INFO
```

---

## Local Development Setup

### Step 1: Clone Repository and Switch to Feature Branch

```bash
cd /Users/jlim/Projects/CollabIQ

# Switch to email reception branch
git checkout 002-email-reception

# Verify branch
git branch --show-current  # Should show "002-email-reception"
```

### Step 2: Install Dependencies

```bash
# Install project dependencies using UV
uv sync

# Verify installation
uv run python -c "from google.oauth2.credentials import Credentials; print('Gmail API client installed')"
uv run python -c "from pydantic import BaseModel; print('Pydantic installed')"
```

### Step 3: Create Required Directories

```bash
# Create data directories
mkdir -p data/raw
mkdir -p data/cleaned
mkdir -p data/logs
mkdir -p data/metadata

# Create config directory if it doesn't exist
mkdir -p config

# Verify directory structure
tree data/ config/
```

### Step 4: Authenticate with Gmail API (First Time Only)

Run the OAuth2 flow to get access/refresh tokens:

```bash
uv run python -m src.email_receiver.gmail_receiver --authenticate
```

This will:
1. Open browser for Google login
2. Prompt you to authorize the app to read Gmail
3. Save `gmail_token.json` to `config/` directory
4. Print "Authentication successful!"

**Expected output**:
```
Please visit this URL to authorize this application:
https://accounts.google.com/o/oauth2/auth?...

Enter the authorization code: <paste code from browser>
Authentication successful! Token saved to config/gmail_token.json
```

---

## Running the Email Receiver

### Manual Email Fetch (Development)

Fetch emails manually for testing:

```bash
# Fetch all unprocessed emails
uv run python -m src.email_receiver.gmail_receiver --fetch

# Fetch emails since specific date
uv run python -m src.email_receiver.gmail_receiver --fetch --since 2025-10-29

# Fetch with max limit
uv run python -m src.email_receiver.gmail_receiver --fetch --max-emails 10
```

**Expected output**:
```
[2025-10-30 14:36:00] Fetching emails from portfolioupdates@signite.co...
[2025-10-30 14:36:01] Found 5 new emails
[2025-10-30 14:36:02] Saved: data/raw/2025/10/20251030_143622_CABc123.json
[2025-10-30 14:36:03] Saved: data/raw/2025/10/20251030_143623_CABc456.json
...
[2025-10-30 14:36:05] Successfully processed 5 emails
```

### Clean Emails with ContentNormalizer

Clean raw emails to remove noise:

```bash
# Clean all raw emails in data/raw/
uv run python -m src.content_normalizer.normalizer --clean-all

# Clean specific email
uv run python -m src.content_normalizer.normalizer --clean data/raw/2025/10/20251030_143622_CABc123.json
```

**Expected output**:
```
[2025-10-30 14:36:10] Cleaning email: 20251030_143622_CABc123.json
[2025-10-30 14:36:10] Removed: Signature (korean_thanks_name)
[2025-10-30 14:36:10] Removed: Quoted thread (angle_bracket_quotes)
[2025-10-30 14:36:10] Saved: data/cleaned/2025/10/20251030_143625_CABc123.json
[2025-10-30 14:36:10] Cleaning complete: 156 chars → 98 chars (37% removed)
```

### Full Pipeline (Fetch + Clean)

Run the complete email reception pipeline:

```bash
uv run python -m src.email_receiver.pipeline --run
```

This will:
1. Fetch new emails from Gmail
2. Skip duplicates using message ID tracking
3. Clean each email with ContentNormalizer
4. Save raw and cleaned emails to file storage
5. Log all activities to `data/logs/processing_log_YYYYMMDD.json`

---

## Testing

### Run Unit Tests

```bash
# Run all tests
make test

# Run specific test module
uv run pytest tests/unit/test_content_normalizer.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=term --cov-report=html
```

### Run Integration Tests

Integration tests require real Gmail API credentials:

```bash
# Gmail API integration tests
uv run pytest tests/integration/test_email_receiver_gmail.py -v

# End-to-end pipeline test
uv run pytest tests/integration/test_end_to_end_email.py -v
```

### Validate Success Criteria

Run accuracy tests to validate SC-002 and SC-003 (95%+ signature/quote removal):

```bash
# Signature removal accuracy test (requires 100 test emails)
uv run pytest tests/accuracy/test_signature_removal_accuracy.py -v

# Expected output:
# test_signature_removal_accuracy PASSED
# Accuracy: 97/100 (97%) ✅ (target: 95%)

# Quote removal accuracy test
uv run pytest tests/accuracy/test_quote_removal_accuracy.py -v
```

### Manual Spot Check

Manually verify cleaned emails:

```bash
# View raw email
cat data/raw/2025/10/20251030_143622_CABc123.json | jq '.body'

# View cleaned email
cat data/cleaned/2025/10/20251030_143625_CABc123.json | jq '.cleaned_body'

# Compare side-by-side
diff <(cat data/raw/2025/10/20251030_143622_CABc123.json | jq -r '.body') \
     <(cat data/cleaned/2025/10/20251030_143625_CABc123.json | jq -r '.cleaned_body')
```

---

## Deployment (Cloud Run)

### Step 1: Build Docker Image

```bash
# Build image
docker build -t gcr.io/collabiq-project/email-receiver:latest .

# Test locally
docker run -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -e GMAIL_CREDENTIALS_PATH=/app/config/gmail_credentials.json \
  -e GMAIL_TOKEN_PATH=/app/config/gmail_token.json \
  gcr.io/collabiq-project/email-receiver:latest
```

### Step 2: Push to Google Container Registry

```bash
# Authenticate Docker with GCR
gcloud auth configure-docker

# Push image
docker push gcr.io/collabiq-project/email-receiver:latest
```

### Step 3: Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy email-receiver \
  --image gcr.io/collabiq-project/email-receiver:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GMAIL_CREDENTIALS_PATH=/app/config/gmail_credentials.json \
  --set-env-vars GMAIL_TOKEN_PATH=/app/config/gmail_token.json \
  --set-env-vars GMAIL_PUBSUB_TOPIC=projects/collabiq-project/topics/gmail-notifications

# Get service URL
gcloud run services describe email-receiver --region us-central1 --format 'value(status.url)'
# Example output: https://email-receiver-abc123.run.app
```

### Step 4: Create Pub/Sub Push Subscription

```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe email-receiver --region us-central1 --format 'value(status.url)')

# Create push subscription
gcloud pubsub subscriptions create gmail-push-sub \
  --topic=gmail-notifications \
  --push-endpoint=${SERVICE_URL}/webhook/gmail \
  --push-auth-service-account=collabiq-webhook@collabiq-project.iam.gserviceaccount.com

# Verify subscription
gcloud pubsub subscriptions list
```

### Step 5: Set Up Gmail Watch (Renew Every 7 Days)

```bash
# Run watch setup script
uv run python -m src.email_receiver.setup_gmail_watch

# Expected output:
# Gmail watch request successful!
# Watch will expire at: 2025-11-06T14:36:00Z
# Set reminder to renew in 7 days
```

**Important**: Gmail watch expires after 7 days. Set up a cron job to renew:

```bash
# Add to crontab (runs every 6 days)
0 0 */6 * * cd /Users/jlim/Projects/CollabIQ && uv run python -m src.email_receiver.setup_gmail_watch
```

### Step 6: Verify Webhook Works

Send a test email to `portfolioupdates@signite.co` and check Cloud Run logs:

```bash
# Tail Cloud Run logs
gcloud run services logs tail email-receiver --region us-central1

# Expected output:
# [2025-10-30 14:36:00] Received Pub/Sub notification
# [2025-10-30 14:36:01] Fetching new emails...
# [2025-10-30 14:36:02] Processed 1 email
# [2025-10-30 14:36:03] Webhook response: 200 OK
```

---

## Troubleshooting

### Issue: "Invalid Credentials" Error

**Symptom**: `google.auth.exceptions.RefreshError: invalid_grant`

**Solution**:
1. Delete `config/gmail_token.json`
2. Re-run authentication: `uv run python -m src.email_receiver.gmail_receiver --authenticate`
3. Authorize app in browser again

### Issue: "Permission Denied" Writing to data/

**Symptom**: `PermissionError: [Errno 13] Permission denied: '/Users/jlim/Projects/CollabIQ/data/raw'`

**Solution**:
```bash
# Fix directory permissions
chmod -R 755 data/
chown -R $(whoami) data/
```

### Issue: Gmail API Rate Limit Exceeded

**Symptom**: `HttpError 429: Rate Limit Exceeded`

**Solution**:
- Wait 60 seconds and retry (exponential backoff will handle this automatically)
- Check quota usage: https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas
- Request quota increase if needed

### Issue: Webhook Not Triggering

**Symptom**: No emails received after sending test email

**Solution**:
1. Check Gmail watch status:
   ```bash
   uv run python -m src.email_receiver.check_watch_status
   ```
2. Verify Pub/Sub subscription is active:
   ```bash
   gcloud pubsub subscriptions describe gmail-push-sub
   ```
3. Check Cloud Run service is running:
   ```bash
   gcloud run services describe email-receiver --region us-central1
   ```
4. Test webhook manually:
   ```bash
   curl -X POST ${SERVICE_URL}/webhook/gmail \
     -H "Content-Type: application/json" \
     -d '{"message": {"data": ""}}'
   ```

### Issue: Signature Not Removed

**Symptom**: Cleaned email still contains signature text

**Solution**:
1. Check if signature matches known patterns:
   ```bash
   uv run python -c "
   from src.content_normalizer.patterns import load_signature_patterns
   patterns = load_signature_patterns()
   for p in patterns:
       print(f'{p.name}: {p.pattern.pattern}')
   "
   ```
2. If signature is non-standard, add custom pattern to `src/content_normalizer/patterns.py`
3. Re-run cleaning:
   ```bash
   uv run python -m src.content_normalizer.normalizer --clean <email_file>
   ```

### Issue: Cleaned Email is Empty (FR-012 Edge Case)

**Symptom**: `cleaned_body` is empty string, `is_empty=True`

**This is expected behavior** if the entire email was signature/disclaimer/quote. Check:

```bash
# View removal summary
cat data/cleaned/YYYYMMDD_HHMMSS_*.json | jq '.removed_content'

# Expected output:
{
  "signature_removed": true,
  "quoted_thread_removed": false,
  "disclaimer_removed": true,
  "original_length": 156,
  "cleaned_length": 0
}
```

**Action**: These emails should be flagged for manual review (handled in Phase 3b).

---

## Directory Structure Reference

```
CollabIQ/
├── config/
│   ├── gmail_credentials.json   # OAuth2 credentials (DO NOT COMMIT)
│   └── gmail_token.json          # Access/refresh tokens (DO NOT COMMIT)
│
├── data/
│   ├── raw/                      # Raw emails from Gmail
│   │   └── 2025/
│   │       └── 10/
│   │           └── 20251030_143622_CABc123.json
│   │
│   ├── cleaned/                  # Cleaned emails (signatures removed)
│   │   └── 2025/
│   │       └── 10/
│   │           └── 20251030_143625_CABc123.json
│   │
│   ├── logs/                     # Processing logs
│   │   └── processing_log_20251030.json
│   │
│   └── metadata/                 # Duplicate tracking
│       └── processed_ids.json
│
├── src/
│   ├── email_receiver/           # Email ingestion component
│   │   ├── __init__.py
│   │   ├── base.py              # EmailReceiver abstract interface
│   │   ├── gmail_receiver.py    # Gmail API implementation
│   │   └── setup_gmail_watch.py # Gmail watch setup script
│   │
│   ├── content_normalizer/       # Email cleaning component
│   │   ├── __init__.py
│   │   ├── normalizer.py        # ContentNormalizer main class
│   │   ├── patterns.py          # Signature/disclaimer/quote patterns
│   │   └── utils.py             # Helper functions
│   │
│   └── models/                   # Data models
│       ├── __init__.py
│       ├── raw_email.py         # RawEmail Pydantic model
│       └── cleaned_email.py     # CleanedEmail Pydantic model
│
└── tests/
    ├── unit/                     # Unit tests
    ├── integration/              # Integration tests
    └── accuracy/                 # Accuracy validation tests
```

---

## Next Steps

After completing this quickstart:

1. **Verify Success Criteria**:
   - Run accuracy tests to confirm SC-002 and SC-003 (95%+ removal accuracy)
   - Send 10 test emails and verify 90%+ are retrieved within 5 minutes (SC-001)

2. **Monitor Performance**:
   - Check `data/logs/processing_log_YYYYMMDD.json` for errors
   - Verify average processing time < 12 seconds/email (SC-006)

3. **Proceed to Phase 1b** (Gemini Extraction):
   - Cleaned emails in `data/cleaned/` are ready for LLM processing
   - See `docs/architecture/IMPLEMENTATION_ROADMAP.md` Phase 1b

4. **Set Up Production Monitoring**:
   - Configure Cloud Logging for error alerts
   - Set up uptime checks for Cloud Run webhook
   - Create dashboard for email ingestion metrics

---

## Additional Resources

- **Gmail API Documentation**: https://developers.google.com/gmail/api
- **Cloud Pub/Sub Documentation**: https://cloud.google.com/pubsub/docs
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **CollabIQ Architecture**: [docs/architecture/ARCHITECTURE.md](../../../docs/architecture/ARCHITECTURE.md)
- **API Contracts**: [contracts/](contracts/)
- **Data Models**: [data-model.md](data-model.md)

---

**Document Status**: Complete - Ready for development
