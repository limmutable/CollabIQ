# Command Group Organization

**Feature**: Admin CLI Enhancement | **Branch**: `011-admin-cli` | **Date**: 2025-11-08

## Overview

This document specifies how CLI commands are organized into logical groups, command routing, and the relationship between command groups and existing CollabIQ modules.

## Command Group Structure

### Group Hierarchy

```
collabiq (root)
├── email (FR-002)
│   ├── fetch
│   ├── clean
│   ├── list
│   ├── verify
│   └── process
├── notion (FR-002)
│   ├── verify
│   ├── schema
│   ├── test-write
│   └── cleanup-tests
├── test (FR-002)
│   ├── e2e
│   ├── select-emails
│   └── validate
├── errors (FR-002)
│   ├── list
│   ├── show <error-id>
│   ├── retry
│   └── clear
├── status (FR-002)
│   └── (no subcommands, options only)
├── llm (FR-002)
│   ├── status
│   ├── test <provider>
│   ├── policy
│   ├── set-policy <strategy>
│   ├── usage
│   ├── disable <provider>
│   └── enable <provider>
└── config (FR-002)
    ├── show
    ├── validate
    ├── test-secrets
    └── get <key>
```

## Group Definitions

### 1. email

**Purpose**: Manage email pipeline operations

**Module Integration**:
- `src/email_receiver/`: Email fetching, deduplication
- `src/content_normalizer/`: Email cleaning

**Commands** (5):
| Command | Module Function | FR |
|---------|----------------|-----|
| fetch | EmailReceiver.fetch_emails() | FR-011 |
| clean | ContentNormalizer.normalize_batch() | FR-012 |
| list | EmailReceiver.list_emails() | FR-013 |
| verify | EmailReceiver.verify_connection() | FR-014 |
| process | Orchestrates all pipeline stages | FR-015 |

**Common Options**:
- `--limit`: Limit items processed
- `--debug`: Enable debug logging
- `--json`: JSON output mode
- `--quiet`: Suppress non-error output

**Group Entry Point**:
```python
# src/collabiq/commands/email.py
import typer

app = typer.Typer(name="email", help="Email pipeline operations")

@app.command()
def fetch(limit: int = 10, debug: bool = False, json_output: bool = False):
    """Fetch emails from Gmail with deduplication"""
    # Implementation...

@app.command()
def clean(debug: bool = False, json_output: bool = False):
    """Normalize raw emails"""
    # Implementation...

# ... other commands
```

---

### 2. notion

**Purpose**: Manage Notion integration operations

**Module Integration**:
- `src/notion_integrator/`: Notion API operations, schema management

**Commands** (4):
| Command | Module Function | FR |
|---------|----------------|-----|
| verify | NotionIntegrator.verify_connection() | FR-020 |
| schema | NotionIntegrator.get_database_schema() | FR-021 |
| test-write | NotionIntegrator.test_write_and_cleanup() | FR-022 |
| cleanup-tests | NotionIntegrator.cleanup_test_entries() | FR-023 |

**Common Options**:
- `--debug`: Enable debug logging
- `--json`: JSON output mode
- `--yes`: Skip confirmation (cleanup-tests only)

**Group Entry Point**:
```python
# src/collabiq/commands/notion.py
import typer

app = typer.Typer(name="notion", help="Notion integration management")

@app.command()
def verify(debug: bool = False, json_output: bool = False):
    """Check Notion connection, auth, and schema"""
    # Implementation...

@app.command(name="test-write")
def test_write(debug: bool = False, json_output: bool = False):
    """Create test entry, verify, and cleanup"""
    # Implementation...

# ... other commands
```

---

### 3. test

**Purpose**: Execute E2E tests and validation

**Module Integration**:
- `src/e2e_test/`: E2E test infrastructure, test email selection

**Commands** (3):
| Command | Module Function | FR |
|---------|----------------|-----|
| e2e | E2ETestRunner.run_tests() | FR-027 |
| select-emails | E2ETestRunner.select_test_emails() | FR-029 |
| validate | QuickValidator.run_checks() | FR-030 |

**E2E Command Options**:
- `--all`: Test all configured emails
- `--limit`: Limit number of emails
- `--email-id`: Test specific email
- `--resume`: Resume interrupted run

