"""Retry decorator with exponential backoff for API calls."""

import asyncio
import functools
import random
import socket
import time
from datetime import datetime, UTC
from typing import Any, Callable, Optional, TypeVar

from .circuit_breaker import (
    CircuitBreakerOpen,
    gemini_circuit_breaker,
    gmail_circuit_breaker,
    infisical_circuit_breaker,
    notion_circuit_breaker,
)
from .error_classifier import ErrorClassifier
from .models import ErrorRecord, ErrorSeverity, RetryConfig
from .structured_logger import logger

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


# Retry configuration constants for each API

GMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=30.0,
    retryable_exceptions={
        socket.timeout,
        ConnectionError,
        TimeoutError,
        OSError,
    },
    respect_retry_after=True,
)

GEMINI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=60.0,
    retryable_exceptions={
        socket.timeout,
        ConnectionError,
        TimeoutError,
    },
    respect_retry_after=True,
)

NOTION_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=30.0,
    retryable_exceptions={
        socket.timeout,
        ConnectionError,
        TimeoutError,
    },
    respect_retry_after=True,
)

INFISICAL_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    backoff_multiplier=1.0,
    backoff_min=1.0,
    backoff_max=10.0,
    jitter_min=0.0,
    jitter_max=2.0,
    timeout=10.0,
    retryable_exceptions={
        socket.timeout,
        ConnectionError,
        TimeoutError,
    },
    respect_retry_after=True,
)


def _get_circuit_breaker_for_function(func: Callable) -> Optional[Any]:
    """
    Determine which circuit breaker to use based on function name/module.

    Args:
        func: The function being decorated

    Returns:
        Circuit breaker instance or None
    """
    func_name = func.__name__.lower()
    module_name = func.__module__.lower() if hasattr(func, "__module__") else ""

    # Detect service based on function or module name
    if "gmail" in func_name or "gmail" in module_name:
        return gmail_circuit_breaker
    elif "gemini" in func_name or "gemini" in module_name:
        return gemini_circuit_breaker
    elif "notion" in func_name or "notion" in module_name:
        return notion_circuit_breaker
    elif "infisical" in func_name or "infisical" in module_name:
        return infisical_circuit_breaker

    # Default to None (no circuit breaker)
    return None


def _calculate_backoff_time(
    attempt: int, config: RetryConfig, exception: Optional[Exception] = None
) -> float:
    """
    Calculate backoff time for retry attempt.

    Args:
        attempt: Current attempt number (1-indexed)
        config: Retry configuration
        exception: The exception that triggered retry (for rate limit detection)

    Returns:
        Backoff time in seconds
    """
    # Check for Retry-After header first
    if exception and config.respect_retry_after:
        retry_after = ErrorClassifier.extract_retry_after(exception)
        if retry_after:
            return retry_after

    # Use exponential backoff with jitter
    # Formula: min(max, base * 2^(attempt-1)) + random(jitter_min, jitter_max)
    base_wait = config.backoff_min * (2 ** (attempt - 1))
    base_wait = min(base_wait, config.backoff_max)
    jitter = random.uniform(config.jitter_min, config.jitter_max)

    return base_wait + jitter


