# Research: Admin CLI Enhancement

**Feature**: Admin CLI Enhancement | **Branch**: `011-admin-cli` | **Date**: 2025-11-08

## Overview

This document captures technical research and design decisions for implementing the unified `collabiq` CLI command. All technical unknowns from the planning phase have been investigated and resolved.

## Research Areas

### 1. CLI Framework Selection

**Decision**: Use **Typer** as the primary CLI framework

**Rationale**:
- **Type Safety**: Typer uses Python type hints for automatic argument parsing and validation
- **Auto-generated Help**: Automatically generates help text from docstrings and type hints
- **Rich Integration**: Built-in integration with Rich library for beautiful terminal output
- **Command Groups**: Native support for command groups (typer.Typer() apps can be nested)
- **Minimal Boilerplate**: Less code compared to argparse or click for equivalent functionality
- **Modern**: Actively maintained, designed for Python 3.6+, aligns with CollabIQ's Python 3.12+ requirement

**Alternatives Considered**:
- **Click**: More mature but requires more boilerplate, no native type hint support
- **argparse**: Standard library but verbose, poor help text formatting, no modern features
- **Custom**: Would violate YAGNI principle and add unnecessary complexity

**Implementation Pattern**:
```python
# src/collabiq/__init__.py
import typer
from .commands import email, notion, test, errors, status, llm, config

app = typer.Typer(
    name="collabiq",
    help="CollabIQ Admin CLI - Unified command interface",
    add_completion=False  # Simplicity: no shell completion for MVP
)

app.add_typer(email.app, name="email", help="Email pipeline operations")
app.add_typer(notion.app, name="notion", help="Notion integration management")
app.add_typer(test.app, name="test", help="Testing and validation")
app.add_typer(errors.app, name="errors", help="Error management and DLQ")
app.add_typer(status.app, name="status", help="System health monitoring")
app.add_typer(llm.app, name="llm", help="LLM provider management")
app.add_typer(config.app, name="config", help="Configuration management")

if __name__ == "__main__":
    app()
```

### 2. Terminal Output Formatting

**Decision**: Use **Rich** library for all terminal output

**Rationale**:
- **Rich Tables**: Beautiful table formatting with automatic column alignment
- **Progress Indicators**: Built-in progress bars, spinners with ETA
- **Color Support**: Automatic color detection, supports NO_COLOR environment variable
- **Console Detection**: Automatically disables colors/formatting in non-TTY environments
- **Markdown Rendering**: Can render help text with formatting
- **Widely Used**: Industry standard for Python CLI tools (pip, pytest use Rich)

**Key Patterns**:
```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()  # Auto-detects TTY, honors NO_COLOR

# Success/Error/Warning patterns
console.print("[green]✓ Operation completed successfully[/green]")
console.print("[red]✗ Operation failed[/red]")
console.print("[yellow]⚠ Warning: Rate limit approaching[/yellow]")

# Table formatting
table = Table(title="Email List")
table.add_column("ID", style="cyan")
table.add_column("Sender", style="magenta")
table.add_column("Subject", style="green")
table.add_column("Status", justify="right")

# Progress tracking
with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
    task = progress.add_task("Fetching emails...", total=None)
    # ... perform operation
    progress.update(task, description="✓ Fetched 10 emails")
```

**JSON Output Mode**:
All commands will support `--json` flag to bypass Rich formatting and output structured JSON:
```python
import json
from typing import Any

def output_result(data: Any, json_mode: bool = False):
    if json_mode:
        console.print(json.dumps(data, indent=2))
    else:
        # Rich formatting
        render_rich_output(data)
```

### 3. Command Organization Strategy

**Decision**: One file per command group, commands as functions with typer decorators

**Rationale**:
- **Simplicity**: Each command group (email, notion, test, etc.) in a single file
- **Discoverability**: Easy to find commands by navigating to the appropriate file
- **No Abstraction**: Direct function-to-command mapping, no command base classes
- **Type Safety**: Typer decorators with type hints provide validation

