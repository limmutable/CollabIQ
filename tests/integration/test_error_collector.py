"""
Integration tests for ErrorCollector

Tests validate:
- collect_error method (auto-severity categorization, exception handling)
- persist_error method (file writing to correct directories)
- get_error_summary method (aggregation across severity levels)
- update_error_status method (updating existing errors)
"""

import json
from pathlib import Path

import pytest

from e2e_test.error_collector import ErrorCollector
from e2e_test.models import PipelineStage, Severity


class TestCollectError:
    """Test collect_error method"""

    def test_collect_error_with_exception(self, tmp_path):
        """Test creating error from exception with stack trace"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        # Create a test exception
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            error = collector.collect_error(
                run_id="2025-11-04T14:30:00",
                email_id="msg_001",
                stage=PipelineStage.EXTRACTION,
                exception=e,
                input_data={"test": "data"},
            )

        assert error.error_id.startswith("2025-11-04T14:30:00_msg_001")
        assert error.error_type == "ValueError"
        assert "Test error message" in error.error_message
        assert error.stack_trace is not None
        assert "raise ValueError" in error.stack_trace

    def test_collect_error_with_manual_message(self, tmp_path):
        """Test creating error with manual error message"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_002",
            stage=PipelineStage.MATCHING,
            error_type="CustomError",
            error_message="Manual error description",
        )

        assert error.error_type == "CustomError"
        assert error.error_message == "Manual error description"
        assert error.stack_trace is None  # No exception, no stack trace

    def test_collect_error_without_exception_or_message_raises_error(self, tmp_path):
        """Test that collect_error raises ValueError if neither exception nor message provided"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        with pytest.raises(
            ValueError, match="Either exception or error_message must be provided"
        ):
            collector.collect_error(
                run_id="2025-11-04T14:30:00",
                email_id="msg_003",
                stage=PipelineStage.WRITE,
            )

    def test_auto_categorization_critical_auth_error(self, tmp_path):
        """Test that authentication errors are auto-categorized as critical"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_004",
            stage=PipelineStage.RECEPTION,
            error_type="AuthenticationError",
            error_message="API authentication failed",
        )

        assert error.severity == Severity.CRITICAL

    def test_auto_categorization_high_encoding_error(self, tmp_path):
        """Test that encoding errors are auto-categorized as high"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_005",
            stage=PipelineStage.EXTRACTION,
            error_type="EncodingError",
            error_message="Korean text corrupted",
        )

        assert error.severity == Severity.HIGH

    def test_manual_severity_override(self, tmp_path):
        """Test that manual severity takes precedence over auto-categorization"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        # Force medium severity even though it's an encoding error
        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_006",
            stage=PipelineStage.EXTRACTION,
            error_type="EncodingError",
            error_message="Minor encoding issue",
            severity=Severity.MEDIUM,  # Override auto-categorization
        )

        assert error.severity == Severity.MEDIUM

    def test_error_id_increments_for_same_email(self, tmp_path):
        """Test that error_id increments when multiple errors occur for same email"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error1 = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_007",
            stage=PipelineStage.EXTRACTION,
            error_message="First error",
        )

        error2 = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_007",
            stage=PipelineStage.MATCHING,
            error_message="Second error",
        )

        assert error1.error_id == "2025-11-04T14:30:00_msg_007_001"
        assert error2.error_id == "2025-11-04T14:30:00_msg_007_002"


class TestPersistError:
    """Test persist_error method"""

    def test_persist_error_creates_file_in_correct_directory(self, tmp_path):
        """Test that error is persisted to correct severity subdirectory"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_008",
            stage=PipelineStage.WRITE,
            error_message="Test error",
            severity=Severity.HIGH,
        )

        file_path = collector.persist_error(error)

        assert Path(file_path).exists()
        assert "errors/high" in file_path
        assert error.error_id in file_path

    def test_persisted_error_can_be_loaded_back(self, tmp_path):
        """Test that persisted error JSON is valid and can be loaded"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_009",
            stage=PipelineStage.CLASSIFICATION,
            error_message="Test error with Korean text: 한글",
            severity=Severity.MEDIUM,
        )

        file_path = collector.persist_error(error)

        # Load JSON and validate
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data["error_id"] == error.error_id
        assert "한글" in loaded_data["error_message"]  # Korean text preserved

    def test_persist_creates_severity_directory_if_not_exists(self, tmp_path):
        """Test that persist_error creates severity directory if needed"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        # Remove low severity directory if exists
        low_dir = tmp_path / "errors" / "low"
        if low_dir.exists():
            low_dir.rmdir()

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_010",
            stage=PipelineStage.VALIDATION,
            error_message="Test error",
            severity=Severity.LOW,
        )

        file_path = collector.persist_error(error)

        assert Path(file_path).exists()
        assert low_dir.exists()


