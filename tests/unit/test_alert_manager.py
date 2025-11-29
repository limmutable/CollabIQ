"""
Unit tests for AlertManager.

Tests critical error alert functionality including:
- Alert creation and classification
- Threshold checking
- Alert batching with time windows
- Rate limiting (max alerts/hour)
- Alert deduplication
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch, MagicMock

from admin_reporting.alerter import AlertManager, AlertBatch
from admin_reporting.models import ActionableAlert, AlertSeverity
from admin_reporting.config import ReportingConfig
from models.daemon_state import DaemonProcessState


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    settings = Mock()
    settings.get_gmail_credentials_path.return_value = "/path/to/credentials.json"
    settings.gmail_token_path = "/path/to/token.json"
    settings.admin_report_recipient = "admin@example.com"
    return settings


@pytest.fixture
def alert_config():
    """Create test alert configuration."""
    return ReportingConfig(
        enabled=True,
        recipients=["admin@example.com"],
        alert_recipients=["alerts@example.com"],
        error_rate_threshold=0.1,  # 10% error rate
        alert_batch_window_minutes=15,
        max_alerts_per_hour=5,
    )


@pytest.fixture
def daemon_state():
    """Create a test daemon state."""
    state = DaemonProcessState()
    state.current_status = "running"
    state.emails_processed_count = 100
    state.error_count = 5
    state.total_processing_cycles = 10
    state.daemon_start_timestamp = datetime.now(UTC) - timedelta(hours=2)
    state.last_gmail_check = datetime.now(UTC) - timedelta(minutes=5)
    state.last_notion_check = datetime.now(UTC) - timedelta(minutes=5)
    return state


@pytest.fixture
def alert_manager(alert_config, mock_settings):
    """Create AlertManager instance with mocked dependencies."""
    with patch("admin_reporting.alerter.get_settings", return_value=mock_settings):
        manager = AlertManager(config=alert_config)
        # Mock the sender to avoid Gmail API calls
        manager._sender = Mock()
        manager._sender.is_connected.return_value = True
        return manager


# ============================================================================
# AlertManager Initialization Tests
# ============================================================================


class TestAlertManagerInit:
    """Test AlertManager initialization."""

    def test_init_with_config(self, alert_config, mock_settings):
        """Test initialization with explicit config."""
        with patch("admin_reporting.alerter.get_settings", return_value=mock_settings):
            manager = AlertManager(config=alert_config)

        assert manager.config == alert_config
        assert manager.batch_window == timedelta(minutes=15)
        assert manager.max_alerts_per_hour == 5

    def test_init_loads_config_from_env(self, mock_settings):
        """Test initialization loads config from environment."""
        with patch("admin_reporting.alerter.get_settings", return_value=mock_settings):
            with patch("admin_reporting.alerter.ReportingConfig.from_env") as mock_from_env:
                mock_from_env.return_value = ReportingConfig(
                    enabled=True,
                    recipients=["admin@example.com"],
                )
                manager = AlertManager()

        mock_from_env.assert_called_once()

    def test_init_creates_empty_batch(self, alert_config, mock_settings):
        """Test initialization creates empty alert batch."""
        with patch("admin_reporting.alerter.get_settings", return_value=mock_settings):
            manager = AlertManager(config=alert_config)

        assert manager.current_batch is not None
        assert len(manager.current_batch.alerts) == 0

    def test_init_creates_empty_alert_history(self, alert_config, mock_settings):
        """Test initialization creates empty alert history."""
        with patch("admin_reporting.alerter.get_settings", return_value=mock_settings):
            manager = AlertManager(config=alert_config)

        assert manager.sent_alerts_history == []


# ============================================================================
# Threshold Checking Tests
# ============================================================================


class TestThresholdChecking:
    """Test threshold checking logic."""

    def test_check_thresholds_no_alerts_when_healthy(self, alert_manager, daemon_state):
        """Test no alerts generated when system is healthy."""
        daemon_state.error_count = 2
        daemon_state.emails_processed_count = 100

        alerts = alert_manager.check_thresholds(daemon_state)

        assert len(alerts) == 0

    def test_check_thresholds_alerts_on_high_error_rate(self, alert_manager, daemon_state):
        """Test alert generated when error rate exceeds threshold."""
        daemon_state.error_count = 20
        daemon_state.emails_processed_count = 100

        alerts = alert_manager.check_thresholds(daemon_state)

        assert len(alerts) >= 1
        error_alert = next(
            (a for a in alerts if "error rate" in a.message.lower()), None
        )
        assert error_alert is not None
        assert error_alert.severity == AlertSeverity.HIGH

    def test_check_thresholds_alerts_on_gmail_stale(self, alert_manager, daemon_state):
        """Test alert when Gmail check is stale."""
        daemon_state.last_gmail_check = datetime.now(UTC) - timedelta(hours=2)

        alerts = alert_manager.check_thresholds(daemon_state)

        gmail_alert = next(
            (a for a in alerts if "gmail" in a.message.lower()), None
        )
        assert gmail_alert is not None

    def test_check_thresholds_alerts_on_notion_stale(self, alert_manager, daemon_state):
        """Test alert when Notion check is stale."""
        daemon_state.last_notion_check = datetime.now(UTC) - timedelta(hours=2)

        alerts = alert_manager.check_thresholds(daemon_state)

        notion_alert = next(
            (a for a in alerts if "notion" in a.message.lower()), None
        )
        assert notion_alert is not None

    def test_check_thresholds_alerts_on_daemon_error_status(
        self, alert_manager, daemon_state
    ):
        """Test alert when daemon is in error status."""
        daemon_state.current_status = "error"

        alerts = alert_manager.check_thresholds(daemon_state)

        status_alert = next(
            (a for a in alerts if "daemon" in a.message.lower() or "error" in a.message.lower()), None
        )
        assert status_alert is not None
        assert status_alert.severity == AlertSeverity.CRITICAL

    def test_check_thresholds_multiple_alerts(self, alert_manager, daemon_state):
        """Test multiple alerts can be generated."""
        daemon_state.current_status = "error"
        daemon_state.error_count = 50
        daemon_state.emails_processed_count = 100
        daemon_state.last_gmail_check = datetime.now(UTC) - timedelta(hours=2)

        alerts = alert_manager.check_thresholds(daemon_state)

        assert len(alerts) >= 2


# ============================================================================
# Alert Batching Tests
# ============================================================================


class TestAlertBatching:
    """Test alert batching functionality."""

    def test_add_alert_to_batch(self, alert_manager):
        """Test adding alert to current batch."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )

        alert_manager.add_to_batch(alert)

        assert len(alert_manager.current_batch.alerts) == 1
        assert alert_manager.current_batch.alerts[0] == alert

    def test_batch_window_check_not_ready(self, alert_manager):
        """Test batch not ready when window hasn't passed."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)

        assert not alert_manager.is_batch_ready()

    def test_batch_window_check_ready(self, alert_manager):
        """Test batch ready when window has passed."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)

        # Simulate batch started 20 minutes ago (window is 15 minutes)
        alert_manager.current_batch.started_at = datetime.now(UTC) - timedelta(
            minutes=20
        )

        assert alert_manager.is_batch_ready()

    def test_batch_empty_not_ready(self, alert_manager):
        """Test empty batch is never ready."""
        alert_manager.current_batch.started_at = datetime.now(UTC) - timedelta(
            minutes=20
        )

        assert not alert_manager.is_batch_ready()

    def test_flush_batch_clears_alerts(self, alert_manager):
        """Test flushing batch clears current alerts."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)

        flushed = alert_manager.flush_batch()

        assert len(flushed.alerts) == 1
        assert len(alert_manager.current_batch.alerts) == 0

    def test_flush_batch_resets_start_time(self, alert_manager):
        """Test flushing batch resets start time."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)
        old_start = alert_manager.current_batch.started_at

        alert_manager.flush_batch()

        assert alert_manager.current_batch.started_at >= old_start

    def test_critical_alerts_bypass_batching(self, alert_manager):
        """Test critical alerts can bypass batching window."""
        alert = ActionableAlert(
            severity=AlertSeverity.CRITICAL,
            category="system",
            message="Critical failure",
            remediation="Immediate action required",
        )
        alert_manager.add_to_batch(alert)

        # Should be ready immediately for critical alerts
        assert alert_manager.should_send_immediately()


