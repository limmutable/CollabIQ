#!/usr/bin/env python3
"""
Notion Database Schema Setup

This script creates the required schema for:
1. CollabIQ database (NOTION_DATABASE_ID_COLLABIQ)
2. Company database (NOTION_DATABASE_ID_CORP)

Based on the data model specification in data-model.md
"""

import os
import sys
from pathlib import Path

from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Notion credentials
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_COLLABIQ = os.getenv("NOTION_DATABASE_ID_COLLABIQ")
NOTION_DATABASE_ID_CORP = os.getenv("NOTION_DATABASE_ID_CORP")

def check_env_vars():
    """Check if all required environment variables are set."""
    missing = []
    if not NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not NOTION_DATABASE_ID_COLLABIQ:
        missing.append("NOTION_DATABASE_ID_COLLABIQ")
    if not NOTION_DATABASE_ID_CORP:
        missing.append("NOTION_DATABASE_ID_CORP")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)

def setup_company_database(notion: Client) -> bool:
    """Set up the Company database schema."""
    print("\n📋 Setting up Company database schema...")

    try:
        # Update database with new properties
        notion.databases.update(
            database_id=NOTION_DATABASE_ID_CORP,
            properties={
                "회사명": {
                    "title": {}  # Title field (already exists by default)
                },
                "Company Type": {
                    "select": {
                        "options": [
                            {"name": "Startup", "color": "blue"},
                            {"name": "Portfolio Company", "color": "green"},
                            {"name": "Shinsegate Affiliate", "color": "purple"}
                        ]
                    }
                },
                "포트폴리오 여부": {
                    "checkbox": {}
                },
                "SSG 계열사 여부": {
                    "checkbox": {}
                },
                "투자 날짜": {
                    "date": {}
                },
                "비고": {
                    "rich_text": {}
                }
            }
        )

        print("✅ Company database schema created successfully")
        print("   Fields:")
        print("   - 회사명 (Title)")
        print("   - Company Type (Select: Startup, Portfolio Company, Shinsegate Affiliate)")
        print("   - 포트폴리오 여부 (Checkbox)")
        print("   - SSG 계열사 여부 (Checkbox)")
        print("   - 투자 날짜 (Date)")
        print("   - 비고 (Rich Text)")

        return True

    except Exception as e:
        print(f"❌ Failed to set up Company database: {e}")
        return False

def setup_collabiq_database(notion: Client) -> bool:
    """Set up the CollabIQ database schema."""
    print("\n📋 Setting up CollabIQ database schema...")

    try:
        # Update database with new properties
        notion.databases.update(
            database_id=NOTION_DATABASE_ID_COLLABIQ,
            properties={
                "협력주체": {
                    "title": {}  # Title field
                },
                "담당자": {
                    "people": {}
                },
                "스타트업명": {
                    "relation": {
                        "database_id": NOTION_DATABASE_ID_CORP,
                        "type": "single_property",
                        "single_property": {}
                    }
                },
                "협업기관": {
                    "relation": {
                        "database_id": NOTION_DATABASE_ID_CORP,
                        "type": "single_property",
                        "single_property": {}
                    }
                },
                "협업내용": {
                    "rich_text": {}
                },
                "협업형태": {
                    "select": {
                        "options": [
                            {"name": "[A]", "color": "blue"},
                            {"name": "[B]", "color": "green"},
                            {"name": "[C]", "color": "yellow"},
                            {"name": "[D]", "color": "gray"}
                        ]
                    }
                },
                "협업강도": {
                    "select": {
                        "options": [
                            {"name": "이해", "color": "default"},
                            {"name": "협력", "color": "blue"},
                            {"name": "투자", "color": "green"},
                            {"name": "인수", "color": "red"}
                        ]
                    }
                },
                "날짜": {
                    "date": {}
                }
            }
        )

        print("✅ CollabIQ database schema created successfully")
        print("   Fields:")
        print("   - 협력주체 (Title)")
        print("   - 담당자 (People)")
        print("   - 스타트업명 (Relation → Company DB)")
        print("   - 협업기관 (Relation → Company DB)")
        print("   - 협업내용 (Rich Text)")
        print("   - 협업형태 (Select: [A], [B], [C], [D])")
        print("   - 협업강도 (Select: 이해, 협력, 투자, 인수)")
        print("   - 날짜 (Date)")

        return True

    except Exception as e:
        print(f"❌ Failed to set up CollabIQ database: {e}")
        return False

def main():
    """Main function to set up Notion database schemas."""
    print("=" * 60)
    print("Notion Database Schema Setup")
    print("=" * 60)

    # Check environment variables
    check_env_vars()

    print("\n✅ All environment variables found")

    # Initialize Notion client
    print("\n🔌 Connecting to Notion API...")
    try:
        notion = Client(auth=NOTION_API_KEY)
        print("✅ Connected to Notion API")

        # Debug: Check current database structure
        print("\n🔍 Checking current database structure...")
        db = notion.databases.retrieve(database_id=NOTION_DATABASE_ID_CORP)
        print(f"   Response keys: {list(db.keys())}")
        if 'properties' in db:
            print(f"   Existing properties: {list(db.get('properties', {}).keys())}")
        else:
            print("   ⚠️  No 'properties' key in response - this might be a database view")

    except Exception as e:
        print(f"❌ Failed to connect to Notion API: {e}")
        sys.exit(1)

    # Set up schemas
    company_success = setup_company_database(notion)
    collabiq_success = setup_collabiq_database(notion)

    print("\n" + "=" * 60)
    if company_success and collabiq_success:
        print("✅ All database schemas created successfully!")
        print("\nNext steps:")
        print("1. Run analyze_notion_structure.py to verify the schema")
        print("2. Add some test company entries to the Company database")
        print("3. Run test_notion_write.py to test entry creation")
    else:
        print("❌ Some database schemas failed to create")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
