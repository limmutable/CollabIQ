#!/usr/bin/env python3
"""
Notion Database Structure Analyzer

This script connects to Notion API and analyzes the structure of:
1. CollabIQ database (NOTION_DATABASE_ID_COLLABIQ)
2. Company database (NOTION_DATABASE_ID_CORP)

It exports the schema analysis to notion-schema-analysis.md
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

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

def format_property_type(prop: Dict[str, Any]) -> str:
    """Format property type information."""
    prop_type = prop.get("type", "unknown")

    if prop_type == "select":
        options = prop.get("select", {}).get("options", [])
        option_names = [opt.get("name") for opt in options]
        return f"Select (options: {', '.join(option_names)})"

    elif prop_type == "multi_select":
        options = prop.get("multi_select", {}).get("options", [])
        option_names = [opt.get("name") for opt in options]
        return f"Multi-select (options: {', '.join(option_names)})"

    elif prop_type == "relation":
        database_id = prop.get("relation", {}).get("database_id", "unknown")
        return f"Relation (→ {database_id[:8]}...)"

    elif prop_type == "people":
        return "People"

    elif prop_type == "title":
        return "Title"

    elif prop_type == "rich_text":
        return "Rich Text"

    elif prop_type == "number":
        return "Number"

    elif prop_type == "checkbox":
        return "Checkbox"

    elif prop_type == "date":
        return "Date"

    elif prop_type == "url":
        return "URL"

    elif prop_type == "email":
        return "Email"

    elif prop_type == "phone_number":
        return "Phone Number"

    else:
        return prop_type.capitalize()

def analyze_database(notion: Client, database_id: str, database_name: str) -> str:
    """Analyze a Notion database and return formatted schema information."""
    try:
        print(f"\n📊 Analyzing {database_name} database...")
        db = notion.databases.retrieve(database_id=database_id)

        # Debug: Print the response
        print(f"   DEBUG: Database response keys: {list(db.keys())}")

        # Get database title
        title_property = db.get("title", [])
        db_title = title_property[0].get("plain_text", "Untitled") if title_property else "Untitled"

        # Get properties
        properties = db.get("properties", {})
        print(f"   DEBUG: Found {len(properties)} properties: {list(properties.keys())}")

        output = f"\n## {database_name} Database\n\n"
        output += f"**Database Title**: {db_title}\n"
        output += f"**Database ID**: `{database_id}`\n"
        output += f"**URL**: https://notion.so/{database_id.replace('-', '')}\n\n"
        output += "### Fields\n\n"

        # Sort properties to show title first
        sorted_props = sorted(
            properties.items(),
            key=lambda x: (0 if x[1].get("type") == "title" else 1, x[0])
        )

        for prop_name, prop_config in sorted_props:
            prop_type = format_property_type(prop_config)
            output += f"- **{prop_name}** ({prop_type})\n"

        output += f"\n**Total Fields**: {len(properties)}\n"

        print(f"✅ Found {len(properties)} fields in {database_name} database")

        return output

    except Exception as e:
        error_msg = f"\n## {database_name} Database\n\n"
        error_msg += f"❌ **Error**: Failed to retrieve database\n"
        error_msg += f"**Database ID**: `{database_id}`\n"
        error_msg += f"**Error Message**: {str(e)}\n\n"

        print(f"❌ Error analyzing {database_name} database: {e}")

        return error_msg

def main():
    """Main function to analyze Notion databases and export results."""
    print("=" * 60)
    print("Notion Database Structure Analyzer")
    print("=" * 60)

    # Check environment variables
    check_env_vars()

    print("\n✅ All environment variables found")
    print(f"   - NOTION_API_KEY: {NOTION_API_KEY[:20]}...")
    print(f"   - NOTION_DATABASE_ID_COLLABIQ: {NOTION_DATABASE_ID_COLLABIQ}")
    print(f"   - NOTION_DATABASE_ID_CORP: {NOTION_DATABASE_ID_CORP}")

    # Initialize Notion client
    print("\n🔌 Connecting to Notion API...")
    try:
        notion = Client(auth=NOTION_API_KEY)
        print("✅ Connected to Notion API")
    except Exception as e:
        print(f"❌ Failed to connect to Notion API: {e}")
        sys.exit(1)

    # Analyze both databases
    collabiq_schema = analyze_database(notion, NOTION_DATABASE_ID_COLLABIQ, "CollabIQ")
    corp_schema = analyze_database(notion, NOTION_DATABASE_ID_CORP, "Company")

    # Generate markdown report
    report = "# Notion Database Schema Analysis\n\n"
    report += "**Generated**: " + str(Path(__file__).parent.parent.name) + "\n"
    report += "**Purpose**: Document actual Notion database structures for validation\n\n"
    report += "---\n"
    report += collabiq_schema
    report += "\n---\n"
    report += corp_schema
    report += "\n---\n\n"
    report += "## Notes\n\n"
    report += "- This analysis was generated automatically by `analyze_notion_structure.py`\n"
    report += "- Use this information to validate field expectations in the research template\n"
    report += "- Relation fields point to other databases using their database IDs\n"
    report += "- Select/Multi-select fields show available options\n"

    # Write report to file
    output_path = Path(__file__).parent.parent / "notion-schema-analysis.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 60)
    print(f"✅ Schema analysis exported to:")
    print(f"   {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
