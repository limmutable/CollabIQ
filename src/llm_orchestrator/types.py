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
    "QualityMetricsRecord",
    "ProviderQualitySummary",
    "QualityThresholdConfig",
    "ProviderQualityComparison",
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
        enable_quality_routing: Whether to enable quality-based routing
        quality_threshold: Optional quality requirements for routing
        quality_weight: Weight for quality vs other factors (0.0-1.0)
    """

    default_strategy: Literal[
        "failover", "consensus", "best_match", "all_providers"
    ] = "failover"
    provider_priority: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=90.0, ge=10.0, le=300.0)
    unhealthy_threshold: int = Field(default=5, ge=1, le=10)
    consensus_min_agreement: int = Field(default=2, ge=2)
    fuzzy_match_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    abstention_confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    circuit_breaker_timeout_seconds: float = Field(default=60.0, ge=1.0)
    half_open_max_calls: int = Field(default=3, ge=1)
    enable_quality_routing: bool = False
    quality_threshold: "QualityThresholdConfig | None" = None
    quality_weight: float = Field(default=0.5, ge=0.0, le=1.0)

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


class QualityMetricsRecord(BaseModel):
    """Quality measurements for a single email extraction attempt.

    Attributes:
        email_id: Unique email identifier
        provider_name: Provider identifier (gemini, claude, openai)
        extraction_timestamp: UTC timestamp when extraction occurred
        per_field_confidence: Confidence scores for 5 key entities (person, startup, partner, details, date)
        overall_confidence: Average of per-field confidence scores (0.0-1.0)
        field_completeness_percentage: (non-null fields / 5) * 100 (0.0-100.0)
        fields_extracted: Count of non-null fields (0-5)
        validation_passed: True if extraction passed validation
        validation_failure_reasons: List of failure reasons if validation failed
        notion_matching_attempted: True if Notion entity matching was attempted
        notion_matching_success: True if matching succeeded, None if not attempted
    """

    email_id: str
    provider_name: Literal["gemini", "claude", "openai"]
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    per_field_confidence: dict[str, float] = Field(
        description="Confidence scores for person, startup, partner, details, date"
    )
    overall_confidence: float = Field(ge=0.0, le=1.0)
    field_completeness_percentage: float = Field(ge=0.0, le=100.0)
    fields_extracted: int = Field(ge=0, le=5)
    validation_passed: bool
    validation_failure_reasons: list[str] | None = None
    notion_matching_attempted: bool = False
    notion_matching_success: bool | None = None

    @field_validator("per_field_confidence")
    @classmethod
    def validate_confidence_dict(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate per-field confidence has correct keys and values."""
        required_fields = {"person", "startup", "partner", "details", "date"}
        if set(v.keys()) != required_fields:
            raise ValueError(f"per_field_confidence must have keys: {required_fields}")
        for field, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Confidence score for {field} must be 0.0-1.0, got {score}"
                )
        return v

    @field_validator("validation_failure_reasons")
    @classmethod
    def validate_failure_reasons(cls, v: list[str] | None, info) -> list[str] | None:
        """Ensure validation_failure_reasons is provided when validation_passed is False."""
        if "validation_passed" in info.data:
            if not info.data["validation_passed"] and not v:
                raise ValueError(
                    "validation_failure_reasons must be non-empty list when validation_passed is False"
                )
        return v


class ProviderQualitySummary(BaseModel):
    """Aggregate quality statistics for a provider.

    Attributes:
        provider_name: Provider identifier
        total_extractions: Total extraction attempts tracked
        successful_validations: Extractions that passed validation
        failed_validations: Extractions that failed validation
        validation_success_rate: (successful_validations / total_extractions) * 100
        average_overall_confidence: Mean of all overall_confidence scores
        confidence_std_deviation: Standard deviation of overall_confidence
        average_field_completeness: Mean of field_completeness_percentage
        average_fields_extracted: Mean of fields_extracted counts
        per_field_confidence_averages: Average confidence per entity field
        quality_trend: improving/degrading/stable based on recent performance
        last_50_avg_confidence: Average confidence of last 50 extractions (None if <50)
        notion_matching_success_rate: (successful matches / attempted matches) * 100
        updated_at: UTC timestamp of last update
    """

    provider_name: Literal["gemini", "claude", "openai"]
    total_extractions: int = Field(default=0, ge=0)
    successful_validations: int = Field(default=0, ge=0)
    failed_validations: int = Field(default=0, ge=0)
    validation_success_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    average_overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_std_deviation: float = Field(default=0.0, ge=0.0)
    average_field_completeness: float = Field(default=0.0, ge=0.0, le=100.0)
    average_fields_extracted: float = Field(default=0.0, ge=0.0, le=5.0)
    per_field_confidence_averages: dict[str, float] = Field(
        default_factory=lambda: {
            "person": 0.0,
            "startup": 0.0,
            "partner": 0.0,
            "details": 0.0,
            "date": 0.0,
        }
    )
    quality_trend: Literal["improving", "degrading", "stable"] = "stable"
    last_50_avg_confidence: float | None = None
    notion_matching_success_rate: float | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QualityThresholdConfig(BaseModel):
    """Configuration defining acceptable quality levels.

    Attributes:
        threshold_name: Descriptive name for this threshold configuration
        minimum_average_confidence: Minimum acceptable average confidence (0.0-1.0)
        minimum_field_completeness: Minimum acceptable field completeness (0.0-100.0)
        maximum_validation_failure_rate: Maximum acceptable validation failure rate (0.0-100.0)
        minimum_notion_matching_success_rate: Minimum Notion matching success rate (0.0-100.0)
        evaluation_window_size: Number of recent extractions to evaluate (≥10)
        enabled: Whether this threshold configuration is active
    """

    threshold_name: str
    minimum_average_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    minimum_field_completeness: float = Field(default=80.0, ge=0.0, le=100.0)
    maximum_validation_failure_rate: float = Field(default=10.0, ge=0.0, le=100.0)
    minimum_notion_matching_success_rate: float | None = Field(
        default=None, ge=0.0, le=100.0
    )
    evaluation_window_size: int = Field(default=100, ge=10)
    enabled: bool = True


class ProviderQualityComparison(BaseModel):
    """Cross-provider quality analysis for decision-making.

    Attributes:
        comparison_timestamp: UTC timestamp when comparison was generated
        providers_compared: List of provider names in comparison
        provider_rankings: Providers ranked by overall quality (best to worst)
        quality_to_cost_rankings: Providers ranked by value score (best to worst)
        recommended_provider: Provider with best overall quality-to-cost ratio
        recommendation_reason: Human-readable explanation of recommendation
    """

    comparison_timestamp: datetime = Field(default_factory=datetime.utcnow)
    providers_compared: list[str]
    provider_rankings: list[
        dict
    ]  # provider_name (str), quality_score (float), rank (int)
    quality_to_cost_rankings: list[
        dict
    ]  # provider_name (str), value_score (float), rank (int)
    recommended_provider: str
    recommendation_reason: str
