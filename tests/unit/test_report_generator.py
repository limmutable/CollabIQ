"""
Unit tests for ReportGenerator class.

Tests report generation and delivery functionality.
"""

import pytest
from datetime import datetime, date, timedelta, UTC
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from admin_reporting.models import (
    DailyReportData,
    ComponentHealthSummary,
    ProcessingMetrics,
    ErrorSummary,
    LLMUsageSummary,
    NotionStats,
    ActionableAlert,
    HealthStatus,
    AlertSeverity,
    AlertCategory,
)
from models.daemon_state import DaemonProcessState


class TestReportGeneratorInit:
    """Tests for ReportGenerator initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default settings."""
        from admin_reporting.reporter import ReportGenerator

        with patch("admin_reporting.reporter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                admin_report_recipients="test@example.com",
                admin_report_time="07:00",
                admin_report_timezone="Asia/Seoul",
            )
            generator = ReportGenerator()

            assert generator.settings is not None
            assert generator.renderer is not None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        from admin_reporting.reporter import ReportGenerator
        from admin_reporting.config import ReportingConfig

        config = ReportingConfig(
            recipients=["admin@test.com"],
            report_time="08:00",
            timezone="UTC",
        )

        with patch("admin_reporting.reporter.get_settings"):
            generator = ReportGenerator(config=config)

            assert generator.config.recipients == ["admin@test.com"]
            assert generator.config.report_time == "08:00"


class TestGenerateDailyReport:
    """Tests for generate_daily_report method."""

    @pytest.fixture
    def generator(self):
        """Create ReportGenerator with mocked dependencies."""
        from admin_reporting.reporter import ReportGenerator

        with patch("admin_reporting.reporter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                admin_report_recipients="test@example.com",
                admin_report_time="07:00",
                admin_report_timezone="Asia/Seoul",
            )
            gen = ReportGenerator()
            gen.renderer = MagicMock()
            return gen

    @pytest.fixture
    def sample_state(self):
        """Create sample DaemonProcessState."""
        state = DaemonProcessState()
        state.emails_received_count = 100
        state.emails_processed_count = 95
        state.emails_skipped_count = 5
        state.total_processing_cycles = 10
        state.last_gmail_check = datetime.now(UTC)
        state.last_notion_check = datetime.now(UTC)
        state.llm_calls_by_provider = {"gemini": 50}
        state.llm_costs_by_provider = {"gemini": 0.10}
        state.notion_entries_created = 45
        state.notion_entries_updated = 10
        return state

    def test_generates_report_data(self, generator, sample_state):
        """Test that generate_daily_report creates DailyReportData."""
        report = generator.generate_daily_report(sample_state)

        assert isinstance(report, DailyReportData)
        assert report.report_date == date.today()
        assert report.processing_metrics.emails_received == 100
        assert report.processing_metrics.emails_processed == 95

    def test_includes_health_status(self, generator, sample_state):
        """Test that report includes health status."""
        report = generator.generate_daily_report(sample_state)

        assert report.health_status is not None
        assert report.health_status.overall_status in HealthStatus

    def test_includes_llm_usage(self, generator, sample_state):
        """Test that report includes LLM usage."""
        report = generator.generate_daily_report(sample_state)

        assert report.llm_usage is not None
        assert "gemini" in report.llm_usage.calls_by_provider

    def test_includes_notion_stats(self, generator, sample_state):
        """Test that report includes Notion stats."""
        report = generator.generate_daily_report(sample_state)

        assert report.notion_stats is not None
        assert report.notion_stats.entries_created == 45


class TestRenderReport:
    """Tests for render_report method."""

    @pytest.fixture
    def generator(self):
        """Create ReportGenerator with mocked dependencies."""
        from admin_reporting.reporter import ReportGenerator

        with patch("admin_reporting.reporter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                admin_report_recipients="test@example.com",
                admin_report_time="07:00",
                admin_report_timezone="Asia/Seoul",
            )
            gen = ReportGenerator()
            gen.renderer = MagicMock()
            gen.renderer.render_daily_report_html.return_value = "<html>Report</html>"
            gen.renderer.render_daily_report_text.return_value = "Text Report"
            return gen

    @pytest.fixture
    def sample_report(self):
        """Create sample DailyReportData."""
        now = datetime.now(UTC)
        return DailyReportData(
            report_date=date.today(),
            period_start=now - timedelta(hours=24),
            period_end=now,
        )

    def test_renders_html_and_text(self, generator, sample_report):
        """Test that render_report produces both HTML and text."""
        html, text = generator.render_report(sample_report)

        assert html == "<html>Report</html>"
        assert text == "Text Report"

    def test_calls_renderer_methods(self, generator, sample_report):
        """Test that render_report calls renderer methods."""
        generator.render_report(sample_report)

        generator.renderer.render_daily_report_html.assert_called_once_with(sample_report)
        generator.renderer.render_daily_report_text.assert_called_once_with(sample_report)


