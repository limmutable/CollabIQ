"""
Unit tests for GmailSender class.

Tests email sending functionality with mocked Gmail API.
"""

import json
import pytest
from datetime import datetime, UTC, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from email.mime.multipart import MIMEMultipart


@pytest.fixture
def mock_token_manager():
    """Mock TokenManager to avoid file system operations."""
    with patch("email_sender.gmail_sender.TokenManager") as mock_tm:
        yield mock_tm


class TestGmailSenderInit:
    """Tests for GmailSender initialization."""

    def test_init_with_paths(self, tmp_path, mock_token_manager):
        """Test initialization with credential and token paths."""
        from email_sender.gmail_sender import GmailSender

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )

        assert sender.credentials_path == creds_path
        assert sender.token_path == token_path
        assert sender.service is None
        assert sender.creds is None

    def test_scopes_include_send(self, tmp_path, mock_token_manager):
        """Test that SCOPES include gmail.send permission."""
        from email_sender.gmail_sender import GmailSender

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )

        assert "https://www.googleapis.com/auth/gmail.send" in sender.SCOPES
        assert "https://www.googleapis.com/auth/gmail.readonly" in sender.SCOPES


class TestGmailSenderConnect:
    """Tests for GmailSender.connect() method."""

    @pytest.fixture
    def sender(self, tmp_path, mock_token_manager):
        """Create a GmailSender instance with mocked TokenManager."""
        from email_sender.gmail_sender import GmailSender

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        # Create dummy credentials file
        creds_path.write_text(json.dumps({
            "installed": {
                "client_id": "test-client-id",
                "client_secret": "test-secret",
                "redirect_uris": ["http://127.0.0.1:8080"],
            }
        }))

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )
        sender.token_manager = mock_token_manager.return_value
        return sender

    def test_connect_with_valid_cached_token(self, sender):
        """Test connect with valid cached token."""
        # Mock cached token
        mock_token_data = {
            "token": "access_token",
            "refresh_token": "refresh_token",
            "client_id": "client_id",
            "client_secret": "secret",
        }
        sender.token_manager.load_token.return_value = mock_token_data

        # Mock Credentials
        with patch("email_sender.gmail_sender.Credentials") as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_creds_class.from_authorized_user_info.return_value = mock_creds

            with patch("email_sender.gmail_sender.build") as mock_build:
                mock_service = MagicMock()
                mock_build.return_value = mock_service

                sender.connect()

                assert sender.service == mock_service
                assert sender.creds == mock_creds
                mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)

    def test_connect_refreshes_expired_token(self, sender):
        """Test connect refreshes expired token."""
        mock_token_data = {"token": "old_access_token", "refresh_token": "refresh_token"}
        sender.token_manager.load_token.return_value = mock_token_data

        with patch("email_sender.gmail_sender.Credentials") as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "refresh_token"
            mock_creds.to_json.return_value = '{"token": "new_token"}'
            mock_creds_class.from_authorized_user_info.return_value = mock_creds

            with patch("email_sender.gmail_sender.Request"):
                with patch("email_sender.gmail_sender.build") as mock_build:
                    sender.connect()

                    mock_creds.refresh.assert_called_once()
                    sender.token_manager.save_token.assert_called_once()

    def test_connect_raises_on_missing_credentials_file(self, tmp_path, mock_token_manager):
        """Test connect raises error when credentials file is missing."""
        from email_sender.gmail_sender import GmailSender, EmailSenderError

        creds_path = tmp_path / "nonexistent.json"
        token_path = tmp_path / "token.json"

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )
        sender.token_manager = mock_token_manager.return_value
        sender.token_manager.load_token.return_value = None

        with patch("email_sender.gmail_sender.InstalledAppFlow") as mock_flow:
            mock_flow.from_client_secrets_file.side_effect = FileNotFoundError()

            with pytest.raises(EmailSenderError) as exc_info:
                sender.connect()

            assert exc_info.value.code == "AUTHENTICATION_FAILED"


