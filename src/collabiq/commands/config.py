"""
Configuration management commands.

Commands:
- show: Display all configuration (secrets masked)
- validate: Check for missing/invalid settings
- test-secrets: Verify Infisical connectivity
- get: Display specific configuration value

All secrets are automatically masked in output.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from collabiq.formatters.colors import console
from collabiq.formatters.json_output import output_json, format_json_error
from collabiq.formatters.tables import create_table, render_table
from collabiq.utils.logging import log_cli_operation, log_cli_error

# Import config management
from config.settings import get_settings
from config.infisical_client import InfisicalClient

app = typer.Typer(
    name="config",
    help="Configuration management (show, validate, test-secrets, get)",
)


# ==============================================================================
# Helper Functions
# ==============================================================================


def mask_secret(value: str) -> str:
    """
    Mask a secret value showing only first 4 and last 3 characters.

    Examples:
        - "AIzaSyD1234567890" -> "AIza...890"
        - "secret_abc123" -> "secr...123"
        - "abc" -> "***" (too short to mask meaningfully)

    Args:
        value: The secret value to mask

    Returns:
        Masked value with format "first4...last3"
    """
    if not value:
        return "***"

    # For very short values, just mask completely
    if len(value) < 8:
        return "***"

    # Show first 4 and last 3 characters
    return f"{value[:4]}...{value[-3:]}"


def get_config_source(key: str, settings: Any) -> str:
    """
    Determine the source of a configuration value.

    Args:
        key: Configuration key name
        settings: Settings instance

    Returns:
        Source indicator: "Infisical", "env", or "default"
    """
    # Check if Infisical is enabled and connected
    if settings.infisical_enabled and settings.infisical_client:
        if settings.infisical_client.is_connected():
            # Check if this key is in Infisical cache
            if key in settings.infisical_client._cache:
                return "Infisical"

    # Check if it's in environment variables
    if os.getenv(key):
        return "env"

    # Otherwise it's a default value
    return "default"


def categorize_config_keys() -> Dict[str, List[str]]:
    """
    Categorize configuration keys by system component.

    Returns:
        Dictionary mapping category names to lists of config keys
    """
    return {
        "Gmail": [
            "GMAIL_CREDENTIALS_FILE",
            "GMAIL_TOKEN_FILE",
            "GMAIL_BATCH_SIZE",
        ],
        "Notion": [
            "NOTION_API_KEY",
            "COLLABIQ_DB_ID",
            "NOTION_DATABASE_ID_COMPANIES",
            "NOTION_DATABASE_ID_COLLABIQ",
            "DUPLICATE_BEHAVIOR",
        ],
        "Gemini": [
            "GEMINI_API_KEY",
            "GEMINI_MODEL",
            "GEMINI_TIMEOUT_SECONDS",
            "GEMINI_MAX_RETRIES",
        ],
        "LLM": [
            # Future Phase 3b - LLM orchestration config
        ],
        "System": [
            "LOG_LEVEL",
            "DEBUG",
            "DATA_DIR",
            "LOG_DIR",
        ],
        "Infisical": [
            "INFISICAL_ENABLED",
            "INFISICAL_HOST",
            "INFISICAL_PROJECT_ID",
            "INFISICAL_ENVIRONMENT",
            "INFISICAL_CLIENT_ID",
            "INFISICAL_CLIENT_SECRET",
            "INFISICAL_CACHE_TTL",
        ],
    }


def is_secret_key(key: str) -> bool:
    """
    Check if a configuration key contains sensitive data.

    Args:
        key: Configuration key name

    Returns:
        True if key should be masked, False otherwise
    """
    secret_keywords = ["KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIALS"]
    return any(keyword in key.upper() for keyword in secret_keywords)


def get_config_value(key: str, settings: Any) -> Optional[str]:
    """
    Get configuration value for a given key.

    Args:
        key: Configuration key name
        settings: Settings instance

    Returns:
        Configuration value or None if not set
    """
    # Map environment variable names to settings attributes
    key_mapping = {
        "GMAIL_CREDENTIALS_FILE": "gmail_credentials_path",
        "GMAIL_TOKEN_FILE": "gmail_token_path",
        "GMAIL_BATCH_SIZE": "gmail_batch_size",
        "NOTION_API_KEY": lambda s: s.get_secret_or_env("NOTION_API_KEY"),
        "COLLABIQ_DB_ID": lambda s: s.get_secret_or_env("COLLABIQ_DB_ID"),
        "NOTION_DATABASE_ID_COMPANIES": "notion_database_id_companies",
        "NOTION_DATABASE_ID_COLLABIQ": "notion_database_id_collabiq",
        "DUPLICATE_BEHAVIOR": "duplicate_behavior",
        "GEMINI_API_KEY": lambda s: s.get_secret_or_env("GEMINI_API_KEY"),
        "GEMINI_MODEL": "gemini_model",
        "GEMINI_TIMEOUT_SECONDS": "gemini_timeout_seconds",
        "GEMINI_MAX_RETRIES": "gemini_max_retries",
        "LOG_LEVEL": "log_level",
        "DEBUG": lambda s: os.getenv("DEBUG", "false"),
        "DATA_DIR": "data_dir",
        "LOG_DIR": "log_dir",
        "INFISICAL_ENABLED": "infisical_enabled",
        "INFISICAL_HOST": "infisical_host",
        "INFISICAL_PROJECT_ID": "infisical_project_id",
        "INFISICAL_ENVIRONMENT": "infisical_environment",
        "INFISICAL_CLIENT_ID": "infisical_client_id",
        "INFISICAL_CLIENT_SECRET": "infisical_client_secret",
        "INFISICAL_CACHE_TTL": "infisical_cache_ttl",
    }

    if key not in key_mapping:
        # Try getting from environment as fallback
        return os.getenv(key)

    attr = key_mapping[key]

    # Handle callable attributes (for secrets)
    if callable(attr):
        try:
            return attr(settings)
        except Exception:
            return None

    # Handle regular attributes
    try:
        value = getattr(settings, attr, None)
        return str(value) if value is not None else None
    except Exception:
        return None


def validate_required_settings(settings: Any) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Validate that all required configuration settings are present.

    Args:
        settings: Settings instance

    Returns:
        Tuple of (is_valid, list of validation errors with suggestions)
    """
    errors = []

    # Gmail requirements
    gmail_creds = settings.get_gmail_credentials_path()
    if not gmail_creds.exists():
        errors.append({
            "key": "GMAIL_CREDENTIALS_FILE",
            "issue": f"File not found: {gmail_creds}",
            "fix": "Download OAuth2 credentials from Google Cloud Console",
        })

    # Notion requirements
    notion_key = settings.get_secret_or_env("NOTION_API_KEY")
    if not notion_key:
        errors.append({
            "key": "NOTION_API_KEY",
            "issue": "Not set",
            "fix": "Set NOTION_API_KEY in .env or Infisical",
        })

    collabiq_db = settings.get_secret_or_env("COLLABIQ_DB_ID")
    if not collabiq_db:
        errors.append({
            "key": "COLLABIQ_DB_ID",
            "issue": "Not set",
            "fix": "Set COLLABIQ_DB_ID in .env or Infisical",
        })

    # Gemini requirements
    gemini_key = settings.get_secret_or_env("GEMINI_API_KEY")
    if not gemini_key:
        errors.append({
            "key": "GEMINI_API_KEY",
            "issue": "Not set",
            "fix": "Set GEMINI_API_KEY in .env or Infisical",
        })

    # Infisical validation (if enabled)
    if settings.infisical_enabled:
        if not settings.infisical_project_id:
            errors.append({
                "key": "INFISICAL_PROJECT_ID",
                "issue": "Required when Infisical is enabled",
                "fix": "Set INFISICAL_PROJECT_ID or disable Infisical",
            })

        if not settings.infisical_environment:
            errors.append({
                "key": "INFISICAL_ENVIRONMENT",
                "issue": "Required when Infisical is enabled",
                "fix": "Set INFISICAL_ENVIRONMENT to 'development' or 'production'",
            })

        if not settings.infisical_client_id:
            errors.append({
                "key": "INFISICAL_CLIENT_ID",
                "issue": "Required when Infisical is enabled",
                "fix": "Set INFISICAL_CLIENT_ID from Infisical dashboard",
            })

        if not settings.infisical_client_secret:
            errors.append({
                "key": "INFISICAL_CLIENT_SECRET",
                "issue": "Required when Infisical is enabled",
                "fix": "Set INFISICAL_CLIENT_SECRET from Infisical dashboard",
            })

    return len(errors) == 0, errors


