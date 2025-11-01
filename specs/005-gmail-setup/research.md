# Technical Research: Gmail Setup for Production Email Access

**Feature**: 005-gmail-setup
**Date**: 2025-11-01
**Research Phase**: Phase 0 - Technical Investigation

## Executive Summary

This document consolidates research findings for setting up Gmail API access to retrieve emails from the collab@signite.co Google Workspace group alias. The key challenges are: (1) configuring OAuth2 credentials for a Python CLI application, and (2) accessing group alias emails when the alias is not a standalone account.

**Key Decisions**:
1. ✅ Use Desktop Application OAuth2 credentials (not Web Application)
2. ✅ Authenticate as a group member to access collab@signite.co emails
3. ✅ Use `deliveredto:"collab@signite.co"` Gmail API query to filter group emails
4. ✅ Store OAuth2 credentials using existing Infisical infrastructure
5. ✅ Provide step-by-step setup documentation for Google Cloud Console

---

## Decision 1: OAuth2 Application Type

### Choice: Desktop Application OAuth2 Credentials

**Rationale**:
- The gmail_receiver.py is a CLI application, not a web service
- No backend server exists to handle OAuth callbacks
- Desktop OAuth uses loopback IP addresses (http://127.0.0.1:PORT) for redirect URIs
- Client secret is embedded in application code (not truly secret for desktop apps)
- Simpler authentication flow for end-users (browser-based sign-in)

**Alternatives Considered**:
- **Web Application OAuth**: Rejected because it requires HTTPS redirect URIs and a backend server to receive callbacks. Adds unnecessary infrastructure complexity for a CLI tool.
- **Service Account with Domain-Wide Delegation**: Rejected for initial setup due to additional administrative complexity. May be considered for production deployment if multiple users need access.

**Implementation Impact**:
- Use `http://127.0.0.1:8080` as the authorized redirect URI
- Application must start a temporary local web server to receive the OAuth callback
- Use `google-auth-oauthlib` library's `InstalledAppFlow` for handling the OAuth flow
- Store credentials.json and token.json locally (excluded from version control)

---

## Decision 2: OAuth2 Scopes

### Choice: `https://www.googleapis.com/auth/gmail.readonly`

**Rationale**:
- CollabIQ only needs read-only access to emails (no send/modify/delete operations)
- Minimizes required permissions (principle of least privilege)
- Users more likely to grant read-only access than full Gmail access
- Aligns with FR-007 requirement for gmail.readonly scope validation

**Alternatives Considered**:
- **`gmail.metadata`**: Too restrictive - only provides email headers and labels, not message bodies needed for entity extraction
- **`gmail`** (full access): Overly broad - includes write operations not required by CollabIQ

**Security Considerations**:
- Scope cannot be changed without deleting token.json and re-authenticating
- Users can revoke access at any time via Google Account settings
- Tokens expire after 6 months of inactivity

---

## Decision 3: Group Alias Email Access

### Choice: Authenticate as Group Member + Use `deliveredto:` Query Filter

**Rationale**:
- Google Workspace group aliases (like collab@signite.co) are **not standalone accounts**
- When an email is sent to a group alias, Google Workspace delivers it to **all member inboxes**
- Group aliases have no separate mailbox or authentication credentials
- Must authenticate as a group member to access emails delivered to that member's inbox
- Use Gmail API query `deliveredto:"collab@signite.co"` to filter only group-related emails

**How It Works**:
1. Email sent to collab@signite.co → Google Workspace expands to member inboxes
2. Authenticate with OAuth2 as a member account (e.g., admin@signite.co)
3. Query Gmail API with `q='deliveredto:"collab@signite.co"'` to retrieve only group emails
4. The `Delivered-To` SMTP header persists after group expansion, enabling filtering

**Alternatives Considered**:
- **Service Account with Domain-Wide Delegation**: More complex administrative setup. Requires Google Workspace admin to configure domain-wide delegation and Group Administrator role. May be appropriate for production but overkill for initial setup.
- **Collaborative Inbox**: Requires Google Groups UI setup and doesn't provide API-based access to a unified inbox. Not suitable for automated email retrieval.
- **Querying with `to:` operator**: Less reliable than `deliveredto:` because it misses BCC and some forwarding scenarios. `deliveredto:` is the most comprehensive approach.

**Implementation Impact**:
- Documentation must explain **which account to authenticate with** (any group member)
- Gmail API queries must include `deliveredto:"collab@signite.co"` filter
- Test emails must be sent to collab@signite.co to validate retrieval
- Group membership changes may affect access (if authenticated member is removed)

---

## Decision 4: Redirect URI Configuration

### Choice: `http://127.0.0.1:8080`

**Rationale**:
- Google's recommended pattern for desktop/CLI applications
- Works across all platforms (macOS, Linux, Windows)
- Avoids potential firewall issues with `localhost` hostname
- Matches existing gmail_receiver.py implementation patterns

**Alternatives Considered**:
- **`http://localhost:8080`**: May cause firewall/DNS issues on some systems. 127.0.0.1 is more reliable.
- **Custom URI schemes** (e.g., `myapp://oauth`): Deprecated by Google due to security risks. No longer supported.

**Configuration Notes**:
- The redirect URI configured in Google Cloud Console **must exactly match** what the application uses
- Port number is configurable but must be consistent
- Only HTTP is required for loopback addresses (HTTPS not needed for localhost)

---

## Decision 5: Credential Storage

### Choice: Infisical for OAuth2 Credentials + Local token.json for Access Tokens

**Rationale**:
- Leverages existing Infisical infrastructure from Phase 003 (003-infisical-secrets)
- OAuth2 credentials (client ID, client secret) are static and can be centrally managed
- Access tokens and refresh tokens are user-specific and must be stored locally
- Separates long-term credentials (Infisical) from session-specific tokens (local filesystem)

**Storage Strategy**:

| Secret Type | Storage Location | Rationale |
|-------------|------------------|-----------|
| Client ID | Infisical or .env | Static, shared across users |
| Client Secret | Infisical or .env | Static, shared across users |
| Access Token | Local token.json | User-specific, short-lived (1 hour) |
| Refresh Token | Local token.json | User-specific, long-lived (6 months) |

**Alternatives Considered**:
- **All credentials in .env file**: Simpler but doesn't leverage existing Infisical infrastructure. Less secure for production deployments.
- **All credentials in Infisical**: Not feasible because access tokens are user-specific and generated during OAuth flow. Cannot be pre-configured.

**Security Measures**:
- credentials.json and token.json must be added to .gitignore
- token.json should have restricted file permissions (chmod 600 on Unix)
- Refresh tokens enable long-term access without repeated user authentication
- Tokens can be revoked by users at any time via Google Account settings

---

## Decision 6: Documentation Approach

### Choice: Step-by-Step Setup Guide in Markdown

**Rationale**:
- FR-002 and FR-006 require clear documentation for obtaining OAuth2 credentials
- SC-001 targets 15-minute setup time (requires clear, concise instructions)
- SC-006 requires documentation usable by developers unfamiliar with Google Cloud Console
- Markdown format is accessible and can be versioned with code

**Documentation Structure**:
1. **Prerequisites**: Google Workspace admin access, project repository cloned
2. **Part 1: Google Cloud Console Setup** (5-8 minutes)
   - Create/select Google Cloud project
   - Enable Gmail API
   - Configure OAuth consent screen
   - Create Desktop Application OAuth credentials
   - Download credentials.json
3. **Part 2: Local Configuration** (3-5 minutes)
   - Store credentials.json securely
   - Configure environment variables or Infisical secrets
   - Add credentials.json and token.json to .gitignore
4. **Part 3: First-Time Authentication** (2-3 minutes)
   - Run gmail_receiver.py authentication flow
   - Authorize application in browser
   - Verify token.json creation
5. **Part 4: Validation** (2-3 minutes)
   - Run integration tests
   - Verify email retrieval from collab@signite.co
6. **Troubleshooting**: Common errors and solutions

**Alternatives Considered**:
- **Video tutorial**: Higher production cost, harder to maintain, not version-controllable
- **Interactive CLI wizard**: Requires additional development work, outside MVP scope

---

## Implementation Checklist

Based on research findings, the implementation requires:

### Documentation Artifacts
- [ ] Step-by-step guide for Google Cloud Console OAuth2 setup
- [ ] Instructions for which Google Workspace account to authenticate with
- [ ] Gmail API query pattern documentation (deliveredto: filter)
- [ ] Troubleshooting guide for common OAuth2 errors
- [ ] Environment variable or Infisical configuration instructions

### Configuration Updates
- [ ] Update settings.py to support GOOGLE_CREDENTIALS_PATH
- [ ] Ensure gmail_receiver.py uses correct redirect URI (http://127.0.0.1:8080)
- [ ] Add credentials.json and token.json to .gitignore
- [ ] Document required OAuth2 scope: gmail.readonly

### Code Verification
- [ ] Verify gmail_receiver.py implements `deliveredto:` query filtering
- [ ] Verify token refresh logic handles 401 errors (expired tokens)
- [ ] Verify error handling for missing credentials.json
- [ ] Verify OAuth flow uses InstalledAppFlow for desktop application pattern

### Testing Updates
- [ ] Update integration tests to use real Gmail API connection
- [ ] Add test for `deliveredto:"collab@signite.co"` query filtering
- [ ] Add test for OAuth2 token refresh
- [ ] Add test for group alias email retrieval

### Edge Case Handling
- [ ] Handle OAuth2 token expiration (automatic refresh)
- [ ] Handle rate limiting from Gmail API (quota exceeded)
- [ ] Handle authenticated user removed from collab@signite.co group
- [ ] Handle missing credentials.json or token.json files
- [ ] Handle network failures during token refresh

---

## Technical Constraints

### Gmail API Quotas (Free Tier)
- **Quota limit**: 1 billion quota units per day
- **Per-user rate limit**: 250 quota units/second/user
- **Most API calls**: 5-10 quota units each
- **Batch requests**: More efficient for high-volume operations

**Impact**: Unlikely to hit quotas for typical CollabIQ usage (<100 emails/day)

### Token Lifecycle
- **Access tokens**: Valid for 1 hour
- **Refresh tokens**: Valid for 6 months of inactivity (or until revoked)
- **Refresh token expiration**: User must re-authenticate after 6 months of no usage

**Impact**: Must handle token refresh gracefully and prompt re-authentication when refresh fails

### Group Alias Limitations
- **No direct authentication**: Cannot authenticate as the group alias itself
- **Member dependency**: Email access depends on authenticated member remaining in group
- **Delivery delay**: Gmail indexing may delay query results by up to 24 hours

**Impact**: Documentation must clearly explain member authentication requirement

---

## References

- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth2 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Gmail API Query Operators](https://support.google.com/mail/answer/7190)
- [Google Workspace Admin - Groups](https://support.google.com/a/answer/33329)

---

**Research Status**: ✅ Complete
**All NEEDS CLARIFICATION items resolved**: Yes
**Ready for Phase 1 (Design)**: Yes
