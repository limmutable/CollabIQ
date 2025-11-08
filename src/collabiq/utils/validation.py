"""
Input validation helpers for CLI arguments.

Provides sanitization and validation functions to prevent
injection attacks and ensure valid input formats.
"""

import re
from datetime import datetime
from typing import Optional
import typer
from dateparser import parse as parse_date


def validate_email_id(email_id: str) -> str:
    """
    Validate email ID format to prevent path traversal.

    Args:
        email_id: Email ID to validate

    Returns:
        Validated email ID

    Raises:
        typer.BadParameter: If email ID contains invalid characters

    Example:
        email_id = validate_email_id("email_001")  # OK
        email_id = validate_email_id("../etc/passwd")  # Raises error
    """
    # Email IDs should be alphanumeric with underscores and hyphens only
    if not re.match(r"^[a-zA-Z0-9_-]+$", email_id):
        raise typer.BadParameter(
            f"Invalid email ID format: '{email_id}'. "
            "Email IDs must contain only letters, numbers, underscores, and hyphens."
        )
    return email_id


def validate_date(date_str: str) -> datetime:
    """
    Validate and parse date string.

    Args:
        date_str: Date string (e.g., "yesterday", "2025-11-01", "3 days ago")

    Returns:
        Parsed datetime object

    Raises:
        typer.BadParameter: If date string cannot be parsed

    Example:
        date = validate_date("yesterday")
        date = validate_date("2025-11-01")
    """
    parsed = parse_date(date_str)
    if not parsed:
        raise typer.BadParameter(
            f"Invalid date format: '{date_str}'. "
            "Use formats like 'yesterday', '2025-11-01', or '3 days ago'."
        )
    return parsed


def validate_severity(severity: str) -> str:
    """
    Validate error severity level.

    Args:
        severity: Severity string

    Returns:
        Validated severity (lowercase)

    Raises:
        typer.BadParameter: If severity is not valid

    Example:
        severity = validate_severity("HIGH")  # Returns "high"
    """
    valid_severities = ["critical", "high", "medium", "low"]
    severity_lower = severity.lower()

    if severity_lower not in valid_severities:
        raise typer.BadParameter(
            f"Invalid severity: '{severity}'. "
            f"Must be one of: {', '.join(valid_severities)}."
        )

    return severity_lower


def validate_provider(provider: str) -> str:
    """
    Validate LLM provider name.

    Args:
        provider: Provider name

    Returns:
        Validated provider (lowercase)

    Raises:
        typer.BadParameter: If provider is not valid

    Example:
        provider = validate_provider("Gemini")  # Returns "gemini"
    """
    valid_providers = ["gemini", "claude", "openai"]
    provider_lower = provider.lower()

    if provider_lower not in valid_providers:
        raise typer.BadParameter(
            f"Invalid provider: '{provider}'. "
            f"Must be one of: {', '.join(valid_providers)}."
        )

    return provider_lower


def validate_strategy(strategy: str) -> str:
    """
    Validate LLM orchestration strategy.

    Args:
        strategy: Strategy name

    Returns:
        Validated strategy (lowercase)

    Raises:
        typer.BadParameter: If strategy is not valid

    Example:
        strategy = validate_strategy("Failover")  # Returns "failover"
    """
    valid_strategies = ["failover", "consensus", "best-match"]
    strategy_lower = strategy.lower()

    if strategy_lower not in valid_strategies:
        raise typer.BadParameter(
            f"Invalid strategy: '{strategy}'. "
            f"Must be one of: {', '.join(valid_strategies)}."
        )

    return strategy_lower
