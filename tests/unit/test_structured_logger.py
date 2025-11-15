"""Unit tests for structured logger.

Tests:
- JSON formatting
- Sanitization of sensitive data (API keys, email content)
- Severity-level logging
- ErrorRecord integration
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from error_handling.models import ErrorCategory, ErrorRecord, ErrorSeverity
from error_handling.structured_logger import JSONFormatter, StructuredLogger


class TestJSONFormatter:
    """Test JSON formatting for log records."""

    def test_json_formatter_basic_message(self):
        """Test formatting a basic log message as JSON."""
        formatter = JSONFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.context = {"key": "value"}

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Test message"
        assert parsed["severity"] == "INFO"
        assert parsed["context"] == {"key": "value"}
        assert parsed["error_type"] is None
        assert parsed["stack_trace"] is None

    def test_json_formatter_with_exception(self):
        """Test formatting log with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.context = {}

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Error occurred"
        assert parsed["severity"] == "ERROR"
        assert parsed["error_type"] == "ValueError"
        assert "Test error" in parsed["stack_trace"]


class TestStructuredLogger:
    """Test StructuredLogger functionality."""

    def setup_method(self):
        """Clean up log directory before each test."""
        # Clear any existing handlers
        logger_instance = StructuredLogger("test_logger")
        logger_instance.logger.handlers.clear()

    def test_logger_initialization(self):
        """Test logger initializes with correct name."""
        logger = StructuredLogger("test_logger")

        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.DEBUG

    def test_sanitize_context_redacts_api_keys(self):
        """Test that API keys are redacted from context."""
        logger = StructuredLogger("test")

        context = {
            "email_id": "msg_123",
            "api_key": "AIzaSyDXYZ1234567890ABCDEFGHIJK",  # Looks like API key
        }

        sanitized = logger._sanitize_context(context)

        assert sanitized["email_id"] == "msg_123"
        assert sanitized["api_key"] == "[REDACTED]"

    def test_sanitize_context_truncates_email_content(self):
        """Test that long email content is truncated."""
        logger = StructuredLogger("test")

        long_content = "x" * 300  # Longer than EMAIL_CONTENT_MAX_LENGTH (200)
        context = {"email_content": long_content}

        sanitized = logger._sanitize_context(context)

        assert len(sanitized["email_content"]) <= 220  # 200 + "... [truncated]"
        assert sanitized["email_content"].endswith("... [truncated]")

    def test_sanitize_context_preserves_normal_values(self):
        """Test that normal values are not modified."""
        logger = StructuredLogger("test")

        context = {
            "email_id": "msg_123",
            "operation": "fetch_emails",
            "retry_count": 2,
            "short_message": "Hello world",
        }

        sanitized = logger._sanitize_context(context)

        assert sanitized == context  # Should be unchanged

    def test_log_error_with_error_record(self):
        """Test logging an ErrorRecord."""
        logger = StructuredLogger("test")

        error_record = ErrorRecord(
            timestamp=datetime.now(UTC),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TRANSIENT,
            message="Connection timeout",
            error_type="socket.timeout",
            stack_trace="Traceback...",
            context={"email_id": "msg_123", "retry_count": 2},
            http_status=None,
            retry_count=2,
        )

        with patch.object(logger.logger, "log") as mock_log:
            logger.log_error(error_record)

            # Check that log was called with correct level
            assert mock_log.called
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.ERROR  # First arg is log level
            assert call_args[0][1] == "Connection timeout"  # Second arg is message

            # Check extra context
            extra = call_args[1]["extra"]
            assert extra["context"]["email_id"] == "msg_123"
            assert extra["error_type"] == "socket.timeout"
            assert extra["category"] == "TRANSIENT"
            assert extra["retry_count"] == 2

    def test_debug_logging(self):
        """Test debug() method."""
        logger = StructuredLogger("test")

        with patch.object(logger.logger, "debug") as mock_debug:
            logger.debug("Debug message", context={"key": "value"})

            assert mock_debug.called
            call_args = mock_debug.call_args
            assert call_args[0][0] == "Debug message"
            assert call_args[1]["extra"]["context"] == {"key": "value"}

    def test_info_logging(self):
        """Test info() method."""
        logger = StructuredLogger("test")

        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Info message", context={"key": "value"})

            assert mock_info.called
            call_args = mock_info.call_args
            assert call_args[0][0] == "Info message"

    def test_warning_logging(self):
        """Test warning() method."""
        logger = StructuredLogger("test")

        with patch.object(logger.logger, "warning") as mock_warning:
            logger.warning("Warning message", context={"key": "value"})

            assert mock_warning.called
            call_args = mock_warning.call_args
            assert call_args[0][0] == "Warning message"

    def test_error_logging(self):
        """Test error() method."""
        logger = StructuredLogger("test")

        with patch.object(logger.logger, "error") as mock_error:
            logger.error("Error message", context={"key": "value"})

            assert mock_error.called
            call_args = mock_error.call_args
            assert call_args[0][0] == "Error message"

    def test_critical_logging(self):
        """Test critical() method."""
        logger = StructuredLogger("test")

        with patch.object(logger.logger, "critical") as mock_critical:
            logger.critical("Critical message", context={"key": "value"})

            assert mock_critical.called
            call_args = mock_critical.call_args
            assert call_args[0][0] == "Critical message"

    def test_logging_with_sanitization(self):
        """Test that all logging methods sanitize context."""
        logger = StructuredLogger("test")

        api_key = "AIzaSyDXYZ1234567890ABCDEFGHIJK"
        context = {"api_key": api_key}

        with patch.object(logger.logger, "info") as mock_info:
            logger.info("Test", context=context)

            # Check that API key was redacted
            extra = mock_info.call_args[1]["extra"]
            assert extra["context"]["api_key"] == "[REDACTED]"

    def test_log_error_with_different_severity_levels(self):
        """Test logging ErrorRecords with different severity levels."""
        logger = StructuredLogger("test")

        severity_to_level = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }

        for severity, expected_level in severity_to_level.items():
            error_record = ErrorRecord(
                timestamp=datetime.now(UTC),
                severity=severity,
                category=ErrorCategory.TRANSIENT,
                message=f"Message with {severity.value}",
                error_type="TestError",
                stack_trace=None,
                context={},
            )

            with patch.object(logger.logger, "log") as mock_log:
                logger.log_error(error_record)

                # Check correct logging level was used
                assert mock_log.call_args[0][0] == expected_level


