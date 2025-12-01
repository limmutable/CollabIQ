# Quickstart: Gmail API Setup for CollabIQ

**Feature**: 005-gmail-setup
**Estimated Time**: 15 minutes
**Prerequisites**: Google Workspace admin access, CollabIQ repository cloned

This guide walks you through setting up Gmail API access for the collab@signite.co group alias.

---

## Overview

CollabIQ needs to access emails sent to **collab@signite.co** (a Google Workspace group alias) to extract entity information. Since group aliases are not standalone accounts, you'll authenticate as a group member and use API queries to filter group emails.

**⚠️ CRITICAL: collab@signite.co is a Google Group, NOT a regular mailbox**
- **You CANNOT authenticate as collab@signite.co directly**
- **You MUST authenticate as a member account** (e.g., jeffreylim@signite.co, gloriakim@signite.co)
- **Use Gmail query `to:collab@signite.co`** to retrieve emails sent to the group
- The authenticated member account must be a member of the collab@signite.co Google Group
- Do NOT try to "login as collab@signite.co" - it will fail

**What you'll do**:
1. Create OAuth2 credentials in Google Cloud Console
2. Configure credentials locally
3. Complete first-time authentication **as a group member account**
4. Verify email retrieval using `to:collab@signite.co` query

---

## Part 1: Google Cloud Console Setup (5-8 minutes)

### Step 1.1: Create or Select Google Cloud Project

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google Workspace admin account
3. Either:
   - **Create new project**: Click "Select a project" → "New Project" → Name it "CollabIQ Production" → Create
   - **Use existing project**: Select your existing project from the dropdown

**Expected Result**: You see your project name in the top navigation bar

---

### Step 1.2: Enable Gmail API

1. In Google Cloud Console, navigate to **APIs & Services → Library**
2. Search for "Gmail API"
3. Click "Gmail API" from search results
4. Click **Enable** button
5. Wait for API to be enabled (10-30 seconds)

**Expected Result**: You see "API enabled" confirmation message

---

### Step 1.3: Configure OAuth Consent Screen

1. Navigate to **APIs & Services → OAuth consent screen**
2. Select **User type**:
   - Choose "Internal" if using Google Workspace (recommended)
   - Choose "External" if not using Google Workspace
3. Click **Create**
4. Fill in required fields:
   - **App name**: `CollabIQ Email Receiver`
   - **User support email**: Your admin email
   - **Developer contact email**: Your admin email
5. Click **Save and Continue**
6. On "Scopes" page, click **Add or Remove Scopes**
7. Filter for `gmail.readonly` and select:
   - `https://www.googleapis.com/auth/gmail.readonly`
8. Click **Update** → **Save and Continue**
9. On "Test users" page (if External):
   - Click **Add Users**
   - Add the email address of the group member you'll authenticate with
   - Click **Save and Continue**
10. Click **Back to Dashboard**

**Expected Result**: OAuth consent screen is configured with `gmail.readonly` scope

---

### Step 1.4: Create OAuth2 Desktop Application Credentials

1. Navigate to **APIs & Services → Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Select **Application type**: "Desktop app"
4. **Name**: `CollabIQ Gmail Receiver`
5. Click **Create**
6. **Download credentials**:
   - Click "Download JSON" button in the popup
   - Save as `credentials.json` (remember this location)
7. Click **OK** to close popup

**Expected Result**: You have `credentials.json` file downloaded

