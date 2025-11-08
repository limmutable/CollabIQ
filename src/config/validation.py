"""Configuration validation on startup.

Verifies credentials, directory permissions, and environment setup.

Usage:
    from config.validation import validate_configuration

    # Validate all settings
    results = validate_configuration()
    if not results.is_valid:
        print(results.error_message)
        sys.exit(1)
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation.

    Attributes:
        is_valid: True if all checks passed
        errors: List of error messages
        warnings: List of warning messages
    """

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    @property
    def error_message(self) -> str:
        """Format errors as a single message."""
        if not self.errors:
            return ""
        return "\n".join(f"  ✗ {err}" for err in self.errors)

    @property
    def warning_message(self) -> str:
        """Format warnings as a single message."""
        if not self.warnings:
            return ""
        return "\n".join(f"  ⚠ {warn}" for warn in self.warnings)


def validate_configuration(
    settings: Optional["Settings"] = None,
) -> ValidationResult:
    """Validate application configuration.

    Checks:
    1. Gmail credentials file exists and is readable
    2. All required directories can be created
    3. All required directories are writable
    4. Log level is valid
    5. Batch size is within reasonable limits

    Args:
        settings: Settings instance to validate (default: get_settings())

    Returns:
        ValidationResult with validation status and messages

    Example:
        >>> result = validate_configuration()
        >>> if not result.is_valid:
        ...     print(result.error_message)
        ...     sys.exit(1)
    """
    if settings is None:
        settings = get_settings()

    errors: List[str] = []
    warnings: List[str] = []

    # Check 1: Gmail credentials
    if not settings.gmail_credentials_path.exists():
        errors.append(f"Gmail credentials not found: {settings.gmail_credentials_path}")
        errors.append(
            "Download OAuth2 credentials from Google Cloud Console as credentials.json"
        )
    elif not settings.gmail_credentials_path.is_file():
        errors.append(
            f"Gmail credentials path is not a file: {settings.gmail_credentials_path}"
        )
    else:
        # Check if file is readable
        try:
            settings.gmail_credentials_path.read_text()
        except PermissionError:
            errors.append(
                f"Cannot read Gmail credentials: {settings.gmail_credentials_path} (permission denied)"
            )
        except Exception as e:
            errors.append(
                f"Cannot read Gmail credentials: {settings.gmail_credentials_path} ({e})"
            )

    # Check 2: Directory creation
    dirs_to_check = [
        ("Data directory", settings.data_dir),
        ("Raw email directory", settings.raw_email_dir),
        ("Cleaned email directory", settings.cleaned_email_dir),
        ("Log directory", settings.log_dir),
    ]

    for name, directory in dirs_to_check:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            errors.append(f"Cannot create {name}: {directory} (permission denied)")
        except Exception as e:
            errors.append(f"Cannot create {name}: {directory} ({e})")

    # Check 3: Directory writability
    for name, directory in dirs_to_check:
        if directory.exists():
            test_file = directory / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except PermissionError:
                errors.append(
                    f"{name} is not writable: {directory} (permission denied)"
                )
            except Exception as e:
                errors.append(f"{name} is not writable: {directory} ({e})")

    # Check 4: Duplicate tracker directory
    tracker_dir = settings.duplicate_tracker_path.parent
    if not tracker_dir.exists():
        try:
            tracker_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(
                f"Cannot create duplicate tracker directory: {tracker_dir} ({e})"
            )

    # Check 5: Batch size warnings
    if settings.gmail_batch_size > 100:
        warnings.append(
            f"Gmail batch size is large ({settings.gmail_batch_size}). "
            "This may trigger rate limits. Consider using 50 or less."
        )

    # Check 6: Token file warnings
    if not settings.gmail_token_path.exists():
        warnings.append(
            f"Gmail token not found: {settings.gmail_token_path}. "
            "OAuth flow will run on first connection."
        )

    # Check 7: Pub/Sub configuration (future feature)
    if settings.pubsub_topic and not settings.pubsub_project_id:
        warnings.append(
            "Pub/Sub topic configured but project_id missing. "
            "Pub/Sub features will not work."
        )

    # Check 8: Infisical configuration validation
    if settings.infisical_enabled:
        # Validate required Infisical settings
        if not settings.infisical_project_id:
            errors.append(
                "Infisical enabled but INFISICAL_PROJECT_ID not configured. "
                "Please set INFISICAL_PROJECT_ID in .env file."
            )
        if not settings.infisical_environment:
            errors.append(
                "Infisical enabled but INFISICAL_ENVIRONMENT not configured. "
                "Please set INFISICAL_ENVIRONMENT to 'development' or 'production'."
            )
        if not settings.infisical_client_id:
            errors.append(
                "Infisical enabled but INFISICAL_CLIENT_ID not configured. "
                "Please set INFISICAL_CLIENT_ID in .env file."
            )
        if not settings.infisical_client_secret:
            errors.append(
                "Infisical enabled but INFISICAL_CLIENT_SECRET not configured. "
                "Please set INFISICAL_CLIENT_SECRET in .env file."
            )

        # Test Infisical connectivity if credentials provided
        if (
            settings.infisical_project_id
            and settings.infisical_environment
            and settings.infisical_client_id
            and settings.infisical_client_secret
        ):
            try:
                from config.infisical_client import InfisicalClient

                client = InfisicalClient(settings)
                client.authenticate()

                # Try to verify we can access at least one secret (connectivity test)
                logger.info(
                    f"✓ Infisical authentication successful "
                    f"(environment: {settings.infisical_environment})"
                )
            except Exception as e:
                # Infisical errors are warnings, not failures (fallback to .env exists)
                warnings.append(
                    f"Infisical authentication failed: {str(e)}. "
                    f"Application will fall back to .env file for secrets. "
                    f"Check INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET."
                )
    else:
        # Infisical disabled - warn if in production
        logger.info("Infisical is disabled - secrets will be read from .env file")

    # Determine overall validity
    is_valid = len(errors) == 0

    result = ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    # Log results
    if is_valid:
        logger.info("Configuration validation passed")
        if warnings:
            logger.warning(f"Configuration warnings:\n{result.warning_message}")
    else:
        logger.error(f"Configuration validation failed:\n{result.error_message}")

    return result


def validate_on_startup() -> None:
    """Validate configuration on startup and exit if invalid.

    This is a convenience function that calls validate_configuration()
    and exits the program if validation fails.

    Example:
        >>> if __name__ == "__main__":
        ...     validate_on_startup()
        ...     # Continue with application logic
    """
    result = validate_configuration()

    if result.warnings:
        print("\nConfiguration Warnings:")
        print(result.warning_message)
        print()

    if not result.is_valid:
        print("\nConfiguration Errors:")
        print(result.error_message)
        print("\nPlease fix the above errors and try again.")
        import sys

        sys.exit(1)

    print("✓ Configuration validation passed")
