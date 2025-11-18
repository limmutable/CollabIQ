"""All Providers Strategy - Extract with all providers and track metrics.

This strategy calls ALL available LLM providers in parallel for every extraction.
It's designed for continuous quality metrics collection and provider comparison.

Key features:
- Calls all providers concurrently (faster than sequential)
- Records quality metrics for ALL providers (not just the one used)
- Selects best result based on configurable criteria
- Essential for quality-based routing to have up-to-date metrics

Selection criteria:
1. Highest confidence (default)
2. Quality-based (if quality tracker available with historical data)
3. Consensus (majority agreement)
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from llm_provider.base import LLMProvider
from llm_provider.types import ExtractedEntities

if TYPE_CHECKING:
    from llm_orchestrator.quality_tracker import QualityTracker

logger = logging.getLogger(__name__)


class AllProvidersStrategy:
    """Strategy that calls all providers and collects metrics from all.

    This is the recommended strategy for production use when you want:
    - Continuous quality metrics collection from all providers
    - Data-driven provider comparison and routing decisions
    - Maximum observability into provider performance

    Args:
        provider_names: List of provider names to use
        selection_mode: How to select result ("highest_confidence", "quality_based", "consensus")
        quality_tracker: Optional quality tracker for quality-based selection
    """

    def __init__(
        self,
        provider_names: list[str],
        selection_mode: str = "highest_confidence",
        quality_tracker: Optional["QualityTracker"] = None,
    ):
        """Initialize All Providers Strategy.

        Args:
            provider_names: List of provider names to call
            selection_mode: Selection criterion for final result
            quality_tracker: Optional quality tracker for selection
        """
        self.provider_names = provider_names
        self.selection_mode = selection_mode
        self.quality_tracker = quality_tracker

        # Store last execution results for metrics collection
        self.last_all_results: dict[str, ExtractedEntities] = {}
        self.last_all_failures: dict[str, Exception] = {}

        logger.info(
            f"Initialized AllProvidersStrategy with {len(provider_names)} providers: "
            f"{provider_names}, selection_mode={selection_mode}"
        )

    async def _call_provider_async(
        self,
        provider: LLMProvider,
        provider_name: str,
        email_text: str,
        company_context: Optional[str],
        email_id: Optional[str],
    ) -> tuple[str, Optional[ExtractedEntities], Optional[Exception]]:
        """Call a single provider asynchronously.

        Args:
            provider: Provider instance
            provider_name: Provider name for logging
            email_text: Email text to extract from
            company_context: Optional company context
            email_id: Optional email ID

        Returns:
            Tuple of (provider_name, extracted_entities or None, exception or None)
        """
        try:
            logger.debug(f"Calling provider {provider_name}")
            entities = provider.extract_entities(
                email_text=email_text,
                company_context=company_context,
                email_id=email_id,
            )
            logger.info(
                f"Provider {provider_name} succeeded "
                f"(confidence: {self._calculate_avg_confidence(entities):.2%})"
            )
            return (provider_name, entities, None)

        except Exception as e:
            logger.warning(f"Provider {provider_name} failed: {e}")
            return (provider_name, None, e)

    def _calculate_avg_confidence(self, entities: ExtractedEntities) -> float:
        """Calculate average confidence across all fields.

        Args:
            entities: Extracted entities

        Returns:
            Average confidence (0.0-1.0)
        """
        return (
            entities.confidence.person
            + entities.confidence.startup
            + entities.confidence.partner
            + entities.confidence.details
            + entities.confidence.date
        ) / 5

    def _select_best_result(
        self,
        results: dict[str, ExtractedEntities],
    ) -> tuple[str, ExtractedEntities]:
        """Select best result from multiple provider results.

        Args:
            results: Dictionary of provider_name → ExtractedEntities

        Returns:
            Tuple of (selected_provider_name, selected_entities)

        Raises:
            ValueError: If no results available
        """
        if not results:
            raise ValueError("No successful extractions to select from")

        if self.selection_mode == "quality_based" and self.quality_tracker:
            # Use historical quality metrics for selection
            return self._select_by_quality(results)

        elif self.selection_mode == "consensus":
            # Use majority agreement (similar to consensus strategy)
            return self._select_by_consensus(results)

        else:
            # Default: highest confidence
            return self._select_by_confidence(results)

    def _select_by_confidence(
        self, results: dict[str, ExtractedEntities]
    ) -> tuple[str, ExtractedEntities]:
        """Select result with highest average confidence.

        Args:
            results: Provider results

        Returns:
            Provider name and entities with highest confidence
        """
        best_provider = max(
            results.items(),
            key=lambda item: self._calculate_avg_confidence(item[1]),
        )

        logger.info(
            f"Selected {best_provider[0]} by confidence "
            f"({self._calculate_avg_confidence(best_provider[1]):.2%})"
        )

        return best_provider

    def _select_by_quality(
        self, results: dict[str, ExtractedEntities]
    ) -> tuple[str, ExtractedEntities]:
        """Select result from provider with best historical quality.

        Args:
            results: Provider results

        Returns:
            Provider name and entities from highest quality provider
        """
        if not self.quality_tracker:
            logger.warning(
                "Quality tracker not available, falling back to confidence selection"
            )
            return self._select_by_confidence(results)

        # Get quality metrics for available providers
        provider_quality = {}
        for provider_name in results.keys():
            metrics = self.quality_tracker.get_metrics(provider_name)
            if metrics and metrics.total_extractions > 0:
                # Calculate quality score (same formula as comparison)
                quality_score = (
                    0.4 * metrics.average_overall_confidence
                    + 0.3 * (metrics.average_field_completeness / 100)
                    + 0.3 * (metrics.validation_success_rate / 100)
                )
                provider_quality[provider_name] = quality_score

        if not provider_quality:
            logger.warning(
                "No historical quality metrics available, "
                "falling back to confidence selection"
            )
            return self._select_by_confidence(results)

        # Select provider with highest quality score
        best_provider_name = max(provider_quality.items(), key=lambda x: x[1])[0]

        logger.info(
            f"Selected {best_provider_name} by quality "
            f"(score: {provider_quality[best_provider_name]:.2f})"
        )

        return (best_provider_name, results[best_provider_name])

    def _select_by_consensus(
        self, results: dict[str, ExtractedEntities]
    ) -> tuple[str, ExtractedEntities]:
        """Select result based on majority agreement across providers.

        For simplicity, this currently uses confidence. Full consensus logic
        would require fuzzy matching across all fields (complex).

        Args:
            results: Provider results

        Returns:
            Provider name and entities selected by consensus
        """
        # TODO: Implement full fuzzy consensus logic
        # For now, fall back to confidence
        logger.info("Consensus selection not fully implemented, using confidence")
        return self._select_by_confidence(results)

    def execute(
        self,
        email_text: str,
        providers: dict[str, LLMProvider],
        health_tracker=None,  # Not used but required for signature compatibility
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> tuple[ExtractedEntities, str]:
        """Execute all providers strategy.

        Calls ALL providers in parallel, collects results and metrics from all,
        then selects the best result based on configured selection mode.

        Args:
            email_text: Email content to extract from
            providers: Available provider instances
            health_tracker: Not used (providers already filtered)
            company_context: Optional company context
            email_id: Optional email ID

        Returns:
            Tuple of (extracted_entities, provider_name)

        Raises:
            Exception: If all providers fail
        """
        logger.info(
            f"Executing AllProvidersStrategy with {len(self.provider_names)} providers"
        )

        # Filter to requested providers
        available_providers = {
            name: providers[name] for name in self.provider_names if name in providers
        }

        if not available_providers:
            raise ValueError(
                f"No providers available from requested: {self.provider_names}"
            )

        # Call all providers in parallel (asyncio)
        loop = asyncio.get_event_loop()
        tasks = [
            self._call_provider_async(
                provider, name, email_text, company_context, email_id
            )
            for name, provider in available_providers.items()
        ]

        # Gather results (don't fail fast - collect all results/errors)
        all_results = loop.run_until_complete(
            asyncio.gather(*tasks, return_exceptions=False)
        )

        # Separate successful and failed results
        successful_results: dict[str, ExtractedEntities] = {}
        failures: dict[str, Exception] = {}

        for provider_name, entities, error in all_results:
            if error is None and entities is not None:
                successful_results[provider_name] = entities
            else:
                failures[provider_name] = error or Exception("Unknown error")

        # Store results for external access (e.g., metrics collection)
        self.last_all_results = successful_results
        self.last_all_failures = failures

        # Log summary
        logger.info(
            f"Results: {len(successful_results)} succeeded, {len(failures)} failed"
        )
        if failures:
            logger.warning(f"Failed providers: {list(failures.keys())}")

        # Check if any provider succeeded
        if not successful_results:
            error_msg = "All providers failed: " + ", ".join(
                f"{name}: {error}" for name, error in failures.items()
            )
            logger.error(error_msg)
            raise Exception(error_msg)

        # Select best result
        selected_provider, selected_entities = self._select_best_result(
            successful_results
        )

        logger.info(
            f"Selected result from {selected_provider} out of "
            f"{len(successful_results)} successful providers"
        )

        # Note: Quality metrics are tracked automatically by the orchestrator
        # after this method returns for the selected provider, but we also
        # want to track metrics for ALL providers that succeeded
        # This will be handled by the orchestrator calling record_quality for each

        return (selected_entities, selected_provider)
