"""
CLI output formatters for CollabIQ.

This module provides consistent formatting utilities for:
- Tables (Rich table helpers)
- Progress indicators (spinners, bars, ETA)
- Color-coded output (with NO_COLOR support)
- JSON output (structured data for automation)
"""

from .tables import create_table, render_table
from .progress import create_progress, create_spinner
from .colors import get_console, disable_colors
from .json_output import output_json

__all__ = [
    "create_table",
    "render_table",
    "create_progress",
    "create_spinner",
    "get_console",
    "disable_colors",
    "output_json",
]
