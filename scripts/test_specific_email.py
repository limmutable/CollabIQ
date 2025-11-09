#!/usr/bin/env python3
"""Test extraction with a specific email ID.

Usage:
    python test_specific_email.py --email-id "your_email_id"
    python test_specific_email.py --email-id "test_001" --text "어제 신세계와..."
    python test_specific_email.py --email-id "test_001" --file path/to/email.txt
    python test_specific_email.py --email-id "test_001" --quality-routing
"""

import argparse
import json
import sys
from pathlib import Path

from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Test extraction with specific email ID")
    parser.add_argument("--email-id", required=True, help="Email ID to use for extraction")
    parser.add_argument("--text", help="Email text to process (inline)")
    parser.add_argument("--file", help="Path to file containing email text")
    parser.add_argument(
        "--strategy",
        choices=["failover", "consensus", "best_match"],
        default="failover",
        help="Orchestration strategy to use (default: failover)",
    )
    parser.add_argument(
        "--quality-routing",
        action="store_true",
        help="Enable quality-based routing (default: disabled)",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "claude", "openai"],
        help="Force specific provider (overrides priority)",
    )
    parser.add_argument(
        "--company-context",
        help="Optional company context for matching",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save extraction results to data/extractions/",
    )
    parser.add_argument(
        "--show-metrics",
        action="store_true",
        help="Show quality metrics after extraction",
    )

    args = parser.parse_args()

    # Get email text
    if args.text:
        email_text = args.text
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {args.file}[/red]")
            sys.exit(1)
        email_text = file_path.read_text()
    else:
        # Default sample email
        email_text = """
어제 신세계와 본봄 킥오프 했는데
결과 공유 받아서 전달 드릴게요!

프랙시스 강승현 대표와 만나기로 했는데,
그 때 이야기해도 되겠죠?

감사합니다.
임정민 드림
"""
        console.print("[yellow]No email text provided, using default sample[/yellow]")

    console.print(f"\n[bold cyan]Testing Extraction with Email ID: {args.email_id}[/bold cyan]\n")

    # Configure orchestrator
    provider_priority = ["gemini", "claude", "openai"]
    if args.provider:
        # Put specified provider first
        provider_priority = [args.provider] + [p for p in provider_priority if p != args.provider]

    config = OrchestrationConfig(
        default_strategy=args.strategy,
        provider_priority=provider_priority,
        enable_quality_routing=args.quality_routing,
    )

    console.print(f"Strategy: [cyan]{args.strategy}[/cyan]")
    console.print(f"Quality Routing: [cyan]{'ENABLED' if args.quality_routing else 'DISABLED'}[/cyan]")
    console.print(f"Provider Priority: [cyan]{', '.join(provider_priority)}[/cyan]\n")

    # Create orchestrator
    orchestrator = LLMOrchestrator.from_config(config)

    # Display email text
    console.print("[bold]Email Text:[/bold]")
    console.print(f"[dim]{email_text.strip()[:200]}{'...' if len(email_text) > 200 else ''}[/dim]\n")

    # Extract entities
    try:
        console.print("[yellow]Extracting entities...[/yellow]")
        entities = orchestrator.extract_entities(
            email_text=email_text,
            email_id=args.email_id,
            strategy=args.strategy,
            company_context=args.company_context,
        )

        # Display results
        console.print("\n[bold green]✓ Extraction Successful![/bold green]\n")

        # Results table
        results_table = Table(show_header=True, header_style="bold magenta")
        results_table.add_column("Field", style="cyan", width=20)
        results_table.add_column("Value", style="white", width=40)
        results_table.add_column("Confidence", justify="right", width=12)

        fields = [
            ("Email ID", args.email_id, None),
            ("Person in Charge", entities.person_in_charge, entities.confidence.person),
            ("Startup Name", entities.startup_name, entities.confidence.startup),
            ("Partner Org", entities.partner_org, entities.confidence.partner),
            ("Details", entities.details, entities.confidence.details),
            ("Date", str(entities.date) if entities.date else None, entities.confidence.date),
        ]

        for field_name, value, confidence in fields:
            if confidence is not None:
                # Format confidence with color
                conf_pct = confidence * 100
                if conf_pct >= 85:
                    conf_color = "green"
                elif conf_pct >= 70:
                    conf_color = "yellow"
                else:
                    conf_color = "red"
                conf_display = f"[{conf_color}]{conf_pct:.1f}%[/{conf_color}]"
            else:
                conf_display = "N/A"

            results_table.add_row(
                field_name,
                str(value) if value else "[dim]None[/dim]",
                conf_display,
            )

        console.print(results_table)

        # Field completeness
        field_count = sum(
            1
            for v in [
                entities.person_in_charge,
                entities.startup_name,
                entities.partner_org,
                entities.details,
                entities.date,
            ]
            if v is not None
        )
        completeness = (field_count / 5) * 100

        console.print(f"\n[bold]Field Completeness:[/bold] {field_count}/5 ({completeness:.0f}%)")

        # Average confidence
        avg_confidence = (
            entities.confidence.person
            + entities.confidence.startup
            + entities.confidence.partner
            + entities.confidence.details
            + entities.confidence.date
        ) / 5
        console.print(f"[bold]Average Confidence:[/bold] {avg_confidence:.2%}\n")

        # Save to file if requested
        if args.save:
            from datetime import datetime

            output_dir = Path("data/extractions/test")
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"{timestamp}_{args.email_id}.json"

            output_data = {
                "email_id": args.email_id,
                "person_in_charge": entities.person_in_charge,
                "startup_name": entities.startup_name,
                "partner_org": entities.partner_org,
                "details": entities.details,
                "date": str(entities.date) if entities.date else None,
                "confidence": {
                    "person": entities.confidence.person,
                    "startup": entities.confidence.startup,
                    "partner": entities.confidence.partner,
                    "details": entities.confidence.details,
                    "date": entities.confidence.date,
                },
                "extracted_at": timestamp,
                "strategy_used": args.strategy,
                "quality_routing_enabled": args.quality_routing,
            }

            output_file.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
            console.print(f"[green]✓[/green] Results saved to: {output_file}")

        # Show quality metrics if requested
        if args.show_metrics:
            console.print("\n[bold]Current Quality Metrics:[/bold]\n")

            quality_metrics = orchestrator.quality_tracker.get_all_metrics()

            metrics_table = Table(show_header=True, header_style="bold magenta")
            metrics_table.add_column("Provider", style="cyan", width=12)
            metrics_table.add_column("Extractions", justify="right", width=12)
            metrics_table.add_column("Avg Confidence", justify="right", width=14)
            metrics_table.add_column("Completeness", justify="right", width=12)

            for provider_name, metrics in quality_metrics.items():
                if metrics.total_extractions > 0:
                    metrics_table.add_row(
                        provider_name.title(),
                        str(metrics.total_extractions),
                        f"{metrics.average_overall_confidence:.2%}",
                        f"{metrics.average_field_completeness:.1f}%",
                    )

            console.print(metrics_table)
            console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Extraction Failed:[/red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
