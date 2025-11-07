"""
ErrorCollector: Capture, categorize, and persist errors from E2E testing

Responsibilities:
- Collect errors with full context (exception, input data, stage)
- Auto-categorize severity based on error type and stage
- Persist errors to disk organized by severity
- Generate error summaries per test run
- Update error resolution status
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.e2e_test.models import ErrorRecord, PipelineStage, ResolutionStatus, Severity


class ErrorCollector:
    """
    Collects and manages errors discovered during E2E testing

    Auto-categorization rules:
    - Critical: API auth failures, unhandled exceptions, data corruption
    - High: Korean encoding errors, date parsing failures, wrong company IDs
    - Medium: Edge cases, ambiguous data, occasional failures
    - Low: Verbose logging, suboptimal messages, minor issues
    """

    def __init__(self, output_dir: str = "data/e2e_test"):
        """
        Initialize ErrorCollector

        Args:
            output_dir: Base directory for E2E test outputs
        """
        self.output_dir = Path(output_dir)
        self.errors_dir = self.output_dir / "errors"

        # Ensure severity subdirectories exist
        for severity in ["critical", "high", "medium", "low"]:
            (self.errors_dir / severity).mkdir(parents=True, exist_ok=True)

        # Track error count per email (for incrementing error_index)
        self._error_counters: dict[str, int] = {}

    def collect_error(
        self,
        run_id: str,
        email_id: str,
        stage: PipelineStage | str,
        exception: Optional[Exception] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        input_data: Optional[dict] = None,
        severity: Optional[Severity] = None,
    ) -> ErrorRecord:
        """
        Capture an error with full context and categorize by severity

        Args:
            run_id: Test run ID where error occurred
            email_id: Email being processed when error occurred
            stage: Pipeline stage where error occurred
            exception: Python exception object (if available)
            error_type: Type of error (e.g., "APIError"). If None, inferred from exception.
            error_message: Human-readable error description. If None, inferred from exception.
            input_data: Relevant input data that caused error (will be sanitized)
            severity: Severity level. If None, auto-categorized based on error type.

        Returns:
            ErrorRecord: Created error record with unique error_id

        Raises:
            ValueError: If both exception and error_message are None
        """
        # Validate inputs
        if exception is None and error_message is None:
            raise ValueError("Either exception or error_message must be provided")

        # Extract error details from exception if provided
        if exception is not None:
            if error_type is None:
                error_type = type(exception).__name__
            if error_message is None:
                error_message = str(exception)
            stack_trace = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
        else:
            stack_trace = None

        # Ensure error_type has a value
        if error_type is None:
            error_type = "UnknownError"

        # Auto-categorize severity if not provided
        if severity is None:
            severity = self._auto_categorize_severity(error_type, stage)

        # Generate unique error_id
        key = f"{run_id}_{email_id}"
        self._error_counters[key] = self._error_counters.get(key, 0) + 1
        error_index = f"{self._error_counters[key]:03d}"
        error_id = f"{run_id}_{email_id}_{error_index}"

        # Sanitize input data (remove sensitive information)
        if input_data is not None:
            input_data = self._sanitize_input_data(input_data)

        # Create ErrorRecord
        error_record = ErrorRecord(
            error_id=error_id,
            run_id=run_id,
            email_id=email_id,
            severity=severity,
            stage=stage if isinstance(stage, str) else stage.value,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            input_data_snapshot=input_data,
            timestamp=datetime.now(),
            resolution_status=ResolutionStatus.OPEN,
            fix_commit=None,
            notes=None,
        )

        return error_record

    def persist_error(self, error: ErrorRecord) -> str:
        """
        Write error record to disk in appropriate severity directory

        Args:
            error: Error record to persist

        Returns:
            str: File path where error was written

        Raises:
            IOError: If file write fails
        """
        # Determine output path
        severity_dir = self.errors_dir / error.severity
        severity_dir.mkdir(parents=True, exist_ok=True)

        file_path = severity_dir / f"{error.error_id}.json"

        # Serialize to JSON with UTF-8 encoding
        error_dict = error.model_dump(mode="json")

        # Convert datetime to ISO format string for JSON serialization
        if isinstance(error_dict.get("timestamp"), datetime):
            error_dict["timestamp"] = error_dict["timestamp"].isoformat()

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(error_dict, f, indent=2, ensure_ascii=False)

        return str(file_path)

    def get_error_summary(self, run_id: str) -> dict[str, int]:
        """
        Get error count breakdown by severity for a test run

        Args:
            run_id: Test run ID to summarize

        Returns:
            dict[str, int]: Error counts by severity
                Keys: "critical", "high", "medium", "low"
                Values: non-negative integers
        """
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        # Scan each severity directory
        for severity in ["critical", "high", "medium", "low"]:
            severity_dir = self.errors_dir / severity

            if not severity_dir.exists():
                continue

            # Count error files matching this run_id
            matching_files = list(severity_dir.glob(f"{run_id}_*.json"))
            summary[severity] = len(matching_files)

        return summary

    def update_error_status(
        self,
        error_id: str,
        resolution_status: str,
        fix_commit: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ErrorRecord:
        """
        Update resolution status of an error after fix is applied

        Args:
            error_id: Error to update
            resolution_status: New status ("open", "fixed", "deferred", "wont_fix")
            fix_commit: Git commit hash where fix was applied
            notes: Additional context about resolution

        Returns:
            ErrorRecord: Updated error record

        Raises:
            FileNotFoundError: If error with error_id not found
        """
        # Find error file across all severity directories
        error_file = None

        for severity in ["critical", "high", "medium", "low"]:
            candidate = self.errors_dir / severity / f"{error_id}.json"
            if candidate.exists():
                error_file = candidate
                break

        if error_file is None:
            raise FileNotFoundError(f"Error with ID '{error_id}' not found")

        # Load existing error record
        with error_file.open("r", encoding="utf-8") as f:
            error_data = json.load(f)

        # Update fields
        error_data["resolution_status"] = resolution_status
        if fix_commit is not None:
            error_data["fix_commit"] = fix_commit
        if notes is not None:
            error_data["notes"] = notes

        # Write updated record back
        with error_file.open("w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)

        # Return updated ErrorRecord
        return ErrorRecord(**error_data)

    def _auto_categorize_severity(
        self, error_type: str, stage: PipelineStage | str
    ) -> Severity:
        """
        Auto-categorize severity based on error type and pipeline stage

        Critical: API auth, unhandled exceptions, data corruption
        High: Korean encoding, date parsing, wrong company IDs
        Medium: Edge cases, occasional failures
        Low: Verbose logging, minor issues

        Args:
            error_type: Type of error (e.g., "ValueError", "AuthenticationError")
            stage: Pipeline stage where error occurred

        Returns:
            Severity: Auto-determined severity level
        """
        error_type_lower = error_type.lower()

        # Critical errors
        if "authentication" in error_type_lower or "auth" in error_type_lower:
            return Severity.CRITICAL
        if "unhandled" in error_type_lower or "crash" in error_type_lower:
            return Severity.CRITICAL
        if "corruption" in error_type_lower or "data loss" in error_type_lower:
            return Severity.CRITICAL
        if "schema" in error_type_lower and "mismatch" in error_type_lower:
            return Severity.CRITICAL

        # High severity errors
        if "encoding" in error_type_lower or "unicode" in error_type_lower:
            return Severity.HIGH
        if "korean" in error_type_lower or "mojibake" in error_type_lower:
            return Severity.HIGH
        if "date" in error_type_lower and "parsing" in error_type_lower:
            return Severity.HIGH
        if "company" in error_type_lower and (
            "match" in error_type_lower or "wrong" in error_type_lower
        ):
            return Severity.HIGH

        # Medium severity errors (edge cases, ambiguity)
        if "edge case" in error_type_lower or "ambiguous" in error_type_lower:
            return Severity.MEDIUM
        if "confidence" in error_type_lower or "threshold" in error_type_lower:
            return Severity.MEDIUM
        if "optional" in error_type_lower or "missing" in error_type_lower:
            return Severity.MEDIUM

        # Low severity (default for unknown errors)
        return Severity.LOW

    def _sanitize_input_data(self, input_data: dict) -> dict:
        """
        Remove sensitive information from input data snapshot

        Removes:
        - API keys (any key containing "api_key", "token", "secret")
        - Credentials (keys containing "password", "credential")
        - Large data (truncate strings > 1000 chars)

        Args:
            input_data: Original input data

        Returns:
            dict: Sanitized input data
        """
        sanitized = {}

        for key, value in input_data.items():
            key_lower = key.lower()

            # Remove sensitive keys
            if any(
                sensitive in key_lower
                for sensitive in [
                    "api_key",
                    "token",
                    "secret",
                    "password",
                    "credential",
                ]
            ):
                sanitized[key] = "[REDACTED]"
                continue

            # Truncate long strings
            if isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "... [truncated]"
            else:
                sanitized[key] = value

        return sanitized
