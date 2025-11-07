"""
Pydantic data models for E2E test harness

Entities:
- TestRun: Metadata about a test execution
- ErrorRecord: Captured errors with context
- PerformanceMetric: Timing and resource data
- TestEmailMetadata: Email selection metadata
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== Enums ====================


class RunStatus(str, Enum):
    """Test run execution status"""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class Severity(str, Enum):
    """Error severity levels"""

    CRITICAL = "critical"  # Blocks pipeline or causes data loss
    HIGH = "high"  # Incorrect data or frequent failures (>10%)
    MEDIUM = "medium"  # Occasional failures (<10%) or degraded experience
    LOW = "low"  # Minor issues, no correctness impact


class PipelineStage(str, Enum):
    """Pipeline stages for error tracking and performance metrics"""

    RECEPTION = "reception"
    EXTRACTION = "extraction"
    MATCHING = "matching"
    CLASSIFICATION = "classification"
    WRITE = "write"
    VALIDATION = "validation"


class ResolutionStatus(str, Enum):
    """Error resolution tracking status"""

    OPEN = "open"
    FIXED = "fixed"
    DEFERRED = "deferred"
    WONT_FIX = "wont_fix"


class SelectionReason(str, Enum):
    """Why a test email was selected"""

    STRATIFIED_SAMPLE = "stratified_sample"
    EDGE_CASE = "edge_case"
    KNOWN_FAILURE = "known_failure"
    MANUAL = "manual"


# ==================== Main Entities ====================


class TestRun(BaseModel):
    """
    Represents a single execution of the E2E test suite

    Persistence: data/e2e_test/runs/{run_id}.json
    """

    run_id: str = Field(..., description="Unique identifier (ISO 8601 timestamp)")
    start_time: datetime = Field(..., description="When test run started")
    end_time: Optional[datetime] = Field(None, description="When test run completed")
    status: RunStatus = Field(..., description="Current execution status")
    email_count: int = Field(..., gt=0, description="Total emails to process")
    emails_processed: int = Field(..., ge=0, description="Emails processed so far")
    success_count: int = Field(..., ge=0, description="Successfully processed emails")
    failure_count: int = Field(..., ge=0, description="Failed emails")
    stage_success_rates: dict[str, float] = Field(
        ..., description="Success rate by pipeline stage"
    )
    total_duration_seconds: Optional[float] = Field(
        None, ge=0, description="Total elapsed time"
    )
    average_time_per_email: Optional[float] = Field(
        None, ge=0, description="Average processing time"
    )
    error_summary: dict[str, int] = Field(..., description="Error counts by severity")
    test_email_ids: list[str] = Field(
        ..., min_length=1, description="Gmail message IDs being tested"
    )
    config: dict = Field(..., description="Configuration for this run")

    model_config = ConfigDict(use_enum_values=True)


class ErrorRecord(BaseModel):
    """
    Represents a single error discovered during testing

    Persistence: data/e2e_test/errors/{severity}/{run_id}_{email_id}_{error_index}.json
    """

    error_id: str = Field(..., description="Unique error identifier")
    run_id: str = Field(..., description="Parent test run ID")
    email_id: str = Field(..., description="Gmail message ID where error occurred")
    severity: Severity = Field(..., description="Error severity level")
    stage: PipelineStage = Field(..., description="Pipeline stage where error occurred")
    error_type: str = Field(..., description="Type of error (e.g., APIError)")
    error_message: str = Field(..., min_length=1, description="Human-readable error")
    stack_trace: Optional[str] = Field(
        None, description="Full stack trace if available"
    )
    input_data_snapshot: Optional[dict] = Field(
        None, description="Input data that caused error (sanitized)"
    )
    timestamp: datetime = Field(..., description="When error occurred")
    resolution_status: ResolutionStatus = Field(
        default=ResolutionStatus.OPEN, description="Current resolution status"
    )
    fix_commit: Optional[str] = Field(None, description="Git commit hash of fix")
    notes: Optional[str] = Field(None, description="Investigation notes")

    model_config = ConfigDict(use_enum_values=True)


class PerformanceMetric(BaseModel):
    """
    Timing and resource usage for a pipeline stage

    Persistence: data/e2e_test/metrics/{run_id}/{email_id}_{stage}.json
    """

    metric_id: str = Field(..., description="Unique metric identifier")
    run_id: str = Field(..., description="Parent test run ID")
    email_id: str = Field(..., description="Gmail message ID being processed")
    stage: PipelineStage = Field(..., description="Pipeline stage being measured")
    start_time: datetime = Field(..., description="Stage start time")
    end_time: datetime = Field(..., description="Stage end time")
    duration_seconds: float = Field(..., gt=0, description="Elapsed time")
    api_calls: Optional[dict[str, int]] = Field(
        None, description="API call counts by service"
    )
    gemini_tokens: Optional[dict[str, int]] = Field(
        None, description="Gemini token usage"
    )
    memory_mb: Optional[float] = Field(None, ge=0, description="Peak memory usage")
    status: str = Field(..., description="success or failure")
    notes: Optional[str] = Field(None, description="Performance observations")

    model_config = ConfigDict(use_enum_values=True)


class TestEmailMetadata(BaseModel):
    """
    Metadata about emails selected for testing

    Persistence: data/e2e_test/test_email_ids.json (array of these objects)
    """

    email_id: str = Field(..., min_length=1, description="Gmail message ID")
    subject: str = Field(..., min_length=1, description="Email subject line")
    received_date: str = Field(
        ..., description="When email was received (ISO 8601 date)"
    )
    collaboration_type: Optional[str] = Field(
        None, description="Detected type: [A], [B], [C], [D], or null"
    )
    has_korean_text: bool = Field(..., description="Contains Korean characters")
    selection_reason: SelectionReason = Field(
        ..., description="Why this email was selected"
    )
    notes: Optional[str] = Field(None, description="Additional context")

    model_config = ConfigDict(use_enum_values=True)
