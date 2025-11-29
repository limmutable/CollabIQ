"""
Data models for Admin Reporting.

Defines the structure of reports, alerts, and related entities.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status of a system component."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class AlertSeverity(str, Enum):
    """Severity level of an alert."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"  # Alias for HIGH
    INFO = "info"  # Alias for LOW


class AlertCategory(str, Enum):
    """Category/type of an alert."""

    CREDENTIAL_EXPIRY = "credential_expiry"
    ERROR_RATE = "error_rate"
    COST_OVERRUN = "cost_overrun"
    COMPONENT_FAILURE = "component_failure"
    CAPACITY = "capacity"


class DeliveryStatus(str, Enum):
    """Status of notification delivery."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


# ============================================================
# Component Health Models
# ============================================================


class ComponentHealthSummary(BaseModel):
    """Health status of system components."""

    gmail_status: HealthStatus = Field(default=HealthStatus.OPERATIONAL)
    gmail_token_expiry: Optional[datetime] = None
    notion_status: HealthStatus = Field(default=HealthStatus.OPERATIONAL)
    llm_providers: dict[str, HealthStatus] = Field(default_factory=dict)
    overall_status: HealthStatus = Field(default=HealthStatus.OPERATIONAL)

    def compute_overall(self) -> None:
        """Compute overall status from component statuses."""
        statuses = [self.gmail_status, self.notion_status]
        statuses.extend(self.llm_providers.values())

        if any(s == HealthStatus.UNAVAILABLE for s in statuses):
            self.overall_status = HealthStatus.UNAVAILABLE
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.OPERATIONAL


# ============================================================
# Processing Metrics Models
# ============================================================


class ProcessingMetrics(BaseModel):
    """Email processing statistics for a reporting period."""

    emails_received: int = 0
    emails_processed: int = 0
    emails_skipped: int = 0
    success_rate: float = 0.0
    average_processing_time_seconds: float = 0.0
    processing_cycles: int = 0

    def compute_success_rate(self) -> None:
        """Compute success rate from processed/received counts."""
        if self.emails_received > 0:
            self.success_rate = self.emails_processed / self.emails_received
        else:
            self.success_rate = 1.0  # No emails = 100% success


class ErrorCategory(BaseModel):
    """Error category with count for summarization."""

    category: str
    count: int
    sample_message: str = ""


class ErrorSummary(BaseModel):
    """Aggregated error information for a reporting period."""

    critical_errors: list[dict] = Field(default_factory=list)
    high_errors: list[dict] = Field(default_factory=list)
    low_error_count: int = 0
    total_error_count: int = 0
    error_rate: float = 0.0
    top_error_categories: list[ErrorCategory] = Field(default_factory=list)


class LLMUsageSummary(BaseModel):
    """LLM provider usage and costs for a reporting period."""

    calls_by_provider: dict[str, int] = Field(default_factory=dict)
    costs_by_provider: dict[str, float] = Field(default_factory=dict)
    total_calls: int = 0
    total_cost: float = 0.0
    provider_health: dict[str, HealthStatus] = Field(default_factory=dict)
    primary_provider: Optional[str] = None

    def compute_totals(self) -> None:
        """Compute total calls and costs from per-provider data."""
        self.total_calls = sum(self.calls_by_provider.values())
        self.total_cost = sum(self.costs_by_provider.values())
        if self.calls_by_provider:
            self.primary_provider = max(
                self.calls_by_provider, key=self.calls_by_provider.get
            )


class NotionStats(BaseModel):
    """Notion database operation statistics for a reporting period."""

    entries_created: int = 0
    entries_updated: int = 0
    entries_skipped: int = 0
    validation_failures: int = 0
    database_health: HealthStatus = Field(default=HealthStatus.OPERATIONAL)


# ============================================================
# Alert Models
# ============================================================


class ActionableAlert(BaseModel):
    """Alert requiring administrator attention."""

    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    severity: AlertSeverity
    category: str = Field(description="Alert category (string for flexibility)")
    title: str = Field(default="", description="Optional short title")
    message: str
    remediation: str
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = False


class AlertNotification(BaseModel):
    """Record of alert delivery."""

    notification_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_ids: list[str] = Field(default_factory=list)
    sent_at: datetime = Field(default_factory=datetime.now)
    delivery_method: str = "email"
    recipients: list[str] = Field(default_factory=list)
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    retry_count: int = 0
    error_message: Optional[str] = None


# ============================================================
# Report Models
# ============================================================


class DailyReportData(BaseModel):
    """Aggregated metrics for a 24-hour reporting period."""

    report_id: str = Field(default_factory=lambda: str(uuid4()))
    report_date: date = Field(default_factory=date.today)
    generated_at: datetime = Field(default_factory=datetime.now)
    period_start: datetime
    period_end: datetime

    # Metrics sections
    health_status: ComponentHealthSummary = Field(
        default_factory=ComponentHealthSummary
    )
    processing_metrics: ProcessingMetrics = Field(default_factory=ProcessingMetrics)
    error_summary: ErrorSummary = Field(default_factory=ErrorSummary)
    llm_usage: LLMUsageSummary = Field(default_factory=LLMUsageSummary)
    notion_stats: NotionStats = Field(default_factory=NotionStats)

    # Alerts
    actionable_alerts: list[ActionableAlert] = Field(default_factory=list)


class ArchivedReport(BaseModel):
    """Stored report for historical reference."""

    archive_id: str = Field(default_factory=lambda: str(uuid4()))
    report_date: date
    json_path: str
    html_path: str
    archived_at: datetime = Field(default_factory=datetime.now)
    size_bytes: int = 0
