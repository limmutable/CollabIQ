#!/usr/bin/env python3
"""
Email Selection Script for E2E Testing

Fetches all emails from collab@signite.co inbox and creates test_email_ids.json

Usage:
    uv run python scripts/select_test_emails.py --all
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.email_receiver.gmail_receiver import GmailReceiver
from src.e2e_test.models import SelectionReason, E2ETestEmailMetadata


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
        # Get credentials paths from environment or defaults
        credentials_path = Path(
            os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        )
        token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "token.json"))

        # Check if credentials file exists
        if not credentials_path.exists():
            print(f"ERROR: Gmail credentials file not found: {credentials_path}")
            print(
                "Please ensure GOOGLE_CREDENTIALS_PATH is set or credentials.json exists"
            )
            sys.exit(1)

        # Initialize Gmail receiver
        receiver = GmailReceiver(
            credentials_path=credentials_path,
            token_path=token_path,
        )

        # Connect to Gmail API
        receiver.connect()

        # Fetch message list directly from Gmail API to get internal message IDs
        print("Fetching message list from Gmail API...")
        query_str = "to:collab@signite.co"
        results = (
            receiver.service.users()
            .messages()
            .list(userId="me", q=query_str, maxResults=100)
            .execute()
        )

        messages = results.get("messages", [])
        print(f"Found {len(messages)} emails in inbox")

        if len(messages) == 0:
            print("WARNING: No emails found in inbox")
            print("Ensure collab@signite.co has emails to test")
            sys.exit(1)

        # Create test email metadata list
        test_emails = []
        for msg in messages:
            # Fetch full message details to extract subject, date, and body
            try:
                msg_detail = (
                    receiver.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )

                # Extract subject from headers
                headers = msg_detail.get("payload", {}).get("headers", [])
                subject = next(
                    (h["value"] for h in headers if h["name"].lower() == "subject"),
                    "(No Subject)",
                )

                # Extract received date from internalDate (milliseconds since epoch)
                received_timestamp = int(msg_detail.get("internalDate", 0)) / 1000
                received_date = datetime.fromtimestamp(received_timestamp)

                # Extract body text (simplified - just get text/plain part)
                body_text = ""
                payload = msg_detail.get("payload", {})

                # Handle multipart messages
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part.get("mimeType") == "text/plain":
                            body_data = part.get("body", {}).get("data", "")
                            if body_data:
                                import base64

                                body_text = base64.urlsafe_b64decode(body_data).decode(
                                    "utf-8", errors="ignore"
                                )
                                break
                # Handle single-part messages
                elif payload.get("mimeType") == "text/plain":
                    body_data = payload.get("body", {}).get("data", "")
                    if body_data:
                        import base64

                        body_text = base64.urlsafe_b64decode(body_data).decode(
                            "utf-8", errors="ignore"
                        )

                # Detect if email contains Korean text
                has_korean = any(
                    "\uac00" <= char <= "\ud7a3"  # Hangul syllables range
                    for char in (subject + body_text)
                )

                # Create metadata using Gmail's internal message ID
                metadata = E2ETestEmailMetadata(
                    email_id=msg[
                        "id"
                    ],  # Use Gmail's internal message ID, not Message-ID header
                    subject=subject,
                    received_date=received_date.isoformat(),
                    collaboration_type=None,  # Will be detected during processing
                    has_korean_text=has_korean,
                    selection_reason=SelectionReason.STRATIFIED_SAMPLE,
                    notes=f"Selected from inbox (Gmail internal ID: {msg['id']})",
                )

                test_emails.append(metadata.model_dump(mode="json"))

            except Exception as e:
                print(f"WARNING: Failed to process message {msg['id']}: {e}")
                continue

        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to JSON file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(test_emails, f, indent=2, ensure_ascii=False)

        print(
            f"\nSuccessfully wrote {len(test_emails)} email metadata to {args.output}"
        )
        print(
            f"  - Emails with Korean text: {sum(1 for e in test_emails if e['has_korean_text'])}"
        )
        print(
            f"  - Emails without Korean: {sum(1 for e in test_emails if not e['has_korean_text'])}"
        )
        print("\nNext step: Run E2E tests with:")
        print("  uv run python scripts/run_e2e_tests.py --all")

    except Exception as e:
        print(f"ERROR: Failed to fetch emails: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
