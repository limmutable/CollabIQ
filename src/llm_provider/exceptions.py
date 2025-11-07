"""LLM Provider exceptions for entity extraction.

This module defines the exception hierarchy for all LLM-related errors,
including API errors, rate limits, timeouts, and authentication failures.

Exception Hierarchy:
    Exception
    └── LLMAPIError (base exception for all LLM errors)
        ├── LLMRateLimitError (429 - rate limit exceeded)
        ├── LLMTimeoutError (request timeout)
        ├── LLMAuthenticationError (401/403 - auth failed)
        └── LLMValidationError (malformed API response)
"""

from typing import Optional


class LLMAPIError(Exception):
    """Base exception for all LLM API errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if applicable)
        original_error: Original exception that was caught
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize LLMAPIError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (if applicable)
            original_error: Original exception that was caught
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.original_error = original_error

    def __str__(self) -> str:
        """Return string representation of the error."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)


class LLMRateLimitError(LLMAPIError):
    """Rate limit exceeded error (HTTP 429).

    Raised when the LLM API returns a rate limit error.
    Caller should implement exponential backoff retry.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        original_error: Optional[Exception] = None,
    ):
        """Initialize LLMRateLimitError.

        Args:
            message: Human-readable error message
            original_error: Original exception that was caught
        """
        super().__init__(
            message=message, status_code=429, original_error=original_error
        )


class LLMTimeoutError(LLMAPIError):
    """Request timeout error.

    Raised when the LLM API doesn't respond within the timeout period.
    Caller may retry with increased timeout.
    """

    def __init__(
        self,
        message: str = "Request timeout",
        timeout_seconds: Optional[int] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize LLMTimeoutError.

        Args:
            message: Human-readable error message
            timeout_seconds: Timeout value that was exceeded
            original_error: Original exception that was caught
        """
        super().__init__(
            message=message, status_code=408, original_error=original_error
        )
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.timeout_seconds:
            return f"{self.message} (timeout: {self.timeout_seconds}s)"
        return self.message


class LLMAuthenticationError(LLMAPIError):
    """Authentication failed error (HTTP 401/403).

    Raised when the LLM API returns an authentication or authorization error.
    No retry should be attempted - requires API key fix.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        original_error: Optional[Exception] = None,
    ):
        """Initialize LLMAuthenticationError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (401 or 403)
            original_error: Original exception that was caught
        """
        super().__init__(
            message=message, status_code=status_code, original_error=original_error
        )


class LLMValidationError(LLMAPIError):
    """Malformed API response error.

    Raised when the LLM API returns a response that doesn't match
    the expected schema or format.
    """

    def __init__(
        self,
        message: str = "Malformed API response",
        original_error: Optional[Exception] = None,
    ):
        """Initialize LLMValidationError.

        Args:
            message: Human-readable error message
            original_error: Original exception that was caught
        """
        super().__init__(
            message=message, status_code=400, original_error=original_error
        )
