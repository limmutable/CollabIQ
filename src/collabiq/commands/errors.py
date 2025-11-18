"""
Error management and DLQ operations commands.

Commands:
- list: View failed operations
- show: Display error details
- retry: Retry failed operations
- clear: Remove resolved errors
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..formatters.progress import create_progress
from ..formatters.json_output import output_json
from ..formatters.tables import create_table
from ..utils.logging import log_cli_operation, log_cli_error

# Import DLQ manager
try:
    from notion_integrator.dlq_manager import DLQManager
    from llm_provider.types import DLQEntry
except ImportError:
    DLQManager = None
    DLQEntry = None

errors_app = typer.Typer(
    name="errors",
    help="Error management and DLQ operations (list, show, retry, clear)",
)

# Default paths
DLQ_DIR = Path("data/dlq")


def _get_severity_from_error(error_details: dict) -> str:
    """Determine severity level from error details."""
    error_type = error_details.get("error_type", "")
    status_code = error_details.get("status_code")

    # Network/connection errors are warnings (retryable)
    if "Connection" in error_type or "Timeout" in error_type:
        return "warning"

    # 4xx errors are errors (client-side issues)
    if status_code and 400 <= status_code < 500:
        return "error"

    # 5xx errors are warnings (server-side, retryable)
    if status_code and status_code >= 500:
        return "warning"

    # Default to error
    return "error"


def _get_remediation_suggestion(error_details: dict) -> str:
    """Get remediation suggestion based on error type."""
    error_type = error_details.get("error_type", "")
    error_message = error_details.get("error_message", "")
    status_code = error_details.get("status_code")

    # Connection errors
    if "Connection" in error_type or "Timeout" in error_type:
        return "Check network connectivity and Notion API status. Retry with `collabiq errors retry --id <error-id>`"

    # Rate limiting (429)
    if status_code == 429:
        return "Notion API rate limit reached. Wait a few minutes and retry with `collabiq errors retry --id <error-id>`"

    # Validation errors (400)
    if status_code == 400:
        return "Invalid data format. Review the extracted data and ensure it matches Notion database schema. May require manual intervention."

    # Unauthorized (401)
    if status_code == 401:
        return "Invalid Notion API token. Update credentials with `collabiq config validate` or check Infisical secrets."

    # Not found (404)
    if status_code == 404:
        return "Notion database not found. Verify NOTION_DATABASE_ID in configuration."

    # Property validation errors
    if "property" in error_message.lower() or "schema" in error_message.lower():
        return "Property mismatch with Notion schema. Check database schema with `collabiq notion schema`"

    # Default
    return "Review error details below and retry with `collabiq errors retry --id <error-id>` if appropriate."


@errors_app.command()
def list(
    severity: Optional[str] = typer.Option(
        None, help="Filter by severity (error, warning, info)"
    ),
    since: Optional[str] = typer.Option(
        None, help="Show errors since date (YYYY-MM-DD)"
    ),
    limit: int = typer.Option(20, help="Maximum number of errors to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    quiet: bool = typer.Option(False, help="Suppress non-error output"),
):
    """
    List failed operations in the DLQ with filtering options.

    Shows error ID, email ID, error type, timestamp, retry count, and severity.
    Use --severity to filter by error level, --since for date filtering.

    Examples:
        collabiq errors list --limit 10
        collabiq errors list --severity error
        collabiq errors list --since 2024-01-01
        collabiq errors list --json
    """
    console = Console()  # Initialize Console locally

    try:
        # Validate service availability
        if DLQManager is None:
            raise RuntimeError(
                "DLQ manager not available. Ensure notion_integrator module is installed."
            )

        # Initialize DLQ manager
        dlq_manager = DLQManager(dlq_dir=str(DLQ_DIR))

        # Load all DLQ entries
        dlq_files = dlq_manager.list_dlq_entries()

        if not dlq_files:
            if json_output:
                output_json(data={"errors": [], "count": 0}, status="success")
            elif not quiet:
                console.print("[green]✓ No errors found in DLQ[/green]")
            return

        # Parse entries with filtering
        errors = []
        since_date = None
        if since:
            try:
                since_date = datetime.fromisoformat(since)
            except ValueError:
                raise ValueError(f"Invalid date format: {since}. Use YYYY-MM-DD")

        for file_path in dlq_files:
            try:
                entry = dlq_manager.load_dlq_entry(file_path)

                # Apply filters
                entry_severity = _get_severity_from_error(entry.error)
                if severity and entry_severity != severity:
                    continue

                if since_date and entry.failed_at < since_date:
                    continue

                # Extract error ID from filename
                error_id = Path(file_path).stem

                errors.append(
                    {
                        "error_id": error_id,
                        "email_id": entry.email_id,
                        "error_type": entry.error.get("error_type", "Unknown"),
                        "error_message": entry.error.get("error_message", ""),
                        "failed_at": entry.failed_at.isoformat(),
                        "retry_count": entry.retry_count,
                        "severity": entry_severity,
                        "file_path": file_path,
                    }
                )
            except Exception as e:
                log_cli_error(f"Failed to load DLQ entry {file_path}: {e}")
                continue

        # Sort by timestamp (newest first) and limit
        errors.sort(key=lambda x: x["failed_at"], reverse=True)
        errors = errors[:limit]

        # Output
        if json_output:
            output_json(
                data={"errors": errors, "count": len(errors), "total": len(dlq_files)},
                status="success",
            )
        else:
            # Create table
            table = create_table(
                title=f"Failed Operations (DLQ) - Showing {len(errors)} of {len(dlq_files)}",
                columns=[
                    {
                        "name": "Error ID",
                        "field": "error_id",
                        "style": "cyan",
                        "no_wrap": True,
                    },
                    {
                        "name": "Email ID",
                        "field": "email_id",
                        "style": "magenta",
                        "no_wrap": True,
                    },
                    {"name": "Error Type", "field": "error_type", "style": "red"},
                    {
                        "name": "Failed At",
                        "field": "failed_at_short",
                        "style": "yellow",
                    },
                    {"name": "Retries", "field": "retry_count", "justify": "right"},
                    {
                        "name": "Severity",
                        "field": "severity_colored",
                        "justify": "center",
                    },
                ],
            )

            for error in errors:
                # Format timestamp
                failed_dt = datetime.fromisoformat(error["failed_at"])
                error["failed_at_short"] = failed_dt.strftime("%Y-%m-%d %H:%M")

                # Color-code severity
                sev = error["severity"]
                if sev == "error":
                    error["severity_colored"] = "[red]ERROR[/red]"
                elif sev == "warning":
                    error["severity_colored"] = "[yellow]WARNING[/yellow]"
                else:
                    error["severity_colored"] = "[blue]INFO[/blue]"

                table.add_row(
                    error["error_id"],
                    error["email_id"],
                    error["error_type"],
                    error["failed_at_short"],
                    str(error["retry_count"]),
                    error["severity_colored"],
                )

            console.print(table)

            if not quiet:
                console.print(
                    "\n[dim]Use 'collabiq errors show <error-id>' to view full details[/dim]"
                )

        log_cli_operation(
            "errors_list",
            {"count": len(errors), "filtered": len(errors) < len(dlq_files)},
        )

    except Exception as e:
        log_cli_error(f"Error listing DLQ entries: {e}")
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ Error listing DLQ entries: {e}[/red]")
        raise typer.Exit(1)


@errors_app.command()
def show(
    error_id: str = typer.Argument(..., help="Error ID to display"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Display full details for a specific error with remediation suggestions.

    Shows complete error information including error type, message, stack trace,
    extracted data, retry count, and suggested remediation steps.

    Examples:
        collabiq errors show email001_20240101_120000
        collabiq errors show email001_20240101_120000 --json
    """
    console = Console()  # Initialize Console locally

    try:
        # Validate service availability
        if DLQManager is None:
            raise RuntimeError(
                "DLQ manager not available. Ensure notion_integrator module is installed."
            )

        # Initialize DLQ manager
        dlq_manager = DLQManager(dlq_dir=str(DLQ_DIR))

        # Find matching file
        file_path = DLQ_DIR / f"{error_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Error ID not found: {error_id}")

        # Load entry
        entry = dlq_manager.load_dlq_entry(str(file_path))

        # Get severity and remediation
        severity = _get_severity_from_error(entry.error)
        remediation = _get_remediation_suggestion(entry.error)

        # Output
        if json_output:
            output_json(
                data={
                    "error_id": error_id,
                    "email_id": entry.email_id,
                    "failed_at": entry.failed_at.isoformat(),
                    "retry_count": entry.retry_count,
                    "severity": severity,
                    "error": entry.error,
                    "extracted_data": entry.extracted_data.model_dump()
                    if entry.extracted_data
                    else None,
                    "remediation": remediation,
                },
                status="success",
            )
        else:
            # Create detailed display
            console.print(f"\n[bold cyan]Error Details: {error_id}[/bold cyan]\n")

            # Basic info
            console.print(f"[bold]Email ID:[/bold] {entry.email_id}")
            console.print(
                f"[bold]Failed At:[/bold] {entry.failed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            console.print(f"[bold]Retry Count:[/bold] {entry.retry_count}")

            # Severity
            sev_color = (
                "red"
                if severity == "error"
                else "yellow"
                if severity == "warning"
                else "blue"
            )
            console.print(
                f"[bold]Severity:[/bold] [{sev_color}]{severity.upper()}[/{sev_color}]"
            )

            # Error details
            console.print("\n[bold red]Error Information:[/bold red]")
            console.print(f"  Type: {entry.error.get('error_type', 'Unknown')}")
            console.print(
                f"  Message: {entry.error.get('error_message', 'No message')}"
            )

            if entry.error.get("status_code"):
                console.print(f"  Status Code: {entry.error['status_code']}")

            # Remediation suggestion
            panel = Panel(
                remediation,
                title="[bold green]Remediation Suggestion[/bold green]",
                border_style="green",
            )
            console.print(f"\n{panel}")

            # Extracted data summary
            if entry.extracted_data:
                console.print("\n[bold]Extracted Data Summary:[/bold]")
                data = entry.extracted_data
                console.print(f"  Person: {data.person_in_charge or 'N/A'}")
                console.print(f"  Startup: {data.startup_name or 'N/A'}")
                console.print(f"  Partner: {data.partner_org or 'N/A'}")
                console.print(
                    f"  Date: {data.date.strftime('%Y-%m-%d') if data.date else 'N/A'}"
                )

                # Show confidence scores if available
                if hasattr(data, "confidence") and data.confidence:
                    console.print("\n[dim]Confidence Scores:[/dim]")
                    console.print(f"  Person: {data.confidence.person:.2f}")
                    console.print(f"  Startup: {data.confidence.startup:.2f}")
                    console.print(f"  Partner: {data.confidence.partner:.2f}")

            console.print(f"\n[dim]File: {file_path}[/dim]")

        log_cli_operation("errors_show", {"error_id": error_id})

    except FileNotFoundError as e:
        log_cli_error(f"Error not found: {e}")
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        log_cli_error(f"Error showing DLQ entry: {e}")
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ Error showing DLQ entry: {e}[/red]")
        raise typer.Exit(1)


@errors_app.command()
def retry(
    all: bool = typer.Option(False, "--all", help="Retry all failed operations"),
    id: Optional[str] = typer.Option(None, "--id", help="Retry specific error ID"),
    since: Optional[str] = typer.Option(
        None, "--since", help="Retry errors since date (YYYY-MM-DD)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    quiet: bool = typer.Option(False, help="Suppress non-error output"),
):
    """
    Retry failed operations from the DLQ.

    Can retry all errors, specific error by ID, or errors since a date.
    Shows progress indicator for bulk retries. Successful retries are removed
    from DLQ, failed retries have their retry count incremented.

    Examples:
        collabiq errors retry --id email001_20240101_120000
        collabiq errors retry --all
        collabiq errors retry --since 2024-01-01
    """
    console = Console()  # Initialize Console locally

    try:
        # Validate service availability
        if DLQManager is None:
            raise RuntimeError(
                "DLQ manager not available. Ensure notion_integrator module is installed."
            )

        # Validate exactly one option is provided
        options_count = sum([all, id is not None, since is not None])
        if options_count == 0:
            raise ValueError("Must specify --all, --id, or --since")
        if options_count > 1:
            raise ValueError("Can only specify one of --all, --id, or --since")

        # Initialize DLQ manager
        dlq_manager = DLQManager(dlq_dir=str(DLQ_DIR))

        # Get NotionWriter for retry (import here to avoid circular dependency)
        try:
            from notion_integrator.writer import NotionWriter

            notion_writer = NotionWriter()
        except ImportError:
            raise RuntimeError(
                "NotionWriter not available. Ensure notion_integrator module is installed."
            )

        # Determine which entries to retry
        entries_to_retry = []

        if id:
            # Single entry
            file_path = DLQ_DIR / f"{id}.json"
            if not file_path.exists():
                raise FileNotFoundError(f"Error ID not found: {id}")
            entries_to_retry = [str(file_path)]
        else:
            # Multiple entries
            all_files = dlq_manager.list_dlq_entries()

            if since:
                # Filter by date
                since_date = datetime.fromisoformat(since)
                for file_path in all_files:
                    try:
                        entry = dlq_manager.load_dlq_entry(file_path)
                        if entry.failed_at >= since_date:
                            entries_to_retry.append(file_path)
                    except Exception as e:
                        log_cli_error(f"Failed to load {file_path}: {e}")
            else:
                # All entries
                entries_to_retry = all_files

        if not entries_to_retry:
            if json_output:
                output_json(
                    data={"succeeded": 0, "failed": 0, "total": 0}, status="success"
                )
            elif not quiet:
                console.print("[yellow]No errors to retry[/yellow]")
            return

        # Run async retry
        async def run_retries():
            results = {"succeeded": 0, "failed": 0}

            if json_output or quiet:
                # No progress bar
                for file_path in entries_to_retry:
                    try:
                        success = await dlq_manager.retry_failed_write(
                            file_path, notion_writer
                        )
                        if success:
                            results["succeeded"] += 1
                        else:
                            results["failed"] += 1
                    except Exception as e:
                        log_cli_error(f"Error retrying {file_path}: {e}")
                        results["failed"] += 1
            else:
                # With progress bar
                with create_progress() as progress:
                    task = progress.add_task(
                        f"[cyan]Retrying {len(entries_to_retry)} failed operations...",
                        total=len(entries_to_retry),
                    )

                    for file_path in entries_to_retry:
                        try:
                            success = await dlq_manager.retry_failed_write(
                                file_path, notion_writer
                            )
                            if success:
                                results["succeeded"] += 1
                            else:
                                results["failed"] += 1
                        except Exception as e:
                            log_cli_error(f"Error retrying {file_path}: {e}")
                            results["failed"] += 1

                        progress.update(task, advance=1)

            return results

        # Execute retries
        results = asyncio.run(run_retries())

        # Output results
        if json_output:
            output_json(
                data={
                    "succeeded": results["succeeded"],
                    "failed": results["failed"],
                    "total": len(entries_to_retry),
                },
                status="success",
            )
        else:
            console.print("\n[bold]Retry Results:[/bold]")
            console.print(f"  [green]✓ Succeeded: {results['succeeded']}[/green]")
            console.print(f"  [red]✗ Failed: {results['failed']}[/red]")
            console.print(f"  Total: {len(entries_to_retry)}")

        log_cli_operation("errors_retry", results)

    except ValueError as e:
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        log_cli_error(f"Error retrying DLQ entries: {e}")
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ Error retrying DLQ entries: {e}[/red]")
        raise typer.Exit(1)


@errors_app.command()
def clear(
    resolved: bool = typer.Option(
        False, "--resolved", help="Clear only resolved errors (already processed)"
    ),
    before: Optional[str] = typer.Option(
        None, "--before", help="Clear errors before date (YYYY-MM-DD)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    quiet: bool = typer.Option(False, help="Suppress non-error output"),
):
    """
    Clear resolved errors from the DLQ.

    Can clear only resolved/processed errors (--resolved) or errors before
    a specific date (--before). Requires confirmation unless --yes is used.

    Examples:
        collabiq errors clear --resolved --yes
        collabiq errors clear --before 2024-01-01
        collabiq errors clear --resolved --before 2024-01-01 -y
    """
    console = Console()  # Initialize Console locally

    try:
        # Validate service availability
        if DLQManager is None:
            raise RuntimeError(
                "DLQ manager not available. Ensure notion_integrator module is installed."
            )

        # Initialize DLQ manager
        dlq_manager = DLQManager(dlq_dir=str(DLQ_DIR))

        # Get all DLQ entries
        all_files = dlq_manager.list_dlq_entries()

        if not all_files:
            if json_output:
                output_json(data={"cleared": 0, "total": 0}, status="success")
            elif not quiet:
                console.print("[green]✓ No errors in DLQ[/green]")
            return

        # Determine which entries to clear
        entries_to_clear = []
        before_date = None

        if before:
            try:
                before_date = datetime.fromisoformat(before)
            except ValueError:
                raise ValueError(f"Invalid date format: {before}. Use YYYY-MM-DD")

        for file_path in all_files:
            try:
                entry = dlq_manager.load_dlq_entry(file_path)

                # Filter by resolved status
                if resolved and not dlq_manager.is_processed(entry.email_id):
                    continue

                # Filter by date
                if before_date and entry.failed_at >= before_date:
                    continue

                entries_to_clear.append(file_path)
            except Exception as e:
                log_cli_error(f"Failed to load {file_path}: {e}")

        if not entries_to_clear:
            if json_output:
                output_json(
                    data={"cleared": 0, "total": len(all_files)}, status="success"
                )
            elif not quiet:
                console.print("[yellow]No errors match the criteria[/yellow]")
            return

        # Confirm deletion
        if not yes and not json_output:
            console.print(
                f"[yellow]About to clear {len(entries_to_clear)} error(s) from DLQ[/yellow]"
            )
            confirm = typer.confirm("Are you sure?")
            if not confirm:
                console.print("[dim]Cancelled[/dim]")
                return

        # Delete files
        cleared_count = 0
        for file_path in entries_to_clear:
            try:
                Path(file_path).unlink()
                cleared_count += 1
            except Exception as e:
                log_cli_error(f"Failed to delete {file_path}: {e}")

        # Output results
        if json_output:
            output_json(
                data={
                    "cleared": cleared_count,
                    "total": len(all_files),
                    "remaining": len(all_files) - cleared_count,
                },
                status="success",
            )
        else:
            console.print(f"[green]✓ Cleared {cleared_count} error(s) from DLQ[/green]")
            remaining = len(all_files) - cleared_count
            if remaining > 0:
                console.print(f"[dim]{remaining} error(s) remaining[/dim]")

        log_cli_operation(
            "errors_clear", {"cleared": cleared_count, "total": len(all_files)}
        )

    except ValueError as e:
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        log_cli_error(f"Error clearing DLQ entries: {e}")
        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ Error clearing DLQ entries: {e}[/red]")
        raise typer.Exit(1)
