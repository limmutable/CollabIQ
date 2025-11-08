"""
System health monitoring commands.

Displays overall system health, component status, and metrics.
Supports continuous monitoring with --watch mode.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from collabiq.formatters.colors import console
from collabiq.formatters.json_output import output_json
from collabiq.formatters.tables import create_table
from collabiq.utils.logging import log_cli_operation, log_cli_error

# Import service components for health checks
from email_receiver.gmail_receiver import GmailReceiver
from notion_integrator.integrator import NotionIntegrator
from llm_adapters.gemini_adapter import GeminiAdapter

app = typer.Typer(
    name="status",
    help="System health monitoring",
    invoke_without_command=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed metrics and extended information"),
    watch: bool = typer.Option(False, "--watch", help="Monitor system health in real-time (30s refresh)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON for automation"),
) -> None:
    """
    Display system health status and component information.

    Shows overall health (healthy/degraded/critical) and status for all components
    (Gmail, Notion, Gemini). Performs parallel health checks for performance.

    Examples:
        # Basic status
        collabiq status

        # Detailed status with metrics
        collabiq status --detailed

        # Real-time monitoring
        collabiq status --watch

        # JSON output for automation
        collabiq status --json
    """
    # Only run status check if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    debug = ctx.obj.get("debug", False) if ctx.obj else False

    try:
        if watch:
            # Watch mode (T102) - continuous monitoring with 30s refresh
            _run_watch_mode(detailed=detailed, json_output=json_output, debug=debug)
        else:
            # Single health check
            health = asyncio.run(run_health_checks())

            if json_output:
                # JSON output (T106)
                output_json(
                    data=health.to_dict(),
                    status="success",
                )
            else:
                # Table output
                if detailed:
                    render_detailed_status(health)
                else:
                    render_basic_status(health)

            # Log operation
            if debug:
                log_cli_operation(
                    "status_check",
                    success=True,
                    debug=True,
                    overall_status=health.overall_status,
                )

            # Exit with non-zero code if system is critical
            if health.overall_status == "critical":
                raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Status check interrupted[/yellow]")
        raise typer.Exit(0)

    except Exception as e:
        if debug:
            log_cli_error("status_check", e)

        if json_output:
            from collabiq.formatters.json_output import format_json_error
            output_json(
                data={},
                status="failure",
                errors=[format_json_error(e, "status_check")],
            )
        else:
            console.print(f"[red]Error checking system health: {str(e)}[/red]")

        raise typer.Exit(1)


# ==============================================================================
# Data Models and Types
# ==============================================================================


class ComponentStatus:
    """Status information for a single component."""

    def __init__(
        self,
        name: str,
        status: str,  # "online", "degraded", "offline"
        message: str,
        response_time_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        remediation: Optional[List[str]] = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.remediation = remediation or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
            "remediation": self.remediation if self.status != "online" else [],
        }


class SystemHealth:
    """Overall system health status."""

    def __init__(self, components: List[ComponentStatus]):
        self.components = components
        self.timestamp = datetime.now()
        self.overall_status = self._calculate_overall_status()

    def _calculate_overall_status(self) -> str:
        """Calculate overall system health (T103)."""
        statuses = [c.status for c in self.components]

        # Critical: Any component offline
        if "offline" in statuses:
            return "critical"

        # Degraded: Any component degraded
        if "degraded" in statuses:
            return "degraded"

        # Healthy: All components online
        return "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output (T106)."""
        return {
            "overall_status": self.overall_status,
            "timestamp": self.timestamp.isoformat(),
            "components": [c.to_dict() for c in self.components],
        }


# ==============================================================================
# Health Check Functions (T099 - Parallel Async Checks)
# ==============================================================================