**Security Note**: The credentials.json file contains a client secret, but for Desktop OAuth applications, this is not truly secret (it's embedded in the application). Google's security model accepts this for desktop apps.

---

## Part 2: Local Configuration (3-5 minutes)

### Step 2.1: Store Credentials File

**Recommended: Store in project root directory** (simplest for local development):

```bash
# Move the downloaded credentials file to your CollabIQ project root
cd /Users/jlim/Projects/CollabIQ
mv ~/Downloads/client_secret_*.json ./credentials.json

# Verify it's there and set permissions
ls -la credentials.json
chmod 600 credentials.json
```

**Note**: The file `credentials.json` is already in `.gitignore`, so it won't be committed to version control.

---

### Step 2.2: Configure Environment Variables

**Option A: Using .env file** (recommended for local development):

1. Create or edit `.env` file in CollabIQ root directory:
   ```bash
   cd /Users/jlim/Projects/CollabIQ
   touch .env
   ```

2. Add the following line (since you stored credentials.json in the project root, you can use the relative path):
   ```bash
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

   **Note**: The default value in settings.py is already `credentials.json`, so if you stored it in the project root, you don't even need to add this to `.env`. It will work automatically!

3. Verify `.env` is in `.gitignore`:
   ```bash
   grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
   ```

**Option B: Using Infisical** (recommended for production):

1. Ensure Infisical is configured (from Phase 003):
   ```bash
   infisical login
   ```

2. Add secret to Infisical:
   ```bash
   infisical secrets set GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   ```

---

### Step 2.3: Verify .gitignore Configuration

Ensure sensitive files are excluded from version control:

```bash
cd /path/to/CollabIQ
grep -qxF 'credentials.json' .gitignore || echo 'credentials.json' >> .gitignore
grep -qxF 'token.json' .gitignore || echo 'token.json' >> .gitignore
```

**Expected Result**: Both `credentials.json` and `token.json` are in `.gitignore`

---

## Part 3: First-Time Authentication (2-3 minutes)

### Step 3.1: Run Gmail Authentication Script

1. Navigate to CollabIQ directory:
   ```bash
   cd /Users/jlim/Projects/CollabIQ
   ```

2. Run the authentication script (this will trigger OAuth flow):
   ```bash
   uv run python scripts/setup/authenticate_gmail.py
   ```

**Expected Behavior**:
- Script confirms it found your credentials.json file
- Application opens a browser window automatically
- You see Google sign-in page

---

### Step 3.2: Complete Google Sign-In

1. **Select Google Account**:
   - Choose a Google Workspace account that is a **member of collab@signite.co group**
   - This is critical: you cannot authenticate as the group alias itself

2. **Review Permissions**:
   - Google shows "CollabIQ Email Receiver wants to access your Google Account"
   - Review requested scope: "Read, compose, send, and permanently delete all your email from Gmail"
   - (Note: Despite the wording, the app only has read-only access due to `gmail.readonly` scope)

3. **Grant Access**:
   - Click **Continue** or **Allow**

4. **Browser Redirect**:
   - Browser shows "The authentication flow has completed. You may close this window."
   - Return to terminal

**Expected Result**: Terminal shows "Authentication successful" or similar message

---

### Step 3.3: Verify Token Storage

1. Check that `token.json` was created:
   ```bash
   ls -la token.json
   ```

2. Verify file permissions (should be `-rw-------` or similar):
   ```bash
   stat -f "%Sp %N" token.json  # macOS
   # OR
   stat -c "%A %n" token.json   # Linux
   ```

**Expected Result**: `token.json` exists with restricted permissions (owner read/write only)

---

## Part 4: Validation (2-3 minutes)

### Step 4.1: Test Email Retrieval

Run the Gmail receiver to verify it can access collab@signite.co emails:

```bash
# Default query: to:collab@signite.co
uv run python tests/manual/test_gmail_retrieval.py --max-results 5

# Custom query (e.g., with subject filter)
uv run python tests/manual/test_gmail_retrieval.py --query 'to:collab@signite.co subject:"Test"' --max-results 5
```

**Expected Output**:
- List of recent emails sent to collab@signite.co (shows message ID, sender, subject, date)
- No authentication errors

**⚠️ CRITICAL: Always Use `to:collab@signite.co` Query Filter**

**Why this matters**:
- The authenticated account (e.g., jeffreylim@signite.co) receives ALL personal emails
- Without filtering, you'll retrieve personal inbox emails instead of group emails
- The `to:collab@signite.co` filter ensures you only get emails sent to the group

**Query Operator Best Practices**:
- ✅ **ALWAYS use**: `to:collab@signite.co` to find emails sent to the group alias
- ✅ **Combine with date filters**: `to:collab@signite.co after:2025/11/01`
- ✅ **Combine with subject filters**: `to:collab@signite.co subject:"협업"`
- ❌ **Do NOT use**: `deliveredto:` operator - it doesn't work reliably with Gmail API
- ❌ **Do NOT use**: `in:inbox` filter alone - group-forwarded emails may not retain inbox label
- ❌ **Do NOT query without `to:collab@signite.co`** - will return personal emails!

---

### Step 4.2: Run Integration Tests

Run the test suite to verify Gmail integration:

```bash
pytest tests/integration/test_gmail_receiver.py -v
```

**Expected Result**: All tests pass (100% pass rate)

---

### Step 4.3: Verify Group Email Filtering

Send a test email to collab@signite.co and verify retrieval:

1. Send test email:
   ```bash
   # From another email account
   Subject: Test CollabIQ Setup
   To: collab@signite.co
   Body: This is a test email for CollabIQ Gmail integration.
   ```

2. Wait 1-2 minutes for Gmail indexing

3. Run retrieval:
   ```bash
   uv run python tests/manual/test_gmail_retrieval.py --query 'deliveredto:"collab@signite.co" subject:"Test CollabIQ Setup"'
   ```

**Expected Result**: Test email appears in results, showing sender, subject, date, and recipients

---

## Troubleshooting

### Error: "Credentials file not found"

**Symptom**: `FileNotFoundError: credentials.json not found`

**Solutions**:
1. Verify `GOOGLE_CREDENTIALS_PATH` environment variable is set correctly:
   ```bash
   echo $GOOGLE_CREDENTIALS_PATH
   ```
2. Check file exists at specified path:
   ```bash
   ls -la $GOOGLE_CREDENTIALS_PATH
   ```
3. Verify path in `.env` file or Infisical matches actual file location

---

### Error: "Redirect URI mismatch"

**Symptom**: `redirect_uri_mismatch` error during OAuth flow

**Solutions**:
1. Verify OAuth client is "Desktop app" type (not "Web application")
2. Check that `http://127.0.0.1:8080` is in authorized redirect URIs
3. In Google Cloud Console:
   - Navigate to APIs & Services → Credentials
   - Click on your OAuth client ID
   - Verify "Authorized redirect URIs" includes `http://127.0.0.1:8080`
   - If not, add it and click Save

---

### Error: "Insufficient permissions" or "Access blocked"

**Symptom**: `403 Insufficient Permission` or `Access blocked: Authorization Error`

**Solutions**:
1. Verify OAuth consent screen has `gmail.readonly` scope configured
2. Delete token.json and re-authenticate:
   ```bash
   rm token.json
   python src/email_receiver/gmail_receiver.py
   ```
3. If using External OAuth app, verify your email is added as a test user

---

### Error: "Token has been expired or revoked"

**Symptom**: `RefreshError: The credentials do not contain the necessary fields for the refresh flow`

**Solutions**:
1. Delete token.json and re-authenticate:
   ```bash
   rm token.json
   python src/email_receiver/gmail_receiver.py
   ```
2. Verify credentials.json is valid (not corrupted)

**Note**: Refresh tokens expire after 6 months of inactivity. You'll need to re-authenticate periodically if not using the system regularly.

---

### Error: "No emails found" despite sending test emails

**Symptom**: Query returns empty results even though emails were sent to collab@signite.co

**Solutions**:
1. Verify authenticated account is a member of collab@signite.co group:
   - Check Google Workspace Admin → Groups → collab@signite.co → Members
2. Wait longer for Gmail indexing (can take up to 24 hours in rare cases)
3. Check if emails are in spam/trash folders:
   ```bash
   uv run python tests/manual/test_gmail_retrieval.py --query 'deliveredto:"collab@signite.co" in:anywhere'
   ```
4. Verify email was actually delivered to member inbox (check Gmail web interface)

---

### Error: "Rate limit exceeded"

**Symptom**: `429 Quota exceeded` or `User rate limit exceeded`

**Solutions**:
1. Wait a few minutes before retrying (Gmail API has per-user rate limits)
2. Reduce `--max-results` parameter to fetch fewer emails
3. Implement exponential backoff (already built into GmailReceiver class)

**Note**: Free tier limit is 1 billion quota units/day. Typical CollabIQ usage (<100 emails/day) should never hit this limit.

---

## Security Best Practices

1. **Never commit credentials**:
   - Ensure `credentials.json` and `token.json` are in `.gitignore`
   - Never share these files via email or chat

2. **Restrict file permissions**:
   ```bash
   chmod 600 credentials.json token.json
   ```

3. **Rotate credentials periodically**:
   - Delete old OAuth client in Google Cloud Console
   - Create new OAuth client
   - Update credentials.json

4. **Monitor access**:
   - Review authorized applications periodically: https://myaccount.google.com/permissions
   - Revoke access if no longer needed

5. **Use Infisical for production**:
   - .env files are acceptable for local development
   - Production deployments should use Infisical secret management

---

## Part 5: Common Mistakes & Troubleshooting

### Common Mistakes to Avoid

#### ❌ Mistake 1: Trying to authenticate as collab@signite.co
```bash
# WRONG - This will fail
# User tries to login as collab@signite.co during OAuth flow
# Result: Authentication error or personal account login
```

**Fix**: Always authenticate as a group member (jeffreylim@signite.co, gloriakim@signite.co, etc.)

---

#### ❌ Mistake 2: Retrieving emails without filtering
```python
# WRONG - Returns personal inbox emails
messages = gmail_receiver.fetch_emails(query="after:2025/11/01", max_emails=10)

# Result: Gets jeffreylim@signite.co's personal emails, NOT group emails
```

**Fix**: Always include `to:collab@signite.co` in query
```python
# CORRECT - Returns emails sent to the group
messages = gmail_receiver.fetch_emails(
    query="to:collab@signite.co after:2025/11/01",
    max_emails=10
)
```

---

#### ❌ Mistake 3: Using deliveredto: operator
```bash
# WRONG - Unreliable with Gmail API
query="deliveredto:collab@signite.co"
```

**Fix**: Use `to:` operator instead
```bash
# CORRECT - Reliable with Gmail API
query="to:collab@signite.co"
```

---

### Additional Troubleshooting Scenarios

#### Issue: No emails found despite correct query
**Symptom**: Query returns empty results even with `to:collab@signite.co`

**Possible Causes**:
1. Authenticated user is not a group member
2. No emails sent to collab@signite.co in date range
3. Gmail indexing delay (wait 1-2 minutes)
4. Query missing `to:collab@signite.co` filter

**Fix**:
```bash
# Verify group membership
# Google Workspace Admin → Groups → collab@signite.co → Members

# Wait for Gmail indexing
sleep 120

# Retry with broader date range
uv run python tests/manual/test_gmail_retrieval.py \
  --query 'to:collab@signite.co after:2025/01/01' \
  --max-results 100
```

---

#### Issue: Getting personal emails instead of group emails
**Symptom**: Retrieved emails are from jeffreylim@signite.co's personal inbox

**Cause**: Missing `to:collab@signite.co` filter in query

**Fix**: Always include `to:collab@signite.co` in all Gmail queries
```python
# BEFORE (wrong)
query = f"after:{since_date.strftime('%Y/%m/%d')}"

# AFTER (correct)
query = f"to:collab@signite.co after:{since_date.strftime('%Y/%m/%d')}"
```

---

### Quick Reference Card

| Question | Answer |
|----------|--------|
| Can I login as collab@signite.co? | ❌ No - it's a group, not an account |
| Which account should I authenticate with? | ✅ A group member (jeffreylim@signite.co) |
| What query should I use? | ✅ `to:collab@signite.co` |
| Can I skip the `to:` filter? | ❌ No - you'll get personal emails |
| Does `deliveredto:` work? | ❌ No - unreliable with Gmail API |
| Where is token.json stored? | `/Users/jlim/Projects/CollabIQ/token.json` |
| Which account does token.json represent? | The member account that authenticated |

---

## Next Steps

After completing this setup:

1. ✅ Gmail API credentials configured
2. ✅ OAuth authentication flow complete
3. ✅ Token refresh working automatically
4. ✅ Group alias email retrieval functional

**You're now ready to**:
- Run entity extraction on real emails from collab@signite.co
- Deploy CollabIQ with production email access
- Monitor email ingestion pipeline

**For ongoing operations**, refer to:
- Token refresh happens automatically (no action needed)
- Re-authenticate every 6 months or if refresh token expires
- Monitor Gmail API quota usage via Google Cloud Console

---

**Setup Status**: ✅ Complete
**Estimated Total Time**: 12-19 minutes (within 15-minute target for SC-001)
