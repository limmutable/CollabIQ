#!/usr/bin/env python3
"""
Check person field population in production Notion database.

This script queries the CollabIQ database to verify that the 담당자 (person) field
is being populated correctly with matched user IDs.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from notion_integrator.integrator import NotionIntegrator


async def check_person_fields():
    """Query recent Notion entries and check person field population."""

    print("Connecting to Notion...")

    # Load config from environment
    import os
    database_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")

    if not database_id:
        print("ERROR: NOTION_DATABASE_ID_COLLABIQ not set in environment")
        print("Run: collabiq config test-secrets")
        sys.exit(1)

    async with NotionIntegrator(use_cache=True) as integrator:
        # Discover schema
        schema = await integrator.discover_database_schema(database_id)

        print(f"\nDatabase: {schema.database.title}")
        print(f"Database ID: {schema.database.id}")

        # Query recent entries (last 10)
        print("\nQuerying recent entries...")
        sdk_client = integrator.client.client

        response = await sdk_client.databases.query(
            database_id=schema.database.id,
            page_size=10,
            sorts=[{"timestamp": "created_time", "direction": "descending"}]
        )

        results = response.get("results", [])
        print(f"Found {len(results)} recent entries\n")

        # Check person field in each entry
        person_field_stats = {
            "total_entries": len(results),
            "person_field_populated": 0,
            "person_field_empty": 0,
            "entries_with_person": []
        }

        for i, page in enumerate(results, 1):
            page_id = page.get("id")
            created_time = page.get("created_time")
            properties = page.get("properties", {})

            # Get 담당자 (person) field
            person_field = properties.get("담당자", {})
            people = person_field.get("people", [])

            # Get Email ID for reference
            email_id_field = properties.get("Email ID", {})
            email_id_texts = email_id_field.get("rich_text", [])
            email_id = email_id_texts[0].get("plain_text") if email_id_texts else "N/A"

            # Get 협력주체 (title) for display
            title_field = properties.get("협력주체", {})
            title_texts = title_field.get("title", [])
            title = title_texts[0].get("plain_text") if title_texts else "Untitled"

            has_person = len(people) > 0
            if has_person:
                person_field_stats["person_field_populated"] += 1
                person_names = [p.get("name", "Unknown") for p in people]
                person_field_stats["entries_with_person"].append({
                    "title": title,
                    "email_id": email_id,
                    "person_names": person_names,
                    "person_ids": [p.get("id") for p in people]
                })
            else:
                person_field_stats["person_field_empty"] += 1

            status_icon = "✅" if has_person else "❌"
            person_display = ", ".join([p.get("name", "Unknown") for p in people]) if people else "(empty)"

            print(f"{i}. {status_icon} {title[:40]}")
            print(f"   Email ID: {email_id}")
            print(f"   Created: {created_time}")
            print(f"   담당자: {person_display}")
            print()

        # Print summary
        print("=" * 70)
        print("PERSON FIELD POPULATION SUMMARY")
        print("=" * 70)
        print(f"Total Entries Checked: {person_field_stats['total_entries']}")
        print(f"✅ Person Field Populated: {person_field_stats['person_field_populated']}")
        print(f"❌ Person Field Empty: {person_field_stats['person_field_empty']}")

        if person_field_stats['total_entries'] > 0:
            population_rate = (person_field_stats['person_field_populated'] /
                             person_field_stats['total_entries'] * 100)
            print(f"Population Rate: {population_rate:.1f}%")

        print("\n" + "=" * 70)
        print("ENTRIES WITH PERSON FIELD POPULATED")
        print("=" * 70)
        for entry in person_field_stats['entries_with_person']:
            print(f"\n📧 {entry['title']}")
            print(f"   Email ID: {entry['email_id']}")
            print(f"   Person(s): {', '.join(entry['person_names'])}")
            print(f"   User ID(s): {', '.join(entry['person_ids'])}")

        if not person_field_stats['entries_with_person']:
            print("\nNo entries with person field populated found in last 10 entries.")
            print("This may indicate:")
            print("  1. Recent emails did not have extractable person names")
            print("  2. Extracted person names did not match workspace users")
            print("  3. Person matching feature not yet used in production")


if __name__ == "__main__":
    try:
        asyncio.run(check_person_fields())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
