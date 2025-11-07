"""Contract tests for retry decorator.

Tests all 9 scenarios from contracts/retry_decorator.md:
1. Successful Execution (No Retry Needed)
2. Transient Failure Recovers (Retry Succeeds)
3. Exhausted Retries (All Attempts Fail)
4. Rate Limit Handling (Respect Retry-After)
5. Non-Retryable Error (Fail Fast)
6. Circuit Breaker Open (Reject Request)
7. Exponential Backoff with Jitter
8. Async Function Support
9. Logging Integration
"""

import asyncio
import socket
import time
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.error_handling.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    gmail_circuit_breaker,
)
from src.error_handling.models import CircuitState, ErrorCategory, ErrorSeverity


# Mock exception classes for testing
class MockHttpError(Exception):
    """Mock HTTP error for testing."""

    def __init__(self, status_code: int, message: str = "Mock error"):
        self.resp = {"status": str(status_code)}
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class MockAPIResponseError(Exception):
    """Mock Notion API error for testing."""

    def __init__(self, status_code: int, headers: Optional[dict] = None):
        self.status_code = status_code
        self.response = Mock()
        self.response.headers = headers or {}
        self.headers = headers or {}
        super().__init__(f"API Error: {status_code}")


# These tests will fail until retry decorator is implemented (TDD - Red phase)