async def check_gmail_health() -> ComponentStatus:
    """
    Check Gmail API connectivity and health.

    Returns:
        ComponentStatus for Gmail
    """
    start_time = time.time()

    try:
        # Get configuration
        credentials_path = Path(os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
        token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "token.json"))

        if not credentials_path.exists():
            return ComponentStatus(
                name="Gmail",
                status="offline",
                message="Credentials file not found",
                response_time_ms=None,
                remediation=[
                    "Ensure GMAIL_CREDENTIALS_PATH is set correctly",
                    "Download credentials from Google Cloud Console",
                    "Place credentials.json in project root",
                ]
            )

        # Try to connect (run in thread pool since it's sync)
        loop = asyncio.get_event_loop()

        def _connect():
            receiver = GmailReceiver(
                credentials_path=credentials_path,
                token_path=token_path,
            )
            receiver.connect()
            return receiver

        receiver = await loop.run_in_executor(None, _connect)

        response_time = (time.time() - start_time) * 1000

        return ComponentStatus(
            name="Gmail",
            status="online",
            message="Connected successfully",
            response_time_ms=response_time,
            details={
                "credentials_path": str(credentials_path),
                "token_path": str(token_path),
            }
        )

    except FileNotFoundError as e:
        return ComponentStatus(
            name="Gmail",
            status="offline",
            message=f"File not found: {str(e)}",
            response_time_ms=None,
            remediation=[
                "Check GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH",
                "Run Gmail authentication flow",
                "Verify file permissions",
            ]
        )
    except Exception as e:
        error_msg = str(e)
        response_time = (time.time() - start_time) * 1000

        # Determine if degraded or offline
        status = "degraded" if "rate limit" in error_msg.lower() or "quota" in error_msg.lower() else "offline"

        remediation = []
        if "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
            remediation = [
                "Re-authenticate with Gmail (run: collabiq email verify)",
                "Check credentials.json is valid",
                "Verify OAuth2 permissions",
            ]
        elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            remediation = [
                "Wait for rate limit to reset",
                "Check Google Cloud Console quota limits",
                "Consider increasing API quota",
            ]
        else:
            remediation = [
                "Check network connectivity",
                "Verify Gmail API is enabled in Google Cloud Console",
                "Try again with --debug flag for details",
            ]

        return ComponentStatus(
            name="Gmail",
            status=status,
            message=f"Error: {error_msg}",
            response_time_ms=response_time,
            remediation=remediation,
        )


async def check_notion_health() -> ComponentStatus:
    """
    Check Notion API connectivity and health.

    Returns:
        ComponentStatus for Notion
    """
    start_time = time.time()

    try:
        # Get configuration
        api_key = os.getenv("NOTION_API_KEY")
        collabiq_db_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")

        if not api_key:
            return ComponentStatus(
                name="Notion",
                status="offline",
                message="NOTION_API_KEY not configured",
                response_time_ms=None,
                remediation=[
                    "Set NOTION_API_KEY environment variable",
                    "Or configure Infisical secrets",
                    "Get API key from Notion integrations page",
                ]
            )

        if not collabiq_db_id:
            return ComponentStatus(
                name="Notion",
                status="degraded",
                message="NOTION_DATABASE_ID_COLLABIQ not configured",
                response_time_ms=None,
                remediation=[
                    "Set NOTION_DATABASE_ID_COLLABIQ environment variable",
                    "Get database ID from Notion database URL",
                ]
            )

        # Initialize integrator and test connection
        integrator = NotionIntegrator(api_key=api_key)

        # Test by attempting to retrieve database schema
        try:
            schema = await integrator.discover_database_schema(database_id=collabiq_db_id)
            response_time = (time.time() - start_time) * 1000

            return ComponentStatus(
                name="Notion",
                status="online",
                message="Connected successfully",
                response_time_ms=response_time,
                details={
                    "database_id": collabiq_db_id[:8] + "...",
                    "properties_count": len(schema.database.properties) if schema else 0,
                }
            )
        except Exception as e:
            error_msg = str(e)
            response_time = (time.time() - start_time) * 1000

            # Determine status based on error type
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                status = "offline"
                remediation = [
                    "Check NOTION_API_KEY is valid",
                    "Verify API key has not expired",
                    "Run: collabiq config show (to check configuration)",
                ]
            elif "not found" in error_msg.lower():
                status = "degraded"
                remediation = [
                    "Check NOTION_DATABASE_ID_COLLABIQ is correct",
                    "Verify database exists and is accessible",
                    "Ensure integration has access to the database",
                ]
            elif "rate limit" in error_msg.lower():
                status = "degraded"
                remediation = [
                    "Wait for rate limit to reset",
                    "Notion rate limit: 3 requests/second",
                    "Try again in a few moments",
                ]
            else:
                status = "degraded"
                remediation = [
                    "Check network connectivity",
                    "Verify Notion API status (status.notion.so)",
                    "Try again with --debug flag for details",
                ]

            return ComponentStatus(
                name="Notion",
                status=status,
                message=f"Error: {error_msg}",
                response_time_ms=response_time,
                remediation=remediation,
            )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentStatus(
            name="Notion",
            status="offline",
            message=f"Unexpected error: {str(e)}",
            response_time_ms=response_time,
            remediation=[
                "Check Notion configuration",
                "Run: collabiq notion verify",
                "Try again with --debug flag for details",
            ]
        )


