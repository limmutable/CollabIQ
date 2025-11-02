"""CollabIQ CLI entry point."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

app = typer.Typer(
    name="collabiq",
    help="CollabIQ - Email-based collaboration tracking system",
    add_completion=False,
)
console = Console()


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


def main() -> None:
    """Main entry point for the CLI."""
    app()
