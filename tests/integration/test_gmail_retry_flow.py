"""Integration tests for Gmail API retry flow with exponential backoff.

Tests verify that the @retry_with_backoff decorator correctly handles transient
failures, respects circuit breaker state, and integrates with structured error logging.
"""

import socket
from unittest.mock import Mock, patch

import pytest

from src.email_receiver.gmail_receiver import GmailReceiver
from src.error_handling import gmail_circuit_breaker, CircuitState


class TestGmailRetryFlow:
    """Test Gmail fetch with retry on transient failures."""

    def setup_method(self):
        """Reset circuit breaker before each test."""
        gmail_circuit_breaker.state_obj.state = CircuitState.CLOSED
        gmail_circuit_breaker.state_obj.failure_count = 0

    @patch('src.email_receiver.gmail_receiver.build')
    def test_gmail_fetch_timeout_retry_success(self, mock_build):
        """
        Test that Gmail fetch_emails retries on timeout and eventually succeeds.

        Scenario: T025 - Mock timeout → retry → success
        """
        # Create receiver with mock paths
        receiver = GmailReceiver(
            credentials_path="mock_credentials.json",
            token_path="mock_token.json"
        )

        # Mock service that fails once then succeeds
        mock_service = Mock()
        mock_list = mock_service.users().messages().list
        mock_get = mock_service.users().messages().get

        # First call: timeout
        # Second call: success with empty messages list
        mock_list().execute.side_effect = [
            socket.timeout("Connection timeout"),
            {"messages": []}
        ]

        receiver.service = mock_service

        # Execute - should retry and succeed
        result = receiver.fetch_emails(max_emails=10)

        # Verify retry happened
        assert mock_list().execute.call_count == 2

        # Verify success (circuit breaker should record success)
        assert gmail_circuit_breaker.state_obj.failure_count == 0

        # Verify empty result (no messages)
        assert result == []

    @patch('src.email_receiver.gmail_receiver.build')
    def test_gmail_fetch_all_retries_exhausted(self, mock_build):
        """
        Test that Gmail fetch_emails exhausts retries after 3 attempts.

        Scenario: All 3 attempts fail → exception raised
        """
        # Create receiver with mock paths
        receiver = GmailReceiver(
            credentials_path="mock_credentials.json",
            token_path="mock_token.json"
        )

        # Mock service that always times out
        mock_service = Mock()
        mock_list = mock_service.users().messages().list
        mock_list().execute.side_effect = socket.timeout("Connection timeout")

        receiver.service = mock_service

        # Execute - should exhaust retries and raise exception
        with pytest.raises(socket.timeout):
            receiver.fetch_emails(max_emails=10)

        # Verify retry attempts (should be 3 with GMAIL_RETRY_CONFIG)
        assert mock_list().execute.call_count == 3

    @patch('src.email_receiver.gmail_receiver.build')
    def test_gmail_fetch_no_retry_on_auth_error(self, mock_build):
        """
        Test that Gmail fetch_emails does NOT retry on authentication errors.

        Scenario: 401 auth error → no retry → immediate failure with EmailReceiverError
        """
        from googleapiclient.errors import HttpError
        from src.email_receiver.gmail_receiver import EmailReceiverError

        # Create receiver with mock paths
        receiver = GmailReceiver(
            credentials_path="mock_credentials.json",
            token_path="mock_token.json"
        )

        # Mock service that returns 401
        mock_service = Mock()
        mock_list = mock_service.users().messages().list

        # Create HTTP 401 error
        resp = Mock()
        resp.status = 401
        http_error = HttpError(resp=resp, content=b"Unauthorized")

        mock_list().execute.side_effect = http_error
        receiver.service = mock_service

        # Execute - should fail immediately with EmailReceiverError (wrapped)
        with pytest.raises(EmailReceiverError) as exc_info:
            receiver.fetch_emails(max_emails=10)

        # Verify it's an authentication error
        assert exc_info.value.code == "AUTHENTICATION_FAILED"

        # Verify NO retry happened (only 1 attempt for non-retryable errors)
        assert mock_list().execute.call_count == 1
