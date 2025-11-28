"""
Google Cloud Storage-backed state manager for daemon.

This manager persists daemon state to GCS, allowing state to survive
across Cloud Run job executions.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from models.daemon_state import DaemonProcessState

logger = logging.getLogger(__name__)


class GCSStateManager:
    """
    Manages daemon state using Google Cloud Storage for persistence.

    Falls back to local file storage if GCS is not configured or unavailable.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        blob_name: str = "daemon/state.json",
        local_fallback_path: Optional[Path] = None,
    ):
        """
        Initialize the GCS state manager.

        Args:
            bucket_name: GCS bucket name. If None, uses GCS_STATE_BUCKET env var.
            blob_name: Path within the bucket for the state file.
            local_fallback_path: Local file path to use if GCS is unavailable.
        """
        self.bucket_name = bucket_name or os.getenv("GCS_STATE_BUCKET")
        self.blob_name = blob_name
        self.local_fallback_path = local_fallback_path or Path("data/daemon/state.json")

        self._gcs_client = None
        self._gcs_available = False

        if self.bucket_name:
            self._init_gcs_client()

    def _init_gcs_client(self):
        """Initialize GCS client if available."""
        try:
            from google.cloud import storage

            self._gcs_client = storage.Client()
            # Verify bucket exists
            self._gcs_client.get_bucket(self.bucket_name)
            self._gcs_available = True
            logger.info(f"GCS state manager initialized: gs://{self.bucket_name}/{self.blob_name}")
        except ImportError:
            logger.warning("google-cloud-storage not installed, using local fallback")
            self._gcs_available = False
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}, using local fallback")
            self._gcs_available = False

    def load_state(self) -> DaemonProcessState:
        """
        Load daemon state from GCS or local file.

        Returns:
            DaemonProcessState instance (empty state if not found).
        """
        if self._gcs_available:
            return self._load_from_gcs()
        return self._load_from_local()

    def save_state(self, state: DaemonProcessState):
        """
        Save daemon state to GCS and local file.

        Saves to both locations if GCS is available for redundancy.
        """
        # Always save locally as backup
        self._save_to_local(state)

        if self._gcs_available:
            self._save_to_gcs(state)

    def _load_from_gcs(self) -> DaemonProcessState:
        """Load state from GCS bucket."""
        try:
            bucket = self._gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(self.blob_name)

            if not blob.exists():
                logger.info("No existing state in GCS, returning default state")
                return DaemonProcessState()

            data = json.loads(blob.download_as_string())
            logger.info(f"Loaded state from GCS: gs://{self.bucket_name}/{self.blob_name}")
            return DaemonProcessState(**data)
        except Exception as e:
            logger.error(f"Failed to load state from GCS: {e}")
            # Try local fallback
            return self._load_from_local()

    def _save_to_gcs(self, state: DaemonProcessState):
        """Save state to GCS bucket."""
        try:
            bucket = self._gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(self.blob_name)

            state_json = state.model_dump_json(indent=2)
            blob.upload_from_string(state_json, content_type="application/json")
            logger.info(f"Saved state to GCS: gs://{self.bucket_name}/{self.blob_name}")
        except Exception as e:
            logger.error(f"Failed to save state to GCS: {e}")

    def _load_from_local(self) -> DaemonProcessState:
        """Load state from local file."""
        if not self.local_fallback_path.exists():
            logger.info("No local state file found, returning default state")
            return DaemonProcessState()

        try:
            data = json.loads(self.local_fallback_path.read_text())
            logger.info(f"Loaded state from local file: {self.local_fallback_path}")
            return DaemonProcessState(**data)
        except Exception as e:
            logger.error(f"Failed to load local state: {e}")
            return DaemonProcessState()

    def _save_to_local(self, state: DaemonProcessState):
        """Save state to local file."""
        try:
            self.local_fallback_path.parent.mkdir(parents=True, exist_ok=True)

            temp_path = self.local_fallback_path.with_suffix(".tmp")
            temp_path.write_text(state.model_dump_json(indent=2))
            temp_path.replace(self.local_fallback_path)
            logger.debug(f"Saved state to local file: {self.local_fallback_path}")
        except Exception as e:
            logger.error(f"Failed to save local state: {e}")
