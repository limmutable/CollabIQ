"""
Email pipeline management commands.

Commands:
- fetch: Download emails from Gmail
- clean: Normalize email content
- list: Display recent emails
- verify: Check Gmail connectivity
- process: Run complete pipeline
"""

import typer

app = typer.Typer(
    name="email",
    help="Email pipeline operations (fetch, clean, list, verify, process)",
)

# Commands will be implemented in Phase 4 (User Story 2)
