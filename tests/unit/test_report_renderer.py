"""
Unit tests for ReportRenderer class.

Tests template rendering functionality.
"""

import pytest
from datetime import datetime, date, timedelta, UTC
from pathlib import Path

from admin_reporting.renderer import ReportRenderer, RenderError
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


class TestReportRendererInit:
    """Tests for ReportRenderer initialization."""

    def test_init_with_default_template_dir(self):
        """Test initialization with default template directory."""
        renderer = ReportRenderer()

        assert renderer.template_dir.exists()
        assert renderer.env is not None

    def test_init_with_custom_template_dir(self, tmp_path):
        """Test initialization with custom template directory."""
        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()

        renderer = ReportRenderer(template_dir=custom_dir)

        assert renderer.template_dir == custom_dir

    def test_creates_template_dir_if_missing(self, tmp_path):
        """Test that template directory is created if missing."""
        custom_dir = tmp_path / "new_templates"

        renderer = ReportRenderer(template_dir=custom_dir)

        assert custom_dir.exists()


class TestCustomFilters:
    """Tests for custom Jinja2 filters."""

    @pytest.fixture
    def renderer(self):
        """Create ReportRenderer instance."""
        return ReportRenderer()

    def test_format_datetime(self, renderer):
        """Test datetime formatting filter."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)

        result = renderer._format_datetime(dt)

        assert "2024-01-15" in result
        assert "10:30:45" in result

    def test_format_datetime_none(self, renderer):
        """Test datetime formatting with None."""
        result = renderer._format_datetime(None)
        assert result == "N/A"

    def test_format_date(self, renderer):
        """Test date formatting filter."""
        d = date(2024, 1, 15)

        result = renderer._format_date(d)

        assert result == "2024-01-15"

    def test_format_date_none(self, renderer):
        """Test date formatting with None."""
        result = renderer._format_date(None)
        assert result == "N/A"

    def test_format_percentage(self, renderer):
        """Test percentage formatting filter."""
        result = renderer._format_percentage(0.956)
        assert result == "95.6%"

    def test_format_currency(self, renderer):
        """Test currency formatting filter."""
        result = renderer._format_currency(1.2345)
        assert result == "$1.2345"

    def test_status_emoji_operational(self, renderer):
        """Test status emoji for operational."""
        result = renderer._status_emoji(HealthStatus.OPERATIONAL)
        assert result == "✅"

    def test_status_emoji_degraded(self, renderer):
        """Test status emoji for degraded."""
        result = renderer._status_emoji(HealthStatus.DEGRADED)
        assert result == "⚠️"

    def test_status_emoji_unavailable(self, renderer):
        """Test status emoji for unavailable."""
        result = renderer._status_emoji(HealthStatus.UNAVAILABLE)
        assert result == "❌"

    def test_status_color_operational(self, renderer):
        """Test status color for operational."""
        result = renderer._status_color(HealthStatus.OPERATIONAL)
        assert result == "#28a745"  # Green

    def test_severity_emoji_critical(self, renderer):
        """Test severity emoji for critical."""
        result = renderer._severity_emoji(AlertSeverity.CRITICAL)
        assert result == "🚨"

    def test_severity_emoji_warning(self, renderer):
        """Test severity emoji for warning."""
        result = renderer._severity_emoji(AlertSeverity.WARNING)
        assert result == "⚠️"


class TestRenderDailyReport:
    """Tests for daily report rendering."""

    @pytest.fixture
    def renderer(self):
        """Create ReportRenderer instance."""
        return ReportRenderer()

    @pytest.fixture
    def sample_report_data(self):
        """Create sample DailyReportData for testing."""
        now = datetime.now(UTC)
        return DailyReportData(
            report_date=date.today(),
            generated_at=now,
            period_start=now - timedelta(hours=24),
            period_end=now,
            health_status=ComponentHealthSummary(
                gmail_status=HealthStatus.OPERATIONAL,
                notion_status=HealthStatus.OPERATIONAL,
                llm_providers={"gemini": HealthStatus.OPERATIONAL},
                overall_status=HealthStatus.OPERATIONAL,
            ),
            processing_metrics=ProcessingMetrics(
                emails_received=100,
                emails_processed=95,
                emails_skipped=5,
                success_rate=0.95,
                processing_cycles=10,
            ),
            error_summary=ErrorSummary(
                total_error_count=5,
                error_rate=0.05,
                low_error_count=5,
            ),
            llm_usage=LLMUsageSummary(
                calls_by_provider={"gemini": 50, "claude": 25},
                costs_by_provider={"gemini": 0.10, "claude": 0.50},
                total_calls=75,
                total_cost=0.60,
                primary_provider="gemini",
            ),
            notion_stats=NotionStats(
                entries_created=45,
                entries_updated=10,
                entries_skipped=5,
                validation_failures=0,
                database_health=HealthStatus.OPERATIONAL,
            ),
        )

    def test_render_html_success(self, renderer, sample_report_data):
        """Test successful HTML rendering."""
        html = renderer.render_daily_report_html(sample_report_data)

        assert "<!DOCTYPE html>" in html
        assert "CollabIQ Daily Report" in html
        assert str(sample_report_data.report_date) in html
        assert "100" in html  # emails_received

    def test_render_html_includes_health_status(self, renderer, sample_report_data):
        """Test HTML includes health status section."""
        html = renderer.render_daily_report_html(sample_report_data)

        assert "System Health" in html
        assert "Gmail API" in html
        assert "Notion API" in html

    def test_render_html_includes_processing_metrics(self, renderer, sample_report_data):
        """Test HTML includes processing metrics."""
        html = renderer.render_daily_report_html(sample_report_data)

        assert "Processing Metrics" in html
        assert "95" in html  # emails_processed
        assert "95.0%" in html  # success_rate

    def test_render_html_includes_llm_usage(self, renderer, sample_report_data):
        """Test HTML includes LLM usage section."""
        html = renderer.render_daily_report_html(sample_report_data)

        assert "LLM Provider Usage" in html
        assert "Gemini" in html
        assert "75" in html  # total_calls

    def test_render_html_includes_notion_stats(self, renderer, sample_report_data):
        """Test HTML includes Notion stats."""
        html = renderer.render_daily_report_html(sample_report_data)

        assert "Notion Database Stats" in html
        assert "45" in html  # entries_created

    def test_render_text_success(self, renderer, sample_report_data):
        """Test successful plain text rendering."""
        text = renderer.render_daily_report_text(sample_report_data)

        assert "COLLABIQ DAILY REPORT" in text
        assert "System Health" in text.upper() or "SYSTEM HEALTH" in text
        assert "Processing Metrics" in text.upper() or "PROCESSING METRICS" in text

    def test_render_text_includes_metrics(self, renderer, sample_report_data):
        """Test plain text includes metrics."""
        text = renderer.render_daily_report_text(sample_report_data)

        assert "100" in text  # emails_received
        assert "95" in text  # emails_processed

    def test_render_html_with_alerts(self, renderer, sample_report_data):
        """Test HTML rendering with actionable alerts."""
        sample_report_data.actionable_alerts = [
            ActionableAlert(
                severity=AlertSeverity.WARNING,
                category=AlertCategory.CREDENTIAL_EXPIRY,
                title="Gmail Token Expiring",
                message="OAuth token expires in 5 days",
                remediation="Re-authenticate Gmail OAuth",
            )
        ]

        html = renderer.render_daily_report_html(sample_report_data)

        assert "Actionable Alerts" in html
        assert "Gmail Token Expiring" in html
        assert "Re-authenticate" in html

    def test_render_html_without_alerts(self, renderer, sample_report_data):
        """Test HTML shows 'no alerts' message when no alerts."""
        sample_report_data.actionable_alerts = []

        html = renderer.render_daily_report_html(sample_report_data)

        assert "No actionable alerts" in html


class TestRenderAlerts:
    """Tests for alert rendering."""

    @pytest.fixture
    def renderer(self):
        """Create ReportRenderer instance."""
        return ReportRenderer()

    @pytest.fixture
    def sample_alerts(self):
        """Create sample alerts for testing."""
        return [
            ActionableAlert(
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.ERROR_RATE,
                title="High Error Rate",
                message="Error rate exceeded 5% threshold",
                remediation="Check recent errors and investigate root cause",
            ),
            ActionableAlert(
                severity=AlertSeverity.WARNING,
                category=AlertCategory.COST_OVERRUN,
                title="LLM Cost Warning",
                message="Daily LLM costs approaching limit",
                remediation="Review LLM usage patterns",
            ),
        ]

    def test_render_alert_html_template_missing(self, renderer, sample_alerts, tmp_path):
        """Test error when alert HTML template missing."""
        renderer_no_templates = ReportRenderer(template_dir=tmp_path)

        with pytest.raises(RenderError) as exc_info:
            renderer_no_templates.render_alert_html(sample_alerts)

        assert "critical_alert.html.j2" in str(exc_info.value)

    def test_render_alert_text_template_missing(self, renderer, sample_alerts, tmp_path):
        """Test error when alert text template missing."""
        renderer_no_templates = ReportRenderer(template_dir=tmp_path)

        with pytest.raises(RenderError) as exc_info:
            renderer_no_templates.render_alert_text(sample_alerts)

        assert "critical_alert.txt.j2" in str(exc_info.value)


class TestTemplateExists:
    """Tests for template_exists method."""

    @pytest.fixture
    def renderer(self):
        """Create ReportRenderer instance."""
        return ReportRenderer()

    def test_template_exists_returns_true_for_existing(self, renderer):
        """Test template_exists returns True for existing template."""
        # daily_report.html.j2 should exist
        assert renderer.template_exists("daily_report.html.j2") is True

    def test_template_exists_returns_false_for_missing(self, renderer):
        """Test template_exists returns False for missing template."""
        assert renderer.template_exists("nonexistent.html.j2") is False


class TestRenderErrors:
    """Tests for render error handling."""

    def test_html_render_error_on_missing_template(self, tmp_path):
        """Test RenderError raised when HTML template missing."""
        renderer = ReportRenderer(template_dir=tmp_path)
        report_data = DailyReportData(
            period_start=datetime.now(UTC) - timedelta(hours=24),
            period_end=datetime.now(UTC),
        )

        with pytest.raises(RenderError) as exc_info:
            renderer.render_daily_report_html(report_data)

        assert "daily_report.html.j2" in str(exc_info.value)

    def test_text_render_error_on_missing_template(self, tmp_path):
        """Test RenderError raised when text template missing."""
        renderer = ReportRenderer(template_dir=tmp_path)
        report_data = DailyReportData(
            period_start=datetime.now(UTC) - timedelta(hours=24),
            period_end=datetime.now(UTC),
        )

        with pytest.raises(RenderError) as exc_info:
            renderer.render_daily_report_text(report_data)

        assert "daily_report.txt.j2" in str(exc_info.value)
