"""
Duplicate tracker for email processing.

This module defines the DuplicateTracker model that tracks processed email
message IDs to prevent reprocessing (FR-011).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Set

from pydantic import BaseModel, Field


class DuplicateTracker(BaseModel):
    """
    Tracks processed email message IDs.

    Stored in data/metadata/processed_ids.json as a persistent set of message IDs
    that have been successfully processed. Used to implement FR-011 (duplicate detection).

    Attributes:
        processed_message_ids: Set of processed message IDs
        last_updated: Timestamp when tracker was last modified
    """

    processed_message_ids: Set[str] = Field(
        default_factory=set,
        description="Set of processed message IDs"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last time tracker was updated"
    )

    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if message ID has been processed.

        Args:
            message_id: Email message ID to check

        Returns:
            True if message has been processed, False otherwise
        """
        return message_id in self.processed_message_ids

    def mark_processed(self, message_id: str) -> None:
        """
        Mark message ID as processed.

        Updates the set of processed IDs and the last_updated timestamp.

        Args:
            message_id: Email message ID to mark as processed
        """
        self.processed_message_ids.add(message_id)
        self.last_updated = datetime.utcnow()

    @classmethod
    def load(cls, file_path: Path) -> "DuplicateTracker":
        """
        Load DuplicateTracker from JSON file.

        Args:
            file_path: Path to processed_ids.json file

        Returns:
            DuplicateTracker instance

        Raises:
            FileNotFoundError: If file doesn't exist (returns empty tracker)
            ValueError: If file contains invalid JSON
        """
        if not file_path.exists():
            # Return empty tracker if file doesn't exist
            return cls()

        try:
            data = json.loads(file_path.read_text())
            # Convert list back to set (JSON doesn't support sets)
            if "processed_message_ids" in data and isinstance(data["processed_message_ids"], list):
                data["processed_message_ids"] = set(data["processed_message_ids"])
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")

    def save(self, file_path: Path) -> None:
        """
        Save DuplicateTracker to JSON file.

        Creates parent directories if they don't exist.
        Converts set to list for JSON serialization.

        Args:
            file_path: Path to processed_ids.json file

        Raises:
            OSError: If file cannot be written
        """
        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert set to list for JSON serialization
        data = {
            "processed_message_ids": list(self.processed_message_ids),
            "last_updated": self.last_updated.isoformat()
        }

        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def count(self) -> int:
        """
        Get count of processed message IDs.

        Returns:
            Number of processed emails
        """
        return len(self.processed_message_ids)

    model_config = {
        "json_encoders": {
            set: list,
            datetime: lambda dt: dt.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "processed_message_ids": [
                    "<CABc123@mail.gmail.com>",
                    "<DEF456@mail.example.com>",
                    "<GHI789@mail.test.com>"
                ],
                "last_updated": "2025-10-30T16:00:00Z"
            }
        }
    }
