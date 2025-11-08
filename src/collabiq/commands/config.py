"""
Configuration management commands.

Commands:
- show: Display all configuration (secrets masked)
- validate: Check for missing/invalid settings
- test-secrets: Verify Infisical connectivity
- get: Display specific configuration value

All secrets are automatically masked in output.
"""

import typer

app = typer.Typer(
    name="config",
    help="Configuration management (show, validate, test-secrets, get)",
)

# Commands will be implemented in Phase 10 (User Story 8)
