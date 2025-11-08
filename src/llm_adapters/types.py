"""Type definitions for LLM adapters and health tracking."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProviderHealthMetrics(BaseModel):
    """Health tracking metrics for a provider.

    Attributes:
        provider_name: Provider identifier
        health_status: Current health state (healthy/unhealthy)
        success_count: Total successful requests
        failure_count: Total failed requests
        consecutive_failures: Current failure streak
        average_response_time_ms: Rolling average response time
        last_success_timestamp: UTC timestamp of last success
        last_failure_timestamp: UTC timestamp of last failure
        last_error_message: Most recent error description
        circuit_breaker_state: Circuit breaker status
        updated_at: Last metrics update timestamp
    """

    provider_name: str
    health_status: Literal["healthy", "unhealthy"] = "healthy"
    success_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    consecutive_failures: int = Field(default=0, ge=0)
    average_response_time_ms: float = Field(default=0.0, ge=0.0)
    last_success_timestamp: datetime | None = None
    last_failure_timestamp: datetime | None = None
    last_error_message: str | None = Field(default=None, max_length=500)
    circuit_breaker_state: Literal["closed", "open", "half_open"] = "closed"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
