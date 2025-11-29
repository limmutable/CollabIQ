"""
Report generator for Admin Reporting.

Generates and sends daily admin reports.
"""

import logging
from datetime import datetime, date, timedelta, UTC
from typing import Optional, Tuple

from config.settings import get_settings
from admin_reporting.config import ReportingConfig
from admin_reporting.collector import MetricsCollector
from admin_reporting.models import (
    DailyReportData,
    ComponentHealthSummary,
)
from admin_reporting.renderer import ReportRenderer
from admin_reporting.alerter import AlertManager
from admin_reporting.archiver import ReportArchiver
from email_sender.gmail_sender import GmailSender
from models.daemon_state import DaemonProcessState

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates and sends admin reports.

    Orchestrates metrics collection, report rendering, and email delivery.

    Attributes:
        config: ReportingConfig with schedule and recipients
        settings: Application settings
        renderer: ReportRenderer for HTML/text generation
        sender: GmailSender for email delivery
    """

    def __init__(self, config: Optional[ReportingConfig] = None):
        """
        Initialize ReportGenerator.

        Args:
            config: ReportingConfig instance. If None, loads from environment.
        """
        self.settings = get_settings()

        if config is not None:
            self.config = config
        else:
            self.config = ReportingConfig.from_env()

        self.renderer = ReportRenderer()
        self._sender: Optional[GmailSender] = None
        self._alert_manager: Optional[AlertManager] = None
        self._archiver: Optional[ReportArchiver] = None

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

    @property
    def alert_manager(self) -> AlertManager:
        """Lazy-initialize AlertManager."""
        if self._alert_manager is None:
            self._alert_manager = AlertManager(config=self.config)
        return self._alert_manager

    @alert_manager.setter
    def alert_manager(self, value: AlertManager) -> None:
        """Allow setting alert manager for testing."""
        self._alert_manager = value

    @property
    def archiver(self) -> ReportArchiver:
        """Lazy-initialize ReportArchiver."""
        if self._archiver is None:
            self._archiver = ReportArchiver(config=self.config)
        return self._archiver

    @archiver.setter
    def archiver(self, value: ReportArchiver) -> None:
        """Allow setting archiver for testing."""
        self._archiver = value

    def generate_daily_report(
        self,
        daemon_state: DaemonProcessState,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> DailyReportData:
        """
        Generate daily report data from daemon state.

        Args:
            daemon_state: Current DaemonProcessState with metrics
            period_start: Start of reporting period (default: 24 hours ago)
            period_end: End of reporting period (default: now)

        Returns:
            DailyReportData with all metrics collected
        """
        now = datetime.now(UTC)
        period_end = period_end or now
        period_start = period_start or (period_end - timedelta(hours=24))

        logger.info(f"Generating daily report for {period_start} to {period_end}")

        # Collect metrics
        collector = MetricsCollector(
            daemon_state=daemon_state,
            period_start=period_start,
            period_end=period_end,
        )

        metrics = collector.collect_all()

        # Collect actionable insights
        actionable_alerts = self.alert_manager.collect_actionable_insights(daemon_state)
        if actionable_alerts:
            logger.info(
                f"Found {len(actionable_alerts)} actionable insights for daily report"
            )

        # Build report
        report = DailyReportData(
            report_date=date.today(),
            generated_at=now,
            period_start=period_start,
            period_end=period_end,
            health_status=metrics["health_status"],
            processing_metrics=metrics["processing_metrics"],
            error_summary=metrics["error_summary"],
            llm_usage=metrics["llm_usage"],
            notion_stats=metrics["notion_stats"],
            actionable_alerts=actionable_alerts,
        )

        logger.info(f"Generated report {report.report_id} for {report.report_date}")
        return report

    def check_component_health(
        self, daemon_state: DaemonProcessState
    ) -> ComponentHealthSummary:
        """
        Check health status of all system components.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            ComponentHealthSummary with health status of all components
        """
        collector = MetricsCollector(daemon_state)
        return collector.collect_component_health()

    def render_report(self, report_data: DailyReportData) -> Tuple[str, str]:
        """
        Render report to HTML and plain text.

        Args:
            report_data: DailyReportData to render

        Returns:
            Tuple of (html_content, text_content)
        """
        html = self.renderer.render_daily_report_html(report_data)
        text = self.renderer.render_daily_report_text(report_data)
        return html, text

    def send_report(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str,
    ) -> dict:
        """
        Send rendered report via email.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            html_body: HTML content
            text_body: Plain text content

        Returns:
            Gmail API response dict
        """
        # Ensure sender is connected
        if not self.sender.is_connected():
            logger.info("Connecting to Gmail API for sending...")
            self.sender.connect()

        result = self.sender.send_report_email(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

        logger.info(f"Report sent to {to}, message ID: {result.get('id')}")
        return result

    def generate_and_send(
        self,
        daemon_state: DaemonProcessState,
        recipients: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate and send daily report in one call.

        Args:
            daemon_state: Current DaemonProcessState with metrics
            recipients: Override recipient list (default: from config)

        Returns:
            Dict with 'report' (DailyReportData) and 'send_result' (API response)
        """
        # Generate report
        report = self.generate_daily_report(daemon_state)

        # Render
        html, text = self.render_report(report)

        # Determine recipients
        to = recipients or self.config.recipients

        # Build subject
        subject = f"CollabIQ Daily Report - {report.report_date.isoformat()}"

        # Send
        send_result = self.send_report(
            to=to,
            subject=subject,
            html_body=html,
            text_body=text,
        )

        # Archive report
        try:
            archive_result = self.archiver.archive_report(report, html_content=html)
            logger.info(f"Report archived to {archive_result.json_path}")

            # Cleanup old archives
            removed = self.archiver.cleanup_old_reports()
            if removed > 0:
                logger.info(f"Cleaned up {removed} old archive files")
        except Exception as e:
            logger.warning(f"Failed to archive report: {e}")
            # Don't fail the overall operation if archiving fails

        # Update daemon state
        daemon_state.last_report_generated = datetime.now(UTC)

        return {
            "report": report,
            "send_result": send_result,
        }

    def collect_processing_metrics(self, daemon_state: DaemonProcessState) -> dict:
        """
        Collect processing metrics from daemon state.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            ProcessingMetrics instance
        """
        collector = MetricsCollector(daemon_state)
        return collector.collect_processing_metrics()

    def collect_error_summary(self, daemon_state: DaemonProcessState) -> dict:
        """
        Collect error summary from daemon state.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            ErrorSummary instance
        """
        collector = MetricsCollector(daemon_state)
        return collector.collect_error_summary()

    def collect_llm_usage(self, daemon_state: DaemonProcessState) -> dict:
        """
        Collect LLM usage metrics from daemon state.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            LLMUsageSummary instance
        """
        collector = MetricsCollector(daemon_state)
        return collector.collect_llm_usage()

    def collect_notion_stats(self, daemon_state: DaemonProcessState) -> dict:
        """
        Collect Notion stats from daemon state.

        Args:
            daemon_state: Current DaemonProcessState

        Returns:
            NotionStats instance
        """
        collector = MetricsCollector(daemon_state)
        return collector.collect_notion_stats()