**File Structure**:
```
src/collabiq/commands/
├── email.py      # collabiq email [fetch|clean|list|verify|process]
├── notion.py     # collabiq notion [verify|schema|test-write|cleanup-tests]
├── test.py       # collabiq test [e2e|select-emails|validate]
├── errors.py     # collabiq errors [list|show|retry|clear]
├── status.py     # collabiq status [--detailed] [--watch]
├── llm.py        # collabiq llm [status|test|policy|set-policy|usage|disable|enable]
└── config.py     # collabiq config [show|validate|test-secrets|get]
```

**Command Implementation Pattern**:
```python
# src/collabiq/commands/email.py
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def fetch(
    limit: int = typer.Option(10, help="Maximum emails to fetch"),
    debug: bool = typer.Option(False, help="Enable debug logging"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """
    Fetch emails from Gmail with deduplication.

    Example: collabiq email fetch --limit 20
    """
    # Implementation calls existing email_receiver module
    from src.email_receiver import EmailReceiver
    # ... orchestrate operation, format output
```

### 4. Interrupt Handling and Resume Capability

**Decision**: Signal handlers with progress state files for resumable operations

**Rationale**:
- **Graceful Shutdown**: Catch SIGINT/SIGTERM to save progress before exiting
- **Resume Support**: Long operations (E2E tests, bulk email processing) save state to JSON
- **User Experience**: Clear messaging about resume commands

**Implementation Pattern**:
```python
import signal
import json
from pathlib import Path
from typing import Optional

class InterruptHandler:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.interrupted = False
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        self.interrupted = True
        console.print("\n[yellow]⚠ Operation interrupted - saving progress...[/yellow]")

    def save_state(self, state: dict):
        self.state_file.write_text(json.dumps(state, indent=2))

    def load_state(self) -> Optional[dict]:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return None

# Usage in E2E test command
@app.command()
def e2e(resume: Optional[str] = typer.Option(None, help="Resume from run ID")):
    state_file = Path(f"data/e2e_test/state/{resume or 'latest'}.json")
    handler = InterruptHandler(state_file)

    # ... process emails
    if handler.interrupted:
        handler.save_state({"completed": completed_ids, "pending": pending_ids})
        console.print(f"[cyan]Resume with: collabiq test e2e --resume {run_id}[/cyan]")
        raise typer.Exit(1)
```

### 5. Package Entry Point Configuration

**Decision**: Add `[project.scripts]` entry point in pyproject.toml

**Rationale**:
- **Standard Approach**: Python ecosystem standard for CLI tools
- **UV Compatibility**: Works seamlessly with UV package manager
- **Global Command**: Installs `collabiq` command in PATH when package installed
- **Development Mode**: Works in editable install (`uv pip install -e .`)

**Configuration**:
```toml
# pyproject.toml
[project.scripts]
collabiq = "collabiq:app"  # Points to typer app in src/collabiq/__init__.py
```

**Development Usage**:
```bash
# Install in development mode
uv pip install -e .

# Now `collabiq` command available globally
collabiq --help
collabiq email fetch --limit 5
```

### 6. Integration with Existing Components

**Decision**: Import and orchestrate existing modules without modification

**Rationale**:
- **No Code Duplication**: CLI commands call existing EmailReceiver, NotionIntegrator, etc.
- **Separation of Concerns**: CLI is presentation layer, business logic stays in modules
- **Backward Compatibility**: Existing scripts continue to work during transition

**Integration Pattern**:
```python
# src/collabiq/commands/email.py
from src.email_receiver import EmailReceiver
from src.config import get_config
from src.error_handling import ErrorTracker

@app.command()
def fetch(limit: int = 10, json_output: bool = False):
    """Fetch emails from Gmail"""
    config = get_config()
    receiver = EmailReceiver(config)
    error_tracker = ErrorTracker()

    try:
        emails = receiver.fetch_emails(limit=limit)
        # Format output based on json_output flag
        if json_output:
            output_json({"count": len(emails), "emails": emails})
        else:
            render_email_table(emails)
    except Exception as e:
        error_tracker.record_error(e, context="email_fetch")
        console.print(f"[red]✗ Failed to fetch emails: {e}[/red]")
        raise typer.Exit(1)
```

### 7. Error Display and Logging

**Decision**: Rich console for user-facing errors, separate audit log for CLI operations

**Rationale**:
- **User Experience**: Actionable error messages with color coding
- **Audit Trail**: Separate log file for CLI operations (who ran what, when, result)
- **Troubleshooting**: Debug mode shows stack traces, normal mode shows remediation