**Group Entry Point**:
```python
# src/collabiq/commands/test.py
import typer
from typing import Optional

app = typer.Typer(name="test", help="Testing and validation")

@app.command()
def e2e(
    all: bool = False,
    limit: Optional[int] = None,
    email_id: Optional[str] = None,
    resume: Optional[str] = None,
    debug: bool = False,
    json_output: bool = False
):
    """Run end-to-end pipeline tests"""
    # Implementation...

# ... other commands
```

---

### 4. errors

**Purpose**: Manage error records and DLQ operations

**Module Integration**:
- `src/error_handling/`: Error tracking, DLQ, retry logic

**Commands** (4):
| Command | Module Function | FR |
|---------|----------------|-----|
| list | ErrorTracker.list_errors() | FR-035 |
| show | ErrorTracker.get_error_details() | FR-036 |
| retry | ErrorTracker.retry_errors() | FR-037 |
| clear | ErrorTracker.clear_errors() | FR-038 |

**List Command Options**:
- `--severity`: Filter by severity (critical, high, medium, low)
- `--since`: Filter by date
- `--limit`: Maximum errors to display

**Retry Command Options**:
- `--all`: Retry all retriable errors
- `--id`: Retry specific error
- `--since`: Retry errors since date

**Clear Command Options**:
- `--resolved`: Clear only resolved errors
- `--before`: Clear errors before date
- `--yes`: Skip confirmation

**Group Entry Point**:
```python
# src/collabiq/commands/errors.py
import typer
from typing import Optional

app = typer.Typer(name="errors", help="Error management and DLQ operations")

@app.command()
def list(
    severity: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 20,
    debug: bool = False,
    json_output: bool = False
):
    """List failed operations with filtering"""
    # Implementation...

@app.command()
def show(
    error_id: str,
    debug: bool = False,
    json_output: bool = False
):
    """Display full error details including remediation"""
    # Implementation...

# ... other commands
```

---

### 5. status

**Purpose**: Monitor system health and component status

**Module Integration**:
- `src/email_receiver/`: Gmail health check
- `src/notion_integrator/`: Notion health check
- `src/llm_adapters/` or `src/llm_provider/`: LLM health checks

**Commands**: No subcommands (command is `collabiq status [OPTIONS]`)

**Options**:
- `--detailed`: Show extended metrics
- `--watch`: Continuous monitoring (30s refresh)
- `--debug`: Enable debug logging
- `--json`: JSON output mode

**Group Entry Point**:
```python
# src/collabiq/commands/status.py
import typer

app = typer.Typer(name="status", help="System health monitoring")

@app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    detailed: bool = False,
    watch: bool = False,
    debug: bool = False,
    json_output: bool = False
):
    """Display overall system health and component status"""
    if ctx.invoked_subcommand is None:
        # Execute status check
        # Implementation...
```

---

### 6. llm

**Purpose**: Manage LLM providers and orchestration

**Module Integration**:
- `src/llm_adapters/`: Single provider access (Phase 3a)
- `src/llm_provider/`: Multi-LLM orchestration (Phase 3b)

**Commands** (7):
| Command | Module Function | FR |
|---------|----------------|-----|
| status | LLMOrchestrator.get_all_providers() | FR-059 |
| test | LLMOrchestrator.test_provider() | FR-060 |
| policy | LLMOrchestrator.get_policy() | FR-061 |
| set-policy | LLMOrchestrator.set_policy() | FR-062 |
| usage | LLMOrchestrator.get_usage_stats() | FR-063 |
| disable | LLMOrchestrator.disable_provider() | FR-064 |
| enable | LLMOrchestrator.enable_provider() | FR-064 |

**Graceful Degradation** (Phase 3a):
When Phase 3b not implemented, commands check availability and show informative message with current Gemini status.

**Group Entry Point**:
```python
# src/collabiq/commands/llm.py
import typer

app = typer.Typer(name="llm", help="LLM provider management")

def check_multi_llm_available() -> bool:
    """Check if Phase 3b multi-LLM is implemented"""
    try:
        from src.llm_provider import LLMOrchestrator
        return hasattr(LLMOrchestrator, 'get_all_providers')
    except (ImportError, AttributeError):
        return False

@app.command()
def status(debug: bool = False, json_output: bool = False):
    """Display all LLM providers with health metrics"""
    if not check_multi_llm_available():
        # Show current Gemini status only
        show_gemini_status(json_output)
        return

    # Full multi-LLM implementation
    # Implementation...

# ... other commands
```

