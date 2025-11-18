"""Health tracking for LLM providers with circuit breaking.

This module implements health monitoring and circuit breaker pattern for LLM providers.
It tracks success/failure rates, response times, and manages circuit breaker states
(CLOSED, OPEN, HALF_OPEN) with persistence across application restarts.
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from llm_adapters.types import ProviderHealthMetrics

logger = logging.getLogger(__name__)


class HealthTracker:
    """Track provider health with circuit breaking and persistent state.

    This class monitors LLM provider health status, implements circuit breaking,
    and provides recovery testing. State is persisted to disk across restarts.

    Attributes:
        data_dir: Directory for health metrics JSON storage
        unhealthy_threshold: Consecutive failures before marking unhealthy
        circuit_breaker_timeout_seconds: Time in OPEN before transitioning to HALF_OPEN
        half_open_max_calls: Maximum calls allowed in HALF_OPEN state

    Example:
        >>> tracker = HealthTracker(data_dir="data/llm_health")
        >>> tracker.record_success("claude", 1834.5)
        >>> tracker.is_healthy("claude")
        True
        >>> for _ in range(5):
        ...     tracker.record_failure("claude", "API Error")
        >>> tracker.is_healthy("claude")
        False
    """

    def __init__(
        self,
        data_dir: str | Path = "data/llm_health",
        unhealthy_threshold: int = 5,
        circuit_breaker_timeout_seconds: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """Initialize HealthTracker.

        Args:
            data_dir: Directory for health metrics JSON storage
            unhealthy_threshold: Consecutive failures before unhealthy (default: 5)
            circuit_breaker_timeout_seconds: Time in OPEN before HALF_OPEN (default: 60.0)
            half_open_max_calls: Max calls in HALF_OPEN state (default: 3)
        """
        self.data_dir = Path(data_dir)
        self.unhealthy_threshold = unhealthy_threshold
        self.circuit_breaker_timeout_seconds = circuit_breaker_timeout_seconds
        self.half_open_max_calls = half_open_max_calls

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Metrics file path
        self.metrics_file = self.data_dir / "health_metrics.json"

        # Track HALF_OPEN state success count
        self._half_open_success_count: dict[str, int] = {}

        # Load existing metrics or initialize defaults
        self.metrics = self._load_metrics()

        logger.info(
            f"Initialized HealthTracker: data_dir={data_dir}, "
            f"unhealthy_threshold={unhealthy_threshold}, "
            f"circuit_breaker_timeout={circuit_breaker_timeout_seconds}s"
        )

    def is_healthy(self, provider_name: str) -> bool:
        """Check if a provider is currently healthy and available.

        Args:
            provider_name: Provider identifier (gemini, claude, openai)

        Returns:
            True if provider is healthy, False otherwise

        Behavior:
            - Returns False if circuit breaker is OPEN (unless timeout elapsed)
            - Transitions OPEN → HALF_OPEN if timeout elapsed
            - Returns False if consecutive_failures >= threshold
            - Returns True otherwise
        """
        metrics = self.get_metrics(provider_name)

        # Check circuit breaker state
        if metrics.circuit_breaker_state == "open":
            # Check if timeout has elapsed → transition to HALF_OPEN
            if metrics.last_failure_timestamp:
                time_since_failure = (
                    datetime.now(timezone.utc) - metrics.last_failure_timestamp
                ).total_seconds()

                if time_since_failure >= self.circuit_breaker_timeout_seconds:
                    logger.info(
                        f"Circuit breaker timeout elapsed for {provider_name}, "
                        f"transitioning to HALF_OPEN"
                    )
                    self._transition_to_half_open(provider_name)
                    return True  # Allow limited testing

            return False  # Circuit still open

        # Check consecutive failures threshold
        if metrics.consecutive_failures >= self.unhealthy_threshold:
            return False

        return True

    def record_success(self, provider_name: str, response_time_ms: float) -> None:
        """Record a successful API call and update health metrics.

        Args:
            provider_name: Provider identifier
            response_time_ms: API response time in milliseconds

        Side Effects:
            - Increments success_count
            - Resets consecutive_failures to 0
            - Updates average_response_time_ms (rolling average)
            - Sets last_success_timestamp to current UTC time
            - Sets health_status to "healthy"
            - Transitions circuit breaker if in HALF_OPEN state
            - Persists metrics to JSON file
        """
        metrics = self.get_metrics(provider_name)

        # Update counters
        metrics.success_count += 1
        metrics.consecutive_failures = 0

        # Update average response time (rolling average)
        if metrics.success_count == 1:
            metrics.average_response_time_ms = response_time_ms
        else:
            # Weighted average: give more weight to recent responses
            alpha = 0.2  # Smoothing factor
            metrics.average_response_time_ms = (
                alpha * response_time_ms
                + (1 - alpha) * metrics.average_response_time_ms
            )

        # Update timestamps and status
        metrics.last_success_timestamp = datetime.now(timezone.utc)
        metrics.health_status = "healthy"
        metrics.updated_at = datetime.now(timezone.utc)

        # Handle circuit breaker transitions
        if metrics.circuit_breaker_state == "half_open":
            # Track successes in HALF_OPEN state
            self._half_open_success_count[provider_name] = (
                self._half_open_success_count.get(provider_name, 0) + 1
            )

            # Require 2 consecutive successes to transition to CLOSED
            if self._half_open_success_count[provider_name] >= 2:
                logger.info(
                    f"Provider {provider_name} recovered: "
                    f"transitioning HALF_OPEN → CLOSED"
                )
                self._transition_to_closed(provider_name)
        else:
            # Already CLOSED, keep it that way
            metrics.circuit_breaker_state = "closed"

        # Persist to disk
        self._save_metrics()

        logger.debug(
            f"Recorded success for {provider_name}: "
            f"response_time={response_time_ms:.1f}ms, "
            f"success_rate={metrics.success_rate:.2f}"
        )

    def record_failure(self, provider_name: str, error_message: str) -> None:
        """Record a failed API call and update health metrics.

        Args:
            provider_name: Provider identifier
            error_message: Error description (max 500 characters)

        Side Effects:
            - Increments failure_count
            - Increments consecutive_failures
            - Sets last_failure_timestamp to current UTC time
            - Sets last_error_message (truncated to 500 chars)
            - Sets health_status to "unhealthy" if threshold reached
            - Opens circuit breaker if threshold reached
            - Transitions HALF_OPEN → OPEN if recovery fails
            - Persists metrics to JSON file
        """
        metrics = self.get_metrics(provider_name)

        # Update counters
        metrics.failure_count += 1
        metrics.consecutive_failures += 1

        # Update timestamps and error message
        metrics.last_failure_timestamp = datetime.now(timezone.utc)
        metrics.last_error_message = error_message[:500]  # Truncate to 500 chars
        metrics.updated_at = datetime.now(timezone.utc)

        # Check if we've hit the unhealthy threshold
        if metrics.consecutive_failures >= self.unhealthy_threshold:
            logger.warning(
                f"Provider {provider_name} unhealthy: "
                f"{metrics.consecutive_failures} consecutive failures"
            )
            metrics.health_status = "unhealthy"
            self._transition_to_open(provider_name)
        elif metrics.circuit_breaker_state == "half_open":
            # Recovery test failed, go back to OPEN
            logger.warning(
                f"Provider {provider_name} recovery test failed: "
                f"transitioning HALF_OPEN → OPEN"
            )
            self._transition_to_open(provider_name)

        # Persist to disk
        self._save_metrics()

        logger.debug(
            f"Recorded failure for {provider_name}: "
            f"consecutive_failures={metrics.consecutive_failures}, "
            f"error='{error_message[:100]}'"
        )

    def get_metrics(self, provider_name: str) -> ProviderHealthMetrics:
        """Get current health metrics for a provider.

        Args:
            provider_name: Provider identifier

        Returns:
            ProviderHealthMetrics for the specified provider
        """
        if provider_name not in self.metrics:
            # Initialize default metrics for new provider
            self.metrics[provider_name] = ProviderHealthMetrics(
                provider_name=provider_name
            )
            self._save_metrics()

        return self.metrics[provider_name]

    def get_all_metrics(self) -> dict[str, ProviderHealthMetrics]:
        """Get health metrics for all configured providers.

        Returns:
            Dictionary mapping provider_name → ProviderHealthMetrics
        """
        return self.metrics.copy()

    def reset_metrics(self, provider_name: str) -> None:
        """Reset health metrics for a provider (for testing or manual recovery).

        Args:
            provider_name: Provider identifier

        Side Effects:
            - Resets all counters to 0
            - Sets health_status to "healthy"
            - Sets circuit_breaker_state to "closed"
            - Clears timestamps and error message
            - Persists to JSON file
        """
        self.metrics[provider_name] = ProviderHealthMetrics(
            provider_name=provider_name,
            health_status="healthy",
            circuit_breaker_state="closed",
        )

        # Clear HALF_OPEN success count
        if provider_name in self._half_open_success_count:
            del self._half_open_success_count[provider_name]

        self._save_metrics()

        logger.info(f"Reset health metrics for {provider_name}")

    def _transition_to_closed(self, provider_name: str) -> None:
        """Transition circuit breaker to CLOSED (normal operation)."""
        metrics = self.get_metrics(provider_name)
        metrics.circuit_breaker_state = "closed"
        metrics.health_status = "healthy"

        # Clear HALF_OPEN success count
        if provider_name in self._half_open_success_count:
            del self._half_open_success_count[provider_name]

    def _transition_to_open(self, provider_name: str) -> None:
        """Transition circuit breaker to OPEN (provider unhealthy)."""
        metrics = self.get_metrics(provider_name)
        metrics.circuit_breaker_state = "open"
        metrics.health_status = "unhealthy"

        # Clear HALF_OPEN success count
        if provider_name in self._half_open_success_count:
            del self._half_open_success_count[provider_name]

    def _transition_to_half_open(self, provider_name: str) -> None:
        """Transition circuit breaker to HALF_OPEN (testing recovery)."""
        metrics = self.get_metrics(provider_name)
        metrics.circuit_breaker_state = "half_open"

        # Reset HALF_OPEN success count
        self._half_open_success_count[provider_name] = 0

    def _load_metrics(self) -> dict[str, ProviderHealthMetrics]:
        """Load health metrics from JSON file.

        Returns:
            Dictionary mapping provider_name → ProviderHealthMetrics
        """
        if not self.metrics_file.exists():
            logger.info("No existing health metrics found, initializing defaults")
            return {}

        try:
            with open(self.metrics_file, "r") as f:
                data = json.load(f)

            # Parse JSON into ProviderHealthMetrics objects
            metrics = {}
            for provider_name, metrics_dict in data.items():
                # Convert ISO timestamps to datetime objects
                if metrics_dict.get("last_success_timestamp"):
                    metrics_dict["last_success_timestamp"] = datetime.fromisoformat(
                        metrics_dict["last_success_timestamp"]
                    )
                if metrics_dict.get("last_failure_timestamp"):
                    metrics_dict["last_failure_timestamp"] = datetime.fromisoformat(
                        metrics_dict["last_failure_timestamp"]
                    )
                if metrics_dict.get("updated_at"):
                    metrics_dict["updated_at"] = datetime.fromisoformat(
                        metrics_dict["updated_at"]
                    )

                metrics[provider_name] = ProviderHealthMetrics(**metrics_dict)

            logger.info(f"Loaded health metrics for {len(metrics)} providers")
            return metrics

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to load health metrics: {e}, initializing defaults")
            return {}

    def _save_metrics(self) -> None:
        """Save health metrics to JSON file using atomic write.

        Uses temp file + rename to ensure atomic writes and prevent corruption.
        """
        # Convert metrics to JSON-serializable dict
        data = {}
        for provider_name, metrics in self.metrics.items():
            metrics_dict = metrics.model_dump()

            # Convert datetime objects to ISO format strings
            if metrics_dict.get("last_success_timestamp"):
                metrics_dict["last_success_timestamp"] = metrics_dict[
                    "last_success_timestamp"
                ].isoformat()
            if metrics_dict.get("last_failure_timestamp"):
                metrics_dict["last_failure_timestamp"] = metrics_dict[
                    "last_failure_timestamp"
                ].isoformat()
            if metrics_dict.get("updated_at"):
                metrics_dict["updated_at"] = metrics_dict["updated_at"].isoformat()

            data[provider_name] = metrics_dict

        # Atomic write: temp file + rename
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")

        try:
            with os.fdopen(temp_fd, "w") as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            shutil.move(temp_path, self.metrics_file)

        except Exception as e:
            # Clean up temp file on error
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            logger.error(f"Failed to save health metrics: {e}")
            raise
