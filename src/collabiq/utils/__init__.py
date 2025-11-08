"""
CLI utility functions for CollabIQ.

This module provides utilities for:
- Interrupt handling (graceful shutdown on SIGINT/SIGTERM)
- Input validation (argument sanitization)
- CLI operation logging (audit trail)
"""

from .interrupt import InterruptHandler, handle_interrupt
from .validation import validate_email_id, validate_date, validate_severity
from .logging import log_cli_operation, setup_cli_logging

__all__ = [
    "InterruptHandler",
    "handle_interrupt",
    "validate_email_id",
    "validate_date",
    "validate_severity",
    "log_cli_operation",
    "setup_cli_logging",
]
