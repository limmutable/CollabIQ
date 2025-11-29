"""
Gmail API implementation for sending emails.

This module provides the GmailSender class that sends emails via Gmail API
using OAuth2 authentication, reusing the same credentials as GmailReceiver.
"""

import base64
import json
import logging
from datetime import datetime, UTC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from email_receiver.token_manager import TokenManager

logger = logging.getLogger(__name__)


class EmailSenderError(Exception):
    """Custom exception for EmailSender errors."""

    def __init__(self, code: str, message: str, retry_count: int = 0, **kwargs):
        self.code = code
        self.message = message
        self.retry_count = retry_count
        self.details = kwargs
        super().__init__(f"{code}: {message}")


class GmailSender:
    """
    Gmail API implementation for sending emails.

    This implementation uses the Gmail API to send emails with OAuth2
    authentication. It shares credentials with GmailReceiver but requires
    additional 'gmail.send' scope.

    Attributes:
        credentials_path: Path to OAuth2 credentials JSON file
        token_path: Path to store/load OAuth2 access/refresh tokens
        service: Gmail API service instance
    """

    # Requires both read and send scopes
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
    ):
        """
        Initialize GmailSender.

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to store OAuth2 access/refresh tokens
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.service = None
        self.creds = None

        # Use TokenManager for consistent token handling
        self.token_manager = TokenManager(self.token_path)

    def connect(self) -> None:
        """
        Establish OAuth2 connection to Gmail API with send permissions.

        This method handles the OAuth2 flow:
        1. Load existing token if available
        2. Refresh token if expired
        3. Run OAuth2 flow if no valid token (requires send scope)
        4. Build Gmail API service

        Raises:
            EmailSenderError: With code AUTHENTICATION_FAILED if OAuth2 fails
        """
        try:
            # Load existing token via TokenManager
            token_data = self.token_manager.load_token()
            if token_data:
                self.creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                logger.info(f"Loaded existing token from {self.token_path}")

            # Refresh expired token or run OAuth flow
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired token")
                    self.creds.refresh(Request())
                else:
                    logger.info("Running OAuth2 flow for send permissions")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.SCOPES
                    )
                    # Use port 8080 per research.md Decision 4
                    self.creds = flow.run_local_server(port=8080)

                # Save token for next run via TokenManager
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                self.token_manager.save_token(json.loads(self.creds.to_json()))
                logger.info(f"Saved token to {self.token_path}")

            # Build Gmail API service
            self.service = build("gmail", "v1", credentials=self.creds)
            logger.info("Successfully connected to Gmail API for sending")

        except FileNotFoundError as e:
            logger.error(f"OAuth2 credentials file not found: {e}")
            raise EmailSenderError(
                code="AUTHENTICATION_FAILED",
                message=(
                    f"Gmail API credentials file not found at {self.credentials_path}. "
                    f"Please follow the setup guide at docs/setup/gmail-oauth-setup.md"
                ),
                retry_count=0,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "redirect_uri_mismatch" in error_str or "redirect uri" in error_str:
                message = (
                    "OAuth2 redirect URI mismatch. "
                    "Ensure 'http://127.0.0.1:8080' is in authorized redirect URIs."
                )
            elif "invalid_grant" in error_str or "token" in error_str:
                message = (
                    f"OAuth2 token is invalid or expired. "
                    f"Delete {self.token_path} and re-run authentication."
                )
            elif "access_denied" in error_str or "insufficient" in error_str:
                message = (
                    "OAuth2 access denied. "
                    "Ensure the OAuth2 credentials have 'gmail.send' scope enabled."
                )
            else:
                message = f"Failed to authenticate with Gmail API: {str(e)}"

            logger.error(f"OAuth2 authentication failed: {message}")
            raise EmailSenderError(
                code="AUTHENTICATION_FAILED", message=message, retry_count=0
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(HttpError),
        reraise=True,
    )
    def send_email(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> dict:
        """
        Send an email via Gmail API.

        Creates a multipart email with HTML and plain text alternatives,
        then sends it using the Gmail API with retry on transient errors.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            html_body: HTML content of the email
            text_body: Plain text alternative (optional, derived from HTML if not provided)
            sender: Sender email address (optional, uses authenticated account if not provided)

        Returns:
            Gmail API response dict containing message ID

        Raises:
            EmailSenderError: With code SEND_FAILED if sending fails after retries
        """
        if not self.service:
            raise EmailSenderError(
                code="CONNECTION_FAILED",
                message="Gmail service not connected. Call connect() first.",
                retry_count=0,
            )

        try:
            # Create multipart message
            message = MIMEMultipart("alternative")
            message["To"] = ", ".join(to)
            message["Subject"] = subject

            if sender:
                message["From"] = sender

            # Add plain text part (fallback)
            if text_body:
                text_part = MIMEText(text_body, "plain", "utf-8")
                message.attach(text_part)

            # Add HTML part (preferred)
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            # Send via Gmail API
            logger.info(f"Sending email to {to} with subject: {subject}")
            result = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            logger.info(f"Successfully sent email, message ID: {result.get('id')}")
            return result

        except HttpError as e:
            if e.resp.status == 401:
                logger.error("Authentication failed (401)")
                raise EmailSenderError(
                    code="AUTHENTICATION_FAILED",
                    message="Gmail OAuth token expired or invalid",
                    retry_count=0,
                ) from e
            elif e.resp.status == 403:
                logger.error("Permission denied (403)")
                raise EmailSenderError(
                    code="AUTHENTICATION_FAILED",
                    message="Insufficient permissions. Ensure gmail.send scope is enabled.",
                    retry_count=0,
                ) from e
            else:
                # For retryable errors (429, 5xx), let tenacity handle retry
                raise

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise EmailSenderError(
                code="SEND_FAILED",
                message=f"Failed to send email: {str(e)}",
                retry_count=0,
            )

    def send_report_email(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str,
    ) -> dict:
        """
        Send an admin report email.

        Convenience method for sending admin reports with both HTML and
        plain text versions.

        Args:
            to: List of recipient email addresses
            subject: Email subject line (e.g., "CollabIQ Daily Report - 2024-01-15")
            html_body: HTML formatted report
            text_body: Plain text formatted report

        Returns:
            Gmail API response dict containing message ID

        Raises:
            EmailSenderError: If sending fails
        """
        return self.send_email(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    def send_alert_email(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str,
    ) -> dict:
        """
        Send a critical alert email.

        Convenience method for sending time-sensitive alerts.

        Args:
            to: List of recipient email addresses
            subject: Email subject line (e.g., "[ALERT] CollabIQ - Critical Error")
            html_body: HTML formatted alert
            text_body: Plain text formatted alert

        Returns:
            Gmail API response dict containing message ID

        Raises:
            EmailSenderError: If sending fails
        """
        return self.send_email(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    def is_connected(self) -> bool:
        """Check if service is connected and authenticated."""
        return self.service is not None and self.creds is not None and self.creds.valid

    def get_token_expiry(self) -> Optional[datetime]:
        """
        Get the OAuth token expiry time.

        Returns:
            Token expiry datetime or None if no valid credentials
        """
        if self.creds and self.creds.expiry:
            return self.creds.expiry
        return None
