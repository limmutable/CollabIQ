# Data Model: Admin CLI Enhancement

**Feature**: Admin CLI Enhancement | **Branch**: `011-admin-cli` | **Date**: 2025-11-08

## Overview

This document defines the data entities used in the Admin CLI Enhancement feature. The CLI is a presentation layer, so most entities are **view models** (formatted representations of existing data) rather than new persistent entities.

## Core Entities

### 1. CLICommand

**Purpose**: Represents an executable CLI command with its metadata

**Attributes**:
- `name` (str): Command name (e.g., "fetch", "verify", "status")
- `group` (str): Command group (email, notion, test, errors, status, llm, config)
- `description` (str): Short description for help text
- `arguments` (List[CommandArgument]): Positional arguments
- `options` (List[CommandOption]): Optional flags and parameters
- `handler` (Callable): Function that executes the command
- `help_text` (str): Full help documentation with examples

**Relationships**:
- Belongs to one CommandGroup
- Has zero or more CommandArgument
- Has zero or more CommandOption

**Validation Rules**:
- `name` must be lowercase, alphanumeric with hyphens
- `group` must be one of: email, notion, test, errors, status, llm, config
- `handler` must accept arguments matching declared arguments/options

**Example**:
```python
CLICommand(
    name="fetch",
    group="email",
    description="Fetch emails from Gmail",
    arguments=[],
    options=[
        CommandOption(name="limit", type=int, default=10, help="Maximum emails to fetch"),
        CommandOption(name="json", type=bool, default=False, help="Output as JSON")
    ],
    handler=email_fetch_handler,
    help_text="Fetch emails from Gmail with deduplication.\n\nExample: collabiq email fetch --limit 20"
)
```

### 2. CommandGroup

**Purpose**: Logical grouping of related commands

**Attributes**:
- `name` (str): Group name (email, notion, test, errors, status, llm, config)
- `description` (str): Group description for help text
- `commands` (List[CLICommand]): Commands in this group
- `typer_app` (typer.Typer): Typer application instance for the group

**Relationships**:
- Has many CLICommand

**Validation Rules**:
- `name` must be unique across all groups
- `commands` list cannot be empty

**Example**:
```python
CommandGroup(
    name="email",
    description="Email pipeline operations",
    commands=[fetch_cmd, clean_cmd, list_cmd, verify_cmd, process_cmd],
    typer_app=email_app
)
```

### 3. OperationResult

**Purpose**: Execution outcome for a CLI command

**Attributes**:
- `success` (bool): Whether operation succeeded
- `status` (str): Status code (success, partial, failure, skipped)
- `message` (str): Human-readable result message
- `data` (Dict[str, Any]): Structured result data (for JSON output)
- `execution_time_ms` (int): Command execution duration in milliseconds
- `errors` (List[str]): Error messages if failed
- `warnings` (List[str]): Warning messages if degraded

**Validation Rules**:
- If `success=False`, `errors` must not be empty
- `execution_time_ms` must be >= 0

**State Transitions**:
- Initial → Running → Success
- Initial → Running → Partial (some items failed)
- Initial → Running → Failure

**Example**:
```python
OperationResult(
    success=True,
    status="success",
    message="Fetched 10 emails successfully",
    data={"count": 10, "duplicates_skipped": 2, "emails": [...]},
    execution_time_ms=1250,
    errors=[],
    warnings=["Rate limit at 80% capacity"]
)
```

### 4. ProgressIndicator

**Purpose**: Visual feedback for long-running operations

**Attributes**:
- `type` (str): Indicator type (spinner, bar, percentage, text)
- `description` (str): Current operation description
- `total` (Optional[int]): Total items to process (for progress bar)
- `completed` (int): Items completed so far
- `eta_seconds` (Optional[int]): Estimated time remaining

**Relationships**:
- Associated with one OperationResult

**Validation Rules**:
- If `type=bar`, `total` must be set
- `completed` must be <= `total` (if total is set)

**Example**:
```python
ProgressIndicator(
    type="bar",
    description="Processing emails",
    total=100,
    completed=45,
    eta_seconds=30
)
```

### 5. ErrorRecord

**Purpose**: Detailed information about a failed operation (from error_handling module)

**Attributes** (Existing entity - CLI provides view):
- `error_id` (str): Unique error identifier
- `timestamp` (datetime): When error occurred
- `severity` (str): critical, high, medium, low
- `error_type` (str): Error category (auth, network, api_limit, validation, etc.)
- `message` (str): Human-readable error message
- `stack_trace` (Optional[str]): Full stack trace if available
- `context` (Dict[str, Any]): Additional context (email_id, operation, etc.)
- `retry_count` (int): Number of retry attempts
- `retriable` (bool): Whether error is transient and can be retried

