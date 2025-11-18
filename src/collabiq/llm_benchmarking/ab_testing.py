"""A/B testing framework for comparing prompt variations and LLM providers.

This module provides tools to compare different prompt variations
and LLM providers to identify which performs better.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from collabiq.llm_benchmarking.metrics import (
    AggregatedMetrics,
    ComparisonResult,
)
from collabiq.llm_benchmarking.suite import BenchmarkSuite
from llm_provider.base import LLMProvider

logger = logging.getLogger(__name__)


class ABTestFramework:
    """A/B testing framework for LLM prompt and provider comparison.

    This class provides methods to run A/B tests comparing:
    - Different prompt variations with the same provider
    - Different providers with the same prompt
    - Combinations of prompts and providers

    Examples:
        >>> framework = ABTestFramework()
        >>> result = framework.compare_prompts(
        ...     provider=gemini_adapter,
        ...     provider_name="gemini",
        ...     baseline_prompt="baseline",
        ...     comparison_prompt="korean_optimized",
        ...     test_data=test_samples
        ... )
        >>> print(f"Winner: {result.winner}")
        >>> print(f"Accuracy improvement: {result.accuracy_improvement}%")
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize A/B testing framework.

        Args:
            output_dir: Directory to save results (default: data/test_metrics/ab_tests/)
        """
        self.output_dir = output_dir or Path("data/test_metrics/ab_tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.suite = BenchmarkSuite(output_dir=output_dir)

    def compare_prompts(
        self,
        provider: LLMProvider,
        provider_name: str,
        baseline_prompt: str,
        comparison_prompt: str,
        test_data: List[Dict[str, Any]],
    ) -> ComparisonResult:
        """Compare two prompt variations using the same provider.

        Args:
            provider: LLM provider instance
            provider_name: Provider name (gemini, claude, openai)
            baseline_prompt: Baseline prompt variation ID
            comparison_prompt: Comparison prompt variation ID
            test_data: List of test samples

        Returns:
            ComparisonResult with performance comparison

        Examples:
            >>> result = framework.compare_prompts(
            ...     provider=gemini_adapter,
            ...     provider_name="gemini",
            ...     baseline_prompt="baseline",
            ...     comparison_prompt="korean_optimized",
            ...     test_data=test_samples
            ... )
        """
        logger.info(
            f"Starting A/B test: {baseline_prompt} vs {comparison_prompt} on {provider_name}"
        )

        # Run baseline
        logger.info(f"Running baseline: {baseline_prompt}")
        baseline_results, baseline_metrics = self.suite.run_benchmark(
            provider=provider,
            provider_name=provider_name,
            test_data=test_data,
            prompt_id=baseline_prompt,
            save_results=True,
        )

        # Run comparison
        logger.info(f"Running comparison: {comparison_prompt}")
        comparison_results, comparison_metrics = self.suite.run_benchmark(
            provider=provider,
            provider_name=provider_name,
            test_data=test_data,
            prompt_id=comparison_prompt,
            save_results=True,
        )

        # Calculate improvements
        accuracy_improvement = self._calculate_improvement(
            baseline_metrics.avg_accuracy, comparison_metrics.avg_accuracy
        )
        confidence_improvement = self._calculate_improvement(
            baseline_metrics.avg_confidence, comparison_metrics.avg_confidence
        )
        speed_improvement = self._calculate_improvement(
            baseline_metrics.avg_response_time,
            comparison_metrics.avg_response_time,
            lower_is_better=True,
        )

        # Determine winner
        winner = self._determine_winner(
            baseline_metrics,
            comparison_metrics,
            accuracy_weight=0.5,
            confidence_weight=0.3,
            speed_weight=0.2,
        )

        result = ComparisonResult(
            baseline_id=baseline_prompt,
            comparison_id=comparison_prompt,
            baseline_metrics=baseline_metrics,
            comparison_metrics=comparison_metrics,
            accuracy_improvement=accuracy_improvement,
            confidence_improvement=confidence_improvement,
            speed_improvement=speed_improvement,
            winner=winner,
        )

        logger.info(
            f"A/B test complete. Winner: {winner}, "
            f"Accuracy: {accuracy_improvement:+.1f}%, "
            f"Confidence: {confidence_improvement:+.1f}%, "
            f"Speed: {speed_improvement:+.1f}%"
        )

        return result

    def compare_providers(
        self,
        baseline_provider: LLMProvider,
        baseline_name: str,
        comparison_provider: LLMProvider,
        comparison_name: str,
        test_data: List[Dict[str, Any]],
        prompt_id: str = "baseline",
    ) -> ComparisonResult:
        """Compare two LLM providers using the same prompt.

        Args:
            baseline_provider: Baseline provider instance
            baseline_name: Baseline provider name
            comparison_provider: Comparison provider instance
            comparison_name: Comparison provider name
            test_data: List of test samples
            prompt_id: Prompt variation ID to use for both

        Returns:
            ComparisonResult with performance comparison

        Examples:
            >>> result = framework.compare_providers(
            ...     baseline_provider=gemini_adapter,
            ...     baseline_name="gemini",
            ...     comparison_provider=claude_adapter,
            ...     comparison_name="claude",
            ...     test_data=test_samples,
            ...     prompt_id="korean_optimized"
            ... )
        """
        logger.info(
            f"Starting provider comparison: {baseline_name} vs {comparison_name}"
        )

        # Run baseline provider
        logger.info(f"Running baseline provider: {baseline_name}")
        baseline_results, baseline_metrics = self.suite.run_benchmark(
            provider=baseline_provider,
            provider_name=baseline_name,
            test_data=test_data,
            prompt_id=prompt_id,
            save_results=True,
        )

        # Run comparison provider
        logger.info(f"Running comparison provider: {comparison_name}")
        comparison_results, comparison_metrics = self.suite.run_benchmark(
            provider=comparison_provider,
            provider_name=comparison_name,
            test_data=test_data,
            prompt_id=prompt_id,
            save_results=True,
        )

        # Calculate improvements
        accuracy_improvement = self._calculate_improvement(
            baseline_metrics.avg_accuracy, comparison_metrics.avg_accuracy
        )
        confidence_improvement = self._calculate_improvement(
            baseline_metrics.avg_confidence, comparison_metrics.avg_confidence
        )
        speed_improvement = self._calculate_improvement(
            baseline_metrics.avg_response_time,
            comparison_metrics.avg_response_time,
            lower_is_better=True,
        )

        # Determine winner
        winner = self._determine_winner(
            baseline_metrics,
            comparison_metrics,
            accuracy_weight=0.5,
            confidence_weight=0.3,
            speed_weight=0.2,
        )

        result = ComparisonResult(
            baseline_id=baseline_name,
            comparison_id=comparison_name,
            baseline_metrics=baseline_metrics,
            comparison_metrics=comparison_metrics,
            accuracy_improvement=accuracy_improvement,
            confidence_improvement=confidence_improvement,
            speed_improvement=speed_improvement,
            winner=winner,
        )

        logger.info(
            f"Provider comparison complete. Winner: {winner}, "
            f"Accuracy: {accuracy_improvement:+.1f}%, "
            f"Confidence: {confidence_improvement:+.1f}%, "
            f"Speed: {speed_improvement:+.1f}%"
        )

        return result

    def _calculate_improvement(
        self,
        baseline_value: float,
        comparison_value: float,
        lower_is_better: bool = False,
    ) -> float:
        """Calculate percentage improvement.

        Args:
            baseline_value: Baseline metric value
            comparison_value: Comparison metric value
            lower_is_better: True if lower values are better (e.g., response time)

        Returns:
            Percentage improvement (positive = better, negative = worse)
        """
        if baseline_value == 0:
            return 0.0

        if lower_is_better:
            # For metrics where lower is better (e.g., response time)
            improvement = ((baseline_value - comparison_value) / baseline_value) * 100
        else:
            # For metrics where higher is better (e.g., accuracy)
            improvement = ((comparison_value - baseline_value) / baseline_value) * 100

        return improvement

    def _determine_winner(
        self,
        baseline_metrics: AggregatedMetrics,
        comparison_metrics: AggregatedMetrics,
        accuracy_weight: float = 0.5,
        confidence_weight: float = 0.3,
        speed_weight: float = 0.2,
    ) -> str:
        """Determine which variant performs better overall.

        Args:
            baseline_metrics: Baseline metrics
            comparison_metrics: Comparison metrics
            accuracy_weight: Weight for accuracy in overall score
            confidence_weight: Weight for confidence in overall score
            speed_weight: Weight for speed in overall score

        Returns:
            ID of the winning variant (baseline or comparison)
        """
        # Calculate weighted scores
        baseline_score = (
            baseline_metrics.avg_accuracy * accuracy_weight
            + baseline_metrics.avg_confidence * confidence_weight
            # Invert speed (lower is better)
            + (1.0 / (baseline_metrics.avg_response_time + 0.01)) * speed_weight
        )

        comparison_score = (
            comparison_metrics.avg_accuracy * accuracy_weight
            + comparison_metrics.avg_confidence * confidence_weight
            # Invert speed (lower is better)
            + (1.0 / (comparison_metrics.avg_response_time + 0.01)) * speed_weight
        )

        if comparison_score > baseline_score:
            return comparison_metrics.prompt_id
        else:
            return baseline_metrics.prompt_id


def compare_prompts(
    provider: LLMProvider,
    provider_name: str,
    baseline_prompt: str,
    comparison_prompt: str,
    test_data: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Convenience function to compare two prompt variations.

    Args:
        provider: LLM provider instance
        provider_name: Provider name
        baseline_prompt: Baseline prompt ID
        comparison_prompt: Comparison prompt ID
        test_data: List of test samples
        output_dir: Output directory for results

    Returns:
        Dictionary with comparison results

    Examples:
        >>> from src.llm_adapters.gemini_adapter import GeminiAdapter
        >>> adapter = GeminiAdapter(api_key="...")
        >>> result = compare_prompts(
        ...     provider=adapter,
        ...     provider_name="gemini",
        ...     baseline_prompt="baseline",
        ...     comparison_prompt="korean_optimized",
        ...     test_data=test_samples
        ... )
    """
    framework = ABTestFramework(output_dir=output_dir)
    result = framework.compare_prompts(
        provider=provider,
        provider_name=provider_name,
        baseline_prompt=baseline_prompt,
        comparison_prompt=comparison_prompt,
        test_data=test_data,
    )

    return {
        "baseline": baseline_prompt,
        "comparison": comparison_prompt,
        "winner": result.winner,
        "accuracy_improvement": result.accuracy_improvement,
        "confidence_improvement": result.confidence_improvement,
        "speed_improvement": result.speed_improvement,
        "baseline_metrics": result.baseline_metrics.model_dump(),
        "comparison_metrics": result.comparison_metrics.model_dump(),
    }


# Public API
__all__ = [
    "ABTestFramework",
    "compare_prompts",
]
