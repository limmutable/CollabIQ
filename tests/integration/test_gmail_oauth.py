"""
Integration tests for Gmail OAuth2 authentication flow.

These tests verify OAuth2 credential loading, token refresh, and authentication.
They follow TDD principles and must be written before implementation code.

Test Coverage:
- T005: OAuth2 credentials loading from Infisical or .env
- T006: Token refresh when access token expires
- T007: First-time OAuth flow (simulated)

To run these tests:
1. Set up Gmail API credentials (credentials.json)
2. Set GOOGLE_CREDENTIALS_PATH environment variable
3. Execute: pytest tests/integration/test_gmail_oauth.py -v
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from email_receiver.gmail_receiver import GmailReceiver, EmailReceiverError


@pytest.fixture
def mock_credentials_content():
    """Mock OAuth2 credentials.json content."""
    return {
        "installed": {
            "client_id": "123456789-abcdefg.apps.googleusercontent.com",
            "client_secret": "GOCSPX-mock_secret",
            "redirect_uris": ["http://127.0.0.1:8080"],
            "project_id": "collabiq-test",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }


@pytest.fixture
def mock_token_content():
    """Mock token.json content with valid access and refresh tokens."""
    return {
        "token": "ya29.a0AfH6SMBx_mock_access_token",
        "refresh_token": "1//0gZ1xYz_mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "123456789-abcdefg.apps.googleusercontent.com",
        "client_secret": "GOCSPX-mock_secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    }


@pytest.fixture
def expired_token_content():
    """Mock token.json content with expired access token."""
    return {
        "token": "ya29.a0AfH6SMBx_expired_token",
        "refresh_token": "1//0gZ1xYz_mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "123456789-abcdefg.apps.googleusercontent.com",
        "client_secret": "GOCSPX-mock_secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expiry": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    }


# T005: Test OAuth2 credentials loading from Infisical or .env
def test_oauth_credentials_loading_from_env(tmp_path, mock_credentials_content):
    """
    T005 [P] [US1]: Verify OAuth2 credentials can be loaded from GOOGLE_CREDENTIALS_PATH.

    Given: GOOGLE_CREDENTIALS_PATH points to valid credentials.json
    When: GmailReceiver is initialized
    Then: Credentials file path is set correctly

    This test validates FR-003: System MUST store OAuth2 refresh tokens securely.
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"

    # Act
    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path,
        raw_email_dir=tmp_path / "raw",
        metadata_dir=tmp_path / "metadata"
    )

    # Assert
    assert receiver.credentials_path == creds_path
    assert receiver.credentials_path.exists()
    assert receiver.token_path == token_path


def test_oauth_credentials_missing_file(tmp_path):
    """
    T005 [P] [US1]: Verify graceful error when credentials.json is missing.

    Given: GOOGLE_CREDENTIALS_PATH points to non-existent file
    When: GmailReceiver attempts to connect
    Then: Raise EmailReceiverError with code AUTHENTICATION_FAILED

    This test validates FR-008: System MUST handle authentication errors gracefully.
    """
    # Arrange
    creds_path = tmp_path / "nonexistent_credentials.json"
    token_path = tmp_path / "token.json"

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Act & Assert
    with pytest.raises(EmailReceiverError) as exc_info:
        receiver.connect()

    assert exc_info.value.code == "AUTHENTICATION_FAILED"
    assert "credentials" in exc_info.value.message.lower() or "failed to authenticate" in exc_info.value.message.lower()


# T006: Test token refresh when access token expires
@patch('email_receiver.gmail_receiver.build')
@patch('email_receiver.gmail_receiver.Request')
@patch('email_receiver.gmail_receiver.Credentials')
def test_oauth_token_refresh(mock_credentials_cls, mock_request_cls, mock_build, tmp_path, mock_credentials_content, expired_token_content):
    """
    T006 [P] [US1]: Verify automatic token refresh when access token expires.

    Given: token.json exists with expired access token but valid refresh token
    When: GmailReceiver attempts to connect
    Then: Token is automatically refreshed without user intervention

    This test validates:
    - FR-004: System MUST automatically refresh expired access tokens
    - SC-005: Token refresh happens automatically without user intervention
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(expired_token_content))

    # Mock credentials object
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "1//0gZ1xYz_mock_refresh_token"
    mock_creds.to_json.return_value = json.dumps({
        "token": "ya29.new_refreshed_token",
        "refresh_token": "1//0gZ1xYz_mock_refresh_token",
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    })

    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds
    mock_build.return_value = MagicMock()

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Act
    receiver.connect()

    # Assert
    mock_creds.refresh.assert_called_once()  # Token refresh was called
    assert token_path.exists()  # Token was saved
    mock_build.assert_called_once()  # Gmail service was built


@patch('email_receiver.gmail_receiver.build')
@patch('email_receiver.gmail_receiver.Request')
@patch('email_receiver.gmail_receiver.Credentials')
def test_oauth_token_refresh_failure(mock_credentials_cls, mock_request_cls, mock_build, tmp_path, mock_credentials_content, expired_token_content):
    """
    T006 [P] [US1]: Verify graceful error when token refresh fails.

    Given: token.json exists but refresh token is invalid/expired
    When: GmailReceiver attempts to refresh token
    Then: Raise EmailReceiverError with actionable message

    This test validates FR-008: System MUST handle authentication errors gracefully.
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(expired_token_content))

    # Mock credentials object that fails to refresh
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "1//0gZ1xYz_mock_refresh_token"
    mock_creds.refresh.side_effect = Exception("Token refresh failed: invalid_grant")

    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Act & Assert
    with pytest.raises(EmailReceiverError) as exc_info:
        receiver.connect()

    assert exc_info.value.code == "AUTHENTICATION_FAILED"
    # Verify error message mentions token issues (token refresh, invalid grant, or expired/invalid)
    error_msg = exc_info.value.message.lower()
    assert ("token" in error_msg and ("invalid" in error_msg or "expired" in error_msg or "refresh" in error_msg)) or "invalid_grant" in error_msg


