"""
CollabIQ CLI - Main package entry point.
"""

# New library modules for testing infrastructure (Phase 015)
# These are standalone libraries per constitution principle I
# Import libraries ONLY - CLI commands are registered lazily to avoid circular imports
from . import date_parser, llm_benchmarking, test_utils


def _register_commands():
    """Lazy registration of CLI commands to avoid circular imports with adapters."""
    # Import the main app instance from the cli module
    from .cli import app

    # Register command subapps
    from .commands.email import email_app
    from .commands.notion import notion_app
    from .commands.test import test_app
    from .commands.errors import errors_app
    from .commands.status import status_app
    from .commands.llm import llm_app
    from .commands.config import config_app

    # Register subcommands with the main app
    app.add_typer(email_app, name="email")
    app.add_typer(notion_app, name="notion")
    app.add_typer(test_app, name="test")
    app.add_typer(errors_app, name="errors")
    app.add_typer(status_app, name="status")
    app.add_typer(llm_app, name="llm")
    app.add_typer(config_app, name="config")

    return app


# Export app via property to trigger lazy registration
def __getattr__(name):
    if name == "app":
        return _register_commands()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
