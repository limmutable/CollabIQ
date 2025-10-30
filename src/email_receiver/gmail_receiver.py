"""
Gmail API implementation of EmailReceiver.

This module provides the GmailReceiver class that connects to Gmail API
using OAuth2 and retrieves emails from portfolioupdates@signite.co inbox.
"""

import base64
import json
import logging
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from ..models.raw_email import EmailAttachment, EmailMetadata, RawEmail
    from .base import EmailReceiver
except ImportError:
    from models.raw_email import EmailAttachment, EmailMetadata, RawEmail
    from email_receiver.base import EmailReceiver

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

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    MAX_RETRIES = 3
    BASE_DELAY = 2  # seconds

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        raw_email_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None
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
            # Load existing token
            if self.token_path.exists():
                self.creds = Credentials.from_authorized_user_file(
                    str(self.token_path),
                    self.SCOPES
                )
                logger.info(f"Loaded existing token from {self.token_path}")

            # Refresh expired token or run OAuth flow
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired token")
                    self.creds.refresh(Request())
                else:
                    logger.info("Running OAuth2 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path),
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # Save token for next run
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                self.token_path.write_text(self.creds.to_json())
                logger.info(f"Saved token to {self.token_path}")

            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Successfully connected to Gmail API")

        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            raise EmailReceiverError(
                code="AUTHENTICATION_FAILED",
                message=f"Failed to authenticate with Gmail API: {str(e)}",
                retry_count=0
            )

    def fetch_emails(
        self,
        since: Optional[datetime] = None,
        max_emails: int = 100
    ) -> List[RawEmail]:
        """
        Retrieve unprocessed emails from Gmail inbox (T031).

        Implements exponential backoff retry logic per FR-010.

        Args:
            since: Only retrieve emails after this timestamp
            max_emails: Maximum number of emails to retrieve (1-500)

        Returns:
            List of RawEmail objects in chronological order (oldest first)

        Raises:
            EmailReceiverError: With codes CONNECTION_FAILED, AUTHENTICATION_FAILED,
                               RATE_LIMIT_EXCEEDED, or INVALID_RESPONSE
        """
        if not self.service:
            raise EmailReceiverError(
                code="CONNECTION_FAILED",
                message="Gmail service not connected. Call connect() first.",
                retry_count=0
            )

        retry_count = 0
        last_error = None

        while retry_count <= self.MAX_RETRIES:
            try:
                # Build query
                query = "in:inbox"
                if since:
                    query += f" after:{int(since.timestamp())}"

                # Fetch message list
                logger.info(f"Fetching emails with query: {query}, max: {max_emails}")
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_emails
                ).execute()

                messages = results.get('messages', [])
                logger.info(f"Found {len(messages)} messages")

                if not messages:
                    return []

                # Fetch full message details
                raw_emails = []
                for msg in messages:
                    try:
                        msg_detail = self.service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='full'
                        ).execute()

                        raw_email = self._parse_message(msg_detail)
                        raw_emails.append(raw_email)

                    except Exception as e:
                        logger.error(f"Failed to fetch message {msg['id']}: {e}")
                        continue

                # Sort by received_at (oldest first)
                raw_emails.sort(key=lambda e: e.metadata.received_at)
                logger.info(f"Successfully fetched {len(raw_emails)} emails")
                return raw_emails

            except HttpError as e:
                last_error = e

                # Authentication failure - no retry
                if e.resp.status == 401:
                    logger.error("Authentication failed (401)")
                    raise EmailReceiverError(
                        code="AUTHENTICATION_FAILED",
                        message="Gmail OAuth token expired or invalid",
                        retry_count=retry_count
                    )

                # Rate limit - retry with longer delay
                elif e.resp.status == 429:
                    retry_count += 1
                    if retry_count > self.MAX_RETRIES:
                        break

                    delay = min(60 * (2 ** retry_count), 600)  # Cap at 10 minutes
                    logger.warning(
                        f"Rate limit exceeded (429). Retry {retry_count}/{self.MAX_RETRIES} "
                        f"after {delay}s"
                    )
                    time.sleep(delay)

                # Server error - retry with exponential backoff
                elif e.resp.status >= 500:
                    retry_count += 1
                    if retry_count > self.MAX_RETRIES:
                        break

                    delay = self.BASE_DELAY * (2 ** retry_count)
                    logger.warning(
                        f"Server error ({e.resp.status}). Retry {retry_count}/{self.MAX_RETRIES} "
                        f"after {delay}s"
                    )
                    time.sleep(delay)

                # Other errors - no retry
                else:
                    logger.error(f"Invalid response from Gmail API: {e}")
                    raise EmailReceiverError(
                        code="INVALID_RESPONSE",
                        message=f"Gmail API returned error: {str(e)}",
                        retry_count=retry_count
                    )

            except Exception as e:
                logger.error(f"Unexpected error fetching emails: {e}")
                raise EmailReceiverError(
                    code="CONNECTION_FAILED",
                    message=f"Failed to fetch emails: {str(e)}",
                    retry_count=retry_count
                )

        # Max retries exceeded
        logger.error(f"Max retries ({self.MAX_RETRIES}) exceeded")
        raise EmailReceiverError(
            code="CONNECTION_FAILED",
            message=f"Failed to connect to Gmail API after {self.MAX_RETRIES} retries",
            retry_count=self.MAX_RETRIES,
            last_error=str(last_error)
        )

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
            payload = msg_detail.get('payload', {})
            headers = {h['name']: h['value'] for h in payload.get('headers', [])}

            # Extract metadata
            message_id = headers.get('Message-ID', f"<{msg_detail['id']}@gmail.com>")
            sender = headers.get('From', 'unknown@unknown.com')
            subject = headers.get('Subject', '(No Subject)')
            date_str = headers.get('Date', '')

            # Parse received date
            try:
                received_at = parsedate_to_datetime(date_str) if date_str else datetime.utcnow()
            except Exception:
                received_at = datetime.utcnow()

            # Extract body
            body = self._extract_body(payload)

            # Check for attachments
            has_attachments = self._has_attachments(payload)
            attachments = []  # TODO: Implement attachment parsing in later phase

            # Create RawEmail
            metadata = EmailMetadata(
                message_id=message_id,
                sender=sender,
                subject=subject,
                received_at=received_at,
                has_attachments=has_attachments
            )

            raw_email = RawEmail(
                metadata=metadata,
                body=body,
                attachments=attachments
            )

            logger.debug(f"Parsed message: {message_id}")
            return raw_email

        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            raise EmailReceiverError(
                code="VALIDATION_FAILED",
                message=f"Failed to parse Gmail message: {str(e)}",
                retry_count=0
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
        if 'body' in payload and payload['body'].get('data'):
            return self._decode_base64(payload['body']['data'])

        # Multipart message - find text/plain part
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                # Prefer text/plain
                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    return self._decode_base64(part['body']['data'])

            # Fallback to text/html
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
                    return self._decode_base64(part['body']['data'])

            # Nested parts
            for part in payload['parts']:
                if 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        return body

        return ""

    def _decode_base64(self, data: str) -> str:
        """Decode base64url-encoded string."""
        try:
            # Gmail uses base64url encoding (RFC 4648)
            decoded = base64.urlsafe_b64decode(data)
            return decoded.decode('utf-8', errors='replace')
        except Exception as e:
            logger.warning(f"Failed to decode base64 data: {e}")
            return ""

    def _has_attachments(self, payload: dict) -> bool:
        """Check if message has attachments."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
                if 'parts' in part:
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
            monthly_dir = self.raw_email_dir / str(received_date.year) / f"{received_date.month:02d}"
            monthly_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename: YYYYMMDD_HHMMSS_{clean_message_id}.json
            timestamp = received_date.strftime("%Y%m%d_%H%M%S")
            clean_id = email.metadata.message_id.strip('<>').replace('@', '_').replace('.', '_')[:50]
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
                    "has_attachments": email.metadata.has_attachments
                },
                "body": email.body,
                "attachments": [
                    {
                        "filename": att.filename,
                        "content_type": att.content_type,
                        "size_bytes": att.size_bytes,
                        "storage_path": str(att.storage_path) if att.storage_path else None
                    }
                    for att in email.attachments
                ]
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
                retry_count=0
            )

    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if email has been processed (placeholder).

        TODO: Implement DuplicateTracker integration in later tasks.

        Args:
            message_id: Email message ID to check

        Returns:
            False (always returns False for now)
        """
        # Placeholder - will implement DuplicateTracker in Phase 4
        return False

    def mark_processed(self, message_id: str) -> None:
        """
        Mark email as processed (placeholder).

        TODO: Implement DuplicateTracker integration in later tasks.

        Args:
            message_id: Email message ID to mark as processed
        """
        # Placeholder - will implement DuplicateTracker in Phase 4
        pass
