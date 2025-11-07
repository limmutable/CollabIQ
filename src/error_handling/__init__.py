"""Error handling and retry logic for CollabIQ."""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    gemini_circuit_breaker,
    gmail_circuit_breaker,
    infisical_circuit_breaker,
    notion_circuit_breaker,
)
from .error_classifier import ErrorClassifier
from .models import (
    CircuitBreakerState,
    CircuitState,
    ErrorCategory,
    ErrorRecord,
    ErrorSeverity,
    RetryConfig,
)
from .retry import (
    GEMINI_RETRY_CONFIG,
    GMAIL_RETRY_CONFIG,
    INFISICAL_RETRY_CONFIG,
    NOTION_RETRY_CONFIG,
    retry_with_backoff,
)
from .structured_logger import StructuredLogger, logger

__all__ = [
    # Models
    "ErrorRecord",
    "ErrorSeverity",
    "ErrorCategory",
    "RetryConfig",
    "CircuitBreakerState",
    "CircuitState",
    # Error Classification
    "ErrorClassifier",
    # Logging
    "StructuredLogger",
    "logger",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "gmail_circuit_breaker",
    "gemini_circuit_breaker",
    "notion_circuit_breaker",
    "infisical_circuit_breaker",
    # Retry Decorator
    "retry_with_backoff",
    "GMAIL_RETRY_CONFIG",
    "GEMINI_RETRY_CONFIG",
    "NOTION_RETRY_CONFIG",
    "INFISICAL_RETRY_CONFIG",
]
