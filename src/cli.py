"""CLI entry point for manual testing of email reception pipeline.

Usage:
    # Fetch and clean emails
    uv run python src/cli.py fetch --max-results 10

    # Fetch only (no cleaning)
    uv run python src/cli.py fetch --max-results 5 --no-clean

    # Clean existing raw emails
    uv run python src/cli.py clean --input-dir data/raw/2025/10

    # Verify setup
    uv run python src/cli.py verify
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from config.logging_config import setup_logging
from config.settings import get_settings
from content_normalizer.normalizer import ContentNormalizer
from email_receiver.duplicate_tracker import DuplicateTracker
from email_receiver.gmail_receiver import GmailReceiver

app = typer.Typer(
    name="collabiq-email",
    help="CollabIQ Email Reception Pipeline CLI",
    add_completion=False,
)


@app.command()
def fetch(
    max_results: int = typer.Option(
        50, "--max-results", "-n", help="Maximum emails to fetch"
    ),
    clean: bool = typer.Option(
        True, "--clean/--no-clean", help="Clean emails after fetching"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
) -> None:
    """Fetch emails from Gmail and optionally clean them."""
    console = Console()
    # Setup
    settings = get_settings()
    setup_logging(level="DEBUG" if debug else settings.log_level)
    settings.create_directories()

    console.print("\n[bold cyan]CollabIQ Email Reception Pipeline[/bold cyan]")
    console.print(f"Fetching up to {max_results} emails...\n")

    # Initialize components
    tracker = DuplicateTracker()
    receiver = GmailReceiver(duplicate_tracker=tracker)

    try:
        # Connect to Gmail
        console.print("[yellow]Connecting to Gmail API...[/yellow]")
        receiver.connect()
        console.print("[green]✓ Connected to Gmail[/green]\n")

        # Fetch emails
        console.print(f"[yellow]Fetching emails (max: {max_results})...[/yellow]")
        raw_emails = receiver.fetch_emails(max_results=max_results)
        console.print(f"[green]✓ Fetched {len(raw_emails)} new emails[/green]\n")

        if not raw_emails:
            console.print("[yellow]No new emails to process[/yellow]")
            return

        # Display email summary
        table = Table(title="Fetched Emails")
        table.add_column("Message ID", style="cyan", no_wrap=True)
        table.add_column("Sender", style="magenta")
        table.add_column("Subject", style="green")
        table.add_column("Date", style="blue")

        for email in raw_emails[:10]:  # Show first 10
            table.add_row(
                email.metadata.message_id[:30] + "...",
                email.metadata.sender,
                email.metadata.subject[:40],
                email.metadata.received_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print()

        # Save raw emails
        console.print("[yellow]Saving raw emails...[/yellow]")
        for email in raw_emails:
            file_path = receiver.save_raw_email(email)
        console.print(f"[green]✓ Saved {len(raw_emails)} raw emails[/green]\n")

        # Clean emails if requested
        if clean:
            console.print("[yellow]Cleaning emails...[/yellow]")
            normalizer = ContentNormalizer()
            empty_count = 0

            for email in raw_emails:
                cleaned = normalizer.process_raw_email(email)
                normalizer.save_cleaned_email(cleaned)

                if cleaned.is_empty:
                    empty_count += 1

            console.print(f"[green]✓ Cleaned {len(raw_emails)} emails[/green]")
            if empty_count > 0:
                console.print(
                    f"[yellow]⚠ {empty_count} emails became empty after cleaning[/yellow]"
                )
            console.print()

        # Save duplicate tracker state
        tracker.save()
        console.print("[green]✓ Duplicate tracker state saved[/green]\n")

        # Summary
        console.print("[bold green]Pipeline completed successfully![/bold green]")

    except FileNotFoundError:
        console.print("[bold red]Error: credentials.json not found[/bold red]")
        console.print(
            "Please download Gmail API credentials and save as credentials.json"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if debug:
            raise
        sys.exit(1)


@app.command()
def clean_emails(
    input_dir: Path = typer.Option(
        Path("data/raw"), "--input-dir", "-i", help="Directory with raw emails"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
) -> None:
    """Clean existing raw emails from directory."""
    console = Console()
    settings = get_settings()
    setup_logging(level="DEBUG" if debug else settings.log_level)
    settings.create_directories()

    console.print("\n[bold cyan]CollabIQ Email Cleaning[/bold cyan]")
    console.print(f"Input directory: {input_dir}\n")

    # Find raw email files
    raw_files = list(input_dir.rglob("*.json"))

    if not raw_files:
        console.print(f"[yellow]No raw email files found in {input_dir}[/yellow]")
        return

    console.print(f"Found {len(raw_files)} raw email files")

    # Clean emails
    normalizer = ContentNormalizer()
    cleaned_count = 0
    empty_count = 0
    error_count = 0

    from models.raw_email import RawEmail

    for file_path in raw_files:
        try:
            # Load raw email
            raw_email = RawEmail.model_validate_json(file_path.read_text())

            # Clean and save
            cleaned = normalizer.process_raw_email(raw_email)
            normalizer.save_cleaned_email(cleaned)

            cleaned_count += 1
            if cleaned.is_empty:
                empty_count += 1

        except Exception as e:
            error_count += 1
            if debug:
                console.print(f"[red]Error processing {file_path.name}: {e}[/red]")

    console.print()
    console.print(f"[green]✓ Cleaned {cleaned_count} emails[/green]")
    if empty_count > 0:
        console.print(
            f"[yellow]⚠ {empty_count} emails became empty after cleaning[/yellow]"
        )
    if error_count > 0:
        console.print(f"[red]✗ {error_count} errors occurred[/red]")


@app.command()
def verify() -> None:
    """Verify setup and configuration."""
    console = Console()
    console.print("\n[bold cyan]CollabIQ Setup Verification[/bold cyan]\n")

    settings = get_settings()

    # Check credentials
    checks = []

    # Gmail credentials
    if settings.gmail_credentials_path.exists():
        checks.append(("Gmail credentials", True, str(settings.gmail_credentials_path)))
    else:
        checks.append(
            (
                "Gmail credentials",
                False,
                f"{settings.gmail_credentials_path} not found",
            )
        )

    # Directories
    dirs_to_check = [
        ("Data directory", settings.data_dir),
        ("Raw email directory", settings.raw_email_dir),
        ("Cleaned email directory", settings.cleaned_email_dir),
        ("Log directory", settings.log_dir),
    ]

    for name, path in dirs_to_check:
        checks.append((name, path.exists(), str(path)))

    # Display results
    table = Table(title="Configuration Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    for name, status, details in checks:
        status_str = "[green]✓ OK[/green]" if status else "[red]✗ FAIL[/red]"
        table.add_row(name, status_str, details)

    console.print(table)
    console.print()

    # Overall status
    all_passed = all(check[1] for check in checks)
    if all_passed:
        console.print("[bold green]✓ All checks passed![/bold green]")
    else:
        console.print(
            "[bold red]✗ Some checks failed. Please fix issues above.[/bold red]"
        )
        sys.exit(1)


if __name__ == "__main__":
    app()
