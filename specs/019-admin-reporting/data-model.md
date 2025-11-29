# Data Model: Automated Admin Reporting

**Feature**: 019-admin-reporting
**Date**: 2025-11-29

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ReportingConfig                              │
│  (Configuration for report generation and delivery)                  │
├─────────────────────────────────────────────────────────────────────┤
│ - report_schedule_time: str (e.g., "07:00")                         │
│ - report_timezone: str (e.g., "America/New_York")                   │
│ - recipient_emails: list[str]                                        │
│ - error_rate_threshold: float (default: 0.05)                       │
│ - cost_limit_daily: float (default: 10.0)                           │
│ - archive_directory: Path                                            │
│ - retention_days: int (default: 30)                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ uses
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DailyReportData                             │
│  (Aggregated metrics for a 24-hour reporting period)                │
├─────────────────────────────────────────────────────────────────────┤
│ - report_id: str (UUID)                                              │
│ - report_date: date                                                  │
│ - generated_at: datetime                                             │
│ - period_start: datetime                                             │
│ - period_end: datetime                                               │
│ - health_status: ComponentHealthSummary                              │
│ - processing_metrics: ProcessingMetrics                              │
│ - error_summary: ErrorSummary                                        │
│ - llm_usage: LLMUsageSummary                                         │
│ - notion_stats: NotionStats                                          │
│ - actionable_alerts: list[ActionableAlert]                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┬─────────────────┐
                    │               │               │                 │
                    ▼               ▼               ▼                 ▼
┌─────────────────────┐ ┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│ ComponentHealthSummary│ │ProcessingMetrics│ │ ErrorSummary  │ │ LLMUsageSummary │
├─────────────────────┤ ├─────────────────┤ ├───────────────┤ ├─────────────────┤
│ - gmail_status      │ │ - emails_received│ │ - critical    │ │ - calls_by_prov │
│ - notion_status     │ │ - emails_processed││ - high        │ │ - costs_by_prov │
│ - llm_providers     │ │ - success_rate  │ │ - low_count   │ │ - total_cost    │
│ - overall_status    │ │ - avg_proc_time │ │ - error_trend │ │ - provider_health│
└─────────────────────┘ └─────────────────┘ └───────────────┘ └─────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         ActionableAlert                              │
│  (Alert requiring admin attention)                                   │
├─────────────────────────────────────────────────────────────────────┤
│ - alert_id: str (UUID)                                               │
│ - severity: AlertSeverity (critical, warning, info)                  │
│ - category: AlertCategory (credential, error_rate, cost, capacity)   │
│ - title: str                                                         │
│ - message: str                                                       │
│ - remediation: str                                                   │
│ - created_at: datetime                                               │
│ - acknowledged: bool                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ triggers
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AlertNotification                            │
│  (Delivery record for an alert)                                      │
├─────────────────────────────────────────────────────────────────────┤
│ - notification_id: str (UUID)                                        │
│ - alert_ids: list[str] (batched alerts)                              │
│ - sent_at: datetime                                                  │
│ - delivery_method: str (email)                                       │
│ - recipients: list[str]                                              │
│ - delivery_status: DeliveryStatus (pending, sent, failed)            │
│ - retry_count: int                                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         ArchivedReport                               │
│  (Stored report for historical analysis)                             │
├─────────────────────────────────────────────────────────────────────┤
│ - archive_id: str (UUID)                                             │
│ - report_date: date                                                  │
│ - json_path: Path                                                    │
│ - html_path: Path                                                    │
│ - archived_at: datetime                                              │
│ - size_bytes: int                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### ReportingConfig

Configuration for the admin reporting system.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| report_schedule_time | str | Yes | "07:00" | Time to send daily report (HH:MM format) |
| report_timezone | str | Yes | "UTC" | Timezone for schedule interpretation |
| recipient_emails | list[str] | Yes | - | Email addresses to receive reports |
| error_rate_threshold | float | No | 0.05 | Error rate (5%) to trigger warning alert |
| cost_limit_daily | float | No | 10.0 | Daily LLM cost ($) to trigger alert |
| archive_directory | Path | No | data/reports | Directory for archived reports |
| retention_days | int | No | 30 | Days to retain archived reports |