**CLI View Operations**:
- List errors with filtering (by severity, date, type)
- Show full error details including remediation suggestions
- Retry retriable errors
- Clear resolved errors

**Example** (CLI display):
```python
{
    "error_id": "err_20251108_123456",
    "timestamp": "2025-11-08T12:34:56",
    "severity": "high",
    "error_type": "api_limit",
    "message": "Gemini API rate limit exceeded",
    "stack_trace": "...",
    "context": {"email_id": "email_001", "operation": "entity_extraction"},
    "retry_count": 0,
    "retriable": True,
    "remediation": "Wait 60 seconds or reduce --limit flag"
}
```

### 6. HealthStatus

**Purpose**: Health snapshot for a system component

**Attributes**:
- `component` (str): Component name (Gmail, Notion, Gemini, LLM Orchestrator)
- `status` (str): healthy, degraded, critical, offline
- `last_check` (datetime): When health was last checked
- `response_time_ms` (Optional[int]): Component response time
- `metrics` (Dict[str, Any]): Component-specific metrics
- `issues` (List[str]): Current issues or warnings
- `remediation` (List[str]): Suggested fixes for issues

**Validation Rules**:
- `status` must be one of: healthy, degraded, critical, offline
- If `status != healthy`, `issues` must not be empty

**Example**:
```python
HealthStatus(
    component="Gmail",
    status="healthy",
    last_check=datetime.now(),
    response_time_ms=145,
    metrics={
        "messages_today": 25,
        "quota_used_percent": 12,
        "last_fetch": "2025-11-08T10:30:00"
    },
    issues=[],
    remediation=[]
)
```

### 7. ConfigurationItem

**Purpose**: Single configuration setting with metadata

**Attributes**:
- `key` (str): Configuration key (e.g., "GEMINI_API_KEY", "NOTION_DATABASE_ID")
- `value` (str): Configuration value
- `source` (str): Where value came from (infisical, env, default)
- `category` (str): Grouping (Gmail, Notion, Gemini, LLM, System)
- `is_secret` (bool): Whether value should be masked
- `is_required` (bool): Whether setting is mandatory
- `is_valid` (bool): Whether value passes validation
- `validation_message` (Optional[str]): Validation error if invalid

**Validation Rules**:
- `key` must match pattern `^[A-Z][A-Z0-9_]*$`
- `source` must be one of: infisical, env, default
- If `is_required=True` and `value` is empty, `is_valid=False`

**Example**:
```python
ConfigurationItem(
    key="GEMINI_API_KEY",
    value="AIzaSyDXXXXXXXXXXXXXXXX",
    source="infisical",
    category="Gemini",
    is_secret=True,
    is_required=True,
    is_valid=True,
    validation_message=None
)
```

### 8. TestReport

**Purpose**: E2E test execution summary

**Attributes**:
- `run_id` (str): Unique test run identifier
- `timestamp` (datetime): When test started
- `total_emails` (int): Number of emails tested
- `passed` (int): Emails that passed all stages
- `failed` (int): Emails that failed any stage
- `skipped` (int): Emails skipped (already tested)
- `stage_results` (Dict[str, StageResult]): Results per pipeline stage
- `execution_time_ms` (int): Total test duration
- `errors` (List[ErrorRecord]): Errors encountered during testing
- `state_file` (Optional[Path]): Resume state file location

**Relationships**:
- Has many StageResult (one per pipeline stage)
- Has many ErrorRecord (if failures occurred)

**Validation Rules**:
- `passed + failed + skipped` must equal `total_emails`
- `stage_results` must include: reception, extraction, matching, classification, validation, write

**Example**:
```python
TestReport(
    run_id="test_20251108_123456",
    timestamp=datetime.now(),
    total_emails=10,
    passed=8,
    failed=2,
    skipped=0,
    stage_results={
        "reception": StageResult(passed=10, failed=0),
        "extraction": StageResult(passed=10, failed=0),
        "matching": StageResult(passed=9, failed=1),
        "classification": StageResult(passed=9, failed=1),
        "validation": StageResult(passed=8, failed=2),
        "write": StageResult(passed=8, failed=2)
    },
    execution_time_ms=145000,
    errors=[error1, error2],
    state_file=Path("data/e2e_test/state/test_20251108_123456.json")
)
```

