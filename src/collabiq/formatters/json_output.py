"""
JSON output formatting for CLI automation.

Provides consistent JSON output structure for all commands
when --json flag is used.
"""

import json
from typing import Any, Dict, List, Optional
from .colors import get_console


def output_json(
    data: Any,
    status: str = "success",
    errors: Optional[List[str]] = None,
    indent: int = 2,
) -> None:
    """
    Output data as formatted JSON to stdout.

    Args:
        data: Data to output (will be placed in 'data' field)
        status: Status string ('success' or 'failure')
        errors: Optional list of error messages
        indent: JSON indentation level (default: 2)

    Output format:
        {
            "status": "success" | "failure",
            "data": <data>,
            "errors": [<error messages>]
        }

    Example:
        output_json(
            data={"count": 10, "emails": [...]},
            status="success",
            errors=[]
        )
    """
    console = get_console()
    output = {
        "status": status,
        "data": data if data is not None else {},
        "errors": errors if errors is not None else [],
    }

    # Use console.print to respect NO_COLOR setting
    # but output raw JSON (no Rich formatting)
    json_str = json.dumps(output, indent=indent, ensure_ascii=False)
    console.print(json_str, markup=False, highlight=False)


def format_json_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    Format an exception as JSON error structure.

    Args:
        error: Exception to format
        context: Optional context string (e.g., "email_fetch")

    Returns:
        Dictionary with error details
    """
    return {
        "error_type": type(error).__name__,
        "message": str(error),
        "context": context,
    }
