# Feature Specification: Gmail Setup for Production Email Access

**Feature Branch**: `005-gmail-setup`
**Created**: 2025-11-01
**Status**: Draft
**Input**: User description: "Make gmail_receiver.py fully functional with actual email (I changed from portfolioupdates@signite.co to collab@signite.co), and make the test suites pass with gmail_receiver(). Guide me how I can provide necessary API keys, oAuth, or any other necessary credentials from the actual email. Note that the collab@signite.co is a group alias in google workspace, not an actual email."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set Up Gmail API Credentials (Priority: P1)

A developer needs to configure the CollabIQ system to access emails from the collab@signite.co Google Workspace group alias, which requires proper OAuth2 credentials and permissions.

**Why this priority**: Without proper Gmail API setup, the entire email ingestion pipeline cannot function. This is a prerequisite for all email processing features.

**Independent Test**: Can be fully tested by running the authentication flow and verifying that the system successfully retrieves at least one email from the collab@signite.co inbox.

**Acceptance Scenarios**:

1. **Given** a Google Workspace admin has access to create OAuth2 credentials, **When** they follow the credential setup guide, **Then** they can download the credentials.json file
2. **Given** valid OAuth2 credentials are configured, **When** a developer runs the initial authentication, **Then** the system opens a browser for Google sign-in and stores refresh tokens
3. **Given** stored refresh tokens exist, **When** the system needs to access Gmail, **Then** it automatically refreshes tokens without requiring user intervention
4. **Given** the OAuth2 setup is complete, **When** the system attempts to read from collab@signite.co, **Then** it successfully retrieves email messages

---

### User Story 2 - Handle Group Alias Email Access (Priority: P1)

The system needs to access emails sent to collab@signite.co (a group alias) without treating it as a standalone Gmail account, since group aliases cannot be directly authenticated.

**Why this priority**: Understanding how to access group alias emails is critical for the specific use case. Without this, the feature cannot work at all.

**Independent Test**: Can be tested by verifying that emails sent to collab@signite.co are retrievable through a member account's inbox.

**Acceptance Scenarios**:

1. **Given** collab@signite.co is a Google Workspace group alias, **When** an email is sent to collab@signite.co, **Then** the email appears in member inboxes
2. **Given** a member account has valid OAuth2 credentials, **When** the system queries for emails sent to collab@signite.co, **Then** it successfully retrieves those messages using label or search filters
3. **Given** the group alias configuration, **When** the documentation is followed, **Then** developers understand which account to authenticate with

---

### User Story 3 - Pass Test Suites with Real Gmail Connection (Priority: P2)

The test suites must validate that gmail_receiver.py works correctly with the actual Gmail API and collab@signite.co email access, not just mocked responses.

**Why this priority**: Ensures the implementation is production-ready and not just theoretically correct. Critical for deployment confidence but depends on P1 setup being complete first.

**Independent Test**: Can be tested by running the integration test suite with real Gmail API credentials and verifying all tests pass.

**Acceptance Scenarios**:

1. **Given** valid Gmail API credentials are configured, **When** integration tests run, **Then** they successfully connect to Gmail API without authentication errors
2. **Given** test emails exist in the collab@signite.co inbox, **When** retrieval tests run, **Then** they successfully fetch and parse email messages
3. **Given** all Gmail API operations are tested, **When** the test suite completes, **Then** no failures related to authentication or email access occur

---

### Edge Cases

- What happens when OAuth2 tokens expire during email retrieval?
- How does the system handle rate limiting from Gmail API (quota exceeded)?
- What if the authenticated user account is removed from the collab@signite.co group?
- How does the system behave when collab@signite.co receives no emails for extended periods?
- What happens if the credentials.json file is missing or corrupted?
- How does the system handle network failures during token refresh?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support OAuth2 authentication flow for Gmail API access with proper scopes
- **FR-002**: System MUST provide clear documentation on obtaining OAuth2 credentials from Google Cloud Console
- **FR-003**: System MUST store OAuth2 refresh tokens securely (using Infisical or .env file)
- **FR-004**: System MUST automatically refresh expired access tokens using stored refresh tokens
- **FR-005**: System MUST access emails sent to collab@signite.co group alias through an authorized member account
- **FR-006**: System MUST provide step-by-step setup guide for Google Workspace administrators
- **FR-007**: System MUST validate that OAuth2 credentials have the correct Gmail API scopes (gmail.readonly)
- **FR-008**: System MUST handle authentication errors gracefully with actionable error messages
- **FR-009**: System MUST support both new authentication (first-time setup) and token refresh workflows
- **FR-010**: Integration tests MUST run successfully with real Gmail API connection
- **FR-011**: System MUST document which Google Workspace account to authenticate with for group alias access
- **FR-012**: System MUST support credential rotation without requiring code changes

### Key Entities

- **OAuth2 Credentials**: Client ID, client secret, authorized redirect URIs from Google Cloud Console
- **OAuth2 Tokens**: Access token (short-lived), refresh token (long-lived), expiry timestamp
- **Gmail API Service**: Authorized API client instance used for making Gmail API calls
- **Group Alias**: collab@signite.co email address (not a standalone account, delivered to member inboxes)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can complete Gmail API credential setup in under 15 minutes following the documentation
- **SC-002**: System successfully authenticates with Gmail API on first attempt after credentials are configured
- **SC-003**: System retrieves emails from collab@signite.co inbox without manual intervention after initial setup
- **SC-004**: All integration tests pass with real Gmail API connection (100% pass rate)
- **SC-005**: Token refresh happens automatically without user intervention when access tokens expire
- **SC-006**: Setup documentation is clear enough that a developer unfamiliar with Google Cloud Console can follow it successfully

## Assumptions

1. **Google Workspace Access**: User has admin access to the Google Workspace account that owns collab@signite.co
2. **Google Cloud Console**: User can create OAuth2 credentials in Google Cloud Console for the Gmail API
3. **Group Membership**: At least one user account is a member of the collab@signite.co group and can be used for authentication
4. **Email Delivery**: Google Workspace is configured to deliver collab@signite.co emails to member inboxes
5. **Network Access**: Development environment has internet access to reach Google APIs
6. **Existing Infrastructure**: The Infisical or .env secret management system from Phase 003 is already functional
7. **Test Email Access**: There are test emails in the collab@signite.co inbox that can be used for validation

## Dependencies

- **Phase 1a (Email Reception)**: Existing gmail_receiver.py implementation that needs configuration
- **Phase 003 (Infisical Secrets)**: Secret management infrastructure for storing OAuth2 tokens securely
- **Google Cloud Console**: External service for creating OAuth2 credentials
- **Google Workspace**: External service that manages collab@signite.co group alias

## Out of Scope (for MVP)

- Automatic credential rotation or management
- Support for multiple email accounts or inboxes
- Advanced Gmail API features (labels, categories, filters beyond basic email retrieval)
- Migration from other email service providers
- Email sending capabilities (only receiving/reading is in scope)
- Support for non-Google Workspace email providers
- Real-time email notifications (polling-based retrieval only)
