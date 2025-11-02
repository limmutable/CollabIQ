#!/usr/bin/env python3
"""
Gmail OAuth2 Authentication Script

This script triggers the OAuth2 authentication flow for Gmail API access.
It will open a browser window for you to authenticate with your Google account.

Usage:
    python scripts/authenticate_gmail.py

After successful authentication, a token.json file will be created in your project root.
"""

import sys
from pathlib import Path

# Add src to path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from email_receiver.gmail_receiver import GmailReceiver
from config.settings import Settings

def main():
    """Run Gmail OAuth2 authentication flow."""
    print("=" * 60)
    print("Gmail API Authentication")
    print("=" * 60)
    print()

    # Load settings
    settings = Settings()
    credentials_path = settings.get_gmail_credentials_path()

    print(f"Looking for credentials at: {credentials_path}")

    if not credentials_path.exists():
        print()
        print("❌ ERROR: Credentials file not found!")
        print()
        print(f"Expected location: {credentials_path}")
        print()
        print("Please follow the setup guide:")
        print("  1. Open docs/setup/gmail-oauth-setup.md")
        print("  2. Complete Part 1: Google Cloud Console Setup")
        print("  3. Download credentials.json to your project root")
        print()
        sys.exit(1)

    print("✓ Credentials file found")
    print()
    print("Starting OAuth2 authentication flow...")
    print("A browser window will open for you to authenticate.")
    print()

    try:
        # Create receiver instance with credentials and token paths
        receiver = GmailReceiver(
            credentials_path=credentials_path,
            token_path=settings.gmail_token_path
        )

        # Connect (this triggers the browser OAuth flow if no token exists)
        receiver.connect()

        print()
        print("=" * 60)
        print("✅ Authentication successful!")
        print("=" * 60)
        print()
        print(f"Token saved to: {settings.gmail_token_path}")
        print()
        print("You can now use the Gmail API to retrieve emails.")
        print("The token will be automatically refreshed when needed.")
        print()

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Authentication failed!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("For troubleshooting help, see:")
        print("  docs/setup/troubleshooting-gmail-api.md")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