class TestStructuredLoggerFileHandlers:
    """Test file handler creation and separation by severity."""

    def test_log_directory_creation(self):
        """Test that log directories are created."""
        # Clear handlers first
        logger = StructuredLogger("test_file_handler")
        logger.logger.handlers.clear()

        # Re-initialize to trigger directory creation
        logger._setup_handlers()

        # Check directories exist
        log_dir = Path("data/logs")
        assert log_dir.exists()
        assert (log_dir / "ERROR").exists()
        assert (log_dir / "WARNING").exists()
        assert (log_dir / "INFO").exists()

    def test_multiple_logger_instances_share_handlers(self):
        """Test that multiple StructuredLogger instances don't duplicate handlers."""
        logger1 = StructuredLogger("test_shared")
        handler_count_1 = len(logger1.logger.handlers)

        # Creating another instance with same name should not add handlers
        logger2 = StructuredLogger("test_shared")
        handler_count_2 = len(logger2.logger.handlers)

        # Should have same number of handlers (not duplicated)
        assert handler_count_1 == handler_count_2


class TestStructuredLoggerIntegration:
    """Integration tests for StructuredLogger."""

    def test_error_record_to_json_serialization(self):
        """Test that ErrorRecord can be serialized to JSON for logging."""
        error_record = ErrorRecord(
            timestamp=datetime.now(UTC),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TRANSIENT,
            message="Test error",
            error_type="socket.timeout",
            stack_trace="Traceback...",
            context={"email_id": "msg_123"},
            http_status=503,
            retry_count=2,
        )

        json_data = error_record.to_json()

        # Verify JSON is valid and contains expected fields
        assert isinstance(json_data, dict)
        assert json_data["severity"] == "ERROR"
        assert json_data["category"] == "TRANSIENT"
        assert json_data["message"] == "Test error"
        assert json_data["error_type"] == "socket.timeout"
        assert json_data["http_status"] == 503
        assert json_data["retry_count"] == 2
        assert json_data["context"]["email_id"] == "msg_123"

        # Verify timestamp is ISO format string
        assert isinstance(json_data["timestamp"], str)
        # Should be parseable back to datetime
        datetime.fromisoformat(json_data["timestamp"])

    def test_global_logger_instance_exists(self):
        """Test that global logger instance is available."""
        from error_handling.structured_logger import logger

        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "collabiq.error_handling"


class TestStructuredLoggerActionableLogging:
    """Test SC-005: 100% of errors have actionable logs."""

    def test_error_log_contains_required_fields(self):
        """Test that error logs contain all required fields for SC-005."""
        logger = StructuredLogger("test")

        error_record = ErrorRecord(
            timestamp=datetime.now(UTC),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TRANSIENT,
            message="Gmail API timeout during fetch_messages",
            error_type="socket.timeout",
            stack_trace="Traceback (most recent call last):\n  File...",
            context={
                "email_id": "msg_123",
                "operation": "fetch_messages",
                "service": "gmail",
                "retry_count": 2,
            },
            http_status=None,
            retry_count=2,
        )

        json_data = error_record.to_json()

        # SC-005 requirements: actionable logs must include
        # 1. What happened (message, error_type)
        assert "message" in json_data
        assert "error_type" in json_data

        # 2. Where it happened (context with operation, service)
        assert "context" in json_data
        assert "operation" in json_data["context"]
        assert "service" in json_data["context"]

        # 3. When it happened (timestamp)
        assert "timestamp" in json_data

        # 4. Why it might have happened (category, http_status if applicable)
        assert "category" in json_data

        # 5. How to debug (stack_trace, retry_count)
        assert "stack_trace" in json_data
        assert "retry_count" in json_data

        # All required fields present → actionable
        required_fields = [
            "timestamp",
            "severity",
            "category",
            "message",
            "error_type",
            "context",
        ]
        for field in required_fields:
            assert field in json_data, f"Missing required field: {field}"
