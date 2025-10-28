"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Gemini API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    # Notion API Configuration
    notion_api_key: str
    notion_database_id_radar: str
    notion_database_id_startup: str
    notion_database_id_corp: str

    # Email Infrastructure (optional - depends on selected approach)
    gmail_credentials_path: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Processing Configuration
    fuzzy_match_threshold: float = 0.85
    confidence_threshold: float = 0.85
    max_retries: int = 3
    retry_delay_seconds: int = 5

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
