"""
Integration tests for E2E test harness Pydantic models

Tests validate:
- Schema constraints (field types, required fields, validation rules)
- Enum value validation
- Field constraints (min/max values, string lengths)
- Optional field handling
- Config.use_enum_values behavior
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.e2e_test.models import (
    ErrorRecord,
    PerformanceMetric,
    PipelineStage,
    ResolutionStatus,
    RunStatus,
    SelectionReason,
    Severity,
    TestEmailMetadata,
    TestRun,
)


class TestTestRunModel:
    """Test TestRun Pydantic model validation"""

    def test_valid_test_run(self):
        """Test creating a valid TestRun"""
        run = TestRun(
            run_id="2025-11-04T14:30:00",
            start_time=datetime.fromisoformat("2025-11-04T14:30:00"),
            end_time=datetime.fromisoformat("2025-11-04T14:45:23"),
            status=RunStatus.COMPLETED,
            email_count=10,
            emails_processed=10,
            success_count=9,
            failure_count=1,
            stage_success_rates={
                "reception": 1.0,
                "extraction": 0.9,
                "matching": 0.9,
                "classification": 0.9,
                "write": 0.9,
            },
            total_duration_seconds=923.45,
            average_time_per_email=92.345,
            error_summary={"critical": 0, "high": 1, "medium": 2, "low": 1},
            test_email_ids=["msg_001", "msg_002", "msg_003"],
            config={"test_mode": True, "database_id": "test_db"},
        )

        assert run.run_id == "2025-11-04T14:30:00"
        assert run.status == RunStatus.COMPLETED
        assert run.email_count == 10
        assert run.success_count == 9

    def test_email_count_must_be_positive(self):
        """Test that email_count must be greater than 0"""
        with pytest.raises(ValidationError, match="greater than 0"):
            TestRun(
                run_id="2025-11-04T14:30:00",
                start_time=datetime.now(),
                status=RunStatus.RUNNING,
                email_count=0,  # Invalid: must be > 0
                emails_processed=0,
                success_count=0,
                failure_count=0,
                stage_success_rates={},
                error_summary={},
                test_email_ids=["msg_001"],
                config={},
            )

    def test_optional_fields_can_be_none(self):
        """Test that end_time, total_duration, avg_time can be None"""
        run = TestRun(
            run_id="2025-11-04T14:30:00",
            start_time=datetime.now(),
            end_time=None,  # Optional
            status=RunStatus.RUNNING,
            email_count=10,
            emails_processed=5,
            success_count=4,
            failure_count=1,
            stage_success_rates={"extraction": 0.8},
            total_duration_seconds=None,  # Optional
            average_time_per_email=None,  # Optional
            error_summary={"critical": 0},
            test_email_ids=["msg_001"],
            config={},
        )

        assert run.end_time is None
        assert run.total_duration_seconds is None
        assert run.average_time_per_email is None

    def test_test_email_ids_cannot_be_empty(self):
        """Test that test_email_ids list must have at least one element"""
        with pytest.raises(ValidationError, match="at least 1 item"):
            TestRun(
                run_id="2025-11-04T14:30:00",
                start_time=datetime.now(),
                status=RunStatus.RUNNING,
                email_count=10,
                emails_processed=0,
                success_count=0,
                failure_count=0,
                stage_success_rates={},
                error_summary={},
                test_email_ids=[],  # Invalid: must have at least 1 item
                config={},
            )


class TestErrorRecordModel:
    """Test ErrorRecord Pydantic model validation"""

    def test_valid_error_record(self):
        """Test creating a valid ErrorRecord"""
        error = ErrorRecord(
            error_id="2025-11-04T14:30:00_msg_042_001",
            run_id="2025-11-04T14:30:00",
            email_id="msg_042",
            severity=Severity.HIGH,
            stage=PipelineStage.EXTRACTION,
            error_type="EncodingError",
            error_message="Korean text corrupted",
            stack_trace="Traceback...",
            input_data_snapshot={"original": "한글", "corrupted": "mojibake"},
            timestamp=datetime.now(),
            resolution_status=ResolutionStatus.OPEN,
            fix_commit=None,
            notes="Need to check UTF-8 encoding",
        )

        assert error.error_id == "2025-11-04T14:30:00_msg_042_001"
        assert error.severity == Severity.HIGH
        assert error.stage == PipelineStage.EXTRACTION

    def test_severity_enum_validation(self):
        """Test that severity must be a valid Severity enum value"""
        with pytest.raises(ValidationError, match="Input should be"):
            ErrorRecord(
                error_id="test_001",
                run_id="2025-11-04T14:30:00",
                email_id="msg_001",
                severity="invalid_severity",  # Invalid enum value
                stage=PipelineStage.EXTRACTION,
                error_type="TestError",
                error_message="Test",
                timestamp=datetime.now(),
            )

    def test_default_resolution_status_is_open(self):
        """Test that resolution_status defaults to OPEN"""
        error = ErrorRecord(
            error_id="test_001",
            run_id="2025-11-04T14:30:00",
            email_id="msg_001",
            severity=Severity.LOW,
            stage=PipelineStage.VALIDATION,
            error_type="TestError",
            error_message="Test error",
            timestamp=datetime.now(),
        )

        assert error.resolution_status == ResolutionStatus.OPEN

    def test_error_message_cannot_be_empty(self):
        """Test that error_message must be non-empty string"""
        with pytest.raises(ValidationError, match="at least 1 character"):
            ErrorRecord(
                error_id="test_001",
                run_id="2025-11-04T14:30:00",
                email_id="msg_001",
                severity=Severity.LOW,
                stage=PipelineStage.VALIDATION,
                error_type="TestError",
                error_message="",  # Invalid: empty string
                timestamp=datetime.now(),
            )


class TestPerformanceMetricModel:
    """Test PerformanceMetric Pydantic model validation"""

    def test_valid_performance_metric(self):
        """Test creating a valid PerformanceMetric"""
        metric = PerformanceMetric(
            metric_id="2025-11-04T14:30:00_msg_010_extraction",
            run_id="2025-11-04T14:30:00",
            email_id="msg_010",
            stage=PipelineStage.EXTRACTION,
            start_time=datetime.fromisoformat("2025-11-04T14:32:15"),
            end_time=datetime.fromisoformat("2025-11-04T14:32:18"),
            duration_seconds=3.42,
            api_calls={"gemini": 1, "notion": 0, "gmail": 0},
            gemini_tokens={"input_tokens": 1250, "output_tokens": 180},
            memory_mb=None,
            status="success",
            notes="Normal execution",
        )

        assert metric.metric_id == "2025-11-04T14:30:00_msg_010_extraction"
        assert metric.stage == PipelineStage.EXTRACTION
        assert metric.duration_seconds == 3.42

    def test_duration_must_be_positive(self):
        """Test that duration_seconds must be greater than 0"""
        with pytest.raises(ValidationError, match="greater than 0"):
            PerformanceMetric(
                metric_id="test_001",
                run_id="2025-11-04T14:30:00",
                email_id="msg_001",
                stage=PipelineStage.RECEPTION,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=0.0,  # Invalid: must be > 0
                status="success",
            )

    def test_optional_tracking_fields(self):
        """Test that api_calls, tokens, memory can be None"""
        metric = PerformanceMetric(
            metric_id="test_001",
            run_id="2025-11-04T14:30:00",
            email_id="msg_001",
            stage=PipelineStage.RECEPTION,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=1.5,
            api_calls=None,  # Optional
            gemini_tokens=None,  # Optional
            memory_mb=None,  # Optional
            status="success",
        )

        assert metric.api_calls is None
        assert metric.gemini_tokens is None
        assert metric.memory_mb is None


class TestTestEmailMetadataModel:
    """Test TestEmailMetadata Pydantic model validation"""

    def test_valid_test_email_metadata(self):
        """Test creating valid TestEmailMetadata"""
        metadata = TestEmailMetadata(
            email_id="msg_001",
            subject="브레이크앤컴퍼니 x 신세계푸드",
            received_date="2025-10-28",
            collaboration_type="[A]",
            has_korean_text=True,
            selection_reason=SelectionReason.STRATIFIED_SAMPLE,
            notes="Typical collaboration email",
        )

        assert metadata.email_id == "msg_001"
        assert metadata.has_korean_text is True
        assert metadata.selection_reason == SelectionReason.STRATIFIED_SAMPLE

    def test_email_id_cannot_be_empty(self):
        """Test that email_id must be non-empty"""
        with pytest.raises(ValidationError, match="at least 1 character"):
            TestEmailMetadata(
                email_id="",  # Invalid: empty string
                subject="Test",
                received_date="2025-11-04",
                has_korean_text=False,
                selection_reason=SelectionReason.MANUAL,
            )

    def test_subject_cannot_be_empty(self):
        """Test that subject must be non-empty"""
        with pytest.raises(ValidationError, match="at least 1 character"):
            TestEmailMetadata(
                email_id="msg_001",
                subject="",  # Invalid: empty string
                received_date="2025-11-04",
                has_korean_text=False,
                selection_reason=SelectionReason.MANUAL,
            )

    def test_optional_collaboration_type(self):
        """Test that collaboration_type can be None"""
        metadata = TestEmailMetadata(
            email_id="msg_042",
            subject="Test email",
            received_date="2025-11-04",
            collaboration_type=None,  # Optional
            has_korean_text=False,
            selection_reason=SelectionReason.EDGE_CASE,
            notes=None,  # Optional
        )

        assert metadata.collaboration_type is None
        assert metadata.notes is None


class TestEnumValuesExport:
    """Test that Config.use_enum_values works correctly"""

    def test_enum_values_exported_as_strings(self):
        """Test that enum fields are serialized as string values"""
        run = TestRun(
            run_id="2025-11-04T14:30:00",
            start_time=datetime.now(),
            status=RunStatus.RUNNING,
            email_count=10,
            emails_processed=0,
            success_count=0,
            failure_count=0,
            stage_success_rates={},
            error_summary={},
            test_email_ids=["msg_001"],
            config={},
        )

        # When exported to dict, enums should be string values
        run_dict = run.model_dump()
        assert run_dict["status"] == "running"  # Not RunStatus.RUNNING object

    def test_severity_exported_as_string(self):
        """Test that Severity enum is exported as string"""
        error = ErrorRecord(
            error_id="test_001",
            run_id="2025-11-04T14:30:00",
            email_id="msg_001",
            severity=Severity.CRITICAL,
            stage=PipelineStage.WRITE,
            error_type="APIError",
            error_message="Notion API failure",
            timestamp=datetime.now(),
        )

        error_dict = error.model_dump()
        assert error_dict["severity"] == "critical"  # String, not enum
        assert error_dict["stage"] == "write"
