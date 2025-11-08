"""Type definitions for LLM orchestration.

This module defines Pydantic models for provider configuration, health metrics,
orchestration strategies, and related types.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Re-export ProviderHealthMetrics from llm_adapters to avoid circular import
from llm_adapters.types import ProviderHealthMetrics

__all__ = [
    "ProviderConfig",
    "ProviderHealthMetrics",
    "ProviderStatus",
    "OrchestrationConfig",
    "CostMetricsSummary",
]


class ProviderConfig(BaseModel):
    """Configuration for a specific LLM provider.

    Attributes:
        provider_name: Unique identifier (gemini, claude, openai)
        display_name: Human-readable name
        model_id: Specific model identifier
        api_key_env_var: Environment variable name for API key
        enabled: Whether provider is active
        priority: Priority order (1 = highest)
        timeout_seconds: Request timeout
        max_retries: Maximum retry attempts
        input_token_price: Cost per 1M input tokens (USD)
        output_token_price: Cost per 1M output tokens (USD)
    """

    provider_name: Literal["gemini", "claude", "openai"]
    display_name: str
    model_id: str
    api_key_env_var: str
    enabled: bool = True
    priority: int = Field(ge=1)
    timeout_seconds: float = Field(default=60.0, ge=5.0, le=300.0)
    max_retries: int = Field(default=3, ge=0, le=5)
    input_token_price: float = Field(ge=0.0)  # USD per 1M tokens
    output_token_price: float = Field(ge=0.0)  # USD per 1M tokens


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


class ProviderStatus(BaseModel):
    """Current status of a provider for monitoring.

    This is a simplified view of ProviderHealthMetrics for API responses.

    Attributes:
        provider_name: Provider identifier
        health_status: Current health state
        enabled: Whether provider is active
        success_rate: Success rate (0.0-1.0)
        average_response_time_ms: Average response time
        total_api_calls: Total number of API calls
        last_success: UTC timestamp of last success
        last_failure: UTC timestamp of last failure
        circuit_breaker_state: Circuit breaker status
    """

    provider_name: str
    health_status: Literal["healthy", "unhealthy"]
    enabled: bool
    success_rate: float = Field(ge=0.0, le=1.0)
    average_response_time_ms: float = Field(ge=0.0)
    total_api_calls: int = Field(ge=0)
    last_success: datetime | None
    last_failure: datetime | None
    circuit_breaker_state: Literal["closed", "open", "half_open"]


class OrchestrationConfig(BaseModel):
    """Configuration for orchestration strategies.

    Attributes:
        default_strategy: Default strategy to use
        provider_priority: Failover sequence (for failover strategy)
        timeout_seconds: Overall orchestration timeout
        unhealthy_threshold: Consecutive failures before unhealthy
        consensus_min_agreement: Minimum providers that must agree (consensus)
        fuzzy_match_threshold: Jaro-Winkler threshold for fuzzy matching
        abstention_confidence_threshold: Min confidence to avoid abstention
        circuit_breaker_timeout_seconds: Time in OPEN before HALF_OPEN
        half_open_max_calls: Max calls in HALF_OPEN state
    """

    default_strategy: Literal["failover", "consensus", "best_match"] = "failover"
    provider_priority: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=90.0, ge=10.0, le=300.0)
    unhealthy_threshold: int = Field(default=5, ge=1, le=10)
    consensus_min_agreement: int = Field(default=2, ge=2)
    fuzzy_match_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    abstention_confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    circuit_breaker_timeout_seconds: float = Field(default=60.0, ge=1.0)
    half_open_max_calls: int = Field(default=3, ge=1)

    @field_validator("provider_priority")
    @classmethod
    def validate_provider_priority(cls, v: list[str]) -> list[str]:
        """Validate provider names in priority list."""
        valid_providers = {"gemini", "claude", "openai"}
        for provider in v:
            if provider not in valid_providers:
                raise ValueError(
                    f"Invalid provider '{provider}'. Must be one of: {valid_providers}"
                )
        return v


class CostMetricsSummary(BaseModel):
    """Financial cost tracking per provider.

    Attributes:
        provider_name: Provider identifier
        total_api_calls: Total number of API requests
        total_input_tokens: Cumulative input tokens
        total_output_tokens: Cumulative output tokens
        total_tokens: Sum of input + output tokens
        total_cost_usd: Cumulative cost (USD)
        average_cost_per_email: Average cost per extraction
        last_updated: Last metrics update timestamp
    """

    provider_name: str
    total_api_calls: int = Field(default=0, ge=0)
    total_input_tokens: int = Field(default=0, ge=0)
    total_output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    average_cost_per_email: float = Field(default=0.0, ge=0.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def average_input_tokens_per_call(self) -> float:
        """Calculate average input tokens per call."""
        if self.total_api_calls == 0:
            return 0.0
        return self.total_input_tokens / self.total_api_calls

    @property
    def average_output_tokens_per_call(self) -> float:
        """Calculate average output tokens per call."""
        if self.total_api_calls == 0:
            return 0.0
        return self.total_output_tokens / self.total_api_calls

    @property
    def average_cost_per_call(self) -> float:
        """Calculate average cost per call."""
        if self.total_api_calls == 0:
            return 0.0
        return self.total_cost_usd / self.total_api_calls
