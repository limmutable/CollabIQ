"""
Unit tests for MetricsCollector class.

Tests metrics collection and aggregation functionality.
"""

import pytest
from datetime import datetime, timedelta, UTC

from admin_reporting.collector import MetricsCollector
from admin_reporting.models import HealthStatus, ErrorCategory
from models.daemon_state import DaemonProcessState


class TestMetricsCollectorInit:
    """Tests for MetricsCollector initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default period."""
        state = DaemonProcessState()
        collector = MetricsCollector(state)

        assert collector.daemon_state == state
        assert collector.period_end is not None
        assert collector.period_start is not None
        # Default period is 24 hours
        assert (collector.period_end - collector.period_start).total_seconds() == pytest.approx(
            24 * 60 * 60, rel=1
        )

    def test_init_with_custom_period(self):
        """Test initialization with custom period."""
        state = DaemonProcessState()
        end = datetime.now(UTC)
        start = end - timedelta(hours=12)

        collector = MetricsCollector(state, period_start=start, period_end=end)

        assert collector.period_start == start
        assert collector.period_end == end


class TestCollectComponentHealth:
    """Tests for collect_component_health method."""

    @pytest.fixture
    def state(self):
        """Create DaemonProcessState for testing."""
        return DaemonProcessState()

    def test_gmail_operational_with_recent_check(self, state):
        """Test Gmail shows operational with recent check."""
        state.last_gmail_check = datetime.now(UTC) - timedelta(minutes=5)
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.gmail_status == HealthStatus.OPERATIONAL

    def test_gmail_degraded_with_stale_check(self, state):
        """Test Gmail shows degraded with stale check."""
        state.last_gmail_check = datetime.now(UTC) - timedelta(minutes=45)
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.gmail_status == HealthStatus.DEGRADED

    def test_gmail_unavailable_with_no_check(self, state):
        """Test Gmail shows unavailable with no check."""
        state.last_gmail_check = None
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.gmail_status == HealthStatus.UNAVAILABLE

    def test_notion_operational_with_recent_check(self, state):
        """Test Notion shows operational with recent check."""
        state.last_notion_check = datetime.now(UTC) - timedelta(minutes=5)
        state.notion_validation_failures = 0
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.notion_status == HealthStatus.OPERATIONAL

    def test_notion_degraded_with_validation_failures(self, state):
        """Test Notion shows degraded with validation failures."""
        state.last_notion_check = datetime.now(UTC) - timedelta(minutes=5)
        state.notion_validation_failures = 3
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.notion_status == HealthStatus.DEGRADED

    def test_overall_status_unavailable_if_any_unavailable(self, state):
        """Test overall status is unavailable if any component unavailable."""
        state.last_gmail_check = None
        state.last_notion_check = datetime.now(UTC)
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.overall_status == HealthStatus.UNAVAILABLE

    def test_overall_status_degraded_if_any_degraded(self, state):
        """Test overall status is degraded if any component degraded."""
        state.last_gmail_check = datetime.now(UTC) - timedelta(minutes=45)  # Stale
        state.last_notion_check = datetime.now(UTC)
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.overall_status == HealthStatus.DEGRADED

    def test_overall_status_operational_if_all_operational(self, state):
        """Test overall status is operational if all components operational."""
        state.last_gmail_check = datetime.now(UTC)
        state.last_notion_check = datetime.now(UTC)
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.overall_status == HealthStatus.OPERATIONAL

    def test_token_expiry_included(self, state):
        """Test that token expiry is included in health status."""
        expiry = datetime.now(UTC) + timedelta(days=5)
        state.last_gmail_check = datetime.now(UTC)
        state.gmail_token_expiry = expiry
        collector = MetricsCollector(state)

        health = collector.collect_component_health()

        assert health.gmail_token_expiry == expiry


