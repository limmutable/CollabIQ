#!/usr/bin/env python3
"""
Run E2E Tests with Real Components

This script initializes all real MVP components and runs E2E tests that actually
write to the Notion database. Use with caution - this will create real entries!

Usage:
    # Process all emails (WILL WRITE TO NOTION!)
    uv run python scripts/run_e2e_with_real_components.py --all

    # Process single email for testing
    uv run python scripts/run_e2e_with_real_components.py --email-id <ID>

Safety:
    - Requires explicit --confirm flag to actually write to Notion
    - Use --dry-run to test without writing
    - Creates entries in production Notion database
    - Use cleanup script after testing
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.email_receiver.gmail_receiver import GmailReceiver
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.models.classification_service import ClassificationService
from src.notion_integrator.integrator import NotionIntegrator
from src.notion_integrator.writer import NotionWriter
from src.e2e_test.runner import E2ERunner
from src.e2e_test.report_generator import ReportGenerator


def load_test_email_ids(email_ids_file: str = "data/e2e_test/test_email_ids.json") -> list[str]:
    """Load test email IDs from JSON file"""
    path = Path(email_ids_file)

    if not path.exists():
        print(f"ERROR: Email IDs file not found: {email_ids_file}")
        print("Run email selection script first:")
        print("  uv run python scripts/select_test_emails.py --all")
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        test_emails = json.load(f)

    email_ids = [email["email_id"] for email in test_emails]
    return email_ids


def initialize_components():
    """Initialize all real MVP components"""
    print("Initializing real MVP components...")

    # Explicitly load .env file first (pydantic_settings not always reliable in all environments)
    from dotenv import load_dotenv
    load_dotenv(override=True)

    # Load settings
    settings = get_settings()

    # 1. Gmail Receiver
    print("  - GmailReceiver...")
    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))
    token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "token.json"))

    if not credentials_path.exists():
        print(f"ERROR: Gmail credentials not found: {credentials_path}")
        sys.exit(1)

    gmail_receiver = GmailReceiver(
        credentials_path=credentials_path,
        token_path=token_path,
    )
    gmail_receiver.connect()

    # 2. Gemini Adapter
    print("  - GeminiAdapter...")
    gemini_api_key = settings.get_secret_or_env("GEMINI_API_KEY")
    if not gemini_api_key:
        print("ERROR: GEMINI_API_KEY not found")
        sys.exit(1)

    gemini_adapter = GeminiAdapter(
        api_key=gemini_api_key,
        model=settings.gemini_model,
    )

    # 3. Notion Integrator
    print("  - NotionIntegrator...")
    notion_api_key = settings.get_secret_or_env("NOTION_API_KEY")
    if not notion_api_key:
        print("ERROR: NOTION_API_KEY not found in .env file")
        sys.exit(1)

    notion_integrator = NotionIntegrator(api_key=notion_api_key)

    # 4. Classification Service
    print("  - ClassificationService...")
    collabiq_db_id = settings.get_notion_collabiq_db_id()
    if not collabiq_db_id:
        print("ERROR: NOTION_DATABASE_ID_COLLABIQ not found in environment")
        sys.exit(1)

    classification_service = ClassificationService(
        notion_integrator=notion_integrator,
        gemini_adapter=gemini_adapter,
        collabiq_db_id=collabiq_db_id,
    )

    # 5. Notion Writer
    print("  - NotionWriter...")
    notion_writer = NotionWriter(
        notion_integrator=notion_integrator,
        collabiq_db_id=collabiq_db_id,
        duplicate_behavior="skip",  # Skip duplicates by default
    )

    print("✓ All components initialized successfully\n")

    return {
        "gmail_receiver": gmail_receiver,
        "gemini_adapter": gemini_adapter,
        "classification_service": classification_service,
        "notion_writer": notion_writer,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run E2E tests with real components (WRITES TO NOTION!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This script writes to the production Notion database!

Examples:
  # Dry-run (no actual writes)
  %(prog)s --all --dry-run

  # Process all emails (REQUIRES --confirm!)
  %(prog)s --all --confirm

  # Process single email
  %(prog)s --email-id msg_001 --confirm
        """,
    )

    # Email selection
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

    # Safety flags
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm that you want to write to Notion (REQUIRED for actual writes)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - no actual writes to Notion",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed error report",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation prompt (use with caution)",
    )

    args = parser.parse_args()

    # Safety check
    if not args.dry_run and not args.confirm:
        print("ERROR: Must use --confirm flag to write to Notion, or --dry-run for testing")
        print("\nThis script WILL CREATE ENTRIES in the production Notion database!")
        print("Use --confirm only if you understand this and want to proceed.")
        print("\nFor testing without writes, use: --dry-run")
        sys.exit(1)

    # Warn about production writes
    if args.confirm and not args.dry_run:
        print("=" * 70)
        print("⚠️  WARNING: PRODUCTION WRITE MODE")
        print("=" * 70)
        print("This will create REAL entries in your Notion database!")
        print("Remember to run cleanup script after testing:")
        print("  uv run python scripts/cleanup_test_entries.py")
        print("=" * 70)
        print()

        if not args.yes:
            response = input("Type 'YES' to continue: ").strip()
            if response != "YES":
                print("Cancelled.")
                sys.exit(0)
        else:
            print("⚠️  Skipping confirmation prompt (--yes flag provided)")
        print()

    # Initialize components
    try:
        components = initialize_components()
    except Exception as e:
        print(f"ERROR: Failed to initialize components: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Initialize E2E runner with real components
    print("Initializing E2E runner with real components...")
    runner = E2ERunner(
        gmail_receiver=components["gmail_receiver"],
        gemini_adapter=components["gemini_adapter"],
        classification_service=components["classification_service"],
        notion_writer=components["notion_writer"],
        test_mode=args.dry_run,  # Use test_mode only for dry-run
    )

    # Load email IDs
    if args.all:
        print("Loading test email IDs...")
        email_ids = load_test_email_ids()
        print(f"Processing {len(email_ids)} emails...\n")
    else:
        email_ids = [args.email_id]
        print(f"Processing single email: {args.email_id}\n")

    # Run E2E tests
    print("Running E2E tests...")
    print("=" * 70)
    test_run = runner.run_tests(email_ids, test_mode=args.dry_run)

    # Generate reports
    print("\nGenerating reports...")
    report_gen = ReportGenerator()

    summary = report_gen.generate_summary(test_run)
    summary_path = Path(f"data/e2e_test/reports/{test_run.run_id}_summary.md")
    summary_path.write_text(summary, encoding="utf-8")

    if args.report:
        error_report = report_gen.generate_error_report(test_run.run_id)
        error_path = Path(f"data/e2e_test/reports/{test_run.run_id}_errors.md")
        error_path.write_text(error_report, encoding="utf-8")
        print(f"Error report: {error_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("Test Run Complete")
    print("=" * 70)
    print(f"Run ID: {test_run.run_id}")
    print(f"Emails Processed: {test_run.emails_processed}")
    print(f"Success: {test_run.success_count} ({test_run.success_count / test_run.emails_processed * 100:.1f}%)")
    print(f"Failures: {test_run.failure_count}")
    print(f"Errors: {test_run.error_summary}")
    print(f"\nSummary: {summary_path}")

    if args.dry_run:
        print("\n[DRY-RUN MODE] No actual writes were performed")
    else:
        print("\n✅ Entries created in Notion database")
        print("Remember to clean up test entries:")
        print("  uv run python scripts/cleanup_test_entries.py --dry-run")
        print("  uv run python scripts/cleanup_test_entries.py")

    print("=" * 70)

    # Exit code
    success_rate = test_run.success_count / test_run.emails_processed
    if success_rate >= 0.95 and test_run.error_summary.get("critical", 0) == 0:
        sys.exit(0)
    else:
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