class TestSendReport:
    """Tests for send_report method."""

    @pytest.fixture
    def generator(self):
        """Create ReportGenerator with mocked dependencies."""
        from admin_reporting.reporter import ReportGenerator

        with patch("admin_reporting.reporter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                admin_report_recipients="admin@test.com",
                admin_report_time="07:00",
                admin_report_timezone="Asia/Seoul",
                get_gmail_credentials_path=lambda: Path("/tmp/creds.json"),
                gmail_token_path=Path("/tmp/token.json"),
            )
            gen = ReportGenerator()
            gen.sender = MagicMock()
            gen.sender.send_report_email.return_value = {"id": "msg123"}
            return gen

    def test_sends_to_configured_recipients(self, generator):
        """Test that report is sent to configured recipients."""
        result = generator.send_report(
            to=["admin@test.com"],
            subject="Test Report",
            html_body="<html>Report</html>",
            text_body="Text Report",
        )

        assert result is not None
        generator.sender.send_report_email.assert_called_once()

    def test_formats_subject_with_date(self, generator):
        """Test that subject includes report date."""
        today = date.today()
        expected_subject = f"CollabIQ Daily Report - {today.isoformat()}"

        generator.send_report(
            to=["admin@test.com"],
            subject=expected_subject,
            html_body="<html>Report</html>",
            text_body="Text Report",
        )

        call_args = generator.sender.send_report_email.call_args
        assert today.isoformat() in call_args.kwargs.get("subject", call_args.args[1] if len(call_args.args) > 1 else "")


class TestCheckComponentHealth:
    """Tests for check_component_health method."""

    @pytest.fixture
    def generator(self):
        """Create ReportGenerator with mocked dependencies."""
        from admin_reporting.reporter import ReportGenerator

        with patch("admin_reporting.reporter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                admin_report_recipients="test@example.com",
                admin_report_time="07:00",
                admin_report_timezone="Asia/Seoul",
            )
            return ReportGenerator()

    def test_returns_operational_for_healthy_components(self, generator):
        """Test operational status when all components are healthy."""
        state = DaemonProcessState()
        state.last_gmail_check = datetime.now(UTC)
        state.last_notion_check = datetime.now(UTC)

        health = generator.check_component_health(state)

        assert health.overall_status == HealthStatus.OPERATIONAL

    def test_returns_degraded_for_stale_gmail(self, generator):
        """Test degraded status when Gmail check is stale."""
        state = DaemonProcessState()
        state.last_gmail_check = datetime.now(UTC) - timedelta(hours=1)
        state.last_notion_check = datetime.now(UTC)

        health = generator.check_component_health(state)

        assert health.gmail_status == HealthStatus.DEGRADED

    def test_returns_unavailable_when_no_check(self, generator):
        """Test unavailable status when no check has been performed."""
        state = DaemonProcessState()
        state.last_gmail_check = None
        state.last_notion_check = None

        health = generator.check_component_health(state)

        assert health.gmail_status == HealthStatus.UNAVAILABLE


class TestGenerateAndSend:
    """Tests for generate_and_send convenience method."""

    @pytest.fixture
    def generator(self):
        """Create ReportGenerator with mocked dependencies."""
        from admin_reporting.reporter import ReportGenerator

        with patch("admin_reporting.reporter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                admin_report_recipients="admin@test.com",
                admin_report_time="07:00",
                admin_report_timezone="Asia/Seoul",
                get_gmail_credentials_path=lambda: Path("/tmp/creds.json"),
                gmail_token_path=Path("/tmp/token.json"),
            )
            gen = ReportGenerator()
            gen.renderer = MagicMock()
            gen.renderer.render_daily_report_html.return_value = "<html>Report</html>"
            gen.renderer.render_daily_report_text.return_value = "Text Report"
            gen.sender = MagicMock()
            gen.sender.send_report_email.return_value = {"id": "msg123"}
            gen.sender.is_connected.return_value = True
            return gen

    def test_generates_and_sends_report(self, generator):
        """Test full generate and send workflow."""
        state = DaemonProcessState()
        state.last_gmail_check = datetime.now(UTC)
        state.last_notion_check = datetime.now(UTC)

        result = generator.generate_and_send(state)

        assert result is not None
        generator.renderer.render_daily_report_html.assert_called_once()
        generator.sender.send_report_email.assert_called_once()

    def test_returns_report_data(self, generator):
        """Test that generate_and_send returns report data."""
        state = DaemonProcessState()
        state.last_gmail_check = datetime.now(UTC)
        state.last_notion_check = datetime.now(UTC)

        result = generator.generate_and_send(state)

        assert "report" in result
        assert "send_result" in result