class TestCollectProcessingMetrics:
    """Tests for collect_processing_metrics method."""

    @pytest.fixture
    def state(self):
        """Create DaemonProcessState with sample data."""
        state = DaemonProcessState()
        state.emails_received_count = 100
        state.emails_processed_count = 95
        state.emails_skipped_count = 5
        state.total_processing_cycles = 10
        return state

    def test_collects_counts(self, state):
        """Test that counts are collected correctly."""
        collector = MetricsCollector(state)

        metrics = collector.collect_processing_metrics()

        assert metrics.emails_received == 100
        assert metrics.emails_processed == 95
        assert metrics.emails_skipped == 5
        assert metrics.processing_cycles == 10

    def test_computes_success_rate(self, state):
        """Test success rate computation."""
        collector = MetricsCollector(state)

        metrics = collector.collect_processing_metrics()

        assert metrics.success_rate == pytest.approx(0.95)

    def test_success_rate_with_no_emails(self):
        """Test success rate is 1.0 with no emails."""
        state = DaemonProcessState()
        state.emails_received_count = 0
        state.emails_processed_count = 0
        collector = MetricsCollector(state)

        metrics = collector.collect_processing_metrics()

        assert metrics.success_rate == 1.0

    def test_average_processing_time_calculated(self, state):
        """Test average processing time calculation."""
        # Set daemon start time to 100 minutes ago
        state.daemon_start_timestamp = datetime.now(UTC) - timedelta(minutes=100)
        state.total_processing_cycles = 10
        collector = MetricsCollector(state)

        metrics = collector.collect_processing_metrics()

        # Should be approximately 600 seconds (10 minutes) per cycle
        assert metrics.average_processing_time_seconds > 0


