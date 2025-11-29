# Implementation Plan: Automated Admin Reporting

**Branch**: `019-admin-reporting` | **Date**: 2025-11-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-admin-reporting/spec.md`

## Summary

Add automated daily reporting and critical alert notifications to CollabIQ. The system will:
- Generate daily summary emails with system health, processing metrics, errors, LLM usage, and Notion stats
- Send immediate alerts for critical errors (within 5 minutes)
- Archive reports for historical analysis
- Use existing Gmail OAuth for email delivery (no new dependencies except Jinja2 for templating)

## Technical Context

**Language/Version**: Python 3.12+ (established in project)
**Primary Dependencies**: Typer, Rich, Jinja2 (new), google-api-python-client (existing), pydantic (existing)
**Storage**: JSON files for reports archive (`data/reports/`), extended DaemonProcessState for metrics
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (Cloud Run), macOS (local development)
**Project Type**: Single project (extending existing CLI)
**Performance Goals**: Report generation <30 seconds
**Constraints**: Email delivery via Gmail API (100 sends/day free tier sufficient for admin reports)
**Scale/Scope**: Single admin user, daily reports, up to 1000 emails/day processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First | ✅ PASS | New `admin_reporting` library with clear purpose |
| II. CLI Interface | ✅ PASS | `collabiq report` command group with JSON/text output |
| III. Test-First | ✅ PASS | Unit tests for report generation, integration tests for email |
| IV. Integration Testing | ✅ PASS | Contract tests for email delivery, template rendering |
| V. Observability | ✅ PASS | Structured logging for all report operations |

**Technology Stack Compliance**:
- Python 3.12+ ✅
- CLI: Typer + Rich ✅
- Data Validation: Pydantic ✅
- Testing: pytest ✅
- New: Jinja2 (standard templating, minimal footprint) ✅

## Project Structure

### Documentation (this feature)

```text
specs/019-admin-reporting/
├── plan.md              # This file
├── research.md          # Phase 0 output ✅
├── data-model.md        # Phase 1 output ✅
├── quickstart.md        # Phase 1 output ✅
├── contracts/           # Phase 1 output ✅
│   ├── cli_commands.yaml
│   └── README.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── admin_reporting/              # NEW: Admin reporting library
│   ├── __init__.py
│   ├── collector.py              # MetricsCollector - aggregate metrics
│   ├── reporter.py               # ReportGenerator - create reports
│   ├── renderer.py               # ReportRenderer - HTML/text templates
│   ├── alerter.py                # AlertManager - threshold checks, batching
│   ├── archiver.py               # ReportArchiver - save/cleanup reports
│   └── templates/                # Jinja2 templates
│       ├── daily_report.html.j2
│       ├── daily_report.txt.j2
│       ├── critical_alert.html.j2
│       └── critical_alert.txt.j2
│
├── email_sender/                 # NEW: Email sending (reuse Gmail OAuth)
│   ├── __init__.py
│   └── gmail_sender.py           # GmailSender - send via Gmail API
│
├── models/
│   └── daemon_state.py           # EXTEND: Add detailed metrics fields
│
├── daemon/
│   ├── controller.py             # EXTEND: Add metrics collection hooks
│   └── scheduler.py              # EXTEND: Add daily scheduling
│
├── collabiq/commands/
│   └── report.py                 # NEW: CLI commands for reporting

tests/
├── unit/
│   ├── test_metrics_collector.py
│   ├── test_report_generator.py
│   ├── test_report_renderer.py
│   ├── test_alert_manager.py
│   └── test_report_archiver.py
│
├── integration/
│   ├── test_gmail_sender.py
│   ├── test_report_delivery.py
│   └── test_alert_batching.py
│
└── contract/
    └── test_report_cli.py
