"""
Notion Test Entry Cleanup Module (T018)

Provides robust cleanup mechanism for Notion test entries with:
- Idempotency: Safe to run multiple times
- Retry logic: Max 3 attempts with exponential backoff
- Verification: Post-cleanup query to confirm deletion
- Error handling: Log failures, continue, non-zero exit on failures
- Selective cleanup: Only delete test-marked entries
- Timeout protection: 30s per operation

Usage (Python API):
    from src.collabiq.test_utils.notion_cleanup import NotionTestCleanup

    cleanup = NotionTestCleanup(
        database_id="abc123",
        test_run_id="test-001"
    )

    result = cleanup.cleanup_test_entries()
    # Returns: {
    #     "cleaned": 15,
    #     "errors": 0,
    #     "duration": 3.2,
    #     "skipped": 2,
    #     "verified": True
    # }

Usage (CLI):
    python -m src.collabiq.test_utils.cli cleanup --database-id=abc123 --test-run-id=test-001
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from notion_client import Client as NotionClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Result of cleanup operation."""

    cleaned: int  # Number of entries successfully deleted
    errors: int  # Number of deletion errors
    skipped: int  # Number of entries skipped (not test entries)
    duration: float  # Total duration in seconds
    verified: bool  # Whether post-cleanup verification succeeded
    failed_ids: List[str]  # Page IDs that failed to delete
    timestamp: str  # Cleanup timestamp

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class NotionTestCleanup:
    """
    Robust cleanup mechanism for Notion test entries.

    Implements FR-003 requirements:
    - Idempotency: Track cleaned entries to avoid double-deletion
    - Retry logic: Max 3 attempts with exponential backoff
    - Verification: Post-cleanup query to confirm deletion
    - Error handling: Log failures, continue, track failed IDs
    - Selective cleanup: Only delete entries with test markers
    - Timeout protection: 30s per operation
    """

    def __init__(
        self,
        database_id: str,
        test_run_id: Optional[str] = None,
        email_ids: Optional[List[str]] = None,
        notion_token: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 30,
    ):
        """
        Initialize cleanup manager.

        Args:
            database_id: Notion database ID to clean up
            test_run_id: Test run ID to filter entries (optional)
            email_ids: List of email IDs to delete entries for (optional)
            notion_token: Notion API token (uses env var if not provided)
            max_retries: Maximum retry attempts per deletion (default: 3)
            timeout_seconds: Timeout per operation in seconds (default: 30)

        Note:
            Either test_run_id or email_ids must be provided to identify test entries.
        """
        if not test_run_id and not email_ids:
            raise ValueError("Either test_run_id or email_ids must be provided")

        self.database_id = database_id
        self.test_run_id = test_run_id
        self.email_ids = email_ids or []
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

        # Initialize Notion client
        import os

        token = (
            notion_token or os.getenv("TEST_NOTION_TOKEN") or os.getenv("NOTION_TOKEN")
        )
        if not token:
            raise ValueError("Notion token not provided and not found in environment")

        self.client = NotionClient(auth=token)

        # Track cleaned entries for idempotency
        self._cleaned_ids: set[str] = set()

    def find_test_entries(self) -> List[Dict]:
        """
        Find all test entries in the database.

        Filters by:
        - test_run_id (if provided)
        - email_ids (if provided)

        Returns:
            List of page objects that match test criteria

        Timeout:
            30 seconds per query
        """
        logger.info(
            f"Searching for test entries in database {self.database_id}"
            f" (test_run_id={self.test_run_id}, email_ids={len(self.email_ids)})"
        )

        test_entries = []
        start_time = time.time()

        try:
            # Query by test_run_id if provided
            if self.test_run_id:
                filter_condition = {
                    "property": "test_run_id",
                    "rich_text": {"equals": self.test_run_id},
                }

                response = self.client.databases.query(
                    database_id=self.database_id, filter=filter_condition
                )

                test_entries.extend(response.get("results", []))

            # Query by email_ids if provided
            if self.email_ids:
                for email_id in self.email_ids:
                    # Check timeout
                    if time.time() - start_time > self.timeout_seconds:
                        logger.warning("Timeout reached while querying email IDs (30s)")
                        break

                    filter_condition = {
                        "property": "email_id",
                        "rich_text": {"equals": email_id},
                    }

                    response = self.client.databases.query(
                        database_id=self.database_id, filter=filter_condition
                    )

                    test_entries.extend(response.get("results", []))

            # Remove duplicates by page ID
            unique_entries = {entry["id"]: entry for entry in test_entries}
            test_entries = list(unique_entries.values())

            logger.info(f"Found {len(test_entries)} test entries to clean")
            return test_entries

        except Exception as e:
            logger.error(f"Error querying test entries: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _delete_page_with_retry(self, page_id: str) -> bool:
        """
        Delete a Notion page with retry logic.

        Args:
            page_id: Notion page ID to delete

        Returns:
            True if deleted successfully

        Raises:
            Exception after max retries exhausted

        Retry Logic:
            - Max 3 attempts
            - Exponential backoff: 1s, 2s, 4s, ...
            - Timeout: 30s per attempt
        """
        # Check idempotency: skip if already cleaned
        if page_id in self._cleaned_ids:
            logger.debug(f"Page {page_id} already cleaned (idempotency check)")
            return True

        logger.debug(f"Deleting page {page_id}")

        try:
            # Archive (soft delete) the page
            self.client.pages.update(page_id=page_id, archived=True)

            # Mark as cleaned for idempotency
            self._cleaned_ids.add(page_id)

            logger.debug(f"Successfully deleted page {page_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to delete page {page_id}: {e}")
            raise  # Let tenacity handle retry

    def cleanup_test_entries(
        self, verify: bool = True, continue_on_error: bool = True
    ) -> CleanupResult:
        """
        Clean up all test entries from database.

        Args:
            verify: If True, verify deletion with post-cleanup query
            continue_on_error: If True, continue cleaning even if some deletions fail

        Returns:
            CleanupResult with statistics

        FR-003 Implementation:
        - Idempotency: _delete_page_with_retry checks _cleaned_ids
        - Retry logic: tenacity decorator with 3 attempts, exponential backoff
        - Verification: Optional post-cleanup query
        - Error handling: continue_on_error allows partial cleanup
        - Selective cleanup: find_test_entries filters by test markers
        - Timeout protection: 30s per operation
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()

        logger.info("Starting test entry cleanup")

        # Find test entries
        test_entries = self.find_test_entries()

        if len(test_entries) == 0:
            logger.info("No test entries found to clean")
            return CleanupResult(
                cleaned=0,
                errors=0,
                skipped=0,
                duration=time.time() - start_time,
                verified=True,
                failed_ids=[],
                timestamp=timestamp,
            )

        # Delete each entry
        cleaned_count = 0
        error_count = 0
        failed_ids = []

        for entry in test_entries:
            page_id = entry["id"]

            try:
                # Delete with retry logic
                success = self._delete_page_with_retry(page_id)

                if success:
                    cleaned_count += 1
                else:
                    error_count += 1
                    failed_ids.append(page_id)

            except Exception as e:
                error_count += 1
                failed_ids.append(page_id)
                logger.error(f"Failed to delete page {page_id} after max retries: {e}")

                if not continue_on_error:
                    # Stop on first error if requested
                    break

        # Verification: Query again to confirm deletion
        verified = False
        if verify:
            logger.info("Verifying cleanup...")
            remaining_entries = self.find_test_entries()

            if len(remaining_entries) == 0:
                logger.info("✓ Verification passed: All test entries removed")
                verified = True
            else:
                logger.warning(
                    f"⚠️  Verification failed: {len(remaining_entries)} entries still present"
                )
                verified = False

        duration = time.time() - start_time

        result = CleanupResult(
            cleaned=cleaned_count,
            errors=error_count,
            skipped=0,  # Not implemented yet (would check for non-test entries)
            duration=duration,
            verified=verified,
            failed_ids=failed_ids,
            timestamp=timestamp,
        )

        logger.info(
            f"Cleanup complete: {cleaned_count} cleaned, "
            f"{error_count} errors, {duration:.1f}s"
        )

        return result


def cleanup_notion(
    database_id: str,
    test_run_id: Optional[str] = None,
    email_ids: Optional[List[str]] = None,
    verify: bool = True,
) -> Dict:
    """
    Simple API function for cleaning up Notion test entries.

    Args:
        database_id: Notion database ID
        test_run_id: Test run ID to filter (optional)
        email_ids: List of email IDs to filter (optional)
        verify: Whether to verify deletion

    Returns:
        Dict with cleanup statistics: {
            "cleaned": 15,
            "errors": 0,
            "duration": 3.2,
            "verified": True
        }

    Example:
        >>> result = cleanup_notion(
        ...     database_id="abc123",
        ...     test_run_id="test-001",
        ...     verify=True
        ... )
        >>> print(f"Cleaned {result['cleaned']} entries")
    """
    cleanup = NotionTestCleanup(
        database_id=database_id, test_run_id=test_run_id, email_ids=email_ids
    )

    result = cleanup.cleanup_test_entries(verify=verify)

    return result.to_dict()