### 9. LLMProvider (Phase 3b dependency)

**Purpose**: Language model provider information and health metrics

**Attributes**:
- `name` (str): Provider name (gemini, claude, openai)
- `display_name` (str): Human-readable name (Gemini, Claude 3.5, GPT-4)
- `status` (str): online, degraded, offline
- `health_check_time` (datetime): Last health check timestamp
- `response_time_ms` (int): Average response time
- `success_rate_percent` (float): Success rate over last 100 requests
- `token_usage` (Dict[str, int]): Token consumption stats
- `estimated_cost` (float): Estimated cost in USD
- `priority` (int): Orchestration priority (1=primary, 2=secondary, etc.)
- `enabled` (bool): Whether provider is active in orchestrator

**Relationships**:
- Managed by LLMOrchestrator (Phase 3b)

**Validation Rules**:
- `name` must be one of: gemini, claude, openai
- `priority` must be >= 1
- `success_rate_percent` must be 0-100

**Graceful Degradation** (Phase 3a):
When Phase 3b not implemented, CLI shows current Gemini adapter status:
```python
LLMProvider(
    name="gemini",
    display_name="Gemini (Primary)",
    status="online",
    health_check_time=datetime.now(),
    response_time_ms=850,
    success_rate_percent=98.5,
    token_usage={"prompt": 125000, "completion": 45000},
    estimated_cost=0.15,
    priority=1,
    enabled=True
)
```

When Phase 3b implemented, shows all providers:
```python
[
    LLMProvider(name="gemini", priority=1, status="online", ...),
    LLMProvider(name="claude", priority=2, status="online", ...),
    LLMProvider(name="openai", priority=3, status="degraded", ...)
]
```

## Supporting Entities

### 10. CommandArgument

**Purpose**: Positional argument for a CLI command

**Attributes**:
- `name` (str): Argument name
- `type` (type): Python type (str, int, Path, etc.)
- `help` (str): Help text
- `required` (bool): Whether argument is mandatory

**Example**:
```python
CommandArgument(
    name="email_id",
    type=str,
    help="Email ID to process",
    required=True
)
```

### 11. CommandOption

**Purpose**: Optional flag or parameter for a CLI command

**Attributes**:
- `name` (str): Option name (without -- prefix)
- `short_name` (Optional[str]): Short form (e.g., -l for --limit)
- `type` (type): Python type
- `default` (Any): Default value if not provided
- `help` (str): Help text
- `is_flag` (bool): Whether option is a boolean flag

**Example**:
```python
CommandOption(
    name="limit",
    short_name="l",
    type=int,
    default=10,
    help="Maximum items to return",
    is_flag=False
)
```

### 12. StageResult

**Purpose**: Test result for a single pipeline stage

**Attributes**:
- `stage_name` (str): Pipeline stage (reception, extraction, matching, etc.)
- `passed` (int): Emails that passed this stage
- `failed` (int): Emails that failed this stage
- `duration_ms` (int): Stage execution time
- `errors` (List[str]): Error messages from failures

**Example**:
```python
StageResult(
    stage_name="extraction",
    passed=9,
    failed=1,
    duration_ms=8500,
    errors=["Email email_007: Entity extraction timeout after 30s"]
)
```

## Entity Relationships Diagram

```
┌─────────────────┐
│  CommandGroup   │
│  - email        │
│  - notion       │
│  - test         │
│  - errors       │
│  - status       │
│  - llm          │
│  - config       │
└────────┬────────┘
         │ has many
         │
         ▼
┌─────────────────┐         ┌──────────────────┐
│   CLICommand    │◄────────│ CommandArgument  │
│  - name         │  has    │  - name          │
│  - group        │  many   │  - type          │
│  - handler      │         │  - required      │
└────────┬────────┘         └──────────────────┘
         │
         │ has many  ┌──────────────────┐
         └──────────►│  CommandOption   │
                     │  - name          │
                     │  - type          │
                     │  - default       │
                     └──────────────────┘

┌──────────────────┐
│ OperationResult  │
│  - success       │
│  - message       │
│  - data          │
│  - errors        │
└────────┬─────────┘
         │
         │ may have
         ▼
┌──────────────────┐
│ProgressIndicator│
│  - type          │
│  - description   │
│  - completed     │
│  - total         │
└──────────────────┘

┌─────────────────┐        ┌──────────────────┐
│   TestReport    │        │   StageResult    │
│  - run_id       │───────►│  - stage_name    │
│  - total_emails │ has    │  - passed        │
│  - passed       │ many   │  - failed        │
│  - failed       │        │  - errors        │
└────────┬────────┘        └──────────────────┘
         │
         │ has many
         ▼
┌─────────────────┐
│   ErrorRecord   │
│  - error_id     │
│  - severity     │
│  - message      │
│  - retriable    │
└─────────────────┘

┌─────────────────┐
│  HealthStatus   │
│  - component    │
│  - status       │
│  - metrics      │
│  - remediation  │
└─────────────────┘

┌──────────────────┐
│ ConfigurationItem│
│  - key           │
│  - value         │
│  - source        │
│  - is_secret     │
└──────────────────┘

┌─────────────────┐
│  LLMProvider    │  (Phase 3b)
│  - name         │
│  - status       │
│  - priority     │
│  - enabled      │
└─────────────────┘
```

