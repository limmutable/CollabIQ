"""CollabIQ CLI entry point."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from notion_integrator import NotionIntegrator

app = typer.Typer(
    name="collabiq",
    help="CollabIQ - Email-based collaboration tracking system",
    add_completion=False,
)
console = Console()

# Notion subcommand group
notion_app = typer.Typer(help="Notion integration commands")
app.add_typer(notion_app, name="notion")


@app.command()
def verify_infisical() -> None:
    """Verify Infisical integration and secret retrieval."""
    console.print("\n[bold cyan]Infisical Integration Verification[/bold cyan]\n")

    try:
        settings = get_settings()

        # Check if Infisical is enabled
        if not settings.infisical_enabled:
            console.print("[yellow]⚠ Infisical is disabled (INFISICAL_ENABLED=false)[/yellow]")
            console.print("[dim]Set INFISICAL_ENABLED=true in .env to enable Infisical integration[/dim]\n")
            sys.exit(1)

        # Display Infisical configuration
        console.print("[green]✅ Infisical configuration valid[/green]")
        console.print(f"[dim]Host: {settings.infisical_host}[/dim]")
        console.print(f"[dim]Project ID: {settings.infisical_project_id}[/dim]")
        console.print(f"[dim]Environment: {settings.infisical_environment}[/dim]")
        console.print(f"[dim]Cache TTL: {settings.infisical_cache_ttl}s[/dim]\n")

        # Try to retrieve secrets
        console.print("[yellow]Testing secret retrieval...[/yellow]")

        # Track which secrets are available
        secrets_found = []
        secrets_missing = []

        # Check each required secret
        secret_checks = [
            ("GMAIL_CREDENTIALS_PATH", str(settings.gmail_credentials_path) if settings.gmail_credentials_path else None),
            ("GEMINI_API_KEY", settings.gemini_api_key),
        ]

        for secret_name, secret_value in secret_checks:
            if secret_value:
                secrets_found.append(secret_name)
            else:
                secrets_missing.append(secret_name)

        # Display results
        if secrets_found:
            console.print(f"\n[green]✅ Retrieved {len(secrets_found)} secrets successfully[/green]\n")
            console.print("[bold]Secrets found:[/bold]")
            for secret_name in secrets_found:
                console.print(f"  [green]✓[/green] {secret_name}")

        if secrets_missing:
            console.print(f"\n[red]✗ {len(secrets_missing)} secrets missing[/red]\n")
            console.print("[bold]Secrets missing:[/bold]")
            for secret_name in secrets_missing:
                console.print(f"  [red]✗[/red] {secret_name}")
            console.print(
                "\n[yellow]Add missing secrets to your Infisical project:[/yellow]"
            )
            console.print(
                f"[dim]https://app.infisical.com/project/{settings.infisical_project_id}/secrets[/dim]\n"
            )
            sys.exit(1)

        console.print("\n[bold green]✅ All secrets loaded successfully[/bold green]")
        console.print(
            "[dim]Infisical integration is working correctly![/dim]\n"
        )

    except Exception as e:
        console.print(f"\n[bold red]✗ Verification failed[/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]\n")
        console.print(
            "[yellow]Check your Infisical configuration in .env:[/yellow]"
        )
        console.print("  - INFISICAL_ENABLED=true")
        console.print("  - INFISICAL_PROJECT_ID=<your-project-id>")
        console.print("  - INFISICAL_CLIENT_ID=<your-client-id>")
        console.print("  - INFISICAL_CLIENT_SECRET=<your-client-secret>")
        console.print(
            "\n[dim]See docs/setup/infisical-setup.md for setup instructions[/dim]\n"
        )
        sys.exit(1)


@app.command()
def version() -> None:
    """Show CollabIQ version."""
    console.print("CollabIQ v0.1.0")


# ==============================================================================
# Notion Commands
# ==============================================================================


@notion_app.command("fetch")
def notion_fetch(
    companies_db_id: Optional[str] = typer.Option(
        None,
        "--companies-db",
        "-c",
        help="Companies database ID (defaults to NOTION_DATABASE_ID_COMPANIES from Infisical or env)",
    ),
    collabiq_db_id: Optional[str] = typer.Option(
        None,
        "--collabiq-db",
        "-q",
        help="CollabIQ database ID (defaults to NOTION_DATABASE_ID_COLLABIQ from Infisical or env)",
    ),
    max_depth: int = typer.Option(
        1,
        "--max-depth",
        "-d",
        help="Maximum relationship resolution depth",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching (always fetch fresh from Notion)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (JSON format)",
    ),
) -> None:
    """Fetch and format data from Notion databases."""
    console.print("\n[bold cyan]Fetching Notion data...[/bold cyan]\n")

    try:
        # Get settings (loads from Infisical first, then .env)
        settings = get_settings()

        # Get database IDs from CLI args, then settings (which tries Infisical, then .env)
        companies_db = companies_db_id or settings.get_notion_companies_db_id()
        collabiq_db = collabiq_db_id or settings.get_notion_collabiq_db_id()

        if not companies_db:
            console.print("[red]✗ Companies database ID not provided[/red]")
            console.print("[yellow]Provide via --companies-db or NOTION_DATABASE_ID_COMPANIES in Infisical/.env[/yellow]\n")
            sys.exit(1)

        # Get API key from settings (tries Infisical first, then .env)
        api_key = settings.get_notion_api_key()
        if not api_key:
            console.print("[red]✗ NOTION_API_KEY not set[/red]")
            console.print("[yellow]Set NOTION_API_KEY in Infisical or .env[/yellow]\n")
            sys.exit(1)

        # Fetch data
        async def fetch_data():
            async with NotionIntegrator(
                api_key=api_key,
                use_cache=not no_cache,
                default_max_depth=max_depth,
            ) as integrator:
                return await integrator.get_data(
                    companies_db_id=companies_db,
                    collabiq_db_id=collabiq_db,
                )

        data = asyncio.run(fetch_data())

        # Display summary
        console.print("[green]✅ Data fetched successfully[/green]\n")

        # Display metadata
        table = Table(title="Data Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Companies", str(data.metadata.total_companies))
        table.add_row("SSG Affiliates", str(data.metadata.shinsegae_affiliate_count))
        table.add_row("Portfolio Companies", str(data.metadata.portfolio_company_count))
        table.add_row("Data Freshness", data.metadata.data_freshness)
        table.add_row("Formatted At", data.metadata.formatted_at.strftime("%Y-%m-%d %H:%M:%S"))

        console.print(table)
        console.print()

        # Display markdown summary
        console.print("[bold]Company Summary:[/bold]\n")
        console.print(data.summary_markdown)
        console.print()

        # Export to file if requested
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
            console.print(f"[green]✅ Data exported to {output}[/green]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Failed to fetch Notion data[/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]\n")
        sys.exit(1)


@notion_app.command("refresh")
def notion_refresh(
    database_id: str = typer.Argument(..., help="Database ID to refresh"),
    schema_only: bool = typer.Option(
        False,
        "--schema-only",
        help="Only refresh schema cache (not data)",
    ),
    data_only: bool = typer.Option(
        False,
        "--data-only",
        help="Only refresh data cache (not schema)",
    ),
) -> None:
    """Manually refresh cached data for a Notion database."""
    console.print("\n[bold cyan]Refreshing Notion cache...[/bold cyan]\n")

    try:
        # Get settings (loads from Infisical first, then .env)
        settings = get_settings()

        # Get API key from settings (tries Infisical first, then .env)
        api_key = settings.get_notion_api_key()
        if not api_key:
            console.print("[red]✗ NOTION_API_KEY not set[/red]")
            console.print("[yellow]Set NOTION_API_KEY in Infisical or .env[/yellow]\n")
            sys.exit(1)

        # Refresh cache
        async def refresh():
            async with NotionIntegrator(api_key=api_key) as integrator:
                refresh_schema = not data_only
                refresh_data = not schema_only

                await integrator.refresh_cache(
                    database_id=database_id,
                    refresh_schema=refresh_schema,
                    refresh_data=refresh_data,
                )

        asyncio.run(refresh())

        console.print("[green]✅ Cache refreshed successfully[/green]")
        console.print(f"[dim]Database ID: {database_id}[/dim]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Failed to refresh cache[/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]\n")
        sys.exit(1)


@notion_app.command("schema")
def notion_schema(
    database_id: str = typer.Argument(..., help="Database ID to inspect"),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching (always fetch fresh from Notion)",
    ),
) -> None:
    """Display schema information for a Notion database."""
    console.print("\n[bold cyan]Fetching database schema...[/bold cyan]\n")

    try:
        # Get settings (loads from Infisical first, then .env)
        settings = get_settings()

        # Get API key from settings (tries Infisical first, then .env)
        api_key = settings.get_notion_api_key()
        if not api_key:
            console.print("[red]✗ NOTION_API_KEY not set[/red]")
            console.print("[yellow]Set NOTION_API_KEY in Infisical or .env[/yellow]\n")
            sys.exit(1)

        # Fetch schema
        async def fetch_schema():
            async with NotionIntegrator(
                api_key=api_key,
                use_cache=not no_cache,
            ) as integrator:
                return await integrator.discover_database_schema(database_id=database_id)

        schema = asyncio.run(fetch_schema())

        # Display schema info
        console.print("[green]✅ Schema fetched successfully[/green]\n")

        # Basic info
        console.print(f"[bold]Database:[/bold] {schema.database.title}")
        console.print(f"[dim]ID: {schema.database.id}[/dim]")
        console.print(f"[dim]URL: {schema.database.url}[/dim]")
        console.print(f"[dim]Created: {schema.database.created_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        console.print(f"[dim]Last edited: {schema.database.last_edited_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")

        # Properties table
        table = Table(title="Properties")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("ID", style="dim")

        for prop_name, prop in schema.database.properties.items():
            table.add_row(prop_name, prop.type, prop.id)

        console.print(table)
        console.print()

        # Relations
        if schema.relation_properties:
            console.print("[bold]Relations:[/bold]")
            for rel_prop in schema.relation_properties:
                target_db = rel_prop.config.get("relation", {}).get("database_id", "N/A")
                console.print(f"  • {rel_prop.name} → {target_db}")
            console.print()

        # Classification fields
        if schema.classification_fields:
            console.print("[bold]Classification Fields:[/bold]")
            for field_name, field_id in schema.classification_fields.items():
                console.print(f"  • {field_name}: {field_id}")
            console.print()

        # Summary stats
        console.print(f"[bold]Total Properties:[/bold] {schema.property_count}")
        console.print(f"[bold]Has Relations:[/bold] {schema.has_relations}")
        console.print(f"[bold]Relation Count:[/bold] {len(schema.relation_properties)}")
        console.print()

    except Exception as e:
        console.print(f"\n[bold red]✗ Failed to fetch schema[/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]\n")
        sys.exit(1)


@notion_app.command("export")
def notion_export(
    companies_db_id: Optional[str] = typer.Option(
        None,
        "--companies-db",
        "-c",
        help="Companies database ID (defaults to NOTION_DATABASE_ID_COMPANIES from Infisical or env)",
    ),
    collabiq_db_id: Optional[str] = typer.Option(
        None,
        "--collabiq-db",
        "-q",
        help="CollabIQ database ID (defaults to NOTION_DATABASE_ID_COLLABIQ from Infisical or env)",
    ),
    output: Path = typer.Option(
        "data/notion_export.json",
        "--output",
        "-o",
        help="Output file path (JSON format)",
    ),
    max_depth: int = typer.Option(
        1,
        "--max-depth",
        "-d",
        help="Maximum relationship resolution depth",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching (always fetch fresh from Notion)",
    ),
) -> None:
    """Export formatted Notion data to a JSON file."""
    console.print("\n[bold cyan]Exporting Notion data...[/bold cyan]\n")

    try:
        # Get settings (loads from Infisical first, then .env)
        settings = get_settings()

        # Get database IDs from CLI args, then settings (which tries Infisical, then .env)
        companies_db = companies_db_id or settings.get_notion_companies_db_id()
        collabiq_db = collabiq_db_id or settings.get_notion_collabiq_db_id()

        if not companies_db:
            console.print("[red]✗ Companies database ID not provided[/red]")
            console.print("[yellow]Provide via --companies-db or NOTION_DATABASE_ID_COMPANIES in Infisical/.env[/yellow]\n")
            sys.exit(1)

        # Get API key from settings (tries Infisical first, then .env)
        api_key = settings.get_notion_api_key()
        if not api_key:
            console.print("[red]✗ NOTION_API_KEY not set[/red]")
            console.print("[yellow]Set NOTION_API_KEY in Infisical or .env[/yellow]\n")
            sys.exit(1)

        # Fetch data
        console.print(f"[yellow]Fetching from Notion...[/yellow]")

        async def fetch_data():
            async with NotionIntegrator(
                api_key=api_key,
                use_cache=not no_cache,
                default_max_depth=max_depth,
            ) as integrator:
                return await integrator.get_data(
                    companies_db_id=companies_db,
                    collabiq_db_id=collabiq_db,
                )

        data = asyncio.run(fetch_data())

        # Export to file
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        console.print(f"[green]✅ Data exported successfully[/green]")
        console.print(f"[dim]Output: {output}[/dim]")
        console.print(f"[dim]Companies: {data.metadata.total_companies}[/dim]")
        console.print(f"[dim]Size: {output.stat().st_size:,} bytes[/dim]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Failed to export data[/bold red]")
        console.print(f"[red]Error: {str(e)}[/red]\n")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    app()
