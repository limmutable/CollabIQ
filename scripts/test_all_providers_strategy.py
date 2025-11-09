#!/usr/bin/env python3
"""Test the new all_providers strategy.

This script demonstrates the all_providers strategy which:
1. Calls ALL providers in parallel
2. Records quality metrics for ALL providers (not just the selected one)
3. Selects best result based on configured criteria

This is the recommended strategy for production use as it continuously
collects quality data from all providers to enable quality-based routing.
"""

from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig
from rich.console import Console
from rich.table import Table

console = Console()

# Sample email
SAMPLE_EMAIL = """어제 신세계와 본봄 킥오프 했는데
결과 공유 받아서 전달 드릴게요!

프랙시스 강승현 대표와 만나기로 했는데,
그 때 이야기해도 되겠죠?

감사합니다.
임정민 드림"""

console.print("\n[bold cyan]Testing all_providers Strategy[/bold cyan]\n")
console.print("This strategy calls ALL providers and collects metrics from all.\n")

# Create orchestrator with all_providers strategy
config = OrchestrationConfig(
    default_strategy="all_providers",
    provider_priority=["gemini", "claude", "openai"],
    enable_quality_routing=True,  # Use quality-based selection
)

orchestrator = LLMOrchestrator.from_config(config)

console.print("[yellow]Extracting with all_providers strategy...[/yellow]\n")

try:
    # Extract entities (will call ALL providers)
    entities = orchestrator.extract_entities(
        email_text=SAMPLE_EMAIL,
        email_id="test_all_providers_001",
    )

    # Display result
    console.print("[bold green]✓ Extraction Complete![/bold green]\n")
    console.print("[bold]Extracted Entities:[/bold]")
    console.print(f"  Person: {entities.person_in_charge}")
    console.print(f"  Startup: {entities.startup_name}")
    console.print(f"  Partner: {entities.partner_org}")
    console.print(f"  Details: {entities.details[:50]}...")
    console.print(f"  Avg Confidence: {(entities.confidence.person + entities.confidence.startup + entities.confidence.partner + entities.confidence.details + entities.confidence.date) / 5:.2%}\n")

    # Show quality metrics for ALL providers
    console.print("[bold]Quality Metrics (All Providers):[/bold]\n")

    quality_metrics = orchestrator.quality_tracker.get_all_metrics()

    if quality_metrics:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Provider", style="cyan", width=12)
        table.add_column("Extractions", justify="right", width=12)
        table.add_column("Avg Confidence", justify="right", width=14)
        table.add_column("Completeness", justify="right", width=12)

        for provider_name, metrics in quality_metrics.items():
            if metrics.total_extractions > 0:
                table.add_row(
                    provider_name.title(),
                    str(metrics.total_extractions),
                    f"{metrics.average_overall_confidence:.2%}",
                    f"{metrics.average_field_completeness:.1f}%",
                )

        console.print(table)
        console.print("\n[green]✓ Metrics collected from all providers![/green]\n")
    else:
        console.print("[yellow]No metrics available yet[/yellow]\n")

except Exception as e:
    console.print(f"[red]Error: {e}[/red]\n")
    import traceback

    traceback.print_exc()
