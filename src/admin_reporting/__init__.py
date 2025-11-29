"""
Admin Reporting Module for CollabIQ.

Provides automated daily reporting and critical alert notifications for system
administrators. Features include:

- Daily summary emails with system health, processing metrics, errors, LLM usage,
  and Notion statistics
- Critical error alerts with batching to prevent alert fatigue
- Actionable insights with remediation guidance
- Report archiving with configurable retention

Configuration via environment variables:
- ADMIN_REPORT_RECIPIENTS: Comma-separated email addresses (default: jeffreylim@signite.co)
- ADMIN_REPORT_TIME: Daily report time in HH:MM format (default: 07:00)
- ADMIN_REPORT_TIMEZONE: IANA timezone (default: Asia/Seoul)
- ADMIN_ERROR_RATE_THRESHOLD: Error rate warning threshold (default: 0.05)
- ADMIN_COST_LIMIT_DAILY: Daily LLM cost limit in USD (default: 10.0)
- ADMIN_REPORT_ARCHIVE_DIR: Archive directory (default: data/reports)
- ADMIN_REPORT_RETENTION_DAYS: Days to retain archives (default: 30)
"""

__version__ = "0.1.0"
