"""Contract tests for error classifier.

Tests all 12 scenarios from contracts/error_classifier.md:
1. Classify Network Timeout (TRANSIENT)
2. Classify Rate Limit (TRANSIENT with Retry-After)
3. Classify Authentication Error (CRITICAL)
4. Classify Permission Error (PERMANENT)
5. Classify Server Error (TRANSIENT)
6. Classify Resource Not Found (PERMANENT)
7. Classify Validation Error (PERMANENT)
8. Classify Gemini Resource Exhausted (TRANSIENT)
9. Classify Gemini Unauthenticated (CRITICAL)
10. Parse Retry-After as Seconds
11. Parse Retry-After as HTTP Date
12. Fallback Classification (Unknown Exception)
"""

import socket
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.error_handling.error_classifier import ErrorClassifier
from src.error_handling.models import ErrorCategory


# Mock exception classes for testing
class MockHttpError(Exception):
    """Mock HTTP error for Gmail API."""

    def __init__(self, status_code: int, message: str = "Mock error"):
        self.resp = {"status": str(status_code)}
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class MockAPIResponseError(Exception):
    """Mock Notion API error."""

    def __init__(self, status_code: int, error_code: str = "", headers: dict = None):
        self.status_code = status_code
        self.code = error_code
        self.response = Mock()
        self.response.headers = headers or {}
        super().__init__(f"API Error: {status_code}")


class MockResourceExhausted(Exception):
    """Mock Gemini ResourceExhausted error."""

    pass


class MockDeadlineExceeded(Exception):
    """Mock Gemini DeadlineExceeded error."""

    pass


class MockUnauthenticated(Exception):
    """Mock Gemini Unauthenticated error."""

    pass


class MockPermissionDenied(Exception):
    """Mock Gemini PermissionDenied error."""

    pass


class MockInvalidArgument(Exception):
    """Mock Gemini InvalidArgument error."""

    pass