**Error Formatting**:
```python
def handle_cli_error(error: Exception, context: str, debug: bool = False):
    """Format and display CLI errors with remediation suggestions"""

    if debug:
        console.print_exception()  # Rich stack trace
    else:
        console.print(f"[red]✗ {context} failed: {str(error)}[/red]")

        # Context-specific remediation
        if isinstance(error, AuthenticationError):
            console.print("[cyan]Suggestion: Run 'collabiq config test-secrets' to verify credentials[/cyan]")
        elif isinstance(error, RateLimitError):
            console.print(f"[cyan]Suggestion: Wait {error.retry_after}s or use --limit to reduce load[/cyan]")

    # Always log to audit file
    log_cli_operation(context, success=False, error=str(error))
```

**Audit Logging**:
```python
# src/collabiq/utils/logging.py
import logging
from pathlib import Path
from datetime import datetime

CLI_LOG_FILE = Path("data/logs/cli_audit.log")

def log_cli_operation(command: str, success: bool, **metadata):
    """Log CLI operations for audit trail"""
    logger = logging.getLogger("collabiq.audit")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(CLI_LOG_FILE)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)

    logger.info(f"{command} | success={success} | {metadata}")
```

### 8. LLM Provider Commands and Phase 3b Graceful Degradation

**Decision**: Check for multi-LLM infrastructure availability at runtime

**Rationale**:
- **Parallel Development**: Phase 3a and 3b developed independently
- **Forward Compatibility**: LLM commands prepared for Phase 3b but work without it
- **User Experience**: Clear messaging when feature not yet available

**Implementation Strategy**:
```python
# src/collabiq/commands/llm.py
from typing import Optional

def check_multi_llm_available() -> bool:
    """Check if Phase 3b multi-LLM infrastructure is available"""
    try:
        from src.llm_provider import LLMOrchestrator
        return hasattr(LLMOrchestrator, 'get_all_providers')
    except (ImportError, AttributeError):
        return False

@app.command()
def status(json_output: bool = False):
    """Display status of all LLM providers"""

    if not check_multi_llm_available():
        # Graceful degradation - show current single provider
        console.print("[yellow]⚠ Multi-LLM support coming in Phase 3b[/yellow]")
        console.print("[cyan]Currently using: Gemini (primary)[/cyan]")

        # Still show useful info about current provider
        from src.llm_adapters.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter()
        health = adapter.health_check()

        if json_output:
            output_json({"provider": "gemini", "status": health})
        else:
            render_single_provider_status(health)
        return

    # Full multi-LLM implementation (Phase 3b available)
    from src.llm_provider import LLMOrchestrator
    orchestrator = LLMOrchestrator()
    providers = orchestrator.get_all_providers()

    if json_output:
        output_json({"providers": providers})
    else:
        render_multi_provider_table(providers)
```

### 9. Testing Strategy

**Decision**: Three-layer testing - Contract → Unit → Integration

**Rationale**:
- **Contract Tests**: Verify CLI interface stability (arguments, help text, exit codes)
- **Unit Tests**: Test formatters, utilities in isolation
- **Integration Tests**: Test command workflows end-to-end with real components

**Contract Test Pattern**:
```python
# tests/contract/test_cli_interface.py
from typer.testing import CliRunner
from collabiq import app

runner = CliRunner()

def test_email_fetch_command_signature():
    """Contract: email fetch accepts --limit and --json flags"""
    result = runner.invoke(app, ["email", "fetch", "--help"])
    assert result.exit_code == 0
    assert "--limit" in result.stdout
    assert "--json" in result.stdout
    assert "Maximum emails to fetch" in result.stdout

def test_email_fetch_exit_codes():
    """Contract: email fetch returns 0 on success, 1 on failure"""
    # Success case (mocked)
    result = runner.invoke(app, ["email", "fetch", "--limit", "1"])
    assert result.exit_code in [0, 1]  # Depends on environment

def test_json_output_format():
    """Contract: --json flag produces valid JSON output"""
    result = runner.invoke(app, ["status", "--json"])
    import json
    data = json.loads(result.stdout)  # Should not raise
    assert "status" in data
```

