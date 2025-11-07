"""DLQManager - Manages dead letter queue for failed Notion writes.

This module provides functionality to capture, store, and retry failed write operations.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from llm_provider.types import DLQEntry, ExtractedEntitiesWithClassification


logger = logging.getLogger(__name__)


class DLQManager:
    """Manages dead letter queue for failed Notion writes."""

    def __init__(self, dlq_dir: str = "data/dlq"):
        """Initialize DLQManager with DLQ directory path.

        Args:
            dlq_dir: Directory path for DLQ files (default: "data/dlq")
        """
        self.dlq_dir = Path(dlq_dir)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def save_failed_write(
        self,
        extracted_data: ExtractedEntitiesWithClassification,
        error_details: Dict[str, Any],
    ) -> str:
        """Save failed write operation to DLQ for manual retry or debugging.

        Args:
            extracted_data: Extracted and classified email data
            error_details: Error information (error_type, error_message, status_code)

        Returns:
            File path to created DLQ entry
        """
        # Create DLQ entry
        dlq_entry = DLQEntry(
            email_id=extracted_data.email_id,
            failed_at=datetime.utcnow(),
            retry_count=error_details.get("retry_count", 0),
            error=error_details,
            extracted_data=extracted_data,
        )

        # Generate filename: {email_id}_{timestamp}.json
        timestamp_str = dlq_entry.failed_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{extracted_data.email_id}_{timestamp_str}.json"
        file_path = self.dlq_dir / filename

        # Serialize to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                dlq_entry.model_dump(), f, indent=2, ensure_ascii=False, default=str
            )

        logger.info(f"DLQ entry created: {file_path}")

        return str(file_path)

    def load_dlq_entry(self, file_path: str) -> DLQEntry:
        """Load and deserialize DLQ entry from JSON file.

        Args:
            file_path: Path to DLQ JSON file

        Returns:
            Deserialized DLQEntry instance
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Deserialize using Pydantic
        return DLQEntry(**data)

    def list_dlq_entries(self) -> List[str]:
        """List all DLQ entries in the directory.

        Returns:
            Sorted list of DLQ file paths (oldest first)
        """
        # Find all .json files in dlq_dir
        dlq_files = list(self.dlq_dir.glob("*.json"))

        # Sort by creation time (oldest first)
        dlq_files.sort(key=lambda p: p.stat().st_ctime)

        # Return as string paths
        return [str(f) for f in dlq_files]

    async def retry_failed_write(self, file_path: str, notion_writer) -> bool:
        """Retry a failed write operation from DLQ.

        Args:
            file_path: Path to DLQ entry file
            notion_writer: NotionWriter instance to use for retry

        Returns:
            True if retry succeeded (file deleted), False if failed (retry_count incremented)
        """
        # Load DLQ entry
        dlq_entry = self.load_dlq_entry(file_path)

        # Check if already processed (idempotency)
        if self.is_processed(dlq_entry.email_id):
            logger.info(
                f"DLQ entry {dlq_entry.email_id} already processed, skipping (idempotency check)"
            )
            # Delete the DLQ file since it's already processed
            Path(file_path).unlink()
            return True

        logger.info(
            f"Retrying DLQ entry: {dlq_entry.email_id} (retry #{dlq_entry.retry_count + 1})"
        )

        # Attempt write
        result = await notion_writer.create_collabiq_entry(dlq_entry.extracted_data)

        if result.success:
            # Success - mark as processed and delete DLQ file
            self._mark_processed(dlq_entry.email_id)
            Path(file_path).unlink()
            logger.info(f"DLQ retry succeeded: {dlq_entry.email_id} - file deleted")
            return True
        else:
            # Failed - increment retry_count and save updated entry
            dlq_entry.retry_count += 1
            dlq_entry.failed_at = datetime.utcnow()

            # Update error details
            dlq_entry.error = {
                "error_type": result.error_type,
                "error_message": result.error_message,
                "status_code": result.status_code,
                "retry_count": dlq_entry.retry_count,
            }

            # Overwrite file with updated entry
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    dlq_entry.model_dump(), f, indent=2, ensure_ascii=False, default=str
                )

            logger.warning(
                f"DLQ retry failed: {dlq_entry.email_id} (retry #{dlq_entry.retry_count}) - {result.error_message}"
            )
            return False

    async def replay_batch(
        self, notion_writer, max_count: int = 10, operation_type: str = "all"
    ) -> Dict[str, int]:
        """Replay multiple DLQ entries in batch.

        Args:
            notion_writer: NotionWriter instance to use for retry
            max_count: Maximum number of entries to replay (default: 10)
            operation_type: Filter by operation type (default: "all")

        Returns:
            Dictionary with success/failure counts: {"succeeded": N, "failed": M}
        """
        results = {"succeeded": 0, "failed": 0}

        # Get all DLQ entries
        dlq_files = self.list_dlq_entries()[:max_count]

        if not dlq_files:
            logger.info("No DLQ entries found for replay")
            return results

        logger.info(f"Replaying {len(dlq_files)} DLQ entries (max: {max_count})")

        # Replay each entry
        for file_path in dlq_files:
            try:
                success = await self.retry_failed_write(file_path, notion_writer)
                if success:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error replaying DLQ entry {file_path}: {e}")
                results["failed"] += 1

        logger.info(
            f"DLQ replay complete: {results['succeeded']} succeeded, {results['failed']} failed"
        )
        return results

    def is_processed(self, email_id: str) -> bool:
        """Check if an email has already been processed (idempotency check).

        Args:
            email_id: Email identifier to check

        Returns:
            True if already processed, False otherwise
        """
        processed_ids = self._load_processed_ids()
        return email_id in processed_ids

    def _mark_processed(self, email_id: str) -> None:
        """Mark an email as processed (for idempotency).

        Args:
            email_id: Email identifier to mark as processed
        """
        processed_ids = self._load_processed_ids()
        processed_ids.add(email_id)
        self._save_processed_ids(processed_ids)

    def _load_processed_ids(self) -> set:
        """Load set of processed email IDs from file.

        Returns:
            Set of processed email IDs
        """
        processed_file = self.dlq_dir / ".processed_ids.json"

        if not processed_file.exists():
            return set()

        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception as e:
            logger.warning(f"Failed to load processed IDs: {e}")
            return set()

    def _save_processed_ids(self, processed_ids: set) -> None:
        """Save set of processed email IDs to file.

        Args:
            processed_ids: Set of email IDs to save
        """
        processed_file = self.dlq_dir / ".processed_ids.json"

        try:
            with open(processed_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"processed_ids": sorted(list(processed_ids))},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            logger.error(f"Failed to save processed IDs: {e}")