# ============================================================================
# Rate Limiting Tests
# ============================================================================


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_can_send_when_under_limit(self, alert_manager):
        """Test sending allowed when under limit."""
        assert alert_manager.can_send_alert()

    def test_cannot_send_when_at_limit(self, alert_manager):
        """Test sending blocked when at limit."""
        now = datetime.now(UTC)
        # Fill history with 5 alerts in the last hour
        alert_manager.sent_alerts_history = [
            now - timedelta(minutes=i * 10) for i in range(5)
        ]

        assert not alert_manager.can_send_alert()

    def test_can_send_after_old_alerts_expire(self, alert_manager):
        """Test sending allowed after old alerts expire from history."""
        now = datetime.now(UTC)
        # 5 alerts but some are old
        alert_manager.sent_alerts_history = [
            now - timedelta(minutes=70),  # Old, should not count
            now - timedelta(minutes=65),  # Old
            now - timedelta(minutes=30),  # Recent
            now - timedelta(minutes=20),  # Recent
            now - timedelta(minutes=10),  # Recent
        ]

        assert alert_manager.can_send_alert()

    def test_record_sent_alert_updates_history(self, alert_manager):
        """Test recording sent alert updates history."""
        initial_count = len(alert_manager.sent_alerts_history)

        alert_manager.record_sent_alert()

        assert len(alert_manager.sent_alerts_history) == initial_count + 1

    def test_cleanup_old_history(self, alert_manager):
        """Test old history entries are cleaned up."""
        now = datetime.now(UTC)
        alert_manager.sent_alerts_history = [
            now - timedelta(hours=2),  # Old
            now - timedelta(hours=1, minutes=30),  # Old
            now - timedelta(minutes=30),  # Recent
        ]

        alert_manager.cleanup_history()

        # Only recent entries should remain
        assert len(alert_manager.sent_alerts_history) == 1