**Validation Rules**:
- `report_schedule_time` must match `HH:MM` pattern (24-hour)
- `report_timezone` must be valid IANA timezone
- `recipient_emails` must contain at least one valid email
- `error_rate_threshold` must be between 0.0 and 1.0
- `retention_days` must be positive integer

---

### DailyReportData

Aggregated metrics for a 24-hour reporting period.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| report_id | str | Yes | Unique identifier (UUID) |
| report_date | date | Yes | Date of the report |
| generated_at | datetime | Yes | When report was generated |
| period_start | datetime | Yes | Start of reporting period |
| period_end | datetime | Yes | End of reporting period |
| health_status | ComponentHealthSummary | Yes | System component health |
| processing_metrics | ProcessingMetrics | Yes | Email processing stats |
| error_summary | ErrorSummary | Yes | Error aggregation |
| llm_usage | LLMUsageSummary | Yes | LLM provider usage |
| notion_stats | NotionStats | Yes | Notion database stats |
| actionable_alerts | list[ActionableAlert] | Yes | Alerts requiring action |

---

### ComponentHealthSummary

Health status of system components.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| gmail_status | HealthStatus | Yes | Gmail API connectivity |
| gmail_token_expiry | datetime | No | When OAuth token expires |
| notion_status | HealthStatus | Yes | Notion API connectivity |
| llm_providers | dict[str, HealthStatus] | Yes | Health per LLM provider |
| overall_status | HealthStatus | Yes | Computed overall health |

**HealthStatus Enum**: `operational`, `degraded`, `unavailable`

---

### ProcessingMetrics

Email processing statistics for the period.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| emails_received | int | Yes | Emails fetched from Gmail |
| emails_processed | int | Yes | Emails successfully processed |
| emails_skipped | int | Yes | Emails skipped (duplicates, filtered) |
| success_rate | float | Yes | Computed: processed / received |
| average_processing_time_seconds | float | Yes | Average time per email |
| processing_cycles | int | Yes | Number of daemon cycles |

---

### ErrorSummary

Aggregated error information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| critical_errors | list[ErrorDetail] | Yes | Critical errors with details |
| high_errors | list[ErrorDetail] | Yes | High-severity errors with details |
| low_error_count | int | Yes | Count of low-severity errors |
| total_error_count | int | Yes | Total errors in period |
| error_rate | float | Yes | Computed: errors / processed |
| top_error_categories | list[ErrorCategory] | Yes | Top 5 error types by frequency |

**ErrorDetail**:
| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | When error occurred |
| severity | str | critical, high, low |
| component | str | gmail, notion, llm, etc. |
| message | str | Error message |
| context | dict | Additional context data |

---

### LLMUsageSummary

LLM provider usage and costs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| calls_by_provider | dict[str, int] | Yes | API calls per provider |
| costs_by_provider | dict[str, float] | Yes | Estimated cost per provider |
| total_calls | int | Yes | Total LLM API calls |
| total_cost | float | Yes | Total estimated cost |
| provider_health | dict[str, HealthStatus] | Yes | Provider availability |
| primary_provider | str | No | Most-used provider |

---

### NotionStats

Notion database operation statistics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| entries_created | int | Yes | New entries created |
| entries_updated | int | Yes | Existing entries updated |
| entries_skipped | int | Yes | Duplicates skipped |
| validation_failures | int | Yes | Schema validation errors |
| database_health | HealthStatus | Yes | Database accessibility |

---

### ActionableAlert

Alert requiring administrator attention.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| alert_id | str | Yes | Unique identifier (UUID) |
| severity | AlertSeverity | Yes | critical, warning, info |
| category | AlertCategory | Yes | Type of alert |
| title | str | Yes | Short alert title |
| message | str | Yes | Detailed description |
| remediation | str | Yes | Steps to resolve |
| created_at | datetime | Yes | When alert was generated |
| acknowledged | bool | No | Whether admin acknowledged |

