# Feature Specification: Automated Admin Reporting

**Feature Branch**: `019-admin-reporting`
**Created**: 2025-11-29
**Status**: Draft
**Input**: User description: "Phase 4c - Automated Admin Reporting with daily summary emails containing system health, processing metrics, error summaries, LLM usage, Notion stats, and actionable alerts. Includes email templating, configurable schedule, optional Slack/webhook notifications, and report archiving."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Daily Summary Email (Priority: P1)

As a system administrator, I want to receive a daily email summarizing system health and processing metrics so that I can monitor CollabIQ operations without manually checking the system.

**Why this priority**: This is the core value proposition - providing administrators with automated visibility into system operations. Without this, admins must manually check logs and metrics daily.

**Independent Test**: Can be fully tested by triggering a report generation and verifying email delivery with all required sections present.

**Acceptance Scenarios**:

1. **Given** the system has been running for 24 hours, **When** the scheduled report time arrives, **Then** the admin receives an email containing all metric sections (health, processing, errors, LLM usage, Notion stats).
2. **Given** the admin email is configured, **When** a daily report is generated, **Then** the email is delivered to all configured recipients within 5 minutes.
3. **Given** the system has no activity for 24 hours, **When** the daily report runs, **Then** the report shows zero counts and indicates "No activity" rather than failing.

---

### User Story 2 - Critical Error Alerts (Priority: P1)

As a system administrator, I want to receive immediate notifications when critical errors occur so that I can respond to issues before they impact operations.

**Why this priority**: Critical errors require immediate attention. Waiting for the daily report could mean hours of downtime or data loss. This is equally critical to the daily summary.

**Independent Test**: Can be tested by simulating a critical error condition and verifying alert delivery within the 5-minute SLA.

**Acceptance Scenarios**:

1. **Given** a critical error occurs (e.g., Gmail auth failure, Notion API unreachable), **When** the system detects it, **Then** an alert is sent to the admin within 5 minutes.
2. **Given** multiple critical errors occur within 15 minutes, **When** alerts are generated, **Then** they are batched into a single notification to prevent alert fatigue.
3. **Given** the error rate exceeds the configured threshold, **When** the condition persists for 5 minutes, **Then** an elevated alert is sent with trend data.

---

### User Story 3 - Actionable Insights (Priority: P2)

As a system administrator, I want the report to highlight actionable items (expiring credentials, elevated error rates, capacity warnings) so that I can proactively address issues before they become critical.

**Why this priority**: Actionable insights prevent problems. While not as urgent as the core metrics, they significantly reduce operational burden by surfacing issues early.

**Independent Test**: Can be tested by configuring known conditions (e.g., auth token expiring in 3 days) and verifying the report includes specific remediation guidance.

**Acceptance Scenarios**:

1. **Given** Gmail authentication expires in 3 days or less, **When** the daily report generates, **Then** an alert is included with specific instructions for re-authentication.
2. **Given** the error rate exceeds the warning threshold (configurable, default 5%), **When** the daily report generates, **Then** an alert is included showing error trend and top error categories.
3. **Given** LLM costs exceed the daily budget threshold, **When** the daily report generates, **Then** a cost alert is included with breakdown by provider.

---

### User Story 4 - Report Archiving (Priority: P3)

As a system administrator, I want reports to be archived locally so that I can reference historical data for trend analysis and troubleshooting.

**Why this priority**: Historical data is valuable but not urgent. The system functions without archives, but they enable trend analysis and debugging.

**Independent Test**: Can be tested by generating a report and verifying the archive file is created in the correct location with proper naming.

**Acceptance Scenarios**:

1. **Given** a daily report is generated, **When** the report completes, **Then** a copy is saved to the configured archive directory with timestamp in the filename.
2. **Given** the archive directory doesn't exist, **When** a report is archived, **Then** the directory is created automatically.
3. **Given** reports older than the retention period exist, **When** the cleanup runs, **Then** old reports are deleted according to the retention policy.

---

### Edge Cases

- What happens when email delivery fails? System retries 3 times with exponential backoff, then logs error and continues. Failure is reported in next day's report.
- How does the system handle partial data availability? Report generates with available data and notes which metrics are unavailable.
- What happens during cloud deployment with no local filesystem? Archive path should be configurable; if unavailable, archiving is skipped with a warning.
- How are large error volumes handled? Errors are summarized (top 10 by frequency) with option to view full details in archived report.
- What if LLM cost data is unavailable? Section shows "Cost data unavailable" rather than failing. Costs are estimated from call counts if actual costs aren't available.

## Requirements *(mandatory)*

### Functional Requirements

