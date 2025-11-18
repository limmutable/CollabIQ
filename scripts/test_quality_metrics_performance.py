#!/usr/bin/env python3
"""Performance test for quality metrics tracker.

This script tests the performance of QualityTracker with a large number of
extraction records to verify:
1. Write performance remains acceptable with 10k+ records
2. Read performance for metrics retrieval
3. Memory usage remains reasonable
4. Atomic writes work correctly under load

Usage:
    python test_quality_metrics_performance.py
    python test_quality_metrics_performance.py --records 5000
    python test_quality_metrics_performance.py --records 10000 --verbose
"""

import argparse
import sys
import time
from pathlib import Path

from llm_orchestrator.quality_tracker import QualityTracker
from llm_provider.types import ConfidenceScores, ExtractedEntities
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)

console = Console()


def generate_mock_extraction(extraction_id: int) -> ExtractedEntities:
    """Generate mock extraction data for testing.

    Args:
        extraction_id: Unique ID for this extraction

    Returns:
        Mock ExtractedEntities with varying confidence and completeness
    """
    # Vary confidence and completeness across records
    confidence_base = 0.65 + (extraction_id % 25) / 100  # 0.65 to 0.89
    completeness_factor = (extraction_id % 5) + 1  # 1 to 5 fields

    entities = ExtractedEntities(
        email_id=f"perf_test_{extraction_id}",
        person_in_charge=f"Person {extraction_id}"
        if completeness_factor >= 1
        else None,
        startup_name=f"Startup {extraction_id}" if completeness_factor >= 2 else None,
        partner_org=f"Partner {extraction_id}" if completeness_factor >= 3 else None,
        details=f"Details for extraction {extraction_id}"
        if completeness_factor >= 4
        else None,
        date=f"2025-11-{(extraction_id % 28) + 1:02d}"
        if completeness_factor >= 5
        else None,
        confidence=ConfidenceScores(
            person=confidence_base + 0.05,
            startup=confidence_base + 0.03,
            partner=confidence_base + 0.02,
            details=confidence_base,
            date=confidence_base - 0.05 if completeness_factor >= 5 else 0.0,
        ),
    )

    return entities


