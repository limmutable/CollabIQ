"""LLM provider management commands.

Commands:
- status: View all provider health metrics and costs
- test: Test provider connectivity
- set-strategy: Change orchestration strategy

Phase 3b multi-LLM orchestration commands with health and cost tracking.
"""

import logging
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.types import OrchestrationConfig

app = typer.Typer(
    name="llm",
    help="LLM provider management (status, test, set-strategy)",
)

console = Console()
logger = logging.getLogger(__name__)


# ==============================================================================
# T083-T087: llm status - View provider health status
# ==============================================================================


@app.command()
def status(
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed cost metrics and orchestration info",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (not implemented)"
    ),
):
    """
    View LLM provider health status and metrics.

    Shows health status, success rates, response times, and error counts.
    Use --detailed flag to include cost metrics and orchestration strategy.

    Examples:
        collabiq llm status
        collabiq llm status --detailed
    """
    try:
        # Create orchestrator with default config
        config = OrchestrationConfig(
            default_strategy="failover",
            provider_priority=["gemini", "claude", "openai"],
        )
        orchestrator = LLMOrchestrator.from_config(config)

        # Get provider status
        provider_status = orchestrator.get_provider_status()

        if not provider_status:
            console.print(
                "\n[yellow]No LLM providers configured. "
                "Please check your API keys.[/yellow]\n"
            )
            raise typer.Exit(1)

        if detailed:
            _display_detailed_status(orchestrator, provider_status)
        else:
            _display_basic_status(provider_status)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        logger.error(f"Failed to get provider status: {e}", exc_info=True)
        raise typer.Exit(1)


def _display_basic_status(provider_status: dict):
    """Display basic provider health status.

    T084: Health status (healthy/unhealthy, circuit breaker state)
    T085: Success rate and error count
    T086: Average response time
    T087: Last success/failure timestamps
    """
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

    for provider_name, status in provider_status.items():
        # Health status with color
        health_color = "green" if status.health_status == "healthy" else "red"
        health_display = f"[{health_color}]{status.health_status.upper()}[/{health_color}]"

        # Circuit breaker state with color
        cb_state = status.circuit_breaker_state.upper()
        if cb_state == "CLOSED":
            cb_display = f"[green]{cb_state}[/green]"
        elif cb_state == "OPEN":
            cb_display = f"[red]{cb_state}[/red]"
        else:  # HALF_OPEN
            cb_display = f"[yellow]{cb_state}[/yellow]"

        # Success rate
        success_rate_display = f"{status.success_rate:.1%}"

        # Error count
        error_count = status.total_api_calls - int(
            status.total_api_calls * status.success_rate
        )

        # Response time
        response_time_display = (
            f"{status.average_response_time_ms:.0f}ms"
            if status.average_response_time_ms > 0
            else "N/A"
        )

        # Last success timestamp
        last_success_display = (
            _format_timestamp(status.last_success) if status.last_success else "Never"
        )

        # Last failure timestamp
        last_failure_display = (
            _format_timestamp(status.last_failure) if status.last_failure else "Never"
        )

        table.add_row(
            provider_name.title(),
            health_display,
            cb_display,
            success_rate_display,
            str(error_count),
            response_time_display,
            last_success_display,
            last_failure_display,
        )

    console.print(table)
    console.print(
        "\n[dim]Use --detailed flag to view cost metrics and orchestration info[/dim]\n"
    )


def _display_detailed_status(orchestrator: LLMOrchestrator, provider_status: dict):
    """Display detailed status with cost metrics and orchestration info.

    T088: --detailed flag
    T089: Total API calls, tokens, and cost per provider
    T090: Average cost per email
    T091: Orchestration strategy display
    T094: Rich formatted tables
    """
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

    for provider_name, status in provider_status.items():
        health_color = "green" if status.health_status == "healthy" else "red"
        health_display = f"[{health_color}]{status.health_status.upper()}[/{health_color}]"

        cb_state = status.circuit_breaker_state.upper()
        if cb_state == "CLOSED":
            cb_display = f"[green]{cb_state}[/green]"
        elif cb_state == "OPEN":
            cb_display = f"[red]{cb_state}[/red]"
        else:
            cb_display = f"[yellow]{cb_state}[/yellow]"

        error_count = status.total_api_calls - int(
            status.total_api_calls * status.success_rate
        )

        response_time_display = (
            f"{status.average_response_time_ms:.0f}ms"
            if status.average_response_time_ms > 0
            else "N/A"
        )

        health_table.add_row(
            provider_name.title(),
            health_display,
            cb_display,
            f"{status.success_rate:.1%}",
            str(status.total_api_calls),
            str(error_count),
            response_time_display,
        )

    console.print(health_table)

    # Cost Metrics Table (T089, T090)
    if orchestrator.cost_tracker:
        console.print("\n[bold]Cost Metrics[/bold]\n")
        cost_table = Table(show_header=True, header_style="bold magenta")
        cost_table.add_column("Provider", style="cyan", width=12)
        cost_table.add_column("API Calls", justify="right", width=10)
        cost_table.add_column("Input Tokens", justify="right", width=14)
        cost_table.add_column("Output Tokens", justify="right", width=14)
        cost_table.add_column("Total Cost", justify="right", width=12)
        cost_table.add_column("Cost/Email", justify="right", width=12)

        cost_metrics = orchestrator.cost_tracker.get_all_metrics()

        for provider_name in provider_status.keys():
            metrics = cost_metrics.get(provider_name)
            if metrics:
                cost_table.add_row(
                    provider_name.title(),
                    str(metrics.total_api_calls),
                    f"{metrics.total_input_tokens:,}",
                    f"{metrics.total_output_tokens:,}",
                    f"${metrics.total_cost_usd:.4f}",
                    f"${metrics.average_cost_per_email:.6f}",
                )
            else:
                cost_table.add_row(
                    provider_name.title(),
                    "0",
                    "0",
                    "0",
                    "$0.0000",
                    "$0.000000",
                )

        console.print(cost_table)

    # Orchestration Strategy (T091)
    console.print("\n[bold]Orchestration Configuration[/bold]\n")
    strategy_table = Table(show_header=False, show_edge=False, box=None)
    strategy_table.add_column("Setting", style="cyan", width=20)
    strategy_table.add_column("Value", style="white")

    strategy_table.add_row(
        "Active Strategy:", f"[green]{orchestrator.get_active_strategy()}[/green]"
    )
    strategy_table.add_row(
        "Provider Priority:", f"[white]{', '.join(orchestrator.config.provider_priority)}[/white]"
    )
    strategy_table.add_row(
        "Available Providers:",
        f"[white]{', '.join(orchestrator.get_available_providers())}[/white]",
    )
    strategy_table.add_row(
        "Unhealthy Threshold:", f"[white]{orchestrator.config.unhealthy_threshold} failures[/white]"
    )
    strategy_table.add_row(
        "Circuit Breaker Timeout:",
        f"[white]{orchestrator.config.circuit_breaker_timeout_seconds}s[/white]",
    )

    console.print(strategy_table)
    console.print()