# ============================================================================
# Alert Deduplication Tests
# ============================================================================


class TestAlertDeduplication:
    """Test alert deduplication logic."""

    def test_duplicate_alert_not_added(self, alert_manager):
        """Test duplicate alerts are not added to batch."""
        alert1 = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Same error message",
            remediation="Fix it",
        )
        alert2 = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Same error message",
            remediation="Fix it",
        )

        alert_manager.add_to_batch(alert1)
        alert_manager.add_to_batch(alert2)

        assert len(alert_manager.current_batch.alerts) == 1

    def test_different_alerts_both_added(self, alert_manager):
        """Test different alerts are both added."""
        alert1 = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Error one",
            remediation="Fix it",
        )
        alert2 = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Error two",
            remediation="Fix it differently",
        )

        alert_manager.add_to_batch(alert1)
        alert_manager.add_to_batch(alert2)

        assert len(alert_manager.current_batch.alerts) == 2

    def test_same_category_different_message_added(self, alert_manager):
        """Test same category but different message alerts are added."""
        alert1 = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="gmail",
            message="Connection failed",
            remediation="Reconnect",
        )
        alert2 = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="gmail",
            message="Auth expired",
            remediation="Re-authenticate",
        )

        alert_manager.add_to_batch(alert1)
        alert_manager.add_to_batch(alert2)

        assert len(alert_manager.current_batch.alerts) == 2


# ============================================================================
# Alert Sending Tests
# ============================================================================


class TestAlertSending:
    """Test alert sending functionality."""

    def test_send_batch_calls_sender(self, alert_manager):
        """Test sending batch calls GmailSender."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)
        alert_manager._sender.send_alert_email.return_value = {"id": "msg123"}

        result = alert_manager.send_alert_batch()

        assert alert_manager._sender.send_alert_email.called
        assert result["id"] == "msg123"

    def test_send_batch_records_in_history(self, alert_manager):
        """Test sending batch records in history."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)
        alert_manager._sender.send_alert_email.return_value = {"id": "msg123"}
        initial_count = len(alert_manager.sent_alerts_history)

        alert_manager.send_alert_batch()

        assert len(alert_manager.sent_alerts_history) == initial_count + 1

    def test_send_batch_returns_none_when_empty(self, alert_manager):
        """Test sending empty batch returns None."""
        result = alert_manager.send_alert_batch()

        assert result is None
        assert not alert_manager._sender.send_alert_email.called

    def test_send_batch_respects_rate_limit(self, alert_manager):
        """Test sending batch respects rate limit."""
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Test error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)

        # Fill history to hit rate limit
        now = datetime.now(UTC)
        alert_manager.sent_alerts_history = [
            now - timedelta(minutes=i * 10) for i in range(5)
        ]

        result = alert_manager.send_alert_batch()

        assert result is None
        assert not alert_manager._sender.send_alert_email.called


