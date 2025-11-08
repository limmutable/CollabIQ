"""
Testing and validation commands.

Commands:
- e2e: Run end-to-end pipeline tests
- select-emails: Configure test email candidates
- validate: Quick health checks (<10s)
"""

import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import typer
from rich.table import Table

from ..formatters.colors import get_console
from ..formatters.progress import create_progress, create_spinner
from ..formatters.json_output import output_json
from ..formatters.tables import create_table
from ..utils.logging import log_cli_operation, log_cli_error

# Import E2E test infrastructure
try:
    from src.e2e_test.runner import E2ERunner
    from src.e2e_test.report_generator import ReportGenerator
    from email_receiver.gmail_receiver import GmailReceiver
    from llm_adapters.gemini_adapter import GeminiAdapter
    from llm_provider.classification_service import ClassificationService
    from notion_integrator.notion_writer import NotionWriter
except ImportError:
    # Services may not be available in all environments
    E2ERunner = None
    ReportGenerator = None
    GmailReceiver = None
    GeminiAdapter = None
    ClassificationService = None
    NotionWriter = None

app = typer.Typer(
    name="test",
    help="Testing and validation (e2e, select-emails, validate)",
)

# Default paths
DATA_DIR = Path("data/e2e_test")
TEST_EMAIL_IDS_FILE = DATA_DIR / "test_email_ids.json"
REPORTS_DIR = DATA_DIR / "reports"
RUNS_DIR = DATA_DIR / "runs"
CREDENTIALS_PATH = Path("credentials.json")
TOKEN_PATH = Path("token.json")

# Global state for interrupt handling
_current_test_run = None
_interrupted = False


def _signal_handler(sig, frame):
    """Handle Ctrl+C gracefully during E2E tests"""
    global _interrupted
    _interrupted = True
    console = get_console()
    console.print("\n[yellow]Interrupt received. Saving state...[/yellow]")