---

### 7. config

**Purpose**: Manage configuration and secrets

**Module Integration**:
- `src/config/`: Configuration loading, validation, Infisical access

**Commands** (4):
| Command | Module Function | FR |
|---------|----------------|-----|
| show | Config.show_all() | FR-051 |
| validate | Config.validate_all() | FR-053 |
| test-secrets | Config.test_infisical_connection() | FR-054 |
| get | Config.get_value() | FR-055 |

**Show Command**: Groups settings by category (Gmail, Notion, Gemini, LLM, System), masks secrets

**Group Entry Point**:
```python
# src/collabiq/commands/config.py
import typer

app = typer.Typer(name="config", help="Configuration management")

@app.command()
def show(debug: bool = False, json_output: bool = False):
    """Display all configuration with secrets masked"""
    # Implementation...

@app.command()
def get(
    key: str,
    debug: bool = False,
    json_output: bool = False
):
    """Display specific configuration value"""
    # Implementation...

# ... other commands
```

## Command Routing

### Main Application Entry Point

```python
# src/collabiq/__init__.py
import typer
from .commands import email, notion, test, errors, status, llm, config

app = typer.Typer(
    name="collabiq",
    help="CollabIQ Admin CLI - Unified command interface",
    add_completion=False  # No shell completion for MVP (simplicity)
)

# Register command groups
app.add_typer(email.app, name="email")
app.add_typer(notion.app, name="notion")
app.add_typer(test.app, name="test")
app.add_typer(errors.app, name="errors")
app.add_typer(status.app, name="status")
app.add_typer(llm.app, name="llm")
app.add_typer(config.app, name="config")

# Global callback for common setup
@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, help="Enable debug logging"),
    quiet: bool = typer.Option(False, help="Suppress non-error output"),
    no_color: bool = typer.Option(False, help="Disable color output")
):
    """CollabIQ Admin CLI - Unified command interface for all operations"""
    # Store global options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['quiet'] = quiet
    ctx.obj['no_color'] = no_color

    # Setup logging based on debug flag
    if debug:
        setup_debug_logging()

    # Disable colors if requested or NO_COLOR environment variable set
    if no_color or os.getenv('NO_COLOR'):
        disable_rich_colors()

if __name__ == "__main__":
    app()
```

### Package Entry Point Configuration

```toml
# pyproject.toml
[project.scripts]
collabiq = "collabiq:app"
```

**Installation**:
```bash
# Development mode (editable install)
uv pip install -e .

# Now `collabiq` command available globally
collabiq --help
collabiq email fetch --limit 5
```

## Module Integration Patterns

### Pattern 1: Direct Module Import

For straightforward operations:

```python
# src/collabiq/commands/email.py
from src.email_receiver import EmailReceiver
from src.config import get_config

@app.command()
def fetch(limit: int = 10, json_output: bool = False):
    """Fetch emails from Gmail"""
    config = get_config()
    receiver = EmailReceiver(config)

    try:
        emails = receiver.fetch_emails(limit=limit)
        if json_output:
            output_json({"count": len(emails), "emails": emails})
        else:
            render_email_table(emails)
    except Exception as e:
        handle_cli_error(e, "Email fetch")
        raise typer.Exit(1)
```

### Pattern 2: Orchestration

For complex workflows spanning multiple modules:

```python
# src/collabiq/commands/email.py
from src.email_receiver import EmailReceiver
from src.content_normalizer import ContentNormalizer
from src.llm_adapters import get_llm_adapter
from src.notion_integrator import NotionIntegrator
from src.error_handling import ErrorTracker

@app.command()
def process(limit: int = 10, json_output: bool = False):
    """Run full pipeline: fetch → clean → extract → write"""
    config = get_config()
    receiver = EmailReceiver(config)
    normalizer = ContentNormalizer()
    llm = get_llm_adapter(config)
    notion = NotionIntegrator(config)
    error_tracker = ErrorTracker()

    results = {
        "fetched": 0,
        "cleaned": 0,
        "extracted": 0,
        "written": 0,
        "failed": 0
    }

    with Progress() as progress:
        task = progress.add_task("Processing emails...", total=None)

        # Stage 1: Fetch
        emails = receiver.fetch_emails(limit=limit)
        results["fetched"] = len(emails)
        progress.update(task, description=f"✓ Fetched {len(emails)} emails")

        # Stage 2: Clean
        cleaned = normalizer.normalize_batch(emails)
        results["cleaned"] = len(cleaned)
        progress.update(task, description=f"✓ Cleaned {len(cleaned)} emails")

        # Stage 3: Extract (with error handling)
        for email in cleaned:
            try:
                entities = llm.extract_entities(email)
                results["extracted"] += 1

                # Stage 4: Write to Notion
                notion.create_entry(entities)
                results["written"] += 1
            except Exception as e:
                error_tracker.record_error(e, context={"email_id": email.id})
                results["failed"] += 1

        progress.update(task, description="✓ Pipeline complete")

    # Output results
    if json_output:
        output_json({"status": "success", "data": results})
    else:
        render_pipeline_summary(results)

    # Exit with error if any failures
    if results["failed"] > 0:
        raise typer.Exit(1)
```