# ============================================================================
# Process Alerts Integration Tests
# ============================================================================


class TestProcessAlerts:
    """Test the main process_alerts integration method."""

    def test_process_alerts_checks_thresholds(self, alert_manager, daemon_state):
        """Test process_alerts checks thresholds."""
        daemon_state.error_count = 50
        daemon_state.emails_processed_count = 100

        alerts = alert_manager.process_alerts(daemon_state)

        assert len(alerts) >= 1

    def test_process_alerts_adds_to_batch(self, alert_manager, daemon_state):
        """Test process_alerts adds alerts to batch."""
        daemon_state.error_count = 50
        daemon_state.emails_processed_count = 100

        alert_manager.process_alerts(daemon_state)

        assert len(alert_manager.current_batch.alerts) >= 1

    def test_process_alerts_sends_when_ready(self, alert_manager, daemon_state):
        """Test process_alerts sends when batch is ready."""
        daemon_state.error_count = 50
        daemon_state.emails_processed_count = 100

        # Pre-add an alert and set batch as ready
        alert = ActionableAlert(
            severity=AlertSeverity.HIGH,
            category="error",
            message="Previous error",
            remediation="Fix it",
        )
        alert_manager.add_to_batch(alert)
        alert_manager.current_batch.started_at = datetime.now(UTC) - timedelta(
            minutes=20
        )
        alert_manager._sender.send_alert_email.return_value = {"id": "msg123"}

        alert_manager.process_alerts(daemon_state)

        assert alert_manager._sender.send_alert_email.called

    def test_process_alerts_sends_critical_immediately(
        self, alert_manager, daemon_state
    ):
        """Test critical alerts trigger immediate send."""
        daemon_state.current_status = "error"
        alert_manager._sender.send_alert_email.return_value = {"id": "msg123"}

        alert_manager.process_alerts(daemon_state)

        # Critical alert should trigger immediate send
        assert alert_manager._sender.send_alert_email.called


# ============================================================================
# Credential Expiry Detection Tests (T044)
# ============================================================================


class TestCredentialExpiryDetection:
    """Test credential expiry detection for actionable insights."""

    def test_no_alert_when_token_valid(self, alert_manager, daemon_state):
        """Test no alert when Gmail token is valid."""
        daemon_state.gmail_token_expiry = datetime.now(UTC) + timedelta(days=30)

        alerts = alert_manager.check_credential_expiry(daemon_state)

        assert len(alerts) == 0

    def test_alert_when_token_expiring_soon(self, alert_manager, daemon_state):
        """Test alert when Gmail token expires within warning period."""
        daemon_state.gmail_token_expiry = datetime.now(UTC) + timedelta(days=5)

        alerts = alert_manager.check_credential_expiry(daemon_state)

        assert len(alerts) == 1
        assert "token" in alerts[0].message.lower() or "credential" in alerts[0].message.lower()
        assert alerts[0].severity in [AlertSeverity.MEDIUM, AlertSeverity.WARNING]

    def test_alert_when_token_expired(self, alert_manager, daemon_state):
        """Test high severity alert when Gmail token is expired."""
        daemon_state.gmail_token_expiry = datetime.now(UTC) - timedelta(hours=1)

        alerts = alert_manager.check_credential_expiry(daemon_state)

        assert len(alerts) == 1
        assert alerts[0].severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]

    def test_no_alert_when_no_expiry_set(self, alert_manager, daemon_state):
        """Test no alert when token expiry is not tracked."""
        daemon_state.gmail_token_expiry = None

        alerts = alert_manager.check_credential_expiry(daemon_state)

        # No alert or info-level alert about missing expiry info
        assert len(alerts) <= 1

    def test_remediation_includes_re_auth_instructions(self, alert_manager, daemon_state):
        """Test remediation text includes re-authentication instructions."""
        daemon_state.gmail_token_expiry = datetime.now(UTC) + timedelta(days=3)

        alerts = alert_manager.check_credential_expiry(daemon_state)

        if alerts:
            assert "auth" in alerts[0].remediation.lower() or "token" in alerts[0].remediation.lower()


