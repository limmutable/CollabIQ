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

# Library exports will be added as modules are implemented
# from .suite import run_benchmark
# from .ab_testing import compare_prompts
# from .metrics import calculate_metrics