class TestCollectErrorSummary:
    """Tests for collect_error_summary method."""

    @pytest.fixture
    def state(self):
        """Create DaemonProcessState with error data."""
        state = DaemonProcessState()
        state.emails_received_count = 100
        return state

    def test_categorizes_critical_errors(self, state):
        """Test critical errors are categorized."""
        now = datetime.now(UTC)
        state.recent_errors = [
            {
                "timestamp": now.isoformat(),
                "severity": "critical",
                "component": "gmail",
                "message": "Authentication failed",
            }
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        assert len(summary.critical_errors) == 1
        assert summary.critical_errors[0]["severity"] == "critical"

    def test_categorizes_high_errors(self, state):
        """Test high severity errors are categorized."""
        now = datetime.now(UTC)
        state.recent_errors = [
            {
                "timestamp": now.isoformat(),
                "severity": "high",
                "component": "notion",
                "message": "Rate limit exceeded",
            }
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        assert len(summary.high_errors) == 1

    def test_counts_low_errors(self, state):
        """Test low severity errors are counted."""
        now = datetime.now(UTC)
        state.recent_errors = [
            {
                "timestamp": now.isoformat(),
                "severity": "low",
                "component": "llm",
                "message": "Retry succeeded",
            },
            {
                "timestamp": now.isoformat(),
                "severity": "low",
                "component": "llm",
                "message": "Retry succeeded",
            },
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        assert summary.low_error_count == 2

    def test_computes_total_error_count(self, state):
        """Test total error count computation."""
        now = datetime.now(UTC)
        state.recent_errors = [
            {"timestamp": now.isoformat(), "severity": "critical", "component": "gmail", "message": "Error 1"},
            {"timestamp": now.isoformat(), "severity": "high", "component": "notion", "message": "Error 2"},
            {"timestamp": now.isoformat(), "severity": "low", "component": "llm", "message": "Error 3"},
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        assert summary.total_error_count == 3

    def test_computes_error_rate(self, state):
        """Test error rate computation."""
        now = datetime.now(UTC)
        state.emails_received_count = 100
        state.notion_entries_created = 50
        state.notion_entries_updated = 0
        state.recent_errors = [
            {"timestamp": now.isoformat(), "severity": "high", "component": "test", "message": "Error"}
            for _ in range(15)
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        # 15 errors / 150 operations = 0.1
        assert summary.error_rate == pytest.approx(0.1)

    def test_filters_errors_by_period(self, state):
        """Test that only errors in period are counted."""
        now = datetime.now(UTC)
        old_time = now - timedelta(days=2)  # Outside 24h period

        state.recent_errors = [
            {"timestamp": now.isoformat(), "severity": "high", "component": "test", "message": "Recent"},
            {"timestamp": old_time.isoformat(), "severity": "critical", "component": "test", "message": "Old"},
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        # Only the recent error should be counted
        assert summary.total_error_count == 1
        assert len(summary.high_errors) == 1
        assert len(summary.critical_errors) == 0

    def test_top_error_categories(self, state):
        """Test top error categories are computed."""
        now = datetime.now(UTC)
        state.recent_errors = [
            {"timestamp": now.isoformat(), "severity": "high", "component": "gmail", "message": "Auth error"} for _ in range(5)
        ] + [
            {"timestamp": now.isoformat(), "severity": "high", "component": "notion", "message": "Rate limit"} for _ in range(3)
        ]
        collector = MetricsCollector(state)

        summary = collector.collect_error_summary()

        assert len(summary.top_error_categories) > 0
        # First category should be gmail with 5 occurrences
        assert summary.top_error_categories[0].count == 5


class TestCollectLLMUsage:
    """Tests for collect_llm_usage method."""

    @pytest.fixture
    def state(self):
        """Create DaemonProcessState with LLM data."""
        state = DaemonProcessState()
        state.llm_calls_by_provider = {"gemini": 50, "claude": 30, "openai": 20}
        state.llm_costs_by_provider = {"gemini": 0.10, "claude": 0.50, "openai": 0.20}
        return state

    def test_collects_calls_by_provider(self, state):
        """Test calls by provider are collected."""
        collector = MetricsCollector(state)

        usage = collector.collect_llm_usage()

        assert usage.calls_by_provider["gemini"] == 50
        assert usage.calls_by_provider["claude"] == 30
        assert usage.calls_by_provider["openai"] == 20

    def test_collects_costs_by_provider(self, state):
        """Test costs by provider are collected."""
        collector = MetricsCollector(state)

        usage = collector.collect_llm_usage()

        assert usage.costs_by_provider["gemini"] == pytest.approx(0.10)
        assert usage.costs_by_provider["claude"] == pytest.approx(0.50)
        assert usage.costs_by_provider["openai"] == pytest.approx(0.20)

    def test_computes_totals(self, state):
        """Test total calls and costs are computed."""
        collector = MetricsCollector(state)

        usage = collector.collect_llm_usage()

        assert usage.total_calls == 100
        assert usage.total_cost == pytest.approx(0.80)

    def test_identifies_primary_provider(self, state):
        """Test primary provider identification."""
        collector = MetricsCollector(state)

        usage = collector.collect_llm_usage()

        assert usage.primary_provider == "gemini"  # Most calls

    def test_includes_provider_health(self, state):
        """Test provider health is included."""
        state.last_gmail_check = datetime.now(UTC)
        collector = MetricsCollector(state)

        usage = collector.collect_llm_usage()

        assert "gemini" in usage.provider_health


class TestCollectNotionStats:
    """Tests for collect_notion_stats method."""

    @pytest.fixture
    def state(self):
        """Create DaemonProcessState with Notion data."""
        state = DaemonProcessState()
        state.notion_entries_created = 45
        state.notion_entries_updated = 10
        state.emails_skipped_count = 5
        state.notion_validation_failures = 2
        state.last_notion_check = datetime.now(UTC)
        return state

    def test_collects_entry_counts(self, state):
        """Test entry counts are collected."""
        collector = MetricsCollector(state)

        stats = collector.collect_notion_stats()

        assert stats.entries_created == 45
        assert stats.entries_updated == 10
        assert stats.entries_skipped == 5
        assert stats.validation_failures == 2

    def test_database_health_degraded_with_failures(self, state):
        """Test database health is degraded with validation failures."""
        collector = MetricsCollector(state)

        stats = collector.collect_notion_stats()

        assert stats.database_health == HealthStatus.DEGRADED

    def test_database_health_operational_without_failures(self, state):
        """Test database health is operational without failures."""
        state.notion_validation_failures = 0
        collector = MetricsCollector(state)

        stats = collector.collect_notion_stats()

        assert stats.database_health == HealthStatus.OPERATIONAL

    def test_database_health_unavailable_without_check(self):
        """Test database health is unavailable without recent check."""
        state = DaemonProcessState()
        state.last_notion_check = None
        collector = MetricsCollector(state)

        stats = collector.collect_notion_stats()

        assert stats.database_health == HealthStatus.UNAVAILABLE


class TestCollectAll:
    """Tests for collect_all method."""

    def test_returns_all_metric_types(self):
        """Test collect_all returns all metric types."""
        state = DaemonProcessState()
        state.last_gmail_check = datetime.now(UTC)
        state.last_notion_check = datetime.now(UTC)
        collector = MetricsCollector(state)

        result = collector.collect_all()

        assert "health_status" in result
        assert "processing_metrics" in result
        assert "error_summary" in result
        assert "llm_usage" in result
        assert "notion_stats" in result
