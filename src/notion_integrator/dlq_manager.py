"""DLQManager - Manages dead letter queue for failed Notion writes.

This module provides functionality to capture, store, and retry failed write operations.
"""

from pathlib import Path


class DLQManager:
    """Manages dead letter queue for failed Notion writes."""

    def __init__(self, dlq_dir: str = "data/dlq"):
        """Initialize DLQManager with DLQ directory path.

        Args:
            dlq_dir: Directory path for DLQ files (default: "data/dlq")
        """
        self.dlq_dir = Path(dlq_dir)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)
