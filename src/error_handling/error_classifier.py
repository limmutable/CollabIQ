"""Error classification system for retry logic."""

import socket
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

try:
    from pydantic import ValidationError as PydanticValidationError
except ImportError:
    PydanticValidationError = None

from .models import ErrorCategory


class ErrorClassifier:
    """Classifies exceptions into TRANSIENT, PERMANENT, or CRITICAL categories."""

    # Transient exceptions (should be retried)
    TRANSIENT_EXCEPTIONS = {
        socket.timeout,
        ConnectionError,
        TimeoutError,
        OSError,
    }

    # Permanent exceptions (should not be retried)
    PERMANENT_EXCEPTIONS = set()
    if PydanticValidationError:
        PERMANENT_EXCEPTIONS.add(PydanticValidationError)

    # Critical exceptions (authentication/authorization failures)
    CRITICAL_EXCEPTIONS = set()  # Will add google.auth.exceptions in Phase 3

    @staticmethod
    def classify(exception: Exception) -> ErrorCategory:
        """
        Classify exception into TRANSIENT, PERMANENT, or CRITICAL.

        Args:
            exception: The exception to classify

        Returns:
            ErrorCategory enum value
        """
        # Check exception type first
        exception_type = type(exception)

        if exception_type in ErrorClassifier.TRANSIENT_EXCEPTIONS:
            return ErrorCategory.TRANSIENT

        if exception_type in ErrorClassifier.CRITICAL_EXCEPTIONS:
            return ErrorCategory.CRITICAL

        if exception_type in ErrorClassifier.PERMANENT_EXCEPTIONS:
            return ErrorCategory.PERMANENT

        # Check HTTP status if available
        http_status = ErrorClassifier.get_http_status(exception)
        if http_status:
            if http_status == 401:
                return ErrorCategory.CRITICAL
            elif http_status == 429:
                return ErrorCategory.TRANSIENT
            elif http_status in {400, 403, 404, 501}:
                return ErrorCategory.PERMANENT
            elif 500 <= http_status <= 504:
                return ErrorCategory.TRANSIENT

        # Check for API-specific exceptions by name
        exception_name = type(exception).__name__

        # Google API exceptions
        if exception_name in {"ResourceExhausted", "DeadlineExceeded"}:
            return ErrorCategory.TRANSIENT
        elif exception_name == "Unauthenticated":
            return ErrorCategory.CRITICAL
        elif exception_name in {"PermissionDenied", "InvalidArgument"}:
            return ErrorCategory.PERMANENT

        # Notion API exceptions
        if exception_name == "APIResponseError":
            # Check error code in exception
            error_code = getattr(exception, "code", None)
            if error_code == "unauthorized":
                return ErrorCategory.CRITICAL
            elif error_code == "rate_limited":
                return ErrorCategory.TRANSIENT
            elif error_code in {"object_not_found", "restricted_resource"}:
                return ErrorCategory.PERMANENT

        # Fallback to PERMANENT (safer default - avoids infinite retries)
        return ErrorCategory.PERMANENT

    @staticmethod
    def is_retryable(exception: Exception) -> bool:
        """
        Check if exception should be retried.

        Args:
            exception: The exception to check

        Returns:
            True if should retry, False otherwise
        """
        category = ErrorClassifier.classify(exception)
        return category == ErrorCategory.TRANSIENT

    @staticmethod
    def extract_retry_after(exception: Exception) -> Optional[float]:
        """
        Extract Retry-After header value (in seconds) if present.

        Args:
            exception: The exception to extract from

        Returns:
            Seconds to wait before retrying, or None if not available
        """
        # Check if exception has response attribute (HTTP errors)
        if not hasattr(exception, "response"):
            return None

        response = exception.response
        if not hasattr(response, "headers"):
            return None

        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return None

        # Try parsing as seconds (integer)
        try:
            return float(retry_after)
        except ValueError:
            pass

        # Try parsing as HTTP date
        try:
            retry_datetime = parsedate_to_datetime(retry_after)
            now = datetime.utcnow()
            # Make now offset-aware if retry_datetime is offset-aware
            if retry_datetime.tzinfo:
                from datetime import timezone

                now = now.replace(tzinfo=timezone.utc)
            delta = (retry_datetime - now).total_seconds()
            return max(0, delta)  # Don't return negative values
        except (ValueError, TypeError):
            pass

        return None

    @staticmethod
    def get_http_status(exception: Exception) -> Optional[int]:
        """
        Extract HTTP status code from exception if available.

        Args:
            exception: The exception to extract from

        Returns:
            HTTP status code or None
        """
        # Check for status_code attribute (common in HTTP libraries)
        if hasattr(exception, "status_code"):
            return exception.status_code

        # Check for resp attribute (Google API)
        if hasattr(exception, "resp"):
            resp = exception.resp
            if isinstance(resp, dict) and "status" in resp:
                try:
                    return int(resp["status"])
                except (ValueError, TypeError):
                    pass

        # Check for response.status_code (requests library)
        if hasattr(exception, "response"):
            response = exception.response
            if hasattr(response, "status_code"):
                return response.status_code

        return None
