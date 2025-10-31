"""Logging configuration for CollabIQ email reception pipeline.

Implements FR-009: Log all email processing activities with timestamps.

Usage:
    from src.config.logging_config import setup_logging

    setup_logging()  # Use defaults
    setup_logging(level="DEBUG", log_dir="custom_logs")  # Custom settings
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """Configure logging for the email reception pipeline.

    Creates both file and console handlers with structured formatting.
    All timestamps are in ISO 8601 format for consistency.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        log_file: Log file name (default: email_reception.log)
        console: Enable console output (default: True)

    Example:
        >>> setup_logging(level="DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Email received", extra={"message_id": "<123@gmail.com>"})
    """
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Define log format (FR-009: timestamps required)
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_dir or log_file:
        log_directory = log_dir or Path("logs")
        log_directory.mkdir(parents=True, exist_ok=True)

        log_filename = log_file or "email_reception.log"
        log_path = log_directory / log_filename

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"Logging initialized: {log_path}")

    # Silence noisy third-party loggers
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


# Pre-configured logger for common use
logger = get_logger(__name__)
