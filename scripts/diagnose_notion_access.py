#!/usr/bin/env python3
"""Diagnostic script to troubleshoot Notion database access issues.

This script helps identify common Notion API integration problems:
1. Token format validation
2. Database connectivity
3. Permission issues
4. Property accessibility
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from notion_client import AsyncClient
from config.settings import get_settings


async def diagnose_notion_access():
    """Run comprehensive Notion access diagnostics."""
    settings = get_settings()

    print("=" * 80)
    print("NOTION API ACCESS DIAGNOSTICS")
    print("=" * 80)

    # Check 1: Token format
    print("\n[1] Token Format Check")
    api_key = settings.notion_api_key
    print(f"   Token prefix: {api_key[:4]}...")
    if api_key.startswith("ntn_"):
        print("   ✅ Using new token format (ntn_) - correct!")
    elif api_key.startswith("secret_"):
        print("   ⚠️  Using old token format (secret_) - still works but consider updating")
    else:
        print(f"   ❌ Unknown token format: {api_key[:10]}")

    # Check 2: Database IDs
    print("\n[2] Database Configuration")
    companies_db = settings.notion_database_id_companies
    collabiq_db = settings.notion_database_id_collabiq
    print(f"   Companies DB: {companies_db}")
    print(f"   CollabIQ DB:  {collabiq_db}")

    # Check 3: Try to connect and retrieve database
    print("\n[3] Database Connectivity Test")
    client = AsyncClient(auth=api_key)

    for db_name, db_id in [("Companies", companies_db), ("CollabIQ", collabiq_db)]:
        print(f"\n   Testing: {db_name} Database")
        print(f"   ID: {db_id}")

        try:
            # Clean the ID (remove hyphens)
            clean_id = db_id.replace("-", "")

            # Retrieve database
            db = await client.databases.retrieve(database_id=clean_id)

            print(f"   ✅ Successfully retrieved database")
            print(f"      Object type: {db.get('object')}")
            print(f"      Archived: {db.get('archived', False)}")

            # Check for data sources (Notion API 2025-09-03)
            data_sources = db.get("data_sources", [])
            print(f"      Data sources: {len(data_sources)}")

            if len(data_sources) == 0:
                print(f"      ❌ NO DATA SOURCES")
                print(f"      This database has no data sources - this is unusual.")
            else:
                # Retrieve first data source to check properties
                ds_id = data_sources[0]["id"]
                ds_name = data_sources[0].get("name", "Unnamed")
                print(f"      Data source ID: {ds_id}")
                print(f"      Data source name: {ds_name}")

                # Get data source properties
                ds = await client.data_sources.retrieve(data_source_id=ds_id)
                properties = ds.get("properties", {})
                print(f"      Properties count: {len(properties)}")

                if len(properties) == 0:
                    print(f"      ❌ NO PROPERTIES ACCESSIBLE")
                    print(f"      ")
                    print(f"      This usually means:")
                    print(f"      1. Integration is not connected to this database")
                    print(f"      2. Database has no columns defined (empty schema)")
                    print(f"      ")
                    print(f"      To fix:")
                    print(f"      - Open: https://notion.so/{clean_id}")
                    print(f"      - Click '...' menu → 'Connections'")
                    print(f"      - Verify your integration is listed")
                    print(f"      - If not, click '+ Add connections' and select it")
                else:
                    print(f"      ✅ Properties accessible (from data source):")
                    for prop_name, prop_data in list(properties.items())[:10]:  # Show first 10
                        prop_type = prop_data.get("type", "unknown")
                        print(f"         - {prop_name} ({prop_type})")
                    if len(properties) > 10:
                        print(f"         ... and {len(properties) - 10} more")

            # Check parent type
            parent = db.get("parent", {})
            parent_type = parent.get("type")
            print(f"      Parent type: {parent_type}")
            if parent_type == "block_id":
                print(f"      ℹ️  This is an inline database (embedded in a page)")
            elif parent_type == "page_id":
                print(f"      ℹ️  This is a full-page database")
            elif parent_type == "workspace":
                print(f"      ℹ️  This is a workspace database")

        except Exception as e:
            print(f"   ❌ Error accessing database: {type(e).__name__}")
            print(f"      {str(e)}")

            if "Could not find database" in str(e):
                print(f"      ")
                print(f"      Possible causes:")
                print(f"      1. Database ID is incorrect")
                print(f"      2. Integration doesn't have access to this database")
                print(f"      3. Database was deleted or moved")

    await client.aclose()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print("\nIf you see '0 properties' errors, follow the fix instructions above.")
    print("After connecting the integration, run this script again to verify.")


if __name__ == "__main__":
    asyncio.run(diagnose_notion_access())
