"""
Alert manager for critical error notifications.

Handles detection, batching, and delivery of critical alerts.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Optional

from config.settings import get_settings
from admin_reporting.config import ReportingConfig
from admin_reporting.models import ActionableAlert, AlertSeverity
from email_sender.gmail_sender import GmailSender
from models.daemon_state import DaemonProcessState

logger = logging.getLogger(__name__)


@dataclass
class AlertBatch:
    """
    Container for batched alerts.

    Attributes:
        alerts: List of alerts in this batch
        started_at: When this batch was started
    """

    alerts: list[ActionableAlert] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_empty(self) -> bool:
        """Check if batch has no alerts."""
        return len(self.alerts) == 0

    def has_critical(self) -> bool:
        """Check if batch contains critical alerts."""
        return any(a.severity == AlertSeverity.CRITICAL for a in self.alerts)

    def get_highest_severity(self) -> Optional[AlertSeverity]:
        """Get highest severity in batch."""
        if not self.alerts:
            return None
        return max(self.alerts, key=lambda a: a.severity.value).severity


class AlertManager:
    """
    Manages critical error alerts with batching and rate limiting.

    Features:
    - Threshold-based alert detection
    - Alert batching with configurable time window
    - Rate limiting (max alerts per hour)
    - Alert deduplication
    - Critical alert fast-path

    Attributes:
        config: ReportingConfig with alert settings
        batch_window: Time window for batching alerts
        max_alerts_per_hour: Maximum alerts allowed per hour
        current_batch: Current batch being accumulated
        sent_alerts_history: History of sent alert timestamps
    """

    # Default thresholds
    DEFAULT_ERROR_RATE_THRESHOLD = 0.1  # 10%
    DEFAULT_STALE_CHECK_MINUTES = 60  # 1 hour without check
    DEFAULT_BATCH_WINDOW_MINUTES = 15
    DEFAULT_MAX_ALERTS_PER_HOUR = 5

    def __init__(self, config: Optional[ReportingConfig] = None):
        """
        Initialize AlertManager.

        Args:
            config: ReportingConfig instance. If None, loads from environment.
        """
        self.settings = get_settings()

        if config is not None:
            self.config = config
        else:
            self.config = ReportingConfig.from_env()

        # Configure thresholds
        self.error_rate_threshold = (
            self.config.error_rate_threshold or self.DEFAULT_ERROR_RATE_THRESHOLD
        )
        self.stale_check_minutes = self.DEFAULT_STALE_CHECK_MINUTES

        # Configure batching
        batch_minutes = (
            self.config.alert_batch_window_minutes
            if self.config.alert_batch_window_minutes is not None
            else self.DEFAULT_BATCH_WINDOW_MINUTES
        )
        self.batch_window = timedelta(minutes=batch_minutes)

        # Configure rate limiting
        self.max_alerts_per_hour = (
            self.config.max_alerts_per_hour
            if self.config.max_alerts_per_hour is not None
            else self.DEFAULT_MAX_ALERTS_PER_HOUR
        )

        # Initialize batch and history
        self.current_batch = AlertBatch()
        self.sent_alerts_history: list[datetime] = []

        # Lazy-initialize sender
        self._sender: Optional[GmailSender] = None

    @property
    def sender(self) -> GmailSender:
        """Lazy-initialize GmailSender."""
        if self._sender is None:
            self._sender = GmailSender(
                credentials_path=self.settings.get_gmail_credentials_path(),
                token_path=self.settings.gmail_token_path,
            )
        return self._sender

    @sender.setter
    def sender(self, value: GmailSender) -> None:
        """Allow setting sender for testing."""
        self._sender = value

    def check_thresholds(
        self, daemon_state: DaemonProcessState
    ) -> list[ActionableAlert]:
        """
        Check all thresholds and return any triggered alerts.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            List of triggered alerts
        """
        alerts = []

        # Check daemon status
        if daemon_state.current_status == "error":
            alerts.append(
                ActionableAlert(
                    severity=AlertSeverity.CRITICAL,
                    category="daemon",
                    message="Daemon is in error status",
                    remediation="Check daemon logs and restart if necessary. Review recent errors in the error log.",
                )
            )

        # Check error rate
        total_processed = daemon_state.emails_processed_count
        if total_processed > 0:
            error_rate = daemon_state.error_count / total_processed
            if error_rate > self.error_rate_threshold:
                alerts.append(
                    ActionableAlert(
                        severity=AlertSeverity.HIGH,
                        category="error_rate",
                        message=f"High error rate detected: {error_rate:.1%} (threshold: {self.error_rate_threshold:.1%})",
                        remediation="Review recent errors in the daemon state. Check for connectivity issues or API problems.",
                    )
                )

        # Check Gmail staleness
        now = datetime.now(UTC)
        if daemon_state.last_gmail_check:
            gmail_age = (
                now - daemon_state.last_gmail_check.replace(tzinfo=UTC)
                if daemon_state.last_gmail_check.tzinfo is None
                else now - daemon_state.last_gmail_check
            )
            if gmail_age > timedelta(minutes=self.stale_check_minutes):
                alerts.append(
                    ActionableAlert(
                        severity=AlertSeverity.HIGH,
                        category="gmail",
                        message=f"Gmail check is stale ({gmail_age.total_seconds() / 60:.0f} minutes since last check)",
                        remediation="Verify Gmail API connectivity. Check OAuth token validity. Review daemon process status.",
                    )
                )

        # Check Notion staleness
        if daemon_state.last_notion_check:
            notion_age = (
                now - daemon_state.last_notion_check.replace(tzinfo=UTC)
                if daemon_state.last_notion_check.tzinfo is None
                else now - daemon_state.last_notion_check
            )
            if notion_age > timedelta(minutes=self.stale_check_minutes):
                alerts.append(
                    ActionableAlert(
                        severity=AlertSeverity.HIGH,
                        category="notion",
                        message=f"Notion check is stale ({notion_age.total_seconds() / 60:.0f} minutes since last check)",
                        remediation="Verify Notion API connectivity. Check API key validity. Review daemon process status.",
                    )
                )

        return alerts

    def add_to_batch(self, alert: ActionableAlert) -> bool:
        """
        Add alert to current batch if not a duplicate.

        Args:
            alert: Alert to add

        Returns:
            True if added, False if duplicate
        """
        # Check for duplicates in current batch
        for existing in self.current_batch.alerts:
            if (
                existing.message == alert.message
                and existing.category == alert.category
            ):
                logger.debug(f"Duplicate alert ignored: {alert.message[:50]}")
                return False

        self.current_batch.alerts.append(alert)
        logger.info(
            f"Alert added to batch: [{alert.severity.name}] {alert.category}: {alert.message[:50]}"
        )
        return True

    def is_batch_ready(self) -> bool:
        """
        Check if batch is ready to send.

        Returns:
            True if batch has alerts and window has passed
        """
        if self.current_batch.is_empty():
            return False

        now = datetime.now(UTC)
        elapsed = now - self.current_batch.started_at
        return elapsed >= self.batch_window

    def should_send_immediately(self) -> bool:
        """
        Check if batch should be sent immediately (critical alerts).

        Returns:
            True if batch contains critical alerts
        """
        return self.current_batch.has_critical()

    def flush_batch(self) -> AlertBatch:
        """
        Flush current batch and start a new one.

        Returns:
            The flushed batch
        """
        flushed = self.current_batch
        self.current_batch = AlertBatch()
        return flushed

    def can_send_alert(self) -> bool:
        """
        Check if we can send an alert (rate limiting).

        Returns:
            True if under rate limit
        """
        self.cleanup_history()
        return len(self.sent_alerts_history) < self.max_alerts_per_hour

    def record_sent_alert(self) -> None:
        """Record that an alert was sent."""
        self.sent_alerts_history.append(datetime.now(UTC))

    def cleanup_history(self) -> None:
        """Remove old entries from sent alerts history."""
        cutoff = datetime.now(UTC) - timedelta(hours=1)
        self.sent_alerts_history = [
            ts for ts in self.sent_alerts_history if ts > cutoff
        ]

    def send_alert_batch(self) -> Optional[dict]:
        """
        Send the current alert batch if ready and under rate limit.

        Returns:
            Gmail API response dict or None if not sent
        """
        if self.current_batch.is_empty():
            logger.debug("No alerts to send")
            return None

        if not self.can_send_alert():
            logger.warning(
                f"Rate limit reached ({self.max_alerts_per_hour} alerts/hour). "
                f"Batch has {len(self.current_batch.alerts)} alerts waiting."
            )
            return None

        # Ensure sender is connected
        if not self.sender.is_connected():
            logger.info("Connecting to Gmail API for alert sending...")
            self.sender.connect()

        # Build alert email content
        batch = self.flush_batch()
        recipients = self.config.alert_recipients or self.config.recipients

        # Determine subject severity
        severity = batch.get_highest_severity()
        severity_prefix = f"[{severity.name}]" if severity else ""

        subject = (
            f"{severity_prefix} CollabIQ Alert - {len(batch.alerts)} issue(s) detected"
        )

        # Build HTML and text content
        html_body = self._render_alert_html(batch)
        text_body = self._render_alert_text(batch)

        result = self.sender.send_alert_email(
            to=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

        self.record_sent_alert()
        logger.info(f"Alert batch sent to {recipients}, message ID: {result.get('id')}")

        return result

    def _render_alert_html(self, batch: AlertBatch) -> str:
        """Render alert batch to HTML."""
        alerts_html = ""
        for alert in batch.alerts:
            color = self._severity_color(alert.severity)
            alerts_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; border-left: 4px solid {color}; background: #f9f9f9;">
                <div style="font-weight: bold; color: {color};">[{alert.severity.name}] {alert.category.upper()}</div>
                <div style="margin: 5px 0;">{alert.message}</div>
                <div style="color: #666; font-size: 0.9em;"><strong>Remediation:</strong> {alert.remediation}</div>
            </div>
            """

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #d32f2f;">CollabIQ Alert Notification</h2>
            <p>The following issues require attention:</p>
            {alerts_html}
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #666; font-size: 0.9em;">
                This is an automated alert from CollabIQ Admin Reporting.
                Generated at {datetime.now(UTC).isoformat()}
            </p>
        </body>
        </html>
        """

    def _render_alert_text(self, batch: AlertBatch) -> str:
        """Render alert batch to plain text."""
        lines = [
            "CollabIQ Alert Notification",
            "=" * 40,
            "",
            "The following issues require attention:",
            "",
        ]

        for alert in batch.alerts:
            lines.append(f"[{alert.severity.name}] {alert.category.upper()}")
            lines.append(f"  {alert.message}")
            lines.append(f"  Remediation: {alert.remediation}")
            lines.append("")

        lines.append("-" * 40)
        lines.append(f"Generated at {datetime.now(UTC).isoformat()}")

        return "\n".join(lines)

    def _severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level."""
        colors = {
            AlertSeverity.CRITICAL: "#d32f2f",
            AlertSeverity.HIGH: "#f57c00",
            AlertSeverity.MEDIUM: "#fbc02d",
            AlertSeverity.LOW: "#388e3c",
        }
        return colors.get(severity, "#666")

    def process_alerts(self, daemon_state: DaemonProcessState) -> list[ActionableAlert]:
        """
        Main entry point: check thresholds, batch alerts, send if ready.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            List of alerts that were detected
        """
        # Check thresholds
        alerts = self.check_thresholds(daemon_state)

        # Add to batch
        for alert in alerts:
            self.add_to_batch(alert)

        # Check if we should send
        if self.should_send_immediately():
            logger.info("Critical alert detected - sending immediately")
            self.send_alert_batch()
        elif self.is_batch_ready():
            logger.info("Batch window passed - sending accumulated alerts")
            self.send_alert_batch()

        return alerts

    # ========================================================================
    # Actionable Insights (T046-T049)
    # ========================================================================

    # Default warning thresholds
    TOKEN_EXPIRY_WARNING_DAYS = 7  # Warn when token expires in 7 days
    COST_WARNING_THRESHOLD = 0.8  # Warn at 80% of daily limit

    def check_credential_expiry(
        self, daemon_state: DaemonProcessState
    ) -> list[ActionableAlert]:
        """
        Check for expiring or expired credentials (T046).

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            List of credential-related alerts
        """
        alerts = []
        now = datetime.now(UTC)

        # Check Gmail token expiry
        if daemon_state.gmail_token_expiry:
            expiry = daemon_state.gmail_token_expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=UTC)

            time_until_expiry = expiry - now

            if time_until_expiry.total_seconds() < 0:
                # Token is expired
                alerts.append(
                    ActionableAlert(
                        severity=AlertSeverity.HIGH,
                        category="credential",
                        message=f"Gmail OAuth token has expired ({abs(time_until_expiry.days)} days ago)",
                        remediation="Re-authenticate Gmail by running 'collabiq config oauth-refresh' or delete the token file and restart the daemon to trigger re-authentication.",
                    )
                )
            elif time_until_expiry.days <= self.TOKEN_EXPIRY_WARNING_DAYS:
                # Token expiring soon
                alerts.append(
                    ActionableAlert(
                        severity=AlertSeverity.MEDIUM,
                        category="credential",
                        message=f"Gmail OAuth token expires in {time_until_expiry.days} days",
                        remediation="Plan to re-authenticate Gmail soon. Run 'collabiq config oauth-refresh' or restart daemon when convenient to refresh the token.",
                    )
                )

        return alerts

    def check_cost_limits(
        self, daemon_state: DaemonProcessState
    ) -> list[ActionableAlert]:
        """
        Check for LLM cost threshold warnings (T048).

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            List of cost-related alerts
        """
        alerts = []

        # Calculate total cost
        total_cost = sum(daemon_state.llm_costs_by_provider.values())
        if total_cost == 0:
            return alerts

        daily_limit = self.config.cost_limit_daily
        cost_ratio = total_cost / daily_limit

        if cost_ratio >= 1.0:
            # Over budget
            alerts.append(
                ActionableAlert(
                    severity=AlertSeverity.HIGH,
                    category="cost",
                    message=f"Daily LLM cost budget exceeded: ${total_cost:.2f} / ${daily_limit:.2f} ({cost_ratio:.0%})",
                    remediation="Review LLM usage patterns. Consider reducing processing volume, switching to cheaper providers (e.g., Gemini Flash), or increasing daily budget limit.",
                )
            )
        elif cost_ratio >= self.COST_WARNING_THRESHOLD:
            # Approaching budget
            alerts.append(
                ActionableAlert(
                    severity=AlertSeverity.MEDIUM,
                    category="cost",
                    message=f"LLM cost approaching daily limit: ${total_cost:.2f} / ${daily_limit:.2f} ({cost_ratio:.0%})",
                    remediation="Monitor usage closely. Consider optimizing prompts or reducing batch sizes if budget is tight.",
                )
            )

        return alerts

    def check_error_rate_trend(
        self, daemon_state: DaemonProcessState
    ) -> list[ActionableAlert]:
        """
        Check for increasing error rate trends (T047).

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            List of trend-related alerts
        """
        alerts = []

        # Simple error rate check (more sophisticated trend analysis could be added)
        total_processed = daemon_state.emails_processed_count
        if total_processed == 0:
            return alerts

        error_rate = daemon_state.error_count / total_processed

        # Only alert if error rate exceeds threshold but is not critical
        # (critical errors are handled by check_thresholds)
        if (
            error_rate > self.error_rate_threshold * 0.7
            and error_rate <= self.error_rate_threshold
        ):
            # Approaching threshold
            alerts.append(
                ActionableAlert(
                    severity=AlertSeverity.LOW,
                    category="trend",
                    message=f"Error rate approaching threshold: {error_rate:.1%} (threshold: {self.error_rate_threshold:.1%})",
                    remediation="Review recent error patterns in the logs. Consider investigating common failure modes before rate becomes critical.",
                )
            )

        return alerts

    def collect_actionable_insights(
        self, daemon_state: DaemonProcessState
    ) -> list[ActionableAlert]:
        """
        Collect all actionable insights for daily report (T049, T050).

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            List of all actionable alerts for the daily report
        """
        insights = []

        # Collect from all insight sources
        insights.extend(self.check_credential_expiry(daemon_state))
        insights.extend(self.check_cost_limits(daemon_state))
        insights.extend(self.check_error_rate_trend(daemon_state))
        insights.extend(self.check_thresholds(daemon_state))

        # Deduplicate by message
        seen_messages = set()
        unique_insights = []
        for insight in insights:
            if insight.message not in seen_messages:
                seen_messages.add(insight.message)
                unique_insights.append(insight)

        # Sort by severity (critical first)
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.WARNING: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4,
        }
        unique_insights.sort(key=lambda a: severity_order.get(a.severity, 5))

        return unique_insights
