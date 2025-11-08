"""
Table formatting utilities using Rich.

Provides helpers for creating and rendering formatted tables
with automatic column alignment and consistent styling.
"""

from typing import Any, Dict, List, Optional
from rich.table import Table
from rich.console import Console


def create_table(
    title: Optional[str] = None,
    columns: Optional[List[Dict[str, Any]]] = None,
    show_header: bool = True,
    show_lines: bool = False,
) -> Table:
    """
    Create a Rich table with specified columns.

    Args:
        title: Optional table title
        columns: List of column definitions with 'name', 'style', 'justify' keys
        show_header: Whether to show column headers
        show_lines: Whether to show lines between rows

    Returns:
        Configured Rich Table instance

    Example:
        table = create_table(
            title="Email List",
            columns=[
                {"name": "ID", "style": "cyan"},
                {"name": "Sender", "style": "magenta"},
                {"name": "Subject", "style": "green"},
                {"name": "Status", "justify": "right"},
            ]
        )
    """
    table = Table(title=title, show_header=show_header, show_lines=show_lines)

    if columns:
        for col in columns:
            table.add_column(
                col.get("name", ""),
                style=col.get("style"),
                justify=col.get("justify", "left"),
                no_wrap=col.get("no_wrap", False),
            )

    return table


def render_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, Any]],
    title: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """
    Create and render a table with data.

    Args:
        data: List of dictionaries with row data
        columns: Column definitions (name, style, justify, field)
        title: Optional table title
        console: Rich Console instance (uses default if not provided)

    Example:
        render_table(
            data=[
                {"id": "email001", "sender": "alice@example.com", "status": "written"},
                {"id": "email002", "sender": "bob@company.org", "status": "extracted"},
            ],
            columns=[
                {"name": "ID", "field": "id", "style": "cyan"},
                {"name": "Sender", "field": "sender", "style": "magenta"},
                {"name": "Status", "field": "status", "justify": "right"},
            ],
            title="Recent Emails"
        )
    """
    if console is None:
        from .colors import console as default_console

        console = default_console

    table = create_table(title=title, columns=columns)

    for row in data:
        table.add_row(*[str(row.get(col.get("field", col["name"]), "")) for col in columns])

    console.print(table)
