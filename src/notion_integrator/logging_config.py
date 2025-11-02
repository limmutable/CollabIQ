"""
Logging Configuration for Notion Integrator

Configures structured logging for the Notion integration module with:
- Module-specific logger
- Configurable log levels
- Structured log formatting
- Performance tracking
- Error context capture

Usage:
    >>> from notion_integrator.logging_config import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Schema discovery started", extra={"database_id": "abc123"})
"""

import logging
import os
import sys
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the given module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def configure_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Configure logging for the Notion integrator module.

    Sets up console and file handlers with structured formatting.
    Should be called once during application initialization.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                   Defaults to LOG_LEVEL env var or INFO
        log_file: Path to log file (optional)
                  Defaults to LOG_FILE env var
        log_format: Custom log format (optional)
                    Defaults to structured format with timestamp
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Determine log file
    if log_file is None:
        log_file = os.getenv("LOG_FILE")

    # Determine log format
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )

    # Get root logger for notion_integrator module
    logger = logging.getLogger("notion_integrator")
    logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    logger.info(
        "Notion integrator logging configured",
        extra={
            "log_level": log_level,
            "log_file": log_file if log_file else "console only",
        },
    )


class PerformanceLogger:
    """
    Context manager for logging operation performance.

    Tracks operation duration and logs completion with timing information.

    Usage:
        >>> logger = get_logger(__name__)
        >>> with PerformanceLogger(logger, "schema_discovery", database_id="abc123"):
        ...     # Perform operation
        ...     schema = await discover_schema(db_id)
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        log_level: int = logging.INFO,
        **context,
    ):
        """
        Initialize performance logger.

        Args:
            logger: Logger instance
            operation: Operation name for logging
            log_level: Log level for completion message
            **context: Additional context to include in logs
        """
        self.logger = logger
        self.operation = operation
        self.log_level = log_level
        self.context = context
        self.start_time = None

    def __enter__(self):
        """Start timing and log operation start."""
        import time

        self.start_time = time.monotonic()
        self.logger.log(
            self.log_level,
            f"{self.operation} started",
            extra=self.context,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation completion with duration."""
        import time

        duration = time.monotonic() - self.start_time

        if exc_type is None:
            # Success
            self.logger.log(
                self.log_level,
                f"{self.operation} completed",
                extra={**self.context, "duration_seconds": f"{duration:.2f}"},
            )
        else:
            # Error
            self.logger.error(
                f"{self.operation} failed",
                extra={
                    **self.context,
                    "duration_seconds": f"{duration:.2f}",
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val),
                },
                exc_info=True,
            )

        return False  # Don't suppress exceptions


def log_cache_operation(
    logger: logging.Logger,
    operation: str,
    cache_type: str,
    database_name: str,
    hit: Optional[bool] = None,
    **extra_context,
) -> None:
    """
    Log cache operation with structured context.

    Args:
        logger: Logger instance
        operation: Operation type (read, write, invalidate)
        cache_type: "schema" or "data"
        database_name: Database name
        hit: Whether cache hit occurred (for read operations)
        **extra_context: Additional context fields
    """
    context = {
        "operation": operation,
        "cache_type": cache_type,
        "database_name": database_name,
        **extra_context,
    }

    if hit is not None:
        context["cache_hit"] = hit

    logger.info(f"Cache {operation}", extra=context)


def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    database_id: Optional[str] = None,
    page_id: Optional[str] = None,
    **extra_context,
) -> None:
    """
    Log Notion API call with structured context.

    Args:
        logger: Logger instance
        endpoint: API endpoint (databases.retrieve, pages.query, etc.)
        database_id: Database ID if applicable
        page_id: Page ID if applicable
        **extra_context: Additional context fields
    """
    context = {
        "endpoint": endpoint,
        **extra_context,
    }

    if database_id:
        context["database_id"] = database_id
    if page_id:
        context["page_id"] = page_id

    logger.debug(f"API call: {endpoint}", extra=context)


def log_relationship_resolution(
    logger: logging.Logger,
    source_page_id: str,
    target_page_id: str,
    depth: int,
    relationship_type: str,
    **extra_context,
) -> None:
    """
    Log relationship resolution with structured context.

    Args:
        logger: Logger instance
        source_page_id: Source page ID
        target_page_id: Target page ID
        depth: Current relationship depth
        relationship_type: Relation property name
        **extra_context: Additional context fields
    """
    context = {
        "source_page_id": source_page_id,
        "target_page_id": target_page_id,
        "depth": depth,
        "relationship_type": relationship_type,
        **extra_context,
    }

    logger.debug("Resolving relationship", extra=context)


def log_data_formatting(
    logger: logging.Logger,
    total_companies: int,
    ssg_count: int,
    portfolio_count: int,
    data_freshness: str,
    **extra_context,
) -> None:
    """
    Log LLM data formatting with structured context.

    Args:
        logger: Logger instance
        total_companies: Total company count
        ssg_count: Shinsegae affiliate count
        portfolio_count: Portfolio company count
        data_freshness: "cached" or "fresh"
        **extra_context: Additional context fields
    """
    context = {
        "total_companies": total_companies,
        "shinsegae_affiliate_count": ssg_count,
        "portfolio_company_count": portfolio_count,
        "data_freshness": data_freshness,
        **extra_context,
    }

    logger.info("Data formatted for LLM", extra=context)


# Initialize module logger with default configuration
# Users can call configure_logging() to customize
_default_logger = logging.getLogger("notion_integrator")
if not _default_logger.handlers:
    # Only configure if not already configured
    configure_logging()