### Pattern 3: Graceful Degradation (LLM Commands)

For features with optional dependencies (Phase 3b):

```python
# src/collabiq/commands/llm.py
@app.command()
def status(json_output: bool = False):
    """Display LLM provider status"""

    # Check if Phase 3b multi-LLM available
    if not check_multi_llm_available():
        # Graceful degradation - show current single provider
        console.print("[yellow]⚠ Multi-LLM support coming in Phase 3b[/yellow]")
        console.print("[cyan]Currently using: Gemini (primary)[/cyan]")

        from src.llm_adapters.gemini_adapter import GeminiAdapter
        adapter = GeminiAdapter()
        health = adapter.health_check()

        if json_output:
            output_json({
                "provider": "gemini",
                "status": health["status"],
                "response_time_ms": health.get("response_time_ms")
            })
        else:
            render_single_provider_status(health)
        return

    # Full multi-LLM implementation (Phase 3b available)
    from src.llm_provider import LLMOrchestrator
    orchestrator = LLMOrchestrator()
    providers = orchestrator.get_all_providers()

    if json_output:
        output_json({"providers": [p.to_dict() for p in providers]})
    else:
        render_multi_provider_table(providers)
```

## Command Group Testing Strategy

### Contract Tests Per Group

Each command group must have contract tests verifying:

```python
# tests/contract/test_cli_email_group.py
def test_email_group_registration():
    """Contract: email group is registered with main app"""
    result = runner.invoke(app, ["--help"])
    assert "email" in result.stdout
    assert "Email pipeline operations" in result.stdout

def test_email_group_commands():
    """Contract: email group has all required commands"""
    result = runner.invoke(app, ["email", "--help"])
    assert "fetch" in result.stdout
    assert "clean" in result.stdout
    assert "list" in result.stdout
    assert "verify" in result.stdout
    assert "process" in result.stdout

def test_email_fetch_signature():
    """Contract: email fetch has documented signature"""
    result = runner.invoke(app, ["email", "fetch", "--help"])
    assert "--limit" in result.stdout
    assert "--json" in result.stdout
    assert "Example:" in result.stdout  # Usage example present
```

### Integration Tests Per Group

```python
# tests/integration/test_cli_email_workflow.py
def test_email_pipeline_workflow():
    """Integration: fetch → clean → process workflow"""
    # Fetch emails
    result = runner.invoke(app, ["email", "fetch", "--limit", "3"])
    assert result.exit_code == 0

    # Clean emails
    result = runner.invoke(app, ["email", "clean"])
    assert result.exit_code == 0

    # Full process
    result = runner.invoke(app, ["email", "process", "--limit", "1"])
    assert result.exit_code in [0, 1]  # Depends on environment
```

## Summary

**7 Command Groups**:
1. `email` (5 commands) - Email pipeline operations
2. `notion` (4 commands) - Notion integration management
3. `test` (3 commands) - E2E testing and validation
4. `errors` (4 commands) - Error management and DLQ
5. `status` (no subcommands) - System health monitoring
6. `llm` (7 commands) - LLM provider management
7. `config` (4 commands) - Configuration management

**Total**: 30+ commands across 7 groups

**Module Integration**: CLI orchestrates existing components without modifying them

**Graceful Degradation**: LLM commands work in both Phase 3a (Gemini only) and Phase 3b (multi-LLM)

**Testing Strategy**: Contract tests (interface stability) + Integration tests (workflows)
