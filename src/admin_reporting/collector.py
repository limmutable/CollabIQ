"""
Metrics collector for Admin Reporting.

Aggregates metrics from DaemonProcessState and system components
for report generation.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

from admin_reporting.models import (
    ComponentHealthSummary,
    ProcessingMetrics,
    ErrorSummary,
    ErrorCategory,
    LLMUsageSummary,
    NotionStats,
    HealthStatus,
)
from models.daemon_state import DaemonProcessState

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics from daemon state and system components.

    This class provides methods to extract and transform raw metrics from
    DaemonProcessState into structured report data models.

    Attributes:
        daemon_state: Reference to DaemonProcessState for metrics
        period_start: Start of the reporting period
        period_end: End of the reporting period
    """

    # Thresholds for health status determination
    HEALTH_CHECK_STALE_MINUTES = (
        30  # Consider component unhealthy if no check in 30 min
    )
    TOKEN_EXPIRY_WARNING_DAYS = 7  # Warn if token expires within 7 days

    def __init__(
        self,
        daemon_state: DaemonProcessState,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ):
        """
        Initialize MetricsCollector.

        Args:
            daemon_state: DaemonProcessState instance with metrics data
            period_start: Start of reporting period (default: 24 hours ago)
            period_end: End of reporting period (default: now)
        """
        self.daemon_state = daemon_state
        self.period_end = period_end or datetime.now(UTC)
        self.period_start = period_start or (self.period_end - timedelta(hours=24))

    def collect_component_health(self) -> ComponentHealthSummary:
        """
        Collect health status of all system components.

        Determines health status based on:
        - Gmail: Last successful check time and token expiry
        - Notion: Last successful check time
        - LLM providers: Based on recent error rates

        Returns:
            ComponentHealthSummary with health status of all components
        """
        health = ComponentHealthSummary()
        now = datetime.now(UTC)

        # Gmail health - based on last check time and token expiry
        if self.daemon_state.last_gmail_check:
            time_since_check = now - self.daemon_state.last_gmail_check
            if time_since_check > timedelta(minutes=self.HEALTH_CHECK_STALE_MINUTES):
                health.gmail_status = HealthStatus.DEGRADED
            else:
                health.gmail_status = HealthStatus.OPERATIONAL
        else:
            health.gmail_status = HealthStatus.UNAVAILABLE

        # Set token expiry for monitoring
        health.gmail_token_expiry = self.daemon_state.gmail_token_expiry

        # Notion health - based on last check time and validation failures
        if self.daemon_state.last_notion_check:
            time_since_check = now - self.daemon_state.last_notion_check
            if time_since_check > timedelta(minutes=self.HEALTH_CHECK_STALE_MINUTES):
                health.notion_status = HealthStatus.DEGRADED
            elif self.daemon_state.notion_validation_failures > 0:
                health.notion_status = HealthStatus.DEGRADED
            else:
                health.notion_status = HealthStatus.OPERATIONAL
        else:
            health.notion_status = HealthStatus.UNAVAILABLE

        # LLM providers health - based on calls and errors
        health.llm_providers = self._compute_llm_health()

        # Compute overall status
        health.compute_overall()

        logger.debug(f"Collected component health: overall={health.overall_status}")
        return health

    def _compute_llm_health(self) -> dict[str, HealthStatus]:
        """Compute health status for each LLM provider."""
        provider_health = {}

        # Check each provider that has been used
        for provider in self.daemon_state.llm_calls_by_provider.keys():
            # Count errors for this provider
            provider_errors = sum(
                1
                for err in self.daemon_state.recent_errors
                if err.get("component") == "llm" and provider in err.get("message", "")
            )

            total_calls = self.daemon_state.llm_calls_by_provider.get(provider, 0)

            if total_calls == 0:
                provider_health[provider] = HealthStatus.UNAVAILABLE
            elif provider_errors > 0:
                error_rate = provider_errors / total_calls if total_calls > 0 else 1.0
                if error_rate > 0.5:
                    provider_health[provider] = HealthStatus.UNAVAILABLE
                elif error_rate > 0.1:
                    provider_health[provider] = HealthStatus.DEGRADED
                else:
                    provider_health[provider] = HealthStatus.OPERATIONAL
            else:
                provider_health[provider] = HealthStatus.OPERATIONAL

        return provider_health

    def collect_processing_metrics(self) -> ProcessingMetrics:
        """
        Collect email processing statistics.

        Aggregates:
        - Emails received, processed, and skipped
        - Success rate calculation
        - Average processing time
        - Processing cycle count

        Handles partial data gracefully - missing or None values default to 0.

        Returns:
            ProcessingMetrics with aggregated processing data
        """
        # Graceful degradation: handle missing or None values
        emails_received = getattr(self.daemon_state, "emails_received_count", 0) or 0
        emails_processed = getattr(self.daemon_state, "emails_processed_count", 0) or 0
        emails_skipped = getattr(self.daemon_state, "emails_skipped_count", 0) or 0
        processing_cycles = (
            getattr(self.daemon_state, "total_processing_cycles", 0) or 0
        )

        metrics = ProcessingMetrics(
            emails_received=emails_received,
            emails_processed=emails_processed,
            emails_skipped=emails_skipped,
            processing_cycles=processing_cycles,
        )

        # Compute success rate
        metrics.compute_success_rate()

        # Calculate average processing time if we have cycle data
        if processing_cycles > 0:
            daemon_start = getattr(self.daemon_state, "daemon_start_timestamp", None)
            if daemon_start:
                # Make timezone-aware if needed
                if daemon_start.tzinfo is None:
                    daemon_start = daemon_start.replace(tzinfo=UTC)
                period_end = self.period_end
                if period_end.tzinfo is None:
                    period_end = period_end.replace(tzinfo=UTC)

                total_runtime = (period_end - daemon_start).total_seconds()
                if total_runtime > 0:
                    metrics.average_processing_time_seconds = (
                        total_runtime / processing_cycles
                    )

        logger.debug(
            f"Collected processing metrics: received={metrics.emails_received}, "
            f"processed={metrics.emails_processed}, success_rate={metrics.success_rate:.2%}"
        )
        return metrics

    def collect_error_summary(self) -> ErrorSummary:
        """
        Collect and categorize errors from the reporting period.

        Categorizes errors by severity:
        - Critical: Immediate attention required
        - High: Should be addressed soon
        - Low: Informational/warnings

        Also identifies top error categories (limited to top 10 for large volumes).

        Handles partial data gracefully - missing recent_errors defaults to empty list.

        Returns:
            ErrorSummary with categorized error data
        """
        summary = ErrorSummary()

        # Graceful degradation: handle missing recent_errors
        recent_errors = getattr(self.daemon_state, "recent_errors", []) or []

        # Filter errors to reporting period
        period_errors = [
            err for err in recent_errors if self._is_in_period(err.get("timestamp"))
        ]

        # Categorize by severity
        for err in period_errors:
            severity = err.get("severity", "low")
            if severity == "critical":
                summary.critical_errors.append(err)
            elif severity == "high":
                summary.high_errors.append(err)
            else:
                summary.low_error_count += 1

        summary.total_error_count = len(period_errors)

        # Compute error rate
        total_operations = (
            self.daemon_state.emails_received_count
            + self.daemon_state.notion_entries_created
            + self.daemon_state.notion_entries_updated
        )
        if total_operations > 0:
            summary.error_rate = summary.total_error_count / total_operations
        else:
            summary.error_rate = 0.0

        # Identify top error categories (limit to top 10 for large volumes)
        summary.top_error_categories = self._compute_error_categories(
            period_errors, top_n=10
        )

        logger.debug(
            f"Collected error summary: critical={len(summary.critical_errors)}, "
            f"high={len(summary.high_errors)}, low={summary.low_error_count}"
        )
        return summary

    def _is_in_period(self, timestamp_str: Optional[str]) -> bool:
        """Check if timestamp string is within reporting period."""
        if not timestamp_str:
            return False
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            # Make timezone-aware if needed
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            return self.period_start <= timestamp <= self.period_end
        except (ValueError, TypeError):
            return False

    def _compute_error_categories(
        self, errors: list[dict], top_n: int = 5
    ) -> list[ErrorCategory]:
        """Compute top error categories from error list."""
        category_counts: dict[str, dict] = {}

        for err in errors:
            component = err.get("component", "unknown")
            msg = err.get("message", "")
            key = f"{component}:{msg[:50]}"  # Use first 50 chars as category

            if key not in category_counts:
                category_counts[key] = {
                    "category": component,
                    "count": 0,
                    "sample_message": msg,
                }
            category_counts[key]["count"] += 1

        # Sort by count and return top N
        sorted_categories = sorted(
            category_counts.values(), key=lambda x: x["count"], reverse=True
        )

        return [
            ErrorCategory(
                category=cat["category"],
                count=cat["count"],
                sample_message=cat["sample_message"],
            )
            for cat in sorted_categories[:top_n]
        ]

    def collect_llm_usage(self) -> LLMUsageSummary:
        """
        Collect LLM provider usage and cost metrics.

        Aggregates:
        - Calls per provider
        - Estimated costs per provider
        - Total calls and costs
        - Provider health status

        Handles partial data gracefully - missing data defaults to empty dicts.

        Returns:
            LLMUsageSummary with LLM usage data
        """
        # Graceful degradation: handle missing or None values
        llm_calls = getattr(self.daemon_state, "llm_calls_by_provider", {}) or {}
        llm_costs = getattr(self.daemon_state, "llm_costs_by_provider", {}) or {}

        summary = LLMUsageSummary(
            calls_by_provider=dict(llm_calls),
            costs_by_provider=dict(llm_costs),
            provider_health=self._compute_llm_health(),
        )

        # Compute totals
        summary.compute_totals()

        logger.debug(
            f"Collected LLM usage: total_calls={summary.total_calls}, "
            f"total_cost=${summary.total_cost:.4f}"
        )
        return summary

    def collect_notion_stats(self) -> NotionStats:
        """
        Collect Notion database operation statistics.

        Aggregates:
        - Entries created and updated
        - Entries skipped (duplicates)
        - Validation failures

        Handles partial data gracefully - missing data defaults to 0.

        Returns:
            NotionStats with Notion operation data
        """
        # Graceful degradation: handle missing or None values
        last_notion_check = getattr(self.daemon_state, "last_notion_check", None)
        validation_failures = (
            getattr(self.daemon_state, "notion_validation_failures", 0) or 0
        )
        entries_created = getattr(self.daemon_state, "notion_entries_created", 0) or 0
        entries_updated = getattr(self.daemon_state, "notion_entries_updated", 0) or 0
        emails_skipped = getattr(self.daemon_state, "emails_skipped_count", 0) or 0

        # Determine database health based on validation failures
        if last_notion_check is None:
            db_health = HealthStatus.UNAVAILABLE
        elif validation_failures > 0:
            db_health = HealthStatus.DEGRADED
        else:
            db_health = HealthStatus.OPERATIONAL

        stats = NotionStats(
            entries_created=entries_created,
            entries_updated=entries_updated,
            entries_skipped=emails_skipped,  # Duplicates
            validation_failures=validation_failures,
            database_health=db_health,
        )

        logger.debug(
            f"Collected Notion stats: created={stats.entries_created}, "
            f"updated={stats.entries_updated}, failures={stats.validation_failures}"
        )
        return stats

    def collect_all(self) -> dict:
        """
        Collect all metrics in a single call.

        Returns:
            Dictionary with all metric collections
        """
        return {
            "health_status": self.collect_component_health(),
            "processing_metrics": self.collect_processing_metrics(),
            "error_summary": self.collect_error_summary(),
            "llm_usage": self.collect_llm_usage(),
            "notion_stats": self.collect_notion_stats(),
        }
