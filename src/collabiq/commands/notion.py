"""
Notion integration management commands.

Commands:
- verify: Check Notion connection and schema
- schema: Display database schema
- test-write: Create and cleanup test entry
- cleanup-tests: Remove all test entries
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from collabiq.formatters.colors import console
from collabiq.formatters.json_output import output_json, format_json_error
from collabiq.formatters.tables import create_table, render_table
from collabiq.utils.logging import log_cli_operation, log_cli_error
from collabiq.utils.validation import validate_email_id

# Import Notion integrator
from notion_integrator.integrator import NotionIntegrator
from notion_integrator.exceptions import (
    NotionAuthenticationError,
    NotionObjectNotFoundError,
    NotionPermissionError,
    NotionAPIError,
)
from llm_provider.types import ExtractedEntitiesWithClassification

app = typer.Typer(
    name="notion",
    help="Notion integration management (verify, schema, test-write, cleanup-tests)",
)


# ==============================================================================
# Helper Functions
# ==============================================================================


def get_notion_config(json_mode: bool = False) -> Dict[str, str]:
    """
    Get Notion configuration from environment variables.

    Args:
        json_mode: Whether to output errors in JSON format

    Returns:
        Dictionary with Notion API key and database ID

    Raises:
        typer.Exit: If required configuration is missing
    """
    api_key = os.getenv("NOTION_API_KEY")
    collabiq_db_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")

    if not api_key:
        if json_mode:
            output_json(
                data={},
                status="failure",
                errors=[{"error_type": "ConfigurationError", "message": "NOTION_API_KEY not set in environment"}]
            )
        else:
            console.print("[red]Error: NOTION_API_KEY not set in environment[/red]")
            console.print("\n[yellow]Remediation:[/yellow]")
            console.print("1. Set NOTION_API_KEY environment variable")
            console.print("2. Or configure Infisical secrets (run: collabiq config test-secrets)")
        raise typer.Exit(1)

    if not collabiq_db_id:
        if json_mode:
            output_json(
                data={},
                status="failure",
                errors=[{"error_type": "ConfigurationError", "message": "NOTION_DATABASE_ID_COLLABIQ not set in environment"}]
            )
        else:
            console.print("[red]Error: NOTION_DATABASE_ID_COLLABIQ not set in environment[/red]")
            console.print("\n[yellow]Remediation:[/yellow]")
            console.print("1. Set NOTION_DATABASE_ID_COLLABIQ environment variable")
            console.print("2. Get database ID from Notion database URL")
        raise typer.Exit(1)

    return {"api_key": api_key, "collabiq_db_id": collabiq_db_id}


def handle_notion_error(error: Exception, context: str, json_mode: bool = False) -> None:
    """
    Handle Notion API errors with user-friendly messages and remediation.

    Args:
        error: Exception that occurred
        context: Context string (e.g., "notion_verify")
        json_mode: Whether to output JSON format
    """
    error_type = type(error).__name__
    error_message = str(error)

    # Log error
    log_cli_error(context, error)

    if json_mode:
        output_json(
            data={},
            status="failure",
            errors=[format_json_error(error, context)],
        )
        raise typer.Exit(1)

    # Display user-friendly error message
    console.print(f"\n[red]Error ({error_type}):[/red] {error_message}")

    # Provide remediation based on error type
    if isinstance(error, NotionAuthenticationError):
        console.print("\n[yellow]Remediation:[/yellow]")
        console.print("1. Check NOTION_API_KEY is valid")
        console.print("2. Verify API key has not expired")
        console.print("3. Run: collabiq config show (to check configuration)")
    elif isinstance(error, NotionObjectNotFoundError):
        console.print("\n[yellow]Remediation:[/yellow]")
        console.print("1. Check NOTION_DATABASE_ID_COLLABIQ is correct")
        console.print("2. Verify database exists and is accessible")
        console.print("3. Ensure integration has access to the database")
    elif isinstance(error, NotionPermissionError):
        console.print("\n[yellow]Remediation:[/yellow]")
        console.print("1. Grant integration permission to database")
        console.print("2. Check database sharing settings in Notion")
        console.print("3. Verify integration has 'Read' and 'Update' permissions")
    else:
        console.print("\n[yellow]Remediation:[/yellow]")
        console.print("1. Check network connectivity")
        console.print("2. Verify Notion API status (status.notion.so)")
        console.print("3. Try again with --debug flag for details")

    raise typer.Exit(1)


# ==============================================================================
# Commands
# ==============================================================================


@app.command()
def verify(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
) -> None:
    """
    Verify Notion connection, authentication, database access, and schema.

    Performs comprehensive checks:
    - API authentication
    - Database connectivity
    - Database permissions
    - Schema validation

    Examples:
        $ collabiq notion verify
        $ collabiq notion verify --json
        $ collabiq notion verify --debug
    """
    start_time = datetime.now()

    try:
        # Get configuration
        config = get_notion_config(json_mode=json)

        async def verify_async():
            async with NotionIntegrator(
                api_key=config["api_key"],
                use_cache=False,  # Force fresh check
            ) as integrator:
                # Step 1: Discover schema (tests auth + database access + permissions)
                schema = await integrator.discover_database_schema(
                    database_id=config["collabiq_db_id"],
                    use_cache=False,
                )

                return {
                    "connection": "OK",
                    "authentication": "OK",
                    "database_access": "OK",
                    "database_id": config["collabiq_db_id"],
                    "database_name": schema.database.title,
                    "property_count": schema.property_count,
                    "has_relations": schema.has_relations,
                    "relation_count": len(schema.relation_properties),
                }

        # Run async verification
        result = asyncio.run(verify_async())

        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Log success
        log_cli_operation("notion verify", success=True, duration_ms=duration_ms)

        # Output result
        if json:
            output_json(data=result, status="success")
        else:
            console.print("\n[green]✓ Notion verification successful![/green]\n")
            console.print(f"[cyan]Database:[/cyan] {result['database_name']}")
            console.print(f"[cyan]Database ID:[/cyan] {result['database_id']}")
            console.print(f"[cyan]Properties:[/cyan] {result['property_count']}")
            console.print(f"[cyan]Relations:[/cyan] {result['relation_count']}")
            console.print(f"[cyan]Connection:[/cyan] {result['connection']}")
            console.print(f"[cyan]Authentication:[/cyan] {result['authentication']}")
            console.print(f"[cyan]Database Access:[/cyan] {result['database_access']}")
            console.print(f"\n[dim]Completed in {duration_ms}ms[/dim]")

    except typer.Exit:
        # Re-raise typer.Exit (from config error)
        raise
    except Exception as e:
        handle_notion_error(e, "notion_verify", json_mode=json)


@app.command()
def schema(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
) -> None:
    """
    Display Notion database schema in table format.

    Shows all database properties with their types, IDs, and configurations.

    Examples:
        $ collabiq notion schema
        $ collabiq notion schema --json
    """
    start_time = datetime.now()

    try:
        # Get configuration
        config = get_notion_config(json_mode=json)

        async def get_schema_async():
            async with NotionIntegrator(
                api_key=config["api_key"],
                use_cache=True,  # Use cache for faster display
            ) as integrator:
                # Discover schema
                schema = await integrator.discover_database_schema(
                    database_id=config["collabiq_db_id"],
                    use_cache=True,
                )

                # Build property list
                properties = []
                for prop in schema.database.properties.values():
                    properties.append({
                        "name": prop.name,
                        "type": prop.type,
                        "id": prop.id,
                    })

                return {
                    "database_name": schema.database.title,
                    "database_id": schema.database.id,
                    "property_count": schema.property_count,
                    "properties": properties,
                    "properties_by_type": {
                        k: len(v) for k, v in schema.properties_by_type.items()
                    },
                }

        # Run async operation
        result = asyncio.run(get_schema_async())

        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Log success
        log_cli_operation("notion schema", success=True, duration_ms=duration_ms)

        # Output result
        if json:
            output_json(data=result, status="success")
        else:
            console.print(f"\n[cyan]Database:[/cyan] {result['database_name']}")
            console.print(f"[cyan]Database ID:[/cyan] {result['database_id']}")
            console.print(f"[cyan]Total Properties:[/cyan] {result['property_count']}\n")

            # Create table for properties
            table = create_table(
                title="Database Schema",
                columns=[
                    {"name": "Property Name", "style": "cyan", "field": "name"},
                    {"name": "Type", "style": "magenta", "field": "type"},
                    {"name": "ID", "style": "dim", "field": "id", "no_wrap": False},
                ],
                show_lines=True,
            )

            for prop in result["properties"]:
                table.add_row(prop["name"], prop["type"], prop["id"])

            console.print(table)

            # Show property type summary
            console.print("\n[cyan]Property Types:[/cyan]")
            for prop_type, count in sorted(result["properties_by_type"].items()):
                console.print(f"  {prop_type}: {count}")

            console.print(f"\n[dim]Completed in {duration_ms}ms[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        handle_notion_error(e, "notion_schema", json_mode=json)


@app.command(name="test-write")
def test_write(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
) -> None:
    """
    Create a test entry in Notion database and automatically cleanup.

    Creates a test entry with sample data, verifies it was written,
    then automatically removes it. Useful for testing write permissions.

    Examples:
        $ collabiq notion test-write
        $ collabiq notion test-write --json
    """
    start_time = datetime.now()

    try:
        # Get configuration
        config = get_notion_config(json_mode=json)

        async def test_write_async():
            async with NotionIntegrator(
                api_key=config["api_key"],
                use_cache=False,
            ) as integrator:
                # Import writer
                from notion_integrator.writer import NotionWriter

                # Create writer instance
                writer = NotionWriter(
                    notion_integrator=integrator,
                    collabiq_db_id=config["collabiq_db_id"],
                    duplicate_behavior="skip",
                )

                # Create test data
                test_email_id = f"cli_test_{int(datetime.now().timestamp())}"
                test_data = ExtractedEntitiesWithClassification(
                    email_id=test_email_id,
                    sender="test@collabiq-cli.test",
                    subject="CLI Test Entry - Safe to Delete",
                    received_date=datetime.now().isoformat(),
                    companies=[],
                    people=[],
                    opportunities=[],
                    collaboration_type_hint="test",
                    summary="This is a test entry created by the CollabIQ CLI.",
                )

                # Write test entry
                write_result = await writer.create_collabiq_entry(test_data)

                if not write_result.success:
                    raise Exception(f"Failed to create test entry: {write_result.error_message}")

                page_id = write_result.page_id

                # Cleanup test entry
                await integrator.client.client.pages.update(
                    page_id=page_id,
                    archived=True,
                )

                return {
                    "test_entry_created": True,
                    "test_entry_cleaned": True,
                    "page_id": page_id,
                    "email_id": test_email_id,
                }

        # Run async operation
        result = asyncio.run(test_write_async())

        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Log success
        log_cli_operation("notion test-write", success=True, duration_ms=duration_ms)

        # Output result
        if json:
            output_json(data=result, status="success")
        else:
            console.print("\n[green]✓ Test write successful![/green]\n")
            console.print(f"[cyan]Created test entry:[/cyan] {result['page_id']}")
            console.print(f"[cyan]Email ID:[/cyan] {result['email_id']}")
            console.print("[green]✓ Test entry automatically cleaned up[/green]")
            console.print(f"\n[dim]Completed in {duration_ms}ms[/dim]")

    except typer.Exit:
        raise
    except Exception as e:
        handle_notion_error(e, "notion_test_write", json_mode=json)


@app.command(name="cleanup-tests")
def cleanup_tests(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
) -> None:
    """
    Remove all test entries from Notion database.

    Searches for entries with email IDs starting with 'cli_test_'
    and archives them. Requires confirmation unless --yes is used.

    Examples:
        $ collabiq notion cleanup-tests
        $ collabiq notion cleanup-tests --yes
        $ collabiq notion cleanup-tests --json
    """
    start_time = datetime.now()

    try:
        # Get configuration
        config = get_notion_config(json_mode=json)

        async def cleanup_async():
            async with NotionIntegrator(
                api_key=config["api_key"],
                use_cache=False,
            ) as integrator:
                # Query for test entries
                # Search for entries with email_id starting with 'cli_test_'
                filter_conditions = {
                    "property": "Email ID",
                    "rich_text": {
                        "starts_with": "cli_test_"
                    },
                }

                response = await integrator.client.query_database(
                    database_id=config["collabiq_db_id"],
                    filter_conditions=filter_conditions,
                )

                test_entries = response.get("results", [])
                entry_count = len(test_entries)

                # If no entries, return early
                if entry_count == 0:
                    return {"cleaned": 0, "entries": []}

                # Collect entry info
                entries = []
                for entry in test_entries:
                    page_id = entry["id"]
                    # Extract email_id from properties
                    email_id_prop = entry.get("properties", {}).get("Email ID", {})
                    email_id = ""
                    if email_id_prop.get("type") == "rich_text":
                        rich_text_array = email_id_prop.get("rich_text", [])
                        if rich_text_array:
                            email_id = rich_text_array[0].get("text", {}).get("content", "")

                    entries.append({
                        "page_id": page_id,
                        "email_id": email_id,
                    })

                return {"cleaned": 0, "entries": entries, "entry_count": entry_count}

        # Run async query
        result = asyncio.run(cleanup_async())

        # If no entries found, exit early
        if result["entry_count"] == 0:
            if json:
                output_json(data={"cleaned": 0, "message": "No test entries found"}, status="success")
            else:
                console.print("\n[yellow]No test entries found to cleanup[/yellow]")
            return

        # Confirmation prompt (unless --yes or --json)
        if not yes and not json:
            console.print(f"\n[yellow]Found {result['entry_count']} test entries to cleanup:[/yellow]")
            for entry in result["entries"][:5]:  # Show first 5
                console.print(f"  - {entry['email_id']} ({entry['page_id']})")
            if result["entry_count"] > 5:
                console.print(f"  ... and {result['entry_count'] - 5} more")

            confirm = typer.confirm("\nAre you sure you want to archive these entries?")
            if not confirm:
                console.print("[yellow]Cleanup cancelled[/yellow]")
                raise typer.Exit(0)

        # Perform cleanup
        async def archive_entries():
            async with NotionIntegrator(
                api_key=config["api_key"],
                use_cache=False,
            ) as integrator:
                cleaned = 0
                for entry in result["entries"]:
                    try:
                        await integrator.client.client.pages.update(
                            page_id=entry["page_id"],
                            archived=True,
                        )
                        cleaned += 1
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to archive {entry['page_id']}: {e}[/yellow]")

                return {"cleaned": cleaned, "total": result["entry_count"]}

        cleanup_result = asyncio.run(archive_entries())

        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Log success
        log_cli_operation("notion cleanup-tests", success=True, duration_ms=duration_ms, cleaned=cleanup_result["cleaned"])

        # Output result
        if json:
            output_json(data=cleanup_result, status="success")
        else:
            console.print(f"\n[green]✓ Cleaned up {cleanup_result['cleaned']} of {cleanup_result['total']} test entries[/green]")
            console.print(f"\n[dim]Completed in {duration_ms}ms[/dim]")

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise  # Re-raise typer.Exit (from cancellation)
        handle_notion_error(e, "notion_cleanup_tests", json_mode=json)
