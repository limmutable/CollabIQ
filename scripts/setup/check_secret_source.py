#!/usr/bin/env python3
"""Check which source your secrets are coming from (Infisical vs .env).

This script shows you:
1. Whether Infisical is enabled
2. Whether connection is active
3. Where each secret comes from

Usage:
    uv run python scripts/check_secret_source.py
"""

import logging
import sys
from pathlib import Path

# Setup logging to see detailed output
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.settings import get_settings


def main():
    """Check secret sources."""
    print("=" * 70)
    print("  🔍 Secret Source Checker")
    print("=" * 70)
    print()

    # Load settings
    settings = get_settings()

    # Show configuration
    print("📋 Configuration:")
    print(f"  - Infisical Enabled: {settings.infisical_enabled}")

    if settings.infisical_enabled:
        print(f"  - Infisical Host: {settings.infisical_host}")
        print(f"  - Project ID: {settings.infisical_project_id}")
        print(f"  - Environment: {settings.infisical_environment}")
        print(f"  - Cache TTL: {settings.infisical_cache_ttl}s")

        # Check connection
        client = settings.infisical_client
        if client and client.is_connected():
            print("  - Status: ✅ Connected to Infisical")
        else:
            print("  - Status: ⚠️  Not connected (will use .env)")
    else:
        print("  - Status: 📄 Using .env file only")

    print()
    print("-" * 70)
    print()

    # Test retrieving secrets
    print("🔑 Testing Secret Retrieval:")
    print()

    test_secrets = [
        "GEMINI_API_KEY",
        "NOTION_API_KEY",
        "GMAIL_CREDENTIALS_PATH",
    ]

    for secret_key in test_secrets:
        print(f"Retrieving '{secret_key}'...")
        try:
            value = settings.get_secret_or_env(secret_key)
            if value:
                value_preview = value[:30] + "..." if len(value) > 30 else value
                print(f"  ✓ Found: {value_preview}")
            else:
                print("  ⚠️  Not found")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()

    print("-" * 70)
    print()

    # Summary
    print("💡 Summary:")
    print()

    if settings.infisical_enabled:
        if settings.infisical_client and settings.infisical_client.is_connected():
            print("  Your application is using INFISICAL for secret management.")
            print("  Secrets are retrieved from Infisical API with .env fallback.")
            print()
            print("  Log messages show:")
            print("    - 'Retrieved from Infisical API' = Coming from Infisical ✓")
            print("    - 'Retrieved from cache' = Coming from Infisical cache ✓")
            print("    - 'falling back to .env' = Coming from .env file")
        else:
            print("  Infisical is ENABLED but NOT CONNECTED.")
            print("  All secrets are coming from .env file.")
            print()
            print("  To use Infisical:")
            print("    1. Set correct INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET")
            print("    2. Run: uv run python tests/manual/test_infisical_connection.py")
    else:
        print("  Your application is using .ENV FILE for secret management.")
        print("  All secrets are read directly from .env file.")
        print()
        print("  To enable Infisical:")
        print("    1. Set INFISICAL_ENABLED=true in .env")
        print(
            "    2. Configure Infisical credentials (see docs/setup/INFISICAL_SETUP.md)"
        )
        print("    3. Run: uv run python tests/manual/test_infisical_connection.py")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
