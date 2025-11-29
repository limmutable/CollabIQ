from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta


class ErrorDetail(BaseModel):
    """Details of an error occurrence for reporting."""

    timestamp: datetime = Field(default_factory=datetime.now)
    severity: str = Field(..., description="Error severity: critical, high, low")
    component: str = Field(..., description="Component that raised the error: gmail, notion, llm, etc.")
    message: str = Field(..., description="Error message")
    context: dict = Field(default_factory=dict, description="Additional context data")


class DaemonProcessState(BaseModel):
    """
    Represents the state of the autonomous background operation daemon.
    """

    # Core daemon state
    daemon_start_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when the daemon was started.")
    last_check_timestamp: Optional[datetime] = Field(None, description="Timestamp of the last email check.")
    last_successful_fetch_timestamp: Optional[datetime] = Field(None, description="Timestamp of last successful email fetch. Used as 'since' filter for next run.")
    check_interval_duration: timedelta = Field(timedelta(minutes=15), description="Duration between email checks.")
    total_processing_cycles: int = Field(0, description="Total number of processing cycles completed.")
    emails_processed_count: int = Field(0, description="Total number of emails processed successfully.")
    error_count: int = Field(0, description="Total number of errors encountered.")
    current_status: str = Field("stopped", description="Current status of the daemon (running, stopped, error).")
    last_processed_email_id: Optional[str] = Field(None, description="The ID of the last email successfully processed to prevent duplicates.")

    # Extended metrics for admin reporting
    emails_received_count: int = Field(0, description="Total emails fetched from Gmail.")
    emails_skipped_count: int = Field(0, description="Emails skipped (duplicates, filtered).")
    llm_calls_by_provider: dict[str, int] = Field(default_factory=dict, description="API calls per LLM provider.")
    llm_costs_by_provider: dict[str, float] = Field(default_factory=dict, description="Estimated costs per LLM provider.")
    notion_entries_created: int = Field(0, description="Notion entries created.")
    notion_entries_updated: int = Field(0, description="Notion entries updated.")
    notion_validation_failures: int = Field(0, description="Notion schema validation failures.")

    # Error tracking for reporting
    recent_errors: list[dict] = Field(default_factory=list, description="Last 100 errors with details.")

    # Component health tracking
    last_gmail_check: Optional[datetime] = Field(None, description="Last successful Gmail API check.")
    last_notion_check: Optional[datetime] = Field(None, description="Last successful Notion API check.")
    gmail_token_expiry: Optional[datetime] = Field(None, description="Gmail OAuth token expiry time.")

    # Reporting state
    last_report_generated: Optional[datetime] = Field(None, description="Last daily report generation time.")
    last_alert_sent: Optional[datetime] = Field(None, description="Last critical alert sent time.")

    def record_error(self, severity: str, component: str, message: str, context: dict | None = None) -> None:
        """Record an error for reporting. Keeps last 100 errors."""
        error = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "component": component,
            "message": message,
            "context": context or {},
        }
        self.recent_errors.append(error)
        # Keep only last 100 errors
        if len(self.recent_errors) > 100:
            self.recent_errors = self.recent_errors[-100:]
        self.error_count += 1

    def record_llm_call(self, provider: str, cost: float = 0.0) -> None:
        """Record an LLM API call with estimated cost."""
        self.llm_calls_by_provider[provider] = self.llm_calls_by_provider.get(provider, 0) + 1
        self.llm_costs_by_provider[provider] = self.llm_costs_by_provider.get(provider, 0.0) + cost

    def record_notion_operation(self, operation: str, success: bool) -> None:
        """Record a Notion database operation."""
        if success:
            if operation == "create":
                self.notion_entries_created += 1
            elif operation == "update":
                self.notion_entries_updated += 1
        else:
            self.notion_validation_failures += 1
