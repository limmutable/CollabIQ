# Infisical Setup Guide

Quick guide to configure Infisical for CollabIQ project.

## Prerequisites

✅ Infisical project "CollabIQ" created with two environments:
- **development** (for local development and testing)
- **production** (for production deployment)

## Step 1: Create Machine Identity

1. Go to your Infisical project: https://app.infisical.com
2. Navigate to **Settings → Machine Identities**
3. Click **"Create Identity"**
4. Configure the identity:
   - **Name**: `collabiq-dev-machine` (or `collabiq-prod-machine` for production)
   - **Type**: Universal Auth
   - Click **"Create"**
5. **Save the credentials** (you'll need these for .env):
   - `Client ID` → Use for `INFISICAL_CLIENT_ID`
   - `Client Secret` → Use for `INFISICAL_CLIENT_SECRET`

## Step 2: Grant Environment Access

1. In Machine Identities, click on your newly created identity
2. Go to **Access** tab
3. Click **"Grant Access"**
4. Configure access:
   - **Environment**: `development` (or `production`)
   - **Secret Path**: `/` (root path)
   - **Permissions**: Read (minimum required)
5. Click **"Add"**

**Important**: Development machine identity should ONLY have access to `development` environment, NOT production.

## Step 3: Add Secrets to Infisical

Navigate to your project's secrets page and add the following secrets:

### Required Secrets

| Secret Key | Description | Example Value |
|------------|-------------|---------------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSyD...` |
| `NOTION_API_KEY` | Notion integration token | `secret_ntn...` |
| `GMAIL_CREDENTIALS_PATH` | Path to Gmail credentials | `credentials.json` |
| `GMAIL_TOKEN_PATH` | Path to Gmail token | `token.json` |

### Optional Secrets

| Secret Key | Description | Default Value |
|------------|-------------|---------------|
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` |
| `LOG_LEVEL` | Logging level | `INFO` |

**Note**: Add these secrets to BOTH `development` and `production` environments with appropriate values for each.

## Step 4: Configure Local Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure Infisical:
   ```bash
   # Enable Infisical
   INFISICAL_ENABLED=true

   # Infisical host (keep default for cloud)
   INFISICAL_HOST=https://app.infisical.com

   # Project ID (from Infisical dashboard URL)
   INFISICAL_PROJECT_ID=your-project-id-here

   # Environment (development or production)
   INFISICAL_ENVIRONMENT=development

   # Machine Identity credentials (from Step 1)
   INFISICAL_CLIENT_ID=your-client-id-here
   INFISICAL_CLIENT_SECRET=your-client-secret-here

   # Cache TTL (optional, default: 60 seconds)
   INFISICAL_CACHE_TTL=60
   ```

3. **Get your Project ID**:
   - Go to Infisical dashboard
   - Your project URL looks like: `https://app.infisical.com/project/[PROJECT_ID]/...`
   - Copy the `[PROJECT_ID]` part

## Step 5: Test Connection

Run the validation script to verify everything is working:

```bash
uv run python scripts/validate_infisical.py
```

Expected output:
```
======================================================================
  Test 1: Configuration Validation
======================================================================

✓ Settings loaded successfully
  - Infisical Enabled: True
  - Infisical Host: https://app.infisical.com
  - Project ID: 6abc1234def5...
  - Environment: development
  - Cache TTL: 60s
  - Client ID: 1a2b3c4d5e6f7g8h9i0j...
  - Client Secret: ********************...

✓ All required configuration fields present

======================================================================
  Test 2: Authentication
======================================================================

✓ Successfully authenticated with Infisical
  - SDK Client: InfisicalSDKClient

======================================================================
  Test 3: List All Secrets
======================================================================

✓ Retrieved 4 secrets from Infisical:

  - GEMINI_API_KEY: AIzaSyD1234567890...
  - GMAIL_CREDENTIALS_PATH: credentials.json
  - NOTION_API_KEY: secret_ntn1234567890...
  - GMAIL_TOKEN_PATH: token.json

======================================================================
  ✅ ALL TESTS PASSED
======================================================================
```

## Step 6: Use Secrets in Your Code

Replace direct environment variable access with Infisical-aware method:

### Before (direct .env access):
```python
import os
api_key = os.getenv("GEMINI_API_KEY")
```

### After (Infisical with fallback):
```python
from config.settings import get_settings

settings = get_settings()
api_key = settings.get_secret_or_env("GEMINI_API_KEY")
```

**Benefits**:
- Automatically retrieves from Infisical if enabled
- Falls back to .env if Infisical is disabled or unreachable
- Caches secrets for 60 seconds (configurable)
- No code changes needed to switch between Infisical and .env

## Troubleshooting

### Error: "Invalid client credentials"

**Cause**: Wrong `INFISICAL_CLIENT_ID` or `INFISICAL_CLIENT_SECRET`

**Fix**:
1. Go to Infisical → Settings → Machine Identities
2. Delete the old identity
3. Create a new one and update `.env` with new credentials

### Error: "Secret not found"

**Cause**: Secret doesn't exist in Infisical for the current environment

**Fix**:
1. Go to Infisical → Secrets → Select environment (development/production)
2. Click **"Add Secret"**
3. Add the missing secret key and value

### Error: "Invalid environment"

**Cause**: `INFISICAL_ENVIRONMENT` is not "development" or "production"

**Fix**: Update `.env` to use either `development` or `production`

### Warning: "Infisical disabled, falling back to .env"

**Cause**: `INFISICAL_ENABLED=false` in `.env`

**Fix**: Set `INFISICAL_ENABLED=true` in `.env`

## Security Best Practices

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Use separate machine identities** for development and production
3. **Grant minimal permissions** - Only "Read" permission on specific paths
4. **Rotate credentials regularly** - Update machine identity credentials quarterly
5. **Monitor access logs** - Review Infisical audit logs for unauthorized access
6. **Use different secrets** for development and production environments

## Environment Setup Summary

### Development Environment
- Machine Identity: `collabiq-dev-machine`
- Access: `development` environment only
- Secrets: Non-production API keys, test credentials
- `.env`: `INFISICAL_ENVIRONMENT=development`

### Production Environment
- Machine Identity: `collabiq-prod-machine`
- Access: `production` environment only
- Secrets: Production API keys, real credentials
- `.env`: `INFISICAL_ENVIRONMENT=production`

## Additional Resources

- [Infisical Documentation](https://infisical.com/docs)
- [Universal Auth Guide](https://infisical.com/docs/documentation/platform/identities/universal-auth)
- [Python SDK Documentation](https://infisical.com/docs/sdks/languages/python)
- [CollabIQ Infisical Architecture](../architecture/TECHSTACK.md#infisical)