class TestErrorClassifierContract:
    """Contract tests for ErrorClassifier."""

    def test_scenario_1_classify_network_timeout_transient(self):
        """
        Contract #1: Classify Network Timeout (TRANSIENT)

        Given: Exception is socket.timeout or ConnectionError
        When: classify() is called
        Then:
        - Returns ErrorCategory.TRANSIENT
        - is_retryable() returns True
        """
        classifier = ErrorClassifier()

        timeout_error = socket.timeout("Connection timed out")
        assert classifier.classify(timeout_error) == ErrorCategory.TRANSIENT
        assert classifier.is_retryable(timeout_error) is True

        connection_error = ConnectionError("Connection refused")
        assert classifier.classify(connection_error) == ErrorCategory.TRANSIENT
        assert classifier.is_retryable(connection_error) is True

        timeout_error_builtin = TimeoutError("Timeout")
        assert classifier.classify(timeout_error_builtin) == ErrorCategory.TRANSIENT
        assert classifier.is_retryable(timeout_error_builtin) is True

    def test_scenario_2_classify_rate_limit_transient_with_retry_after(self):
        """
        Contract #2: Classify Rate Limit (TRANSIENT with Retry-After)

        Given: Exception is APIResponseError with 429 status and Retry-After header
        When: classify() and extract_retry_after() are called
        Then:
        - Returns ErrorCategory.TRANSIENT
        - is_retryable() returns True
        - extract_retry_after() returns seconds from header
        """
        classifier = ErrorClassifier()

        rate_limit_error = MockAPIResponseError(
            429, error_code="rate_limited", headers={"Retry-After": "120"}
        )

        assert classifier.classify(rate_limit_error) == ErrorCategory.TRANSIENT
        assert classifier.is_retryable(rate_limit_error) is True
        assert classifier.extract_retry_after(rate_limit_error) == 120.0

    def test_scenario_3_classify_authentication_error_critical(self):
        """
        Contract #3: Classify Authentication Error (CRITICAL)

        Given: Exception is HttpError with 401 status code
        When: classify() is called
        Then:
        - Returns ErrorCategory.CRITICAL
        - is_retryable() returns False
        """
        classifier = ErrorClassifier()

        auth_error = MockHttpError(401, "Unauthorized")

        assert classifier.classify(auth_error) == ErrorCategory.CRITICAL
        assert classifier.is_retryable(auth_error) is False
        assert classifier.get_http_status(auth_error) == 401

    def test_scenario_4_classify_permission_error_permanent(self):
        """
        Contract #4: Classify Permission Error (PERMANENT)

        Given: Exception is HttpError with 403 status code
        When: classify() is called
        Then:
        - Returns ErrorCategory.PERMANENT
        - is_retryable() returns False
        """
        classifier = ErrorClassifier()

        permission_error = MockHttpError(403, "Forbidden")

        assert classifier.classify(permission_error) == ErrorCategory.PERMANENT
        assert classifier.is_retryable(permission_error) is False

    def test_scenario_5_classify_server_error_transient(self):
        """
        Contract #5: Classify Server Error (TRANSIENT)

        Given: Exception is HttpError with 503 status code
        When: classify() is called
        Then:
        - Returns ErrorCategory.TRANSIENT
        - is_retryable() returns True
        """
        classifier = ErrorClassifier()

        server_error = MockHttpError(503, "Service Unavailable")

        assert classifier.classify(server_error) == ErrorCategory.TRANSIENT
        assert classifier.is_retryable(server_error) is True

        # Test all 5xx errors
        for status_code in [500, 501, 502, 503, 504]:
            error = MockHttpError(status_code, "Server Error")
            assert classifier.classify(error) == ErrorCategory.TRANSIENT

    def test_scenario_6_classify_resource_not_found_permanent(self):
        """
        Contract #6: Classify Resource Not Found (PERMANENT)

        Given: Exception is HttpError with 404 status code
        When: classify() is called
        Then:
        - Returns ErrorCategory.PERMANENT
        - is_retryable() returns False
        """
        classifier = ErrorClassifier()

        not_found_error = MockHttpError(404, "Not Found")

        assert classifier.classify(not_found_error) == ErrorCategory.PERMANENT
        assert classifier.is_retryable(not_found_error) is False

    def test_scenario_7_classify_validation_error_permanent(self):
        """
        Contract #7: Classify Validation Error (PERMANENT)

        Given: Exception is ValidationError from Pydantic
        When: classify() is called
        Then:
        - Returns ErrorCategory.PERMANENT
        - is_retryable() returns False

        Note: ValidationError will be added to PERMANENT_EXCEPTIONS in Phase 4 (US2)
        For now, test the fallback classification behavior
        """
        classifier = ErrorClassifier()

        # Create a mock validation error
        class MockValidationError(Exception):
            pass

        validation_error = MockValidationError("field required")

        # Should return PERMANENT (fallback classification)
        assert classifier.classify(validation_error) == ErrorCategory.PERMANENT
        assert classifier.is_retryable(validation_error) is False

    def test_scenario_8_classify_gemini_resource_exhausted_transient(self):
        """
        Contract #8: Classify Gemini Resource Exhausted (TRANSIENT)

        Given: Exception is google.api_core.exceptions.ResourceExhausted (429)
        When: classify() is called
        Then:
        - Returns ErrorCategory.TRANSIENT
        - is_retryable() returns True
        """
        classifier = ErrorClassifier()

        # Mock ResourceExhausted exception (classified by name)
        quota_error = MockResourceExhausted("Quota exceeded")

        assert classifier.classify(quota_error) == ErrorCategory.TRANSIENT
        assert classifier.is_retryable(quota_error) is True

    def test_scenario_9_classify_gemini_unauthenticated_critical(self):
        """
        Contract #9: Classify Gemini Unauthenticated (CRITICAL)

        Given: Exception is google.api_core.exceptions.Unauthenticated (401)
        When: classify() is called
        Then:
        - Returns ErrorCategory.CRITICAL
        - is_retryable() returns False
        """
        classifier = ErrorClassifier()

        # Mock Unauthenticated exception (classified by name)
        unauth_error = MockUnauthenticated("Invalid API key")

        assert classifier.classify(unauth_error) == ErrorCategory.CRITICAL
        assert classifier.is_retryable(unauth_error) is False

    def test_scenario_10_parse_retry_after_as_seconds(self):
        """
        Contract #10: Parse Retry-After as Seconds

        Given: Exception has Retry-After: 120 header (seconds format)
        When: extract_retry_after() is called
        Then:
        - Returns 120.0 (float seconds)
        """
        classifier = ErrorClassifier()

        rate_limit_error = MockAPIResponseError(
            429, error_code="rate_limited", headers={"Retry-After": "120"}
        )

        assert classifier.extract_retry_after(rate_limit_error) == 120.0

    def test_scenario_11_parse_retry_after_as_http_date(self):
        """
        Contract #11: Parse Retry-After as HTTP Date

        Given: Exception has Retry-After header in HTTP date format
        When: extract_retry_after() is called
        Then:
        - Parses date, calculates seconds from now
        - Returns seconds as float
        """
        classifier = ErrorClassifier()

        # Create future time (5 minutes from now)
        future_time = datetime.utcnow() + timedelta(minutes=5)
        http_date = future_time.strftime("%a, %d %b %Y %H:%M:%S GMT")

        rate_limit_error = MockAPIResponseError(
            429, error_code="rate_limited", headers={"Retry-After": http_date}
        )

        retry_seconds = classifier.extract_retry_after(rate_limit_error)

        # Should be approximately 5 minutes (300 seconds)
        assert retry_seconds is not None
        assert 295 <= retry_seconds <= 305  # Allow some timing variance

    def test_scenario_12_fallback_classification_unknown_exception(self):
        """
        Contract #12: Fallback Classification (Unknown Exception)

        Given: Exception is unknown type (e.g., KeyError)
        When: classify() is called
        Then:
        - Returns ErrorCategory.PERMANENT (safer default)
        - is_retryable() returns False
        """
        classifier = ErrorClassifier()

        unknown_error = KeyError("missing_key")

        assert classifier.classify(unknown_error) == ErrorCategory.PERMANENT
        assert classifier.is_retryable(unknown_error) is False


