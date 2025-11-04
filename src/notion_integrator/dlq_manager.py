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

        logger.info(
            f"Retrying DLQ entry: {dlq_entry.email_id} (retry #{dlq_entry.retry_count + 1})"
        )

        # Attempt write
        result = await notion_writer.create_collabiq_entry(dlq_entry.extracted_data)

        if result.success:
            # Success - delete DLQ file
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
