"""Data models for error handling and retry logic."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ErrorSeverity(Enum):
    """Error severity levels for logging."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error classification categories."""

    TRANSIENT = "TRANSIENT"  # Network timeouts, 5xx errors, rate limits
    PERMANENT = "PERMANENT"  # 4xx errors (except 429), validation errors
    CRITICAL = "CRITICAL"  # Auth failures, token expiration


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation (requests pass through)
    OPEN = "OPEN"  # Fail-fast mode (reject all requests)
    HALF_OPEN = "HALF_OPEN"  # Testing recovery (allow test request)


@dataclass
class ErrorRecord:
    """Structured error log entry with contextual information."""

    # Core fields
    timestamp: datetime  # ISO 8601 format
    severity: ErrorSeverity  # Log level
    category: ErrorCategory  # Error classification
    message: str  # Human-readable error message

    # Error details
    error_type: str  # Exception class name (e.g., "socket.timeout")
    stack_trace: Optional[str]  # Full stack trace for debugging

    # Context
    context: Dict[str, Any]  # Email ID, operation type, retry count

    # Optional API-specific fields
    http_status: Optional[int] = None  # HTTP status code if applicable
    retry_count: int = 0  # Number of retry attempts made

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "http_status": self.http_status,
            "retry_count": self.retry_count,
        }


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""

    # Retry limits
    max_attempts: int  # Maximum retry attempts (default: 3)

    # Backoff configuration
    backoff_multiplier: float  # Exponential multiplier (default: 1.0)
    backoff_min: float  # Minimum wait time in seconds (default: 1.0)
    backoff_max: float  # Maximum wait time in seconds (default: 10.0)

    # Jitter
    jitter_min: float  # Minimum jitter in seconds (default: 0.0)
    jitter_max: float  # Maximum jitter in seconds (default: 2.0)

    # Timeout
    timeout: float  # Request timeout in seconds (default: 30.0)

    # Retryable exceptions
    retryable_exceptions: set = field(default_factory=set)  # Exception types to retry

    # API-specific
    respect_retry_after: bool = True  # Honor Retry-After headers (default: True)


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker pattern."""

    # Service identifier
    service_name: str  # e.g., "gmail", "gemini", "notion", "infisical"

    # Current state
    state: CircuitState  # CLOSED, OPEN, HALF_OPEN

    # Failure tracking
    failure_count: int  # Consecutive failures in CLOSED state
    success_count: int  # Consecutive successes in HALF_OPEN state

    # Timestamps
    last_failure_time: Optional[datetime]  # Last failure timestamp
    open_timestamp: Optional[datetime]  # When circuit opened

    # Configuration
    failure_threshold: int  # Failures before opening (default: 5)
    success_threshold: int  # Successes before closing (default: 2)
    timeout: float  # Seconds before attempting HALF_OPEN (default: 60.0)

    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit breaker."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self.open_timestamp:
                elapsed = (datetime.utcnow() - self.open_timestamp).total_seconds()
                if elapsed >= self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def record_failure(self):
        """Record failed request."""
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.open_timestamp = datetime.utcnow()

        elif self.state == CircuitState.HALF_OPEN:
            # Failed during test → back to OPEN
            self.state = CircuitState.OPEN
            self.open_timestamp = datetime.utcnow()
            self.success_count = 0
