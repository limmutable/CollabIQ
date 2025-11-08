"""LLM Orchestrator for multi-provider coordination.

This module provides the main orchestrator class that coordinates multiple
LLM providers using configurable strategies (failover, consensus, best-match).
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from src.llm_orchestrator.exceptions import InvalidProviderError, InvalidStrategyError
from src.llm_orchestrator.strategies.failover import FailoverStrategy
from src.llm_orchestrator.types import (
    OrchestrationConfig,
    ProviderConfig,
    ProviderStatus,
)
from src.llm_provider.base import LLMProvider
from src.llm_provider.types import ExtractedEntities

if TYPE_CHECKING:
    from src.llm_adapters.claude_adapter import ClaudeAdapter
    from src.llm_adapters.gemini_adapter import GeminiAdapter
    from src.llm_adapters.health_tracker import HealthTracker
    from src.llm_adapters.openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Orchestrate multiple LLM providers with configurable strategies.

    The orchestrator provides a unified interface for entity extraction across
    multiple providers, handling failover, health monitoring, and strategy selection.

    Example:
        >>> from src.llm_orchestrator.orchestrator import LLMOrchestrator
        >>> from src.llm_orchestrator.types import OrchestrationConfig
        >>>
        >>> config = OrchestrationConfig(
        ...     default_strategy="failover",
        ...     provider_priority=["gemini", "claude", "openai"]
        ... )
        >>> orchestrator = LLMOrchestrator.from_config(config)
        >>> entities = orchestrator.extract_entities("email text")
    """

    def __init__(
        self,
        providers: dict[str, LLMProvider],
        config: OrchestrationConfig,
        health_tracker: "HealthTracker",
    ):
        """Initialize LLM Orchestrator.

        Args:
            providers: Dictionary mapping provider_name → LLMProvider instance
            config: Orchestration configuration
            health_tracker: Health tracking instance
        """
        self.providers = providers
        self.config = config
        self.health_tracker = health_tracker

        # Initialize strategies
        self._strategies = {
            "failover": FailoverStrategy(priority_order=config.provider_priority)
        }

        self._active_strategy = config.default_strategy

        logger.info(
            f"Initialized LLMOrchestrator with {len(providers)} providers: "
            f"{list(providers.keys())}, strategy={config.default_strategy}"
        )

    @classmethod
    def from_config(
        cls,
        config: OrchestrationConfig,
        provider_configs: Optional[dict[str, ProviderConfig]] = None,
        data_dir: str | Path = "data/llm_health",
    ) -> "LLMOrchestrator":
        """Create orchestrator from configuration with automatic provider setup.

        Args:
            config: Orchestration configuration
            provider_configs: Optional provider configurations (uses defaults if None)
            data_dir: Directory for health metrics storage

        Returns:
            Configured LLMOrchestrator instance

        Example:
            >>> config = OrchestrationConfig(
            ...     default_strategy="failover",
            ...     provider_priority=["gemini", "claude"]
            ... )
            >>> orchestrator = LLMOrchestrator.from_config(config)
        """
        # Import adapters here to avoid circular import
        from src.llm_adapters.claude_adapter import ClaudeAdapter
        from src.llm_adapters.gemini_adapter import GeminiAdapter
        from src.llm_adapters.health_tracker import HealthTracker
        from src.llm_adapters.openai_adapter import OpenAIAdapter

        # Use default provider configs if not provided
        if provider_configs is None:
            provider_configs = cls._get_default_provider_configs()

        # Initialize providers
        providers = {}
        for name, pconfig in provider_configs.items():
            if not pconfig.enabled:
                logger.info(f"Skipping disabled provider: {name}")
                continue

            # Get API key from environment
            api_key = os.getenv(pconfig.api_key_env_var)
            if not api_key:
                logger.warning(
                    f"API key not found for {name} "
                    f"(env var: {pconfig.api_key_env_var}), skipping"
                )
                continue

            # Initialize provider adapter
            if name == "gemini":
                providers[name] = GeminiAdapter(
                    api_key=api_key,
                    model=pconfig.model_id,
                    timeout=int(pconfig.timeout_seconds),
                    max_retries=pconfig.max_retries,
                )
            elif name == "claude":
                providers[name] = ClaudeAdapter(
                    api_key=api_key,
                    model=pconfig.model_id,
                    timeout=int(pconfig.timeout_seconds),
                    max_retries=pconfig.max_retries,
                )
            elif name == "openai":
                providers[name] = OpenAIAdapter(
                    api_key=api_key,
                    model=pconfig.model_id,
                    timeout=int(pconfig.timeout_seconds),
                    max_retries=pconfig.max_retries,
                )
            else:
                logger.warning(f"Unknown provider type: {name}, skipping")

        # Initialize health tracker
        health_tracker = HealthTracker(
            data_dir=data_dir,
            unhealthy_threshold=config.unhealthy_threshold,
            circuit_breaker_timeout_seconds=config.circuit_breaker_timeout_seconds,
            half_open_max_calls=config.half_open_max_calls,
        )

        return cls(
            providers=providers, config=config, health_tracker=health_tracker
        )

    @staticmethod
    def _get_default_provider_configs() -> dict[str, ProviderConfig]:
        """Get default provider configurations.

        Returns:
            Dictionary mapping provider_name → ProviderConfig
        """
        return {
            "gemini": ProviderConfig(
                provider_name="gemini",
                display_name="Google Gemini 2.0 Flash",
                model_id="gemini-2.0-flash-exp",
                api_key_env_var="GEMINI_API_KEY",
                enabled=True,
                priority=1,
                timeout_seconds=60.0,
                max_retries=3,
                input_token_price=0.0,  # Free tier
                output_token_price=0.0,
            ),
            "claude": ProviderConfig(
                provider_name="claude",
                display_name="Claude Sonnet 4.5",
                model_id="claude-sonnet-4-5-20250929",
                api_key_env_var="ANTHROPIC_API_KEY",
                enabled=True,
                priority=2,
                timeout_seconds=60.0,
                max_retries=3,
                input_token_price=3.0,  # $3 per 1M input tokens
                output_token_price=15.0,  # $15 per 1M output tokens
            ),
            "openai": ProviderConfig(
                provider_name="openai",
                display_name="GPT-5 Mini",
                model_id="gpt-5-mini",
                api_key_env_var="OPENAI_API_KEY",
                enabled=True,
                priority=3,
                timeout_seconds=60.0,
                max_retries=3,
                input_token_price=0.15,  # $0.15 per 1M input tokens
                output_token_price=0.60,  # $0.60 per 1M output tokens
            ),
        }

    def extract_entities(
        self,
        email_text: str,
        strategy: Optional[str] = None,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> ExtractedEntities:
        """Extract entities from email text using configured orchestration strategy.

        Args:
            email_text: Cleaned email body
            strategy: Override default strategy (one of: failover, consensus, best_match)
            company_context: Optional company context for matching
            email_id: Optional email ID

        Returns:
            ExtractedEntities with provider metadata populated

        Raises:
            AllProvidersFailedError: All enabled providers failed
            NoHealthyProvidersError: No healthy providers available
            OrchestrationTimeoutError: Overall timeout exceeded
            InvalidStrategyError: Unknown strategy specified

        Example:
            >>> entities = orchestrator.extract_entities("어제 신세계와 본봄 킥오프")
            >>> print(f"Used provider: {entities.provider_name}")
        """
        # Determine strategy to use
        strategy_name = strategy or self._active_strategy

        if strategy_name not in self._strategies:
            raise InvalidStrategyError(
                f"Unknown strategy: {strategy_name}", strategy_name=strategy_name
            )

        # Execute strategy
        strategy_impl = self._strategies[strategy_name]
        entities, provider_used = strategy_impl.execute(
            providers=self.providers,
            email_text=email_text,
            health_tracker=self.health_tracker,
            company_context=company_context,
            email_id=email_id,
        )

        logger.info(
            f"Successfully extracted entities using {provider_used} "
            f"(strategy={strategy_name})"
        )

        return entities

    def get_provider_status(self) -> dict[str, ProviderStatus]:
        """Get current status of all configured providers.

        Returns:
            Dictionary mapping provider_name → ProviderStatus

        Example:
            >>> status = orchestrator.get_provider_status()
            >>> for name, pstatus in status.items():
            ...     print(f"{name}: {pstatus.health_status}, "
            ...           f"success_rate={pstatus.success_rate:.2f}")
        """
        status = {}

        for provider_name in self.providers.keys():
            metrics = self.health_tracker.get_metrics(provider_name)

            status[provider_name] = ProviderStatus(
                provider_name=provider_name,
                health_status=metrics.health_status,
                enabled=True,  # If in self.providers, it's enabled
                success_rate=metrics.success_rate,
                average_response_time_ms=metrics.average_response_time_ms,
                total_api_calls=metrics.success_count + metrics.failure_count,
                last_success=metrics.last_success_timestamp,
                last_failure=metrics.last_failure_timestamp,
                circuit_breaker_state=metrics.circuit_breaker_state,
            )

        return status

    def set_strategy(self, strategy_type: str) -> None:
        """Change the active orchestration strategy.

        Args:
            strategy_type: Strategy to activate (failover, consensus, best_match)

        Raises:
            InvalidStrategyError: If strategy_type not recognized

        Example:
            >>> orchestrator.set_strategy("failover")
        """
        if strategy_type not in self._strategies:
            raise InvalidStrategyError(
                f"Unknown strategy: {strategy_type}", strategy_name=strategy_type
            )

        self._active_strategy = strategy_type
        logger.info(f"Switched orchestration strategy to: {strategy_type}")

    def test_provider(self, provider_name: str) -> bool:
        """Test connectivity and health of a specific provider.

        Args:
            provider_name: Provider to test (gemini, claude, openai)

        Returns:
            True if provider is healthy and responsive, False otherwise

        Raises:
            InvalidProviderError: If provider_name not configured

        Example:
            >>> if orchestrator.test_provider("claude"):
            ...     print("Claude is healthy")
        """
        if provider_name not in self.providers:
            raise InvalidProviderError(
                f"Provider not configured: {provider_name}",
                provider_name=provider_name,
            )

        # Simple health check: verify provider is healthy in tracker
        is_healthy = self.health_tracker.is_healthy(provider_name)

        logger.info(
            f"Provider {provider_name} health check: "
            f"{'healthy' if is_healthy else 'unhealthy'}"
        )

        return is_healthy

    def get_active_strategy(self) -> str:
        """Get the currently active strategy name.

        Returns:
            Active strategy name (e.g., "failover")
        """
        return self._active_strategy

    def get_available_providers(self) -> list[str]:
        """Get list of configured provider names.

        Returns:
            List of provider names (e.g., ["gemini", "claude", "openai"])
        """
        return list(self.providers.keys())
