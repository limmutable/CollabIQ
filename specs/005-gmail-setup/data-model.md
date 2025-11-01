# Data Model: Gmail Setup for Production Email Access

**Feature**: 005-gmail-setup
**Date**: 2025-11-01
**Phase**: Phase 1 - Design

## Entity Definitions

### OAuth2Credentials

OAuth2 credentials obtained from Google Cloud Console for authenticating with Gmail API.

**Purpose**: Static credentials shared across all users of the application. Identifies the CollabIQ application to Google's OAuth2 servers.

**Attributes**:
- `client_id` (string, required): OAuth2 client ID from Google Cloud Console
- `client_secret` (string, required): OAuth2 client secret from Google Cloud Console
- `redirect_uris` (list[string], required): List of authorized redirect URIs (e.g., `["http://127.0.0.1:8080"]`)
- `project_id` (string, optional): Google Cloud Project ID
- `auth_uri` (string, default: `"https://accounts.google.com/o/oauth2/auth"`): OAuth2 authorization endpoint
- `token_uri` (string, default: `"https://oauth2.googleapis.com/token"`): OAuth2 token endpoint

**Storage**: Infisical secret manager or .env file (fallback)

**Lifecycle**: Long-lived, manually rotated by administrators

**Example**:
```json
{
  "client_id": "123456789-abcdefg.apps.googleusercontent.com",
  "client_secret": "GOCSPX-abc123...",
  "redirect_uris": ["http://127.0.0.1:8080"],
  "project_id": "collabiq-prod",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

---

### OAuth2Token

User-specific access and refresh tokens obtained after completing the OAuth2 authorization flow.

**Purpose**: Provides authenticated access to Gmail API on behalf of a specific user. Tokens are user-specific and cannot be shared.

**Attributes**:
- `access_token` (string, required): Short-lived token for API requests (valid 1 hour)
- `refresh_token` (string, required): Long-lived token for obtaining new access tokens (valid 6 months)
- `token_expiry` (datetime, required): When the access token expires
- `scopes` (list[string], required): Granted OAuth2 scopes (e.g., `["https://www.googleapis.com/auth/gmail.readonly"]`)
- `token_uri` (string, required): URI for token refresh operations

**Storage**: Local filesystem (`token.json`) with restricted permissions (chmod 600)

**Lifecycle**:
- Access tokens expire after 1 hour (automatically refreshed)
- Refresh tokens expire after 6 months of inactivity
- User must re-authenticate if refresh token expires

**Security Constraints**:
- Must NOT be committed to version control
- Must NOT be stored in Infisical (user-specific, generated during OAuth flow)
- File permissions should be restricted (owner read/write only)

**Example**:
```json
{
  "access_token": "ya29.a0AfH6SMBx...",
  "refresh_token": "1//0gZ1xYz...",
  "token_expiry": "2025-11-01T15:30:00Z",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

---

### GmailServiceClient

Authenticated Gmail API client instance used for making API requests.

**Purpose**: Provides interface to Gmail API operations (list messages, get message, search, etc.)

**Attributes**:
- `credentials` (OAuth2Token, required): Valid OAuth2 credentials
- `user_id` (string, default: `"me"`): Gmail user ID (always "me" for authenticated user)
- `max_retries` (int, default: 3): Maximum retry attempts for failed API calls
- `base_delay` (float, default: 2.0): Base delay for exponential backoff (seconds)

**Methods**:
- `list_messages(query: str, max_results: int) -> list[Message]`: Search and retrieve messages
- `get_message(message_id: str) -> Message`: Retrieve full message by ID
- `refresh_credentials() -> None`: Refresh expired access token

**Lifecycle**:
- Created on-demand when Gmail access is needed
- Automatically refreshes credentials when access token expires
- Raises authentication error if refresh token is invalid/expired

**Example Usage**:
```python
service = GmailServiceClient(credentials=oauth2_token)
messages = service.list_messages(query='deliveredto:"collab@signite.co"', max_results=10)
```

---

### GroupAlias

Represents a Google Workspace group alias email address that distributes emails to member inboxes.

**Purpose**: Encapsulates information about the group alias being monitored (collab@signite.co)

**Attributes**:
- `email_address` (string, required): Group alias email (e.g., `"collab@signite.co"`)
- `gmail_query` (string, computed): Gmail API query filter (e.g., `'deliveredto:"collab@signite.co"'`)
- `authenticated_member` (string, optional): Email of the member account used for authentication

**Methods**:
- `build_query() -> str`: Returns Gmail API query string for filtering group emails
- `validate_access(service: GmailServiceClient) -> bool`: Verifies authenticated user can access group emails

**Notes**:
- Group aliases have NO separate mailbox
- Emails sent to group alias are delivered to all member inboxes
- Must authenticate as a group member, not as the alias itself
- Use `deliveredto:` query operator to filter group emails

**Example**:
```python
group_alias = GroupAlias(
    email_address="collab@signite.co",
    authenticated_member="admin@signite.co"
)
query = group_alias.build_query()  # 'deliveredto:"collab@signite.co"'
```

---

## Entity Relationships

```
OAuth2Credentials (static, shared)
    ↓ (used during OAuth flow)
OAuth2Token (user-specific, generated)
    ↓ (authenticates)
GmailServiceClient (runtime instance)
    ↓ (queries using)
GroupAlias (configuration)
    ↓ (retrieves emails from)
Gmail Inbox (external)
```

**Flow**:
1. Application loads OAuth2Credentials from Infisical/env
2. User completes OAuth flow → generates OAuth2Token → stored in token.json
3. Application creates GmailServiceClient using OAuth2Token
4. GmailServiceClient queries Gmail API with GroupAlias.build_query()
5. Gmail API returns messages delivered to group alias

---

## Data Validation Rules

### OAuth2Credentials
- `client_id` must match pattern: `*-*.apps.googleusercontent.com`
- `client_secret` must match pattern: `GOCSPX-*`
- `redirect_uris` must include at least one loopback address (`http://127.0.0.1:*` or `http://localhost:*`)

### OAuth2Token
- `access_token` and `refresh_token` must be non-empty strings
- `token_expiry` must be a valid ISO 8601 datetime
- `scopes` must include `"https://www.googleapis.com/auth/gmail.readonly"`

### GroupAlias
- `email_address` must be a valid email format
- `email_address` must exist in Google Workspace (validation done at runtime)

---

## Storage Locations

| Entity | Storage Location | Format | Version Control |
|--------|------------------|--------|-----------------|
| OAuth2Credentials | Infisical or .env | JSON or key-value | .env in .gitignore |
| OAuth2Token | Local token.json | JSON | .gitignore |
| GmailServiceClient | Runtime memory | N/A | N/A |
| GroupAlias | Configuration (settings.py) | Python class | Yes |

---

## Security Considerations

1. **OAuth2Credentials**: Client secret is not truly secret for desktop applications (embedded in code). Google accepts this for Desktop OAuth flow.
2. **OAuth2Token**: Refresh tokens provide long-term access. Must be protected with file permissions and never committed to version control.
3. **Token Expiry**: Access tokens expire after 1 hour. Application must handle refresh gracefully.
4. **Scope Minimization**: Only request `gmail.readonly` scope (principle of least privilege).
5. **Token Revocation**: Users can revoke access at any time via Google Account settings.

---

## Error States

### Missing Credentials
- **Trigger**: credentials.json not found or invalid
- **Handling**: Provide clear error message directing user to setup documentation

### Expired Refresh Token
- **Trigger**: Refresh token expired (6 months inactivity) or revoked by user
- **Handling**: Prompt user to re-authenticate (delete token.json and re-run OAuth flow)

### Invalid Scopes
- **Trigger**: Token scopes don't include gmail.readonly
- **Handling**: Delete token.json and re-authenticate with correct scopes

### Group Access Denied
- **Trigger**: Authenticated user is not a member of collab@signite.co group
- **Handling**: Error message explaining group membership requirement

---

**Design Status**: ✅ Complete
**Ready for Phase 2 (Implementation Planning)**: Yes
