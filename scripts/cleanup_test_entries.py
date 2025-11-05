#!/usr/bin/env python3
"""
Cleanup Test Entries Script

Deletes Notion entries from production database that match test email IDs.
Uses email_id field to identify test entries created during E2E testing.

Safety Features:
- Dry-run mode (preview only, no deletion)
- Explicit confirmation required
- Filters by email_id from test set only
- Logs all deletions to audit trail

Usage:
    uv run python scripts/cleanup_test_entries.py                 # Interactive
    uv run python scripts/cleanup_test_entries.py --dry-run      # Preview only
    uv run python scripts/cleanup_test_entries.py --yes          # Skip confirmation
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.notion_integrator.notion_client_wrapper import NotionClientWrapper


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


def find_test_entries(notion_client: NotionClientWrapper, email_ids: list[str]) -> list[dict]:
    """Find all Notion entries matching test email IDs"""
    print("\nSearching for test entries in production database...")

    # Query Notion database for entries with matching email_ids
    # Assuming notion_client has method to query by email_id field
    test_entries = []

    for email_id in email_ids:
        try:
            # Query database for this email_id
            # Note: Actual implementation depends on NotionClientWrapper API
            entries = notion_client.query_by_email_id(email_id)
            test_entries.extend(entries)
        except Exception as e:
            print(f"  Warning: Failed to query email_id {email_id}: {e}")

    print(f"Found {len(test_entries)} test entries to delete")
    return test_entries


def preview_entries(entries: list[dict]):
    """Show preview of entries that will be deleted"""
    print("\n" + "=" * 70)
    print("PREVIEW: The following entries will be deleted:")
    print("=" * 70)

    for i, entry in enumerate(entries, 1):
        print(f"\n{i}. Entry ID: {entry.get('id', 'unknown')}")
        print(f"   Email ID: {entry.get('email_id', 'unknown')}")
        print(f"   Subject: {entry.get('subject', 'No subject')[:50]}")
        print(f"   Created: {entry.get('created_time', 'unknown')}")

    print("\n" + "=" * 70)
    print(f"TOTAL: {len(entries)} entries will be deleted")
    print("=" * 70)


def confirm_deletion() -> bool:
    """Prompt user for explicit confirmation"""
    print("\n⚠️  WARNING: This action will PERMANENTLY delete the entries above")
    print("⚠️  from the production CollabIQ database.")
    print()

    while True:
        response = input("Type 'yes' to confirm deletion, or 'no' to cancel: ").strip().lower()

        if response == "yes":
            return True
        elif response == "no":
            return False
        else:
            print("Please type 'yes' or 'no'")


def delete_entries(
    notion_client: NotionClientWrapper, entries: list[dict], audit_log_path: Path
) -> int:
    """Delete entries and log to audit trail"""
    print("\nDeleting entries...")

    deleted_count = 0
    audit_records = []

    for entry in entries:
        entry_id = entry.get("id")

        try:
            # Delete entry from Notion
            notion_client.delete_page(entry_id)

            print(f"  ✓ Deleted entry: {entry_id}")
            deleted_count += 1

            # Record deletion in audit log
            audit_records.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "deleted",
                    "entry_id": entry_id,
                    "email_id": entry.get("email_id", "unknown"),
                    "subject": entry.get("subject", "No subject"),
                }
            )

        except Exception as e:
            print(f"  ✗ Failed to delete entry {entry_id}: {e}")

    # Write audit log
    if audit_records:
        with audit_log_path.open("w", encoding="utf-8") as f:
            json.dump(audit_records, f, indent=2, ensure_ascii=False)

        print(f"\nAudit trail saved to: {audit_log_path}")

    return deleted_count


def main():
    parser = argparse.ArgumentParser(
        description="Delete test entries from production Notion database"
    )
    parser.add_argument(
        "--email-ids-file",
        type=str,
        default="data/e2e_test/test_email_ids.json",
        help="Path to test email IDs file (default: data/e2e_test/test_email_ids.json)",
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

    args = parser.parse_args()

    # Load test email IDs
    email_ids = load_test_email_ids(args.email_ids_file)

    if len(email_ids) == 0:
        print("ERROR: No test email IDs found in file")
        sys.exit(1)

    # Initialize Notion client
    try:
        notion_client = NotionClientWrapper()
    except Exception as e:
        print(f"ERROR: Failed to initialize Notion client: {e}")
        sys.exit(1)

    # Find test entries
    test_entries = find_test_entries(notion_client, email_ids)

    if len(test_entries) == 0:
        print("\n✓ No test entries found. Database is clean.")
        sys.exit(0)

    # Preview entries
    preview_entries(test_entries)

    # Dry-run mode: stop here
    if args.dry_run:
        print("\n[DRY-RUN MODE] No deletions performed")
        print("Remove --dry-run flag to actually delete entries")
        sys.exit(0)

    # Confirm deletion
    if not args.yes:
        if not confirm_deletion():
            print("\nCancelled. No entries deleted.")
            sys.exit(0)
    else:
        print("\n[SKIP CONFIRMATION] Proceeding with deletion...")

    # Delete entries
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audit_log_path = Path(f"data/e2e_test/cleanup_audit_{timestamp}.log")

    deleted_count = delete_entries(notion_client, test_entries, audit_log_path)

    print(f"\n{'='*70}")
    print(f"✓ Successfully deleted {deleted_count}/{len(test_entries)} entries")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
