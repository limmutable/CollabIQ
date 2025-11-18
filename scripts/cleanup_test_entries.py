#!/usr/bin/env python3
"""
Cleanup Test Entries Script (Enhanced with T018)

Deletes Notion entries from test database that match test email IDs or test_run_id.
Uses robust cleanup mechanism with retry logic, verification, and error handling.

Safety Features:
- Dry-run mode (preview only, no deletion)
- Explicit confirmation required
- Filters by email_id or test_run_id only
- Retry logic with exponential backoff
- Post-cleanup verification
- Detailed audit logging

Usage:
    # Clean by test run ID
    uv run python scripts/cleanup_test_entries.py --test-run-id test-001

    # Clean by email IDs from file
    uv run python scripts/cleanup_test_entries.py --email-ids-file data/e2e_test/test_email_ids.json

    # Preview only (no deletion)
    uv run python scripts/cleanup_test_entries.py --test-run-id test-001 --dry-run

    # Skip confirmation prompt
    uv run python scripts/cleanup_test_entries.py --test-run-id test-001 --yes
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collabiq.test_utils.notion_cleanup import NotionTestCleanup


def load_test_email_ids(email_ids_file: str) -> list[str]:
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

    print(f"Loaded {len(email_ids)} test email IDs from {email_ids_file}")
    return email_ids


def confirm_deletion(entry_count: int) -> bool:
    """Prompt user for explicit confirmation"""
    print("\n" + "=" * 70)
    print(f"⚠️  WARNING: This will PERMANENTLY delete {entry_count} entries")
    print("⚠️  from the Notion test database.")
    print("=" * 70)
    print()

    while True:
        response = (
            input("Type 'yes' to confirm deletion, or 'no' to cancel: ").strip().lower()
        )

        if response == "yes":
            return True
        elif response == "no":
            return False
        else:
            print("Please type 'yes' or 'no'")


def main():
    parser = argparse.ArgumentParser(
        description="Delete test entries from Notion test database using robust cleanup mechanism"
    )
    parser.add_argument(
        "--test-run-id",
        type=str,
        help="Test run ID to filter entries (e.g., test-001)",
    )
    parser.add_argument(
        "--email-ids-file",
        type=str,
        help="Path to test email IDs file (e.g., data/e2e_test/test_email_ids.json)",
    )
    parser.add_argument(
        "--database-id",
        type=str,
        help="Notion database ID (uses NOTION_DATABASE_ID_COLLABIQ env var if not provided)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only, do not delete anything",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (use with caution)",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip post-cleanup verification",
    )

    args = parser.parse_args()

    # Validate arguments: need either test_run_id or email_ids_file
    if not args.test_run_id and not args.email_ids_file:
        print("ERROR: Must provide either --test-run-id or --email-ids-file")
        parser.print_help()
        sys.exit(1)

    # Get database ID from args or environment
    database_id = args.database_id or os.getenv("NOTION_DATABASE_ID_COLLABIQ")

    if not database_id:
        print(
            "ERROR: Database ID not provided. Set NOTION_DATABASE_ID_COLLABIQ env var or use --database-id"
        )
        sys.exit(1)

    # Load email IDs if provided
    email_ids = None
    if args.email_ids_file:
        email_ids = load_test_email_ids(args.email_ids_file)

        if len(email_ids) == 0:
            print("ERROR: No test email IDs found in file")
            sys.exit(1)

    # Initialize cleanup manager
    try:
        cleanup = NotionTestCleanup(
            database_id=database_id,
            test_run_id=args.test_run_id,
            email_ids=email_ids,
            max_retries=3,
            timeout_seconds=30,
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize cleanup manager: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("Notion Test Entry Cleanup")
    print("=" * 70)
    print(f"Database ID: {database_id}")
    if args.test_run_id:
        print(f"Test Run ID: {args.test_run_id}")
    if email_ids:
        print(f"Email IDs: {len(email_ids)} emails")
    print("=" * 70)

    # Find test entries (preview)
    print("\nSearching for test entries...")
    test_entries = cleanup.find_test_entries()

    if len(test_entries) == 0:
        print("\n✓ No test entries found. Database is clean.")
        sys.exit(0)

    # Preview entries
    print(f"\nFound {len(test_entries)} test entries:")
    for i, entry in enumerate(test_entries[:10], 1):  # Show first 10
        page_id = entry.get("id", "unknown")
        print(f"  {i}. Page ID: {page_id[:16]}...")

    if len(test_entries) > 10:
        print(f"  ... and {len(test_entries) - 10} more")

    # Dry-run mode: stop here
    if args.dry_run:
        print("\n[DRY-RUN MODE] No deletions performed")
        print("Remove --dry-run flag to actually delete entries")
        sys.exit(0)

    # Confirm deletion
    if not args.yes:
        if not confirm_deletion(len(test_entries)):
            print("\nCancelled. No entries deleted.")
            sys.exit(0)
    else:
        print("\n[SKIP CONFIRMATION] Proceeding with deletion...")

    # Perform cleanup with retry logic and verification
    print("\nStarting cleanup (with retry logic and verification)...")

    try:
        result = cleanup.cleanup_test_entries(
            verify=not args.no_verify, continue_on_error=True
        )

        # Print results
        print("\n" + "=" * 70)
        print("Cleanup Complete")
        print("=" * 70)
        print(f"✓ Successfully cleaned: {result.cleaned} entries")
        print(f"✗ Errors: {result.errors}")
        print(f"⏱  Duration: {result.duration:.1f}s")

        if not args.no_verify:
            if result.verified:
                print("✓ Verification: All entries removed")
            else:
                print("⚠️  Verification: Some entries may still exist")

        if result.failed_ids:
            print(f"\nFailed to delete {len(result.failed_ids)} entries:")
            for failed_id in result.failed_ids[:5]:  # Show first 5
                print(f"  - {failed_id}")
            if len(result.failed_ids) > 5:
                print(f"  ... and {len(result.failed_ids) - 5} more")

        # Save audit log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_log_path = Path(f"data/e2e_test/cleanup_audit_{timestamp}.json")
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        with audit_log_path.open("w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"\n📝 Audit log saved to: {audit_log_path}")
        print("=" * 70)

        # Exit with non-zero if there were errors
        if result.errors > 0:
            sys.exit(1)

    except Exception as e:
        print(f"\nERROR: Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
