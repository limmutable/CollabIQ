"""
Notion integration management commands.

Commands:
- verify: Check Notion connection and schema
- schema: Display database schema
- test-write: Create and cleanup test entry
- cleanup-tests: Remove all test entries
"""

import typer

app = typer.Typer(
    name="notion",
    help="Notion integration management (verify, schema, test-write, cleanup-tests)",
)

# Commands will be implemented in Phase 5 (User Story 3)