## Data Flow

### Command Execution Flow

1. **User invokes command**: `collabiq email fetch --limit 5`
2. **Typer parses input**: Creates CLICommand with validated arguments/options
3. **Handler executes**: Calls existing components (EmailReceiver)
4. **Progress tracking**: Creates ProgressIndicator, updates during execution
5. **Result formatting**: Creates OperationResult with data
6. **Output rendering**: Formats as Rich table or JSON based on --json flag
7. **Audit logging**: Records command execution to CLI audit log

### Error Handling Flow

1. **Exception occurs**: During command execution
2. **Error capture**: Wrapped in try/except, creates ErrorRecord
3. **Error formatting**: Displays user-friendly message with remediation
4. **Error persistence**: Saved to error_handling module's DLQ
5. **CLI display**: Shows actionable error message, logs to audit file
6. **Exit**: Returns exit code 1 for failures, 0 for success

### Health Check Flow

1. **User runs**: `collabiq status`
2. **Parallel checks**: Async health checks for Gmail, Notion, Gemini (or LLM Orchestrator if Phase 3b)
3. **Result aggregation**: Combines into overall HealthStatus
4. **Metric collection**: Gathers recent activity, error rates, quota usage
5. **Display**: Renders as formatted table with color-coded status
6. **Watch mode**: If --watch, repeats every 30s with cached results

## Persistence Strategy

### CLI-Specific Data

**Audit Log** (`data/logs/cli_audit.log`):
- Format: Structured text log (timestamp, command, user, result)
- Retention: Rotate when > 10MB, keep last 3 files
- Permissions: 640 (owner read/write, group read)

**Resume State** (`data/e2e_test/state/*.json`):
- Format: JSON files with run_id as filename
- Lifetime: Deleted after successful completion or 7 days
- Content: TestReport partial state for resumption

**Configuration Cache**: No new cache - uses existing config module

**Error Records**: No new storage - uses existing error_handling module's DLQ

### Display-Only Data

Most entities (HealthStatus, OperationResult, ProgressIndicator, ConfigurationItem) are transient view models created at runtime from existing data sources. They are not persisted by the CLI.

## Validation Rules Summary

| Entity | Key Validation Rules |
|--------|---------------------|
| CLICommand | name: lowercase alphanumeric+hyphens; group: valid group name |
| CommandGroup | name: unique; commands: non-empty |
| OperationResult | success=False → errors non-empty; execution_time_ms >= 0 |
| ProgressIndicator | type=bar → total must be set; completed <= total |
| ErrorRecord | severity: valid enum; retriable: bool; retry_count >= 0 |
| HealthStatus | status: valid enum; status!=healthy → issues non-empty |
| ConfigurationItem | key: uppercase snake_case; source: valid enum; is_required+empty → invalid |
| TestReport | passed+failed+skipped = total_emails; stage_results: all stages present |
| LLMProvider | name: valid provider; priority >= 1; success_rate: 0-100 |

## Schema Changes to Existing Entities

**No modifications to existing data schemas**. The CLI is a presentation layer that reads from existing components:
- Email data: Read from `data/raw/`, `data/cleaned/`
- Error data: Read from error_handling module's DLQ
- E2E test data: Read from `data/e2e_test/`
- Configuration: Read from config module (Infisical + .env)
- Notion data: Read via notion_integrator module
- LLM data: Read via llm_adapters (Phase 3a) or llm_provider (Phase 3b)

## Future Enhancements

Potential data model extensions (out of scope for this feature):
- **CommandHistory**: Track command usage patterns for analytics
- **UserPreferences**: Store per-user CLI preferences (output format, default limits)
- **ScheduledCommand**: Support for scheduled CLI operations (requires scheduler)
- **CommandAlias**: User-defined command shortcuts
