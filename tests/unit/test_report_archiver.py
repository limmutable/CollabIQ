"""
Unit tests for ReportArchiver.

Tests report archiving functionality including:
- Archive creation (JSON + HTML)
- File naming conventions
- Retention policy (cleanup old reports)
- Archive listing
"""

import pytest
import json
from datetime import datetime, date, timedelta, UTC
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from admin_reporting.archiver import ReportArchiver
from admin_reporting.models import (
    DailyReportData,
    ComponentHealthSummary,
    ProcessingMetrics,
    ErrorSummary,
    LLMUsageSummary,
    NotionStats,
    HealthStatus,
)
from admin_reporting.config import ReportingConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_archive_dir():
    """Create a temporary directory for archives."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def archive_config(temp_archive_dir):
    """Create test archive configuration."""
    return ReportingConfig(
        enabled=True,
        recipients=["admin@example.com"],
        archive_directory=temp_archive_dir,
        retention_days=7,
    )


@pytest.fixture
def archiver(archive_config):
    """Create ReportArchiver instance."""
    return ReportArchiver(config=archive_config)


@pytest.fixture
def sample_report():
    """Create a sample report for testing."""
    now = datetime.now(UTC)
    return DailyReportData(
        report_id="test-report-123",
        report_date=date.today(),
        generated_at=now,
        period_start=now - timedelta(hours=24),
        period_end=now,
        health_status=ComponentHealthSummary(
            gmail_status=HealthStatus.OPERATIONAL,
            notion_status=HealthStatus.OPERATIONAL,
            overall_status=HealthStatus.OPERATIONAL,
        ),
        processing_metrics=ProcessingMetrics(
            emails_received=50,
            emails_processed=48,
            emails_skipped=2,
            success_rate=0.96,
        ),
        error_summary=ErrorSummary(
            total_error_count=3,
            error_rate=0.06,
        ),
        llm_usage=LLMUsageSummary(
            total_calls=150,
            total_cost=2.50,
            calls_by_provider={"gemini": 100, "claude": 50},
            costs_by_provider={"gemini": 1.00, "claude": 1.50},
        ),
        notion_stats=NotionStats(
            entries_created=48,
        ),
    )


# ============================================================================
# ReportArchiver Initialization Tests
# ============================================================================


class TestReportArchiverInit:
    """Test ReportArchiver initialization."""

    def test_init_with_config(self, archive_config):
        """Test initialization with explicit config."""
        archiver = ReportArchiver(config=archive_config)

        assert archiver.config == archive_config
        assert archiver.archive_dir == archive_config.archive_directory

    def test_init_creates_archive_dir(self, temp_archive_dir):
        """Test initialization creates archive directory if missing."""
        new_dir = temp_archive_dir / "new_archives"
        config = ReportingConfig(
            enabled=True,
            recipients=["admin@example.com"],
            archive_directory=new_dir,
        )

        archiver = ReportArchiver(config=config)

        assert new_dir.exists()

    def test_init_loads_config_from_env(self):
        """Test initialization loads config from environment."""
        with patch("admin_reporting.archiver.ReportingConfig.from_env") as mock_from_env:
            mock_from_env.return_value = ReportingConfig(
                enabled=True,
                recipients=["admin@example.com"],
                archive_directory=Path("/tmp/test"),
            )
            archiver = ReportArchiver()

        mock_from_env.assert_called_once()


# ============================================================================
# Archive Creation Tests
# ============================================================================


class TestArchiveReport:
    """Test report archiving functionality."""

    def test_archive_creates_json_file(self, archiver, sample_report):
        """Test archiving creates JSON file."""
        result = archiver.archive_report(sample_report)

        json_path = Path(result.json_path)
        assert json_path.exists()
        assert json_path.suffix == ".json"

    def test_archive_creates_html_file(self, archiver, sample_report):
        """Test archiving creates HTML file."""
        result = archiver.archive_report(sample_report)

        html_path = Path(result.html_path)
        assert html_path.exists()
        assert html_path.suffix == ".html"

    def test_archive_json_is_valid(self, archiver, sample_report):
        """Test archived JSON is valid and contains report data."""
        result = archiver.archive_report(sample_report)

        json_path = Path(result.json_path)
        with open(json_path) as f:
            data = json.load(f)

        assert data["report_id"] == sample_report.report_id
        assert data["report_date"] == sample_report.report_date.isoformat()

    def test_archive_html_contains_content(self, archiver, sample_report):
        """Test archived HTML contains report content."""
        result = archiver.archive_report(sample_report)

        html_path = Path(result.html_path)
        content = html_path.read_text()

        assert "CollabIQ" in content
        assert "Daily Report" in content or "report" in content.lower()

    def test_archive_file_naming_convention(self, archiver, sample_report):
        """Test archive files follow naming convention."""
        result = archiver.archive_report(sample_report)

        json_path = Path(result.json_path)
        html_path = Path(result.html_path)

        # Should include date in filename
        date_str = sample_report.report_date.isoformat()
        assert date_str in json_path.name
        assert date_str in html_path.name

    def test_archive_returns_metadata(self, archiver, sample_report):
        """Test archive returns metadata about stored files."""
        result = archiver.archive_report(sample_report)

        assert result.report_date == sample_report.report_date
        assert result.json_path is not None
        assert result.html_path is not None
        assert result.size_bytes > 0

    def test_archive_with_html_override(self, archiver, sample_report):
        """Test archiving with pre-rendered HTML."""
        custom_html = "<html><body>Custom Report</body></html>"

        result = archiver.archive_report(sample_report, html_content=custom_html)

        html_path = Path(result.html_path)
        assert html_path.read_text() == custom_html


# ============================================================================
# Retention Policy Tests
# ============================================================================


class TestCleanupOldReports:
    """Test retention policy cleanup."""

    def test_cleanup_removes_old_files(self, archiver, sample_report, temp_archive_dir):
        """Test cleanup removes files older than retention period."""
        # Archive current report
        archiver.archive_report(sample_report)

        # Create old files manually
        old_date = date.today() - timedelta(days=10)
        old_json = temp_archive_dir / f"report-{old_date.isoformat()}.json"
        old_html = temp_archive_dir / f"report-{old_date.isoformat()}.html"
        old_json.write_text("{}")
        old_html.write_text("<html></html>")

        # Verify old files exist
        assert old_json.exists()
        assert old_html.exists()

        # Run cleanup
        removed = archiver.cleanup_old_reports()

        # Old files should be removed
        assert not old_json.exists()
        assert not old_html.exists()
        assert removed >= 2

    def test_cleanup_preserves_recent_files(self, archiver, sample_report, temp_archive_dir):
        """Test cleanup preserves files within retention period."""
        # Archive current report
        result = archiver.archive_report(sample_report)

        # Run cleanup
        archiver.cleanup_old_reports()

        # Current report should still exist
        assert Path(result.json_path).exists()
        assert Path(result.html_path).exists()

    def test_cleanup_with_custom_retention(self, temp_archive_dir):
        """Test cleanup with custom retention period."""
        config = ReportingConfig(
            enabled=True,
            recipients=["admin@example.com"],
            archive_directory=temp_archive_dir,
            retention_days=3,  # Shorter retention
        )
        archiver = ReportArchiver(config=config)

        # Create file from 5 days ago
        old_date = date.today() - timedelta(days=5)
        old_file = temp_archive_dir / f"report-{old_date.isoformat()}.json"
        old_file.write_text("{}")

        # Run cleanup
        archiver.cleanup_old_reports()

        # Should be removed (older than 3 days)
        assert not old_file.exists()

    def test_cleanup_returns_count(self, archiver, temp_archive_dir):
        """Test cleanup returns number of files removed."""
        # Create multiple old files
        old_date = date.today() - timedelta(days=10)
        for i in range(3):
            old_file = temp_archive_dir / f"report-{old_date.isoformat()}-{i}.json"
            old_file.write_text("{}")

        removed = archiver.cleanup_old_reports()

        assert removed == 3


# ============================================================================
# Archive Listing Tests
# ============================================================================


class TestListArchives:
    """Test archive listing functionality."""

    def test_list_returns_all_archives(self, archiver, sample_report):
        """Test listing returns all archived reports."""
        # Archive multiple reports
        archiver.archive_report(sample_report)

        archives = archiver.list_archives()

        assert len(archives) >= 1

    def test_list_returns_sorted_by_date(self, archiver, temp_archive_dir):
        """Test listing returns archives sorted by date (newest first)."""
        # Create archives for multiple dates
        dates = [date.today() - timedelta(days=i) for i in range(3)]
        for d in dates:
            archiver.archive_dir.joinpath(f"report-{d.isoformat()}.json").write_text("{}")
            archiver.archive_dir.joinpath(f"report-{d.isoformat()}.html").write_text("<html></html>")

        archives = archiver.list_archives()

        # Should be sorted with newest first
        assert len(archives) == 3
        assert archives[0]["date"] >= archives[1]["date"]
        assert archives[1]["date"] >= archives[2]["date"]

    def test_list_empty_directory(self, archiver):
        """Test listing empty archive directory."""
        archives = archiver.list_archives()

        assert archives == []

    def test_list_includes_metadata(self, archiver, sample_report):
        """Test listing includes metadata about each archive."""
        archiver.archive_report(sample_report)

        archives = archiver.list_archives()

        assert len(archives) >= 1
        archive = archives[0]
        assert "date" in archive
        assert "json_path" in archive
        assert "html_path" in archive


# ============================================================================
# Get Archive Tests
# ============================================================================


class TestGetArchive:
    """Test retrieving specific archives."""

    def test_get_archive_by_date(self, archiver, sample_report):
        """Test retrieving archive by date."""
        archiver.archive_report(sample_report)

        archive = archiver.get_archive(sample_report.report_date)

        assert archive is not None
        assert "json_path" in archive
        assert Path(archive["json_path"]).exists()

    def test_get_nonexistent_archive(self, archiver):
        """Test retrieving nonexistent archive returns None."""
        old_date = date.today() - timedelta(days=100)

        archive = archiver.get_archive(old_date)

        assert archive is None

    def test_get_archive_loads_data(self, archiver, sample_report):
        """Test get_archive can load report data."""
        archiver.archive_report(sample_report)

        data = archiver.get_archive_data(sample_report.report_date)

        assert data is not None
        assert data["report_id"] == sample_report.report_id
