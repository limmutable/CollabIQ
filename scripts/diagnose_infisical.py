#!/usr/bin/env python3
"""Diagnose Infisical configuration and suggest fixes.

This script helps troubleshoot Infisical secret management issues by:
1. Validating configuration
2. Testing connection
3. Listing available environments
4. Providing step-by-step fix instructions
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.config.settings import get_settings


def main():
    print("=" * 70)
    print("INFISICAL CONFIGURATION DIAGNOSTICS")
    print("=" * 70)

    settings = get_settings()

    # 1. Check if Infisical is enabled
    print("\n1. CONFIGURATION CHECK")
    print("-" * 70)
    print(f"   Infisical Enabled: {settings.infisical_enabled}")

    if not settings.infisical_enabled:
        print("\n   ℹ️  Infisical is disabled")
        print("   To enable: Set INFISICAL_ENABLED=true in .env")
        return

    print(f"   Host: {settings.infisical_host}")
    print(f"   Project ID: {settings.infisical_project_id}")
    print(f"   Environment: {settings.infisical_environment}")
    print(f"   Client ID: {settings.infisical_client_id[:20]}...")
    print(f"   Cache TTL: {settings.infisical_cache_ttl}s")

    # 2. Test authentication
    print("\n2. AUTHENTICATION TEST")
    print("-" * 70)

    if not settings.infisical_client:
        print("   ✗ Infisical client not initialized")
        return

    try:
        settings.infisical_client.authenticate()
        print("   ✓ Authentication successful!")
    except Exception as e:
        print(f"   ✗ Authentication failed: {e}")
        print("\n   📋 FIX STEPS:")
        print("   1. Go to https://app.infisical.com")
        print("   2. Navigate to your project settings")
        print("   3. Go to Machine Identities → Select your identity")
        print("   4. Generate new Universal Auth credentials")
        print("   5. Update INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET in .env")
        return

    # 3. Try to list secrets
    print("\n3. SECRET RETRIEVAL TEST")
    print("-" * 70)

    try:
        secrets = settings.infisical_client.get_all_secrets()
        print(f"   ✓ Found {len(secrets)} secrets in '{settings.infisical_environment}' environment")

        if secrets:
            print("\n   Secrets found:")
            for key in sorted(secrets.keys()):
                print(f"     - {key}")
        else:
            print("\n   ⚠️  No secrets found in this environment")
            print("\n   📋 FIX STEPS:")
            print(f"   1. Go to https://app.infisical.com")
            print(f"   2. Select your project (ID: {settings.infisical_project_id})")
            print(f"   3. Select environment: {settings.infisical_environment}")
            print("   4. Add secrets:")
            print("      - GEMINI_API_KEY")
            print("      - NOTION_API_KEY")
            print("      - NOTION_DATABASE_ID_COLLABIQ")
            print("      - NOTION_DATABASE_ID_COMPANIES")
            print("      - (and any other secrets from your .env file)")

    except Exception as e:
        error_msg = str(e)
        print(f"   ✗ Failed to list secrets: {error_msg}")

        if "404" in error_msg or "not found" in error_msg.lower():
            print("\n   📋 FIX STEPS:")
            print(f"   The environment '{settings.infisical_environment}' doesn't exist in your project.")
            print()
            print("   Option 1: Create the environment")
            print(f"   1. Go to https://app.infisical.com")
            print(f"   2. Select your project (ID: {settings.infisical_project_id})")
            print("   3. Go to Settings → Environments")
            print(f"   4. Create a new environment with slug: {settings.infisical_environment}")
            print()
            print("   Option 2: Use an existing environment")
            print("   1. Check what environments exist in your Infisical project")
            print("   2. Update INFISICAL_ENVIRONMENT in .env to match")
            print("      (common values: 'dev', 'development', 'prod', 'production')")
        else:
            print(f"\n   Unexpected error. Check your configuration.")

    # 4. Test individual secret retrieval
    print("\n4. INDIVIDUAL SECRET TEST")
    print("-" * 70)

    test_key = "GEMINI_API_KEY"
    try:
        value = settings.infisical_client.get_secret(test_key)
        print(f"   ✓ Retrieved {test_key}: {value[:20]}...")
    except Exception as e:
        print(f"   ℹ️  {test_key} not in Infisical, using .env fallback")

    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
