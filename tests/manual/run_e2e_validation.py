#!/usr/bin/env python3
"""
Manual E2E Validation Runner

Interactive CLI for manual testing with progress output. This script provides
a user-friendly interface for running E2E tests and viewing results.

Usage:
    uv run python tests/manual/run_e2e_validation.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from e2e_test.runner import E2ERunner
from e2e_test.report_generator import ReportGenerator


def print_header():
    """Print formatted header"""
    print("=" * 70)
    print("MVP E2E Pipeline Validation")
    print("=" * 70)
    print()


def print_section(title: str):
    """Print section divider"""
    print()
    print(f"{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def load_test_emails():
    """Load test email IDs from data/e2e_test/test_email_ids.json"""
    email_ids_file = Path("data/e2e_test/test_email_ids.json")

    if not email_ids_file.exists():
        print("ERROR: Test email IDs file not found")
        print()
        print("Please run the email selection script first:")
        print("  uv run python scripts/select_test_emails.py --all")
        print()
        sys.exit(1)

    with email_ids_file.open("r", encoding="utf-8") as f:
        test_emails = json.load(f)

    email_ids = [email["email_id"] for email in test_emails]

    if len(email_ids) == 0:
        print("ERROR: No test email IDs found in file")
        sys.exit(1)

    return email_ids, test_emails


def print_test_emails(test_emails):
    """Print test email summary"""
    print_section("Test Emails")
    print()
    print(f"Found {len(test_emails)} test emails:")
    print()

    for i, email in enumerate(test_emails, 1):
        has_korean = "✓" if email.get("has_korean_text", False) else "✗"
        print(f"  {i}. {email['email_id']}")
        print(f"     Subject: {email.get('subject', 'N/A')[:60]}")
        print(f"     Date: {email.get('received_date', 'N/A')}")
        print(f"     Korean text: {has_korean}")
        print()


def confirm_execution():
    """Prompt user for confirmation"""
    print_section("Confirmation")
    print()
    print("⚠️  This will process all emails through the complete MVP pipeline:")
    print("   1. Fetch email from Gmail")
    print("   2. Extract entities with Gemini")
    print("   3. Match companies and partners")
    print("   4. Classify collaboration type and intensity")
    print("   5. Write to Notion database (TEST MODE)")
    print("   6. Validate Notion entries")
    print()

    while True:
        response = input("Continue? (yes/no): ").strip().lower()

        if response == "yes":
            return True
        elif response == "no":
            return False
        else:
            print("Please enter 'yes' or 'no'")


def print_progress_bar(current: int, total: int, width: int = 50):
    """Print progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percent = progress * 100
    print(f"\r  Progress: [{bar}] {current}/{total} ({percent:.1f}%)", end="", flush=True)


def run_tests_with_progress(runner: E2ERunner, email_ids: list):
    """Run tests with progress output"""
    print_section("Processing Emails")
    print()
    print(f"Processing {len(email_ids)} emails...")
    print()

    # Run tests
    test_run = runner.run_tests(email_ids, test_mode=True)

    # Print final progress
    print_progress_bar(len(email_ids), len(email_ids))
    print()  # New line after progress bar

    return test_run


def print_results(test_run, report_path):
    """Print test results summary"""
    print()
    print_section("Test Results")
    print()

    # Calculate metrics
    success_rate = (
        (test_run.success_count / test_run.emails_processed * 100)
        if test_run.emails_processed > 0
        else 0.0
    )

    # Print summary
    print(f"  Run ID: {test_run.run_id}")
    print(f"  Status: {test_run.status}")
    print()
    print(f"  Emails Processed: {test_run.emails_processed}")
    print(f"  Success: {test_run.success_count} ({success_rate:.1f}%)")
    print(f"  Failures: {test_run.failure_count}")
    print()
    print("  Errors by Severity:")
    print(f"    Critical: {test_run.error_summary.get('critical', 0)}")
    print(f"    High: {test_run.error_summary.get('high', 0)}")
    print(f"    Medium: {test_run.error_summary.get('medium', 0)}")
    print(f"    Low: {test_run.error_summary.get('low', 0)}")
    print()

    # Success criteria assessment
    if success_rate >= 95:
        print("  ✅ SUCCESS CRITERIA MET: Success rate ≥95% (SC-001)")
    else:
        print(f"  ❌ SUCCESS CRITERIA NOT MET: Success rate {success_rate:.1f}% < 95% (SC-001)")

    if test_run.error_summary.get("critical", 0) == 0:
        print("  ✅ NO CRITICAL ERRORS (SC-003)")
    else:
        print(f"  ❌ CRITICAL ERRORS: {test_run.error_summary.get('critical', 0)} errors detected (SC-003)")

    print()
    print(f"  Report saved to: {report_path}")


def print_next_steps(test_run):
    """Print next steps"""
    print()
    print_section("Next Steps")
    print()

    success_rate = (
        (test_run.success_count / test_run.emails_processed * 100)
        if test_run.emails_processed > 0
        else 0.0
    )

    if success_rate >= 95 and test_run.error_summary.get("critical", 0) == 0:
        print("  1. Review detailed test report:")
        print(f"     cat data/e2e_test/reports/{test_run.run_id}_summary.md")
        print()
        print("  2. Manually verify Notion entries (SC-002):")
        print("     - Check that all required fields are populated")
        print("     - Verify Korean text preservation (SC-007)")
        print("     - Validate date formats and collaboration types")
        print()
        print("  3. Run cleanup script:")
        print("     uv run python scripts/cleanup_test_entries.py --dry-run")
        print("     uv run python scripts/cleanup_test_entries.py  # After verification")
    else:
        print("  1. Review error report:")
        print(f"     cat data/e2e_test/reports/{test_run.run_id}_errors.md")
        print()
        print("  2. Fix critical and high severity errors (SC-003, SC-004)")
        print()
        print("  3. Re-run E2E tests:")
        print("     uv run python tests/manual/run_e2e_validation.py")
        print()
        print("  4. Or run specific tests:")
        print("     pytest tests/e2e/test_full_pipeline.py -v")

    print()


def main():
    """Main entry point"""
    # Print header
    print_header()

    # Load test emails
    email_ids, test_emails = load_test_emails()

    # Print test email summary
    print_test_emails(test_emails)

    # Confirm execution
    if not confirm_execution():
        print()
        print("Cancelled by user.")
        sys.exit(0)

    # Initialize runner
    print()
    print("Initializing E2E runner...")
    runner = E2ERunner(
        gmail_receiver=None,  # Components will be mocked in test mode
        gemini_adapter=None,
        classification_service=None,
        notion_writer=None,
        test_mode=True,
    )

    # Run tests with progress
    test_run = run_tests_with_progress(runner, email_ids)

    # Generate report
    print()
    print("Generating report...")
    report_gen = ReportGenerator()
    summary = report_gen.generate_summary(test_run)

    # Save report
    report_path = Path(f"data/e2e_test/reports/{test_run.run_id}_summary.md")
    report_path.write_text(summary, encoding="utf-8")

    # Print results
    print_results(test_run, report_path)

    # Print next steps
    print_next_steps(test_run)

    # Footer
    print()
    print("=" * 70)
    print("E2E Validation Complete")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print()
        print()
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