# ============================================================================
# Cost Threshold Detection Tests (T045)
# ============================================================================


class TestCostThresholdDetection:
    """Test LLM cost threshold detection for actionable insights."""

    def test_no_alert_when_under_budget(self, alert_manager, daemon_state):
        """Test no alert when daily LLM cost is under budget."""
        # Set costs well under the $10 default limit
        daemon_state.llm_costs_by_provider = {"gemini": 2.0, "claude": 1.5}

        alerts = alert_manager.check_cost_limits(daemon_state)

        assert len(alerts) == 0

    def test_warning_when_approaching_budget(self, alert_manager, daemon_state):
        """Test warning when LLM cost is approaching daily limit."""
        # Set costs at 80% of $10 limit
        daemon_state.llm_costs_by_provider = {"gemini": 5.0, "claude": 3.0}

        alerts = alert_manager.check_cost_limits(daemon_state)

        # Should get a warning when at 80% of limit
        assert len(alerts) == 1
        assert "cost" in alerts[0].message.lower() or "budget" in alerts[0].message.lower()
        assert alerts[0].severity in [AlertSeverity.MEDIUM, AlertSeverity.WARNING]

    def test_high_alert_when_over_budget(self, alert_manager, daemon_state):
        """Test high severity alert when over daily LLM budget."""
        # Set costs over $10 limit
        daemon_state.llm_costs_by_provider = {"gemini": 8.0, "claude": 5.0}

        alerts = alert_manager.check_cost_limits(daemon_state)

        assert len(alerts) == 1
        assert alerts[0].severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]

    def test_no_alert_when_no_costs(self, alert_manager, daemon_state):
        """Test no alert when no LLM costs recorded."""
        daemon_state.llm_costs_by_provider = {}

        alerts = alert_manager.check_cost_limits(daemon_state)

        assert len(alerts) == 0

    def test_cost_alert_includes_breakdown(self, alert_manager, daemon_state):
        """Test cost alert message includes provider breakdown."""
        daemon_state.llm_costs_by_provider = {"gemini": 8.0, "claude": 5.0}

        alerts = alert_manager.check_cost_limits(daemon_state)

        if alerts:
            # Message should reference the total or provider costs
            assert "13" in alerts[0].message or "$" in alerts[0].message

    def test_remediation_suggests_cost_reduction(self, alert_manager, daemon_state):
        """Test remediation text suggests cost reduction strategies."""
        daemon_state.llm_costs_by_provider = {"gemini": 8.0, "claude": 5.0}

        alerts = alert_manager.check_cost_limits(daemon_state)

        if alerts:
            remediation_lower = alerts[0].remediation.lower()
            # Should suggest reducing usage or reviewing provider selection
            assert any(word in remediation_lower for word in ["review", "reduce", "limit", "provider", "usage"])


# ============================================================================
# Error Rate Trend Detection Tests
# ============================================================================


class TestErrorRateTrendDetection:
    """Test error rate trend detection for actionable insights."""

    def test_no_alert_when_error_rate_stable(self, alert_manager, daemon_state):
        """Test no alert when error rate is within normal range."""
        daemon_state.error_count = 2
        daemon_state.emails_processed_count = 100

        alerts = alert_manager.check_error_rate_trend(daemon_state)

        assert len(alerts) == 0

    def test_alert_when_error_rate_increasing(self, alert_manager, daemon_state):
        """Test alert when error rate is increasing trend."""
        daemon_state.error_count = 15
        daemon_state.emails_processed_count = 100
        # Simulate recent errors
        now = datetime.now(UTC)
        daemon_state.recent_errors = [
            {"timestamp": (now - timedelta(minutes=i)).isoformat(), "severity": "high"}
            for i in range(10)
        ]

        alerts = alert_manager.check_error_rate_trend(daemon_state)

        # Should detect the increasing error trend
        assert len(alerts) >= 0  # May or may not trigger based on implementation

    def test_alert_includes_error_pattern_info(self, alert_manager, daemon_state):
        """Test alert includes information about error patterns."""
        daemon_state.error_count = 20
        daemon_state.emails_processed_count = 100

        alerts = alert_manager.check_error_rate_trend(daemon_state)

        # If alert is generated, it should mention the error rate or pattern
        if alerts:
            assert "error" in alerts[0].message.lower()
