"""Failover orchestration strategy.

This module implements the failover strategy which tries providers sequentially
in priority order until one succeeds. Unhealthy providers are automatically skipped.
"""

import logging
from typing import Optional

from src.llm_adapters.health_tracker import HealthTracker
from src.llm_orchestrator.exceptions import AllProvidersFailedError
from src.llm_provider.base import LLMProvider
from src.llm_provider.exceptions import LLMAPIError
from src.llm_provider.types import ExtractedEntities

logger = logging.getLogger(__name__)


class FailoverStrategy:
    """Failover orchestration strategy.

    Tries providers sequentially in priority order. If one fails,
    automatically tries the next healthy provider. Skips unhealthy providers.

    Example:
        >>> strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])
        >>> providers = {"gemini": gemini_adapter, "claude": claude_adapter}
        >>> tracker = HealthTracker()
        >>> result = strategy.execute(providers, "email text", tracker)
    """

    def __init__(self, priority_order: list[str]):
        """Initialize failover strategy.

        Args:
            priority_order: List of provider names in priority order
                          (e.g., ["gemini", "claude", "openai"])
        """
        self.priority_order = priority_order
        logger.info(f"Initialized FailoverStrategy with priority: {priority_order}")

    def execute(
        self,
        providers: dict[str, LLMProvider],
        email_text: str,
        health_tracker: HealthTracker,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> tuple[ExtractedEntities, str]:
        """Execute failover strategy across providers.

        Tries providers in priority order until one succeeds.

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
            - MUST try providers in priority order
            - MUST skip unhealthy providers
            - MUST record failures in health tracker
            - MUST raise AllProvidersFailedError if all fail
            - MUST complete failover in < 2 seconds per provider
        """
        last_error: Optional[Exception] = None
        attempted_providers = []

        for provider_name in self.priority_order:
            # Skip if provider not available
            if provider_name not in providers:
                logger.warning(
                    f"Provider '{provider_name}' in priority order but not configured, skipping"
                )
                continue

            # Skip if provider is unhealthy
            if not health_tracker.is_healthy(provider_name):
                logger.info(
                    f"Skipping unhealthy provider: {provider_name} "
                    f"(circuit_breaker={health_tracker.get_metrics(provider_name).circuit_breaker_state})"
                )
                continue

            provider = providers[provider_name]
            attempted_providers.append(provider_name)

            try:
                logger.info(f"Attempting extraction with provider: {provider_name}")

                # Start timing
                import time

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

                logger.info(
                    f"Successfully extracted entities using {provider_name} "
                    f"(response_time={response_time_ms:.1f}ms)"
                )

                return entities, provider_name

            except LLMAPIError as e:
                # Record failure in health tracker
                health_tracker.record_failure(provider_name, str(e))

                logger.warning(
                    f"Provider {provider_name} failed: {type(e).__name__}: {str(e)[:100]}"
                )

                last_error = e
                # Continue to next provider

            except Exception as e:
                # Unexpected error - still record as failure
                health_tracker.record_failure(provider_name, f"Unexpected: {str(e)}")

                logger.error(
                    f"Unexpected error from provider {provider_name}: {e}",
                    exc_info=True,
                )

                last_error = e
                # Continue to next provider

        # All providers failed
        error_msg = (
            f"All providers failed or unhealthy. "
            f"Attempted: {attempted_providers}, "
            f"Priority order: {self.priority_order}"
        )

        if last_error:
            error_msg += f". Last error: {str(last_error)}"

        logger.error(error_msg)
        raise AllProvidersFailedError(error_msg)
