"""
Testing and validation commands.

Commands:
- e2e: Run end-to-end pipeline tests
- select-emails: Configure test email candidates
- validate: Quick health checks (<10s)
"""

import typer

app = typer.Typer(
    name="test",
    help="Testing and validation (e2e, select-emails, validate)",
)

# Commands will be implemented in Phase 7 (User Story 5)
