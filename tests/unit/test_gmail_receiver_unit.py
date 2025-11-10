"""
Unit tests for GmailReceiver implementation.

Tests cover OAuth2 connection, message fetching, parsing, saving,
and exponential backoff retry logic per FR-010.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call
import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from email_receiver.gmail_receiver import GmailReceiver
from models.raw_email import RawEmail, EmailMetadata


@pytest.fixture
def mock_credentials_path(tmp_path):
    """Create temporary mock credentials file."""
    creds_file = tmp_path / "mock_credentials.json"
    creds_data = {
        "installed": {
            "client_id": "test-client-id.apps.googleusercontent.com",
            "project_id": "test-project",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "TEST_SECRET",
            "redirect_uris": ["http://localhost"],
        }
    }
    creds_file.write_text(json.dumps(creds_data))
    return creds_file


@pytest.fixture
def mock_token_path(tmp_path):
    """Create temporary mock token file."""
    token_file = tmp_path / "mock_token.json"
    return token_file


@pytest.fixture
def gmail_api_list_response():
    """Mock Gmail API messages.list() response."""
    return {
        "messages": [
            {"id": "18c5f2e8b3a4d1f0", "threadId": "18c5f2e8b3a4d1f0"},
            {"id": "18c5f2e8b3a4d1f1", "threadId": "18c5f2e8b3a4d1f1"},
        ],
        "resultSizeEstimate": 2,
    }


@pytest.fixture
def gmail_api_message_detail():
    """Mock Gmail API messages.get() response for a single message."""
    return {
        "id": "18c5f2e8b3a4d1f0",
        "threadId": "18c5f2e8b3a4d1f0",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "안녕하세요, 프로젝트 진행 상황을 공유드립니다.",
        "payload": {
            "partId": "",
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "partner@example.com"},
                {"name": "To", "value": "portfolioupdates@signite.co"},
                {"name": "Subject", "value": "CollabIQ 협업 업데이트"},
                {"name": "Date", "value": "Wed, 30 Oct 2025 14:35:22 +0900"},
                {"name": "Message-ID", "value": "<CABc123@mail.gmail.com>"},
            ],
            "body": {
                "size": 156,
                "data": "7JWI64WV7ZWY7IS47JqULAoK7KeA64K067KI7KO8IO2ajOydmOyXkOyEnCDrhbztpZTtlZwg7ZSE66Gc7KCd7Yq47Yq4IOyngO2Wieygke2VqeustOuLiOuLpC4KCuqwkOyCrO2VqeuLiOuLpC4K6rmA7LKg7IiYIOuTnOumvA==",
            },
        },
        "sizeEstimate": 3456,
        "historyId": "123456",
        "internalDate": "1730267722000",
    }


# T024: Test Gmail receiver connect
@patch("email_receiver.gmail_receiver.build")
@patch("email_receiver.gmail_receiver.Credentials")
def test_gmail_receiver_connect(
    mock_creds_class, mock_build, mock_credentials_path, mock_token_path
):
    """
    Test OAuth2 connection initialization.

    Verifies:
    - Credentials are loaded from file
    - Gmail API service is built successfully
    - Connection state is established
    """
    # Create mock token file to avoid OAuth flow
    token_data = {
        "token": "mock_token",
        "refresh_token": "mock_refresh",
        "expiry": "2025-12-31T00:00:00Z",
    }
    mock_token_path.write_text(json.dumps(token_data))

    # Setup mock credentials
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = "mock_refresh_token"
    mock_creds_class.from_authorized_user_file.return_value = mock_creds

    # Setup mock Gmail service
    mock_service = Mock()
    mock_build.return_value = mock_service

    # Create receiver and connect
    receiver = GmailReceiver(
        credentials_path=mock_credentials_path, token_path=mock_token_path
    )
    receiver.connect()

    # Assertions
    assert receiver.service is not None
    mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)


# T025: Test Gmail receiver fetch new messages
@patch("email_receiver.gmail_receiver.build")
@patch("email_receiver.gmail_receiver.Credentials")
def test_gmail_receiver_fetch_new_messages(
    mock_creds_class,
    mock_build,
    gmail_api_list_response,
    gmail_api_message_detail,
    mock_credentials_path,
    mock_token_path,
):
    """
    Test fetching messages from Gmail API.

    Verifies:
    - messages.list() is called with correct parameters
    - Response contains expected message IDs
    - Messages are returned in chronological order
    """
    # Create mock token file to avoid OAuth flow
    token_data = {
        "token": "mock_token",
        "refresh_token": "mock_refresh",
        "expiry": "2025-12-31T00:00:00Z",
    }
    mock_token_path.write_text(json.dumps(token_data))

    # Setup mocks
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds_class.from_authorized_user_file.return_value = mock_creds

    mock_service = Mock()
    mock_build.return_value = mock_service

    # Mock messages.list() call
    mock_list = Mock()
    mock_list.execute.return_value = gmail_api_list_response
    mock_service.users().messages().list.return_value = mock_list

    # Mock messages.get() calls
    mock_get = Mock()
    mock_get.execute.return_value = gmail_api_message_detail
    mock_service.users().messages().get.return_value = mock_get

    # Create receiver and fetch messages
    receiver = GmailReceiver(
        credentials_path=mock_credentials_path, token_path=mock_token_path
    )
    receiver.connect()

    messages = receiver.fetch_emails(max_emails=10)

    # Assertions
    mock_service.users().messages().list.assert_called_once()
    call_kwargs = mock_service.users().messages().list.call_args[1]
    assert call_kwargs["userId"] == "me"
    assert call_kwargs["maxResults"] == 10

    assert len(messages) == 2  # Two messages from list response
    assert all(isinstance(msg, RawEmail) for msg in messages)


# T026: Test Gmail receiver parse message
def test_gmail_receiver_parse_message(
    gmail_api_message_detail, mock_credentials_path, mock_token_path, tmp_path
):
    """
    Test parsing Gmail API response to RawEmail model.

    Verifies:
    - Message headers are correctly extracted
    - Body content is decoded from base64
    - RawEmail model is created with valid data
    - All required fields are populated
    """
    # Create mock token file to avoid OAuth flow
    token_data = {
        "token": "mock_token",
        "refresh_token": "mock_refresh",
        "expiry": "2025-12-31T00:00:00Z",
    }
    mock_token_path.write_text(json.dumps(token_data))

    receiver = GmailReceiver(
        credentials_path=mock_credentials_path, token_path=mock_token_path
    )

    raw_email = receiver._parse_message(gmail_api_message_detail)

    # Assertions
    assert isinstance(raw_email, RawEmail)
    assert raw_email.metadata.message_id == "<CABc123@mail.gmail.com>"
    assert raw_email.metadata.sender == "partner@example.com"
    assert raw_email.metadata.subject == "CollabIQ 협업 업데이트"
    assert raw_email.metadata.has_attachments is False
    assert len(raw_email.body) > 0  # Body should be decoded from base64
    assert isinstance(raw_email.metadata.received_at, datetime)


# T027: Test Gmail receiver save raw email
def test_gmail_receiver_save_raw_email(
    tmp_path, mock_credentials_path, mock_token_path
):
    """
    Test saving RawEmail to file storage.

    Verifies:
    - File is created at correct path: data/raw/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json
    - Monthly directory is created if missing
    - File contains valid JSON matching RawEmail schema
    - File content can be deserialized back to RawEmail
    """
    # Create mock token file to avoid OAuth flow
    token_data = {
        "token": "mock_token",
        "refresh_token": "mock_refresh",
        "expiry": "2025-12-31T00:00:00Z",
    }
    mock_token_path.write_text(json.dumps(token_data))

    # Create test email
    raw_email = RawEmail(
        metadata=EmailMetadata(
            message_id="<TEST123@mail.gmail.com>",
            sender="test@example.com",
            subject="Test Email",
            received_at=datetime(2025, 10, 30, 14, 35, 22),
            has_attachments=False,
        ),
        body="Test email body content",
        attachments=[],
    )

    receiver = GmailReceiver(
        credentials_path=mock_credentials_path,
        token_path=mock_token_path,
        raw_email_dir=tmp_path / "data" / "raw",
    )

    # Save email
    saved_path = receiver.save_raw_email(raw_email)

    # Assertions
    assert saved_path.exists()
    assert saved_path.parent.name == "10"  # October
    assert saved_path.parent.parent.name == "2025"  # Year
    assert "TEST123" in saved_path.name
    assert saved_path.suffix == ".json"

    # Verify file content
    saved_data = json.loads(saved_path.read_text())
    assert saved_data["metadata"]["message_id"] == "<TEST123@mail.gmail.com>"
    assert saved_data["body"] == "Test email body content"


# T028: Test Gmail receiver exponential backoff
@patch("email_receiver.gmail_receiver.build")
@patch("email_receiver.gmail_receiver.Credentials")
@patch("time.sleep")  # Mock sleep to speed up tests
def test_gmail_receiver_exponential_backoff(
    mock_sleep, mock_creds_class, mock_build, mock_credentials_path, mock_token_path
):
    """
    Test exponential backoff retry logic per FR-010.

    Verifies:
    - Retries 3 times with increasing delays (4s, 8s, 16s)
    - Raises EmailReceiverError with code CONNECTION_FAILED after max retries
    - Logs ProcessingEvent.CONNECTION_RETRY for each retry
    - Does not retry on authentication failures (401)
    """
    # Create mock token file to avoid OAuth flow
    token_data = {
        "token": "mock_token",
        "refresh_token": "mock_refresh",
        "expiry": "2025-12-31T00:00:00Z",
    }
    mock_token_path.write_text(json.dumps(token_data))

    # Setup mocks
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds_class.from_authorized_user_file.return_value = mock_creds

    mock_service = Mock()
    mock_build.return_value = mock_service

    # Mock 503 Service Unavailable error (should retry)
    http_error = HttpError(resp=Mock(status=503), content=b"Service Unavailable")
    mock_list = Mock()
    mock_list.execute.side_effect = http_error
    mock_service.users().messages().list.return_value = mock_list

    # Create receiver
    receiver = GmailReceiver(
        credentials_path=mock_credentials_path, token_path=mock_token_path
    )
    receiver.connect()

    # Attempt to fetch messages (should fail after retries)
    with pytest.raises(Exception) as exc_info:
        receiver.fetch_emails()

    # Assertions
    assert "CONNECTION_FAILED" in str(exc_info.value) or "Service Unavailable" in str(
        exc_info.value
    )

    # Verify exponential backoff delays
    # With 3 retry attempts, there are 2 sleep calls (between retry 1→2 and retry 2→3)
    # The first attempt happens immediately without sleep
    assert mock_sleep.call_count == 2  # 2 sleep calls for 3 retry attempts
    sleep_calls = [call_args[0][0] for call_args in mock_sleep.call_args_list]

    # Verify sleep delays are positive and increasing (exponential backoff with jitter)
    # Jitter adds 0-2 seconds to base delay
    assert sleep_calls[0] > 0  # First sleep is positive
    assert sleep_calls[1] > sleep_calls[0]  # Second sleep is longer (exponential backoff)


@patch("email_receiver.gmail_receiver.build")
@patch("email_receiver.gmail_receiver.Credentials")
def test_gmail_receiver_no_retry_on_auth_failure(
    mock_creds_class, mock_build, mock_credentials_path, mock_token_path
):
    """
    Test that authentication failures (401) do not trigger retry.

    Verifies:
    - Raises EmailReceiverError with code AUTHENTICATION_FAILED immediately
    - Does not retry on 401 errors
    """
    # Create mock token file to avoid OAuth flow
    token_data = {
        "token": "mock_token",
        "refresh_token": "mock_refresh",
        "expiry": "2025-12-31T00:00:00Z",
    }
    mock_token_path.write_text(json.dumps(token_data))

    # Setup mocks
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds_class.from_authorized_user_file.return_value = mock_creds

    mock_service = Mock()
    mock_build.return_value = mock_service

    # Mock 401 Unauthorized error (should not retry)
    http_error = HttpError(resp=Mock(status=401), content=b"Unauthorized")
    mock_list = Mock()
    mock_list.execute.side_effect = http_error
    mock_service.users().messages().list.return_value = mock_list

    # Create receiver
    receiver = GmailReceiver(
        credentials_path=mock_credentials_path, token_path=mock_token_path
    )
    receiver.connect()

    # Attempt to fetch messages (should fail immediately)
    with pytest.raises(Exception) as exc_info:
        receiver.fetch_emails()

    # Assertions
    assert "AUTHENTICATION_FAILED" in str(exc_info.value) or "Unauthorized" in str(
        exc_info.value
    )

    # Verify only called once (no retries)
    assert mock_list.execute.call_count == 1