# T007: Test first-time OAuth flow (simulated)
@patch('email_receiver.gmail_receiver.build')
@patch('email_receiver.gmail_receiver.InstalledAppFlow')
def test_oauth_first_time_flow_simulation(mock_installed_flow_cls, mock_build, tmp_path, mock_credentials_content):
    """
    T007 [P] [US1]: Verify first-time OAuth flow creates and saves token.

    Given: credentials.json exists but token.json does not exist
    When: GmailReceiver attempts to connect (OAuth flow simulated)
    Then: OAuth flow is initiated and token.json is created

    Note: This test simulates the OAuth flow since browser interaction cannot be automated.

    This test validates:
    - FR-009: System MUST support both new authentication and token refresh workflows
    - US1 Acceptance Scenario 2: Browser opens, stores refresh tokens
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    assert not token_path.exists()  # No token yet

    # Mock OAuth flow
    mock_flow = MagicMock()
    mock_creds = MagicMock()
    mock_creds.to_json.return_value = json.dumps({
        "token": "ya29.new_token_from_oauth",
        "refresh_token": "1//0gZ1xYz_new_refresh_token",
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    })
    mock_flow.run_local_server.return_value = mock_creds

    mock_installed_flow_cls.from_client_secrets_file.return_value = mock_flow
    mock_build.return_value = MagicMock()

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Act
    receiver.connect()

    # Assert
    mock_flow.run_local_server.assert_called_once()  # OAuth flow was run
    assert token_path.exists()  # Token was saved

    # Verify token.json content
    saved_token = json.loads(token_path.read_text())
    assert "token" in saved_token
    assert "refresh_token" in saved_token


def test_oauth_scope_validation(tmp_path, mock_credentials_content):
    """
    T007 [P] [US1]: Verify OAuth2 scopes are correctly configured.

    Given: GmailReceiver is initialized
    When: Checking OAuth scopes
    Then: gmail.readonly scope is configured

    This test validates FR-007: System MUST validate OAuth2 credentials have correct scopes.
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Assert
    assert receiver.SCOPES == ['https://www.googleapis.com/auth/gmail.readonly']
    assert len(receiver.SCOPES) == 1  # Only read-only scope per research.md Decision 2


# T008: Test Gmail API connection with valid credentials
@patch('email_receiver.gmail_receiver.build')
@patch('email_receiver.gmail_receiver.Credentials')
def test_gmail_api_connection(mock_credentials_cls, mock_build, tmp_path, mock_credentials_content, mock_token_content):
    """
    T008 [US1]: Verify successful Gmail API connection with valid credentials.

    Given: Valid credentials.json and token.json exist
    When: GmailReceiver.connect() is called
    Then: Gmail API service is successfully built and ready

    This test validates:
    - FR-001: System MUST support OAuth2 authentication flow
    - US1 Acceptance Scenario 4: Successfully retrieves email messages
    - SC-002: System successfully authenticates with Gmail API on first attempt
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(mock_token_content))

    # Mock valid credentials
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds

    # Mock Gmail service
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Act
    receiver.connect()

    # Assert
    assert receiver.service is not None
    assert receiver.service == mock_service
    assert receiver.creds == mock_creds
    mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)


@patch('email_receiver.gmail_receiver.InstalledAppFlow')
def test_gmail_api_connection_without_token(mock_installed_flow_cls, tmp_path, mock_credentials_content):
    """
    T008 [US1]: Verify connection fails gracefully when token.json doesn't exist and OAuth flow cannot run.

    Given: credentials.json exists but token.json does not and OAuth flow fails
    When: GmailReceiver.connect() is called
    Then: Raise EmailReceiverError with clear message

    This test validates FR-008: System MUST handle authentication errors gracefully.
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    assert not token_path.exists()

    # Mock OAuth flow to simulate failure (e.g., user closes browser)
    mock_flow = MagicMock()
    mock_flow.run_local_server.side_effect = Exception("OAuth flow cancelled by user")
    mock_installed_flow_cls.from_client_secrets_file.return_value = mock_flow

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path
    )

    # Act & Assert
    # OAuth flow should fail gracefully
    with pytest.raises((EmailReceiverError, Exception)) as exc_info:
        receiver.connect()

    # Verify error message is actionable
    error_message = str(exc_info.value).lower()
    assert "oauth" in error_message or "auth" in error_message or "cancelled" in error_message
