"""
Report renderer for Admin Reporting.

Renders report data to HTML and plain text using Jinja2 templates.
"""

import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from admin_reporting.models import (
    DailyReportData,
    ActionableAlert,
    HealthStatus,
    AlertSeverity,
)

logger = logging.getLogger(__name__)


class RenderError(Exception):
    """Error during template rendering."""

    pass


class ReportRenderer:
    """
    Renders admin reports using Jinja2 templates.

    Supports rendering to both HTML and plain text formats for
    email multipart messages.

    Attributes:
        template_dir: Directory containing Jinja2 templates
        env: Jinja2 environment instance
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize ReportRenderer.

        Args:
            template_dir: Path to templates directory. Defaults to
                         src/admin_reporting/templates/
        """
        if template_dir is None:
            # Default to templates directory relative to this file
            self.template_dir = Path(__file__).parent / "templates"
        else:
            self.template_dir = Path(template_dir)

        # Ensure template directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,  # Security: escape HTML by default
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

        logger.debug(
            f"ReportRenderer initialized with templates from {self.template_dir}"
        )

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["format_datetime"] = self._format_datetime
        self.env.filters["format_date"] = self._format_date
        self.env.filters["format_percentage"] = self._format_percentage
        self.env.filters["format_currency"] = self._format_currency
        self.env.filters["status_emoji"] = self._status_emoji
        self.env.filters["status_color"] = self._status_color
        self.env.filters["severity_emoji"] = self._severity_emoji
        self.env.filters["severity_color"] = self._severity_color
        self.env.filters["ljust"] = self._ljust
        self.env.filters["rjust"] = self._rjust

    @staticmethod
    def _format_datetime(value: Optional[datetime]) -> str:
        """Format datetime for display."""
        if value is None:
            return "N/A"
        return value.strftime("%Y-%m-%d %H:%M:%S %Z")

    @staticmethod
    def _format_date(value: Optional[date]) -> str:
        """Format date for display."""
        if value is None:
            return "N/A"
        return value.strftime("%Y-%m-%d")

    @staticmethod
    def _format_percentage(value: float) -> str:
        """Format float as percentage."""
        return f"{value * 100:.1f}%"

    @staticmethod
    def _format_currency(value: float) -> str:
        """Format float as USD currency."""
        return f"${value:.4f}"

    @staticmethod
    def _status_emoji(status: HealthStatus) -> str:
        """Get emoji for health status."""
        emoji_map = {
            HealthStatus.OPERATIONAL: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNAVAILABLE: "❌",
        }
        return emoji_map.get(status, "❓")

    @staticmethod
    def _status_color(status: HealthStatus) -> str:
        """Get CSS color for health status."""
        color_map = {
            HealthStatus.OPERATIONAL: "#28a745",  # Green
            HealthStatus.DEGRADED: "#ffc107",  # Yellow/Amber
            HealthStatus.UNAVAILABLE: "#dc3545",  # Red
        }
        return color_map.get(status, "#6c757d")  # Gray default

    @staticmethod
    def _severity_emoji(severity: AlertSeverity) -> str:
        """Get emoji for alert severity."""
        emoji_map = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.INFO: "ℹ️",
        }
        return emoji_map.get(severity, "❓")

    @staticmethod
    def _severity_color(severity: AlertSeverity) -> str:
        """Get CSS color for alert severity."""
        color_map = {
            AlertSeverity.CRITICAL: "#dc3545",  # Red
            AlertSeverity.WARNING: "#ffc107",  # Yellow/Amber
            AlertSeverity.INFO: "#17a2b8",  # Blue
        }
        return color_map.get(severity, "#6c757d")  # Gray default

    @staticmethod
    def _ljust(value: str, width: int) -> str:
        """Left-justify string to given width."""
        return str(value).ljust(width)

    @staticmethod
    def _rjust(value: str, width: int) -> str:
        """Right-justify string to given width."""
        return str(value).rjust(width)

    def render_daily_report_html(self, report_data: DailyReportData) -> str:
        """
        Render daily report to HTML.

        Args:
            report_data: DailyReportData containing all metrics

        Returns:
            Rendered HTML string

        Raises:
            RenderError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template("daily_report.html.j2")
            return template.render(report=report_data)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise RenderError("Template not found: daily_report.html.j2") from e
        except Exception as e:
            logger.error(f"Failed to render HTML report: {e}")
            raise RenderError(f"Failed to render HTML report: {e}") from e

    def render_daily_report_text(self, report_data: DailyReportData) -> str:
        """
        Render daily report to plain text.

        Args:
            report_data: DailyReportData containing all metrics

        Returns:
            Rendered plain text string

        Raises:
            RenderError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template("daily_report.txt.j2")
            return template.render(report=report_data)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise RenderError("Template not found: daily_report.txt.j2") from e
        except Exception as e:
            logger.error(f"Failed to render text report: {e}")
            raise RenderError(f"Failed to render text report: {e}") from e

    def render_alert_html(self, alerts: list[ActionableAlert]) -> str:
        """
        Render critical alerts to HTML.

        Args:
            alerts: List of ActionableAlert objects

        Returns:
            Rendered HTML string

        Raises:
            RenderError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template("critical_alert.html.j2")
            return template.render(alerts=alerts)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise RenderError("Template not found: critical_alert.html.j2") from e
        except Exception as e:
            logger.error(f"Failed to render HTML alert: {e}")
            raise RenderError(f"Failed to render HTML alert: {e}") from e

    def render_alert_text(self, alerts: list[ActionableAlert]) -> str:
        """
        Render critical alerts to plain text.

        Args:
            alerts: List of ActionableAlert objects

        Returns:
            Rendered plain text string

        Raises:
            RenderError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template("critical_alert.txt.j2")
            return template.render(alerts=alerts)
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise RenderError("Template not found: critical_alert.txt.j2") from e
        except Exception as e:
            logger.error(f"Failed to render text alert: {e}")
            raise RenderError(f"Failed to render text alert: {e}") from e

    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.

        Args:
            template_name: Name of template file

        Returns:
            True if template exists, False otherwise
        """
        template_path = self.template_dir / template_name
        return template_path.exists()
