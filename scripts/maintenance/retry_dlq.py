#!/usr/bin/env python3
"""Manual retry script for DLQ (Dead Letter Queue) entries.

This script allows manual retry of failed Notion write operations from the DLQ.

Usage:
    # Retry all DLQ entries
    uv run python scripts/retry_dlq.py --all

    # Retry specific DLQ file
    uv run python scripts/retry_dlq.py --file data/dlq/email-123_20251104_120000.json

    # Dry run (show what would be retried without actually retrying)
    uv run python scripts/retry_dlq.py --all --dry-run

Options:
    --all           Retry all DLQ entries in data/dlq/ directory
    --file PATH     Retry specific DLQ file by path
    --dry-run       Show what would be retried without actually retrying
    --help          Show this help message
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.infisical_client import InfisicalClient
from config.settings import Settings
from notion_integrator import NotionIntegrator, NotionWriter, DLQManager


async def retry_dlq_entries(
    dlq_files: list[str],
    notion_writer: NotionWriter,
    dlq_manager: DLQManager,
    dry_run: bool = False,
) -> dict:
    """Retry DLQ entries and return results summary.

    Args:
        dlq_files: List of DLQ file paths to retry
        notion_writer: NotionWriter instance for retrying writes
        dlq_manager: DLQManager instance for loading entries
        dry_run: If True, show what would be retried without actually retrying

    Returns:
        Dict with success/failure counts
    """
    results = {"total": len(dlq_files), "success": 0, "failed": 0, "errors": []}

    for i, file_path in enumerate(dlq_files, 1):
        print(f"\n[{i}/{results['total']}] Processing: {Path(file_path).name}")

        try:
            # Load DLQ entry
            dlq_entry = dlq_manager.load_dlq_entry(file_path)

            print(f"  Email ID: {dlq_entry.email_id}")
            print(f"  Failed at: {dlq_entry.failed_at}")
            print(f"  Retry count: {dlq_entry.retry_count}")
            print(
                f"  Error: {dlq_entry.error.get('error_type', 'Unknown')}: {dlq_entry.error.get('error_message', 'No message')}"
            )

            if dry_run:
                print("  [DRY RUN] Would retry this entry")
                results["success"] += 1
                continue

            # Attempt retry
            print("  Retrying write...")
            success = await dlq_manager.retry_failed_write(file_path, notion_writer)

            if success:
                print("  ✅ Retry succeeded - DLQ entry deleted")
                results["success"] += 1
            else:
                print("  ❌ Retry failed - retry_count incremented")
                results["failed"] += 1

        except Exception as e:
            print(f"  ❌ Error processing DLQ entry: {e}")
            results["failed"] += 1
            results["errors"].append({"file": file_path, "error": str(e)})

    return results


async def main():
    parser = argparse.ArgumentParser(
        description="Retry failed Notion write operations from DLQ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Retry all DLQ entries")
    group.add_argument("--file", type=str, help="Retry specific DLQ file by path")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be retried without actually retrying",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("DLQ Retry Script")
    print("=" * 80)
    print()

    # 1. Load secrets
    print("1. Loading secrets from Infisical...")
    settings = Settings()
    infisical = InfisicalClient(settings)

    notion_api_key = infisical.get_secret("NOTION_API_KEY")
    collabiq_db_id = infisical.get_secret("COLLABIQ_DB_ID")

    print("✅ Secrets loaded")
    print(f"   - Notion: ***{notion_api_key[-4:]}")
    print(f"   - CollabIQ DB: {collabiq_db_id}")
    print()

    # 2. Initialize services
    print("2. Initializing services...")
    notion = NotionIntegrator(api_key=notion_api_key)
    dlq_manager = DLQManager(dlq_dir="data/dlq")

    writer = NotionWriter(
        notion_integrator=notion,
        collabiq_db_id=collabiq_db_id,
        duplicate_behavior="skip",  # Skip duplicates for safety during retry
        dlq_manager=None,  # Don't create new DLQ entries during retry
    )

    print("✅ Services initialized")
    print()

    # 3. Get list of DLQ files to process
    if args.all:
        print("3. Loading all DLQ entries...")
        dlq_files = dlq_manager.list_dlq_entries()

        if not dlq_files:
            print("❌ No DLQ entries found")
            return 0

        print(f"✅ Found {len(dlq_files)} DLQ entries")
    else:
        print(f"3. Loading DLQ entry: {args.file}")
        file_path = Path(args.file)

        if not file_path.exists():
            print(f"❌ DLQ file not found: {args.file}")
            return 1

        dlq_files = [str(file_path)]
        print("✅ DLQ entry loaded")

    print()

    # 4. Retry DLQ entries
    if args.dry_run:
        print("4. DRY RUN - Showing what would be retried...")
    else:
        print("4. Retrying DLQ entries...")

    results = await retry_dlq_entries(dlq_files, writer, dlq_manager, args.dry_run)

    # 5. Print summary
    print()
    print("=" * 80)
    print("Retry Results Summary")
    print("=" * 80)
    print(f"Total entries processed: {results['total']}")
    print(f"✅ Successful retries: {results['success']}")
    print(f"❌ Failed retries: {results['failed']}")

    if results["errors"]:
        print()
        print("Errors encountered:")
        for error in results["errors"]:
            print(f"  - {error['file']}: {error['error']}")

    print()

    if args.dry_run:
        print("DRY RUN complete - no actual retries performed")
    elif results["failed"] > 0:
        print("Some retries failed. Failed entries remain in DLQ for future retry.")
        return 1
    else:
        print("All retries completed successfully!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