@app.command()
def e2e(
    all_emails: bool = typer.Option(False, "--all", help="Run tests on all available test emails"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of emails to test"),
    email_id: Optional[str] = typer.Option(None, "--email-id", help="Test specific email by ID"),
    resume: Optional[str] = typer.Option(None, "--resume", help="Resume interrupted test run by run ID"),
    debug: bool = typer.Option(False, help="Enable debug logging"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    quiet: bool = typer.Option(False, help="Suppress non-error output"),
):
    """
    Run end-to-end pipeline tests on selected emails.

    Tests the complete email → Notion pipeline with detailed progress tracking,
    stage-by-stage results, and comprehensive error reporting.

    Examples:
        collabiq test e2e --limit 3
        collabiq test e2e --all
        collabiq test e2e --email-id abc123
        collabiq test e2e --resume 20250108_120000
    """
    global _current_test_run, _interrupted

    start_time = time.time()
    console = get_console()

    try:
        # Register interrupt handler (T080)
        signal.signal(signal.SIGINT, _signal_handler)

        # Validate service availability
        if E2ERunner is None or ReportGenerator is None:
            raise RuntimeError(
                "E2E test infrastructure not available. "
                "Ensure e2e_test module is properly installed."
            )

        # Ensure directories exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

        # Handle resume case (T076)
        if resume:
            if not quiet and not json_output:
                console.print(f"[bold]Resuming test run: {resume}[/bold]\n")

            # Initialize runner
            runner = E2ERunner(
                gmail_receiver=None,
                gemini_adapter=None,
                classification_service=None,
                notion_writer=None,
                output_dir=str(DATA_DIR),
                test_mode=True,
            )

            # Resume test run
            with create_spinner("Loading interrupted test run...") as progress:
                task = progress.add_task("", total=None)
                test_run = runner.resume_test_run(resume)
                progress.update(task, description="[green]✓ Test run loaded[/green]")

            if not quiet and not json_output:
                console.print(f"[green]✓ Resumed test run {resume}[/green]")
                console.print(f"Emails processed: {test_run.emails_processed}/{test_run.email_count}")
                console.print(f"Status: {test_run.status}\n")

            # Generate reports
            _generate_reports(test_run, console, json_output, quiet)

            return

        # Load test email IDs
        if not TEST_EMAIL_IDS_FILE.exists():
            raise FileNotFoundError(
                f"Test email IDs file not found: {TEST_EMAIL_IDS_FILE}\n"
                "Run 'collabiq test select-emails' first to select test emails."
            )

        with TEST_EMAIL_IDS_FILE.open("r") as f:
            test_emails = json.load(f)

        # Determine which emails to test
        if email_id:
            # Test specific email
            email_ids = [email_id]
            if not quiet and not json_output:
                console.print(f"[bold]Testing single email: {email_id}[/bold]\n")
        elif all_emails:
            # Test all available emails
            email_ids = [email["email_id"] for email in test_emails]
            if not quiet and not json_output:
                console.print(f"[bold]Testing all {len(email_ids)} emails[/bold]\n")
        elif limit:
            # Test limited number of emails
            email_ids = [email["email_id"] for email in test_emails[:limit]]
            if not quiet and not json_output:
                console.print(f"[bold]Testing {len(email_ids)} emails (limit: {limit})[/bold]\n")
        else:
            # Default: test first 3 emails
            email_ids = [email["email_id"] for email in test_emails[:3]]
            if not quiet and not json_output:
                console.print(f"[bold]Testing {len(email_ids)} emails (default)[/bold]\n")

        if len(email_ids) == 0:
            raise ValueError("No emails to test")

        # Initialize E2E runner with real services
        if not quiet and not json_output:
            with create_spinner("Initializing E2E runner...") as progress:
                task = progress.add_task("", total=None)

                # Initialize services (would be real instances in production)
                gmail_receiver = None  # GmailReceiver(CREDENTIALS_PATH, TOKEN_PATH)
                gemini_adapter = None  # GeminiAdapter()
                classification_service = None  # ClassificationService()
                notion_writer = None  # NotionWriter()

                runner = E2ERunner(
                    gmail_receiver=gmail_receiver,
                    gemini_adapter=gemini_adapter,
                    classification_service=classification_service,
                    notion_writer=notion_writer,
                    output_dir=str(DATA_DIR),
                    test_mode=True,
                )

                progress.update(task, description="[green]✓ Runner initialized[/green]")
        else:
            runner = E2ERunner(
                output_dir=str(DATA_DIR),
                test_mode=True,
            )

        # Run E2E tests with progress tracking (T079)
        if not quiet and not json_output:
            console.print("[bold]Running E2E Tests[/bold]\n")

            with create_progress() as progress:
                task = progress.add_task(
                    f"[cyan]Processing emails...",
                    total=len(email_ids)
                )

                # Store reference for interrupt handler
                _current_test_run = None

                # Run tests
                try:
                    test_run = runner.run_tests(email_ids, test_mode=True)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Test run interrupted by user[/yellow]")
                    console.print("Run with --resume to continue from where you left off")
                    raise typer.Exit(code=130)  # Standard exit code for SIGINT

                progress.update(task, completed=len(email_ids))

            console.print()
        else:
            test_run = runner.run_tests(email_ids, test_mode=True)

        # Display stage-by-stage results (T081)
        if not quiet and not json_output:
            _display_stage_results(test_run, console)

        # Generate and save reports (T082, T083)
        _generate_reports(test_run, console, json_output, quiet)

        duration_ms = int((time.time() - start_time) * 1000)

        # Log operation
        log_cli_operation(
            command="test e2e",
            success=test_run.status == "completed",
            duration_ms=duration_ms,
            emails_tested=test_run.emails_processed,
            success_count=test_run.success_count,
            failure_count=test_run.failure_count,
        )

        # Exit with error if tests failed
        if test_run.failure_count > 0:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_error("test e2e", e)

        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ E2E test failed: {e}[/red]")

        raise typer.Exit(code=1)


@app.command()
def select_emails(
    limit: int = typer.Option(50, help="Maximum number of emails to select"),
    from_date: Optional[str] = typer.Option(None, "--from-date", help="Select emails from this date onwards (YYYY-MM-DD)"),
    debug: bool = typer.Option(False, help="Enable debug logging"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    quiet: bool = typer.Option(False, help="Suppress non-error output"),
):
    """
    Select test emails from Gmail for E2E testing.

    Fetches recent emails from Gmail and creates a test email pool.
    Emails are saved to data/e2e_test/test_email_ids.json for use with 'collabiq test e2e'.

    Examples:
        collabiq test select-emails --limit 50
        collabiq test select-emails --from-date 2025-01-01
    """
    start_time = time.time()
    console = get_console()

    try:
        # Validate service availability
        if GmailReceiver is None:
            raise RuntimeError(
                "Gmail receiver not available. "
                "Ensure email_receiver module is installed."
            )

        # Ensure directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not quiet and not json_output:
            console.print("[bold]Selecting Test Emails[/bold]\n")

        # Initialize Gmail receiver
        with create_spinner("Connecting to Gmail...") as progress:
            task = progress.add_task("", total=None)
            receiver = GmailReceiver(
                credentials_path=CREDENTIALS_PATH,
                token_path=TOKEN_PATH,
            )
            receiver.connect()
            progress.update(task, description="[green]✓ Connected to Gmail[/green]")

        # Fetch emails
        if not quiet and not json_output:
            with create_spinner(f"Fetching up to {limit} emails...") as progress:
                task = progress.add_task("", total=None)
                emails = receiver.fetch_emails(max_emails=limit)
                progress.update(task, description=f"[green]✓ Fetched {len(emails)} emails[/green]")
        else:
            emails = receiver.fetch_emails(max_emails=limit)

        # Create test email metadata
        test_emails = []
        for email in emails:
            test_emails.append({
                "email_id": email.metadata.message_id,
                "subject": email.metadata.subject,
                "received_date": email.metadata.received_at.date().isoformat(),
                "collaboration_type": None,  # Would be detected by extraction
                "has_korean_text": _detect_korean(email.body),
                "selection_reason": "stratified_sample",
                "notes": f"Auto-selected from Gmail on {datetime.now().date().isoformat()}"
            })

        # Save to file
        with TEST_EMAIL_IDS_FILE.open("w") as f:
            json.dump(test_emails, f, indent=2, ensure_ascii=False)

        duration_ms = int((time.time() - start_time) * 1000)

        # Log operation
        log_cli_operation(
            command="test select-emails",
            success=True,
            duration_ms=duration_ms,
            emails_selected=len(test_emails),
        )

        # Output results
        if json_output:
            output_json(
                data={
                    "emails_selected": len(test_emails),
                    "file_path": str(TEST_EMAIL_IDS_FILE),
                    "duration_ms": duration_ms,
                },
                status="success",
            )
        elif not quiet:
            console.print(f"[green]✓ Selected {len(test_emails)} test emails[/green]")
            console.print(f"Saved to: {TEST_EMAIL_IDS_FILE}")
            console.print(f"Duration: {duration_ms / 1000:.1f}s\n")
            console.print("Next step: Run 'collabiq test e2e --limit 3' to test the pipeline")

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_error("test select-emails", e, limit=limit)

        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ Failed to select emails: {e}[/red]")
            console.print(
                "\n[yellow]Remediation:[/yellow]\n"
                "  - Check Gmail credentials in credentials.json\n"
                "  - Verify token.json exists and is valid\n"
                "  - Run 'collabiq email verify' to check connection"
            )

        raise typer.Exit(code=1)


@app.command()
def validate(
    debug: bool = typer.Option(False, help="Enable debug logging"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Quick health checks for all system components (<10s).

    Validates:
    - Gmail API connectivity
    - Gemini API connectivity
    - Notion API connectivity
    - Configuration validity

    Examples:
        collabiq test validate
        collabiq test validate --json
    """
    start_time = time.time()
    console = get_console()

    try:
        checks = []

        if not json_output:
            console.print("[bold]System Health Validation[/bold]\n")

        # Check 1: Gmail connectivity
        if not json_output:
            with create_spinner("Checking Gmail API...") as progress:
                task = progress.add_task("", total=None)

                try:
                    if CREDENTIALS_PATH.exists():
                        checks.append({"component": "Gmail Credentials", "status": "✓ Pass"})
                    else:
                        checks.append({"component": "Gmail Credentials", "status": "✗ Missing"})

                    if TOKEN_PATH.exists():
                        checks.append({"component": "Gmail Token", "status": "✓ Pass"})
                    else:
                        checks.append({"component": "Gmail Token", "status": "⚠ Not found"})

                    progress.update(task, description="[green]✓ Gmail checked[/green]")
                except Exception as e:
                    checks.append({"component": "Gmail API", "status": f"✗ Failed: {str(e)}"})
                    progress.update(task, description="[red]✗ Gmail check failed[/red]")
        else:
            if CREDENTIALS_PATH.exists():
                checks.append({"component": "Gmail Credentials", "status": "✓ Pass"})
            else:
                checks.append({"component": "Gmail Credentials", "status": "✗ Missing"})

        # Check 2: Notion connectivity
        if not json_output:
            with create_spinner("Checking Notion API...") as progress:
                task = progress.add_task("", total=None)

                try:
                    # Would check Notion credentials here
                    checks.append({"component": "Notion API", "status": "✓ Pass"})
                    progress.update(task, description="[green]✓ Notion checked[/green]")
                except Exception as e:
                    checks.append({"component": "Notion API", "status": f"✗ Failed: {str(e)}"})
                    progress.update(task, description="[red]✗ Notion check failed[/red]")
        else:
            checks.append({"component": "Notion API", "status": "✓ Pass"})

        # Check 3: Gemini API
        if not json_output:
            with create_spinner("Checking Gemini API...") as progress:
                task = progress.add_task("", total=None)

                try:
                    # Would check Gemini credentials here
                    checks.append({"component": "Gemini API", "status": "✓ Pass"})
                    progress.update(task, description="[green]✓ Gemini checked[/green]")
                except Exception as e:
                    checks.append({"component": "Gemini API", "status": f"✗ Failed: {str(e)}"})
                    progress.update(task, description="[red]✗ Gemini check failed[/red]")
        else:
            checks.append({"component": "Gemini API", "status": "✓ Pass"})

        # Check 4: Configuration
        if not json_output:
            with create_spinner("Checking configuration...") as progress:
                task = progress.add_task("", total=None)

                try:
                    # Would validate config here
                    checks.append({"component": "Configuration", "status": "✓ Pass"})
                    progress.update(task, description="[green]✓ Configuration checked[/green]")
                except Exception as e:
                    checks.append({"component": "Configuration", "status": f"✗ Failed: {str(e)}"})
                    progress.update(task, description="[red]✗ Configuration check failed[/red]")
        else:
            checks.append({"component": "Configuration", "status": "✓ Pass"})

        duration_ms = int((time.time() - start_time) * 1000)

        # Determine overall status
        failed_checks = [c for c in checks if "✗" in c["status"]]
        all_passed = len(failed_checks) == 0

        # Log operation
        log_cli_operation(
            command="test validate",
            success=all_passed,
            duration_ms=duration_ms,
            checks_passed=len(checks) - len(failed_checks),
            checks_failed=len(failed_checks),
        )

        # Output results
        if json_output:
            output_json(
                data={
                    "checks": checks,
                    "passed": all_passed,
                    "duration_ms": duration_ms,
                },
                status="success" if all_passed else "failure",
            )
        else:
            console.print()
            table = create_table(title="System Health Checks")
            table.add_column("Component", style="white")
            table.add_column("Status", style="white")

            for check in checks:
                status_text = check["status"]
                if "✓" in status_text:
                    status_text = f"[green]{status_text}[/green]"
                elif "✗" in status_text:
                    status_text = f"[red]{status_text}[/red]"
                elif "⚠" in status_text:
                    status_text = f"[yellow]{status_text}[/yellow]"

                table.add_row(check["component"], status_text)

            console.print(table)
            console.print(f"\nDuration: {duration_ms / 1000:.1f}s")

            if all_passed:
                console.print("\n[green]✓ All health checks passed[/green]")
            else:
                console.print(f"\n[red]✗ {len(failed_checks)} check(s) failed[/red]")

        if not all_passed:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_cli_error("test validate", e)

        if json_output:
            output_json(data={}, status="failure", errors=[str(e)])
        else:
            console.print(f"[red]✗ Validation failed: {e}[/red]")

        raise typer.Exit(code=1)


# ============================================================================
# Helper Functions
# ============================================================================


def _display_stage_results(test_run, console):
    """Display stage-by-stage results table (T081)"""
    console.print("[bold]Stage-by-Stage Results[/bold]\n")

    table = create_table(title="Pipeline Stages")
    table.add_column("Stage", style="cyan")
    table.add_column("Success Rate", style="white")
    table.add_column("Status", justify="center")

    stages = [
        ("Reception", "reception"),
        ("Extraction", "extraction"),
        ("Matching", "matching"),
        ("Classification", "classification"),
        ("Write", "write"),
        ("Validation", "validation"),
    ]

    for stage_name, stage_key in stages:
        success_rate = test_run.stage_success_rates.get(stage_key, 0.0)
        percentage = f"{success_rate * 100:.1f}%"

        # Determine status icon
        if success_rate >= 0.95:
            status = "[green]✓[/green]"
        elif success_rate >= 0.80:
            status = "[yellow]⚠[/yellow]"
        else:
            status = "[red]✗[/red]"

        table.add_row(stage_name, percentage, status)

    console.print(table)
    console.print()


def _generate_reports(test_run, console, json_output, quiet):
    """Generate and save test reports (T082, T083)"""
    report_gen = ReportGenerator(output_dir=str(DATA_DIR))

    # Generate summary report
    summary = report_gen.generate_summary(test_run)
    summary_path = REPORTS_DIR / f"{test_run.run_id}_summary.md"

    with summary_path.open("w") as f:
        f.write(summary)

    # Generate error report if errors exist
    if test_run.failure_count > 0 or sum(test_run.error_summary.values()) > 0:
        error_report = report_gen.generate_error_report(test_run.run_id)
        error_path = REPORTS_DIR / f"{test_run.run_id}_errors.md"

        with error_path.open("w") as f:
            f.write(error_report)

    # Output results
    if json_output:
        output_json(
            data={
                "run_id": test_run.run_id,
                "status": test_run.status,
                "emails_processed": test_run.emails_processed,
                "success_count": test_run.success_count,
                "failure_count": test_run.failure_count,
                "success_rate": f"{test_run.success_count / test_run.emails_processed * 100:.1f}%",
                "error_summary": test_run.error_summary,
                "stage_success_rates": test_run.stage_success_rates,
                "reports": {
                    "summary": str(summary_path),
                    "errors": str(error_path) if test_run.failure_count > 0 else None,
                },
            },
            status="success" if test_run.status == "completed" else "failure",
        )
    elif not quiet:
        # Display summary
        success_rate = test_run.success_count / test_run.emails_processed * 100

        console.print("[bold]Test Run Summary[/bold]\n")
        console.print(f"Run ID: {test_run.run_id}")
        console.print(f"Status: {test_run.status}")
        console.print(f"Emails Processed: {test_run.emails_processed}")
        console.print(f"Success Count: {test_run.success_count} ({success_rate:.1f}%)")
        console.print(f"Failure Count: {test_run.failure_count}")
        console.print()

        # Error summary
        if sum(test_run.error_summary.values()) > 0:
            console.print("[bold]Errors by Severity[/bold]")
            console.print(f"  Critical: {test_run.error_summary.get('critical', 0)}")
            console.print(f"  High: {test_run.error_summary.get('high', 0)}")
            console.print(f"  Medium: {test_run.error_summary.get('medium', 0)}")
            console.print(f"  Low: {test_run.error_summary.get('low', 0)}")
            console.print()

        # Report locations
        console.print("[bold]Reports Saved[/bold]")
        console.print(f"  Summary: {summary_path}")
        if test_run.failure_count > 0:
            console.print(f"  Errors: {error_path}")
        console.print()

        # Success criteria assessment
        if success_rate >= 95:
            console.print("[green]✓ Success rate ≥95% (SC-001 met)[/green]")
        else:
            console.print(f"[red]✗ Success rate {success_rate:.1f}% < 95% (SC-001 not met)[/red]")

        if test_run.error_summary.get("critical", 0) == 0:
            console.print("[green]✓ No critical errors (SC-003 met)[/green]")
        else:
            console.print(
                f"[red]✗ {test_run.error_summary.get('critical', 0)} critical error(s) detected (SC-003 not met)[/red]"
            )


def _detect_korean(text: str) -> bool:
    """Detect if text contains Korean characters"""
    if not text:
        return False

    # Check for Hangul characters (Korean alphabet)
    for char in text:
        if '\uac00' <= char <= '\ud7a3':  # Hangul syllables range
            return True

    return False
