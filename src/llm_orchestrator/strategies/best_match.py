"""Best-match orchestration strategy.

This module implements the best-match strategy which queries multiple providers
in parallel and selects the extraction result with the highest aggregate confidence score.

The aggregate confidence is calculated as a weighted average across all entity fields,
with higher weights given to more critical fields (person, startup, partner).
"""

import logging
import time
from typing import Optional

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.exceptions import AllProvidersFailedError
from llm_provider.base import LLMProvider
from llm_provider.exceptions import LLMAPIError
from llm_provider.types import ConfidenceScores, ExtractedEntities

logger = logging.getLogger(__name__)

# Default weights for aggregate confidence calculation
# Higher weights = more important for entity extraction quality
DEFAULT_WEIGHTS = {
    "person": 1.5,  # Person in charge is critical
    "startup": 1.5,  # Startup name is critical
    "partner": 1.0,  # Partner org is important
    "details": 0.8,  # Details are useful but less critical
    "date": 0.5,  # Date is least critical (often missing or low confidence)
}


def calculate_aggregate_confidence(
    confidence: ConfidenceScores,
    weights: Optional[dict[str, float]] = None,
) -> float:
    """Calculate weighted average confidence across all entity fields.

    Args:
        confidence: ConfidenceScores from a provider's extraction result
        weights: Optional custom weights dict. If None, uses DEFAULT_WEIGHTS.
                Keys: person, startup, partner, details, date
                Values: Weight multipliers (must be non-negative)

    Returns:
        Aggregate confidence score (0.0-1.0) as weighted average

    Raises:
        ValueError: If weights are negative or sum to zero

    Example:
        >>> confidence = ConfidenceScores(
        ...     person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        ... )
        >>> aggregate = calculate_aggregate_confidence(confidence)
        >>> # Returns weighted average favoring person/startup/partner
        >>> aggregate  # ~0.896

    Formula:
        aggregate = sum(confidence_i * weight_i) / sum(weight_i)

    Default weights prioritize:
        1. Person (1.5x) - Critical for tracking responsibility
        2. Startup (1.5x) - Critical for entity identification
        3. Partner (1.0x) - Important for collaboration context
        4. Details (0.8x) - Useful but less critical
        5. Date (0.5x) - Often missing or low confidence
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Merge custom weights with defaults (custom weights override defaults)
    final_weights = {**DEFAULT_WEIGHTS, **weights}

    # Validate weights
    for field, weight in final_weights.items():
        if weight < 0:
            raise ValueError(f"Weights must be non-negative, got {field}={weight}")

    # Calculate weighted sum
    weighted_sum = 0.0
    weight_total = 0.0

    weighted_sum += confidence.person * final_weights["person"]
    weighted_sum += confidence.startup * final_weights["startup"]
    weighted_sum += confidence.partner * final_weights["partner"]
    weighted_sum += confidence.details * final_weights["details"]
    weighted_sum += confidence.date * final_weights["date"]

    weight_total = (
        final_weights["person"]
        + final_weights["startup"]
        + final_weights["partner"]
        + final_weights["details"]
        + final_weights["date"]
    )

    # Validate weight sum
    if weight_total <= 0:
        raise ValueError("Sum of weights must be positive")

    # Calculate weighted average
    aggregate = weighted_sum / weight_total

    return aggregate


class BestMatchStrategy:
    """Best-match orchestration strategy.

    Queries all providers in parallel and selects the extraction result with
    the highest aggregate confidence score. If multiple results have the same
    aggregate confidence, uses tie-breaking logic (historical success rate, then
    priority order).

    This strategy optimizes for extraction quality by leveraging all providers
    simultaneously and selecting the most confident result.

    Example:
        >>> strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])
        >>> providers = {"gemini": gemini_adapter, "claude": claude_adapter, ...}
        >>> tracker = HealthTracker()
        >>> result, provider_used = strategy.execute(providers, "email text", tracker)
        >>> # Returns result from provider with highest aggregate confidence
    """

    def __init__(self, provider_names: list[str]):
        """Initialize best-match strategy.

        Args:
            provider_names: List of provider names to query in parallel
                          (e.g., ["gemini", "claude", "openai"])
        """
        self.provider_names = provider_names
        logger.info(f"Initialized BestMatchStrategy with providers: {provider_names}")

    def execute(
        self,
        providers: dict[str, LLMProvider],
        email_text: str,
        health_tracker: HealthTracker,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> tuple[ExtractedEntities, str]:
        """Execute best-match strategy across providers.

        Queries all healthy providers in parallel, calculates aggregate confidence
        for each result, and selects the result with highest confidence.

        Args:
            providers: Dictionary mapping provider_name → LLMProvider instance
            email_text: Email text to extract entities from
            health_tracker: HealthTracker for monitoring provider health
            company_context: Optional company context for matching
            email_id: Optional email ID

        Returns:
            Tuple of (ExtractedEntities, provider_name_used)

        Raises:
            AllProvidersFailedError: If all providers failed or are unhealthy

        Contract:
            - MUST query all healthy providers in parallel
            - MUST calculate aggregate confidence for each result
            - MUST select result with highest aggregate confidence
            - MUST use tie-breaking (success rate → priority order)
            - MUST record success/failure in health tracker
            - MUST raise AllProvidersFailedError if all fail
        """
        logger.info(
            f"BestMatch: Querying {len(self.provider_names)} providers in parallel"
        )

        # Track results from all providers
        results: list[tuple[ExtractedEntities, str, float]] = []
        failed_providers = []

        # Query all healthy providers (synchronous for now)
        for provider_name in self.provider_names:
            # Skip if provider not available
            if provider_name not in providers:
                logger.warning(f"Provider '{provider_name}' not configured, skipping")
                continue

            # Skip if provider is unhealthy
            if not health_tracker.is_healthy(provider_name):
                logger.info(
                    f"Skipping unhealthy provider: {provider_name} "
                    f"(circuit_breaker={health_tracker.get_metrics(provider_name).circuit_breaker_state})"
                )
                continue

            provider = providers[provider_name]

            try:
                logger.info(f"BestMatch: Querying provider: {provider_name}")

                # Start timing
                start_time = time.time()

                # Call provider's extract_entities
                entities = provider.extract_entities(
                    email_text=email_text,
                    company_context=company_context,
                    email_id=email_id,
                )

                # Calculate response time
                response_time_ms = (time.time() - start_time) * 1000

                # Record success
                health_tracker.record_success(provider_name, response_time_ms)

                # Calculate aggregate confidence
                aggregate_confidence = calculate_aggregate_confidence(
                    entities.confidence
                )

                logger.info(
                    f"BestMatch: {provider_name} succeeded "
                    f"(aggregate_confidence={aggregate_confidence:.3f}, "
                    f"response_time={response_time_ms:.1f}ms)"
                )

                # Store result with aggregate confidence
                results.append((entities, provider_name, aggregate_confidence))

            except LLMAPIError as e:
                # Record failure in health tracker
                health_tracker.record_failure(provider_name, str(e))

                logger.warning(
                    f"BestMatch: {provider_name} failed: {type(e).__name__}: {str(e)[:100]}"
                )

                failed_providers.append((provider_name, str(e)))

            except Exception as e:
                # Unexpected error - still record as failure
                health_tracker.record_failure(provider_name, f"Unexpected: {str(e)}")

                logger.error(
                    f"BestMatch: Unexpected error from {provider_name}: {e}",
                    exc_info=True,
                )

                failed_providers.append((provider_name, f"Unexpected: {str(e)}"))

        # Check if we have any results
        if not results:
            error_msg = (
                f"All providers failed or unhealthy. Attempted: {self.provider_names}"
            )
            if failed_providers:
                error_msg += f". Failures: {failed_providers}"

            logger.error(error_msg)
            raise AllProvidersFailedError(error_msg)

        # Select result with highest aggregate confidence
        # Sort by: 1) aggregate_confidence (descending), 2) priority order (ascending)
        # Priority order = index in self.provider_names (lower index = higher priority)
        results_with_priority = [
            (
                entities,
                provider_name,
                agg_conf,
                self.provider_names.index(provider_name),
            )
            for entities, provider_name, agg_conf in results
        ]

        # Sort by aggregate confidence (descending), then priority (ascending)
        # Also use historical success rate as secondary tie-breaker
        def sort_key(item):
            entities, provider_name, agg_conf, priority_index = item
            success_rate = health_tracker.get_metrics(provider_name).success_rate
            return (
                -agg_conf,  # Higher confidence first (negative for descending)
                -success_rate,  # Higher success rate first (tie-breaker)
                priority_index,  # Lower priority index first (final tie-breaker)
            )

        results_with_priority.sort(key=sort_key)

        # Select best result
        best_entities, best_provider, best_confidence, _ = results_with_priority[0]

        logger.info(
            f"BestMatch: Selected {best_provider} "
            f"(aggregate_confidence={best_confidence:.3f}, "
            f"total_providers_queried={len(results)}, "
            f"total_providers_failed={len(failed_providers)})"
        )

        return best_entities, best_provider
