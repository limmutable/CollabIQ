"""
Central CLI application definition for CollabIQ.

This file creates the main Typer application instance and defines the root callback.
Command modules import the `app` object from this file.
"""

import os
import typer
import logging # Import logging module for basicConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure basic logging early for debug visibility
# This ensures debug messages from module-level loggers are visible immediately
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import formatters and utilities
from collabiq.formatters.colors import disable_colors
from collabiq.utils.logging import setup_cli_logging, log_cli_operation # setup_cli_logging will reconfigure later if debug=True is passed

# Create main app instance
app = typer.Typer(
    name="collabiq",
    help="CollabIQ Admin CLI - Unified command interface for all operations",
    add_completion=False,
    no_args_is_help=True,
)

# Register command groups
from collabiq.commands import config_app
from collabiq.commands.email import email_app
from collabiq.commands.run import run
from collabiq.commands.test import test_app

app.add_typer(config_app, name="config")
app.add_typer(email_app, name="email")
app.add_typer(test_app, name="test")
app.command()(run)


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
