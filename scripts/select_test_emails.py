#!/usr/bin/env python3
"""
Email Selection Script for E2E Testing

Fetches all emails from collab@signite.co inbox and creates test_email_ids.json

Usage:
    uv run python scripts/select_test_emails.py --all
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.email_receiver.gmail_receiver import GmailReceiver
from src.e2e_test.models import TestEmailMetadata, SelectionReason


def main():
    parser = argparse.ArgumentParser(
        description="Select test emails from collab@signite.co inbox"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch ALL emails from inbox (currently <10 emails)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/e2e_test/test_email_ids.json",
        help="Output file path (default: data/e2e_test/test_email_ids.json)",
    )

    args = parser.parse_args()

    if not args.all:
        print("ERROR: --all flag is required")
        print("Usage: uv run python scripts/select_test_emails.py --all")
        sys.exit(1)

    print("Fetching emails from collab@signite.co inbox...")

    try:
        # Initialize Gmail receiver
        receiver = GmailReceiver()

        # Fetch all emails from inbox (using existing method)
        # Assuming GmailReceiver.fetch_emails() retrieves from configured inbox
        emails = receiver.fetch_emails(max_results=100)  # Fetch up to 100 (we have <10)

        print(f"Found {len(emails)} emails in inbox")

        if len(emails) == 0:
            print("WARNING: No emails found in inbox")
            print("Ensure collab@signite.co has emails to test")
            sys.exit(1)

        # Create test email metadata list
        test_emails = []
        for email in emails:
            # Detect if email contains Korean text
            has_korean = any(
                "\uac00" <= char <= "\ud7a3"  # Hangul syllables range
                for char in (email.get("subject", "") + email.get("body", ""))
            )

            # Create metadata
            metadata = TestEmailMetadata(
                email_id=email.get("id", "unknown"),
                subject=email.get("subject", "No Subject"),
                received_date=email.get("date", "unknown"),
                collaboration_type=None,  # Will be detected during processing
                has_korean_text=has_korean,
                selection_reason=SelectionReason.STRATIFIED_SAMPLE,
                notes=f"Selected from inbox (all available emails)",
            )

            test_emails.append(metadata.model_dump())

        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to JSON file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(test_emails, f, indent=2, ensure_ascii=False)

        print(f"\nSuccessfully wrote {len(test_emails)} email metadata to {args.output}")
        print(f"  - Emails with Korean text: {sum(1 for e in test_emails if e['has_korean_text'])}")
        print(f"  - Emails without Korean: {sum(1 for e in test_emails if not e['has_korean_text'])}")
        print("\nNext step: Run E2E tests with:")
        print(f"  uv run python scripts/run_e2e_tests.py --all")

    except Exception as e:
        print(f"ERROR: Failed to fetch emails: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
