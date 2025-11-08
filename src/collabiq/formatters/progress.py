"""
Progress indicator utilities using Rich.

Provides helpers for creating progress bars, spinners, and ETA displays
for long-running CLI operations.
"""

from typing import Optional
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)


def create_progress(show_percentage: bool = True, show_time: bool = True) -> Progress:
    """
    Create a Rich Progress instance with standard columns.

    Args:
        show_percentage: Include percentage completion
        show_time: Include time remaining estimate

    Returns:
        Configured Progress instance

    Example:
        with create_progress() as progress:
            task = progress.add_task("Processing emails...", total=100)
            for i in range(100):
                # ... do work
                progress.update(task, advance=1)
    """
    columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
    ]

    if show_percentage:
        columns.append(TaskProgressColumn())

    if show_time:
        columns.append(TimeRemainingColumn())

    return Progress(*columns)


def create_spinner(text: str = "Working...") -> Progress:
    """
    Create a spinner progress indicator for indeterminate operations.

    Args:
        text: Text to display next to spinner

    Returns:
        Progress instance with spinner

    Example:
        with create_spinner("Fetching emails...") as progress:
            task = progress.add_task("", total=None)
            # ... do work
            progress.update(task, description="✓ Fetched 10 emails")
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    )
