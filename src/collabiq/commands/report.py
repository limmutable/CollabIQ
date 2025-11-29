"""
CLI commands for Admin Reporting.

Provides commands for generating, viewing, and managing admin reports.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from admin_reporting.config import ReportingConfig
from admin_reporting.reporter import ReportGenerator
from admin_reporting.alerter import AlertManager
from admin_reporting.archiver import ReportArchiver
from admin_reporting.models import HealthStatus, AlertSeverity
from daemon.state_manager import StateManager
from models.daemon_state import DaemonProcessState

logger = logging.getLogger(__name__)
console = Console()

report_app = typer.Typer(
    name="report",
    help="Admin reporting commands for system monitoring and email delivery.",
)


@report_app.command("generate")
def generate_report(
    send: bool = typer.Option(False, "--send", "-s", help="Send report via email"),
    recipients: Optional[str] = typer.Option(
        None, "--to", "-t", help="Override recipients (comma-separated emails)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Save HTML report to file"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output report data as JSON"
    ),
) -> None:
    """
    Generate admin report from current daemon state.

    Examples:
        collabiq report generate                  # Generate and display report
        collabiq report generate --send           # Generate and send via email
        collabiq report generate --output report.html  # Save to file
        collabiq report generate --json           # Output as JSON
    """
    # Load daemon state
    state_path = Path("data/daemon/state.json")
    if not state_path.exists():
        console.print(
            "[yellow]No daemon state found. Creating sample state...[/yellow]"
        )
        state = DaemonProcessState()
    else:
        state_manager = StateManager(state_path)
        state = state_manager.load_state()

    # Generate report
    generator = ReportGenerator()
    report = generator.generate_daily_report(state)

    if json_output:
        # Output as JSON
        report_dict = report.model_dump(mode="json")
        console.print(json.dumps(report_dict, indent=2, default=str))
        return

    # Render report
    html, text = generator.render_report(report)

    if output:
        # Save to file
        output.write_text(html)
        console.print(f"[green]Report saved to {output}[/green]")
        return

    if send:
        # Send via email
        to_list = recipients.split(",") if recipients else None
        try:
            result = generator.generate_and_send(state, recipients=to_list)
            console.print(
                f"[green]Report sent successfully![/green]\n"
                f"Message ID: {result['send_result'].get('id')}"
            )
        except Exception as e:
            console.print(f"[red]Failed to send report: {e}[/red]")
            raise typer.Exit(1)
        return

    # Display in console
    console.print(Panel(text, title="CollabIQ Daily Report", expand=False))


@report_app.command("config")
def show_config() -> None:
    """
    Display current reporting configuration.

    Shows recipients, schedule, thresholds, and archive settings.
    """
    config = ReportingConfig.from_env()

    table = Table(title="Admin Reporting Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Recipients", ", ".join(config.recipients))
    table.add_row("Report Time", config.report_time)
    table.add_row("Timezone", config.timezone)
    table.add_row("Error Rate Threshold", f"{config.error_rate_threshold:.1%}")
    table.add_row("Daily Cost Limit", f"${config.cost_limit_daily:.2f}")
    table.add_row("Archive Directory", str(config.archive_directory))
    table.add_row("Retention Days", str(config.retention_days))

    console.print(table)


@report_app.command("status")
def show_status() -> None:
    """
    Display current system health status.

    Shows health of Gmail, Notion, and LLM providers.
    """
    # Load daemon state
    state_path = Path("data/daemon/state.json")
    if not state_path.exists():
        console.print("[yellow]No daemon state found.[/yellow]")
        return

    state_manager = StateManager(state_path)
    state = state_manager.load_state()

    # Get health status
    generator = ReportGenerator()
    health = generator.check_component_health(state)

    # Display status
    table = Table(title="System Health Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    table.add_column("Last Check")

    def status_color(status: HealthStatus) -> str:
        colors = {
            HealthStatus.OPERATIONAL: "green",
            HealthStatus.DEGRADED: "yellow",
            HealthStatus.UNAVAILABLE: "red",
        }
        return colors.get(status, "white")

    # Gmail
    gmail_check = (
        state.last_gmail_check.isoformat() if state.last_gmail_check else "Never"
    )
    table.add_row(
        "Gmail API",
        f"[{status_color(health.gmail_status)}]{health.gmail_status.value.upper()}[/]",
        gmail_check,
    )

    # Notion
    notion_check = (
        state.last_notion_check.isoformat() if state.last_notion_check else "Never"
    )
    table.add_row(
        "Notion API",
        f"[{status_color(health.notion_status)}]{health.notion_status.value.upper()}[/]",
        notion_check,
    )

    # LLM Providers
    for provider, status in health.llm_providers.items():
        calls = state.llm_calls_by_provider.get(provider, 0)
        table.add_row(
            f"LLM: {provider.capitalize()}",
            f"[{status_color(status)}]{status.value.upper()}[/]",
            f"{calls} calls",
        )

    console.print(table)

    # Overall status
    overall_color = status_color(health.overall_status)
    console.print(
        f"\n[bold]Overall Status:[/bold] [{overall_color}]{health.overall_status.value.upper()}[/]"
    )


@report_app.command("metrics")
def show_metrics() -> None:
    """
    Display current processing metrics.

    Shows email processing stats, error rates, and LLM usage.
    """
    # Load daemon state
    state_path = Path("data/daemon/state.json")
    if not state_path.exists():
        console.print("[yellow]No daemon state found.[/yellow]")
        return

    state_manager = StateManager(state_path)
    state = state_manager.load_state()

    # Display metrics
    table = Table(title="Processing Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Emails Received", str(state.emails_received_count))
    table.add_row("Emails Processed", str(state.emails_processed_count))
    table.add_row("Emails Skipped", str(state.emails_skipped_count))
    table.add_row("Total Processing Cycles", str(state.total_processing_cycles))
    table.add_row("Total Errors", str(state.error_count))

    # Success rate
    if state.emails_received_count > 0:
        success_rate = state.emails_processed_count / state.emails_received_count
        table.add_row("Success Rate", f"{success_rate:.1%}")

    console.print(table)

    # LLM Usage
    if state.llm_calls_by_provider:
        llm_table = Table(title="\nLLM Provider Usage")
        llm_table.add_column("Provider", style="cyan")
        llm_table.add_column("Calls", justify="right")
        llm_table.add_column("Cost (USD)", justify="right")

        total_calls = 0
        total_cost = 0.0

        for provider, calls in state.llm_calls_by_provider.items():
            cost = state.llm_costs_by_provider.get(provider, 0.0)
            llm_table.add_row(provider.capitalize(), str(calls), f"${cost:.4f}")
            total_calls += calls
            total_cost += cost

        llm_table.add_row("[bold]Total[/bold]", str(total_calls), f"${total_cost:.4f}")

        console.print(llm_table)

    # Notion Stats
    notion_table = Table(title="\nNotion Database Stats")
    notion_table.add_column("Metric", style="cyan")
    notion_table.add_column("Value", style="green", justify="right")

    notion_table.add_row("Entries Created", str(state.notion_entries_created))
    notion_table.add_row("Entries Updated", str(state.notion_entries_updated))
    notion_table.add_row("Validation Failures", str(state.notion_validation_failures))

    console.print(notion_table)


# ============================================================================
# Alerts Sub-commands
# ============================================================================


alerts_app = typer.Typer(
    name="alerts",
    help="Critical error alert management.",
)
report_app.add_typer(alerts_app, name="alerts")


@alerts_app.command("list")
def list_alerts() -> None:
    """
    List current pending alerts in the batch.

    Shows alerts that have been detected but not yet sent.
    """
    # Load daemon state
    state_path = Path("data/daemon/state.json")
    if not state_path.exists():
        console.print("[yellow]No daemon state found.[/yellow]")
        return

    state_manager = StateManager(state_path)
    state = state_manager.load_state()

    # Create alert manager and check thresholds
    alert_manager = AlertManager()
    alerts = alert_manager.check_thresholds(state)

    if not alerts:
        console.print("[green]No active alerts detected.[/green]")
        return

    # Display alerts
    table = Table(title="Active Alerts")
    table.add_column("Severity", style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Message")
    table.add_column("Remediation")

    def severity_color(severity: AlertSeverity) -> str:
        colors = {
            AlertSeverity.CRITICAL: "red",
            AlertSeverity.HIGH: "orange3",
            AlertSeverity.MEDIUM: "yellow",
            AlertSeverity.LOW: "green",
        }
        return colors.get(severity, "white")

    for alert in alerts:
        color = severity_color(alert.severity)
        table.add_row(
            f"[{color}]{alert.severity.value.upper()}[/]",
            alert.category,
            alert.message[:60] + "..." if len(alert.message) > 60 else alert.message,
            alert.remediation[:40] + "..."
            if len(alert.remediation) > 40
            else alert.remediation,
        )

    console.print(table)

    # Show batch info
    console.print(
        f"\n[dim]Pending in batch: {len(alert_manager.current_batch.alerts)}[/dim]"
    )
    console.print(
        f"[dim]Alerts sent this hour: {len(alert_manager.sent_alerts_history)}[/dim]"
    )


@alerts_app.command("test")
def test_alert(
    recipients: Optional[str] = typer.Option(
        None, "--to", "-t", help="Override recipients (comma-separated emails)"
    ),
) -> None:
    """
    Send a test alert to verify email delivery.

    This sends a test alert to confirm the alerting system is working.

    Examples:
        collabiq report alerts test
        collabiq report alerts test --to admin@example.com
    """
    from admin_reporting.models import ActionableAlert

    config = ReportingConfig.from_env()
    alert_manager = AlertManager(config=config)

    # Create test alert
    test_alert = ActionableAlert(
        severity=AlertSeverity.LOW,
        category="test",
        message="This is a test alert from CollabIQ. If you received this, your alert system is working correctly.",
        remediation="No action required. This is a test message.",
    )

    # Add to batch
    alert_manager.add_to_batch(test_alert)

    # Override recipients if specified
    if recipients:
        config.alert_recipients = [r.strip() for r in recipients.split(",")]

    try:
        console.print("[cyan]Sending test alert...[/cyan]")
        result = alert_manager.send_alert_batch()

        if result:
            console.print(
                f"[green]Test alert sent successfully![/green]\n"
                f"Message ID: {result.get('id')}"
            )
        else:
            console.print(
                "[yellow]Alert was not sent. This could be due to rate limiting.[/yellow]"
            )
    except Exception as e:
        console.print(f"[red]Failed to send test alert: {e}[/red]")
        raise typer.Exit(1)


@alerts_app.command("config")
def alerts_config() -> None:
    """
    Display current alert configuration.

    Shows alert recipients, thresholds, batching, and rate limiting settings.
    """
    config = ReportingConfig.from_env()

    table = Table(title="Alert Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Recipients
    alert_recipients = (
        config.alert_recipients if config.alert_recipients else config.recipients
    )
    table.add_row("Alert Recipients", ", ".join(alert_recipients))

    # Thresholds
    table.add_row("Error Rate Threshold", f"{config.error_rate_threshold:.1%}")

    # Batching
    table.add_row("Batch Window", f"{config.alert_batch_window_minutes} minutes")
    table.add_row("Max Alerts/Hour", str(config.max_alerts_per_hour))

    console.print(table)


# ============================================================================
# Archive Commands (T056-T057)
# ============================================================================


@report_app.command("list")
def list_archives(
    limit: int = typer.Option(
        10, "--limit", "-n", help="Maximum number of archives to show"
    ),
) -> None:
    """
    List archived reports.

    Shows recent archived reports with date, size, and file paths.

    Examples:
        collabiq report list
        collabiq report list --limit 20
    """
    archiver = ReportArchiver()
    archives = archiver.list_archives()

    if not archives:
        console.print("[yellow]No archived reports found.[/yellow]")
        console.print(f"Archive directory: {archiver.archive_dir}")
        return

    # Limit results
    archives = archives[:limit]

    table = Table(title="Archived Reports")
    table.add_column("Date", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("JSON Path")
    table.add_column("HTML", justify="center")

    for archive in archives:
        size_kb = archive.get("size_bytes", 0) / 1024
        has_html = "yes" if archive.get("html_path") else "no"

        table.add_row(
            archive["date"].isoformat(),
            f"{size_kb:.1f} KB",
            str(archive["json_path"]),
            f"[green]{has_html}[/green]"
            if has_html == "yes"
            else f"[red]{has_html}[/red]",
        )

    console.print(table)
    console.print(
        f"\n[dim]Showing {len(archives)} of {len(archiver.list_archives())} archives[/dim]"
    )
    console.print(f"[dim]Archive directory: {archiver.archive_dir}[/dim]")


@report_app.command("show")
def show_archive(
    report_date: Optional[str] = typer.Argument(
        None, help="Date of report to show (YYYY-MM-DD). Defaults to today."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    html: bool = typer.Option(False, "--html", help="Output HTML content"),
) -> None:
    """
    Show a specific archived report.

    Examples:
        collabiq report show                    # Show today's report
        collabiq report show 2024-01-15         # Show specific date
        collabiq report show --json             # Output as JSON
        collabiq report show --html             # Output HTML content
    """
    from datetime import date as date_type

    # Parse date
    if report_date:
        try:
            parts = report_date.split("-")
            target_date = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            console.print(
                f"[red]Invalid date format: {report_date}. Use YYYY-MM-DD.[/red]"
            )
            raise typer.Exit(1)
    else:
        target_date = date_type.today()

    archiver = ReportArchiver()
    archive = archiver.get_archive(target_date)

    if archive is None:
        console.print(
            f"[yellow]No archived report found for {target_date.isoformat()}[/yellow]"
        )
        raise typer.Exit(1)

    if html:
        # Output HTML content
        html_path = archive.get("html_path")
        if html_path and Path(html_path).exists():
            console.print(Path(html_path).read_text())
        else:
            console.print("[yellow]HTML file not found.[/yellow]")
        return

    # Load report data
    data = archiver.get_archive_data(target_date)
    if data is None:
        console.print(
            f"[red]Failed to load report data for {target_date.isoformat()}[/red]"
        )
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(data, indent=2, default=str))
        return

    # Display summary
    console.print(Panel(f"[bold]Archived Report: {target_date.isoformat()}[/bold]"))

    # Report metadata
    meta_table = Table(show_header=False)
    meta_table.add_column("Key", style="cyan")
    meta_table.add_column("Value")

    meta_table.add_row("Report ID", data.get("report_id", "N/A"))
    meta_table.add_row("Generated At", data.get("generated_at", "N/A"))
    meta_table.add_row("Period Start", data.get("period_start", "N/A"))
    meta_table.add_row("Period End", data.get("period_end", "N/A"))

    console.print(meta_table)

    # Processing metrics
    if "processing_metrics" in data:
        metrics = data["processing_metrics"]
        console.print("\n[bold]Processing Metrics[/bold]")
        metrics_table = Table()
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", justify="right")

        metrics_table.add_row("Emails Received", str(metrics.get("emails_received", 0)))
        metrics_table.add_row(
            "Emails Processed", str(metrics.get("emails_processed", 0))
        )
        metrics_table.add_row("Success Rate", f"{metrics.get('success_rate', 0):.1%}")

        console.print(metrics_table)

    # LLM Usage
    if "llm_usage" in data:
        llm = data["llm_usage"]
        console.print("\n[bold]LLM Usage[/bold]")
        llm_table = Table()
        llm_table.add_column("Metric", style="cyan")
        llm_table.add_column("Value", justify="right")

        llm_table.add_row("Total Calls", str(llm.get("total_calls", 0)))
        llm_table.add_row("Total Cost", f"${llm.get('total_cost', 0):.4f}")

        console.print(llm_table)

    # File paths
    console.print(f"\n[dim]JSON: {archive['json_path']}[/dim]")
    if archive.get("html_path"):
        console.print(f"[dim]HTML: {archive['html_path']}[/dim]")