def _format_timestamp(dt: datetime) -> str:
    """Format datetime for display (relative time)."""
    if dt is None:
        return "Never"

    # Make timezone aware if needed
    if dt.tzinfo is None:
        from datetime import timezone

        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(dt.tzinfo)
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


# ==============================================================================
# T092: llm test - Test specific provider connectivity
# ==============================================================================


@app.command()
def test(
    provider: str = typer.Argument(
        ..., help="Provider name (gemini, claude, openai)"
    ),
):
    """
    Test specific LLM provider connectivity and health.

    Checks if the provider is configured, has valid credentials,
    and is currently healthy according to circuit breaker state.

    Examples:
        collabiq llm test gemini
        collabiq llm test claude
    """
    try:
        # Validate provider name
        valid_providers = {"gemini", "claude", "openai"}
        if provider.lower() not in valid_providers:
            console.print(
                f"\n[red]Invalid provider: {provider}[/red]\n"
                f"Valid providers: {', '.join(valid_providers)}\n"
            )
            raise typer.Exit(1)

        # Create orchestrator
        config = OrchestrationConfig(
            default_strategy="failover",
            provider_priority=["gemini", "claude", "openai"],
        )
        orchestrator = LLMOrchestrator.from_config(config)

        # Test provider
        is_healthy = orchestrator.test_provider(provider.lower())

        # Display result
        console.print(f"\n[bold]Testing {provider.title()}...[/bold]\n")

        if is_healthy:
            console.print(
                f"[green]✓[/green] {provider.title()} is [green]HEALTHY[/green] and available\n"
            )
        else:
            console.print(
                f"[red]✗[/red] {provider.title()} is [red]UNHEALTHY[/red] or unavailable\n"
            )
            console.print(
                "[yellow]Check circuit breaker state with 'collabiq llm status'[/yellow]\n"
            )

    except Exception as e:
        console.print(f"\n[red]Error testing provider: {e}[/red]\n")
        logger.error(f"Failed to test provider {provider}: {e}", exc_info=True)
        raise typer.Exit(1)


# ==============================================================================
# T093: llm set-strategy - Set orchestration strategy
# ==============================================================================


@app.command()
def set_strategy(
    strategy: str = typer.Argument(
        ..., help="Orchestration strategy (failover, consensus, best_match)"
    ),
):
    """
    Set LLM orchestration strategy.

    Available strategies:
    - failover: Sequential failover through provider priority list
    - consensus: Query multiple providers and merge results (not yet implemented)
    - best_match: Select best result from multiple providers (not yet implemented)

    Examples:
        collabiq llm set-strategy failover
        collabiq llm set-strategy consensus
    """
    try:
        # Validate strategy
        valid_strategies = {"failover", "consensus", "best_match"}
        if strategy.lower() not in valid_strategies:
            console.print(
                f"\n[red]Invalid strategy: {strategy}[/red]\n"
                f"Valid strategies: {', '.join(valid_strategies)}\n"
            )
            raise typer.Exit(1)

        # Create orchestrator
        config = OrchestrationConfig(
            default_strategy="failover",
            provider_priority=["gemini", "claude", "openai"],
        )
        orchestrator = LLMOrchestrator.from_config(config)

        # Check if strategy is implemented
        if strategy.lower() in {"consensus", "best_match"}:
            console.print(
                f"\n[yellow]Warning: Strategy '{strategy}' is not yet implemented.[/yellow]\n"
                "Currently only 'failover' strategy is available.\n"
            )
            raise typer.Exit(1)

        # Set strategy
        orchestrator.set_strategy(strategy.lower())

        console.print(
            f"\n[green]✓[/green] Orchestration strategy set to [cyan]{strategy}[/cyan]\n"
        )

    except Exception as e:
        console.print(f"\n[red]Error setting strategy: {e}[/red]\n")
        logger.error(f"Failed to set strategy {strategy}: {e}", exc_info=True)
        raise typer.Exit(1)
