"""
Gmail API implementation of EmailReceiver.

This module provides the GmailReceiver class that connects to Gmail API
using OAuth2 and retrieves emails from portfolioupdates@signite.co inbox.
"""

import base64
import json
import logging
from datetime import datetime, UTC
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import ValidationError

try:
    from ..models.raw_email import EmailAttachment, EmailMetadata, RawEmail
    from ..models.duplicate_tracker import DuplicateTracker
    from .base import EmailReceiver
    from ..error_handling.structured_logger import logger as error_logger
    from ..error_handling.models import ErrorRecord, ErrorSeverity, ErrorCategory
    from ..error_handling import (
        retry_with_backoff,
        GMAIL_RETRY_CONFIG,
        gmail_circuit_breaker,
    )
except ImportError:
    from models.raw_email import EmailMetadata, RawEmail
    from models.duplicate_tracker import DuplicateTracker
    from email_receiver.base import EmailReceiver
    from error_handling.structured_logger import logger as error_logger
    from error_handling.models import ErrorRecord, ErrorSeverity, ErrorCategory
    from error_handling import retry_with_backoff, GMAIL_RETRY_CONFIG

# Configure logging
logger = logging.getLogger(__name__)


class EmailReceiverError(Exception):
    """Custom exception for EmailReceiver errors."""

    def __init__(self, code: str, message: str, retry_count: int = 0, **kwargs):
        self.code = code
        self.message = message
        self.retry_count = retry_count
        self.details = kwargs
        super().__init__(f"{code}: {message}")


