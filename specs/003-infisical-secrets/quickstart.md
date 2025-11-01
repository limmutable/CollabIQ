# Quickstart Guide: Infisical Secret Management Integration

**Feature**: 003-infisical-secrets
**Date**: 2025-11-01
**Audience**: Developers setting up CollabIQ with Infisical

## Overview

This guide walks you through setting up Infisical secret management for CollabIQ in under 15 minutes. After completion, all API credentials (Gmail, Gemini, Notion) will be securely retrieved from Infisical instead of local .env files.

**Time Estimate**: 10-15 minutes

---

## Prerequisites

Before starting, ensure you have:

- [ ] CollabIQ repository cloned locally
- [ ] Python 3.12+ installed
- [ ] UV package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] Active Infisical Cloud account (free tier: https://app.infisical.com/signup)
- [ ] Admin access to Infisical project (to create machine identities)

---

## Step 1: Create Infisical Project (5 minutes)

### 1.1 Sign Up / Log In to Infisical

1. Go to https://app.infisical.com
2. Sign up (if new user) or log in
3. Verify email address

### 1.2 Create Project

1. Click "Create Project" button
2. Project name: `CollabIQ`
3. Click "Create"
4. **Save the Project ID** (visible in URL: `app.infisical.com/project/{PROJECT_ID}`)

### 1.3 Create Environments

Infisical projects come with default environments. Verify these exist:

- `dev` (Development)
- `staging` (Staging)
- `prod` (Production)

If missing, create them via Project Settings → Environments.

---

## Step 2: Add Secrets to Infisical (3 minutes)

### 2.1 Navigate to Secrets

1. Select `CollabIQ` project
2. Choose `dev` environment from dropdown
3. Click "Secrets" tab

### 2.2 Add API Credentials

Add these three secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GMAIL_CREDENTIALS_PATH` | Path to Gmail OAuth credentials | `credentials.json` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSyD...` |
| `NOTION_API_KEY` | Notion integration token | `secret_ntn...` |

**For each secret**:
1. Click "+ Add Secret"
2. Key: Enter secret name (e.g., `GMAIL_CREDENTIALS_PATH`)
3. Value: Enter secret value
4. Click "Add"

### 2.3 Repeat for Staging/Prod

Repeat Step 2.2 for `staging` and `prod` environments with environment-specific values.

**Important**: Use different API keys for each environment to prevent accidental production access from development.

---

## Step 3: Create Machine Identity (4 minutes)

### 3.1 Navigate to Machine Identities

1. Go to Project Settings (gear icon)
2. Click "Machine Identities" tab
3. Click "+ Create Identity"

### 3.2 Create Dev Machine Identity

1. Name: `collabiq-dev`
2. Description: "Development environment machine identity"
3. Click "Create"

### 3.3 Configure Permissions

1. Click on newly created `collabiq-dev` identity
2. Go to "Permissions" tab
3. Add permission:
   - Environment: `dev`
   - Access Level: `Read`
4. Click "Save"

### 3.4 Generate Universal Auth Credentials

1. Go to "Authentication" tab
2. Click "Universal Auth"
3. Click "Generate Credentials"
4. **Copy and save immediately**:
   - Client ID: `machine-identity-abc123...`
   - Client Secret: `secret-xyz789...` (shown only once!)

**Critical**: Store these securely - client secret cannot be retrieved later.

### 3.5 Repeat for Staging/Prod (Optional)

For production deployments, create separate machine identities:
- `collabiq-staging` (read access to `staging` environment)
- `collabiq-prod` (read access to `prod` environment)

---

## Step 4: Install Infisical SDK (1 minute)

### 4.1 Add Dependency

```bash
cd /path/to/CollabIQ
uv add infisicalsdk
```

### 4.2 Verify Installation

```bash
uv run python -c "import infisical_sdk; print('✅ Infisical SDK installed')"
```

Expected output:
```
✅ Infisical SDK installed
```

---

## Step 5: Configure Environment Variables (2 minutes)

### 5.1 Update .env File

Edit `.env` file in project root:

```bash
# Infisical Configuration
INFISICAL_ENABLED=true
INFISICAL_HOST=https://app.infisical.com
INFISICAL_PROJECT_ID=your-project-id-here  # From Step 1.2
INFISICAL_ENVIRONMENT=dev  # or staging, prod
INFISICAL_CLIENT_ID=machine-identity-abc123...  # From Step 3.4
INFISICAL_CLIENT_SECRET=secret-xyz789...  # From Step 3.4
INFISICAL_CACHE_TTL=60  # Optional: cache duration in seconds (default: 60)

# Fallback credentials (optional, for offline development)
# GMAIL_CREDENTIALS_PATH=credentials.json
# GEMINI_API_KEY=fallback-key
# NOTION_API_KEY=fallback-key
```

### 5.2 Update .env.example

Add Infisical configuration template (without actual secrets):

```bash
# .env.example
INFISICAL_ENABLED=false  # Set to true to enable Infisical
INFISICAL_HOST=https://app.infisical.com
INFISICAL_PROJECT_ID=your-project-id-here
INFISICAL_ENVIRONMENT=dev
INFISICAL_CLIENT_ID=your-client-id-here
INFISICAL_CLIENT_SECRET=your-client-secret-here
INFISICAL_CACHE_TTL=60
```

---

## Step 6: Verify Integration (1 minute)

### 6.1 Run Verification Command

```bash
uv run collabiq verify-infisical
```

Expected output:
```
✅ Infisical configuration valid
✅ Authentication successful
✅ Connected to Infisical (https://app.infisical.com)
✅ Retrieved 3 secrets from environment 'dev'
✅ All secrets loaded successfully

Secrets found:
  - GMAIL_CREDENTIALS_PATH (source: infisical)
  - GEMINI_API_KEY (source: infisical)
  - NOTION_API_KEY (source: infisical)
```

### 6.2 Test Application Startup

```bash
uv run collabiq --help
```

If application starts without errors, Infisical integration is working!

---

## Step 7: Test Secret Retrieval (Optional)

### 7.1 Interactive Python Shell

```bash
uv run python
```

```python
>>> from src.config.settings import get_settings
>>> settings = get_settings()
>>> print(settings.gmail_credentials_path)
credentials.json  # Retrieved from Infisical!
```

### 7.2 Check Logs

```bash
tail -f data/logs/collabiq.log
```

Look for:
```
INFO | Retrieved GMAIL_CREDENTIALS_PATH from infisical
INFO | Retrieved GEMINI_API_KEY from cache
```

---

## Environment Setup

### Development Environment

```bash
# .env
INFISICAL_ENVIRONMENT=dev
INFISICAL_CLIENT_ID=dev-machine-identity-id
INFISICAL_CLIENT_SECRET=dev-machine-identity-secret
```

Use dev secrets only. Cannot access staging or prod secrets with this configuration.

### Staging Environment

```bash
# .env
INFISICAL_ENVIRONMENT=staging
INFISICAL_CLIENT_ID=staging-machine-identity-id
INFISICAL_CLIENT_SECRET=staging-machine-identity-secret
```

Separate machine identity with read access to `staging` environment only.

### Production Environment

```bash
# Cloud Run environment variables (via Secret Manager)
INFISICAL_ENVIRONMENT=prod
INFISICAL_CLIENT_ID=prod-machine-identity-id
INFISICAL_CLIENT_SECRET=prod-machine-identity-secret
```

**Never commit production credentials** - use Cloud Run secret injection.

---

## Cache TTL Configuration & Secret Rotation

### Understanding Cache TTL

The `INFISICAL_CACHE_TTL` parameter controls how long secrets are cached in memory before being refreshed from Infisical. This directly impacts how quickly rotated secrets are picked up by your application.

**Default Value**: 60 seconds
**Range**: 0-3600 seconds (0 = no caching, 3600 = 1 hour)

### How Caching Works

1. **First Access**: Secret fetched from Infisical API → Stored in cache with timestamp
2. **Subsequent Access (within TTL)**: Secret retrieved from cache (< 10ms, no API call)
3. **After TTL Expires**: Secret refetched from Infisical API → Cache updated with new value
4. **API Unreachable**: Falls back to stale cached value (graceful degradation)

### Secret Rotation Timeline

When you rotate a secret in Infisical (e.g., update `GEMINI_API_KEY`):

```
Time 0s:   Admin updates secret in Infisical dashboard
Time 0-60s: Running instances still use old cached value
Time 60s+:  Cache expires, instances fetch new value on next access
Time 61s:   All instances now using new secret value
```

**No restart required** - rotation happens automatically!

### Configuration Examples

#### Fast Rotation (Development)
```bash
INFISICAL_CACHE_TTL=10  # Secrets refresh every 10 seconds
```
- **Pros**: Near-instant secret rotation detection
- **Cons**: More API calls, higher latency (100-300ms every 10s)
- **Use Case**: Development, testing secret rotation

#### Balanced (Default)
```bash
INFISICAL_CACHE_TTL=60  # Secrets refresh every 60 seconds
```
- **Pros**: Good balance of performance and rotation speed
- **Cons**: Up to 1-minute delay for secret rotation
- **Use Case**: Production, staging environments

#### Long-Lived Cache (High Performance)
```bash
INFISICAL_CACHE_TTL=300  # Secrets refresh every 5 minutes
```
- **Pros**: Minimal API calls, lowest latency (cache hits)
- **Cons**: Up to 5-minute delay for secret rotation
- **Use Case**: Production with infrequent secret rotation

#### No Caching (Always Fresh)
```bash
INFISICAL_CACHE_TTL=0  # No caching, always fetch from API
```
- **Pros**: Instant secret rotation detection
- **Cons**: High latency (100-300ms per secret access), more API calls
- **Use Case**: Critical systems requiring immediate rotation

### Cache Refresh Logs

Monitor cache refresh behavior in application logs:

```bash
# First access (cache miss)
INFO | ✓ Retrieved 'GEMINI_API_KEY' from Infisical API (first fetch)

# Cached access (within TTL)
DEBUG | ✓ Retrieved 'GEMINI_API_KEY' from cache (age: 25s)

# Cache expiration + refresh
INFO | Cache expired for 'GEMINI_API_KEY' (TTL: 60s) - refreshing from Infisical
INFO | ✓ Cache refreshed for 'GEMINI_API_KEY' from Infisical API

# Bulk cache refresh (get_all_secrets)
INFO | Fetching all secrets from Infisical (environment: development)
INFO | ✓ Cache refreshed with 3 secrets from Infisical (TTL: 60s)
```

### Best Practices

**Development**:
- Use `INFISICAL_CACHE_TTL=30` for faster iteration
- Test secret rotation by updating secrets in Infisical and waiting 30s

**Staging**:
- Use `INFISICAL_CACHE_TTL=60` (default) for production-like behavior
- Validate rotation timing matches production

**Production**:
- Use `INFISICAL_CACHE_TTL=60-120` for balance
- Consider `INFISICAL_CACHE_TTL=300` for high-traffic applications with stable secrets
- Never use `INFISICAL_CACHE_TTL=0` in production (performance impact)

### Testing Secret Rotation

1. **Set short TTL** for testing:
   ```bash
   INFISICAL_CACHE_TTL=10  # 10 seconds for faster testing
   ```

2. **Start application and access a secret**:
   ```bash
   uv run collabiq fetch
   # Check logs: "✓ Retrieved 'GEMINI_API_KEY' from Infisical API (first fetch)"
   ```

3. **Update secret in Infisical dashboard**:
   - Go to Infisical → CollabIQ project → development environment
   - Edit `GEMINI_API_KEY` value
   - Save changes

4. **Wait for cache to expire** (10 seconds in this example)

5. **Access secret again**:
   ```bash
   uv run collabiq fetch
   # Check logs: "Cache expired for 'GEMINI_API_KEY' (TTL: 10s) - refreshing from Infisical"
   # Check logs: "✓ Cache refreshed for 'GEMINI_API_KEY' from Infisical API"
   ```

6. **Verify new value is used** - application now using rotated secret!

---

## Troubleshooting

### Error: "Authentication failed: Invalid client ID or secret"

**Cause**: Incorrect INFISICAL_CLIENT_ID or INFISICAL_CLIENT_SECRET

**Solution**:
1. Verify client ID/secret copied correctly from Infisical dashboard
2. Regenerate credentials if lost (Settings → Machine Identities → collabiq-dev → Authentication → Generate New)
3. Check for trailing whitespace in .env file

---

### Error: "Secret GMAIL_CREDENTIALS_PATH not found"

**Cause**: Secret not added to Infisical project

**Solution**:
1. Go to Infisical dashboard
2. Select `CollabIQ` project
3. Select correct environment (`dev`, `staging`, or `prod`)
4. Click "Secrets" tab
5. Add missing secret with "+ Add Secret" button

---

### Error: "Cannot connect to Infisical at https://app.infisical.com"

**Cause**: Network connectivity issue

**Solution**:
1. Check internet connection: `ping app.infisical.com`
2. Verify firewall/proxy settings
3. Temporary workaround: Set `INFISICAL_ENABLED=false` and use .env fallback

---

### Warning: "Using stale cached value for GMAIL_CREDENTIALS_PATH"

**Cause**: Infisical API temporarily unreachable, using expired cache

**Impact**: Low (stale secrets still work)

**Solution**:
1. Wait for network connectivity to restore
2. Cache will auto-refresh on next access
3. Or manually refresh: `uv run python -c "from src.config.infisical_client import client; client.refresh_cache()"`

---

### Application starts but uses .env fallback

**Symptom**: Logs show "Retrieved X from env_file"

**Cause**: Infisical integration disabled or failed

**Solution**:
1. Verify `INFISICAL_ENABLED=true` in .env
2. Check logs for authentication errors: `tail -f data/logs/collabiq.log`
3. Run `uv run collabiq verify-infisical` for detailed diagnostics

---

## Disabling Infisical (Fallback Mode)

### Temporary Disable

```bash
# .env
INFISICAL_ENABLED=false
```

Application falls back to .env file values immediately.

### Permanent Disable

1. Set `INFISICAL_ENABLED=false`
2. Ensure all secrets present in .env:
   ```bash
   GMAIL_CREDENTIALS_PATH=credentials.json
   GEMINI_API_KEY=your-gemini-key
   NOTION_API_KEY=your-notion-key
   ```

---

## Best Practices

### ✅ Do

- Use separate machine identities per environment (dev, staging, prod)
- Rotate machine identity credentials quarterly
- Keep `INFISICAL_ENABLED=false` in `.env.example` (developers opt-in)
- Use .env fallback for offline development
- Monitor logs for fallback usage (indicates Infisical issues)

### ❌ Don't

- Commit `INFISICAL_CLIENT_SECRET` to version control (add .env to .gitignore)
- Use prod machine identity in development environment
- Disable caching in production (`INFISICAL_CACHE_TTL=0` increases latency)
- Share machine identity credentials via Slack/email
- Log secret values (already prevented by InfisicalClient)

---

## Next Steps

After completing this quickstart:

1. **Test secret rotation**: Update a secret in Infisical, verify app picks up new value after cache TTL
2. **Setup staging environment**: Repeat Steps 1-6 for staging environment
3. **Configure CI/CD**: Add Infisical credentials to GitHub Actions secrets
4. **Monitor logs**: Watch for fallback usage and authentication errors
5. **Document team process**: Share this guide with team members

---

## Additional Resources

- [Infisical Documentation](https://infisical.com/docs)
- [Python SDK Reference](https://infisical.com/docs/sdks/languages/python)
- [Feature Specification](spec.md)
- [API Contract](contracts/infisical_client.yaml)
- [Data Model](data-model.md)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-01
**Estimated Setup Time**: 10-15 minutes
