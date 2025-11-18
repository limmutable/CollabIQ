"""Performance metrics for LLM benchmarking.

This module defines data models for tracking and calculating
LLM performance metrics including accuracy, confidence, and speed.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MetricType(str, Enum):
    """Type of performance metric."""

    ACCURACY = "accuracy"  # Field extraction accuracy
    CONFIDENCE = "confidence"  # Average confidence score
    COMPLETENESS = "completeness"  # Percentage of fields extracted
    SPEED = "speed"  # Response time in seconds
    TOKEN_USAGE = "token_usage"  # Number of tokens used


class BenchmarkResult(BaseModel):
    """Result from a single benchmark run.

    Attributes:
        test_id: Unique identifier for this test
        provider: LLM provider name (gemini, claude, openai)
        prompt_id: Prompt variation ID used
        email_text: Original email text
        extracted_entities: Extracted entities (dict representation)
        expected_entities: Ground truth entities (dict representation)
        accuracy_scores: Per-field accuracy (0.0-1.0)
        confidence_scores: Per-field confidence (0.0-1.0)
        response_time: Time taken in seconds
        token_count: Number of tokens used
        error: Error message if extraction failed
        timestamp: When this test was run
    """

    test_id: str = Field(..., description="Unique test identifier")
    provider: str = Field(..., description="LLM provider name")
    prompt_id: str = Field(..., description="Prompt variation ID")
    email_text: str = Field(..., description="Original email text")

    extracted_entities: Dict[str, Any] = Field(..., description="Extracted entities")
    expected_entities: Optional[Dict[str, Any]] = Field(
        None, description="Ground truth entities"
    )

    accuracy_scores: Dict[str, float] = Field(
        default_factory=dict, description="Per-field accuracy scores"
    )
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict, description="Per-field confidence scores"
    )

    response_time: float = Field(..., ge=0.0, description="Response time in seconds")
    token_count: Optional[int] = Field(None, description="Token count if available")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Test timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "test_id": "test_001",
                "provider": "gemini",
                "prompt_id": "korean_optimized",
                "email_text": "어제 신세계와 본봄 킥오프",
                "extracted_entities": {
                    "startup_name": "본봄",
                    "partner_org": "신세계",
                },
                "expected_entities": {
                    "startup_name": "본봄",
                    "partner_org": "신세계",
                },
                "accuracy_scores": {"startup_name": 1.0, "partner_org": 1.0},
                "confidence_scores": {"startup_name": 0.95, "partner_org": 0.92},
                "response_time": 2.3,
                "token_count": 150,
                "error": None,
                "timestamp": "2024-11-17T10:30:00",
            }
        }
    )


class AggregatedMetrics(BaseModel):
    """Aggregated metrics across multiple benchmark runs.

    Attributes:
        provider: LLM provider name
        prompt_id: Prompt variation ID
        total_tests: Number of tests run
        successful_tests: Number of successful extractions
        failed_tests: Number of failed extractions
        avg_accuracy: Average accuracy score (0.0-1.0)
        avg_confidence: Average confidence score (0.0-1.0)
        avg_completeness: Average field completeness (0.0-1.0)
        avg_response_time: Average response time in seconds
        total_tokens: Total tokens used (if available)
        field_accuracies: Per-field accuracy breakdown
        field_confidences: Per-field confidence breakdown
    """

    provider: str = Field(..., description="LLM provider name")
    prompt_id: str = Field(..., description="Prompt variation ID")

    total_tests: int = Field(..., ge=0, description="Total number of tests")
    successful_tests: int = Field(..., ge=0, description="Successful extractions")
    failed_tests: int = Field(..., ge=0, description="Failed extractions")

    avg_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Average accuracy score"
    )
    avg_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Average confidence score"
    )
    avg_completeness: float = Field(
        ..., ge=0.0, le=1.0, description="Average field completeness"
    )
    avg_response_time: float = Field(
        ..., ge=0.0, description="Average response time in seconds"
    )

    total_tokens: Optional[int] = Field(None, description="Total tokens used")

    field_accuracies: Dict[str, float] = Field(
        default_factory=dict, description="Per-field accuracy breakdown"
    )
    field_confidences: Dict[str, float] = Field(
        default_factory=dict, description="Per-field confidence breakdown"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "provider": "gemini",
                "prompt_id": "korean_optimized",
                "total_tests": 20,
                "successful_tests": 19,
                "failed_tests": 1,
                "avg_accuracy": 0.92,
                "avg_confidence": 0.88,
                "avg_completeness": 0.95,
                "avg_response_time": 2.3,
                "total_tokens": 3000,
                "field_accuracies": {
                    "person_in_charge": 0.85,
                    "startup_name": 0.95,
                    "partner_org": 0.90,
                    "details": 0.92,
                    "date": 0.88,
                },
                "field_confidences": {
                    "person_in_charge": 0.82,
                    "startup_name": 0.92,
                    "partner_org": 0.88,
                    "details": 0.90,
                    "date": 0.85,
                },
            }
        }
    )


class ComparisonResult(BaseModel):
    """Comparison between two prompt variations or providers.

    Attributes:
        baseline_id: Baseline prompt/provider ID
        comparison_id: Comparison prompt/provider ID
        baseline_metrics: Metrics for baseline
        comparison_metrics: Metrics for comparison
        accuracy_improvement: Percentage improvement in accuracy
        confidence_improvement: Percentage improvement in confidence
        speed_improvement: Percentage improvement in speed (negative = slower)
        winner: Which variant performed better overall
    """

    baseline_id: str = Field(..., description="Baseline variant ID")
    comparison_id: str = Field(..., description="Comparison variant ID")

    baseline_metrics: AggregatedMetrics = Field(..., description="Baseline metrics")
    comparison_metrics: AggregatedMetrics = Field(..., description="Comparison metrics")

    accuracy_improvement: float = Field(
        ..., description="Percentage improvement in accuracy"
    )
    confidence_improvement: float = Field(
        ..., description="Percentage improvement in confidence"
    )
    speed_improvement: float = Field(..., description="Percentage improvement in speed")

    winner: str = Field(..., description="Better performing variant")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baseline_id": "baseline",
                "comparison_id": "korean_optimized",
                "accuracy_improvement": 15.2,
                "confidence_improvement": 8.5,
                "speed_improvement": -5.3,
                "winner": "korean_optimized",
            }
        }
    )


def calculate_accuracy(
    extracted: Dict[str, Any], expected: Dict[str, Any]
) -> Dict[str, float]:
    """Calculate per-field accuracy scores.

    Args:
        extracted: Extracted entities
        expected: Expected/ground truth entities

    Returns:
        Dictionary mapping field names to accuracy scores (0.0-1.0)

    Examples:
        >>> extracted = {"startup_name": "본봄", "partner_org": "신세계"}
        >>> expected = {"startup_name": "본봄", "partner_org": "신세계"}
        >>> calculate_accuracy(extracted, expected)
        {'startup_name': 1.0, 'partner_org': 1.0}
    """
    scores = {}
    for field in expected.keys():
        extracted_value = extracted.get(field)
        expected_value = expected.get(field)

        if expected_value is None and extracted_value is None:
            scores[field] = 1.0  # Both null - correct
        elif expected_value is None or extracted_value is None:
            scores[field] = 0.0  # One null, one not - incorrect
        elif str(extracted_value).lower() == str(expected_value).lower():
            scores[field] = 1.0  # Exact match
        else:
            scores[field] = 0.0  # Mismatch

    return scores


def calculate_completeness(entities: Dict[str, Any]) -> float:
    """Calculate field completeness (percentage of non-null fields).

    Args:
        entities: Extracted entities

    Returns:
        Completeness score (0.0-1.0)

    Examples:
        >>> entities = {"startup_name": "본봄", "partner_org": None, "details": "킥오프"}
        >>> calculate_completeness(entities)
        0.6666666666666666
    """
    if not entities:
        return 0.0

    non_null_count = sum(1 for v in entities.values() if v is not None)
    return non_null_count / len(entities)


def aggregate_results(results: List[BenchmarkResult]) -> AggregatedMetrics:
    """Aggregate multiple benchmark results into summary metrics.

    Args:
        results: List of benchmark results

    Returns:
        Aggregated metrics

    Examples:
        >>> results = [result1, result2, result3]
        >>> metrics = aggregate_results(results)
        >>> metrics.avg_accuracy
        0.92
    """
    if not results:
        raise ValueError("Cannot aggregate empty results list")

    provider = results[0].provider
    prompt_id = results[0].prompt_id

    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]

    # Calculate averages
    if successful:
        avg_response_time = sum(r.response_time for r in successful) / len(successful)

        # Average accuracy per field
        all_fields = set()
        for r in successful:
            all_fields.update(r.accuracy_scores.keys())

        field_accuracies = {}
        for field in all_fields:
            scores = [
                r.accuracy_scores.get(field, 0.0)
                for r in successful
                if field in r.accuracy_scores
            ]
            if scores:
                field_accuracies[field] = sum(scores) / len(scores)

        # Average confidence per field
        field_confidences = {}
        for field in all_fields:
            scores = [
                r.confidence_scores.get(field, 0.0)
                for r in successful
                if field in r.confidence_scores
            ]
            if scores:
                field_confidences[field] = sum(scores) / len(scores)

        # Overall averages
        avg_accuracy = (
            sum(field_accuracies.values()) / len(field_accuracies)
            if field_accuracies
            else 0.0
        )
        avg_confidence = (
            sum(field_confidences.values()) / len(field_confidences)
            if field_confidences
            else 0.0
        )

        # Completeness
        completeness_scores = []
        for r in successful:
            completeness_scores.append(calculate_completeness(r.extracted_entities))
        avg_completeness = (
            sum(completeness_scores) / len(completeness_scores)
            if completeness_scores
            else 0.0
        )

        # Token usage
        total_tokens = sum(r.token_count for r in successful if r.token_count)
    else:
        avg_response_time = 0.0
        avg_accuracy = 0.0
        avg_confidence = 0.0
        avg_completeness = 0.0
        field_accuracies = {}
        field_confidences = {}
        total_tokens = None

    return AggregatedMetrics(
        provider=provider,
        prompt_id=prompt_id,
        total_tests=len(results),
        successful_tests=len(successful),
        failed_tests=len(failed),
        avg_accuracy=avg_accuracy,
        avg_confidence=avg_confidence,
        avg_completeness=avg_completeness,
        avg_response_time=avg_response_time,
        total_tokens=total_tokens,
        field_accuracies=field_accuracies,
        field_confidences=field_confidences,
    )


# Public API
__all__ = [
    "MetricType",
    "BenchmarkResult",
    "AggregatedMetrics",
    "ComparisonResult",
    "calculate_accuracy",
    "calculate_completeness",
    "aggregate_results",
]
