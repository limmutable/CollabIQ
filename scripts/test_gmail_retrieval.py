#!/usr/bin/env python3
"""
Test Gmail Email Retrieval

This script tests Gmail API email retrieval with optional query filters.
Useful for verifying group alias filtering and OAuth authentication.

Usage:
    python scripts/test_gmail_retrieval.py
    python scripts/test_gmail_retrieval.py --query 'deliveredto:"collab@signite.co" subject:"test"'
    python scripts/test_gmail_retrieval.py --max-results 5
"""

import argparse
import sys
from pathlib import Path

# Add src to path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from email_receiver.gmail_receiver import GmailReceiver
from config.settings import Settings


def main():
    """Test Gmail email retrieval with optional filters."""
    parser = argparse.ArgumentParser(
        description="Test Gmail API email retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Retrieve latest 10 emails from collab@signite.co
  python scripts/test_gmail_retrieval.py

  # Search for specific subject
  python scripts/test_gmail_retrieval.py --query 'deliveredto:"collab@signite.co" subject:"Test"'

  # Limit to 5 results
  python scripts/test_gmail_retrieval.py --max-results 5
        """
    )
    parser.add_argument(
        "--query",
        default='to:collab@signite.co',
        help='Gmail search query (default: to:collab@signite.co)'
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of emails to retrieve (default: 10)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Gmail Email Retrieval Test")
    print("=" * 70)
    print()

    # Load settings
    settings = Settings()
    credentials_path = settings.get_gmail_credentials_path()
    token_path = settings.gmail_token_path

    print(f"Credentials: {credentials_path}")
    print(f"Token:       {token_path}")
    print(f"Query:       {args.query}")
    print(f"Max results: {args.max_results}")
    print()

    # Verify credentials and token exist
    if not credentials_path.exists():
        print("❌ ERROR: Credentials file not found!")
        print(f"Expected location: {credentials_path}")
        print()
        print("Run authentication first:")
        print("  uv run python scripts/authenticate_gmail.py")
        print()
        sys.exit(1)

    if not token_path.exists():
        print("❌ ERROR: Token file not found!")
        print()
        print("Run authentication first:")
        print("  uv run python scripts/authenticate_gmail.py")
        print()
        sys.exit(1)

    print("✓ Credentials and token found")
    print()

    try:
        # Create receiver and connect
        print("Connecting to Gmail API...")
        receiver = GmailReceiver(
            credentials_path=credentials_path,
            token_path=token_path
        )
        receiver.connect()
        print("✓ Connected successfully")
        print()

        # Fetch emails
        print(f"Fetching emails with query: {args.query}")
        print(f"Max results: {args.max_results}")
        print("-" * 70)

        emails = receiver.fetch_emails(
            query=args.query,
            max_emails=args.max_results
        )

        print()
        print("=" * 70)
        print(f"Found {len(emails)} email(s)")
        print("=" * 70)
        print()

        if len(emails) == 0:
            print("No emails found matching the query.")
            print()
            print("Tips:")
            print("  - Verify you sent a test email to collab@signite.co")
            print("  - Wait 1-2 minutes for Gmail indexing")
            print("  - Check if authenticated account is a member of the group")
            print()
            return

        # Display email summaries
        for i, email in enumerate(emails, 1):
            print(f"Email {i}:")
            print(f"  Message ID: {email.metadata.message_id}")
            print(f"  From:       {email.metadata.sender}")
            print(f"  Subject:    {email.metadata.subject}")
            print(f"  Received:   {email.metadata.received_at}")
            print(f"  Retrieved:  {email.metadata.retrieved_at}")
            print(f"  Has Attachments: {email.metadata.has_attachments}")
            print(f"  Body Length: {len(email.body)} characters")
            print()

        print("=" * 70)
        print("✅ Email retrieval test successful!")
        print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Email retrieval failed!")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("For troubleshooting help, see:")
        print("  docs/troubleshooting-gmail-api.md")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