async def check_gemini_health() -> ComponentStatus:
    """
    Check Gemini API connectivity and health.

    Returns:
        ComponentStatus for Gemini
    """
    start_time = time.time()

    try:
        # Get configuration
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            return ComponentStatus(
                name="Gemini",
                status="offline",
                message="GEMINI_API_KEY not configured",
                response_time_ms=None,
                remediation=[
                    "Set GEMINI_API_KEY environment variable",
                    "Or configure Infisical secrets",
                    "Get API key from Google AI Studio",
                ]
            )

        # Initialize adapter and test with minimal request
        adapter = GeminiAdapter(api_key=api_key)

        # Test by extracting from a minimal test string
        try:
            # This is a quick test - we just want to see if API is accessible
            test_email = "Test email for health check"
            result = adapter.extract_entities(test_email)

            response_time = (time.time() - start_time) * 1000

            return ComponentStatus(
                name="Gemini",
                status="online",
                message="Connected successfully",
                response_time_ms=response_time,
                details={
                    "model": adapter.model,
                }
            )
        except Exception as e:
            error_msg = str(e)
            response_time = (time.time() - start_time) * 1000

            # Determine status based on error type
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                status = "offline"
                remediation = [
                    "Check GEMINI_API_KEY is valid",
                    "Get new API key from Google AI Studio",
                    "Verify API key format (starts with 'AIza')",
                ]
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                status = "degraded"
                remediation = [
                    "Wait for rate limit to reset",
                    "Check Google AI Studio quota limits",
                    "Consider upgrading API tier",
                ]
            elif "timeout" in error_msg.lower():
                status = "degraded"
                remediation = [
                    "Check network connectivity",
                    "Gemini API may be experiencing delays",
                    "Try again in a few moments",
                ]
            else:
                status = "degraded"
                remediation = [
                    "Check network connectivity",
                    "Verify Gemini API availability",
                    "Try again with --debug flag for details",
                ]

            return ComponentStatus(
                name="Gemini",
                status=status,
                message=f"Error: {error_msg}",
                response_time_ms=response_time,
                remediation=remediation,
            )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ComponentStatus(
            name="Gemini",
            status="offline",
            message=f"Unexpected error: {str(e)}",
            response_time_ms=response_time,
            remediation=[
                "Check Gemini configuration",
                "Run: collabiq llm test gemini",
                "Try again with --debug flag for details",
            ]
        )


async def run_health_checks() -> SystemHealth:
    """
    Run all health checks in parallel (T099, T107).

    Returns:
        SystemHealth with all component statuses
    """
    # Run all checks concurrently for performance
    results = await asyncio.gather(
        check_gmail_health(),
        check_notion_health(),
        check_gemini_health(),
        return_exceptions=True,
    )

    # Convert any exceptions to error status
    components = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            component_names = ["Gmail", "Notion", "Gemini"]
            components.append(ComponentStatus(
                name=component_names[i],
                status="offline",
                message=f"Health check failed: {str(result)}",
                response_time_ms=None,
                remediation=["Unexpected error during health check", "Contact support if issue persists"]
            ))
        else:
            components.append(result)

    return SystemHealth(components=components)


# ==============================================================================
# Display Functions (T104 - Component Status Highlighting)
# ==============================================================================


def get_status_color(status: str) -> str:
    """Get Rich color markup for status (T104)."""
    colors = {
        "online": "green",
        "degraded": "yellow",
        "offline": "red",
        "healthy": "green",
        "critical": "red",
    }
    return colors.get(status, "white")


