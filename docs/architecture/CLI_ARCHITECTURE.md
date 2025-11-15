# CollabIQ CLI Architecture

## Overview

The CollabIQ CLI uses a **hierarchical subcommand structure** built with Typer. This architecture provides modularity, scalability, and clear command namespacing.

## Architecture Pattern

```
collabiq (main app)
├── llm (subcommand group)
│   ├── status
│   ├── test
│   ├── set-strategy
│   └── compare
├── test (subcommand group)
│   ├── e2e
│   ├── select-emails
│   └── validate
├── email (subcommand group)
│   ├── fetch
│   ├── clean
│   └── list
└── notion (subcommand group)
    ├── verify
    ├── schema
    └── write
```

## Implementation Structure

### 1. Main CLI Entry Point (`src/collabiq/cli.py`)

```python
app = typer.Typer(
    name="collabiq",
    help="CollabIQ Admin CLI - Unified command interface",
    add_completion=False,
    no_args_is_help=True,
)

@app.callback()
def main(ctx: typer.Context, debug: bool = ..., quiet: bool = ...):
    """Global options handler"""
    pass
```

### 2. Command Module Structure (`src/collabiq/commands/*.py`)

Each command module creates its own Typer app:

```python
# src/collabiq/commands/llm.py
llm_app = typer.Typer(
    name="llm",
    help="LLM provider management (status, test, strategy, routing)",
)

@llm_app.command()
def status(...):
    """View provider health status"""
    pass

@llm_app.command()
def test(provider: str):
    """Test provider connectivity"""
    pass
```

### 3. Registration (`src/collabiq/__init__.py`)

Subcommand apps are registered with the main app:

```python
from .cli import app
from .commands.llm import llm_app
from .commands.test import test_app

# Register subcommands
app.add_typer(llm_app, name="llm")
app.add_typer(test_app, name="test")
```

## Benefits of This Architecture

### 1. **Namespace Isolation**
- Commands are grouped logically: `collabiq llm test` vs `collabiq test e2e`
- No naming conflicts between modules
- Clear command hierarchy

### 2. **Modularity**
- Each module is self-contained
- Independent development and testing
- Easy to add/remove command groups

### 3. **Scalability**
- New command groups can be added without affecting existing ones
- Each module can grow independently
- Clear ownership boundaries

### 4. **User Experience**
- Contextual help at each level
- Logical command grouping
- Consistent interface patterns

### 5. **Code Organization**
- Each module handles its own:
  - Imports and dependencies
  - Error handling
  - Configuration
  - Help text

## Adding a New Command Group

### Step 1: Create the Command Module

```python
# src/collabiq/commands/newfeature.py
import typer

newfeature_app = typer.Typer(
    name="newfeature",
    help="New feature management",
)

@newfeature_app.command()
def action():
    """Perform an action"""
    pass
```

### Step 2: Register with Main App

```python
# src/collabiq/__init__.py
from .commands.newfeature import newfeature_app

app.add_typer(newfeature_app, name="newfeature")
```

### Step 3: Test the Command

```bash
collabiq newfeature --help
collabiq newfeature action
```

## Common Patterns

### Error Handling
```python
from collabiq.utils.logging import log_cli_error

try:
    # Command logic
    pass
except Exception as e:
    log_cli_error("command_name", e)
    raise typer.Exit(1)
```

### Progress Indicators
```python
from collabiq.formatters.spinner import create_spinner

with create_spinner("Loading...") as progress:
    # Long-running operation
    pass
```

### JSON Output Support
```python
@command()
def action(json_output: bool = typer.Option(False, "--json")):
    if json_output:
        console.print_json(data)
    else:
        # Rich formatted output
        pass
```

## Testing CLI Commands

Use the Typer testing utilities:

```python
from typer.testing import CliRunner
from collabiq.cli import app

runner = CliRunner()

def test_command():
    result = runner.invoke(app, ["llm", "status"])
    assert result.exit_code == 0
    assert "health" in result.stdout.lower()
```

## Directory Structure

```
src/collabiq/
├── __init__.py         # App registration
├── cli.py              # Main app definition
└── commands/           # Command modules
    ├── __init__.py
    ├── llm.py          # LLM commands
    ├── test.py         # Test commands
    ├── email.py        # Email commands
    └── notion.py       # Notion commands
```

## Migration from Flat Structure

If migrating from a flat command structure:

1. Create separate Typer apps for each command group
2. Move `@app.command()` decorators to `@group_app.command()`
3. Register group apps with main app using `app.add_typer()`
4. Update imports in `__init__.py`
5. Update tests to use new command paths

## Best Practices

1. **Keep command groups focused** - Each group should have a single responsibility
2. **Use consistent naming** - Follow patterns like `verb-noun` or `noun-verb`
3. **Provide comprehensive help** - Every command and option should have help text
4. **Support both interactive and scriptable modes** - Offer `--json` output options
5. **Handle errors gracefully** - Use proper exit codes and error messages
6. **Test command interfaces** - Not just the underlying logic

## Troubleshooting

### Command Not Found
- Ensure the subapp is registered in `__init__.py`
- Check that the module is imported correctly
- Verify the command decorator is on the right app

### Import Errors
- Use conditional imports for optional dependencies
- Handle ImportError gracefully with user-friendly messages

### Name Conflicts
- Each subcommand group has its own namespace
- Use descriptive command names within groups
- Consider command aliases for common operations

## Future Enhancements

1. **Plugin System** - Dynamic command loading from external packages
2. **Command Aliases** - Short forms for common commands
3. **Tab Completion** - Shell-specific completion scripts
4. **Command History** - Track and replay commands
5. **Interactive Mode** - REPL-style interface

---

*Last Updated: November 2024*
*Architecture Version: 2.0 (Hierarchical Subcommands)*