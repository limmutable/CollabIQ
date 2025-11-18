"""
Integration tests for GmailReceiver email retrieval functionality.

Test Coverage:
- T017: Group alias query filter construction
- T019: Group alias email retrieval integration

These tests validate Phase 3 (User Story 2): Handle Group Alias Email Access

To run these tests:
    pytest tests/integration/test_gmail_receiver.py -v
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from email_receiver.gmail_receiver import GmailReceiver


@pytest.fixture
def mock_credentials_content():
    """Mock Google OAuth2 credentials JSON content."""
    return {
        "installed": {
            "client_id": "123456789-abcdefg.apps.googleusercontent.com",
            "project_id": "collabiq-test",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "GOCSPX-mock_secret",
            "redirect_uris": ["http://127.0.0.1:8080"],
        }
    }


@pytest.fixture
def valid_token_content():
    """Mock valid OAuth2 token JSON content."""
    return {
        "token": "ya29.mock_access_token",
        "refresh_token": "1//0gZ1xYz_mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "123456789-abcdefg.apps.googleusercontent.com",
        "client_secret": "GOCSPX-mock_secret",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expiry": (datetime.now(UTC) + timedelta(hours=1)).isoformat() + "Z",
    }


# T017: Test group alias query filter
@patch("email_receiver.gmail_receiver.build")
@patch("email_receiver.gmail_receiver.Credentials")
def test_group_alias_query_filter(
    mock_credentials_cls,
    mock_build,
    tmp_path,
    mock_credentials_content,
    valid_token_content,
):
    """
    T017 [P] [US2]: Verify deliveredto query filter is constructed correctly.

    Given: GmailReceiver is connected
    When: fetch_emails() is called with deliveredto query
    Then: Gmail API is called with correct query string including deliveredto filter

    This test validates:
    - FR-011: System MUST filter emails by deliveredto header (collab@signite.co)
    - US2 Acceptance Scenario 2: Member account retrieves messages using deliveredto: filter
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(valid_token_content))

    # Mock credentials and service
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds

    mock_service = MagicMock()
    mock_messages_list = MagicMock()
    mock_messages_list.execute.return_value = {"messages": []}
    mock_service.users().messages().list.return_value = mock_messages_list
    mock_build.return_value = mock_service

    receiver = GmailReceiver(credentials_path=creds_path, token_path=token_path)
    receiver.connect()

    # Act
    receiver.fetch_emails(query='deliveredto:"collab@signite.co"', max_emails=10)

    # Assert
    # Verify the Gmail API was called with the correct query
    mock_service.users().messages().list.assert_called_once()
    call_kwargs = mock_service.users().messages().list.call_args[1]
    assert "q" in call_kwargs
    assert 'deliveredto:"collab@signite.co"' in call_kwargs["q"]
    assert call_kwargs["userId"] == "me"
    assert call_kwargs["maxResults"] == 10


# T019: Test group alias email retrieval integration
@patch("email_receiver.gmail_receiver.build")
@patch("email_receiver.gmail_receiver.Credentials")
def test_group_alias_email_retrieval_integration(
    mock_credentials_cls,
    mock_build,
    tmp_path,
    mock_credentials_content,
    valid_token_content,
):
    """
    T019 [US2]: Verify emails sent to group alias can be retrieved with deliveredto filter.

    Given: Email sent to collab@signite.co exists in member inbox
    When: fetch_emails() is called with deliveredto:"collab@signite.co" query
    Then: Email is retrieved successfully

    This test validates:
    - US2 Acceptance Scenario 1: Email sent to collab@signite.co appears in member inboxes
    - US2 Acceptance Scenario 2: Member account retrieves messages using deliveredto: filter
    """
    # Arrange
    creds_path = tmp_path / "credentials.json"
    creds_path.write_text(json.dumps(mock_credentials_content))

    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps(valid_token_content))

    # Mock credentials and service
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_credentials_cls.from_authorized_user_file.return_value = mock_creds

    # Mock Gmail API response with a message sent to group alias
    mock_message = {
        "id": "msg123",
        "threadId": "thread123",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "collab@signite.co"},
                {"name": "Subject", "value": "Test collaboration email"},
                {"name": "Date", "value": "Fri, 01 Nov 2025 10:00:00 +0000"},
                {"name": "Message-ID", "value": "<test123@mail.example.com>"},
                {"name": "Delivered-To", "value": "collab@signite.co"},
            ],
            "body": {
                "data": "VGVzdCBlbWFpbCBib2R5"
            },  # base64 encoded "Test email body"
        },
        "internalDate": "1698753600000",
    }

    mock_service = MagicMock()

    # Mock messages().list() to return message IDs
    mock_messages_list = MagicMock()
    mock_messages_list.execute.return_value = {
        "messages": [{"id": "msg123", "threadId": "thread123"}]
    }
    mock_service.users().messages().list.return_value = mock_messages_list

    # Mock messages().get() to return full message
    mock_messages_get = MagicMock()
    mock_messages_get.execute.return_value = mock_message
    mock_service.users().messages().get.return_value = mock_messages_get

    mock_build.return_value = mock_service

    receiver = GmailReceiver(credentials_path=creds_path, token_path=token_path)
    receiver.connect()

    # Act
    emails = receiver.fetch_emails(
        query='deliveredto:"collab@signite.co"', max_emails=10
    )

    # Assert
    assert len(emails) == 1
    email = emails[0]

    # Verify email metadata
    assert email.metadata.message_id == "<test123@mail.example.com>"
    assert email.metadata.sender == "sender@example.com"
    assert email.metadata.subject == "Test collaboration email"

    # Verify the query included deliveredto filter
    call_kwargs = mock_service.users().messages().list.call_args[1]
    assert 'deliveredto:"collab@signite.co"' in call_kwargs["q"]
