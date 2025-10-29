#!/usr/bin/env python3
"""
Query Notion Databases to Understand Schema

Since databases.retrieve() doesn't return properties for existing databases,
we'll query actual pages/entries to understand the schema structure.
"""

import os
import sys
import json
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

def format_property_info(prop_name: str, prop_data: dict) -> str:
    """Format property information from a page."""
    prop_type = prop_data.get("type", "unknown")

    if prop_type == "title":
        content = prop_data.get("title", [])
        sample = content[0].get("plain_text", "") if content else ""
        return f"Title (sample: '{sample[:30]}...')" if len(sample) > 30 else f"Title (sample: '{sample}')"

    elif prop_type == "rich_text":
        content = prop_data.get("rich_text", [])
        sample = content[0].get("plain_text", "") if content else ""
        return f"Rich Text (sample: '{sample[:30]}...')" if len(sample) > 30 else f"Rich Text (sample: '{sample}')"

    elif prop_type == "select":
        select_data = prop_data.get("select")
        value = select_data.get("name", "") if select_data else ""
        return f"Select (value: '{value}')"

    elif prop_type == "multi_select":
        values = [item.get("name", "") for item in prop_data.get("multi_select", [])]
        return f"Multi-select (values: {', '.join(values)})"

    elif prop_type == "date":
        date_data = prop_data.get("date")
        value = date_data.get("start", "") if date_data else ""
        return f"Date (value: '{value}')"

    elif prop_type == "people":
        people = prop_data.get("people", [])
        return f"People ({len(people)} person(s))"

    elif prop_type == "relation":
        relations = prop_data.get("relation", [])
        return f"Relation ({len(relations)} linked item(s))"

    elif prop_type == "checkbox":
        value = prop_data.get("checkbox", False)
        return f"Checkbox (value: {value})"

    elif prop_type == "number":
        value = prop_data.get("number", "")
        return f"Number (value: {value})"

    else:
        return f"{prop_type.capitalize()}"

def query_database(notion: Client, database_id: str, database_name: str) -> str:
    """Query a Notion database to understand its schema."""
    try:
        print(f"\n📊 Querying {database_name} database...")

        # Query the database using direct HTTP request
        # The notion-client's request() method has issues with the path format
        import requests

        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        http_response = requests.post(url, headers=headers, json={"page_size": 5})

        if http_response.status_code != 200:
            raise Exception(f"HTTP {http_response.status_code}: {http_response.text}")

        response = http_response.json()

        results = response.get("results", [])
        print(f"   Found {len(results)} entries (showing first 5)")

        if not results:
            output = f"\n## {database_name} Database\n\n"
            output += "⚠️  **No entries found in database**\n\n"
            output += f"**Database ID**: `{database_id}`\n"
            output += "**Cannot analyze schema** - database is empty or query failed\n"
            return output

        # Get properties from the first entry
        first_entry = results[0]
        properties = first_entry.get("properties", {})

        print(f"   Found {len(properties)} properties")

        # Build output
        output = f"\n## {database_name} Database\n\n"
        output += f"**Database ID**: `{database_id}`\n"
        output += f"**Entries Found**: {len(results)}\n"
        output += f"**URL**: https://notion.so/{database_id.replace('-', '')}\n\n"
        output += "### Fields (from existing entries)\n\n"

        # List all properties
        for prop_name, prop_data in sorted(properties.items()):
            prop_info = format_property_info(prop_name, prop_data)
            output += f"- **{prop_name}**: {prop_info}\n"

        output += f"\n**Total Fields**: {len(properties)}\n"

        # Show sample entry titles
        output += "\n### Sample Entries\n\n"
        for i, entry in enumerate(results[:3], 1):
            title_prop = None
            for prop_name, prop_data in entry.get("properties", {}).items():
                if prop_data.get("type") == "title":
                    title_prop = prop_data
                    break

            if title_prop:
                title_content = title_prop.get("title", [])
                title_text = title_content[0].get("plain_text", "Untitled") if title_content else "Untitled"
                output += f"{i}. {title_text}\n"

        print(f"✅ Schema extracted from {database_name} database")
        return output

    except Exception as e:
        error_msg = f"\n## {database_name} Database\n\n"
        error_msg += f"❌ **Error**: Failed to query database\n"
        error_msg += f"**Database ID**: `{database_id}`\n"
        error_msg += f"**Error Message**: {str(e)}\n\n"

        print(f"❌ Error querying {database_name} database: {e}")
        return error_msg

def main():
    """Main function to query Notion databases and analyze schema."""
    print("=" * 60)
    print("Notion Database Query & Schema Analysis")
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

    # Query both databases
    collabiq_schema = query_database(notion, NOTION_DATABASE_ID_COLLABIQ, "CollabIQ")
    corp_schema = query_database(notion, NOTION_DATABASE_ID_CORP, "Company")

    # Generate markdown report
    report = "# Notion Database Schema Analysis\n\n"
    report += "**Generated**: Queried from existing database entries\n"
    report += "**Purpose**: Document actual Notion database structures for validation\n\n"
    report += "---\n"
    report += collabiq_schema
    report += "\n---\n"
    report += corp_schema
    report += "\n---\n\n"
    report += "## Notes\n\n"
    report += "- This analysis was generated by querying existing database entries\n"
    report += "- Field types are inferred from actual data in the databases\n"
    report += "- Relation fields show the number of linked items\n"
    report += "- Sample values are shown to understand field usage\n"

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
