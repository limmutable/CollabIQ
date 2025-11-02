# Troubleshooting Guide: Gmail API Setup

**Feature**: 005-gmail-setup
**Last Updated**: 2025-11-01

This guide provides solutions to common errors encountered during Gmail API setup and authentication.

---

## Table of Contents

1. [Credentials and File Errors](#credentials-and-file-errors)
2. [OAuth2 Flow Errors](#oauth2-flow-errors)
3. [Token and Authentication Errors](#token-and-authentication-errors)
4. [Group Alias Access Issues](#group-alias-access-issues)
5. [API Quota and Rate Limiting](#api-quota-and-rate-limiting)

---

## Credentials and File Errors

### Error: "Credentials file not found"

**Symptom**:
```
EmailReceiverError: AUTHENTICATION_FAILED
Gmail API credentials file not found at credentials.json
```

**Cause**: The `GOOGLE_CREDENTIALS_PATH` or `GMAIL_CREDENTIALS_PATH` environment variable points to a non-existent file.

**Solution**:
1. Verify the file path:
   ```bash
   echo $GOOGLE_CREDENTIALS_PATH
   ls -la $GOOGLE_CREDENTIALS_PATH
   ```

2. If the file doesn't exist:
   - Download credentials.json from Google Cloud Console
   - Follow [gmail-oauth-setup.md](gmail-oauth-setup.md) Part 1.4

3. Update your `.env` file:
   ```bash
   GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   ```

---

### Error: "Invalid credentials format"

**Symptom**:
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause**: The credentials.json file is corrupted or not valid JSON.

**Solution**:
1. Verify the file is valid JSON:
   ```bash
   python -m json.tool credentials.json
   ```

2. If invalid, re-download from Google Cloud Console:
   - Navigate to **APIs & Services → Credentials**
   - Find your OAuth 2.0 Client ID
   - Click the download icon
   - Replace the corrupted file

---

## OAuth2 Flow Errors

### Error: "redirect_uri_mismatch"

**Symptom**:
```
OAuth2 redirect URI mismatch.
Error 400: redirect_uri_mismatch
```

**Cause**: The redirect URI configured in Google Cloud Console doesn't match what the application uses.

**Solution**:
1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services → Credentials**
3. Click on your OAuth 2.0 Client ID (CollabIQ Gmail Receiver)
4. Under "Authorized redirect URIs", ensure this URL is present:
   ```
   http://127.0.0.1:8080
   ```
5. If not present, click **+ ADD URI**, paste the URL, and click **Save**
6. Wait 5 minutes for changes to propagate
7. Delete `token.json` and re-run authentication

**Note**: The application uses port 8080 by default (per research.md Decision 4). If you need to use a different port, update `gmail_receiver.py` line 124.

---

### Error: "Access blocked: Authorization Error"

**Symptom**:
```
Error 403: access_denied
This app is blocked. This app tried to access sensitive info in your Google Account.
```

**Cause**: OAuth consent screen is not configured or is in "Testing" mode with missing test users.

**Solution for Internal (Google Workspace) apps**:
1. Navigate to **APIs & Services → OAuth consent screen**
2. Verify **User type** is set to "Internal"
3. Click **Back to Dashboard**

**Solution for External apps**:
1. Navigate to **APIs & Services → OAuth consent screen**
2. Under "Test users", click **+ ADD USERS**
3. Add the email address you're authenticating with
4. Click **Save**
5. Delete `token.json` and re-run authentication

---

### Error: "invalid_scope"

**Symptom**:
```
Error 400: invalid_scope
Some requested scopes were invalid.
```

**Cause**: The OAuth consent screen doesn't have the `gmail.readonly` scope configured.

**Solution**:
1. Navigate to **APIs & Services → OAuth consent screen**
2. Click **EDIT APP**
3. Click **Save and Continue** until you reach the "Scopes" page
4. Click **ADD OR REMOVE SCOPES**
5. Search for "Gmail API"
6. Select: `https://www.googleapis.com/auth/gmail.readonly`
7. Click **UPDATE** → **Save and Continue**
8. Delete `token.json` and re-run authentication

---

## Token and Authentication Errors

### Error: "Token has been expired or revoked"

**Symptom**:
```
OAuth2 token is invalid or expired.
RefreshError: invalid_grant: Token has been expired or revoked.
```

**Cause**: Refresh token expired (6 months of inactivity) or was manually revoked by the user.

**Solution**:
1. Delete the expired token:
   ```bash
   rm token.json
   ```

2. Re-run authentication:
   ```bash
   python src/email_receiver/gmail_receiver.py
   ```

3. Complete the OAuth flow in the browser

**Prevention**: Use the application at least once every 6 months to prevent refresh token expiration.

---

### Error: "invalid_grant"

**Symptom**:
```
google.auth.exceptions.RefreshError: invalid_grant: Bad Request
```

**Cause**: Token refresh failed. Common reasons:
- Refresh token revoked by user
- OAuth credentials changed
- Scopes changed

**Solution**:
1. Revoke existing access:
   - Visit https://myaccount.google.com/permissions
   - Find "CollabIQ Email Receiver"
   - Click **Remove access**

2. Delete token file:
   ```bash
   rm token.json
   ```

3. Re-authenticate:
   ```bash
   python src/email_receiver/gmail_receiver.py
   ```

---

### Error: "Insufficient permissions"

**Symptom**:
```
HttpError 403: Request had insufficient authentication scopes.
```

**Cause**: Token was created with different scopes than currently required.

**Solution**:
1. Delete token with old scopes:
   ```bash
   rm token.json
   ```

2. Verify `gmail.readonly` scope in OAuth consent screen (see "invalid_scope" above)

3. Re-authenticate to get token with correct scopes

---

## Group Alias Access Issues

### Error: "No emails found" despite sending test emails

**Symptom**: Query returns empty results even though emails were sent to collab@signite.co

**Cause**: Authenticated account is not a member of the collab@signite.co Google Workspace group.

**Solution**:
1. Verify group membership:
   - Go to [Google Admin Console](https://admin.google.com/)
   - Navigate to **Directory → Groups**
   - Find `collab@signite.co`
   - Check that the authenticated user is in the **Members** list

2. If not a member, add the user:
   - Click **Add members**
   - Enter the user's email
   - Click **Add to group**

3. Wait 5 minutes for changes to sync

4. Re-run email retrieval

---

### Error: "Emails appear in Gmail but not via API"

**Symptom**: Emails sent to collab@signite.co are visible in Gmail web interface but not retrieved by the API query.

**Cause**: Gmail API query doesn't use the `deliveredto:` filter correctly.

**Solution**:
1. Verify the query uses the correct filter:
   ```python
   query = 'deliveredto:"collab@signite.co"'
   ```

2. Check if emails are in spam/trash:
   ```python
   query = 'deliveredto:"collab@signite.co" in:anywhere'
   ```

3. Wait up to 24 hours for Gmail indexing (rare but possible)

**Note**: The `deliveredto:` operator filters by the SMTP `Delivered-To` header, which persists even after group expansion (per research.md Decision 3).

---

## API Quota and Rate Limiting

### Error: "Quota exceeded"

**Symptom**:
```
HttpError 429: Quota exceeded for quota metric 'Queries' and limit 'Queries per day' of service 'gmail.googleapis.com'
```

**Cause**: Gmail API daily quota limit reached (1 billion units/day for free tier).

**Solution**:
1. Check quota usage:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **APIs & Services → Dashboard**
   - Click **Gmail API**
   - View **Quotas & System Limits**

2. Wait until quota resets (midnight Pacific Time)

3. Reduce API calls:
   - Decrease `max_results` parameter
   - Add date filters to queries: `after:2025/10/01`
   - Implement caching

**Note**: Typical CollabIQ usage (<100 emails/day) should never hit this limit.

---

### Error: "User rate limit exceeded"

**Symptom**:
```
HttpError 429: User-rate limit exceeded. Retry after 2025-11-01T15:30:00Z
```

**Cause**: Per-user rate limit reached (250 units/second/user).

**Solution**:
1. The application automatically retries with exponential backoff

2. If errors persist, reduce concurrent requests:
   - Process emails sequentially instead of in parallel
   - Add delays between API calls: `time.sleep(1)`

---

## Network and Connection Errors

### Error: "Failed to establish a new connection"

**Symptom**:
```
requests.exceptions.ConnectionError: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known
```

**Cause**: No internet connection or DNS resolution failure.

**Solution**:
1. Verify internet connectivity:
   ```bash
   ping -c 4 google.com
   ```

2. Check DNS resolution:
   ```bash
   nslookup gmail.googleapis.com
   ```

3. If behind a corporate firewall, configure proxy:
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

---

### Error: "SSL: CERTIFICATE_VERIFY_FAILED"

**Symptom**:
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Cause**: SSL certificate verification failure (common in corporate networks).

**Solution**:
1. **Not recommended for production**: Disable SSL verification (development only)
   ```python
   import os
   os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
   ```

2. **Recommended**: Install corporate CA certificates:
   ```bash
   export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt
   ```

---

## Advanced Troubleshooting

### Enable Debug Logging

Get detailed error information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
python src/email_receiver/gmail_receiver.py
```

---

### Verify OAuth2 Flow Manually

Test OAuth flow outside the application:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    SCOPES
)

creds = flow.run_local_server(port=8080)
print(f"Access token: {creds.token[:20]}...")
print(f"Refresh token: {creds.refresh_token[:20]}...")
```

---

### Check Gmail API Status

Verify Gmail API is operational:
- Visit [Google Workspace Status Dashboard](https://www.google.com/appsstatus/dashboard/)
- Check for reported outages

---

## Getting Help

If the above solutions don't resolve your issue:

1. **Check logs**: Review application logs for detailed error messages
2. **Verify configuration**: Double-check all environment variables and file paths
3. **Consult documentation**: Review [gmail-oauth-setup.md](gmail-oauth-setup.md) for setup steps
4. **Search GitHub issues**: Check if others have encountered similar issues
5. **Report bug**: Create a detailed issue report with:
   - Error message (sanitized, no secrets)
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)

---

## Related Documentation

- [Gmail OAuth Setup Guide](gmail-oauth-setup.md)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Gmail API Error Codes](https://developers.google.com/gmail/api/guides/handle-errors)
