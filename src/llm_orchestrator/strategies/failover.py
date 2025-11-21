"""Failover orchestration strategy.

This module implements the failover strategy which tries providers sequentially
in priority order until one succeeds. Unhealthy providers are automatically skipped.
"""

import logging
import time
from typing import TYPE_CHECKING, Optional

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.exceptions import AllProvidersFailedError
from llm_provider.base import LLMProvider
from llm_provider.exceptions import LLMAPIError
from llm_provider.types import ExtractedEntities

if TYPE_CHECKING:
    from llm_orchestrator.quality_tracker import QualityTracker

logger = logging.getLogger(__name__)


class FailoverStrategy:
    """Failover orchestration strategy.

    Tries providers sequentially in priority order. If one fails,
    automatically tries the next healthy provider. Skips unhealthy providers.

    Supports optional quality-based routing to select providers based on
    historical quality metrics before falling back to priority order.

    Example:
        >>> strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])
        >>> providers = {"gemini": gemini_adapter, "claude": claude_adapter}
        >>> tracker = HealthTracker()
        >>> result = strategy.execute(providers, "email text", tracker)
    """

    def __init__(
        self,
        priority_order: list[str],
        quality_tracker: Optional["QualityTracker"] = None,
    ):
        """Initialize failover strategy.

        Args:
            priority_order: List of provider names in priority order
                          (e.g., ["gemini", "claude", "openai"])
            quality_tracker: Optional QualityTracker for quality-based routing
        """
        self.priority_order = priority_order
        self.quality_tracker = quality_tracker
        logger.info(
            f"Initialized FailoverStrategy with priority: {priority_order}, "
            f"quality_routing={'enabled' if quality_tracker else 'disabled'}"
        )

    async def execute(
        self,
        providers: dict[str, LLMProvider],
        email_text: str,
        health_tracker: HealthTracker,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> tuple[ExtractedEntities, str]:
        """Execute failover strategy across providers (asynchronously).

        Tries providers in priority order until one succeeds.
        If quality_tracker is available, quality-ranked providers are tried first,
        then falls back to priority order for remaining providers.

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
            - MUST try providers in priority order (or quality order if enabled)
            - MUST skip unhealthy providers
            - MUST record failures in health tracker
            - MUST raise AllProvidersFailedError if all fail
            - MUST complete failover in < 2 seconds per provider
        """
        last_error: Optional[Exception] = None
        attempted_providers = []

        provider_order = self.priority_order.copy()
        logger.debug(f"Initial provider_order: {provider_order}")

        if self.quality_tracker:
            available_providers = list(providers.keys())
            quality_selected = self.quality_tracker.select_provider_by_quality(
                available_providers
            )

            if quality_selected:
                provider_order = [quality_selected]
                for provider_name in self.priority_order:
                    if (
                        provider_name != quality_selected
                        and provider_name in available_providers
                    ):
                        provider_order.append(provider_name)

                logger.info(
                    f"Quality routing enabled: trying {quality_selected} first, "
                    f"then falling back to: {provider_order[1:]}"
                )
            else:
                logger.info(
                    "Quality routing enabled but no quality metrics available, "
                    "falling back to priority order"
                )
                logger.debug(
                    f"Fallback provider_order (no quality metrics): {provider_order}"
                )

        for provider_name in provider_order:
            logger.debug(f"Attempting provider: {provider_name}")
            if provider_name not in providers:
                logger.warning(
                    f"Provider '{provider_name}' in priority order but not configured, skipping"
                )
                continue

            is_provider_healthy = health_tracker.is_healthy(provider_name)
            logger.debug(
                f"Provider {provider_name} health status: {is_provider_healthy}"
            )
            if not is_provider_healthy:
                logger.info(
                    f"Skipping unhealthy provider: {provider_name} "
                    f"(circuit_breaker={health_tracker.get_metrics(provider_name).circuit_breaker_state})"
                )
                continue

            provider = providers[provider_name]
            attempted_providers.append(provider_name)

            try:
                logger.info(f"Attempting extraction with provider: {provider_name}")

                start_time = time.time()

                entities = await provider.extract_entities(
                    email_text=email_text,
                    company_context=company_context,
                    email_id=email_id,
                )

                response_time_ms = (time.time() - start_time) * 1000

                health_tracker.record_success(provider_name, response_time_ms)

                logger.info(
                    f"Successfully extracted entities using {provider_name} "
                    f"(response_time={response_time_ms:.1f}ms)"
                )

                return entities, provider_name

            except LLMAPIError as e:
                health_tracker.record_failure(provider_name, str(e))

                logger.warning(
                    f"Provider {provider_name} failed: {type(e).__name__}: {str(e)[:100]}"
                )

                last_error = e

            except Exception as e:
                health_tracker.record_failure(provider_name, f"Unexpected: {str(e)}")

                logger.error(
                    f"Unexpected error from provider {provider_name}: {e}",
                    exc_info=True,
                )

                last_error = e

        error_msg = (
            f"All providers failed or unhealthy. "
            f"Attempted: {attempted_providers}, "
            f"Priority order: {self.priority_order}"
        )

        if last_error:
            error_msg += f". Last error: {str(last_error)}"

        logger.error(error_msg)
        raise AllProvidersFailedError(error_msg)