class TestRetryContract:
    """Contract tests for @retry_with_backoff decorator."""

    def setup_method(self):
        """Reset circuit breaker state before each test."""
        # Reset gmail circuit breaker to CLOSED state
        gmail_circuit_breaker.state_obj.state = CircuitState.CLOSED
        gmail_circuit_breaker.state_obj.failure_count = 0
        gmail_circuit_breaker.state_obj.success_count = 0
        gmail_circuit_breaker.state_obj.open_timestamp = None

    def test_scenario_1_successful_execution_no_retry(self):
        """
        Contract #1: Successful Execution (No Retry Needed)

        Given: Function succeeds on first attempt
        When: Decorated function is called
        Then:
        - Function executes once
        - Result is returned immediately
        - No retry attempts made
        - Circuit breaker records success
        """
        # Import will fail until retry.py is created
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails():
            attempt_count["count"] += 1
            return ["email1", "email2"]

        result = fetch_emails()

        assert result == ["email1", "email2"]
        assert attempt_count["count"] == 1
        assert gmail_circuit_breaker.get_state() == CircuitState.CLOSED
        assert gmail_circuit_breaker.failure_count == 0

    def test_scenario_2_transient_failure_recovers(self):
        """
        Contract #2: Transient Failure Recovers (Retry Succeeds)

        Given: Function fails twice, then succeeds on third attempt
        When: Decorated function is called
        Then:
        - Function executes 3 times total
        - Exponential backoff applied between attempts
        - Success result returned on third attempt
        - Circuit breaker records success (failure count reset)
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}
        wait_times = []

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_flaky():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise socket.timeout("Connection timeout")
            return ["email1"]

        start_time = time.time()
        result = fetch_emails_flaky()
        total_time = time.time() - start_time

        assert result == ["email1"]
        assert attempt_count["count"] == 3
        # Should have waited ~3 seconds total (1s + 2s with jitter)
        assert 2 <= total_time <= 6  # Allow for jitter variance
        assert gmail_circuit_breaker.get_state() == CircuitState.CLOSED
        assert gmail_circuit_breaker.failure_count == 0  # Reset after success

    def test_scenario_3_exhausted_retries_all_fail(self):
        """
        Contract #3: Exhausted Retries (All Attempts Fail)

        Given: Function fails on all 3 attempts
        When: Decorated function is called
        Then:
        - Function executes 3 times (max_attempts)
        - Exponential backoff applied between attempts
        - Original exception re-raised after final attempt
        - Circuit breaker records failures (increments failure_count)
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_always_fails():
            attempt_count["count"] += 1
            raise socket.timeout("Connection timeout")

        with pytest.raises(socket.timeout):
            fetch_emails_always_fails()

        assert attempt_count["count"] == 3
        # Circuit breaker should have recorded 3 failures
        assert gmail_circuit_breaker.failure_count == 3
        assert gmail_circuit_breaker.get_state() == CircuitState.CLOSED  # Not yet opened

    def test_scenario_4_rate_limit_handling_retry_after(self):
        """
        Contract #4: Rate Limit Handling (Respect Retry-After)

        Given: API returns 429 with Retry-After: 2 header
        When: Decorated function is called
        Then:
        - Function executes, raises rate limit error
        - Retry waits 2 seconds (from Retry-After, not backoff)
        - Function retries after wait
        - If succeeds, returns result
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_with_rate_limit():
            attempt_count["count"] += 1
            if attempt_count["count"] == 1:
                raise MockAPIResponseError(429, headers={"Retry-After": "2"})
            return ["email1"]

        start_time = time.time()
        result = fetch_with_rate_limit()
        total_time = time.time() - start_time

        assert result == ["email1"]
        assert attempt_count["count"] == 2
        # Should have waited ~2 seconds (Retry-After value)
        assert 1.8 <= total_time <= 2.5  # Allow some variance

    def test_scenario_5_non_retryable_error_fail_fast(self):
        """
        Contract #5: Non-Retryable Error (Fail Fast)

        Given: Function raises non-retryable exception (401 auth error)
        When: Decorated function is called
        Then:
        - Function executes once
        - Exception raised immediately (no retry)
        - Circuit breaker records failure
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_auth_error():
            attempt_count["count"] += 1
            raise MockHttpError(401, "Unauthorized")

        with pytest.raises(MockHttpError) as exc_info:
            fetch_emails_auth_error()

        assert exc_info.value.status_code == 401
        assert attempt_count["count"] == 1  # No retries
        assert gmail_circuit_breaker.failure_count == 1

    def test_scenario_6_circuit_breaker_open_reject_request(self):
        """
        Contract #6: Circuit Breaker Open (Reject Request)

        Given: Circuit breaker is OPEN (5 consecutive failures)
        When: Decorated function is called
        Then:
        - Function does NOT execute (no HTTP call)
        - CircuitBreakerOpen exception raised immediately
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        function_call_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_tracked():
            function_call_count["count"] += 1
            return ["email1"]

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_always_fails():
            raise socket.timeout("Connection timeout")

        # Trigger circuit breaker to open (5 consecutive failures)
        for _ in range(5):
            try:
                fetch_emails_always_fails()
            except socket.timeout:
                pass

        assert gmail_circuit_breaker.get_state() == CircuitState.OPEN

        # Next request should be rejected
        with pytest.raises(CircuitBreakerOpen):
            fetch_emails_tracked()

        assert function_call_count["count"] == 0  # Function never executed

    def test_scenario_7_exponential_backoff_with_jitter(self):
        """
        Contract #7: Exponential Backoff with Jitter

        Given: Function fails on attempts 1 and 2
        When: Decorated function is called
        Then:
        - Wait times increase exponentially: 2^0, 2^1 (base)
        - Jitter added: random(0, 2) seconds
        - Wait times capped at backoff_max (10s)
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}
        attempt_times = []

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_with_retries():
            attempt_times.append(time.time())
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise socket.timeout("Connection timeout")
            return ["email1"]

        result = fetch_emails_with_retries()

        assert result == ["email1"]
        assert attempt_count["count"] == 3

        # Check wait times between attempts
        if len(attempt_times) >= 2:
            wait_1 = attempt_times[1] - attempt_times[0]
            wait_2 = attempt_times[2] - attempt_times[1]

            # First wait: ~1s (2^0) + jitter (0-2s) = 1-3s
            assert 0.8 <= wait_1 <= 3.5

            # Second wait: ~2s (2^1) + jitter (0-2s) = 2-4s
            assert 1.8 <= wait_2 <= 4.5

    @pytest.mark.asyncio
    async def test_scenario_8_async_function_support(self):
        """
        Contract #8: Async Function Support

        Given: Decorated function is async
        When: Function is awaited
        Then:
        - Retry logic works correctly with async/await
        - Backoff waits use asyncio.sleep() (not time.sleep())
        - Circuit breaker state updates correctly
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        async def async_fetch_emails():
            attempt_count["count"] += 1
            if attempt_count["count"] == 1:
                raise socket.timeout("Connection timeout")
            return ["email1"]

        result = await async_fetch_emails()

        assert result == ["email1"]
        assert attempt_count["count"] == 2

    def test_scenario_9_logging_integration(self):
        """
        Contract #9: Logging Integration

        Given: Function fails and retries
        When: Each retry attempt occurs
        Then:
        - ErrorRecord logged for each failure
        - Log includes: operation, attempt_number, error_type
        - Final failure (after exhausted retries) logged as ERROR severity
        """
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import retry_with_backoff, GMAIL_RETRY_CONFIG

        attempt_count = {"count": 0}

        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails_with_logging():
            attempt_count["count"] += 1
            raise socket.timeout("Connection timeout")

        with patch("src.error_handling.structured_logger.logger") as mock_logger:
            with pytest.raises(socket.timeout):
                fetch_emails_with_logging()

            # Check that logger was called for each retry attempt
            assert mock_logger.warning.call_count >= 2  # At least 2 retries logged
            assert mock_logger.error.call_count >= 1  # Final failure logged


class TestRetryConfigConstants:
    """Test that retry config constants exist and are properly configured."""

    def test_gmail_retry_config_exists(self):
        """Gmail retry config should exist with correct settings."""
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import GMAIL_RETRY_CONFIG

        assert GMAIL_RETRY_CONFIG.max_attempts == 3
        assert GMAIL_RETRY_CONFIG.timeout == 30.0
        assert GMAIL_RETRY_CONFIG.respect_retry_after is True

    def test_gemini_retry_config_exists(self):
        """Gemini retry config should exist with correct settings."""
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import GEMINI_RETRY_CONFIG

        assert GEMINI_RETRY_CONFIG.max_attempts == 3
        assert GEMINI_RETRY_CONFIG.timeout == 60.0
        assert GEMINI_RETRY_CONFIG.respect_retry_after is True

    def test_notion_retry_config_exists(self):
        """Notion retry config should exist with correct settings."""
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import NOTION_RETRY_CONFIG

        assert NOTION_RETRY_CONFIG.max_attempts == 3
        assert NOTION_RETRY_CONFIG.timeout == 30.0
        assert NOTION_RETRY_CONFIG.respect_retry_after is True

    def test_infisical_retry_config_exists(self):
        """Infisical retry config should exist with correct settings."""
        pytest.importorskip("src.error_handling.retry", reason="retry.py not yet implemented")

        from src.error_handling.retry import INFISICAL_RETRY_CONFIG

        assert INFISICAL_RETRY_CONFIG.max_attempts == 2
        assert INFISICAL_RETRY_CONFIG.timeout == 10.0
