# Contracts: Automated Admin Reporting

**Feature**: 019-admin-reporting
**Date**: 2025-11-29

## Contract Files

| File | Description |
|------|-------------|
| `cli_commands.yaml` | CLI command specifications for `collabiq report` |

## CLI Command Summary

### `collabiq report` Command Group

| Command | Description |
|---------|-------------|
| `report generate` | Generate and optionally send a daily report |
| `report list` | List archived reports |
| `report show <DATE>` | Display a specific archived report |
| `report config` | View or update reporting configuration |
| `report alerts list` | List active alerts |
| `report alerts acknowledge <ID>` | Acknowledge an alert |
| `report alerts test` | Send a test alert |

## Internal Contracts

This feature primarily uses internal Python interfaces rather than external APIs:

### Metrics Collection Interface

```python
class MetricsCollector(Protocol):
    async def collect_metrics(self, period: timedelta) -> DailyReportData:
        """Collect and aggregate metrics for the specified period."""
        ...

    def record_email_processed(self, success: bool) -> None:
        """Record an email processing result."""
        ...

    def record_llm_call(self, provider: str, cost: float) -> None:
        """Record an LLM API call with estimated cost."""
        ...

    def record_error(self, severity: str, component: str, message: str) -> None:
        """Record an error occurrence."""
        ...
```

### Report Renderer Interface

```python
class ReportRenderer(Protocol):
    def render_html(self, data: DailyReportData) -> str:
        """Render report as HTML email."""
        ...

    def render_text(self, data: DailyReportData) -> str:
        """Render report as plain text email."""
        ...

    def render_json(self, data: DailyReportData) -> str:
        """Render report as JSON for archiving."""
        ...
```

### Email Sender Interface

```python
class EmailSender(Protocol):
    async def send_report(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """Send report email to recipients."""
        ...

    async def send_alert(
        self,
        recipients: list[str],
        alert: ActionableAlert,
    ) -> bool:
        """Send critical alert notification."""
        ...
```

### Alert Manager Interface

```python
class AlertManager(Protocol):
    def check_thresholds(self, metrics: DailyReportData) -> list[ActionableAlert]:
        """Check metrics against configured thresholds."""
        ...

    def batch_alerts(self, alerts: list[ActionableAlert]) -> list[AlertNotification]:
        """Batch alerts within time window."""
        ...

    async def send_notification(self, notification: AlertNotification) -> bool:
        """Send batched alert notification."""
        ...
```

## Gmail API Usage

The feature uses the existing Gmail API integration for sending:

### Send Message Endpoint

```
POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send

Authorization: Bearer {access_token}
Content-Type: application/json

{
  "raw": "{base64_encoded_message}"
}
```

The raw message is a base64url-encoded MIME message with:
- `From:` header (authenticated user)
- `To:` header (recipients)
- `Subject:` header
- `Content-Type: multipart/alternative` (HTML + plain text)

## Configuration Contract

Environment variables following existing patterns:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ADMIN_REPORT_RECIPIENTS` | string | `jeffreylim@signite.co` | Comma-separated recipient emails |
| `ADMIN_REPORT_TIME` | string | `07:00` | Daily report time (HH:MM) |
| `ADMIN_REPORT_TIMEZONE` | string | `Asia/Seoul` | Schedule timezone (KST) |
| `ADMIN_ERROR_RATE_THRESHOLD` | float | `0.05` | Error rate warning threshold |
| `ADMIN_COST_LIMIT_DAILY` | float | `10.0` | Daily LLM cost limit ($) |
| `ADMIN_REPORT_ARCHIVE_DIR` | string | `data/reports` | Archive directory |
| `ADMIN_REPORT_RETENTION_DAYS` | int | `30` | Archive retention period |
