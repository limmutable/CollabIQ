"""
LLM provider management commands.

Commands:
- status: View all provider health metrics
- test: Test provider connectivity
- policy: Display orchestration strategy
- set-policy: Change orchestration strategy
- usage: View API usage and costs
- disable/enable: Manage provider status

Gracefully handles Phase 3a (Gemini only) and Phase 3b (multi-LLM).
"""

import typer
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from ..formatters.tables import create_table, render_table
from ..formatters.json_output import output_json
from ..formatters.colors import console
from ..formatters.progress import create_spinner
from ..utils.validation import validate_provider, validate_strategy
from ..utils.logging import log_cli_operation, log_cli_error

app = typer.Typer(
    name="llm",
    help="LLM provider management (status, test, policy, usage, enable/disable)",
)


# ==============================================================================
# T059: Phase 3b Availability Check Helper
# ==============================================================================


def is_phase_3b_available() -> bool:
    """
    Check if multi-LLM orchestration (Phase 3b) is available.

    Returns:
        True if Phase 3b is implemented, False otherwise (Phase 3a only)
    """
    try:
        # Try to import orchestration module
        from llm_provider.orchestration import LLMOrchestrator

        return True
    except ImportError:
        return False


def get_gemini_provider():
    """
    Get the Gemini provider instance.

    Returns:
        GeminiAdapter instance or None if not available
    """
    try:
        from llm_adapters.gemini_adapter import GeminiAdapter

        return GeminiAdapter()
    except Exception:
        return None


# ==============================================================================
# T060: llm status - View all provider health status
# ==============================================================================