class TestGmailSenderSendEmail:
    """Tests for GmailSender.send_email() method."""

    @pytest.fixture
    def connected_sender(self, tmp_path, mock_token_manager):
        """Create a connected GmailSender with mocked service."""
        from email_sender.gmail_sender import GmailSender

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )

        # Mock connected state
        sender.service = MagicMock()
        sender.creds = MagicMock()
        sender.creds.valid = True

        return sender

    def test_send_email_success(self, connected_sender):
        """Test successful email sending."""
        # Setup mock response
        mock_response = {"id": "msg123", "threadId": "thread123"}
        connected_sender.service.users().messages().send().execute.return_value = mock_response

        result = connected_sender.send_email(
            to=["test@example.com"],
            subject="Test Subject",
            html_body="<p>Test HTML</p>",
            text_body="Test plain text",
        )

        assert result == mock_response
        # Verify send was called (don't check exact call count due to mock chain setup)
        assert connected_sender.service.users().messages().send.called

    def test_send_email_with_multiple_recipients(self, connected_sender):
        """Test sending to multiple recipients."""
        mock_response = {"id": "msg123"}
        connected_sender.service.users().messages().send().execute.return_value = mock_response

        result = connected_sender.send_email(
            to=["user1@example.com", "user2@example.com", "user3@example.com"],
            subject="Multi-recipient Test",
            html_body="<p>Test</p>",
        )

        assert result == mock_response

    def test_send_email_without_text_body(self, connected_sender):
        """Test sending email with only HTML body."""
        mock_response = {"id": "msg123"}
        connected_sender.service.users().messages().send().execute.return_value = mock_response

        result = connected_sender.send_email(
            to=["test@example.com"],
            subject="HTML Only",
            html_body="<p>HTML content only</p>",
        )

        assert result == mock_response

    def test_send_email_raises_when_not_connected(self, tmp_path, mock_token_manager):
        """Test send_email raises error when not connected."""
        from email_sender.gmail_sender import GmailSender, EmailSenderError

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )

        with pytest.raises(EmailSenderError) as exc_info:
            sender.send_email(
                to=["test@example.com"],
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert exc_info.value.code == "CONNECTION_FAILED"

    def test_send_email_handles_auth_error(self, connected_sender):
        """Test handling of authentication errors (401)."""
        from googleapiclient.errors import HttpError
        from email_sender.gmail_sender import EmailSenderError

        mock_resp = Mock()
        mock_resp.status = 401
        http_error = HttpError(mock_resp, b"Unauthorized")

        connected_sender.service.users().messages().send().execute.side_effect = http_error

        with pytest.raises(EmailSenderError) as exc_info:
            connected_sender.send_email(
                to=["test@example.com"],
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert exc_info.value.code == "AUTHENTICATION_FAILED"

    def test_send_email_handles_permission_error(self, connected_sender):
        """Test handling of permission errors (403)."""
        from googleapiclient.errors import HttpError
        from email_sender.gmail_sender import EmailSenderError

        mock_resp = Mock()
        mock_resp.status = 403
        http_error = HttpError(mock_resp, b"Forbidden")

        connected_sender.service.users().messages().send().execute.side_effect = http_error

        with pytest.raises(EmailSenderError) as exc_info:
            connected_sender.send_email(
                to=["test@example.com"],
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert exc_info.value.code == "AUTHENTICATION_FAILED"
        assert "gmail.send scope" in exc_info.value.message


class TestGmailSenderConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.fixture
    def connected_sender(self, tmp_path, mock_token_manager):
        """Create a connected GmailSender."""
        from email_sender.gmail_sender import GmailSender

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        sender = GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )

        sender.service = MagicMock()
        sender.creds = MagicMock()
        sender.creds.valid = True

        return sender

    def test_send_report_email(self, connected_sender):
        """Test send_report_email convenience method."""
        mock_response = {"id": "report123"}
        connected_sender.service.users().messages().send().execute.return_value = mock_response

        result = connected_sender.send_report_email(
            to=["admin@example.com"],
            subject="CollabIQ Daily Report - 2024-01-15",
            html_body="<h1>Daily Report</h1>",
            text_body="Daily Report\n============",
        )

        assert result == mock_response

    def test_send_alert_email(self, connected_sender):
        """Test send_alert_email convenience method."""
        mock_response = {"id": "alert123"}
        connected_sender.service.users().messages().send().execute.return_value = mock_response

        result = connected_sender.send_alert_email(
            to=["admin@example.com"],
            subject="[ALERT] CollabIQ - Critical Error",
            html_body="<h1>Critical Alert</h1>",
            text_body="CRITICAL ALERT",
        )

        assert result == mock_response


class TestGmailSenderHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def sender(self, tmp_path, mock_token_manager):
        """Create a GmailSender instance."""
        from email_sender.gmail_sender import GmailSender

        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"

        return GmailSender(
            credentials_path=creds_path,
            token_path=token_path,
        )

    def test_is_connected_false_when_no_service(self, sender):
        """Test is_connected returns False when no service."""
        assert sender.is_connected() is False

    def test_is_connected_false_when_invalid_creds(self, sender):
        """Test is_connected returns False when creds invalid."""
        sender.service = MagicMock()
        sender.creds = MagicMock()
        sender.creds.valid = False

        assert sender.is_connected() is False

    def test_is_connected_true_when_valid(self, sender):
        """Test is_connected returns True when connected and valid."""
        sender.service = MagicMock()
        sender.creds = MagicMock()
        sender.creds.valid = True

        assert sender.is_connected() is True

    def test_get_token_expiry_returns_none_when_no_creds(self, sender):
        """Test get_token_expiry returns None without credentials."""
        assert sender.get_token_expiry() is None

    def test_get_token_expiry_returns_datetime(self, sender):
        """Test get_token_expiry returns expiry datetime."""
        expiry_time = datetime.now(UTC) + timedelta(hours=1)
        sender.creds = MagicMock()
        sender.creds.expiry = expiry_time

        result = sender.get_token_expiry()
        assert result == expiry_time
