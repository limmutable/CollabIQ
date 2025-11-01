"""Application settings using Pydantic for environment variable management.

Manages Gmail credentials, Pub/Sub configuration, and other environment settings.

Usage:
    from src.config.settings import get_settings

    settings = get_settings()
    print(settings.gmail_credentials_path)
"""

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from config.infisical_client import InfisicalClient


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        gmail_credentials_path: Path to Gmail API OAuth credentials
        gmail_token_path: Path to Gmail API token cache
        gmail_batch_size: Number of emails to fetch per batch
        pubsub_topic: Google Cloud Pub/Sub topic name
        pubsub_project_id: Google Cloud project ID
        data_dir: Base directory for storing raw/cleaned emails
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gmail API Configuration
    gmail_credentials_path: Path = Field(
        default=Path("credentials.json"),
        description="Path to Gmail API OAuth2 credentials file",
    )
    gmail_token_path: Path = Field(
        default=Path("token.json"),
        description="Path to Gmail API token cache",
    )
    gmail_batch_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of emails to fetch per batch (1-500)",
    )

    # Google Cloud Pub/Sub Configuration (Future use)
    pubsub_topic: Optional[str] = Field(
        default=None,
        description="Pub/Sub topic name for email notifications",
    )
    pubsub_project_id: Optional[str] = Field(
        default=None,
        description="Google Cloud project ID",
    )

    # Data Storage Configuration
    data_dir: Path = Field(
        default=Path("data"),
        description="Base directory for email storage",
    )
    raw_email_dir: Path = Field(
        default=Path("data/raw"),
        description="Directory for raw emails",
    )
    cleaned_email_dir: Path = Field(
        default=Path("data/cleaned"),
        description="Directory for cleaned emails",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files",
    )

    # Duplicate Detection Configuration
    duplicate_tracker_path: Path = Field(
        default=Path("data/duplicate_tracker.json"),
        description="Path to duplicate tracker state file",
    )

    # Rate Limiting Configuration
    rate_limit_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retries for rate limit errors",
    )
    rate_limit_base_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Base delay in seconds for exponential backoff",
    )

    # Infisical Secret Management Configuration
    infisical_enabled: bool = Field(
        default=False,
        description="Enable Infisical secret management integration",
    )
    infisical_host: str = Field(
        default="https://app.infisical.com",
        description="Infisical API endpoint URL",
    )
    infisical_project_id: Optional[str] = Field(
        default=None,
        description="Infisical project identifier",
    )
    infisical_environment: Optional[str] = Field(
        default=None,
        description="Environment slug (dev, staging, prod)",
    )
    infisical_client_id: Optional[str] = Field(
        default=None,
        description="Universal Auth machine identity client ID",
    )
    infisical_client_secret: Optional[str] = Field(
        default=None,
        description="Universal Auth machine identity client secret",
    )
    infisical_cache_ttl: int = Field(
        default=60,
        ge=0,
        le=3600,
        description="Secret cache TTL in seconds (0=disabled, 60=default)",
    )

    @field_validator("infisical_environment")
    @classmethod
    def validate_infisical_environment(cls, v: Optional[str]) -> Optional[str]:
        """Validate Infisical environment slug.

        Valid environments: development, production
        Enforces FR-005 (environment-specific secret management)
        """
        if v is not None:
            valid_envs = {"development", "production"}
            if v not in valid_envs:
                raise ValueError(
                    f"Invalid environment slug '{v}'. "
                    f"Must be one of: {', '.join(sorted(valid_envs))}. "
                    f"Please set INFISICAL_ENVIRONMENT to 'development' or 'production'."
                )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper

    @field_validator(
        "gmail_credentials_path",
        "data_dir",
        "raw_email_dir",
        "cleaned_email_dir",
        "log_dir",
    )
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        """Ensure path is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v

    def __init__(self, **data):
        """Initialize Settings with Infisical client."""
        super().__init__(**data)
        self._infisical_client: Optional["InfisicalClient"] = None

    @property
    def infisical_client(self) -> Optional["InfisicalClient"]:
        """Get or create Infisical client instance (lazy initialization).

        Returns:
            InfisicalClient instance if enabled, None otherwise
        """
        if not self.infisical_enabled:
            return None

        if self._infisical_client is None:
            from config.infisical_client import InfisicalClient

            self._infisical_client = InfisicalClient(self)
            if self.infisical_enabled:
                try:
                    self._infisical_client.authenticate()
                except Exception:
                    # Authentication failed, client will fall back to .env
                    pass

        return self._infisical_client

    def get_secret_or_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve secret from Infisical with fallback to environment variable.

        Three-tier fallback:
        1. Infisical API (if enabled and authenticated)
        2. SDK cache (if available)
        3. .env file / environment variable

        Args:
            key: Secret key to retrieve (e.g., "GEMINI_API_KEY")
            default: Default value if secret not found anywhere (default: None)

        Returns:
            Secret value as string, or default if not found

        Example:
            >>> settings = get_settings()
            >>> api_key = settings.get_secret_or_env("GEMINI_API_KEY")
            >>> print(api_key)
            'mock-gemini-api-key-AIzaSyD1234567890'
        """
        if self.infisical_client:
            try:
                return self.infisical_client.get_secret(key)
            except Exception:
                # Fall through to environment variable
                pass

        # Fallback to environment variable
        import os

        return os.getenv(key, default)

    def create_directories(self) -> None:
        """Create all required directories if they don't exist.

        Example:
            >>> settings = get_settings()
            >>> settings.create_directories()
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_email_dir.mkdir(parents=True, exist_ok=True)
        self.cleaned_email_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create monthly subdirectories for current month
        from datetime import datetime

        now = datetime.utcnow()
        year_month_raw = self.raw_email_dir / str(now.year) / f"{now.month:02d}"
        year_month_cleaned = (
            self.cleaned_email_dir / str(now.year) / f"{now.month:02d}"
        )
        year_month_raw.mkdir(parents=True, exist_ok=True)
        year_month_cleaned.mkdir(parents=True, exist_ok=True)

    def validate_gmail_credentials(self) -> bool:
        """Check if Gmail credentials file exists.

        Returns:
            True if credentials file exists, False otherwise
        """
        return self.gmail_credentials_path.exists()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    This function uses lru_cache to ensure settings are loaded only once
    per application run.

    Returns:
        Settings instance loaded from environment

    Example:
        >>> settings = get_settings()
        >>> print(settings.gmail_batch_size)
        50
    """
    return Settings()
