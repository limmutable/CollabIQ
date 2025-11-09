#!/usr/bin/env python3
"""Populate quality metrics for all LLM providers.

This script tests all available providers (Gemini, Claude, OpenAI) with sample
emails to populate quality metrics. This is essential for:
1. Quality-based routing to have data for all providers
2. Provider comparison to show meaningful rankings
3. Testing the orchestration selection policy

Usage:
    python populate_quality_metrics.py
    python populate_quality_metrics.py --email-count 3
    python populate_quality_metrics.py --providers gemini claude
"""

import argparse
import sys
from pathlib import Path

from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Sample test emails (Korean + English)
SAMPLE_EMAILS = [
    {
        "id": "test_001",
        "text": """어제 신세계와 본봄 킥오프 했는데
결과 공유 받아서 전달 드릴게요!

프랙시스 강승현 대표와 만나기로 했는데,
그 때 이야기해도 되겠죠?

감사합니다.
임정민 드림""",
    },
    {
        "id": "test_002",
        "text": """안녕하세요,

지난주 웨이크 김동욱 대표님과 미팅했습니다.
신세계백화점과의 협업 건으로 PoC 진행 예정입니다.

다음주 월요일 오전 10시에 킥오프 미팅 잡혔습니다.

감사합니다.
박지성 드림""",
    },
    {
        "id": "test_003",
        "text": """Hi team,

Met with Praxis CEO Kang Seung-hyun yesterday.
Discussed potential collaboration with Shinsegae Food.

They want to start a pilot project next month.
Will share detailed notes tomorrow.

Best regards,
Jeffrey Lim""",
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Populate quality metrics for all LLM providers"
    )
    parser.add_argument(
        "--email-count",
        type=int,
        default=len(SAMPLE_EMAILS),
        help=f"Number of test emails to process (max {len(SAMPLE_EMAILS)})",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["gemini", "claude", "openai"],
        default=["gemini", "claude", "openai"],
        help="Providers to test (default: all)",
    )
    parser.add_argument(
        "--show-results",
        action="store_true",
        help="Show detailed extraction results",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]Populating Quality Metrics for All Providers[/bold cyan]\n")
    console.print(f"Testing providers: [cyan]{', '.join(args.providers)}[/cyan]")
    console.print(f"Processing [cyan]{args.email_count}[/cyan] test emails\n")

    # Create orchestrator with failover strategy (to test one provider at a time)
    config = OrchestrationConfig(
        default_strategy="failover",
        provider_priority=args.providers,
        enable_quality_routing=False,  # Disable to force specific provider testing
    )

    orchestrator = LLMOrchestrator.from_config(config)

    # Test each provider with each email
    results = {}
    emails_to_process = SAMPLE_EMAILS[: args.email_count]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for provider in args.providers:
            results[provider] = []
            provider_task = progress.add_task(
                f"Testing {provider}...", total=len(emails_to_process)
            )

            for email in emails_to_process:
                try:
                    # Force specific provider by setting priority
                    config.provider_priority = [provider]
                    orchestrator.config = config

                    # Extract entities
                    entities = orchestrator.extract_entities(
                        email_text=email["text"],
                        email_id=email["id"],
                        strategy="failover",  # Use failover to test single provider
                    )

                    results[provider].append(
                        {
                            "email_id": email["id"],
                            "success": True,
                            "entities": entities,
                            "avg_confidence": (
                                entities.confidence.person
                                + entities.confidence.startup
                                + entities.confidence.partner
                                + entities.confidence.details
                                + entities.confidence.date
                            )
                            / 5,
                        }
                    )

                except Exception as e:
                    console.print(
                        f"[red]✗[/red] {provider} failed on {email['id']}: {e}"
                    )
                    results[provider].append(
                        {
                            "email_id": email["id"],
                            "success": False,
                            "error": str(e),
                        }
                    )

                progress.advance(provider_task)

    # Display results summary
    console.print("\n[bold green]✓ Processing Complete![/bold green]\n")

    # Summary table
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Provider", style="cyan", width=12)
    summary_table.add_column("Successful", justify="right", width=12)
    summary_table.add_column("Failed", justify="right", width=8)
    summary_table.add_column("Avg Confidence", justify="right", width=14)

    for provider, provider_results in results.items():
        successful = sum(1 for r in provider_results if r["success"])
        failed = sum(1 for r in provider_results if not r["success"])

        if successful > 0:
            avg_conf = sum(
                r["avg_confidence"] for r in provider_results if r["success"]
            ) / successful
            avg_conf_str = f"{avg_conf:.2%}"
        else:
            avg_conf_str = "N/A"

        summary_table.add_row(
            provider.title(),
            str(successful),
            str(failed) if failed > 0 else "-",
            avg_conf_str,
        )

    console.print(summary_table)

    # Show detailed results if requested
    if args.show_results:
        console.print("\n[bold]Detailed Extraction Results:[/bold]\n")

        for provider, provider_results in results.items():
            console.print(f"[bold cyan]{provider.upper()}[/bold cyan]")

            for result in provider_results:
                if result["success"]:
                    entities = result["entities"]
                    console.print(f"  Email: {result['email_id']}")
                    console.print(f"    Person: {entities.person_in_charge}")
                    console.print(f"    Startup: {entities.startup_name}")
                    console.print(f"    Partner: {entities.partner_org}")
                    console.print(f"    Details: {entities.details[:50]}...")
                    console.print(f"    Date: {entities.date}")
                    console.print(
                        f"    Avg Confidence: {result['avg_confidence']:.2%}\n"
                    )
                else:
                    console.print(f"  Email: {result['email_id']} - FAILED")
                    console.print(f"    Error: {result['error']}\n")

    # Show quality metrics after population
    console.print("\n[bold]Updated Quality Metrics:[/bold]\n")

    quality_metrics = orchestrator.quality_tracker.get_all_metrics()

    if not quality_metrics:
        console.print("[yellow]No quality metrics available yet.[/yellow]")
        return

    metrics_table = Table(show_header=True, header_style="bold magenta")
    metrics_table.add_column("Provider", style="cyan", width=12)
    metrics_table.add_column("Extractions", justify="right", width=12)
    metrics_table.add_column("Avg Confidence", justify="right", width=14)
    metrics_table.add_column("Completeness", justify="right", width=12)
    metrics_table.add_column("Validation Rate", justify="right", width=14)

    for provider_name, metrics in quality_metrics.items():
        if metrics.total_extractions > 0:
            metrics_table.add_row(
                provider_name.title(),
                str(metrics.total_extractions),
                f"{metrics.average_overall_confidence:.2%}",
                f"{metrics.average_field_completeness:.1f}%",
                f"{metrics.validation_success_rate:.1f}%",
            )

    console.print(metrics_table)

    # Show next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Run [cyan]collabiq llm compare --detailed[/cyan] to see rankings")
    console.print(
        "2. Enable quality routing: [cyan]collabiq llm set-quality-routing --enabled[/cyan]"
    )
    console.print(
        "3. Test routing: [cyan]collabiq llm test \"your email text\"[/cyan]\n"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)