class TestErrorClassifierAPIMappings:
    """Test API-specific exception mappings."""

    def test_gmail_api_exceptions(self):
        """Test Gmail API exception mappings."""
        classifier = ErrorClassifier()

        # 401 → CRITICAL
        assert (
            classifier.classify(MockHttpError(401, "Unauthorized"))
            == ErrorCategory.CRITICAL
        )

        # 403 → PERMANENT
        assert (
            classifier.classify(MockHttpError(403, "Forbidden"))
            == ErrorCategory.PERMANENT
        )

        # 404 → PERMANENT
        assert (
            classifier.classify(MockHttpError(404, "Not Found"))
            == ErrorCategory.PERMANENT
        )

        # 429 → TRANSIENT
        assert (
            classifier.classify(MockHttpError(429, "Rate Limited"))
            == ErrorCategory.TRANSIENT
        )

        # 5xx → TRANSIENT
        for status in [500, 502, 503, 504]:
            assert (
                classifier.classify(MockHttpError(status, "Server Error"))
                == ErrorCategory.TRANSIENT
            )

        # socket.timeout → TRANSIENT
        assert classifier.classify(socket.timeout()) == ErrorCategory.TRANSIENT

    def test_gemini_api_exceptions(self):
        """Test Gemini API exception mappings."""
        classifier = ErrorClassifier()

        # ResourceExhausted → TRANSIENT
        assert classifier.classify(MockResourceExhausted()) == ErrorCategory.TRANSIENT

        # DeadlineExceeded → TRANSIENT
        assert classifier.classify(MockDeadlineExceeded()) == ErrorCategory.TRANSIENT

        # Unauthenticated → CRITICAL
        assert classifier.classify(MockUnauthenticated()) == ErrorCategory.CRITICAL

        # PermissionDenied → PERMANENT
        assert classifier.classify(MockPermissionDenied()) == ErrorCategory.PERMANENT

        # InvalidArgument → PERMANENT
        assert classifier.classify(MockInvalidArgument()) == ErrorCategory.PERMANENT

    def test_notion_api_exceptions(self):
        """Test Notion API exception mappings."""
        classifier = ErrorClassifier()

        # unauthorized → CRITICAL
        unauthorized = MockAPIResponseError(401, error_code="unauthorized")
        assert classifier.classify(unauthorized) == ErrorCategory.CRITICAL

        # rate_limited → TRANSIENT
        rate_limited = MockAPIResponseError(429, error_code="rate_limited")
        assert classifier.classify(rate_limited) == ErrorCategory.TRANSIENT

        # object_not_found → PERMANENT
        not_found = MockAPIResponseError(404, error_code="object_not_found")
        assert classifier.classify(not_found) == ErrorCategory.PERMANENT

        # restricted_resource → PERMANENT
        restricted = MockAPIResponseError(403, error_code="restricted_resource")
        assert classifier.classify(restricted) == ErrorCategory.PERMANENT

        # 5xx → TRANSIENT
        server_error = MockAPIResponseError(503, error_code="service_unavailable")
        assert classifier.classify(server_error) == ErrorCategory.TRANSIENT

    def test_infisical_api_exceptions(self):
        """Test Infisical API exception mappings."""
        classifier = ErrorClassifier()

        # Timeout → TRANSIENT
        assert classifier.classify(socket.timeout()) == ErrorCategory.TRANSIENT

        # ConnectionError → TRANSIENT
        assert classifier.classify(ConnectionError()) == ErrorCategory.TRANSIENT

        # 401 → CRITICAL
        assert (
            classifier.classify(MockHttpError(401, "Unauthorized"))
            == ErrorCategory.CRITICAL
        )


