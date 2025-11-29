"""
Configuration for Admin Reporting.

Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class ReportingConfig(BaseModel):
    """Configuration for admin reporting system."""

    # Feature toggle
    enabled: bool = Field(
        default=True,
        description="Enable/disable admin reporting",
    )

    # Recipients
    recipients: list[str] = Field(
        default_factory=lambda: ["jeffreylim@signite.co"],
        description="Email addresses to receive reports",
    )
    alert_recipients: list[str] = Field(
        default_factory=list,
        description="Email addresses for critical alerts (defaults to recipients if empty)",
    )

    # Schedule
    report_time: str = Field(
        default="07:00",
        description="Daily report time in HH:MM format (24-hour)",
    )
    timezone: str = Field(
        default="Asia/Seoul",
        description="IANA timezone for schedule",
    )

    # Alert thresholds
    error_rate_threshold: float = Field(
        default=0.05,
        description="Error rate (0-1) to trigger warning alert",
    )
    cost_limit_daily: float = Field(
        default=10.0,
        description="Daily LLM cost limit in USD",
    )

    # Alert batching and rate limiting
    alert_batch_window_minutes: int = Field(
        default=15,
        description="Time window in minutes to batch alerts before sending",
    )
    max_alerts_per_hour: int = Field(
        default=5,
        description="Maximum number of alert emails per hour (rate limit)",
    )

    # Archiving
    archive_directory: Path = Field(
        default=Path("data/reports"),
        description="Directory for archived reports",
    )
    retention_days: int = Field(
        default=30,
        description="Days to retain archived reports",
    )

    @field_validator("report_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate HH:MM format."""
        try:
            parts = v.split(":")
            if len(parts) != 2:
                raise ValueError
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid time format: {v}. Expected HH:MM (24-hour)")
        return v

    @field_validator("error_rate_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(f"Error rate threshold must be between 0 and 1, got {v}")
        return v

    @field_validator("retention_days")
    @classmethod
    def validate_retention(cls, v: int) -> int:
        """Validate retention is positive."""
        if v < 1:
            raise ValueError(f"Retention days must be positive, got {v}")
        return v

    @classmethod
    def from_env(cls) -> "ReportingConfig":
        """Load configuration from environment variables."""
        recipients_str = os.getenv("ADMIN_REPORT_RECIPIENTS", "jeffreylim@signite.co")
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

        alert_recipients_str = os.getenv("ADMIN_ALERT_RECIPIENTS", "")
        alert_recipients = [
            r.strip() for r in alert_recipients_str.split(",") if r.strip()
        ]

        return cls(
            enabled=os.getenv("ADMIN_REPORTING_ENABLED", "true").lower() == "true",
            recipients=recipients,
            alert_recipients=alert_recipients,
            report_time=os.getenv("ADMIN_REPORT_TIME", "07:00"),
            timezone=os.getenv("ADMIN_REPORT_TIMEZONE", "Asia/Seoul"),
            error_rate_threshold=float(os.getenv("ADMIN_ERROR_RATE_THRESHOLD", "0.05")),
            cost_limit_daily=float(os.getenv("ADMIN_COST_LIMIT_DAILY", "10.0")),
            alert_batch_window_minutes=int(
                os.getenv("ADMIN_ALERT_BATCH_WINDOW_MINUTES", "15")
            ),
            max_alerts_per_hour=int(os.getenv("ADMIN_MAX_ALERTS_PER_HOUR", "5")),
            archive_directory=Path(
                os.getenv("ADMIN_REPORT_ARCHIVE_DIR", "data/reports")
            ),
            retention_days=int(os.getenv("ADMIN_REPORT_RETENTION_DAYS", "30")),
        )
