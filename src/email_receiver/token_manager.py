import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from models.gmail_token import GmailTokenPair

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Manages Gmail OAuth2 tokens with encryption at rest.
    """
    def __init__(self, token_path: Path, encryption_key: Optional[str] = None):
        self.token_path = token_path
        self.encryption_key = encryption_key or os.environ.get("GMAIL_ENCRYPTION_KEY")
        self._fernet = Fernet(self.encryption_key.encode()) if self.encryption_key else None

    def save_token(self, token_data: dict):
        """
        Saves the token data to file, optionally encrypted.
        """
        try:
            if self._fernet:
                # Encrypt the refresh token and access token if needed
                # For now, we'll just encrypt the entire JSON string
                json_data = json.dumps(token_data)
                encrypted_data = self._fernet.encrypt(json_data.encode())
                self.token_path.write_bytes(encrypted_data)
                logger.info(f"Saved encrypted token to {self.token_path}")
            else:
                self.token_path.write_text(json.dumps(token_data, indent=2))
                logger.warning(f"Saved UNENCRYPTED token to {self.token_path} (no encryption key provided)")
        except OSError as e:
            if e.errno == 30:  # Read-only file system
                logger.warning(f"Could not save token to {self.token_path}: Read-only file system. "
                             "This is expected in Cloud Run with mounted secrets. "
                             "The new token will be used for this session but not persisted.")
            else:
                logger.error(f"Failed to save token to {self.token_path}: {e}")
                raise

    def load_token(self) -> Optional[dict]:
        """
        Loads the token data from file, decrypting if necessary.
        """
        if not self.token_path.exists():
            return None

        try:
            if self._fernet:
                encrypted_data = self.token_path.read_bytes()
                try:
                    decrypted_data = self._fernet.decrypt(encrypted_data)
                    return json.loads(decrypted_data.decode())
                except Exception as e:
                    logger.warning(f"Failed to decrypt token: {e}. Attempting to read as plain JSON.")
                    # Fallback for migration: try reading as plain JSON
                    return json.loads(self.token_path.read_text())
            else:
                return json.loads(self.token_path.read_text())
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return None