class TestErrorClassifierHelperMethods:
    """Test helper methods of ErrorClassifier."""

    def test_get_http_status_from_status_code_attribute(self):
        """Test extracting status code from status_code attribute."""
        classifier = ErrorClassifier()

        error = MockHttpError(404, "Not Found")
        assert classifier.get_http_status(error) == 404

    def test_get_http_status_from_resp_attribute(self):
        """Test extracting status code from resp dict (Google API format)."""
        classifier = ErrorClassifier()

        class GoogleAPIError(Exception):
            def __init__(self, status):
                self.resp = {"status": str(status)}

        error = GoogleAPIError(503)
        assert classifier.get_http_status(error) == 503

    def test_get_http_status_from_response_attribute(self):
        """Test extracting status code from response.status_code (requests format)."""
        classifier = ErrorClassifier()

        class RequestsError(Exception):
            def __init__(self, status_code):
                self.response = Mock()
                self.response.status_code = status_code

        error = RequestsError(429)
        assert classifier.get_http_status(error) == 429

    def test_get_http_status_returns_none_for_no_status(self):
        """Test that get_http_status returns None when no status is available."""
        classifier = ErrorClassifier()

        error = ValueError("Some error")
        assert classifier.get_http_status(error) is None

    def test_extract_retry_after_returns_none_when_not_available(self):
        """Test that extract_retry_after returns None when header not present."""
        classifier = ErrorClassifier()

        # Exception without response attribute
        error1 = socket.timeout()
        assert classifier.extract_retry_after(error1) is None

        # Exception with response but no Retry-After header
        error2 = MockAPIResponseError(503, headers={})
        assert classifier.extract_retry_after(error2) is None

        # Exception with invalid Retry-After format
        error3 = MockAPIResponseError(429, headers={"Retry-After": "invalid"})
        assert classifier.extract_retry_after(error3) is None


class TestErrorClassifierPerformance:
    """Test performance requirements for ErrorClassifier."""

    def test_classification_performance(self):
        """Test that classification takes < 1ms (SC-008 requirement)."""
        import time

        classifier = ErrorClassifier()
        error = socket.timeout()

        start = time.perf_counter()
        for _ in range(1000):
            classifier.classify(error)
        elapsed = time.perf_counter() - start

        # 1000 classifications should take < 1ms each (< 1s total)
        assert elapsed < 1.0

        # Average per classification should be < 1ms
        avg_per_call = elapsed / 1000
        assert avg_per_call < 0.001
