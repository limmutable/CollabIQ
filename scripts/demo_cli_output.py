#!/usr/bin/env python
"""Generate example CLI output for documentation.

This script shows what the CLI commands will display.
"""

from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.table import Table

# Simulate some realistic provider status
provider_data = {
    "gemini": {
        "health": "healthy",
        "circuit_breaker": "closed",
        "success_rate": 0.98,
        "total_calls": 127,
        "errors": 3,
        "avg_response_ms": 845,
        "last_success": datetime.now(timezone.utc) - timedelta(minutes=5),
        "last_failure": datetime.now(timezone.utc) - timedelta(hours=2),
        "api_calls": 127,
        "input_tokens": 1_234_567,
        "output_tokens": 567_890,
        "total_cost": 0.0,  # Free tier
        "cost_per_email": 0.0,
    },
    "claude": {
        "health": "healthy",
        "circuit_breaker": "closed",
        "success_rate": 1.0,
        "total_calls": 45,
        "errors": 0,
        "avg_response_ms": 1234,
        "last_success": datetime.now(timezone.utc) - timedelta(minutes=2),
        "last_failure": None,
        "api_calls": 45,
        "input_tokens": 456_789,
        "output_tokens": 234_567,
        "total_cost": 4.8912,
        "cost_per_email": 0.108693,
    },
    "openai": {
        "health": "unhealthy",
        "circuit_breaker": "open",
        "success_rate": 0.75,
        "total_calls": 32,
        "errors": 8,
        "avg_response_ms": 2100,
        "last_success": datetime.now(timezone.utc) - timedelta(hours=1),
        "last_failure": datetime.now(timezone.utc) - timedelta(minutes=15),
        "api_calls": 32,
        "input_tokens": 234_567,
        "output_tokens": 123_456,
        "total_cost": 0.109345,
        "cost_per_email": 0.003417,
    },
}


def format_timestamp(dt):
    """Format datetime for display."""
    if dt is None:
        return "Never"
    now = datetime.now(timezone.utc)
    delta = now - dt
    if delta.total_seconds() < 60:
        return "Just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes}m ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = int(delta.total_seconds() / 86400)
        return f"{days}d ago"


# =============================================================================
# Example 1: Basic Status
# =============================================================================

console = Console()

print("\n" + "=" * 80)
print("EXAMPLE 1: collabiq llm status")
print("=" * 80 + "\n")

console.print("\n[bold cyan]LLM Provider Health Status[/bold cyan]\n")

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Provider", style="cyan", width=12)
table.add_column("Health", justify="center", width=10)
table.add_column("Circuit", justify="center", width=10)
table.add_column("Success Rate", justify="right", width=12)
table.add_column("Errors", justify="right", width=8)
table.add_column("Avg Response", justify="right", width=12)
table.add_column("Last Success", justify="center", width=16)
table.add_column("Last Failure", justify="center", width=16)

for provider_name, data in provider_data.items():
    health_color = "green" if data["health"] == "healthy" else "red"
    health_display = f"[{health_color}]{data['health'].upper()}[/{health_color}]"

    cb_state = data["circuit_breaker"].upper()
    if cb_state == "CLOSED":
        cb_display = f"[green]{cb_state}[/green]"
    elif cb_state == "OPEN":
        cb_display = f"[red]{cb_state}[/red]"
    else:
        cb_display = f"[yellow]{cb_state}[/yellow]"

    table.add_row(
        provider_name.title(),
        health_display,
        cb_display,
        f"{data['success_rate']:.1%}",
        str(data["errors"]),
        f"{data['avg_response_ms']:.0f}ms",
        format_timestamp(data["last_success"]),
        format_timestamp(data["last_failure"]),
    )

console.print(table)
console.print(
    "\n[dim]Use --detailed flag to view cost metrics and orchestration info[/dim]\n"
)

# =============================================================================
# Example 2: Detailed Status
# =============================================================================

print("\n" + "=" * 80)
print("EXAMPLE 2: collabiq llm status --detailed")
print("=" * 80 + "\n")

console.print("\n[bold cyan]LLM Provider Detailed Status[/bold cyan]\n")

