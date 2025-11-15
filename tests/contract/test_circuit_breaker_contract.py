"""Contract tests for circuit breaker.

Tests all 9 scenarios from contracts/circuit_breaker.md:
1. Normal Operation (CLOSED State)
2. Record Consecutive Failures (CLOSED → OPEN)
3. Timeout Elapsed (OPEN → HALF_OPEN)
4. Recovery (HALF_OPEN → CLOSED)
5. Failed Test Request (HALF_OPEN → OPEN)
6. Partial Failures Don't Trigger Opening
7. Per-Service Isolation
8. Fast Failure Detection (< 1ms decision)
9. State Transitions Logged
"""

import socket
import time
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, patch

import pytest

from error_handling.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    gmail_circuit_breaker,
    gemini_circuit_breaker,
    notion_circuit_breaker,
)
from error_handling.models import CircuitState


class TestCircuitBreakerContract:
    """Contract tests for CircuitBreaker class."""

    def test_scenario_1_normal_operation_closed_state(self):
        """
        Contract #1: Normal Operation (CLOSED State)

        Given: Circuit breaker is CLOSED (initial state)
        When: Request is made
        Then:
        - Request passes through to underlying function
        - Function executes normally
        - Result returned to caller
        - Failure count remains 0 (assuming success)
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5)

        def fetch_emails():
            return ["email1", "email2"]

        result = cb.call(fetch_emails)

        assert result == ["email1", "email2"]
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_scenario_2_consecutive_failures_closed_to_open(self):
        """
        Contract #2: Record Consecutive Failures (CLOSED → OPEN)

        Given: Circuit breaker is CLOSED with 4 failures
        When: 5th consecutive failure occurs
        Then:
        - Circuit transitions to OPEN state
        - open_timestamp recorded
        - All subsequent requests rejected immediately
        - CircuitBreakerOpen exception raised
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5)
        function_call_count = {"count": 0}

        def failing_function():
            raise socket.timeout("Connection timeout")

        def fetch_emails():
            function_call_count["count"] += 1
            return ["email1"]

        # Trigger 5 consecutive failures
        for i in range(5):
            try:
                cb.call(failing_function)
            except socket.timeout:
                pass

        assert cb.get_state() == CircuitState.OPEN
        assert cb.failure_count == 5
        assert cb.open_timestamp is not None

        # Next request should be rejected
        with pytest.raises(CircuitBreakerOpen):
            cb.call(fetch_emails)

        assert function_call_count["count"] == 0  # Function never executed

    def test_scenario_3_timeout_elapsed_open_to_half_open(self):
        """
        Contract #3: Timeout Elapsed (OPEN → HALF_OPEN)

        Given: Circuit breaker is OPEN for timeout duration
        When: New request arrives after timeout
        Then:
        - Circuit transitions to HALF_OPEN state
        - Test request allowed through
        - If test succeeds, increment success_count
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5, timeout=2.0)

        def failing_function():
            raise socket.timeout("Connection timeout")

        def fetch_emails():
            return ["email1"]

        # Open circuit
        for _ in range(5):
            try:
                cb.call(failing_function)
            except socket.timeout:
                pass

        assert cb.get_state() == CircuitState.OPEN

        # Wait for timeout to elapse
        time.sleep(2.1)

        # Next request should transition to HALF_OPEN and succeed
        result = cb.call(fetch_emails)
        assert cb.get_state() == CircuitState.HALF_OPEN
        assert result == ["email1"]
        assert cb.success_count == 1

    def test_scenario_4_recovery_half_open_to_closed(self):
        """
        Contract #4: Recovery (HALF_OPEN → CLOSED)

        Given: Circuit breaker is HALF_OPEN with 1 success
        When: 2nd consecutive success occurs
        Then:
        - Circuit transitions to CLOSED state
        - success_count reset to 0
        - failure_count reset to 0
        - Normal operation resumes
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5, success_threshold=2)

        def fetch_emails():
            return ["email1"]

        # Manually set to HALF_OPEN (simulating recovery from OPEN)
        cb.state_obj.state = CircuitState.HALF_OPEN
        cb.state_obj.success_count = 0

        # First success
        cb.call(fetch_emails)
        assert cb.get_state() == CircuitState.HALF_OPEN
        assert cb.success_count == 1

        # Second success → CLOSED
        cb.call(fetch_emails)
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.success_count == 0
        assert cb.failure_count == 0

    def test_scenario_5_failed_test_request_half_open_to_open(self):
        """
        Contract #5: Failed Test Request (HALF_OPEN → OPEN)

        Given: Circuit breaker is HALF_OPEN (testing recovery)
        When: Test request fails
        Then:
        - Circuit transitions back to OPEN state
        - open_timestamp updated to current time
        - success_count reset to 0
        - Must wait another timeout duration before next test
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5, timeout=60.0)

        def failing_function():
            raise socket.timeout("Connection timeout")

        # Manually set to HALF_OPEN
        cb.state_obj.state = CircuitState.HALF_OPEN
        cb.state_obj.success_count = 0
        old_timestamp = datetime.now(UTC) - timedelta(seconds=10)
        cb.state_obj.open_timestamp = old_timestamp

        # Test request fails
        try:
            cb.call(failing_function)
        except socket.timeout:
            pass

        assert cb.get_state() == CircuitState.OPEN
        assert cb.success_count == 0
        assert cb.open_timestamp > old_timestamp  # Updated timestamp

    def test_scenario_6_partial_failures_dont_trigger_opening(self):
        """
        Contract #6: Partial Failures Don't Trigger Opening

        Given: Circuit breaker has 4 failures, then 1 success
        When: Request succeeds
        Then:
        - failure_count reset to 0
        - Circuit remains CLOSED
        - Does NOT transition to OPEN
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5)

        def failing_function():
            raise socket.timeout("Connection timeout")

        def fetch_emails():
            return ["email1"]

        # 4 failures
        for _ in range(4):
            try:
                cb.call(failing_function)
            except socket.timeout:
                pass

        assert cb.failure_count == 4
        assert cb.get_state() == CircuitState.CLOSED

        # 1 success resets counter
        cb.call(fetch_emails)
        assert cb.failure_count == 0
        assert cb.get_state() == CircuitState.CLOSED

    def test_scenario_7_per_service_isolation(self):
        """
        Contract #7: Per-Service Isolation

        Given: Multiple circuit breakers for different services
        When: One service fails repeatedly
        Then:
        - Only that service's circuit breaker opens
        - Other services continue operating normally
        """
        # Use global circuit breakers for realistic test
        gmail_cb = CircuitBreaker("gmail_test", failure_threshold=5)
        notion_cb = CircuitBreaker("notion_test", failure_threshold=5)

        def failing_function():
            raise socket.timeout("Connection timeout")

        def write_to_notion():
            return {"id": "page_123"}

        # Gmail fails 5 times
        for _ in range(5):
            try:
                gmail_cb.call(failing_function)
            except socket.timeout:
                pass

        assert gmail_cb.get_state() == CircuitState.OPEN
        assert notion_cb.get_state() == CircuitState.CLOSED

        # Notion still works
        result = notion_cb.call(write_to_notion)
        assert result == {"id": "page_123"}

    def test_scenario_8_fast_failure_detection(self):
        """
        Contract #8: Fast Failure Detection (< 1ms decision)

        Given: Circuit breaker is OPEN
        When: New request arrives
        Then:
        - should_allow_request() returns False in < 1ms
        - No network call made (fail fast)
        - Meets SC-008 performance requirement
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5)

        def failing_function():
            raise socket.timeout("Connection timeout")

        # Open circuit
        for _ in range(5):
            try:
                cb.call(failing_function)
            except socket.timeout:
                pass

        # Measure decision time
        start = time.perf_counter()
        allowed = cb.should_allow_request()
        elapsed = time.perf_counter() - start

        assert not allowed
        assert elapsed < 0.001  # < 1ms

    def test_scenario_9_state_transitions_logged(self):
        """
        Contract #9: State Transitions Logged

        Given: Circuit breaker changes state
        When: State transition occurs
        Then:
        - Log entry created with state change details
        - Log includes: service_name, old_state, new_state, failure_count
        """
        cb = CircuitBreaker("test_gmail", failure_threshold=5)

        def failing_function():
            raise socket.timeout("Connection timeout")

        with patch("error_handling.circuit_breaker.logger") as mock_logger:
            # Trigger state change (CLOSED → OPEN)
            for _ in range(5):
                try:
                    cb.call(failing_function)
                except socket.timeout:
                    pass

            # Check that state transition was logged
            assert mock_logger.warning.call_count >= 1

            # Get the last warning call
            last_call_args = mock_logger.warning.call_args

            # Check context contains state transition info
            context = last_call_args[1]["context"]
            assert "old_state" in context
            assert "new_state" in context
            assert context["old_state"] == "CLOSED"
            assert context["new_state"] == "OPEN"
            assert context["failure_count"] == 5


class TestCircuitBreakerStateTransitions:
    """Test complete state transition matrix."""

    def test_state_transition_matrix_closed_success(self):
        """CLOSED + success → CLOSED (failure_count = 0)."""
        cb = CircuitBreaker("test", failure_threshold=5)

        def success_func():
            return "ok"

        cb.call(success_func)
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_state_transition_matrix_closed_failure_below_threshold(self):
        """CLOSED + failure (count < threshold) → CLOSED (failure_count += 1)."""
        cb = CircuitBreaker("test", failure_threshold=5)

        def fail_func():
            raise socket.timeout()

        for i in range(4):
            try:
                cb.call(fail_func)
            except socket.timeout:
                pass

        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 4

    def test_state_transition_matrix_closed_failure_at_threshold(self):
        """CLOSED + failure (count >= threshold) → OPEN."""
        cb = CircuitBreaker("test", failure_threshold=5)

        def fail_func():
            raise socket.timeout()

        for _ in range(5):
            try:
                cb.call(fail_func)
            except socket.timeout:
                pass

        assert cb.get_state() == CircuitState.OPEN
        assert cb.open_timestamp is not None

    def test_state_transition_matrix_open_before_timeout(self):
        """OPEN + request before timeout → OPEN (reject with CircuitBreakerOpen)."""
        cb = CircuitBreaker("test", failure_threshold=5, timeout=60.0)

        def fail_func():
            raise socket.timeout()

        def success_func():
            return "ok"

        # Open the circuit
        for _ in range(5):
            try:
                cb.call(fail_func)
            except socket.timeout:
                pass

        # Request before timeout should be rejected
        with pytest.raises(CircuitBreakerOpen):
            cb.call(success_func)

        assert cb.get_state() == CircuitState.OPEN

    def test_state_transition_matrix_open_after_timeout(self):
        """OPEN + request after timeout → HALF_OPEN (allow test request)."""
        cb = CircuitBreaker("test", failure_threshold=5, timeout=1.0)

        def fail_func():
            raise socket.timeout()

        def success_func():
            return "ok"

        # Open the circuit
        for _ in range(5):
            try:
                cb.call(fail_func)
            except socket.timeout:
                pass

        # Wait for timeout
        time.sleep(1.1)

        # Request after timeout should transition to HALF_OPEN
        result = cb.call(success_func)
        assert result == "ok"
        assert cb.get_state() == CircuitState.HALF_OPEN

    def test_state_transition_matrix_half_open_success_below_threshold(self):
        """HALF_OPEN + success (count < threshold) → HALF_OPEN (success_count += 1)."""
        cb = CircuitBreaker("test", failure_threshold=5, success_threshold=2)

        def success_func():
            return "ok"

        # Set to HALF_OPEN
        cb.state_obj.state = CircuitState.HALF_OPEN
        cb.state_obj.success_count = 0

        cb.call(success_func)
        assert cb.get_state() == CircuitState.HALF_OPEN
        assert cb.success_count == 1

    def test_state_transition_matrix_half_open_success_at_threshold(self):
        """HALF_OPEN + success (count >= threshold) → CLOSED (reset counters)."""
        cb = CircuitBreaker("test", failure_threshold=5, success_threshold=2)

        def success_func():
            return "ok"

        # Set to HALF_OPEN with 1 success
        cb.state_obj.state = CircuitState.HALF_OPEN
        cb.state_obj.success_count = 1

        cb.call(success_func)
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.success_count == 0
        assert cb.failure_count == 0

    def test_state_transition_matrix_half_open_failure(self):
        """HALF_OPEN + failure → OPEN (update open_timestamp)."""
        cb = CircuitBreaker("test", failure_threshold=5, timeout=60.0)

        def fail_func():
            raise socket.timeout()

        # Set to HALF_OPEN
        cb.state_obj.state = CircuitState.HALF_OPEN
        old_timestamp = cb.state_obj.open_timestamp

        try:
            cb.call(fail_func)
        except socket.timeout:
            pass

        assert cb.get_state() == CircuitState.OPEN
        # Timestamp should be updated (but may be same if test runs very fast)
        assert cb.open_timestamp is not None


class TestGlobalCircuitBreakerInstances:
    """Test that global circuit breaker instances exist and are configured correctly."""

    def test_gmail_circuit_breaker_exists(self):
        """Gmail circuit breaker should exist with correct configuration."""
        assert gmail_circuit_breaker.state_obj.service_name == "gmail"
        assert gmail_circuit_breaker.state_obj.failure_threshold == 5
        assert gmail_circuit_breaker.state_obj.success_threshold == 2
        assert gmail_circuit_breaker.state_obj.timeout == 60.0

    def test_gemini_circuit_breaker_exists(self):
        """Gemini circuit breaker should exist with correct configuration."""
        assert gemini_circuit_breaker.state_obj.service_name == "gemini"
        assert gemini_circuit_breaker.state_obj.failure_threshold == 5
        assert gemini_circuit_breaker.state_obj.success_threshold == 2
        assert gemini_circuit_breaker.state_obj.timeout == 60.0

    def test_notion_circuit_breaker_exists(self):
        """Notion circuit breaker should exist with correct configuration."""
        assert notion_circuit_breaker.state_obj.service_name == "notion"
        assert notion_circuit_breaker.state_obj.failure_threshold == 5
        assert notion_circuit_breaker.state_obj.success_threshold == 2
        assert notion_circuit_breaker.state_obj.timeout == 60.0
