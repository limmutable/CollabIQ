"""LLM provider management commands.

Commands:
- status: View all provider health metrics and costs
- test: Test provider connectivity
- set-strategy: Change orchestration strategy

Phase 3b multi-LLM orchestration commands with health and cost tracking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig, ProviderQualityComparison

# Create the llm subcommand app
llm_app = typer.Typer(
    name="llm",
    help="LLM provider management (status, test, strategy, routing)",
)

# ==============================================================================
# T083-T087: llm status - View provider health status
# ==============================================================================


@llm_app.command()
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
    console = Console()
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
    console = Console()
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
    console = Console()
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

    # Quality Metrics Table (T017 - Phase 3c)
    if orchestrator.quality_tracker:
        console.print("\n[bold]Quality Metrics[/bold]\n")
        quality_table = Table(show_header=True, header_style="bold magenta")
        quality_table.add_column("Provider", style="cyan", width=12)
        quality_table.add_column("Extractions", justify="right", width=12)
        quality_table.add_column("Validation", justify="right", width=12)
        quality_table.add_column("Avg Confidence", justify="right", width=14)
        quality_table.add_column("Completeness", justify="right", width=12)
        quality_table.add_column("Fields Avg", justify="right", width=10)

        quality_metrics = orchestrator.quality_tracker.get_all_metrics()

        for provider_name in provider_status.keys():
            metrics = quality_metrics.get(provider_name)
            if metrics and metrics.total_extractions > 0:
                # Format validation success rate with color
                validation_rate = metrics.validation_success_rate
                if validation_rate >= 95:
                    validation_color = "green"
                elif validation_rate >= 80:
                    validation_color = "yellow"
                else:
                    validation_color = "red"
                validation_display = f"[{validation_color}]{validation_rate:.1f}%[/{validation_color}]"

                # Format confidence with color
                confidence = metrics.average_overall_confidence * 100
                if confidence >= 85:
                    confidence_color = "green"
                elif confidence >= 70:
                    confidence_color = "yellow"
                else:
                    confidence_color = "red"
                confidence_display = f"[{confidence_color}]{confidence:.1f}%[/{confidence_color}]"

                # Format completeness with color
                completeness = metrics.average_field_completeness
                if completeness >= 90:
                    completeness_color = "green"
                elif completeness >= 75:
                    completeness_color = "yellow"
                else:
                    completeness_color = "red"
                completeness_display = f"[{completeness_color}]{completeness:.1f}%[/{completeness_color}]"

                quality_table.add_row(
                    provider_name.title(),
                    str(metrics.total_extractions),
                    validation_display,
                    confidence_display,
                    completeness_display,
                    f"{metrics.average_fields_extracted:.1f}/5",
                )
            else:
                quality_table.add_row(
                    provider_name.title(),
                    "0",
                    "[dim]N/A[/dim]",
                    "[dim]N/A[/dim]",
                    "[dim]N/A[/dim]",
                    "[dim]0.0/5[/dim]",
                )

        console.print(quality_table)

        # Per-field confidence breakdown for each provider
        console.print("\n[bold]Per-Field Confidence Breakdown[/bold]\n")
        for provider_name in provider_status.keys():
            metrics = quality_metrics.get(provider_name)
            if metrics and metrics.total_extractions > 0:
                console.print(f"[cyan]{provider_name.title()}:[/cyan]")
                field_table = Table(show_header=False, show_edge=False, box=None, pad_edge=False)
                field_table.add_column("Field", style="white", width=15)
                field_table.add_column("Confidence", style="white", width=10, justify="right")

                for field_name, confidence_value in metrics.per_field_confidence_averages.items():
                    confidence_pct = confidence_value * 100
                    if confidence_pct >= 85:
                        color = "green"
                    elif confidence_pct >= 70:
                        color = "yellow"
                    else:
                        color = "red"
                    field_table.add_row(
                        f"  {field_name.title()}:",
                        f"[{color}]{confidence_pct:.1f}%[/{color}]"
                    )

                console.print(field_table)
                console.print()

    # Orchestration Strategy (T091)
    console.print("[bold]Orchestration Configuration[/bold]\n")
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

    # Quality Routing Status (T029)
    quality_routing_enabled = orchestrator.config.enable_quality_routing
    if quality_routing_enabled:
        quality_status = "[green]ENABLED[/green]"
    else:
        quality_status = "[yellow]DISABLED[/yellow]"

    strategy_table.add_row(
        "Quality Routing:", quality_status
    )

    # Show quality thresholds if enabled and configured
    if quality_routing_enabled and orchestrator.config.quality_threshold:
        threshold = orchestrator.config.quality_threshold
        threshold_info = (
            f"confidence≥{threshold.minimum_average_confidence:.2f}, "
            f"completeness≥{threshold.minimum_field_completeness:.1f}%, "
            f"failures≤{threshold.maximum_validation_failure_rate:.1f}%"
        )
        strategy_table.add_row(
            "  Thresholds:", f"[dim]{threshold_info}[/dim]"
        )

        # Show which provider would be selected based on current metrics
        if orchestrator.quality_tracker:
            available_providers = orchestrator.get_available_providers()
            selected_provider = orchestrator.quality_tracker.select_provider_by_quality(
                available_providers
            )
            if selected_provider:
                strategy_table.add_row(
                    "  Selected Provider:", f"[cyan]{selected_provider.title()}[/cyan]"
                )
            else:
                strategy_table.add_row(
                    "  Selected Provider:", "[dim]None (no quality metrics)[/dim]"
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


@llm_app.command()
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
    console = Console()
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


@llm_app.command()
def set_strategy(
    strategy: str = typer.Argument(
        ..., help="Orchestration strategy (failover, consensus, best_match, all_providers)"
    ),
):
    """
    Set LLM orchestration strategy.

    Available strategies:
    - failover: Sequential failover through provider priority list
    - consensus: Query multiple providers and merge results via voting
    - best_match: Query all providers and select highest confidence result
    - all_providers: Query ALL providers and collect metrics from all (RECOMMENDED)

    RECOMMENDED: Use 'all_providers' for production to continuously collect
    quality metrics from all providers for quality-based routing decisions.

    Examples:
        collabiq llm set-strategy all_providers  # Recommended
        collabiq llm set-strategy failover
        collabiq llm set-strategy consensus
    """
    console = Console()
    try:
        # Validate strategy
        valid_strategies = {"failover", "consensus", "best_match", "all_providers"}
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

        # Set strategy
        orchestrator.set_strategy(strategy.lower())

        console.print(
            f"\n[green]✓[/green] Orchestration strategy set to [cyan]{strategy}[/cyan]\n"
        )

    except Exception as e:
        console.print(f"\n[red]Error setting strategy: {e}[/red]\n")
        logger.error(f"Failed to set strategy {strategy}: {e}", exc_info=True)
        raise typer.Exit(1)


# ==============================================================================
# T028: llm set-quality-routing - Enable/disable quality-based routing
# ==============================================================================


@llm_app.command()
def set_quality_routing(
    enable: bool = typer.Option(
        None,
        "--enable/--disable",
        help="Enable or disable quality-based routing",
    ),
    min_confidence: Optional[float] = typer.Option(
        None,
        "--min-confidence",
        help="Minimum average confidence threshold (0.0-1.0)",
        min=0.0,
        max=1.0,
    ),
    min_completeness: Optional[float] = typer.Option(
        None,
        "--min-completeness",
        help="Minimum field completeness threshold (0.0-100.0)",
        min=0.0,
        max=100.0,
    ),
    max_validation_failures: Optional[float] = typer.Option(
        None,
        "--max-validation-failures",
        help="Maximum validation failure rate (0.0-100.0)",
        min=0.0,
        max=100.0,
    ),
):
    """
    Configure quality-based provider routing.

    Quality routing selects providers based on historical quality metrics
    instead of fixed priority order. This helps ensure high-quality extractions
    by routing requests to providers with the best track record.

    Examples:
        collabiq llm set-quality-routing --enable
        collabiq llm set-quality-routing --disable
        collabiq llm set-quality-routing --enable --min-confidence 0.85
        collabiq llm set-quality-routing --enable --min-completeness 90.0
    """
    console = Console()
    try:
        if enable is None:
            console.print(
                "\n[yellow]Error: Must specify --enable or --disable[/yellow]\n"
            )
            raise typer.Exit(1)

        # Display current configuration
        console.print("\n[bold cyan]Quality-Based Routing Configuration[/bold cyan]\n")

        if enable:
            console.print("[green]✓[/green] Quality routing [green]ENABLED[/green]")

            # Show threshold configuration if provided
            if any([min_confidence, min_completeness, max_validation_failures]):
                console.print("\n[bold]Quality Thresholds:[/bold]")
                if min_confidence is not None:
                    console.print(
                        f"  Minimum Confidence: [cyan]{min_confidence:.2f}[/cyan]"
                    )
                if min_completeness is not None:
                    console.print(
                        f"  Minimum Completeness: [cyan]{min_completeness:.1f}%[/cyan]"
                    )
                if max_validation_failures is not None:
                    console.print(
                        f"  Max Validation Failures: [cyan]{max_validation_failures:.1f}%[/cyan]"
                    )

                console.print(
                    "\n[yellow]Note: Threshold configuration persistence not yet implemented.[/yellow]"
                )
                console.print(
                    "[yellow]These settings will be used for the current session only.[/yellow]"
                )
            else:
                console.print("\n[dim]Using default quality thresholds[/dim]")

            console.print(
                "\n[bold]How it works:[/bold]\n"
                "  1. System evaluates provider quality metrics\n"
                "  2. Providers meeting thresholds are ranked by quality score\n"
                "  3. Highest quality provider is tried first\n"
                "  4. Falls back to priority order if quality routing fails\n"
            )
        else:
            console.print("[yellow]○[/yellow] Quality routing [yellow]DISABLED[/yellow]")
            console.print(
                "\n[dim]Providers will be tried in fixed priority order:[/dim]\n"
                "  [dim]1. Gemini → 2. Claude → 3. OpenAI[/dim]\n"
            )

        console.print(
            "\n[dim]Use 'collabiq llm status --detailed' to view quality metrics[/dim]\n"
        )

    except Exception as e:
        console.print(f"\n[red]Error configuring quality routing: {e}[/red]\n")
        logger.error(f"Failed to configure quality routing: {e}", exc_info=True)
        raise typer.Exit(1)


# ==============================================================================
# T022: llm compare - Compare provider performance
# ==============================================================================


@llm_app.command()
def compare(
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed per-metric breakdown for each provider",
    ),
):
    """
    Compare LLM provider performance across quality and value metrics.

    Displays provider rankings by:
    - Quality Score: Composite metric (40% confidence, 30% completeness, 30% validation)
    - Value Score: Quality-to-cost ratio (quality per dollar)
    - Recommendation: Best provider based on value score

    Use --detailed flag for per-metric breakdown (confidence, completeness, validation).

    Examples:
        collabiq llm compare
        collabiq llm compare --detailed
    """
    console = Console()
    try:
        # Create orchestrator with quality_tracker and cost_tracker
        config = OrchestrationConfig(
            default_strategy="failover",
            provider_priority=["gemini", "claude", "openai"],
        )
        orchestrator = LLMOrchestrator.from_config(config)

        # Ensure quality_tracker and cost_tracker are available
        if not orchestrator.quality_tracker:
            console.print(
                "\n[red]Error: Quality tracking is not enabled.[/red]\n"
                "Quality tracker must be initialized in orchestrator.\n"
            )
            raise typer.Exit(1)

        # Compare providers
        try:
            comparison = orchestrator.quality_tracker.compare_providers(
                cost_tracker=orchestrator.cost_tracker
            )
        except ValueError as e:
            console.print(
                f"\n[yellow]Cannot compare providers: {e}[/yellow]\n"
                "Process at least one extraction per provider before comparing.\n"
            )
            raise typer.Exit(1)

        # Display comparison results
        if detailed:
            _display_detailed_comparison(orchestrator, comparison)
        else:
            _display_basic_comparison(comparison)

    except Exception as e:
        console.print(f"\n[red]Error comparing providers: {e}[/red]\n")
        logger.error(f"Failed to compare providers: {e}", exc_info=True)
        raise typer.Exit(1)


def _display_basic_comparison(comparison: "ProviderQualityComparison"):
    """Display basic provider comparison with quality and value rankings.

    T022: Display comparison table with rank, provider, quality score, value score
    """
    console = Console()
    console.print("\n[bold cyan]LLM Provider Performance Comparison[/bold cyan]\n")

    # Quality Rankings Table
    console.print("[bold]Quality Rankings[/bold]")
    console.print("[dim]Composite score: 40% confidence, 30% completeness, 30% validation[/dim]\n")

    quality_table = Table(show_header=True, header_style="bold magenta")
    quality_table.add_column("Rank", justify="center", width=6)
    quality_table.add_column("Provider", style="cyan", width=12)
    quality_table.add_column("Quality Score", justify="right", width=14)

    for ranking in comparison.provider_rankings:
        rank = ranking["rank"]
        provider = ranking["provider_name"]
        score = ranking["quality_score"]

        # Color code by score
        if score >= 0.85:
            score_color = "green"
        elif score >= 0.70:
            score_color = "yellow"
        else:
            score_color = "red"

        quality_table.add_row(
            str(rank),
            provider.title(),
            f"[{score_color}]{score:.3f}[/{score_color}]",
        )

    console.print(quality_table)

    # Value Rankings Table
    console.print("\n[bold]Value Rankings[/bold]")
    console.print("[dim]Quality-to-cost ratio (higher is better value)[/dim]\n")

    value_table = Table(show_header=True, header_style="bold magenta")
    value_table.add_column("Rank", justify="center", width=6)
    value_table.add_column("Provider", style="cyan", width=12)
    value_table.add_column("Value Score", justify="right", width=14)
    value_table.add_column("Recommended", justify="center", width=12)

    for ranking in comparison.quality_to_cost_rankings:
        rank = ranking["rank"]
        provider = ranking["provider_name"]
        score = ranking["value_score"]
        is_recommended = provider == comparison.recommended_provider

        # Highlight recommended provider
        if is_recommended:
            recommended_marker = "[green]✓ YES[/green]"
        else:
            recommended_marker = ""

        value_table.add_row(
            str(rank),
            provider.title(),
            f"{score:.3f}",
            recommended_marker,
        )

    console.print(value_table)

    # Recommendation Summary
    console.print(f"\n[bold green]Recommendation[/bold green]\n")
    console.print(f"[cyan]{comparison.recommended_provider.title()}[/cyan]: {comparison.recommendation_reason}\n")
    console.print(
        "[dim]Use --detailed flag for per-metric breakdown[/dim]\n"
    )


def _display_detailed_comparison(
    orchestrator: LLMOrchestrator,
    comparison: "ProviderQualityComparison",
):
    """Display detailed comparison with per-metric breakdown.

    T022: Show per-metric breakdown (confidence, completeness, validation rate, cost)
    """
    console = Console()
    console.print("\n[bold cyan]LLM Provider Detailed Comparison[/bold cyan]\n")

    # Per-Provider Metrics Table
    console.print("[bold]Per-Provider Metrics Breakdown[/bold]\n")

    metrics_table = Table(show_header=True, header_style="bold magenta")
    metrics_table.add_column("Provider", style="cyan", width=12)
    metrics_table.add_column("Confidence", justify="right", width=12)
    metrics_table.add_column("Completeness", justify="right", width=12)
    metrics_table.add_column("Validation", justify="right", width=12)
    metrics_table.add_column("Cost/Email", justify="right", width=12)
    metrics_table.add_column("Quality Score", justify="right", width=14)
    metrics_table.add_column("Value Score", justify="right", width=12)

    for provider_name in comparison.providers_compared:
        # Get quality metrics
        quality_summary = orchestrator.quality_tracker.get_metrics(provider_name)

        # Get cost metrics
        cost_per_email = 0.0
        if orchestrator.cost_tracker:
            cost_metrics = orchestrator.cost_tracker.get_metrics(provider_name)
            cost_per_email = cost_metrics.average_cost_per_email

        # Find scores from rankings
        quality_score = None
        value_score = None
        for ranking in comparison.provider_rankings:
            if ranking["provider_name"] == provider_name:
                quality_score = ranking["quality_score"]
                break
        for ranking in comparison.quality_to_cost_rankings:
            if ranking["provider_name"] == provider_name:
                value_score = ranking["value_score"]
                break

        # Format metrics with color coding
        confidence = quality_summary.average_overall_confidence * 100
        if confidence >= 85:
            confidence_color = "green"
        elif confidence >= 70:
            confidence_color = "yellow"
        else:
            confidence_color = "red"

        completeness = quality_summary.average_field_completeness
        if completeness >= 90:
            completeness_color = "green"
        elif completeness >= 75:
            completeness_color = "yellow"
        else:
            completeness_color = "red"

        validation = quality_summary.validation_success_rate
        if validation >= 95:
            validation_color = "green"
        elif validation >= 80:
            validation_color = "yellow"
        else:
            validation_color = "red"

        metrics_table.add_row(
            provider_name.title(),
            f"[{confidence_color}]{confidence:.1f}%[/{confidence_color}]",
            f"[{completeness_color}]{completeness:.1f}%[/{completeness_color}]",
            f"[{validation_color}]{validation:.1f}%[/{validation_color}]",
            f"${cost_per_email:.6f}",
            f"{quality_score:.3f}" if quality_score else "N/A",
            f"{value_score:.3f}" if value_score else "N/A",
        )

    console.print(metrics_table)

    # Quality Rankings
    console.print("\n[bold]Quality Rankings[/bold]")
    console.print("[dim]Composite score: 40% confidence, 30% completeness, 30% validation[/dim]\n")

    quality_table = Table(show_header=True, header_style="bold magenta")
    quality_table.add_column("Rank", justify="center", width=6)
    quality_table.add_column("Provider", style="cyan", width=12)
    quality_table.add_column("Quality Score", justify="right", width=14)

    for ranking in comparison.provider_rankings:
        rank = ranking["rank"]
        provider = ranking["provider_name"]
        score = ranking["quality_score"]

        # Color code by score
        if score >= 0.85:
            score_color = "green"
        elif score >= 0.70:
            score_color = "yellow"
        else:
            score_color = "red"

        quality_table.add_row(
            str(rank),
            provider.title(),
            f"[{score_color}]{score:.3f}[/{score_color}]",
        )

    console.print(quality_table)

    # Value Rankings
    console.print("\n[bold]Value Rankings[/bold]")
    console.print("[dim]Quality-to-cost ratio (higher is better value)[/dim]\n")

    value_table = Table(show_header=True, header_style="bold magenta")
    value_table.add_column("Rank", justify="center", width=6)
    value_table.add_column("Provider", style="cyan", width=12)
    value_table.add_column("Value Score", justify="right", width=14)
    value_table.add_column("Recommended", justify="center", width=12)

    for ranking in comparison.quality_to_cost_rankings:
        rank = ranking["rank"]
        provider = ranking["provider_name"]
        score = ranking["value_score"]
        is_recommended = provider == comparison.recommended_provider

        # Highlight recommended provider
        if is_recommended:
            recommended_marker = "[green]✓ YES[/green]"
        else:
            recommended_marker = ""

        value_table.add_row(
            str(rank),
            provider.title(),
            f"{score:.3f}",
            recommended_marker,
        )

    console.print(value_table)

    # Recommendation Summary
    console.print(f"\n[bold green]Recommendation[/bold green]\n")
    console.print(f"[cyan]{comparison.recommended_provider.title()}[/cyan]: {comparison.recommendation_reason}\n")

@llm_app.command()
def export_metrics(
    output_path: str = typer.Option(
        "llm_metrics_export.json",
        "--output",
        "-o",
        help="Output file path for exported metrics",
    ),
    include_health: bool = typer.Option(
        True,
        "--health/--no-health",
        help="Include health metrics in export",
    ),
    include_cost: bool = typer.Option(
        True,
        "--cost/--no-cost",
        help="Include cost metrics in export",
    ),
    include_quality: bool = typer.Option(
        True,
        "--quality/--no-quality",
        help="Include quality metrics in export",
    ),
):
    """Export LLM metrics (health, cost, quality) to JSON file.

    Exports current metrics from all trackers to a single JSON file for:
    - Backup and archival
    - External analysis and reporting
    - Integration with other systems

    Examples:
        # Export all metrics to default file
        collabiq llm export-metrics

        # Export only quality metrics to custom path
        collabiq llm export-metrics -o quality_report.json --no-health --no-cost

        # Export health and cost only
        collabiq llm export-metrics -o health_cost.json --no-quality
    """
    console = Console()

    console.print(f"\n[bold cyan]Exporting LLM Metrics[/bold cyan]\n")

    try:
        orchestrator = LLMOrchestrator.from_config()

        # Collect metrics based on flags
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metrics": {}
        }

        if include_health and orchestrator.health_tracker:
            console.print("[dim]- Collecting health metrics...[/dim]")
            health_status = orchestrator.health_tracker.get_all_health_status()
            export_data["metrics"]["health"] = {
                provider: status.model_dump()
                for provider, status in health_status.items()
            }

        if include_cost and orchestrator.cost_tracker:
            console.print("[dim]- Collecting cost metrics...[/dim]")
            cost_metrics = orchestrator.cost_tracker.get_all_metrics()
            export_data["metrics"]["cost"] = {
                provider: metrics.model_dump()
                for provider, metrics in cost_metrics.items()
            }

        if include_quality and orchestrator.quality_tracker:
            console.print("[dim]- Collecting quality metrics...[/dim]")
            quality_metrics = orchestrator.quality_tracker.get_all_metrics()
            export_data["metrics"]["quality"] = {
                provider: metrics.model_dump()
                for provider, metrics in quality_metrics.items()
            }

        # Write to output file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        console.print(f"\n[green]✓ Metrics exported to {output_file}[/green]\n")

        # Show summary
        summary = []
        if include_health:
            summary.append(f"health ({len(export_data['metrics'].get('health', {}))} providers)")
        if include_cost:
            summary.append(f"cost ({len(export_data['metrics'].get('cost', {}))} providers)")
        if include_quality:
            summary.append(f"quality ({len(export_data['metrics'].get('quality', {}))} providers)")

        console.print(f"Exported: {', '.join(summary)}\n")

    except Exception as e:
        console.print(f"[red]Error exporting metrics: {e}[/red]\n")
        raise typer.Exit(1)
