"""
CLI audit logging for operation tracking.

Logs all CLI operations to a file for audit trail and troubleshooting.
"""

import logging
from pathlib import Path
from typing import Any, Optional


# CLI audit log file location
CLI_LOG_FILE = Path("data/logs/cli_audit.log")


def setup_cli_logging(
    log_file: Optional[Path] = None, debug: bool = False
) -> logging.Logger:
    """
    Set up CLI audit logger.

    Args:
        log_file: Path to log file (defaults to CLI_LOG_FILE)
        debug: Enable debug level logging

    Returns:
        Configured logger instance

    Example:
        logger = setup_cli_logging(debug=True)
        logger.info("Command executed")
    """
    if log_file is None:
        log_file = CLI_LOG_FILE

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("collabiq.cli")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create file handler
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Set file permissions (owner read/write, group read)
    try:
        log_file.chmod(0o640)
    except Exception:
        # Ignore permission errors (may not be supported on all systems)
        pass

    return logger


def log_cli_operation(
    command: str,
    success: bool,
    duration_ms: Optional[int] = None,
    **metadata: Any,
) -> None:
    """
    Log a CLI operation to the audit log.

    Args:
        command: Command that was executed (e.g., "email fetch")
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds
        **metadata: Additional metadata to log

    Example:
        log_cli_operation(
            command="email fetch",
            success=True,
            duration_ms=1250,
            limit=10,
            fetched=10
        )
    """
    logger = setup_cli_logging()

    # Build log message
    parts = [
        f"command={command}",
        f"success={success}",
    ]

    if duration_ms is not None:
        parts.append(f"duration_ms={duration_ms}")

    # Add metadata
    for key, value in metadata.items():
        parts.append(f"{key}={value}")

    message = " | ".join(parts)

    if success:
        logger.info(message)
    else:
        logger.error(message)


def log_cli_error(command: str, error: Exception, **metadata: Any) -> None:
    """
    Log a CLI error to the audit log.

    Args:
        command: Command that failed
        error: Exception that occurred
        **metadata: Additional context

    Example:
        try:
            # ... operation
        except Exception as e:
            log_cli_error("email fetch", e, limit=10)
    """
    logger = setup_cli_logging()

    parts = [
        f"command={command}",
        f"error_type={type(error).__name__}",
        f"error_message={str(error)}",
    ]

    # Add metadata
    for key, value in metadata.items():
        parts.append(f"{key}={value}")

    message = " | ".join(parts)
    logger.error(message)
