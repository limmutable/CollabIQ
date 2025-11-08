"""
Color output handling with NO_COLOR support.

Manages Rich Console instance and handles color disabling
based on environment variables or flags.
"""

import os
from rich.console import Console

# Global console instance
# Automatically respects NO_COLOR environment variable
_console: Console = Console()


def get_console(force_color: bool = False, force_no_color: bool = False) -> Console:
    """
    Get or create a Console instance with specified color settings.

    Args:
        force_color: Force colors even if NO_COLOR is set
        force_no_color: Disable colors even if not in NO_COLOR mode

    Returns:
        Console instance with appropriate color settings
    """
    global _console

    if force_no_color or os.getenv("NO_COLOR"):
        return Console(force_terminal=False, no_color=True)
    elif force_color:
        return Console(force_terminal=True, force_interactive=True)
    else:
        return _console


def disable_colors() -> None:
    """
    Disable colors globally by setting NO_COLOR environment variable.

    This affects all Rich output for the remainder of the program.
    """
    os.environ["NO_COLOR"] = "1"
    global _console
    _console = Console(force_terminal=False, no_color=True)


# Export default console for convenience
console = _console