# Health Metrics Table
console.print("[bold]Health Metrics[/bold]\n")
health_table = Table(show_header=True, header_style="bold magenta")
health_table.add_column("Provider", style="cyan", width=12)
health_table.add_column("Health", justify="center", width=10)
health_table.add_column("Circuit", justify="center", width=10)
health_table.add_column("Success Rate", justify="right", width=12)
health_table.add_column("API Calls", justify="right", width=10)
health_table.add_column("Errors", justify="right", width=8)
health_table.add_column("Avg Response", justify="right", width=12)

for provider_name, data in provider_data.items():
    health_color = "green" if data["health"] == "healthy" else "red"
    health_display = f"[{health_color}]{data['health'].upper()}[/{health_color}]"

    cb_state = data["circuit_breaker"].upper()
    if cb_state == "CLOSED":
        cb_display = f"[green]{cb_state}[/green]"
    elif cb_state == "OPEN":
        cb_display = f"[red]{cb_state}[/red]"
    else:
        cb_display = f"[yellow]{cb_state}[/yellow]"

    health_table.add_row(
        provider_name.title(),
        health_display,
        cb_display,
        f"{data['success_rate']:.1%}",
        str(data["total_calls"]),
        str(data["errors"]),
        f"{data['avg_response_ms']:.0f}ms",
    )

console.print(health_table)

# Cost Metrics Table
console.print("\n[bold]Cost Metrics[/bold]\n")
cost_table = Table(show_header=True, header_style="bold magenta")
cost_table.add_column("Provider", style="cyan", width=12)
cost_table.add_column("API Calls", justify="right", width=10)
cost_table.add_column("Input Tokens", justify="right", width=14)
cost_table.add_column("Output Tokens", justify="right", width=14)
cost_table.add_column("Total Cost", justify="right", width=12)
cost_table.add_column("Cost/Email", justify="right", width=12)

for provider_name, data in provider_data.items():
    cost_table.add_row(
        provider_name.title(),
        str(data["api_calls"]),
        f"{data['input_tokens']:,}",
        f"{data['output_tokens']:,}",
        f"${data['total_cost']:.4f}",
        f"${data['cost_per_email']:.6f}",
    )

console.print(cost_table)

# Orchestration Configuration
console.print("\n[bold]Orchestration Configuration[/bold]\n")
strategy_table = Table(show_header=False, show_edge=False, box=None)
strategy_table.add_column("Setting", style="cyan", width=20)
strategy_table.add_column("Value", style="white")

strategy_table.add_row("Active Strategy:", "[green]failover[/green]")
strategy_table.add_row("Provider Priority:", "[white]gemini, claude, openai[/white]")
strategy_table.add_row("Available Providers:", "[white]gemini, claude, openai[/white]")
strategy_table.add_row("Unhealthy Threshold:", "[white]5 failures[/white]")
strategy_table.add_row("Circuit Breaker Timeout:", "[white]60.0s[/white]")

console.print(strategy_table)
console.print()

# =============================================================================
# Example 3: Test Provider
# =============================================================================

print("\n" + "=" * 80)
print("EXAMPLE 3: collabiq llm test gemini")
print("=" * 80 + "\n")

console.print("\n[bold]Testing Gemini...[/bold]\n")
console.print("[green]✓[/green] Gemini is [green]HEALTHY[/green] and available\n")

print("\n" + "=" * 80)
print("EXAMPLE 4: collabiq llm test openai")
print("=" * 80 + "\n")

console.print("\n[bold]Testing Openai...[/bold]\n")
console.print("[red]✗[/red] Openai is [red]UNHEALTHY[/red] or unavailable\n")
console.print(
    "[yellow]Check circuit breaker state with 'collabiq llm status'[/yellow]\n"
)

# =============================================================================
# Example 5: Set Strategy
# =============================================================================

print("\n" + "=" * 80)
print("EXAMPLE 5: collabiq llm set-strategy failover")
print("=" * 80 + "\n")

console.print(
    "\n[green]✓[/green] Orchestration strategy set to [cyan]failover[/cyan]\n"
)

print("\n" + "=" * 80)
print("Done! All examples generated.")
print("=" * 80 + "\n")
