"""
IMAP implementation of EmailReceiver (PLACEHOLDER).

This module is a placeholder for future IMAP-based email reception.
All methods are currently unimplemented and will raise NotImplementedError.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from ..models.raw_email import RawEmail
    from .base import EmailReceiver
except ImportError:
    from models.raw_email import RawEmail
    from email_receiver.base import EmailReceiver


class IMAPReceiver(EmailReceiver):
    """
    IMAP implementation for email ingestion (PLACEHOLDER).

    This is a placeholder class for IMAP-based email reception.
    The Gmail API implementation (GmailReceiver) is the primary focus for MVP.

    Future implementation will support:
    - Standard IMAP connection (imap.gmail.com:993)
    - SSL/TLS encryption
    - Folder-based message retrieval
    - Message ID tracking for duplicate detection
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        raw_email_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None
    ):
        """
        Initialize IMAPReceiver (PLACEHOLDER).

        Args:
            host: IMAP server hostname (e.g., 'imap.gmail.com')
            port: IMAP server port (e.g., 993 for SSL)
            username: Email address for authentication
            password: App-specific password or account password
            use_ssl: Whether to use SSL/TLS (default: True)
            raw_email_dir: Directory for raw email storage
            metadata_dir: Directory for metadata storage
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.raw_email_dir = Path(raw_email_dir or "data/raw")
        self.metadata_dir = Path(metadata_dir or "data/metadata")

    def fetch_emails(
        self,
        since: Optional[datetime] = None,
        max_emails: int = 100
    ) -> List[RawEmail]:
        """
        Retrieve emails via IMAP (PLACEHOLDER).

        TODO: Implement IMAP connection and message retrieval.

        Args:
            since: Only retrieve emails after this timestamp
            max_emails: Maximum number of emails to retrieve

        Returns:
            List of RawEmail objects

        Raises:
            NotImplementedError: IMAP implementation not yet available
        """
        raise NotImplementedError(
            "IMAPReceiver is a placeholder. Use GmailReceiver for MVP implementation."
        )

    def save_raw_email(self, email: RawEmail) -> Path:
        """
        Save RawEmail to file storage (PLACEHOLDER).

        TODO: Implement file storage logic (same as GmailReceiver).

        Args:
            email: RawEmail object to save

        Returns:
            Path to saved JSON file

        Raises:
            NotImplementedError: IMAP implementation not yet available
        """
        raise NotImplementedError(
            "IMAPReceiver is a placeholder. Use GmailReceiver for MVP implementation."
        )

    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if email has been processed (PLACEHOLDER).

        TODO: Implement DuplicateTracker integration.

        Args:
            message_id: Email message ID to check

        Returns:
            bool: Whether email is a duplicate

        Raises:
            NotImplementedError: IMAP implementation not yet available
        """
        raise NotImplementedError(
            "IMAPReceiver is a placeholder. Use GmailReceiver for MVP implementation."
        )

    def mark_processed(self, message_id: str) -> None:
        """
        Mark email as processed (PLACEHOLDER).

        TODO: Implement DuplicateTracker integration.

        Args:
            message_id: Email message ID to mark as processed

        Raises:
            NotImplementedError: IMAP implementation not yet available
        """
        raise NotImplementedError(
            "IMAPReceiver is a placeholder. Use GmailReceiver for MVP implementation."
        )
