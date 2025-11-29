# Research: Automated Admin Reporting

**Feature**: 019-admin-reporting
**Date**: 2025-11-29
**Status**: Complete

## Research Questions

### 1. Email Sending Infrastructure

**Question**: How should the system send outbound emails for reports and alerts?

**Decision**: Use Gmail API for sending (leveraging existing OAuth setup)

**Rationale**:
- Gmail API is already integrated for receiving emails (gmail_receiver.py)
- OAuth credentials are already configured and managed
- Avoids adding new dependencies (SMTP server, SendGrid API key, etc.)
- Gmail API supports multipart HTML/plain text emails
- Token refresh mechanism already implemented

**Alternatives Considered**:
| Option | Pros | Cons |
|--------|------|------|
| SMTP (direct) | Simple, universal | Requires new credentials, firewall config, deliverability issues |
| SendGrid | High deliverability, analytics | Additional cost, API key management |
| AWS SES | Scalable, cheap | AWS account required, more setup |
| Gmail API | Already integrated, no new deps | Quota limits (100/day free tier sufficient for admin reports) |

**Implementation Notes**:
- Use `gmail.users.messages.send` API endpoint
- Reuse existing token refresh logic from GmailReceiver
- Create `GmailSender` class in `src/email_sender/` module

---

### 2. Metrics Collection Architecture

**Question**: How should metrics be collected and aggregated for reporting?

**Decision**: Extend DaemonProcessState with detailed metrics + new MetricsCollector service

**Rationale**:
- DaemonProcessState already tracks basic counts (emails_processed_count, error_count)
- Adding more fields to state model is straightforward
- Centralized collection point in DaemonController.process_cycle()
- State is persisted to JSON (local) or GCS (cloud), enabling cross-cycle aggregation

**Current State Fields**:
```python
# From src/models/daemon_state.py
emails_processed_count: int = 0
error_count: int = 0
total_processing_cycles: int = 0
current_status: str = "stopped"
```

**New Metrics Needed**:
- `emails_received_count` (fetched, not necessarily processed)
- `processing_success_rate` (computed)
- `llm_calls_by_provider` (dict: provider → count)
- `llm_estimated_costs` (dict: provider → float)
- `notion_entries_created` (count)
- `notion_validation_failures` (count)
- `error_details` (list of recent errors with severity/message)
- `component_health` (dict: component → status)

---

### 3. Report Template System

**Question**: How should HTML and plain text email templates be managed?

**Decision**: Jinja2 templates stored in `src/admin_reporting/templates/`

**Rationale**:
- Jinja2 is a Python standard for templating
- Separates presentation from logic
- Easy to maintain and customize
- Supports both HTML and plain text from same data

**Alternatives Considered**:
| Option | Pros | Cons |
|--------|------|------|
| Jinja2 | Standard, powerful, easy | New dependency |
| String formatting | No deps | Hard to maintain, error-prone |
| Mako | Fast | Less common, learning curve |
| Built-in f-strings | Simple | No logic, repetitive |

**Template Structure**:
```
src/admin_reporting/templates/
├── daily_report.html.j2
├── daily_report.txt.j2
├── critical_alert.html.j2
└── critical_alert.txt.j2
```

---

### 4. Scheduling Mechanism

**Question**: How should daily reports be scheduled?

**Decision**: Extend existing Scheduler class with cron-like scheduling

**Rationale**:
- Daemon already has Scheduler in `src/daemon/scheduler.py`
- Adding time-based scheduling (run at 7:00 AM) is natural extension
- No external scheduler (cron, systemd timer) dependency
- Works in both local and Cloud Run environments

**Implementation**:
- Add `schedule_daily(time: str, timezone: str, callback: Callable)` to Scheduler
- Check if scheduled time passed since last report in each cycle
- Cloud Run: Use Cloud Scheduler to trigger job at report time

---

### 5. Alert Batching Strategy

**Question**: How should critical alerts be batched to prevent alert fatigue?

**Decision**: Time-window batching with 15-minute aggregation

**Rationale**:
- Prevents dozens of alerts during cascading failures
- 15-minute window balances responsiveness with noise reduction
- Alerts within window are grouped by type/severity
- Single notification sent at end of window (or immediately if first alert)

**Implementation**:
- `AlertBuffer` class with timestamp-based windowing
- First critical alert triggers immediate notification + starts window
- Subsequent alerts within window are queued
- Window expiry triggers batch notification if queue non-empty
- Maximum 5 alerts per hour to prevent spam

---

### 6. Archive Format and Retention

**Question**: What format should archived reports use?

**Decision**: JSON for data + HTML for human-readable archive

**Rationale**:
- JSON enables programmatic trend analysis
- HTML provides standalone viewable report
- Both generated from same report data
- Retention handled by simple file age check

**Archive Structure**:
```
data/reports/
├── 2025-11-29_daily_report.json
├── 2025-11-29_daily_report.html
├── 2025-11-28_daily_report.json
└── 2025-11-28_daily_report.html
```

**Retention**:
- Default: 30 days
- Configurable via `REPORT_RETENTION_DAYS` env var
- Cleanup runs after each daily report generation

---

### 7. Credential Expiration Detection

**Question**: How should the system detect expiring Gmail credentials?

**Decision**: Parse token expiry from OAuth token file

**Rationale**:
- Gmail OAuth tokens include `expiry` timestamp
- Token file already stored at `gmail_token_path`
- Check during report generation and compare to current time
- Alert if expiry within 3 days

**Implementation**:
- Read token JSON from `gmail_token_path`
- Parse `expiry` field (ISO 8601 format)
- Compare with `datetime.now()` + 3 days
- Include in actionable alerts if approaching

---

## Technology Stack Additions

| Component | Technology | Justification |
|-----------|------------|---------------|
| Email Sending | Gmail API (existing) | Already integrated, no new deps |
| Templating | Jinja2 | Standard Python templating |
| Scheduling | Extended Scheduler | Built on existing daemon code |
| Archive Storage | JSON + HTML files | Simple, portable, no database needed |

## Dependencies to Add

```toml
# pyproject.toml
[project.dependencies]
jinja2 = "^3.1"  # Templating engine for reports
```

## Integration Points

1. **DaemonController**: Extend `process_cycle()` to collect detailed metrics
2. **StateManager**: Extend DaemonProcessState model with new metric fields
3. **GmailReceiver**: Reuse OAuth for sending (new GmailSender class)
4. **Error handling**: Hook into existing error logging for severity tracking
5. **LLM Orchestrator**: Add cost tracking hooks to providers