# ==============================================================================
# Commands
# ==============================================================================


@app.command(name="show")
def show_config(
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    ctx: typer.Context = typer.Context,
) -> None:
    """
    Display all configuration values with secrets masked.

    Shows configuration organized by category (Gmail, Notion, Gemini, etc.)
    with source indicators (Infisical/env/default) and automatic secret masking.

    Examples:
        collabiq config show
        collabiq config show --json
    """
    try:
        settings = get_settings()
        categories = categorize_config_keys()

        # Collect all config data
        config_data = {}

        for category, keys in categories.items():
            category_data = []

            for key in keys:
                value = get_config_value(key, settings)

                if value is None:
                    continue

                # Mask secrets
                display_value = mask_secret(value) if is_secret_key(key) else value
                source = get_config_source(key, settings)

                category_data.append({
                    "key": key,
                    "value": display_value,
                    "source": source,
                })

            if category_data:  # Only include categories with values
                config_data[category] = category_data

        if json:
            # JSON output with secret masking
            output_json(
                data={"configuration": config_data},
                status="success",
            )
        else:
            # Interactive table output
            console.print("\n[bold cyan]Configuration Overview[/bold cyan]\n")

            for category, items in config_data.items():
                if not items:
                    continue

                table = create_table(
                    title=f"{category} Configuration",
                    columns=["Key", "Value", "Source"],
                )

                for item in items:
                    table.add_row(
                        item["key"],
                        item["value"],
                        f"[green]{item['source']}[/green]" if item["source"] == "Infisical" else f"[yellow]{item['source']}[/yellow]"
                    )

                render_table(table)
                console.print()

        log_cli_operation("config_show", success=True)

    except Exception as e:
        log_cli_error("config_show", e)
        if json:
            output_json(
                data={},
                status="failure",
                errors=[format_json_error(e)],
            )
        else:
            console.print(f"[red]Error showing configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="validate")
def validate_config(
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    ctx: typer.Context = typer.Context,
) -> None:
    """
    Validate configuration and check for missing required settings.

    Checks all required configuration values and provides fix suggestions
    for any missing or invalid settings.

    Examples:
        collabiq config validate
        collabiq config validate --json
    """
    try:
        settings = get_settings()
        is_valid, errors = validate_required_settings(settings)

        if json:
            if is_valid:
                output_json(
                    data={"validation": "passed", "errors": []},
                    status="success",
                )
            else:
                output_json(
                    data={
                        "validation": "failed",
                        "errors": errors,
                    },
                    status="failure",
                )
        else:
            if is_valid:
                console.print("\n[bold green]✓ Configuration is valid[/bold green]\n")
                console.print("All required settings are present and properly configured.")
            else:
                console.print("\n[bold red]✗ Configuration validation failed[/bold red]\n")

                # Create validation errors table
                table = create_table(
                    title="Validation Errors",
                    columns=["Key", "Issue", "Fix"],
                )

                for error in errors:
                    table.add_row(
                        f"[red]{error['key']}[/red]",
                        error["issue"],
                        f"[yellow]{error['fix']}[/yellow]",
                    )

                render_table(table)
                console.print()

        log_cli_operation("config_validate", success=is_valid)

        if not is_valid:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        log_cli_error("config_validate", e)
        if json:
            output_json(
                data={},
                status="failure",
                errors=[format_json_error(e)],
            )
        else:
            console.print(f"[red]Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="test-secrets")
def test_secrets(
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    ctx: typer.Context = typer.Context,
) -> None:
    """
    Test Infisical connection and secret retrieval.

    Verifies that Infisical is properly configured and can retrieve secrets.
    Falls back to .env if Infisical is disabled.

    Examples:
        collabiq config test-secrets
        collabiq config test-secrets --json
    """
    try:
        settings = get_settings()

        if not settings.infisical_enabled:
            if json:
                output_json(
                    data={
                        "infisical_enabled": False,
                        "message": "Infisical is disabled - using .env file",
                    },
                    status="success",
                )
            else:
                console.print("\n[yellow]Infisical is disabled[/yellow]")
                console.print("Configuration is loaded from .env file")
                console.print("\nTo enable Infisical:")
                console.print("1. Set INFISICAL_ENABLED=true in .env")
                console.print("2. Configure Infisical credentials")

            log_cli_operation("config_test_secrets", success=True, metadata={"source": "env"})
            return

        # Test Infisical connection
        client = settings.infisical_client

        if not client:
            if json:
                output_json(
                    data={},
                    status="failure",
                    errors=[{"error_type": "InfisicalError", "message": "Failed to initialize Infisical client"}],
                )
            else:
                console.print("\n[red]✗ Failed to initialize Infisical client[/red]")
            raise typer.Exit(1)

        # Try to authenticate
        try:
            client.authenticate()
            is_connected = client.is_connected()

            if is_connected:
                # Try to fetch a test secret
                try:
                    test_key = "GEMINI_API_KEY"  # Test with a known secret
                    value = client.get_secret(test_key)

                    if json:
                        output_json(
                            data={
                                "infisical_enabled": True,
                                "connected": True,
                                "test_secret_retrieved": True,
                                "host": settings.infisical_host,
                                "project_id": settings.infisical_project_id,
                                "environment": settings.infisical_environment,
                                "cache_ttl": settings.infisical_cache_ttl,
                            },
                            status="success",
                        )
                    else:
                        console.print("\n[bold green]✓ Infisical connection successful[/bold green]\n")

                        info_table = create_table(
                            title="Infisical Configuration",
                            columns=["Setting", "Value"],
                        )
                        info_table.add_row("Host", settings.infisical_host)
                        info_table.add_row("Project ID", settings.infisical_project_id)
                        info_table.add_row("Environment", settings.infisical_environment)
                        info_table.add_row("Cache TTL", f"{settings.infisical_cache_ttl}s")
                        info_table.add_row("Test Secret", f"{test_key} = {mask_secret(value)}")

                        render_table(info_table)
                        console.print()

                    log_cli_operation("config_test_secrets", success=True, metadata={"source": "infisical"})

                except Exception as e:
                    if json:
                        output_json(
                            data={},
                            status="failure",
                            errors=[{"error_type": "SecretRetrievalError", "message": str(e)}],
                        )
                    else:
                        console.print(f"\n[red]✗ Failed to retrieve test secret: {e}[/red]")
                    raise typer.Exit(1)
            else:
                if json:
                    output_json(
                        data={},
                        status="failure",
                        errors=[{"error_type": "InfisicalConnectionError", "message": "Not connected to Infisical"}],
                    )
                else:
                    console.print("\n[red]✗ Not connected to Infisical[/red]")
                raise typer.Exit(1)

        except Exception as e:
            if json:
                output_json(
                    data={},
                    status="failure",
                    errors=[format_json_error(e)],
                )
            else:
                console.print(f"\n[red]✗ Infisical authentication failed: {e}[/red]")
                console.print("\n[yellow]Remediation:[/yellow]")
                console.print("1. Check INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET")
                console.print("2. Verify machine identity has access to the environment")
                console.print("3. Check network connectivity to Infisical host")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        log_cli_error("config_test_secrets", e)
        if json:
            output_json(
                data={},
                status="failure",
                errors=[format_json_error(e)],
            )
        else:
            console.print(f"[red]Error testing secrets: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="get")
def get_config_key(
    key: str = typer.Argument(..., help="Configuration key to retrieve"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    ctx: typer.Context = typer.Context,
) -> None:
    """
    Get a specific configuration value.

    Retrieves and displays a single configuration value with automatic
    secret masking and source indication.

    Examples:
        collabiq config get GEMINI_API_KEY
        collabiq config get LOG_LEVEL --json
    """
    try:
        settings = get_settings()
        value = get_config_value(key, settings)

        if value is None:
            if json:
                output_json(
                    data={},
                    status="failure",
                    errors=[{"error_type": "ConfigKeyNotFound", "message": f"Configuration key '{key}' not found"}],
                )
            else:
                console.print(f"\n[red]Configuration key '{key}' not found[/red]\n")
            raise typer.Exit(1)

        # Mask if it's a secret
        display_value = mask_secret(value) if is_secret_key(key) else value
        source = get_config_source(key, settings)

        if json:
            output_json(
                data={
                    "key": key,
                    "value": display_value,
                    "source": source,
                    "is_secret": is_secret_key(key),
                },
                status="success",
            )
        else:
            console.print(f"\n[bold]{key}[/bold]")
            console.print(f"Value: [green]{display_value}[/green]")
            console.print(f"Source: [yellow]{source}[/yellow]")
            console.print()

        log_cli_operation("config_get", success=True, metadata={"key": key})

    except typer.Exit:
        raise
    except Exception as e:
        log_cli_error("config_get", e)
        if json:
            output_json(
                data={},
                status="failure",
                errors=[format_json_error(e)],
            )
        else:
            console.print(f"[red]Error getting configuration: {e}[/red]")
        raise typer.Exit(1)
