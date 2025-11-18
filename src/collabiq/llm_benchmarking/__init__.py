"""
LLM Benchmarking Library - Standalone library for LLM performance testing.

This library systematically evaluates LLM performance on Korean and English text,
providing both programmatic API and CLI interface per constitution principle II.

Usage (Python API):
    from src.collabiq.llm_benchmarking import run_benchmark, compare_prompts

    results = run_benchmark(provider="gemini", dataset="korean_samples.json")
    # Returns: {"provider": "gemini", "accuracy": 0.92, "avg_time": 2.1, "confidence": 0.88}

Usage (CLI):
    python -m src.collabiq.llm_benchmarking.cli --provider=gemini --dataset=korean_samples.json
    # Output: JSON metrics to stdout
"""

__version__ = "0.1.0"

# Library exports
from .ab_testing import ABTestFramework, compare_prompts
from .metrics import (
    AggregatedMetrics,
    BenchmarkResult,
    ComparisonResult,
    MetricType,
    aggregate_results,
    calculate_accuracy,
    calculate_completeness,
)
from .prompts import (
    BASELINE,
    EXPLICIT_FORMAT,
    FEW_SHOT,
    KOREAN_OPTIMIZED,
    STRUCTURED_OUTPUT,
    get_all_prompts,
    get_prompt_by_id,
    list_prompt_ids,
)
from .suite import BenchmarkSuite, run_benchmark

__all__ = [
    # Core classes
    "BenchmarkSuite",
    "ABTestFramework",
    # Main functions
    "run_benchmark",
    "compare_prompts",
    # Metrics
    "BenchmarkResult",
    "AggregatedMetrics",
    "ComparisonResult",
    "MetricType",
    "calculate_accuracy",
    "calculate_completeness",
    "aggregate_results",
    # Prompts
    "BASELINE",
    "KOREAN_OPTIMIZED",
    "EXPLICIT_FORMAT",
    "FEW_SHOT",
    "STRUCTURED_OUTPUT",
    "get_prompt_by_id",
    "get_all_prompts",
    "list_prompt_ids",
]
