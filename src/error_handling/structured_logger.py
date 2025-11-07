"""Structured JSON logging for error handling."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .models import ErrorRecord, ErrorSeverity, ErrorCategory


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": self.formatTime(record),
            "severity": record.levelname,
            "message": record.getMessage(),
            "error_type": (
                record.exc_info[0].__name__ if record.exc_info else None
            ),
            "stack_trace": (
                self.formatException(record.exc_info) if record.exc_info else None
            ),
            "context": getattr(record, "context", {}),
        }
        return json.dumps(log_obj)


class StructuredLogger:
    """Structured logger with JSON formatting and sanitization."""

    # Patterns for sensitive data
    API_KEY_PATTERN = re.compile(r"[A-Za-z0-9_-]{20,}")
    EMAIL_CONTENT_MAX_LENGTH = 200

    def __init__(self, name: str = "collabiq.error_handling"):
        """
        Initialize structured logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create handlers for each severity level
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up file handlers for each severity level."""
        log_dir = Path("data/logs")

        severity_levels = {
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
        }

        for severity_name, level in severity_levels.items():
            severity_dir = log_dir / severity_name
            severity_dir.mkdir(parents=True, exist_ok=True)

            # Create handler
            handler = logging.FileHandler(
                severity_dir / f"{severity_name.lower()}.log"
            )
            handler.setLevel(level)
            handler.setFormatter(JSONFormatter())

            # Add filter to only log this severity level
            handler.addFilter(lambda record, lvl=level: record.levelno == lvl)

            self.logger.addHandler(handler)

        # Also add console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        self.logger.addHandler(console_handler)

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context to remove sensitive information.

        Args:
            context: Original context dictionary

        Returns:
            Sanitized context
        """
        sanitized = {}

        for key, value in context.items():
            if isinstance(value, str):
                # Redact API keys
                if self.API_KEY_PATTERN.fullmatch(value):
                    sanitized[key] = "[REDACTED]"
                # Truncate email content
                elif key == "email_content" and len(value) > self.EMAIL_CONTENT_MAX_LENGTH:
                    sanitized[key] = value[: self.EMAIL_CONTENT_MAX_LENGTH] + "... [truncated]"
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value

        return sanitized

    def log_error(
        self,
        error_record: ErrorRecord,
    ):
        """
        Log an error record with sanitization.

        Args:
            error_record: ErrorRecord to log
        """
        # Sanitize context
        sanitized_context = self._sanitize_context(error_record.context)

        # Map ErrorSeverity to logging level
        level_map = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }

        level = level_map.get(error_record.severity, logging.ERROR)

        # Create log record with extra context
        self.logger.log(
            level,
            error_record.message,
            extra={
                "context": sanitized_context,
                "error_type": error_record.error_type,
                "category": error_record.category.value,
                "retry_count": error_record.retry_count,
            },
            exc_info=(
                (
                    type(error_record.stack_trace),
                    error_record.stack_trace,
                    None,
                )
                if error_record.stack_trace
                else None
            ),
        )

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        sanitized = self._sanitize_context(context or {})
        self.logger.debug(message, extra={"context": sanitized})

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        sanitized = self._sanitize_context(context or {})
        self.logger.info(message, extra={"context": sanitized})

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        sanitized = self._sanitize_context(context or {})
        self.logger.warning(message, extra={"context": sanitized})

    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log error message."""
        sanitized = self._sanitize_context(context or {})
        self.logger.error(message, extra={"context": sanitized})

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        sanitized = self._sanitize_context(context or {})
        self.logger.critical(message, extra={"context": sanitized})


# Global logger instance
logger = StructuredLogger()
