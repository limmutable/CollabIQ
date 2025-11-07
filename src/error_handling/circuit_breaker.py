"""Circuit breaker implementation for external API calls."""

from datetime import datetime
from typing import Any, Callable, Optional

from .models import CircuitBreakerState, CircuitState
from .structured_logger import logger


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker open for service: {service_name}")


class CircuitBreaker:
    """
    Circuit breaker implementation with CLOSED → OPEN → HALF_OPEN state machine.

    Prevents cascading failures by stopping requests to failing services after
    a threshold is reached.
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
    ):
        """
        Initialize circuit breaker.

        Args:
            service_name: Name of the service (e.g., "gmail", "gemini")
            failure_threshold: Number of failures before opening (default: 5)
            success_threshold: Number of successes before closing (default: 2)
            timeout: Seconds before attempting HALF_OPEN (default: 60.0)
        """
        self.state_obj = CircuitBreakerState(
            service_name=service_name,
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            open_timestamp=None,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
        )

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func(*args, **kwargs)

        Raises:
            CircuitBreakerOpen: If circuit breaker is open
            Exception: Original exception from func
        """
        if not self.should_allow_request():
            logger.error(
                f"Circuit breaker open for {self.state_obj.service_name}",
                context={
                    "service": self.state_obj.service_name,
                    "failure_count": self.state_obj.failure_count,
                    "state": self.state_obj.state.value,
                },
            )
            raise CircuitBreakerOpen(self.state_obj.service_name)

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def should_allow_request(self) -> bool:
        """
        Check if request should be allowed through circuit breaker.

        Returns:
            True if request should proceed, False otherwise
        """
        return self.state_obj.should_allow_request()

    def record_success(self):
        """Record successful request and update state."""
        old_state = self.state_obj.state
        self.state_obj.record_success()
        new_state = self.state_obj.state

        # Log state transitions
        if old_state != new_state:
            logger.info(
                f"Circuit breaker state transition: {old_state.value} → {new_state.value}",
                context={
                    "service": self.state_obj.service_name,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "success_count": self.state_obj.success_count,
                },
            )

    def record_failure(self):
        """Record failed request and update state."""
        old_state = self.state_obj.state
        self.state_obj.record_failure()
        new_state = self.state_obj.state

        # Log state transitions
        if old_state != new_state:
            logger.warning(
                f"Circuit breaker state transition: {old_state.value} → {new_state.value}",
                context={
                    "service": self.state_obj.service_name,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "failure_count": self.state_obj.failure_count,
                },
            )

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state_obj.state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self.state_obj.failure_count

    @property
    def success_count(self) -> int:
        """Get current success count."""
        return self.state_obj.success_count

    @property
    def last_failure_time(self) -> Optional[datetime]:
        """Get timestamp of last failure."""
        return self.state_obj.last_failure_time

    @property
    def open_timestamp(self) -> Optional[datetime]:
        """Get timestamp when circuit opened."""
        return self.state_obj.open_timestamp


# Global circuit breaker instances for each service

# Gmail, Gemini, Notion (critical services)
gmail_circuit_breaker = CircuitBreaker(
    service_name="gmail", failure_threshold=5, success_threshold=2, timeout=60.0
)

gemini_circuit_breaker = CircuitBreaker(
    service_name="gemini", failure_threshold=5, success_threshold=2, timeout=60.0
)

notion_circuit_breaker = CircuitBreaker(
    service_name="notion", failure_threshold=5, success_threshold=2, timeout=60.0
)

# Infisical (has .env fallback, fail faster)
infisical_circuit_breaker = CircuitBreaker(
    service_name="infisical", failure_threshold=3, success_threshold=2, timeout=30.0
)
