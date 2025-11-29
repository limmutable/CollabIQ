"""
Report archiver for Admin Reporting.

Archives daily reports to filesystem with retention policy.
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from admin_reporting.config import ReportingConfig
from admin_reporting.models import DailyReportData, ArchivedReport
from admin_reporting.renderer import ReportRenderer

logger = logging.getLogger(__name__)


class ReportArchiver:
    """
    Archives reports to filesystem with retention management.

    Features:
    - Saves reports as JSON and HTML files
    - Date-based file naming
    - Retention policy with automatic cleanup
    - Archive listing and retrieval

    Attributes:
        config: ReportingConfig with archive settings
        archive_dir: Directory for storing archives
        renderer: ReportRenderer for HTML generation
    """

    def __init__(self, config: Optional[ReportingConfig] = None):
        """
        Initialize ReportArchiver.

        Args:
            config: ReportingConfig instance. If None, loads from environment.
        """
        if config is not None:
            self.config = config
        else:
            self.config = ReportingConfig.from_env()

        self.archive_dir = self.config.archive_directory
        self.retention_days = self.config.retention_days
        self.renderer = ReportRenderer()

        # Ensure archive directory exists
        self._ensure_archive_dir()

    def _ensure_archive_dir(self) -> None:
        """Create archive directory if it doesn't exist."""
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Archive directory ready: {self.archive_dir}")

    def archive_report(
        self,
        report: DailyReportData,
        html_content: Optional[str] = None,
    ) -> ArchivedReport:
        """
        Archive a daily report to filesystem.

        Args:
            report: DailyReportData to archive
            html_content: Pre-rendered HTML content (optional)

        Returns:
            ArchivedReport with file paths and metadata
        """
        date_str = report.report_date.isoformat()

        # Define file paths
        json_path = self.archive_dir / f"report-{date_str}.json"
        html_path = self.archive_dir / f"report-{date_str}.html"

        # Save JSON
        json_data = report.model_dump(mode="json")
        json_content = json.dumps(json_data, indent=2, default=str)
        json_path.write_text(json_content)
        logger.info(f"Archived report JSON to {json_path}")

        # Generate or use provided HTML
        if html_content is None:
            html_content = self.renderer.render_daily_report_html(report)

        html_path.write_text(html_content)
        logger.info(f"Archived report HTML to {html_path}")

        # Calculate total size
        total_size = json_path.stat().st_size + html_path.stat().st_size

        return ArchivedReport(
            report_date=report.report_date,
            json_path=str(json_path),
            html_path=str(html_path),
            archived_at=datetime.now(),
            size_bytes=total_size,
        )

    def cleanup_old_reports(self) -> int:
        """
        Remove reports older than retention period.

        Returns:
            Number of files removed
        """
        cutoff_date = date.today() - timedelta(days=self.retention_days)
        removed_count = 0

        logger.info(f"Cleaning up archives older than {cutoff_date}")

        for file_path in self.archive_dir.glob("report-*.json"):
            try:
                # Extract date from filename
                date_str = file_path.stem.replace("report-", "").split("-")
                if len(date_str) >= 3:
                    # Handle format: report-YYYY-MM-DD.json or report-YYYY-MM-DD-N.json
                    file_date = date(
                        int(date_str[0]), int(date_str[1]), int(date_str[2])
                    )

                    if file_date < cutoff_date:
                        file_path.unlink()
                        removed_count += 1
                        logger.debug(f"Removed old archive: {file_path}")

                        # Also remove corresponding HTML
                        html_path = file_path.with_suffix(".html")
                        if html_path.exists():
                            html_path.unlink()
                            removed_count += 1

            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse date from {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Removed {removed_count} old archive files")

        return removed_count

    def list_archives(self) -> list[dict]:
        """
        List all archived reports.

        Returns:
            List of archive metadata dicts, sorted by date (newest first)
        """
        archives = []

        for json_path in self.archive_dir.glob("report-*.json"):
            try:
                # Extract date from filename
                date_str = json_path.stem.replace("report-", "")
                # Handle format with potential suffix
                date_parts = date_str.split("-")[:3]
                if len(date_parts) >= 3:
                    file_date = date(
                        int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                    )

                    html_path = json_path.with_suffix(".html")

                    archives.append(
                        {
                            "date": file_date,
                            "json_path": str(json_path),
                            "html_path": str(html_path) if html_path.exists() else None,
                            "size_bytes": json_path.stat().st_size,
                        }
                    )

            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse archive {json_path}: {e}")

        # Sort by date, newest first
        archives.sort(key=lambda x: x["date"], reverse=True)

        return archives

    def get_archive(self, report_date: date) -> Optional[dict]:
        """
        Get archive metadata for a specific date.

        Args:
            report_date: Date of the report to retrieve

        Returns:
            Archive metadata dict or None if not found
        """
        date_str = report_date.isoformat()
        json_path = self.archive_dir / f"report-{date_str}.json"

        if not json_path.exists():
            return None

        html_path = json_path.with_suffix(".html")

        return {
            "date": report_date,
            "json_path": str(json_path),
            "html_path": str(html_path) if html_path.exists() else None,
            "size_bytes": json_path.stat().st_size,
        }

    def get_archive_data(self, report_date: date) -> Optional[dict]:
        """
        Load archived report data for a specific date.

        Args:
            report_date: Date of the report to load

        Returns:
            Report data as dict or None if not found
        """
        archive = self.get_archive(report_date)
        if archive is None:
            return None

        try:
            with open(archive["json_path"]) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load archive for {report_date}: {e}")
            return None