#### Report Content
- **FR-001**: System MUST generate a daily summary report containing system health status for all components (Gmail, Notion, LLM providers).
- **FR-002**: System MUST include processing metrics in the daily report: emails received, emails processed, success rate, and average processing time.
- **FR-003**: System MUST include error summary: critical errors with full details, high-severity errors with details, and low-severity error counts.
- **FR-004**: System MUST include LLM provider usage: API calls per provider, estimated costs, and provider health status.
- **FR-005**: System MUST include Notion database statistics: entries created, entries updated, and validation failures.
- **FR-006**: System MUST include actionable alerts for: expiring credentials (≤3 days), error rate above threshold, cost overruns, and capacity warnings.

#### Report Delivery
- **FR-007**: System MUST deliver the daily report via email at the configured time (default: 7:00 AM in configured timezone).
- **FR-008**: System MUST support both HTML and plain text email formats, sending multipart emails for compatibility.
- **FR-009**: System MUST support multiple recipient email addresses.
- **FR-010**: System MUST complete report generation in under 30 seconds.

#### Critical Alerts
- **FR-011**: System MUST send immediate alerts for critical errors within 5 minutes of detection.
- **FR-012**: System MUST batch multiple alerts occurring within a 15-minute window to prevent alert fatigue.

#### Archiving
- **FR-013**: System MUST archive each generated report to the configured directory with a timestamped filename.
- **FR-014**: System MUST support configurable report retention period (default: 30 days).
- **FR-015**: System MUST automatically clean up reports older than the retention period.

#### Configuration
- **FR-016**: System MUST allow configuration of report schedule (time and timezone).
- **FR-017**: System MUST allow configuration of recipient email addresses.
- **FR-018**: System MUST allow configuration of alert thresholds (error rate, cost limits).
- **FR-019**: System MUST allow configuration of archive directory and retention period.

### Key Entities

- **DailyReport**: Aggregated metrics for a 24-hour period including health status, processing metrics, error summaries, LLM usage, Notion stats, and actionable alerts. Timestamped and associated with a reporting period.
- **Alert**: A notification triggered by a threshold breach or critical condition. Has severity (critical, warning, info), message, timestamp, and delivery status.
- **ReportRecipient**: An email address configured to receive reports/alerts.
- **ArchivedReport**: A stored copy of a generated report with filename, generation timestamp, and file path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Daily email is delivered reliably at the configured time with 99% success rate over 30 days.
- **SC-002**: Report includes all key metrics (health, processing, errors, LLM usage, Notion stats) with accurate data matching system logs.
- **SC-003**: Critical errors trigger immediate notification within 5 minutes of detection.
- **SC-004**: Admin can diagnose 80% of operational issues from the report alone without accessing the CLI or logs.
- **SC-005**: Report generation completes in under 30 seconds for a system processing up to 1,000 emails per day.
- **SC-006**: Archived reports are retained according to policy and accessible for trend analysis.
- **SC-007**: Alert fatigue is minimized through batching, with no more than 5 alert notifications per hour during sustained error conditions.

## Configuration

### Default Settings

| Setting | Environment Variable | Default Value |
|---------|---------------------|---------------|
| Report Recipients | `ADMIN_REPORT_RECIPIENTS` | `jeffreylim@signite.co` |
| Report Time | `ADMIN_REPORT_TIME` | `07:00` |
| Report Timezone | `ADMIN_REPORT_TIMEZONE` | `Asia/Seoul` |
| Error Rate Threshold | `ADMIN_ERROR_RATE_THRESHOLD` | `0.05` (5%) |
| Daily Cost Limit | `ADMIN_COST_LIMIT_DAILY` | `10.0` (USD) |
| Archive Directory | `ADMIN_REPORT_ARCHIVE_DIR` | `data/reports` |
| Retention Days | `ADMIN_REPORT_RETENTION_DAYS` | `30` |

## Assumptions

- **Email Infrastructure**: The system has access to an email sending service (either SMTP or API-based). Gmail API used for receiving can also be configured for sending, or a separate SMTP server is available.
- **Timezone Handling**: Report schedule uses the system's configured timezone. If not configured, defaults to Asia/Seoul (KST).
- **Cost Estimation**: LLM costs are estimated based on token counts and published pricing. Actual billing may vary slightly.
- **Error Classification**: Errors are classified using existing error handling system severity levels (critical, high, low).
- **Metrics Storage**: Processing metrics are already being tracked by the daemon and stored in the state file.
- **Alert Deduplication**: Alerts for the same root cause are deduplicated within the batching window.

## Out of Scope

- Real-time dashboard or web UI for metrics visualization
- Historical trend graphs or charting in email reports
- SMS or phone call notifications
- Slack or webhook notifications (email only)
- Integration with third-party monitoring services (Datadog, PagerDuty, etc.)
- User-level (non-admin) reporting
- Customizable report templates by end users
