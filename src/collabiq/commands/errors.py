"""
Error management and DLQ operations commands.

Commands:
- list: View failed operations
- show: Display error details
- retry: Retry failed operations
- clear: Remove resolved errors
"""

import typer

app = typer.Typer(
    name="errors",
    help="Error management and DLQ operations (list, show, retry, clear)",
)

# Commands will be implemented in Phase 8 (User Story 6)
