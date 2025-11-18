"""Orchestration-specific exceptions.

This module defines exceptions specific to multi-provider orchestration,
extending the base LLM provider exceptions.
"""

from llm_provider.exceptions import LLMAPIError


class AllProvidersFailedError(LLMAPIError):
    """All enabled providers failed to extract entities.

    Raised when all providers in the orchestration strategy failed
    to successfully extract entities from the email text.
    """

    def __init__(self, message: str = "All providers failed"):
        """Initialize AllProvidersFailedError.

        Args:
            message: Human-readable error message
        """
        super().__init__(message=message, status_code=503)


class NoHealthyProvidersError(LLMAPIError):
    """No healthy providers available.

    Raised when all providers are marked as unhealthy and cannot
    be used for extraction.
    """

    def __init__(self, message: str = "No healthy providers available"):
        """Initialize NoHealthyProvidersError.

        Args:
            message: Human-readable error message
        """
        super().__init__(message=message, status_code=503)


class OrchestrationTimeoutError(LLMAPIError):
    """Overall orchestration timeout exceeded.

    Raised when the orchestration operation takes longer than
    the configured timeout.
    """

    def __init__(
        self,
        message: str = "Orchestration timeout",
        timeout_seconds: float | None = None,
    ):
        """Initialize OrchestrationTimeoutError.

        Args:
            message: Human-readable error message
            timeout_seconds: Timeout value that was exceeded
        """
        super().__init__(message=message, status_code=408)
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.timeout_seconds:
            return f"{self.message} (timeout: {self.timeout_seconds}s)"
        return self.message


class InvalidStrategyError(LLMAPIError):
    """Unknown orchestration strategy specified.

    Raised when an invalid or unknown strategy type is specified.
    """

    def __init__(
        self, message: str = "Invalid strategy", strategy_name: str | None = None
    ):
        """Initialize InvalidStrategyError.

        Args:
            message: Human-readable error message
            strategy_name: The invalid strategy name that was provided
        """
        super().__init__(message=message, status_code=400)
        self.strategy_name = strategy_name

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.strategy_name:
            return f"{self.message}: '{self.strategy_name}'"
        return self.message


class InvalidProviderError(LLMAPIError):
    """Unknown or unconfigured provider specified.

    Raised when an invalid or unconfigured provider name is specified.
    """

    def __init__(
        self, message: str = "Invalid provider", provider_name: str | None = None
    ):
        """Initialize InvalidProviderError.

        Args:
            message: Human-readable error message
            provider_name: The invalid provider name that was provided
        """
        super().__init__(message=message, status_code=400)
        self.provider_name = provider_name

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.provider_name:
            return f"{self.message}: '{self.provider_name}'"
        return self.message