```

**Structure Decision**: Follows existing single-project pattern with new `admin_reporting` library module. Reuses existing patterns from `email_receiver`, `daemon`, and `collabiq/commands`.

## Component Design

### 1. MetricsCollector (`src/admin_reporting/collector.py`)

Extends daemon state with detailed metrics collection:

```python
class MetricsCollector:
    """Collects and aggregates operational metrics."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def record_email_processed(self, success: bool) -> None: ...
    def record_llm_call(self, provider: str, cost: float) -> None: ...
    def record_error(self, severity: str, component: str, message: str) -> None: ...
    def record_notion_operation(self, operation: str, success: bool) -> None: ...

    async def collect_period_metrics(self, hours: int = 24) -> DailyReportData: ...
```

### 2. ReportGenerator (`src/admin_reporting/reporter.py`)

Orchestrates report generation:

```python
class ReportGenerator:
    """Generates daily reports from collected metrics."""

    def __init__(
        self,
        collector: MetricsCollector,
        renderer: ReportRenderer,
        alerter: AlertManager,
    ):
        ...

    async def generate_report(self, period_hours: int = 24) -> DailyReportData: ...
    def check_component_health(self) -> ComponentHealthSummary: ...
```

### 3. ReportRenderer (`src/admin_reporting/renderer.py`)

Renders reports using Jinja2 templates:

```python
class ReportRenderer:
    """Renders report data to HTML/text/JSON formats."""

    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_html(self, data: DailyReportData) -> str: ...
    def render_text(self, data: DailyReportData) -> str: ...
    def render_json(self, data: DailyReportData) -> str: ...
```

### 4. AlertManager (`src/admin_reporting/alerter.py`)

Manages threshold monitoring and alert batching:

```python
class AlertManager:
    """Monitors thresholds and manages alert notifications."""

    def __init__(self, config: ReportingConfig, sender: EmailSender):
        self.config = config
        self.sender = sender
        self.alert_buffer: list[ActionableAlert] = []
        self.last_batch_time: Optional[datetime] = None

    def check_thresholds(self, metrics: DailyReportData) -> list[ActionableAlert]: ...
    async def process_alert(self, alert: ActionableAlert) -> None: ...
    async def flush_batch(self) -> None: ...
```

### 5. GmailSender (`src/email_sender/gmail_sender.py`)

Sends emails via Gmail API (reuses OAuth):

```python
class GmailSender:
    """Sends emails via Gmail API."""

    def __init__(self, credentials_path: Path, token_path: Path):
        # Reuse OAuth token from GmailReceiver
        ...

    async def send_email(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool: ...
```

## Integration Points

1. **DaemonController.process_cycle()**: Add hooks to MetricsCollector
2. **StateManager**: Extend DaemonProcessState with new fields
3. **Scheduler**: Add `schedule_daily()` for report generation
4. **CLI**: Register `report_app` in `collabiq/commands/__init__.py`

## Dependencies to Add

```toml
# pyproject.toml
[project.dependencies]
jinja2 = "^3.1"
```

## Environment Configuration

```bash
# .env (with defaults)
ADMIN_REPORT_RECIPIENTS=jeffreylim@signite.co  # Comma-separated for multiple
ADMIN_REPORT_TIME=07:00                         # 24-hour format (KST)
ADMIN_REPORT_TIMEZONE=Asia/Seoul                # Korea Standard Time
ADMIN_ERROR_RATE_THRESHOLD=0.05                 # 5% error rate warning
ADMIN_COST_LIMIT_DAILY=10.0                     # USD per day
ADMIN_REPORT_ARCHIVE_DIR=data/reports           # Archive location
ADMIN_REPORT_RETENTION_DAYS=30                  # Days to keep archives
```

## Complexity Tracking

No constitution violations requiring justification. All design choices follow established patterns:

- Library-first: New `admin_reporting` module
- CLI interface: `collabiq report` command group
- Test-first: Unit/integration/contract tests planned
- Reuses existing infrastructure (Gmail OAuth, StateManager, Scheduler)
