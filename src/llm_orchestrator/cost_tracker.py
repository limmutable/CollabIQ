"""Cost tracking for LLM providers with file-based persistence.

This module implements cost tracking for LLM API usage, recording tokens consumed
and calculating costs based on provider-specific pricing. Metrics are persisted
to disk across application restarts.
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.llm_orchestrator.types import CostMetricsSummary, ProviderConfig

logger = logging.getLogger(__name__)


class CostTracker:
    """Track LLM provider costs with persistent state.

    This class monitors API usage, token consumption, and financial costs per provider.
    State is persisted to disk across restarts using atomic file writes.

    Attributes:
        data_dir: Directory for cost metrics JSON storage
        provider_configs: Dictionary mapping provider_name → ProviderConfig for pricing

    Example:
        >>> provider_configs = {
        ...     "claude": ProviderConfig(
        ...         provider_name="claude",
        ...         input_token_price=3.0,
        ...         output_token_price=15.0,
        ...         ...
        ...     )
        ... }
        >>> tracker = CostTracker(
        ...     data_dir="data/llm_health",
        ...     provider_configs=provider_configs
        ... )
        >>> tracker.record_usage("claude", input_tokens=1000, output_tokens=500)
        >>> metrics = tracker.get_metrics("claude")
        >>> print(f"Total cost: ${metrics.total_cost_usd:.4f}")
    """

    def __init__(
        self,
        data_dir: str | Path = "data/llm_health",
        provider_configs: dict[str, ProviderConfig] | None = None,
    ):
        """Initialize CostTracker.

        Args:
            data_dir: Directory for cost metrics JSON storage
            provider_configs: Provider configurations with pricing info (defaults to empty)
        """
        self.data_dir = Path(data_dir)
        self.provider_configs = provider_configs or {}

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Metrics file path
        self.metrics_file = self.data_dir / "cost_metrics.json"

        # Load existing metrics or initialize defaults
        self.metrics = self._load_metrics()

        logger.info(
            f"Initialized CostTracker: data_dir={data_dir}, "
            f"providers={list(self.provider_configs.keys())}"
        )

    def record_usage(
        self,
        provider_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record API usage and calculate cost.

        Args:
            provider_name: Provider identifier (gemini, claude, openai)
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens consumed

        Side Effects:
            - Increments total_api_calls
            - Adds to total_input_tokens and total_output_tokens
            - Calculates and adds to total_cost_usd using provider pricing
            - Updates average_cost_per_email
            - Sets last_updated to current UTC time
            - Persists metrics to JSON file

        Cost Calculation:
            cost = (input_tokens / 1_000_000) * input_token_price
                 + (output_tokens / 1_000_000) * output_token_price

        Note:
            If provider_config not found, cost is calculated as 0.0
        """
        metrics = self.get_metrics(provider_name)

        # Update counters
        metrics.total_api_calls += 1
        metrics.total_input_tokens += input_tokens
        metrics.total_output_tokens += output_tokens
        metrics.total_tokens = metrics.total_input_tokens + metrics.total_output_tokens

        # Calculate cost for this call
        call_cost = self._calculate_cost(provider_name, input_tokens, output_tokens)
        metrics.total_cost_usd += call_cost

        # Update average cost per email (assumes 1 API call per email)
        if metrics.total_api_calls > 0:
            metrics.average_cost_per_email = (
                metrics.total_cost_usd / metrics.total_api_calls
            )

        # Update timestamp
        metrics.last_updated = datetime.now(timezone.utc)

        # Persist to disk
        self._save_metrics()

        logger.debug(
            f"Recorded usage for {provider_name}: "
            f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
            f"cost=${call_cost:.6f}, total_cost=${metrics.total_cost_usd:.4f}"
        )

    def get_metrics(self, provider_name: str) -> CostMetricsSummary:
        """Get current cost metrics for a provider.

        Args:
            provider_name: Provider identifier

        Returns:
            CostMetricsSummary for the specified provider
        """
        if provider_name not in self.metrics:
            # Initialize default metrics for new provider
            self.metrics[provider_name] = CostMetricsSummary(
                provider_name=provider_name
            )
            self._save_metrics()

        return self.metrics[provider_name]

    def get_all_metrics(self) -> dict[str, CostMetricsSummary]:
        """Get cost metrics for all tracked providers.

        Returns:
            Dictionary mapping provider_name → CostMetricsSummary
        """
        return self.metrics.copy()

    def reset_metrics(self, provider_name: str) -> None:
        """Reset cost metrics for a provider (for testing or manual reset).

        Args:
            provider_name: Provider identifier

        Side Effects:
            - Resets all counters to 0
            - Resets total_cost_usd to 0.0
            - Updates last_updated timestamp
            - Persists to JSON file
        """
        self.metrics[provider_name] = CostMetricsSummary(
            provider_name=provider_name,
            last_updated=datetime.now(timezone.utc),
        )

        self._save_metrics()

        logger.info(f"Reset cost metrics for {provider_name}")

    def _calculate_cost(
        self, provider_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost for a single API call.

        Args:
            provider_name: Provider identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Formula:
            cost = (input_tokens / 1_000_000) * input_token_price
                 + (output_tokens / 1_000_000) * output_token_price
        """
        if provider_name not in self.provider_configs:
            logger.warning(
                f"Provider config not found for {provider_name}, "
                f"using $0.00 for cost calculation"
            )
            return 0.0

        config = self.provider_configs[provider_name]

        input_cost = (input_tokens / 1_000_000) * config.input_token_price
        output_cost = (output_tokens / 1_000_000) * config.output_token_price

        return input_cost + output_cost

    def _load_metrics(self) -> dict[str, CostMetricsSummary]:
        """Load cost metrics from JSON file.

        Returns:
            Dictionary mapping provider_name → CostMetricsSummary
        """
        if not self.metrics_file.exists():
            logger.info("No existing cost metrics found, initializing defaults")
            return {}

        try:
            with open(self.metrics_file, "r") as f:
                data = json.load(f)

            # Parse JSON into CostMetricsSummary objects
            metrics = {}
            for provider_name, metrics_dict in data.items():
                # Convert ISO timestamp to datetime object
                if metrics_dict.get("last_updated"):
                    metrics_dict["last_updated"] = datetime.fromisoformat(
                        metrics_dict["last_updated"]
                    )

                metrics[provider_name] = CostMetricsSummary(**metrics_dict)

            logger.info(f"Loaded cost metrics for {len(metrics)} providers")
            return metrics

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to load cost metrics: {e}, initializing defaults")
            return {}

    def _save_metrics(self) -> None:
        """Save cost metrics to JSON file using atomic write.

        Uses temp file + rename to ensure atomic writes and prevent corruption.
        """
        # Convert metrics to JSON-serializable dict
        data = {}
        for provider_name, metrics in self.metrics.items():
            metrics_dict = metrics.model_dump()

            # Convert datetime object to ISO format string
            if metrics_dict.get("last_updated"):
                metrics_dict["last_updated"] = metrics_dict["last_updated"].isoformat()

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
            logger.error(f"Failed to save cost metrics: {e}")
            raise