def render_basic_status(health: SystemHealth) -> None:
    """
    Render basic status table (T100).

    Args:
        health: SystemHealth object with component statuses
    """
    # Overall health panel
    overall_color = get_status_color(health.overall_status)
    overall_text = health.overall_status.upper()

    console.print()
    console.print(
        Panel(
            f"[{overall_color} bold]{overall_text}[/{overall_color} bold]",
            title="System Health",
            border_style=overall_color,
        )
    )

    # Component status table
    table = create_table(
        title="Component Status",
        columns=[
            {"name": "Component", "style": "cyan", "no_wrap": True},
            {"name": "Status", "justify": "center"},
            {"name": "Message", "style": "white"},
        ],
    )

    for component in health.components:
        status_color = get_status_color(component.status)
        status_text = f"[{status_color}]{component.status.upper()}[/{status_color}]"

        table.add_row(
            component.name,
            status_text,
            component.message,
        )

    console.print(table)
    console.print(f"\n[dim]Last checked: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    # Show remediation for degraded/offline components (T105)
    degraded_components = [c for c in health.components if c.status in ["degraded", "offline"]]
    if degraded_components:
        console.print()
        for component in degraded_components:
            if component.remediation:
                console.print(f"[yellow]Remediation for {component.name}:[/yellow]")
                for i, suggestion in enumerate(component.remediation, 1):
                    console.print(f"  {i}. {suggestion}")
                console.print()


def render_detailed_status(health: SystemHealth) -> None:
    """
    Render detailed status with extended metrics (T101).

    Args:
        health: SystemHealth object with component statuses
    """
    # Overall health panel
    overall_color = get_status_color(health.overall_status)
    overall_text = health.overall_status.upper()

    console.print()
    console.print(
        Panel(
            f"[{overall_color} bold]{overall_text}[/{overall_color} bold]",
            title="System Health",
            border_style=overall_color,
        )
    )

    # Detailed component status table
    table = create_table(
        title="Detailed Component Status",
        columns=[
            {"name": "Component", "style": "cyan", "no_wrap": True},
            {"name": "Status", "justify": "center"},
            {"name": "Response Time", "justify": "right"},
            {"name": "Message", "style": "white"},
        ],
    )

    for component in health.components:
        status_color = get_status_color(component.status)
        status_text = f"[{status_color}]{component.status.upper()}[/{status_color}]"

        response_time = (
            f"{component.response_time_ms:.1f}ms"
            if component.response_time_ms is not None
            else "N/A"
        )

        table.add_row(
            component.name,
            status_text,
            response_time,
            component.message,
        )

    console.print(table)

    # Show detailed information for each component
    console.print("\n[bold]Component Details:[/bold]")
    for component in health.components:
        console.print(f"\n[cyan]{component.name}:[/cyan]")
        console.print(f"  Status: [{get_status_color(component.status)}]{component.status}[/{get_status_color(component.status)}]")
        console.print(f"  Message: {component.message}")

        if component.response_time_ms is not None:
            console.print(f"  Response Time: {component.response_time_ms:.1f}ms")

        if component.details:
            console.print("  Details:")
            for key, value in component.details.items():
                console.print(f"    - {key}: {value}")

        if component.remediation and component.status in ["degraded", "offline"]:
            console.print("  [yellow]Remediation:[/yellow]")
            for i, suggestion in enumerate(component.remediation, 1):
                console.print(f"    {i}. {suggestion}")

    console.print(f"\n[dim]Last checked: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


# ==============================================================================
# Command Implementations
# ==============================================================================


def _run_watch_mode(detailed: bool, json_output: bool, debug: bool) -> None:
    """
    Run status in watch mode with 30-second refresh (T102).

    Args:
        detailed: Whether to show detailed status
        json_output: Whether to output JSON
        debug: Debug mode flag
    """
    if json_output:
        console.print("[yellow]Watch mode not supported with --json flag[/yellow]")
        console.print("[dim]Falling back to single status check[/dim]")
        health = asyncio.run(run_health_checks())
        output_json(data=health.to_dict(), status="success")
        return

    console.print("[cyan]Starting real-time monitoring (30s refresh)[/cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")

    try:
        iteration = 0
        while True:
            # Clear screen for clean display (but show iteration count)
            if iteration > 0:
                console.print("\n" + "=" * 80 + "\n")

            console.print(f"[dim]Refresh #{iteration + 1} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

            # Run health check
            health = asyncio.run(run_health_checks())

            # Display status
            if detailed:
                render_detailed_status(health)
            else:
                render_basic_status(health)

            iteration += 1

            # Show next refresh countdown
            console.print(f"\n[dim]Next refresh in 30 seconds... (Press Ctrl+C to exit)[/dim]")

            # Wait 30 seconds
            time.sleep(30)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Monitoring stopped[/yellow]")
        raise typer.Exit(0)
