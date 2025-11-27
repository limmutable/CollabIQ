#!/usr/bin/env python3
"""
Main CLI for E2E Testing

Production CLI with argparse for flexible test execution. Supports running
tests with all emails, single email, or resuming interrupted runs. Now includes
multi-LLM orchestration and quality-based routing.

Generates consolidated test report with format: YYYYMMDD_HHMMSS-e2e_test.md

Usage:
    # Process all emails from test_email_ids.json (failover strategy)
    uv run python scripts/run_e2e_tests.py --all

    # Process with all providers strategy (collects metrics from all LLMs)
    uv run python scripts/run_e2e_tests.py --all --strategy all_providers

    # Enable quality-based routing
    uv run python scripts/run_e2e_tests.py --all --quality-routing

    # Process single email by ID with consensus strategy
    uv run python scripts/run_e2e_tests.py --email-id msg_001 --strategy consensus

    # Resume interrupted test run
    uv run python scripts/run_e2e_tests.py --resume 20251105_143000
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.e2e_test.runner import E2ERunner
from src.e2e_test.detailed_report_generator import DetailedReportGenerator


def load_test_email_ids(
    email_ids_file: str = "data/e2e_test/test_email_ids.json",
) -> list[str]:
    """Load test email IDs from JSON file"""
    path = Path(email_ids_file)

    if not path.exists():
        print(f"ERROR: Email IDs file not found: {email_ids_file}")
        print("Run email selection script first:")
        print("  uv run python scripts/select_test_emails.py --all")
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        test_emails = json.load(f)

    # Extract email_ids from metadata
    email_ids = [email["email_id"] for email in test_emails]

    return email_ids


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run E2E tests for MVP pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all emails (default: failover strategy)
  %(prog)s --all

  # Process with all providers strategy (collects metrics from ALL LLMs)
  %(prog)s --all --strategy all_providers

  # Enable quality-based routing
  %(prog)s --all --quality-routing

  # Process single email with consensus strategy
  %(prog)s --email-id msg_001 --strategy consensus

  # Resume interrupted run
  %(prog)s --resume 20251105_143000

Multi-LLM Strategies:
  failover       - Try providers sequentially (fastest, default)
  consensus      - Query multiple providers, use majority vote
  best_match     - Query all providers, select highest confidence
  all_providers  - Query ALL providers, collect metrics from all (recommended)
        """,
    )

    # Mutually exclusive group for run mode
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all emails from test_email_ids.json",
    )
    group.add_argument(
        "--email-id",
        type=str,
        metavar="EMAIL_ID",
        help="Process single email by ID",
    )
    group.add_argument(
        "--resume",
        type=str,
        metavar="RUN_ID",
        help="Resume interrupted test run by run ID",
    )

    # Optional arguments
    parser.add_argument(
        "--email-ids-file",
        type=str,
        default="data/e2e_test/test_email_ids.json",
        help="Path to test email IDs file (default: data/e2e_test/test_email_ids.json)",
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        default=True,
        help="Run in test mode (default: True)",
    )

    parser.add_argument(
        "--production-mode",
        action="store_false",
        dest="test_mode",
        help="Run in production mode (use real components)",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default="failover",
        choices=["failover", "consensus", "best_match", "all_providers"],
        help="LLM orchestration strategy (default: failover)",
    )

    parser.add_argument(
        "--quality-routing",
        action="store_true",
        help="Enable quality-based provider selection",
    )

    args = parser.parse_args()

    # Initialize runner with multi-LLM support
    print("Initializing E2E runner...")
    print(f"  Strategy: {args.strategy}")
    print(f"  Quality routing: {args.quality_routing}")
    print(f"  Test mode: {args.test_mode}")

    runner = E2ERunner(
        gmail_receiver=None,  # Components will be initialized based on test_mode
        llm_orchestrator=None,  # Will be auto-initialized with config
        classification_service=None,
        notion_writer=None,
        test_mode=args.test_mode,
        orchestration_strategy=args.strategy,
        enable_quality_routing=args.quality_routing,
    )

    # Initialize report generator
    report_gen = DetailedReportGenerator()

    # Run tests based on mode
    test_run = None

    if args.resume:
        # Resume interrupted run
        print(f"Resuming test run: {args.resume}")
        try:
            test_run = asyncio.run(runner.resume_test_run(args.resume))
            print(f"Resumed test run {args.resume}")
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    elif args.email_id:
        # Single email
        print(f"Processing single email: {args.email_id}")
        test_run = asyncio.run(runner.run_tests([args.email_id], test_mode=args.test_mode))

    elif args.all:
        # All emails
        print("Loading test email IDs...")
        email_ids = load_test_email_ids(args.email_ids_file)

        if len(email_ids) == 0:
            print("ERROR: No test email IDs found in file")
            sys.exit(1)

        print(f"Processing {len(email_ids)} emails...")
        test_run = asyncio.run(runner.run_tests(email_ids, test_mode=args.test_mode))

    # Generate consolidated report
    if test_run:
        # Print summary to console
        print("\n" + "=" * 70)
        print("Test Run Summary")
        print("=" * 70)
        print(f"Run ID: {test_run.run_id}")
        print(f"Status: {test_run.status}")
        print(f"Emails Processed: {test_run.emails_processed}")
        print(
            f"Success: {test_run.success_count} ({test_run.success_count / test_run.emails_processed * 100:.1f}%)"
        )
        print(f"Failures: {test_run.failure_count}")
        print(f"Errors: {test_run.error_summary}")

        # Show quality metrics if available
        quality_metrics = runner.get_quality_metrics_summary()
        if quality_metrics:
            print("\n" + "=" * 70)
            print("Quality Metrics Summary")
            print("=" * 70)
            for provider, metrics in quality_metrics.items():
                print(f"\n{provider.upper()}:")
                print(f"  Extractions: {metrics['total_extractions']}")
                print(f"  Avg Confidence: {metrics['avg_confidence']:.2%}")
                print(f"  Field Completeness: {metrics['field_completeness']:.1f}%")
                print(f"  Validation Rate: {metrics['validation_success_rate']:.1f}%")
            print("=" * 70)

        # Generate single consolidated report with format: YYYYMMDD_HHMMSS-e2e_test.md
        print("\nGenerating consolidated E2E test report...")
        report_path = report_gen.save_report(test_run.run_id)
        print(f"Report saved to: {report_path}")
        print("=" * 70)

        # Exit with appropriate status code
        if test_run.status == "completed":
            success_rate = test_run.success_count / test_run.emails_processed
            critical_errors = test_run.error_summary.get("critical", 0)

            if success_rate >= 0.95 and critical_errors == 0:
                print("\n✅ SUCCESS: All success criteria met (SC-001, SC-003)")
                sys.exit(0)
            else:
                print("\n❌ FAILURE: Success criteria not met")
                if success_rate < 0.95:
                    print(f"   - Success rate {success_rate:.1%} < 95% (SC-001)")
                if critical_errors > 0:
                    print(f"   - {critical_errors} critical errors detected (SC-003)")
                sys.exit(1)
        elif test_run.status == "interrupted":
            print("\n⚠️  WARNING: Test run was interrupted")
            print(f"   Resume with: {sys.argv[0]} --resume {test_run.run_id}")
            sys.exit(2)
        else:
            print("\n❌ ERROR: Test run failed")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
