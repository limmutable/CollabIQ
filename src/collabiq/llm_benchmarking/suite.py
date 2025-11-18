"""Benchmarking suite for LLM performance evaluation.

This module provides tools to systematically evaluate LLM performance
on Korean and English text extraction tasks.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from collabiq.llm_benchmarking.metrics import (
    AggregatedMetrics,
    BenchmarkResult,
    aggregate_results,
    calculate_accuracy,
)
from collabiq.llm_benchmarking.prompts import get_prompt_by_id, list_prompt_ids
from llm_provider.base import LLMProvider
from llm_provider.exceptions import LLMAPIError
from llm_provider.types import ExtractedEntities

logger = logging.getLogger(__name__)


class BenchmarkSuite:
    """Benchmarking suite for LLM performance testing.

    This class provides methods to run benchmarks across different
    LLM providers, prompt variations, and test datasets.

    Examples:
        >>> from src.llm_adapters.gemini_adapter import GeminiAdapter
        >>> suite = BenchmarkSuite()
        >>> adapter = GeminiAdapter(api_key="...")
        >>> results = suite.run_benchmark(
        ...     provider=adapter,
        ...     provider_name="gemini",
        ...     test_data=test_samples,
        ...     prompt_id="korean_optimized"
        ... )
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize benchmarking suite.

        Args:
            output_dir: Directory to save benchmark results (default: data/test_metrics/benchmarks/)
        """
        self.output_dir = output_dir or Path("data/test_metrics/benchmarks")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_single_test(
        self,
        provider: LLMProvider,
        provider_name: str,
        email_text: str,
        expected_entities: Optional[Dict[str, Any]] = None,
        prompt_id: str = "baseline",
        custom_prompt: Optional[str] = None,
    ) -> BenchmarkResult:
        """Run a single benchmark test.

        Args:
            provider: LLM provider instance
            provider_name: Provider name (gemini, claude, openai)
            email_text: Email text to extract from
            expected_entities: Ground truth entities for accuracy calculation
            prompt_id: Prompt variation ID to use
            custom_prompt: Custom prompt template (overrides prompt_id)

        Returns:
            BenchmarkResult with extraction results and metrics

        Examples:
            >>> result = suite.run_single_test(
            ...     provider=gemini_adapter,
            ...     provider_name="gemini",
            ...     email_text="어제 신세계와 본봄 킥오프",
            ...     expected_entities={"startup_name": "본봄"},
            ...     prompt_id="korean_optimized"
            ... )
        """
        test_id = str(uuid4())
        start_time = time.time()

        try:
            # Get prompt template
            if custom_prompt:
                prompt_template = custom_prompt
            else:
                prompt_template = get_prompt_by_id(prompt_id)

            # Format prompt with email text
            # Note: For now, we use the provider's built-in prompting
            # In future, we could inject custom prompts if adapters support it
            entities = provider.extract_entities(email_text)

            response_time = time.time() - start_time

            # Extract as dict
            extracted_dict = {
                "person_in_charge": entities.person_in_charge,
                "startup_name": entities.startup_name,
                "partner_org": entities.partner_org,
                "details": entities.details,
                "date": entities.date.strftime("%Y-%m-%d") if entities.date else None,
            }

            # Calculate accuracy if expected entities provided
            accuracy_scores = {}
            if expected_entities:
                accuracy_scores = calculate_accuracy(extracted_dict, expected_entities)

            # Get confidence scores
            confidence_scores = {
                "person": entities.confidence.person,
                "startup": entities.confidence.startup,
                "partner": entities.confidence.partner,
                "details": entities.confidence.details,
                "date": entities.confidence.date,
            }

            return BenchmarkResult(
                test_id=test_id,
                provider=provider_name,
                prompt_id=prompt_id,
                email_text=email_text,
                extracted_entities=extracted_dict,
                expected_entities=expected_entities,
                accuracy_scores=accuracy_scores,
                confidence_scores=confidence_scores,
                response_time=response_time,
                token_count=None,  # Not available from current adapters
                error=None,
                timestamp=datetime.now(),
            )

        except LLMAPIError as e:
            response_time = time.time() - start_time
            logger.error(f"LLM API error in test {test_id}: {e}")

            return BenchmarkResult(
                test_id=test_id,
                provider=provider_name,
                prompt_id=prompt_id,
                email_text=email_text,
                extracted_entities={},
                expected_entities=expected_entities,
                accuracy_scores={},
                confidence_scores={},
                response_time=response_time,
                token_count=None,
                error=str(e),
                timestamp=datetime.now(),
            )

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Unexpected error in test {test_id}: {e}")

            return BenchmarkResult(
                test_id=test_id,
                provider=provider_name,
                prompt_id=prompt_id,
                email_text=email_text,
                extracted_entities={},
                expected_entities=expected_entities,
                accuracy_scores={},
                confidence_scores={},
                response_time=response_time,
                token_count=None,
                error=str(e),
                timestamp=datetime.now(),
            )

    def run_benchmark(
        self,
        provider: LLMProvider,
        provider_name: str,
        test_data: List[Dict[str, Any]],
        prompt_id: str = "baseline",
        save_results: bool = True,
    ) -> Tuple[List[BenchmarkResult], AggregatedMetrics]:
        """Run benchmark across multiple test samples.

        Args:
            provider: LLM provider instance
            provider_name: Provider name (gemini, claude, openai)
            test_data: List of test samples, each with 'email_text' and optional 'expected_entities'
            prompt_id: Prompt variation ID to use
            save_results: Whether to save results to disk

        Returns:
            Tuple of (individual results, aggregated metrics)

        Examples:
            >>> test_data = [
            ...     {
            ...         "email_text": "어제 신세계와 본봄 킥오프",
            ...         "expected_entities": {"startup_name": "본봄", "partner_org": "신세계"}
            ...     },
            ...     {
            ...         "email_text": "TableManager meeting next week",
            ...         "expected_entities": {"startup_name": "TableManager"}
            ...     }
            ... ]
            >>> results, metrics = suite.run_benchmark(
            ...     provider=gemini_adapter,
            ...     provider_name="gemini",
            ...     test_data=test_data,
            ...     prompt_id="korean_optimized"
            ... )
        """
        logger.info(
            f"Starting benchmark: provider={provider_name}, prompt={prompt_id}, tests={len(test_data)}"
        )

        results = []
        for i, test_sample in enumerate(test_data):
            email_text = test_sample["email_text"]
            expected_entities = test_sample.get("expected_entities")

            logger.info(f"Running test {i+1}/{len(test_data)}")

            result = self.run_single_test(
                provider=provider,
                provider_name=provider_name,
                email_text=email_text,
                expected_entities=expected_entities,
                prompt_id=prompt_id,
            )

            results.append(result)

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        # Aggregate results
        metrics = aggregate_results(results)

        logger.info(
            f"Benchmark complete: {metrics.successful_tests}/{metrics.total_tests} successful, "
            f"avg_accuracy={metrics.avg_accuracy:.2f}, avg_confidence={metrics.avg_confidence:.2f}"
        )

        # Save results if requested
        if save_results:
            self.save_results(results, metrics, provider_name, prompt_id)

        return results, metrics

    def save_results(
        self,
        results: List[BenchmarkResult],
        metrics: AggregatedMetrics,
        provider_name: str,
        prompt_id: str,
    ) -> Path:
        """Save benchmark results to disk.

        Args:
            results: Individual benchmark results
            metrics: Aggregated metrics
            provider_name: Provider name
            prompt_id: Prompt variation ID

        Returns:
            Path to saved results file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{provider_name}_{prompt_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "provider": provider_name,
            "prompt_id": prompt_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics.model_dump(),
            "results": [r.model_dump(mode="json") for r in results],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {filepath}")
        return filepath

    def load_results(self, filepath: Path) -> Tuple[List[BenchmarkResult], AggregatedMetrics]:
        """Load benchmark results from disk.

        Args:
            filepath: Path to saved results file

        Returns:
            Tuple of (individual results, aggregated metrics)
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = [BenchmarkResult(**r) for r in data["results"]]
        metrics = AggregatedMetrics(**data["metrics"])

        return results, metrics


def run_benchmark(
    provider: LLMProvider,
    provider_name: str,
    test_data: List[Dict[str, Any]],
    prompt_id: str = "baseline",
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Convenience function to run a benchmark.

    Args:
        provider: LLM provider instance
        provider_name: Provider name (gemini, claude, openai)
        test_data: List of test samples
        prompt_id: Prompt variation ID to use
        output_dir: Directory to save results

    Returns:
        Dictionary with metrics and results

    Examples:
        >>> from src.llm_adapters.gemini_adapter import GeminiAdapter
        >>> adapter = GeminiAdapter(api_key="...")
        >>> test_data = [{"email_text": "...", "expected_entities": {...}}]
        >>> results = run_benchmark(adapter, "gemini", test_data, "korean_optimized")
    """
    suite = BenchmarkSuite(output_dir=output_dir)
    results, metrics = suite.run_benchmark(
        provider=provider,
        provider_name=provider_name,
        test_data=test_data,
        prompt_id=prompt_id,
        save_results=True,
    )

    return {
        "provider": provider_name,
        "prompt_id": prompt_id,
        "metrics": metrics.model_dump(),
        "total_tests": len(results),
        "successful_tests": metrics.successful_tests,
        "failed_tests": metrics.failed_tests,
    }


# Public API
__all__ = [
    "BenchmarkSuite",
    "run_benchmark",
]