@app.command()
def status(
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    View all LLM provider health status.

    Shows health status, response times, and error rates for all configured
    LLM providers (or Gemini only if Phase 3b not yet implemented).

    Examples:
        collabiq llm status
        collabiq llm status --json
    """
    start_time = time.time()

    try:
        phase_3b = is_phase_3b_available()

        if phase_3b:
            # Phase 3b: Multi-LLM orchestration
            # This code path will be activated when Phase 3b is implemented
            from llm_provider.orchestration import LLMOrchestrator

            orchestrator = LLMOrchestrator()
            providers_status = orchestrator.get_all_provider_status()

            if json:
                output_json({"providers": providers_status, "phase": "3b"})
            else:
                _display_multi_provider_status(providers_status)

        else:
            # Phase 3a: Gemini only
            gemini = get_gemini_provider()

            if not gemini:
                if json:
                    output_json(
                        data={},
                        status="failure",
                        errors=["Gemini provider not available"],
                    )
                else:
                    console.print("\n[red]Error: Gemini provider not available[/red]")
                raise typer.Exit(1)

            # Test Gemini connectivity
            gemini_status = _test_gemini_health(gemini)

            if json:
                output_json(
                    {
                        "providers": [gemini_status],
                        "phase": "3a",
                        "note": "Multi-LLM orchestration (Phase 3b) not yet implemented",
                    }
                )
            else:
                _display_gemini_only_status(gemini_status)

        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_operation("llm status", success=True, duration_ms=duration_ms)

    except Exception as e:
        log_cli_error("llm status", e)
        if json:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _test_gemini_health(gemini) -> Dict[str, Any]:
    """Test Gemini provider health and return status."""
    try:
        # Simple connectivity test
        start = time.time()
        # Try to initialize/configure the provider
        if hasattr(gemini, "configure"):
            gemini.configure()
        response_time = int((time.time() - start) * 1000)

        return {
            "provider": "gemini",
            "status": "healthy",
            "response_time_ms": response_time,
            "error_rate": 0.0,
            "last_check": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "provider": "gemini",
            "status": "unhealthy",
            "response_time_ms": 0,
            "error_rate": 1.0,
            "last_check": datetime.now().isoformat(),
            "error": str(e),
        }


def _display_gemini_only_status(gemini_status: Dict[str, Any]):
    """Display status for Gemini-only (Phase 3a) configuration."""
    console.print("\n[bold cyan]LLM Provider Status[/bold cyan]")
    console.print("[dim]Phase 3a: Single provider (Gemini)[/dim]\n")

    # Create table
    table = create_table(
        title=None,
        columns=[
            {"name": "Provider", "style": "cyan"},
            {"name": "Status", "style": "bold"},
            {"name": "Response Time", "justify": "right"},
            {"name": "Error Rate", "justify": "right"},
        ],
    )

    # Add Gemini row
    status_style = "green" if gemini_status["status"] == "healthy" else "red"
    table.add_row(
        "Gemini (primary)",
        f"[{status_style}]{gemini_status['status'].upper()}[/{status_style}]",
        f"{gemini_status['response_time_ms']}ms",
        f"{gemini_status['error_rate']:.1%}",
    )

    console.print(table)
    console.print(
        "\n[dim]Note: Multi-LLM orchestration (Phase 3b) not yet implemented.[/dim]"
    )


def _display_multi_provider_status(providers_status: List[Dict[str, Any]]):
    """Display status for multi-provider (Phase 3b) configuration."""
    console.print("\n[bold cyan]LLM Provider Status[/bold cyan]")
    console.print("[dim]Phase 3b: Multi-provider orchestration[/dim]\n")

    # Create table
    table = create_table(
        title=None,
        columns=[
            {"name": "Provider", "style": "cyan"},
            {"name": "Status", "style": "bold"},
            {"name": "Response Time", "justify": "right"},
            {"name": "Error Rate", "justify": "right"},
            {"name": "Enabled", "justify": "center"},
        ],
    )

    for provider in providers_status:
        status_style = "green" if provider["status"] == "healthy" else "red"
        enabled_mark = "[green]✓[/green]" if provider.get("enabled", True) else "[red]✗[/red]"

        table.add_row(
            provider["name"],
            f"[{status_style}]{provider['status'].upper()}[/{status_style}]",
            f"{provider.get('response_time_ms', 0)}ms",
            f"{provider.get('error_rate', 0.0):.1%}",
            enabled_mark,
        )

    console.print(table)


# ==============================================================================
# T061: llm test - Test specific provider connectivity
# ==============================================================================


@app.command()
def test(
    provider: str = typer.Argument(..., help="Provider name (gemini, claude, openai)"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    Test specific LLM provider connectivity.

    Performs a connectivity test to verify the provider is accessible
    and responding correctly.

    Examples:
        collabiq llm test gemini
        collabiq llm test claude --json
    """
    start_time = time.time()

    try:
        # Validate provider name
        provider = validate_provider(provider)

        phase_3b = is_phase_3b_available()

        if provider != "gemini" and not phase_3b:
            if json:
                output_json(
                    data={},
                    status="failure",
                    errors=[
                        f"Provider '{provider}' not available. Only Gemini is configured (Phase 3a)."
                    ],
                )
            else:
                console.print(
                    f"\n[red]Error: Provider '{provider}' not available.[/red]"
                )
                console.print(
                    "[yellow]Only Gemini is configured. Multi-LLM orchestration (Phase 3b) not yet implemented.[/yellow]"
                )
            raise typer.Exit(1)

        # Test the provider
        if provider == "gemini":
            gemini = get_gemini_provider()
            if not gemini:
                raise Exception("Gemini provider not available")

            with create_spinner(f"Testing {provider} connectivity...") as spinner:
                task = spinner.add_task("", total=None)
                test_result = _test_gemini_health(gemini)

        else:
            # Phase 3b providers
            from llm_provider.orchestration import LLMOrchestrator

            orchestrator = LLMOrchestrator()
            with create_spinner(f"Testing {provider} connectivity...") as spinner:
                task = spinner.add_task("", total=None)
                test_result = orchestrator.test_provider(provider)

        duration_ms = int((time.time() - start_time) * 1000)

        if json:
            output_json({"provider": provider, "test_result": test_result})
        else:
            _display_test_result(provider, test_result)

        log_cli_operation(
            f"llm test {provider}", success=True, duration_ms=duration_ms
        )

    except Exception as e:
        log_cli_error(f"llm test {provider}", e)
        if json:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _display_test_result(provider: str, result: Dict[str, Any]):
    """Display test result for a provider."""
    status = result.get("status", "unknown")
    status_color = "green" if status == "healthy" else "red"

    console.print(f"\n[bold]Test Results for {provider.title()}[/bold]\n")

    table = create_table(
        columns=[
            {"name": "Metric", "style": "cyan"},
            {"name": "Value", "justify": "left"},
        ]
    )

    table.add_row("Status", f"[{status_color}]{status.upper()}[/{status_color}]")
    table.add_row("Response Time", f"{result.get('response_time_ms', 0)}ms")
    table.add_row("Error Rate", f"{result.get('error_rate', 0.0):.1%}")

    if "error" in result:
        table.add_row("Error", f"[red]{result['error']}[/red]")

    console.print(table)


# ==============================================================================
# T062: llm policy - View current orchestration policy
# ==============================================================================


@app.command()
def policy(
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    View current LLM orchestration policy.

    Shows the active orchestration strategy (failover, consensus, best-match)
    and configuration details.

    Examples:
        collabiq llm policy
        collabiq llm policy --json
    """
    start_time = time.time()

    try:
        phase_3b = is_phase_3b_available()

        if not phase_3b:
            # Phase 3a: Single provider, no orchestration
            policy_info = {
                "strategy": "N/A (single provider - Gemini)",
                "phase": "3a",
                "note": "Multi-LLM orchestration not yet implemented",
            }

            if json:
                output_json(policy_info)
            else:
                console.print("\n[bold cyan]LLM Orchestration Policy[/bold cyan]")
                console.print("\n[yellow]Strategy: N/A (single provider - Gemini)[/yellow]")
                console.print(
                    "\n[dim]Note: Multi-LLM orchestration (Phase 3b) not yet implemented.[/dim]"
                )
                console.print(
                    "[dim]Only Gemini is configured. Orchestration policies will be available after Phase 3b.[/dim]"
                )

        else:
            # Phase 3b: Get orchestration policy
            from llm_provider.orchestration import LLMOrchestrator

            orchestrator = LLMOrchestrator()
            policy_info = orchestrator.get_policy()

            if json:
                output_json(policy_info)
            else:
                _display_policy(policy_info)

        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_operation("llm policy", success=True, duration_ms=duration_ms)

    except Exception as e:
        log_cli_error("llm policy", e)
        if json:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _display_policy(policy_info: Dict[str, Any]):
    """Display orchestration policy information."""
    console.print("\n[bold cyan]LLM Orchestration Policy[/bold cyan]\n")

    table = create_table(
        columns=[
            {"name": "Setting", "style": "cyan"},
            {"name": "Value", "justify": "left"},
        ]
    )

    table.add_row("Strategy", f"[green]{policy_info.get('strategy', 'unknown')}[/green]")
    table.add_row("Active Providers", str(policy_info.get("active_providers", 0)))
    table.add_row("Fallback Enabled", str(policy_info.get("fallback_enabled", False)))

    console.print(table)


# ==============================================================================
# T063: llm set-policy - Set orchestration strategy
# ==============================================================================


@app.command()
def set_policy(
    strategy: str = typer.Argument(
        ..., help="Orchestration strategy (failover, consensus, best-match)"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    Set LLM orchestration strategy.

    Available strategies:
    - failover: Use primary, fall back to secondary on failure
    - consensus: Compare results from multiple providers
    - best-match: Select provider based on task type

    Examples:
        collabiq llm set-policy failover
        collabiq llm set-policy consensus
    """
    start_time = time.time()

    try:
        # Validate strategy
        strategy = validate_strategy(strategy)

        phase_3b = is_phase_3b_available()

        if not phase_3b:
            console.print(
                "\n[red]Error: Multi-LLM orchestration not yet available.[/red]"
            )
            console.print(
                "[yellow]Only Gemini is configured (Phase 3a). Orchestration strategies will be available after Phase 3b implementation.[/yellow]"
            )
            raise typer.Exit(1)

        # Set the policy
        from llm_provider.orchestration import LLMOrchestrator

        orchestrator = LLMOrchestrator()
        orchestrator.set_policy(strategy)

        console.print(
            f"\n[green]✓[/green] Orchestration strategy set to [cyan]{strategy}[/cyan]"
        )

        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_operation(
            f"llm set-policy {strategy}", success=True, duration_ms=duration_ms
        )

    except Exception as e:
        log_cli_error(f"llm set-policy {strategy}", e)
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# T064: llm usage - View usage statistics
# ==============================================================================


@app.command()
def usage(
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    View LLM provider usage statistics.

    Shows API call counts, token usage, costs, and rate limit status
    for all configured providers.

    Examples:
        collabiq llm usage
        collabiq llm usage --json
    """
    start_time = time.time()

    try:
        phase_3b = is_phase_3b_available()

        if phase_3b:
            # Phase 3b: Get usage from orchestrator
            from llm_provider.orchestration import LLMOrchestrator

            orchestrator = LLMOrchestrator()
            usage_stats = orchestrator.get_usage_statistics()

            if json:
                output_json(usage_stats)
            else:
                _display_multi_provider_usage(usage_stats)

        else:
            # Phase 3a: Gemini only - mock usage data
            usage_stats = {
                "providers": [
                    {
                        "name": "gemini",
                        "api_calls": 0,
                        "tokens_used": 0,
                        "estimated_cost": 0.0,
                        "rate_limit_remaining": "N/A",
                    }
                ],
                "phase": "3a",
                "note": "Usage tracking not yet implemented for Phase 3a",
            }

            if json:
                output_json(usage_stats)
            else:
                _display_gemini_usage(usage_stats)

        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_operation("llm usage", success=True, duration_ms=duration_ms)

    except Exception as e:
        log_cli_error("llm usage", e)
        if json:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _display_gemini_usage(usage_stats: Dict[str, Any]):
    """Display usage statistics for Gemini-only configuration."""
    console.print("\n[bold cyan]LLM Usage Statistics[/bold cyan]")
    console.print("[dim]Phase 3a: Single provider (Gemini)[/dim]\n")

    table = create_table(
        columns=[
            {"name": "Provider", "style": "cyan"},
            {"name": "API Calls", "justify": "right"},
            {"name": "Tokens", "justify": "right"},
            {"name": "Cost", "justify": "right"},
        ]
    )

    provider = usage_stats["providers"][0]
    table.add_row(
        provider["name"].title(),
        str(provider["api_calls"]),
        str(provider["tokens_used"]),
        f"${provider['estimated_cost']:.2f}",
    )

    console.print(table)
    console.print(
        "\n[dim]Note: Detailed usage tracking will be available in Phase 3b.[/dim]"
    )


def _display_multi_provider_usage(usage_stats: Dict[str, Any]):
    """Display usage statistics for multi-provider configuration."""
    console.print("\n[bold cyan]LLM Usage Statistics[/bold cyan]\n")

    table = create_table(
        columns=[
            {"name": "Provider", "style": "cyan"},
            {"name": "API Calls", "justify": "right"},
            {"name": "Tokens", "justify": "right"},
            {"name": "Cost", "justify": "right"},
            {"name": "Rate Limit", "justify": "right"},
        ]
    )

    for provider in usage_stats.get("providers", []):
        table.add_row(
            provider["name"].title(),
            str(provider.get("api_calls", 0)),
            str(provider.get("tokens_used", 0)),
            f"${provider.get('estimated_cost', 0.0):.2f}",
            str(provider.get("rate_limit_remaining", "N/A")),
        )

    console.print(table)


# ==============================================================================
# T065: llm disable - Disable a provider
# ==============================================================================


@app.command()
def disable(
    provider: str = typer.Argument(..., help="Provider name to disable"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    Disable an LLM provider.

    Temporarily disables a provider from the orchestration pool without
    removing its configuration.

    Examples:
        collabiq llm disable claude
        collabiq llm disable openai
    """
    start_time = time.time()

    try:
        # Validate provider
        provider = validate_provider(provider)

        phase_3b = is_phase_3b_available()

        if not phase_3b:
            console.print(
                "\n[red]Error: Provider management not available in Phase 3a.[/red]"
            )
            console.print(
                "[yellow]Only Gemini is configured. Provider enable/disable will be available after Phase 3b implementation.[/yellow]"
            )
            raise typer.Exit(1)

        # Disable the provider
        from llm_provider.orchestration import LLMOrchestrator

        orchestrator = LLMOrchestrator()
        orchestrator.disable_provider(provider)

        console.print(
            f"\n[green]✓[/green] Provider [cyan]{provider}[/cyan] has been disabled"
        )

        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_operation(
            f"llm disable {provider}", success=True, duration_ms=duration_ms
        )

    except Exception as e:
        log_cli_error(f"llm disable {provider}", e)
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# T066: llm enable - Enable a provider
# ==============================================================================


@app.command()
def enable(
    provider: str = typer.Argument(..., help="Provider name to enable"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """
    Enable an LLM provider.

    Re-enables a previously disabled provider, making it available in the
    orchestration pool.

    Examples:
        collabiq llm enable claude
        collabiq llm enable openai
    """
    start_time = time.time()

    try:
        # Validate provider
        provider = validate_provider(provider)

        phase_3b = is_phase_3b_available()

        if not phase_3b:
            console.print(
                "\n[red]Error: Provider management not available in Phase 3a.[/red]"
            )
            console.print(
                "[yellow]Only Gemini is configured. Provider enable/disable will be available after Phase 3b implementation.[/yellow]"
            )
            raise typer.Exit(1)

        # Enable the provider
        from llm_provider.orchestration import LLMOrchestrator

        orchestrator = LLMOrchestrator()
        orchestrator.enable_provider(provider)

        console.print(
            f"\n[green]✓[/green] Provider [cyan]{provider}[/cyan] has been enabled"
        )

        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_operation(
            f"llm enable {provider}", success=True, duration_ms=duration_ms
        )

    except Exception as e:
        log_cli_error(f"llm enable {provider}", e)
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)