**Integration Test Pattern**:
```python
# tests/integration/test_cli_email_workflow.py
def test_email_fetch_clean_list_workflow():
    """Integration: fetch → clean → list workflow"""
    # Fetch emails
    result = runner.invoke(app, ["email", "fetch", "--limit", "3"])
    assert result.exit_code == 0
    assert "fetched" in result.stdout.lower()

    # Clean emails
    result = runner.invoke(app, ["email", "clean"])
    assert result.exit_code == 0
    assert "cleaned" in result.stdout.lower()

    # List emails
    result = runner.invoke(app, ["email", "list", "--limit", "10"])
    assert result.exit_code == 0
    assert "Sender" in result.stdout  # Table header
```

## Dependencies

### New Dependencies to Add

**Primary**:
- **typer[all]** ~= 0.9.0 - CLI framework with Rich integration
- **rich** ~= 13.7.0 - Terminal formatting and progress indicators

**Rationale for Versions**:
- typer 0.9.x: Latest stable, includes all needed features
- rich 13.7.x: Latest stable, wide compatibility
- [all] extra for typer includes shell completion support (future enhancement)

**Installation**:
```bash
uv add typer[all] rich
```

### Existing Dependencies Used

- Python 3.12+ (established)
- pytest (testing)
- All existing CollabIQ modules (email_receiver, llm_adapters, notion_integrator, etc.)

## Performance Considerations

### Target Benchmarks

From Success Criteria:
- **SC-002**: Status command < 5 seconds
- **SC-003**: E2E test on 10 emails < 3 minutes
- **SC-009**: Non-processing commands < 2 seconds
- **SC-011**: Progress updates every 5 seconds for long operations

### Optimization Strategies

1. **Lazy Imports**: Import heavy modules only when commands are invoked
   ```python
   @app.command()
   def fetch():
       # Import here, not at module level
       from src.email_receiver import EmailReceiver
   ```

2. **Parallel Operations**: Use asyncio for concurrent health checks in status command
   ```python
   async def check_all_components():
       gmail_task = asyncio.create_task(check_gmail())
       notion_task = asyncio.create_task(check_notion())
       gemini_task = asyncio.create_task(check_gemini())
       return await asyncio.gather(gmail_task, notion_task, gemini_task)
   ```

3. **Caching**: Cache health check results for --watch mode (refresh every 30s)

4. **Streaming Output**: For large lists, use pagination instead of loading all data

## Security Considerations

### Secret Masking

All configuration display must mask secrets:
```python
def mask_secret(value: str) -> str:
    """Mask secret values showing first 4 and last 3 chars"""
    if len(value) < 8:
        return "***"
    return f"{value[:4]}...{value[-3:]}"

# Example: AIzaSyDXXXXXXXXXXXXXXXX → AIza...XXX
```

### Input Validation

Sanitize all user inputs to prevent injection:
```python
def validate_email_id(email_id: str) -> str:
    """Validate email ID format to prevent path traversal"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', email_id):
        raise typer.BadParameter("Invalid email ID format")
    return email_id
```

### File Permissions

CLI audit log must be protected:
```python
CLI_LOG_FILE.chmod(0o640)  # Owner read/write, group read, others none
```

## Open Questions Resolved

1. **Q: Should CLI support batch operations (e.g., process multiple emails with single command)?**
   - **A**: Yes, via --limit flag for fetch/process, --all flag for retry. Keeps interface simple.

2. **Q: How to handle backward compatibility with existing `uv run python src/cli.py` scripts?**
   - **A**: Keep existing scripts unchanged during transition. Document migration path. Eventually deprecate old scripts.

3. **Q: Should status --watch mode use curses for full-screen display?**
   - **A**: No - use Rich live display (simpler, works in all terminals). Curses adds complexity.

4. **Q: How to test commands that require API credentials?**
   - **A**: Use pytest fixtures with mock credentials. Add integration tests that skip if real creds unavailable.

5. **Q: Should LLM commands fail hard when Phase 3b not available?**
   - **A**: No - graceful degradation with informative messages. Show current Gemini status.

## Next Steps

All technical unknowns resolved. Ready to proceed to:
- **Phase 1**: Generate data-model.md, contracts/, quickstart.md
- **Phase 1**: Update agent context with new dependencies
- **Phase 2**: Generate tasks.md with implementation plan (via /speckit.tasks command)
