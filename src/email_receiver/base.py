"""
Email receiver abstract base class.

This module defines the abstract interface that all EmailReceiver implementations
must follow (IMAP, Gmail API, Webhook, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from ..models.raw_email import RawEmail
except ImportError:
    from models.raw_email import RawEmail


class EmailReceiver(ABC):
    """
    Abstract base class for email ingestion implementations.

    All implementations must inherit from this interface and implement the required methods.

    Requirements Coverage:
    - FR-001: Connect to inbox with configurable authentication
    - FR-002: Retrieve unprocessed emails in chronological order
    - FR-003: Save raw email content with timestamp and unique ID
    - FR-009: Log all processing activities with timestamps
    - FR-010: Handle connection failures with exponential backoff (max 3 retries)
    - FR-011: Detect duplicate emails using message ID
    - SC-001: Retrieve 90%+ of emails within 5 minutes
    """

    @abstractmethod
    def fetch_emails(
        self,
        since: Optional[datetime] = None,
        max_emails: int = 100
    ) -> List[RawEmail]:
        """
        Retrieve unprocessed emails from the inbox in chronological order.

        This is the primary method for email ingestion.

        Args:
            since: Only retrieve emails received after this timestamp.
                   If None, retrieve all unprocessed emails.
            max_emails: Maximum number of emails to retrieve in one batch.
                       Useful for rate limiting and pagination.
                       Valid range: 1-500.

        Returns:
            List of RawEmail objects in chronological order (oldest first).
            Empty list if no new emails found.

        Raises:
            EmailReceiverError: With one of the following error codes:
                - CONNECTION_FAILED: Failed to connect after max retries (FR-010)
                - AUTHENTICATION_FAILED: Invalid credentials or expired token
                - RATE_LIMIT_EXCEEDED: Email service rate limit exceeded
                - INVALID_RESPONSE: Malformed response from email service

        Side Effects:
            - Logs ProcessingEvent.EMAIL_RETRIEVED for each email (FR-009)
            - Logs ProcessingEvent.DUPLICATE_DETECTED for skipped emails (FR-011)
            - Logs ProcessingEvent.CONNECTION_FAILED on errors (FR-010)
            - Logs ProcessingEvent.CONNECTION_RETRY for retry attempts (FR-010)
            - Updates DuplicateTracker.processed_message_ids (FR-011)
        """
        pass

    @abstractmethod
    def save_raw_email(self, email: RawEmail) -> Path:
        """
        Save RawEmail to file storage with timestamp and message ID.

        Creates monthly subdirectories automatically.

        Args:
            email: The RawEmail object to save

        Returns:
            Path to the saved JSON file.
            Format: data/raw/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json

        Raises:
            EmailReceiverError: With one of the following error codes:
                - STORAGE_FAILED: Failed to write email to file storage
                - VALIDATION_FAILED: RawEmail failed Pydantic validation

        Side Effects:
            - Creates monthly directory if it doesn't exist (data/raw/YYYY/MM/)
            - Writes JSON file with format YYYYMMDD_HHMMSS_{message_id}.json
            - Logs ProcessingEvent.EMAIL_RETRIEVED on success
        """
        pass

    @abstractmethod
    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if an email has already been processed using message ID.

        Uses DuplicateTracker to maintain set of processed IDs.

        Args:
            message_id: Email message ID to check

        Returns:
            True if message_id exists in DuplicateTracker.processed_message_ids,
            False otherwise.

        Raises:
            EmailReceiverError: With error code:
                - TRACKER_LOAD_FAILED: Failed to load DuplicateTracker from file

        Side Effects:
            - Loads DuplicateTracker from data/metadata/processed_ids.json
            - No modifications to tracker (read-only operation)
        """
        pass

    @abstractmethod
    def mark_processed(self, message_id: str) -> None:
        """
        Mark an email as processed by adding message ID to DuplicateTracker.

        Args:
            message_id: Email message ID to mark as processed

        Raises:
            EmailReceiverError: With error code:
                - TRACKER_SAVE_FAILED: Failed to save DuplicateTracker to file

        Side Effects:
            - Updates DuplicateTracker.processed_message_ids set
            - Updates DuplicateTracker.last_updated timestamp
            - Writes updated tracker to data/metadata/processed_ids.json
        """
        pass