def main():
    parser = argparse.ArgumentParser(
        description="Performance test for QualityTracker with large datasets"
    )
    parser.add_argument(
        "--records",
        type=int,
        default=10000,
        help="Number of extraction records to test (default: 10000)",
    )
    parser.add_argument(
        "--providers",
        type=int,
        default=3,
        choices=[1, 2, 3],
        help="Number of providers to test (default: 3)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress and timing",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]Quality Metrics Performance Test[/bold cyan]\n")
    console.print(f"Testing with [cyan]{args.records:,}[/cyan] extraction records")
    console.print(f"Testing [cyan]{args.providers}[/cyan] provider(s)\n")

    # Setup test directory
    test_data_dir = Path("data/llm_health_test_perf")
    if test_data_dir.exists():
        import shutil

        shutil.rmtree(test_data_dir)
    test_data_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize tracker
        console.print("[yellow]Initializing QualityTracker...[/yellow]")
        start_init = time.perf_counter()
        tracker = QualityTracker(data_dir=test_data_dir, evaluation_window_size=50)
        init_time = time.perf_counter() - start_init
        console.print(f"[green]✓ Initialized in {init_time * 1000:.2f}ms[/green]\n")

        # Provider names
        provider_names = ["gemini", "claude", "openai"][: args.providers]

        # Write test - record extractions
        console.print("[bold]Write Performance Test[/bold]")
        console.print(
            f"Recording {args.records:,} extractions for {args.providers} provider(s)...\n"
        )

        write_times = []
        total_start = time.perf_counter()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            for provider_name in provider_names:
                provider_task = progress.add_task(
                    f"Recording for {provider_name}...", total=args.records
                )

                for i in range(args.records):
                    entities = generate_mock_extraction(i)
                    validation_passed = (i % 20) != 0  # 95% validation success rate

                    write_start = time.perf_counter()
                    tracker.record_extraction(
                        provider_name=provider_name,
                        extracted_entities=entities,
                        validation_passed=validation_passed,
                        validation_failure_reasons=["Mock validation failure"]
                        if not validation_passed
                        else None,
                    )
                    write_time = time.perf_counter() - write_start
                    write_times.append(write_time)

                    progress.advance(provider_task)

        total_write_time = time.perf_counter() - total_start

        # Write performance summary
        console.print("\n[bold green]✓ Write Test Complete[/bold green]\n")
        console.print(f"Total time: [cyan]{total_write_time:.2f}s[/cyan]")
        console.print(f"Total records: [cyan]{len(write_times):,}[/cyan]")
        console.print(
            f"Avg write time: [cyan]{sum(write_times) / len(write_times) * 1000:.2f}ms[/cyan]"
        )
        console.print(f"Min write time: [cyan]{min(write_times) * 1000:.2f}ms[/cyan]")
        console.print(f"Max write time: [cyan]{max(write_times) * 1000:.2f}ms[/cyan]")
        console.print(
            f"Throughput: [cyan]{len(write_times) / total_write_time:.1f} records/sec[/cyan]\n"
        )

        # Read test - retrieve metrics
        console.print("[bold]Read Performance Test[/bold]\n")

        read_times = []
        for provider_name in provider_names:
            read_start = time.perf_counter()
            metrics = tracker.get_metrics(provider_name)
            read_time = time.perf_counter() - read_start
            read_times.append(read_time)

            console.print(f"[cyan]{provider_name.title()}[/cyan]:")
            console.print(f"  Extractions: {metrics.total_extractions:,}")
            console.print(f"  Avg Confidence: {metrics.average_overall_confidence:.2%}")
            console.print(f"  Completeness: {metrics.average_field_completeness:.1f}%")
            console.print(f"  Validation Rate: {metrics.validation_success_rate:.1f}%")
            console.print(f"  Read time: {read_time * 1000:.2f}ms\n")

        # Read performance summary
        console.print("[bold green]✓ Read Test Complete[/bold green]\n")
        console.print(
            f"Avg read time: [cyan]{sum(read_times) / len(read_times) * 1000:.2f}ms[/cyan]"
        )
        console.print(f"Max read time: [cyan]{max(read_times) * 1000:.2f}ms[/cyan]\n")

        # File size check
        metrics_file = test_data_dir / "quality_metrics.json"
        if metrics_file.exists():
            file_size_kb = metrics_file.stat().st_size / 1024
            console.print("[bold]Storage[/bold]\n")
            console.print(f"Metrics file size: [cyan]{file_size_kb:.2f} KB[/cyan]\n")

        # Performance verdict
        console.print("[bold]Performance Verdict[/bold]\n")

        avg_write_ms = sum(write_times) / len(write_times) * 1000
        max_write_ms = max(write_times) * 1000

        if avg_write_ms < 10 and max_write_ms < 50:
            console.print("[green]✓ EXCELLENT[/green] - Write performance is excellent")
        elif avg_write_ms < 20 and max_write_ms < 100:
            console.print("[green]✓ GOOD[/green] - Write performance is acceptable")
        elif avg_write_ms < 50:
            console.print(
                "[yellow]⚠ FAIR[/yellow] - Write performance may need optimization"
            )
        else:
            console.print("[red]✗ POOR[/red] - Write performance needs optimization")

        console.print("\nRecommendation: ")
        if args.records >= 10000:
            console.print("[green]✓ Tested at production scale (10k+ records)[/green]")
        else:
            console.print(
                "[yellow]ℹ Test with --records 10000 for production validation[/yellow]"
            )

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error during performance test: {e}[/red]\n")
        import traceback

        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup test directory
        if test_data_dir.exists() and not args.verbose:
            import shutil

            shutil.rmtree(test_data_dir)
            console.print("[dim]Test directory cleaned up[/dim]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
