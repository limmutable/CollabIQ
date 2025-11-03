# Gmail Group Authentication Quick Reference

**Last Updated**: 2025-11-03
**Status**: Active - Critical Reference Document

---

## ⚠️ CRITICAL: collab@signite.co is a Google Group

### Key Facts

1. **collab@signite.co is NOT a regular Gmail mailbox**
   - It's a Google Workspace group alias
   - Cannot authenticate directly as collab@signite.co
   - No standalone credentials exist for this group

2. **Authentication Method**
   - ✅ Authenticate as a **group member account** (e.g., jeffreylim@signite.co)
   - ✅ Ensure the member account is part of the collab@signite.co Google Group
   - ❌ Do NOT try to login as collab@signite.co (will fail)

3. **Email Retrieval**
   - ✅ **ALWAYS use Gmail query**: `to:collab@signite.co`
   - ✅ Combine with date filters: `to:collab@signite.co after:2025/11/01`
   - ❌ Do NOT query without `to:collab@signite.co` filter (will return personal emails)

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Trying to authenticate as collab@signite.co
```bash
# WRONG - This will fail
# User tries to login as collab@signite.co during OAuth flow
# Result: Authentication error or personal account login
```

**Fix**: Always authenticate as a group member (jeffreylim@signite.co, gloriakim@signite.co, etc.)

---

### ❌ Mistake 2: Retrieving emails without filtering
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

### ❌ Mistake 3: Using deliveredto: operator
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

## Correct Authentication Flow

### Step 1: Verify Group Membership
```bash
# Admin should verify the authenticated user is a group member
# Google Workspace Admin → Groups → collab@signite.co → Members
# Ensure jeffreylim@signite.co (or other member) is listed
```

### Step 2: Authenticate as Group Member
```bash
cd /Users/jlim/Projects/CollabIQ

# Run authentication script
uv run python scripts/authenticate_gmail.py

# When browser opens:
# 1. Login as jeffreylim@signite.co (group member)
# 2. Grant permissions
# 3. Complete OAuth flow
```

### Step 3: Verify Group Email Access
```bash
# Test retrieval with correct query
uv run python scripts/test_gmail_retrieval.py \
  --query 'to:collab@signite.co' \
  --max-results 5

# Expected: Shows emails sent to collab@signite.co
# If empty: Check group membership or email delivery
```

---

## Test Scripts Reference

### test_gmail_retrieval.py
**Purpose**: Test Gmail API connectivity and email retrieval

**Correct Usage**:
```bash
# Retrieve group emails from last 30 days
uv run python scripts/test_gmail_retrieval.py \
  --query 'to:collab@signite.co after:2025/10/01' \
  --max-results 10
```

### test_phase2b_real_emails.py
**Purpose**: Test Phase 2b LLM matching with real emails

**Current Implementation**: Already includes `to:collab@signite.co` filter (line 102)
```python
# scripts/test_phase2b_real_emails.py:102
query = f"to:collab@signite.co after:{since_date.strftime('%Y/%m/%d')}"
```

---

## Environment Variables

### Required Token Files
```bash
# OAuth2 credentials (from Google Cloud Console)
GOOGLE_CREDENTIALS_PATH=credentials.json

# OAuth2 access/refresh token (created during authentication)
GMAIL_TOKEN_PATH=token.json
```

### Token File Contents
- **credentials.json**: OAuth2 client configuration (client_id, client_secret)
- **token.json**: OAuth2 access token + refresh token for **jeffreylim@signite.co** (or other member)

**Note**: token.json is tied to the specific account that authenticated (e.g., jeffreylim@signite.co), NOT to collab@signite.co.

---

## Troubleshooting

### Issue: No emails found
**Symptom**: Query returns empty results

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
uv run python scripts/test_gmail_retrieval.py \
  --query 'to:collab@signite.co after:2025/01/01' \
  --max-results 100
```

---

### Issue: Getting personal emails instead of group emails
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

## Quick Reference Card

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

## Related Documentation

- [Full Gmail OAuth Setup Guide](gmail-oauth-setup.md) - Complete authentication setup
- [Troubleshooting Gmail API](troubleshooting-gmail-api.md) - Common issues and solutions
- [Phase 2b Test Script](../../scripts/test_phase2b_real_emails.py) - Real email testing

---

**Document Owner**: CollabIQ Development Team
**Review Frequency**: After any Gmail authentication changes
**Critical Status**: Always verify group membership before authentication