class GmailReceiver(EmailReceiver):
    """
    Gmail API implementation with OAuth2 authentication.

    This implementation uses the Gmail API to retrieve emails from the inbox
    and supports exponential backoff retry logic per FR-010.

    Attributes:
        credentials_path: Path to OAuth2 credentials JSON file
        token_path: Path to store/load OAuth2 access/refresh tokens
        raw_email_dir: Directory for saving raw email JSON files
        scopes: Gmail API OAuth scopes
        service: Gmail API service instance
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        raw_email_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None,
    ):
        """
        Initialize GmailReceiver.

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to store OAuth2 access/refresh tokens
            raw_email_dir: Directory for raw email storage (default: data/raw)
            metadata_dir: Directory for metadata storage (default: data/metadata)
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.raw_email_dir = Path(raw_email_dir or "data/raw")
        self.metadata_dir = Path(metadata_dir or "data/metadata")
        self.service = None
        self.creds = None
        
        # Initialize TokenManager
        # Import here to avoid circular imports if necessary, or assume it's available
        from .token_manager import TokenManager
        self.token_manager = TokenManager(self.token_path)

    def connect(self) -> None:
        """
        Establish OAuth2 connection to Gmail API (T030).

        This method handles the OAuth2 flow:
        1. Load existing token if available
        2. Refresh token if expired
        3. Run OAuth2 flow if no valid token
        4. Build Gmail API service

        Raises:
            EmailReceiverError: With code AUTHENTICATION_FAILED if OAuth2 fails
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
                    logger.info("Running OAuth2 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.SCOPES
                    )
                    # Use port 8080 per research.md Decision 4 (http://127.0.0.1:8080)
                    # This must match the redirect URI configured in Google Cloud Console
                    self.creds = flow.run_local_server(port=8080)

                # Save token for next run via TokenManager
                try:
                    self.token_path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    if e.errno == 30:  # Read-only file system
                        pass  # Directory likely exists, ignore
                    else:
                        logger.warning(f"Failed to create token directory: {e}")

                self.token_manager.save_token(json.loads(self.creds.to_json()))
                logger.info(f"Saved token to {self.token_path}")

            # Build Gmail API service
            self.service = build("gmail", "v1", credentials=self.creds)
            logger.info("Successfully connected to Gmail API")

        except FileNotFoundError as e:
            logger.error(f"OAuth2 credentials file not found: {e}")
            raise EmailReceiverError(
                code="AUTHENTICATION_FAILED",
                message=(
                    f"Gmail API credentials file not found at {self.credentials_path}. "
                    f"Please follow the setup guide at docs/setup/gmail-oauth-setup.md to: "
                    f"1) Create OAuth2 credentials in Google Cloud Console, "
                    f"2) Download credentials.json, "
                    f"3) Place it at the path specified in GOOGLE_CREDENTIALS_PATH or GMAIL_CREDENTIALS_PATH environment variable."
                ),
                retry_count=0,
            )
        except Exception as e:
            error_str = str(e).lower()
            # Provide specific guidance based on error type
            if "redirect_uri_mismatch" in error_str or "redirect uri" in error_str:
                message = (
                    "OAuth2 redirect URI mismatch. "
                    "Ensure your Google Cloud Console OAuth2 client has 'http://127.0.0.1:8080' "
                    "in the authorized redirect URIs list. See docs/setup/troubleshooting-gmail-api.md for details."
                )
            elif "invalid_grant" in error_str or "token" in error_str:
                message = (
                    f"OAuth2 token is invalid or expired. "
                    f"Delete {self.token_path} and re-run authentication to refresh your tokens. "
                    f"If this persists, check that your OAuth2 consent screen is configured correctly."
                )
            elif "access_denied" in error_str or "insufficient" in error_str:
                message = (
                    "OAuth2 access denied or insufficient permissions. "
                    "Ensure the OAuth2 credentials have 'gmail.readonly' scope enabled. "
                    "Check your Google Cloud Console OAuth consent screen configuration."
                )
            else:
                message = (
                    f"Failed to authenticate with Gmail API: {str(e)}. "
                    f"Check that: 1) credentials.json is valid, "
                    f"2) OAuth2 consent screen is configured, "
                    f"3) Gmail API is enabled in Google Cloud Console. "
                    f"See docs/setup/troubleshooting-gmail-api.md for common solutions."
                )

            logger.error(f"OAuth2 authentication failed: {message}")
            raise EmailReceiverError(
                code="AUTHENTICATION_FAILED", message=message, retry_count=0
            )

    @retry_with_backoff(GMAIL_RETRY_CONFIG)
    def fetch_emails(
        self,
        since: Optional[datetime] = None,
        max_emails: int = 100,
        query: Optional[str] = None,
    ) -> List[RawEmail]:
        """
        Retrieve unprocessed emails from Gmail inbox (T031).

        Implements exponential backoff retry logic per FR-010 via @retry_with_backoff decorator.
        The decorator handles all retry logic, error classification, and circuit breaker integration.

        Args:
            since: Only retrieve emails after this timestamp
            max_emails: Maximum number of emails to retrieve (1-500)
            query: Custom Gmail search query (T020). If None, defaults to 'to:collab@signite.co'

        Returns:
            List of RawEmail objects in chronological order (oldest first)

        Raises:
            HttpError: Native Gmail API errors (handled by retry decorator)
            EmailReceiverError: Application-level errors after retry exhaustion
        """
        if not self.service:
            raise EmailReceiverError(
                code="CONNECTION_FAILED",
                message="Gmail service not connected. Call connect() first.",
                retry_count=0,
            )

        try:
            # Build query (T020, T021, T022)
            if query is None:
                # Default query filters emails sent to group alias (T022)
                # Using 'to:' operator which works reliably with Gmail API
                # Explicitly exclude TRASH and SPAM to avoid processing deleted messages
                # Note: Gmail API default excludes trash/spam but Google Groups forwarded
                # emails may have different label behavior
                query_str = "to:collab@signite.co -in:trash -in:spam"
            else:
                # For custom queries, also exclude trash and spam unless explicitly included
                if "-in:trash" not in query.lower() and "in:trash" not in query.lower():
                    query = f"{query} -in:trash"
                if "-in:spam" not in query.lower() and "in:spam" not in query.lower():
                    query = f"{query} -in:spam"
                query_str = query

            # Add timestamp filter if provided
            if since:
                query_str += f" after:{int(since.timestamp())}"

            # Fetch message list
            # includeSpamTrash=False is the default, but we set it explicitly for clarity
            logger.info(f"Fetching emails with query: {query_str}, max: {max_emails}")
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query_str,
                    maxResults=max_emails,
                    includeSpamTrash=False,
                )
                .execute()
            )

            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} messages")

            if not messages:
                return []

            # Fetch full message details
            raw_emails = []
            for msg in messages:
                try:
                    msg_detail = (
                        self.service.users()
                        .messages()
                        .get(userId="me", id=msg["id"], format="full")
                        .execute()
                    )

                    raw_email = self._parse_message(msg_detail)
                    raw_emails.append(raw_email)

                except ValidationError as e:
                    # Log validation error with field-level details and continue processing
                    logger.warning(
                        f"Validation error for message {msg['id']}, skipping: {e}"
                    )
                    error_record = ErrorRecord(
                        timestamp=datetime.now(UTC),
                        severity=ErrorSeverity.WARNING,
                        category=ErrorCategory.PERMANENT,
                        message=f"Email validation failed for message {msg['id']}",
                        error_type="ValidationError",
                        stack_trace=str(e),
                        context={
                            "message_id": msg["id"],
                            "operation": "fetch_emails",
                            "validation_errors": e.errors()
                            if hasattr(e, "errors")
                            else str(e),
                        },
                        retry_count=0,
                    )
                    error_logger.log_error(error_record)
                    continue

                except Exception as e:
                    logger.error(f"Failed to fetch message {msg['id']}: {e}")
                    continue

            # Sort by received_at (oldest first)
            raw_emails.sort(key=lambda e: e.metadata.received_at)
            logger.info(f"Successfully fetched {len(raw_emails)} emails")
            return raw_emails

        except HttpError as e:
            # Let the decorator handle retries for transient errors
            # Only wrap in EmailReceiverError for specific non-retryable cases
            if e.resp.status == 401:
                logger.error("Authentication failed (401)")
                raise EmailReceiverError(
                    code="AUTHENTICATION_FAILED",
                    message="Gmail OAuth token expired or invalid",
                    retry_count=0,
                ) from e
            elif e.resp.status == 403:
                logger.error("Permission denied (403)")
                raise EmailReceiverError(
                    code="AUTHENTICATION_FAILED",
                    message="Insufficient permissions to access Gmail API",
                    retry_count=0,
                ) from e
            elif e.resp.status == 404:
                logger.error("Resource not found (404)")
                raise EmailReceiverError(
                    code="INVALID_RESPONSE",
                    message="Gmail resource not found",
                    retry_count=0,
                ) from e
            else:
                # For retryable errors (429, 5xx), let the decorator handle it
                # by re-raising the original exception
                raise

    def _parse_message(self, msg_detail: dict) -> RawEmail:
        """
        Parse Gmail API message to RawEmail model (T032).

        Args:
            msg_detail: Gmail API message detail response

        Returns:
            RawEmail object with parsed metadata and body

        Raises:
            EmailReceiverError: With code VALIDATION_FAILED if parsing fails
        """
        try:
            payload = msg_detail.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

            # Extract metadata
            message_id = headers.get("Message-ID", f"<{msg_detail['id']}@gmail.com>")
            sender = headers.get("From", "unknown@unknown.com")
            subject = headers.get("Subject", "(No Subject)")
            date_str = headers.get("Date", "")

            # Parse received date
            try:
                received_at = (
                    parsedate_to_datetime(date_str) if date_str else datetime.now(UTC)
                )
            except Exception:
                received_at = datetime.now(UTC)

            # Extract body
            body = self._extract_body(payload)

            # Check for attachments
            has_attachments = self._has_attachments(payload)
            attachments = []  # TODO: Implement attachment parsing in later phase

            # Create RawEmail
            metadata = EmailMetadata(
                message_id=message_id,
                internal_id=msg_detail.get("id"),
                sender=sender,
                subject=subject,
                received_at=received_at,
                has_attachments=has_attachments,
            )

            raw_email = RawEmail(metadata=metadata, body=body, attachments=attachments)

            logger.debug(f"Parsed message: {message_id}")
            return raw_email

        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            raise EmailReceiverError(
                code="VALIDATION_FAILED",
                message=f"Failed to parse Gmail message: {str(e)}",
                retry_count=0,
            )

    def _extract_body(self, payload: dict) -> str:
        """
        Extract email body from Gmail API payload.

        Handles both plain text and multipart messages.

        Args:
            payload: Gmail API message payload

        Returns:
            Decoded email body text
        """
        # Single-part message
        if "body" in payload and payload["body"].get("data"):
            return self._decode_base64(payload["body"]["data"])

        # Multipart message - find text/plain part
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")

                # Prefer text/plain
                if mime_type == "text/plain" and part.get("body", {}).get("data"):
                    return self._decode_base64(part["body"]["data"])

            # Fallback to text/html
            for part in payload["parts"]:
                if part.get("mimeType") == "text/html" and part.get("body", {}).get(
                    "data"
                ):
                    return self._decode_base64(part["body"]["data"])

            # Nested parts
            for part in payload["parts"]:
                if "parts" in part:
                    body = self._extract_body(part)
                    if body:
                        return body

        return ""

    def _decode_base64(self, data: str) -> str:
        """Decode base64url-encoded string with fallback encoding."""
        try:
            # Gmail uses base64url encoding (RFC 4648)
            decoded = base64.urlsafe_b64decode(data)

            # Try UTF-8 first
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1 (never fails but may not be semantically correct)
                logger.warning("UTF-8 decode failed, falling back to latin-1")
                error_record = ErrorRecord(
                    timestamp=datetime.now(UTC),
                    severity=ErrorSeverity.WARNING,
                    category=ErrorCategory.PERMANENT,
                    message="Email encoding issue: UTF-8 decode failed, using fallback",
                    error_type="UnicodeDecodeError",
                    stack_trace=None,
                    context={
                        "operation": "_decode_base64",
                        "encoding": "latin-1 fallback",
                    },
                    retry_count=0,
                )
                error_logger.log_error(error_record)
                return decoded.decode("latin-1", errors="replace")

        except Exception as e:
            logger.warning(f"Failed to decode base64 data: {e}")
            error_record = ErrorRecord(
                timestamp=datetime.now(UTC),
                severity=ErrorSeverity.WARNING,
                category=ErrorCategory.PERMANENT,
                message=f"Base64 decode failed: {str(e)}",
                error_type=type(e).__name__,
                stack_trace=str(e),
                context={"operation": "_decode_base64"},
                retry_count=0,
            )
            error_logger.log_error(error_record)
            return ""

    def _has_attachments(self, payload: dict) -> bool:
        """Check if message has attachments."""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    return True
                if "parts" in part:
                    if self._has_attachments(part):
                        return True
        return False

    def save_raw_email(self, email: RawEmail) -> Path:
        """
        Save RawEmail to file storage (T033).

        Creates monthly directories automatically:
        data/raw/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json

        Args:
            email: RawEmail object to save

        Returns:
            Path to saved JSON file

        Raises:
            EmailReceiverError: With codes STORAGE_FAILED or VALIDATION_FAILED
        """
        try:
            # Create monthly directory structure
            received_date = email.metadata.received_at
            monthly_dir = (
                self.raw_email_dir
                / str(received_date.year)
                / f"{received_date.month:02d}"
            )
            monthly_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename: YYYYMMDD_HHMMSS_{clean_message_id}.json
            timestamp = received_date.strftime("%Y%m%d_%H%M%S")
            clean_id = (
                email.metadata.message_id.strip("<>")
                .replace("@", "_")
                .replace(".", "_")[:50]
            )
            filename = f"{timestamp}_{clean_id}.json"
            file_path = monthly_dir / filename

            # Serialize to JSON
            email_dict = {
                "metadata": {
                    "message_id": email.metadata.message_id,
                    "sender": email.metadata.sender,
                    "subject": email.metadata.subject,
                    "received_at": email.metadata.received_at.isoformat(),
                    "retrieved_at": email.metadata.retrieved_at.isoformat(),
                    "has_attachments": email.metadata.has_attachments,
                },
                "body": email.body,
                "attachments": [
                    {
                        "filename": att.filename,
                        "content_type": att.content_type,
                        "size_bytes": att.size_bytes,
                        "storage_path": str(att.storage_path)
                        if att.storage_path
                        else None,
                    }
                    for att in email.attachments
                ],
            }

            # Write to file
            file_path.write_text(json.dumps(email_dict, indent=2, ensure_ascii=False))
            logger.info(f"Saved raw email to {file_path}")

            return file_path

        except Exception as e:
            logger.error(f"Failed to save raw email: {e}")
            raise EmailReceiverError(
                code="STORAGE_FAILED",
                message=f"Failed to save email to file storage: {str(e)}",
                retry_count=0,
            )

    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if email has been processed using DuplicateTracker.

        Loads the tracker from data/metadata/processed_ids.json and checks
        if the message ID exists in the processed set.

        Args:
            message_id: Email message ID to check

        Returns:
            True if message has been processed, False otherwise

        Raises:
            EmailReceiverError: With code TRACKER_LOAD_FAILED if tracker cannot be loaded
        """
        try:
            tracker_path = self.metadata_dir / "processed_ids.json"
            tracker = DuplicateTracker.load(tracker_path)
            is_dup = tracker.is_duplicate(message_id)

            if is_dup:
                logger.debug(f"Duplicate detected: {message_id}")
            else:
                logger.debug(f"New message: {message_id}")

            return is_dup

        except ValueError as e:
            logger.error(f"Failed to load duplicate tracker: {e}")
            raise EmailReceiverError(
                code="TRACKER_LOAD_FAILED",
                message=f"Failed to load duplicate tracker: {str(e)}",
                retry_count=0,
            )
        except Exception as e:
            logger.error(f"Unexpected error checking duplicate: {e}")
            raise EmailReceiverError(
                code="TRACKER_LOAD_FAILED",
                message=f"Unexpected error checking duplicate: {str(e)}",
                retry_count=0,
            )

    def mark_processed(self, message_id: str) -> None:
        """
        Mark email as processed using DuplicateTracker.

        Adds the message ID to the processed set and saves the tracker
        to data/metadata/processed_ids.json.

        Args:
            message_id: Email message ID to mark as processed

        Raises:
            EmailReceiverError: With code TRACKER_SAVE_FAILED if tracker cannot be saved
        """
        try:
            tracker_path = self.metadata_dir / "processed_ids.json"

            # Load existing tracker or create new one
            tracker = DuplicateTracker.load(tracker_path)

            # Mark as processed
            tracker.mark_processed(message_id)

            # Save updated tracker
            tracker.save(tracker_path)

            logger.info(f"Marked as processed: {message_id} (total: {tracker.count()})")

        except ValueError as e:
            logger.error(f"Failed to load duplicate tracker: {e}")
            raise EmailReceiverError(
                code="TRACKER_SAVE_FAILED",
                message=f"Failed to load duplicate tracker: {str(e)}",
                retry_count=0,
            )
        except OSError as e:
            logger.error(f"Failed to save duplicate tracker: {e}")
            raise EmailReceiverError(
                code="TRACKER_SAVE_FAILED",
                message=f"Failed to save duplicate tracker: {str(e)}",
                retry_count=0,
            )
        except Exception as e:
            logger.error(f"Unexpected error marking as processed: {e}")
            raise EmailReceiverError(
                code="TRACKER_SAVE_FAILED",
                message=f"Unexpected error marking as processed: {str(e)}",
                retry_count=0,
            )