**AlertSeverity Enum**: `critical`, `warning`, `info`

**AlertCategory Enum**:
- `credential_expiry` - OAuth token expiring soon
- `error_rate` - Error rate above threshold
- `cost_overrun` - LLM costs exceeding limit
- `component_failure` - Component unavailable
- `capacity` - Approaching limits

---

### AlertNotification

Record of alert delivery.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| notification_id | str | Yes | Unique identifier (UUID) |
| alert_ids | list[str] | Yes | Alerts included (batching) |
| sent_at | datetime | Yes | Delivery timestamp |
| delivery_method | str | Yes | "email" |
| recipients | list[str] | Yes | Recipient addresses |
| delivery_status | DeliveryStatus | Yes | Delivery outcome |
| retry_count | int | No | Number of retry attempts |
| error_message | str | No | If delivery failed |

**DeliveryStatus Enum**: `pending`, `sent`, `failed`

---

### ArchivedReport

Stored report for historical reference.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| archive_id | str | Yes | Unique identifier (UUID) |
| report_date | date | Yes | Date of the report |
| json_path | Path | Yes | Path to JSON data file |
| html_path | Path | Yes | Path to HTML report file |
| archived_at | datetime | Yes | When archived |
| size_bytes | int | Yes | Combined file size |

---

## State Transitions

### Alert Lifecycle

```
                    ┌──────────────┐
                    │   Created    │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
     ┌────────────────┐       ┌────────────────┐
     │   Immediate    │       │    Batched     │
     │  (first alert) │       │   (in window)  │
     └───────┬────────┘       └───────┬────────┘
             │                        │
             └────────────┬───────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │   Notified     │
                 └───────┬────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
     ┌────────────────┐    ┌────────────────┐
     │  Acknowledged  │    │    Expired     │
     └────────────────┘    │  (after 24h)   │
                           └────────────────┘
```

### Report Generation Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Collect   │───▶│  Aggregate  │───▶│   Render    │───▶│   Deliver   │
│   Metrics   │    │    Data     │    │  Templates  │    │    Email    │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                │
                                                                ▼
                                                       ┌─────────────┐
                                                       │   Archive   │
                                                       └─────────────┘
```

## Extended DaemonProcessState

The existing `DaemonProcessState` model needs extension:

```python
# Additional fields for src/models/daemon_state.py
class DaemonProcessState(BaseModel):
    # ... existing fields ...

    # New metrics fields
    emails_received_count: int = 0
    llm_calls_by_provider: dict[str, int] = {}
    llm_costs_by_provider: dict[str, float] = {}
    notion_entries_created: int = 0
    notion_validation_failures: int = 0

    # Error tracking
    recent_errors: list[dict] = []  # Last 100 errors

    # Component health
    last_gmail_check: Optional[datetime] = None
    last_notion_check: Optional[datetime] = None
    gmail_token_expiry: Optional[datetime] = None

    # Reporting
    last_report_generated: Optional[datetime] = None
    last_alert_sent: Optional[datetime] = None
```

## File Storage Patterns

### Report Archive

```
data/reports/
├── 2025-11-29_daily_report.json    # Machine-readable
├── 2025-11-29_daily_report.html    # Human-readable
├── 2025-11-28_daily_report.json
├── 2025-11-28_daily_report.html
└── index.json                       # Archive manifest
```

### Configuration

```bash
# Environment variables (with defaults)
ADMIN_REPORT_RECIPIENTS=jeffreylim@signite.co  # Default recipient
ADMIN_REPORT_TIME=07:00                         # 7 AM KST
ADMIN_REPORT_TIMEZONE=Asia/Seoul                # Korea Standard Time
ADMIN_ERROR_RATE_THRESHOLD=0.05
ADMIN_COST_LIMIT_DAILY=10.0
ADMIN_REPORT_ARCHIVE_DIR=data/reports
ADMIN_REPORT_RETENTION_DAYS=30
```
