"""Unit tests for HealthTracker.

This module tests the health tracking and circuit breaker functionality
as defined in specs/012-multi-llm/contracts/health-tracker-interface.md.
"""

import time
from pathlib import Path

import pytest

from llm_adapters.health_tracker import HealthTracker


@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for health metrics."""
    return tmp_path / "llm_health"


@pytest.fixture
def tracker(temp_data_dir):
    """Create HealthTracker instance for testing."""
    return HealthTracker(
        data_dir=temp_data_dir,
        unhealthy_threshold=3,
        circuit_breaker_timeout_seconds=1.0,
        half_open_max_calls=3,
    )


class TestHealthTrackerBasics:
    """Test basic health tracking functionality."""

    def test_is_healthy_returns_true_for_healthy_provider(self, tracker):
        """Test that is_healthy returns True for a healthy provider."""
        # Record some successes
        tracker.record_success("gemini", 1000.0)
        tracker.record_success("gemini", 1200.0)

        assert tracker.is_healthy("gemini") is True

    def test_is_healthy_returns_false_after_threshold_failures(self, tracker):
        """Test that is_healthy returns False after consecutive failures exceed threshold."""
        # Threshold is 3 for this fixture
        for _ in range(3):
            tracker.record_failure("gemini", "API Error")

        assert tracker.is_healthy("gemini") is False

    def test_consecutive_failures_reset_on_success(self, tracker):
        """Test that consecutive_failures resets to 0 on success."""
        # Record some failures
        tracker.record_failure("gemini", "Error 1")
        tracker.record_failure("gemini", "Error 2")

        # Record success
        tracker.record_success("gemini", 1000.0)

        # Check consecutive failures reset
        metrics = tracker.get_metrics("gemini")
        assert metrics.consecutive_failures == 0

    def test_average_response_time_calculation(self, tracker):
        """Test that average response time is calculated correctly."""
        tracker.record_success("gemini", 1000.0)
        tracker.record_success("gemini", 2000.0)
        tracker.record_success("gemini", 3000.0)

        metrics = tracker.get_metrics("gemini")

        # Should use weighted average (alpha=0.2)
        # This won't be a simple arithmetic mean
        assert metrics.average_response_time_ms > 0.0
        assert metrics.average_response_time_ms < 3000.0


class TestCircuitBreaker:
    """Test circuit breaker state machine."""

    def test_circuit_breaker_opens_after_threshold(self, tracker):
        """Test that circuit breaker opens after consecutive failures reach threshold."""
        # Threshold is 3
        for _ in range(3):
            tracker.record_failure("gemini", "API Error")

        metrics = tracker.get_metrics("gemini")
        assert metrics.circuit_breaker_state == "open"
        assert metrics.health_status == "unhealthy"

    def test_circuit_breaker_transitions_to_half_open(self, tracker):
        """Test that circuit breaker transitions from OPEN to HALF_OPEN after timeout."""
        # Open the circuit
        for _ in range(3):
            tracker.record_failure("gemini", "API Error")

        # Verify it's open
        assert tracker.is_healthy("gemini") is False
        assert tracker.get_metrics("gemini").circuit_breaker_state == "open"

        # Wait for timeout (1 second in fixture)
        time.sleep(1.1)

        # Check should transition to HALF_OPEN
        assert tracker.is_healthy("gemini") is True
        metrics = tracker.get_metrics("gemini")
        assert metrics.circuit_breaker_state == "half_open"

    def test_circuit_breaker_closes_after_half_open_successes(self, tracker):
        """Test that circuit breaker closes after successful recovery in HALF_OPEN."""
        # Open the circuit
        for _ in range(3):
            tracker.record_failure("gemini", "API Error")

        # Wait for timeout to transition to HALF_OPEN
        time.sleep(1.1)
        tracker.is_healthy("gemini")  # Trigger transition

        # Record 2 successes (required for CLOSED transition)
        tracker.record_success("gemini", 1000.0)
        tracker.record_success("gemini", 1100.0)

        metrics = tracker.get_metrics("gemini")
        assert metrics.circuit_breaker_state == "closed"
        assert metrics.health_status == "healthy"

    def test_circuit_breaker_reopens_on_half_open_failure(self, tracker):
        """Test that circuit breaker reopens if recovery fails in HALF_OPEN."""
        # Open the circuit
        for _ in range(3):
            tracker.record_failure("gemini", "API Error")

        # Wait for timeout to transition to HALF_OPEN
        time.sleep(1.1)
        tracker.is_healthy("gemini")  # Trigger transition

        # Record a failure during recovery test
        tracker.record_failure("gemini", "Still failing")

        metrics = tracker.get_metrics("gemini")
        assert metrics.circuit_breaker_state == "open"
        assert metrics.health_status == "unhealthy"


class TestPersistence:
    """Test metrics persistence across instances."""

    def test_metrics_persist_across_instances(self, temp_data_dir):
        """Test that metrics are persisted and loaded correctly."""
        # Create first tracker and record some data
        tracker1 = HealthTracker(data_dir=temp_data_dir, unhealthy_threshold=5)
        tracker1.record_success("gemini", 1000.0)
        tracker1.record_success("claude", 1500.0)
        tracker1.record_failure("openai", "Connection error")

        # Create second tracker with same data_dir
        tracker2 = HealthTracker(data_dir=temp_data_dir, unhealthy_threshold=5)

        # Verify metrics were loaded
        gemini_metrics = tracker2.get_metrics("gemini")
        assert gemini_metrics.success_count == 1
        assert gemini_metrics.provider_name == "gemini"

        claude_metrics = tracker2.get_metrics("claude")
        assert claude_metrics.success_count == 1

        openai_metrics = tracker2.get_metrics("openai")
        assert openai_metrics.failure_count == 1

    def test_metrics_file_created_atomically(self, temp_data_dir):
        """Test that metrics file is written atomically."""
        tracker = HealthTracker(data_dir=temp_data_dir)
        tracker.record_success("gemini", 1000.0)

        # Verify the file exists and is valid JSON
        metrics_file = temp_data_dir / "health_metrics.json"
        assert metrics_file.exists()

        # Should be able to load it
        import json

        with open(metrics_file) as f:
            data = json.load(f)

        assert "gemini" in data


class TestMultiProvider:
    """Test tracking multiple providers."""

    def test_get_all_metrics(self, tracker):
        """Test that get_all_metrics returns all provider metrics."""
        tracker.record_success("gemini", 1000.0)
        tracker.record_success("claude", 1500.0)
        tracker.record_failure("openai", "Error")

        all_metrics = tracker.get_all_metrics()

        assert len(all_metrics) == 3
        assert "gemini" in all_metrics
        assert "claude" in all_metrics
        assert "openai" in all_metrics

    def test_reset_metrics(self, tracker):
        """Test that reset_metrics clears all counters."""
        # Record some data
        tracker.record_failure("gemini", "Error 1")
        tracker.record_failure("gemini", "Error 2")
        tracker.record_failure("gemini", "Error 3")

        # Verify it's unhealthy
        assert tracker.is_healthy("gemini") is False

        # Reset
        tracker.reset_metrics("gemini")

        # Verify it's healthy again
        assert tracker.is_healthy("gemini") is True
        metrics = tracker.get_metrics("gemini")
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.consecutive_failures == 0
        assert metrics.circuit_breaker_state == "closed"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_new_provider_initialized_automatically(self, tracker):
        """Test that new providers are initialized with default metrics."""
        # Request metrics for a provider that doesn't exist
        metrics = tracker.get_metrics("new_provider")

        assert metrics.provider_name == "new_provider"
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.health_status == "healthy"
        assert metrics.circuit_breaker_state == "closed"

    def test_error_message_truncated_to_500_chars(self, tracker):
        """Test that error messages are truncated to 500 characters."""
        long_error = "x" * 1000

        tracker.record_failure("gemini", long_error)

        metrics = tracker.get_metrics("gemini")
        assert len(metrics.last_error_message) == 500

    def test_success_rate_calculation(self, tracker):
        """Test that success_rate property is calculated correctly."""
        tracker.record_success("gemini", 1000.0)
        tracker.record_success("gemini", 1100.0)
        tracker.record_failure("gemini", "Error")

        metrics = tracker.get_metrics("gemini")

        # 2 successes, 1 failure = 2/3 = 0.666...
        assert abs(metrics.success_rate - 0.6667) < 0.001

    def test_success_rate_zero_when_no_calls(self, tracker):
        """Test that success_rate is 0.0 when no calls have been made."""
        metrics = tracker.get_metrics("new_provider")

        assert metrics.success_rate == 0.0