def retry_with_backoff(
    config: RetryConfig, circuit_breaker: Optional[Any] = None
) -> Callable[[F], F]:
    """
    Decorator that adds retry logic with exponential backoff to a function.

    Features:
    - Exponential backoff with jitter
    - Respects Retry-After headers for rate limits
    - Integrates with circuit breaker pattern
    - Logs retry attempts and failures
    - Supports both sync and async functions

    Args:
        config: Retry configuration
        circuit_breaker: Optional circuit breaker instance (auto-detected if None)

    Returns:
        Decorated function with retry behavior

    Raises:
        Original exception after max retry attempts exhausted
        CircuitBreakerOpen if circuit breaker is open

    Example:
        @retry_with_backoff(GMAIL_RETRY_CONFIG)
        def fetch_emails():
            # Will retry on transient failures
            return gmail_api.fetch()
    """

    def decorator(func: F) -> F:
        # Auto-detect circuit breaker if not provided
        if circuit_breaker:
            cb = circuit_breaker
        else:
            # Try to infer from config
            if config is GMAIL_RETRY_CONFIG:
                cb = gmail_circuit_breaker
            elif config is GEMINI_RETRY_CONFIG:
                cb = gemini_circuit_breaker
            elif config is NOTION_RETRY_CONFIG:
                cb = notion_circuit_breaker
            elif config is INFISICAL_RETRY_CONFIG:
                cb = infisical_circuit_breaker
            else:
                # Fall back to function name detection
                cb = _get_circuit_breaker_for_function(func)

        # Determine if function is async
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Check circuit breaker before attempting
                if cb and not cb.should_allow_request():
                    logger.error(
                        f"Circuit breaker open for {cb.state_obj.service_name}",
                        context={
                            "service": cb.state_obj.service_name,
                            "function": func.__name__,
                            "state": cb.state_obj.state.value,
                        },
                    )
                    raise CircuitBreakerOpen(cb.state_obj.service_name)

                last_exception = None

                for attempt in range(1, config.max_attempts + 1):
                    try:
                        result = await func(*args, **kwargs)

                        # Success! Record in circuit breaker
                        if cb:
                            cb.record_success()

                        return result

                    except Exception as e:
                        last_exception = e

                        # Classify the error
                        category = ErrorClassifier.classify(e)
                        is_retryable = ErrorClassifier.is_retryable(e)

                        # Log the attempt
                        severity = (
                            ErrorSeverity.WARNING
                            if attempt < config.max_attempts and is_retryable
                            else ErrorSeverity.ERROR
                        )

                        error_record = ErrorRecord(
                            timestamp=datetime.now(UTC),
                            severity=severity,
                            category=category,
                            message=f"Retry attempt {attempt}/{config.max_attempts} failed: {str(e)}",
                            error_type=type(e).__name__,
                            stack_trace=None,
                            context={
                                "function": func.__name__,
                                "attempt_number": attempt,
                                "max_attempts": config.max_attempts,
                            },
                            http_status=ErrorClassifier.get_http_status(e),
                            retry_count=attempt,
                        )

                        if severity == ErrorSeverity.WARNING:
                            logger.warning(
                                error_record.message,
                                context=error_record.context,
                            )
                        else:
                            logger.error(
                                error_record.message, context=error_record.context
                            )

                        # Record failure in circuit breaker for this attempt
                        # (each API call counts as a failure for circuit breaker tracking)
                        if cb:
                            cb.record_failure()

                        # If not retryable or last attempt, fail now
                        if not is_retryable or attempt >= config.max_attempts:
                            raise

                        # Calculate backoff time and wait
                        backoff_time = _calculate_backoff_time(attempt, config, e)
                        await asyncio.sleep(backoff_time)

                # Should never reach here, but just in case
                if last_exception:
                    raise last_exception

            return async_wrapper  # type: ignore

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Check circuit breaker before attempting
                if cb and not cb.should_allow_request():
                    logger.error(
                        f"Circuit breaker open for {cb.state_obj.service_name}",
                        context={
                            "service": cb.state_obj.service_name,
                            "function": func.__name__,
                            "state": cb.state_obj.state.value,
                        },
                    )
                    raise CircuitBreakerOpen(cb.state_obj.service_name)

                last_exception = None

                for attempt in range(1, config.max_attempts + 1):
                    try:
                        result = func(*args, **kwargs)

                        # Success! Record in circuit breaker
                        if cb:
                            cb.record_success()

                        return result

                    except Exception as e:
                        last_exception = e

                        # Classify the error
                        category = ErrorClassifier.classify(e)
                        is_retryable = ErrorClassifier.is_retryable(e)

                        # Log the attempt
                        severity = (
                            ErrorSeverity.WARNING
                            if attempt < config.max_attempts and is_retryable
                            else ErrorSeverity.ERROR
                        )

                        error_record = ErrorRecord(
                            timestamp=datetime.now(UTC),
                            severity=severity,
                            category=category,
                            message=f"Retry attempt {attempt}/{config.max_attempts} failed: {str(e)}",
                            error_type=type(e).__name__,
                            stack_trace=None,
                            context={
                                "function": func.__name__,
                                "attempt_number": attempt,
                                "max_attempts": config.max_attempts,
                            },
                            http_status=ErrorClassifier.get_http_status(e),
                            retry_count=attempt,
                        )

                        if severity == ErrorSeverity.WARNING:
                            logger.warning(
                                error_record.message,
                                context=error_record.context,
                            )
                        else:
                            logger.error(
                                error_record.message, context=error_record.context
                            )

                        # Record failure in circuit breaker for this attempt
                        # (each API call counts as a failure for circuit breaker tracking)
                        if cb:
                            cb.record_failure()

                        # If not retryable or last attempt, fail now
                        if not is_retryable or attempt >= config.max_attempts:
                            raise

                        # Calculate backoff time and wait
                        backoff_time = _calculate_backoff_time(attempt, config, e)
                        time.sleep(backoff_time)

                # Should never reach here, but just in case
                if last_exception:
                    raise last_exception

            return sync_wrapper  # type: ignore

    return decorator