class TestGetErrorSummary:
    """Test get_error_summary method"""

    def test_get_error_summary_empty_run(self, tmp_path):
        """Test error summary for run with no errors"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        summary = collector.get_error_summary("2025-11-04T14:30:00")

        assert summary == {"critical": 0, "high": 0, "medium": 0, "low": 0}

    def test_get_error_summary_with_multiple_errors(self, tmp_path):
        """Test error summary aggregates across severity levels"""
        collector = ErrorCollector(output_dir=str(tmp_path))
        run_id = "2025-11-04T14:30:00"

        # Create 2 high, 3 medium, 1 low errors
        for i in range(2):
            error = collector.collect_error(
                run_id=run_id,
                email_id=f"msg_{i}",
                stage=PipelineStage.EXTRACTION,
                error_message=f"High error {i}",
                severity=Severity.HIGH,
            )
            collector.persist_error(error)

        for i in range(3):
            error = collector.collect_error(
                run_id=run_id,
                email_id=f"msg_{i + 10}",
                stage=PipelineStage.MATCHING,
                error_message=f"Medium error {i}",
                severity=Severity.MEDIUM,
            )
            collector.persist_error(error)

        error = collector.collect_error(
            run_id=run_id,
            email_id="msg_100",
            stage=PipelineStage.VALIDATION,
            error_message="Low error",
            severity=Severity.LOW,
        )
        collector.persist_error(error)

        summary = collector.get_error_summary(run_id)

        assert summary == {"critical": 0, "high": 2, "medium": 3, "low": 1}

    def test_get_error_summary_filters_by_run_id(self, tmp_path):
        """Test that get_error_summary only counts errors for specified run_id"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        # Create errors for two different runs
        error1 = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_001",
            stage=PipelineStage.EXTRACTION,
            error_message="Run 1 error",
            severity=Severity.HIGH,
        )
        collector.persist_error(error1)

        error2 = collector.collect_error(
            run_id="2025-11-04T16:00:00",
            email_id="msg_002",
            stage=PipelineStage.EXTRACTION,
            error_message="Run 2 error",
            severity=Severity.HIGH,
        )
        collector.persist_error(error2)

        # Get summary for first run only
        summary = collector.get_error_summary("2025-11-04T14:30:00")

        assert summary == {"critical": 0, "high": 1, "medium": 0, "low": 0}


class TestUpdateErrorStatus:
    """Test update_error_status method"""

    def test_update_error_status_to_fixed(self, tmp_path):
        """Test updating error status to fixed with commit hash"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        # Create and persist initial error
        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_011",
            stage=PipelineStage.EXTRACTION,
            error_message="Test error",
            severity=Severity.HIGH,
        )
        collector.persist_error(error)

        # Update status
        updated_error = collector.update_error_status(
            error_id=error.error_id,
            resolution_status="fixed",
            fix_commit="abc123def456",
            notes="Fixed by adding UTF-8 encoding",
        )

        assert updated_error.resolution_status == "fixed"
        assert updated_error.fix_commit == "abc123def456"
        assert "UTF-8 encoding" in updated_error.notes

    def test_update_error_status_preserves_original_data(self, tmp_path):
        """Test that updating status doesn't modify original error data"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        error = collector.collect_error(
            run_id="2025-11-04T14:30:00",
            email_id="msg_012",
            stage=PipelineStage.MATCHING,
            error_message="Original error message",
            severity=Severity.MEDIUM,
        )
        collector.persist_error(error)

        updated_error = collector.update_error_status(
            error_id=error.error_id,
            resolution_status="deferred",
        )

        # Original data preserved
        assert updated_error.error_message == "Original error message"
        assert updated_error.severity == Severity.MEDIUM
        assert updated_error.stage == PipelineStage.MATCHING

    def test_update_error_status_nonexistent_error_raises(self, tmp_path):
        """Test that updating nonexistent error raises FileNotFoundError"""
        collector = ErrorCollector(output_dir=str(tmp_path))

        with pytest.raises(FileNotFoundError):
            collector.update_error_status(
                error_id="nonexistent_error_id",
                resolution_status="fixed",
            )
