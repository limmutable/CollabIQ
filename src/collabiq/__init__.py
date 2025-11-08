"""
CollabIQ CLI - Unified command interface for all operations.

This is the main entry point for the CollabIQ admin CLI.
All commands are organized into logical groups:
- email: Email pipeline operations
- notion: Notion integration management
- test: E2E testing and validation
- errors: Error management and DLQ operations
- status: System health monitoring
- llm: LLM provider management
- config: Configuration management
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import formatters and utilities
from collabiq.formatters.colors import console, disable_colors
from collabiq.utils.logging import setup_cli_logging, log_cli_operation

# Import command groups
from collabiq.commands import email, notion, test, errors, status, llm, config

# Create main app
app = typer.Typer(
    name="collabiq",
    help="CollabIQ Admin CLI - Unified command interface for all operations",
    add_completion=False,  # No shell completion for MVP (simplicity)
    no_args_is_help=True,
)

# Global state for options (stored in context)
# This will be accessed by subcommands via ctx.obj


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-error output"),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable color output (also honors NO_COLOR env var)"
    ),
) -> None:
    """
    CollabIQ Admin CLI - Unified command interface for all operations.

    Use --help with any command to see detailed usage information and examples.
    """
    # Store global options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color

    # Setup logging based on debug flag
    if debug:
        setup_cli_logging(debug=True)
        log_cli_operation("cli_start", success=True, debug=True)

    # Disable colors if requested or NO_COLOR environment variable set
    if no_color or os.getenv("NO_COLOR"):
        disable_colors()


# Register command groups
app.add_typer(email.app, name="email", help="Email pipeline operations")
app.add_typer(notion.app, name="notion", help="Notion integration management")
app.add_typer(test.app, name="test", help="Testing and validation")
app.add_typer(errors.app, name="errors", help="Error management and DLQ operations")
app.add_typer(status.app, name="status", help="System health monitoring")
app.add_typer(llm.app, name="llm", help="LLM provider management")
app.add_typer(config.app, name="config", help="Configuration management")


# Main entry point when run as a script
if __name__ == "__main__":
    app()
