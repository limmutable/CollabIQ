"""
Central CLI application definition for CollabIQ.

This file creates the main Typer application instance and defines the root callback.
Command modules import the `app` object from this file.
"""

import os
import typer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import formatters and utilities
from collabiq.formatters.colors import disable_colors
from collabiq.utils.logging import setup_cli_logging, log_cli_operation

# Create main app instance
app = typer.Typer(
    name="collabiq",
    help="CollabIQ Admin CLI - Unified command interface for all operations",
    add_completion=False,
    no_args_is_help=True,
)

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
    """
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color

    if debug:
        setup_cli_logging(debug=True)
        log_cli_operation("cli_start", success=True, debug=True)

    if no_color or os.getenv("NO_COLOR"):
        disable_colors()
