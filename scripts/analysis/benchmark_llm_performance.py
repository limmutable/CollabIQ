#!/usr/bin/env python3
"""Benchmark LLM performance on Korean and English text extraction.

This script provides a CLI wrapper for the llm_benchmarking library,
allowing you to:
1. Run benchmarks on different LLM providers
2. Compare prompt variations (A/B testing)
3. Evaluate Korean vs English text extraction accuracy
4. Generate performance reports

Usage:
    # Run benchmark with default settings
    python scripts/benchmark_llm_performance.py

    # Run with specific provider and prompt
    python scripts/benchmark_llm_performance.py --provider gemini --prompt korean_optimized

    # Compare two prompts
    python scripts/benchmark_llm_performance.py --compare --baseline baseline --test korean_optimized

    # Run with custom test data
    python scripts/benchmark_llm_performance.py --test-data data/test_emails.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import directly from llm_benchmarking to avoid CLI imports
from collabiq.llm_benchmarking.prompts import (
    BASELINE,
    EXPLICIT_FORMAT,
    FEW_SHOT,
    KOREAN_OPTIMIZED,
    STRUCTURED_OUTPUT,
    get_prompt_description,
    list_prompt_ids,
)
from collabiq.llm_benchmarking.suite import run_benchmark
from collabiq.llm_benchmarking.ab_testing import compare_prompts
from llm_adapters.gemini_adapter import GeminiAdapter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Sample test data for Korean and English emails
DEFAULT_TEST_DATA = [
    {
        "email_text": "어제 신세계와 본봄 킥오프 미팅을 진행했습니다. 담당자는 김철수입니다.",
        "expected_entities": {
            "person_in_charge": "김철수",
            "startup_name": "본봄",
            "partner_org": "신세계",
            "details": "킥오프 미팅",
            "date": "2024-11-16",
        },
    },
    {
        "email_text": "TableManager kicked off pilot with Shinsegae yesterday. Contact: John Kim.",
        "expected_entities": {
            "person_in_charge": "John Kim",
            "startup_name": "TableManager",
            "partner_org": "Shinsegae",
            "details": "kicked off pilot",
            "date": "2024-11-16",
        },
    },
    {
        "email_text": "11월 1주에 스마트시티 프로젝트 관련 회의 예정",
        "expected_entities": {
            "person_in_charge": None,
            "startup_name": None,
            "partner_org": None,
            "details": "스마트시티 프로젝트 관련 회의",
            "date": "2024-11-01",
        },
    },
    {
        "email_text": "프랙시스 강승현 대표와 만나기로 했는데, 신세계 파트너십 논의할 예정입니다.",
        "expected_entities": {
            "person_in_charge": "강승현",
            "startup_name": "프랙시스",
            "partner_org": "신세계",
            "details": "파트너십 논의",
            "date": None,
        },
    },
    {
        "email_text": "BreakandCompany meeting scheduled for November 20, 2024. Will discuss CJ partnership.",
        "expected_entities": {
            "person_in_charge": None,
            "startup_name": "BreakandCompany",
            "partner_org": "CJ",
            "details": "discuss CJ partnership",
            "date": "2024-11-20",
        },
    },
]


def load_test_data(filepath: Path | None) -> list[dict[str, Any]]:
    """Load test data from file or use default samples.

    Args:
        filepath: Path to JSON file with test data

    Returns:
        List of test samples with email_text and expected_entities
    """
    if filepath and filepath.exists():
        logger.info(f"Loading test data from {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        logger.info("Using default test data (5 samples)")
        return DEFAULT_TEST_DATA


def get_provider(provider_name: str):
    """Get LLM provider instance.

    Args:
        provider_name: Provider name (gemini, claude, openai)

    Returns:
        LLM provider instance
    """
    if provider_name.lower() == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        return GeminiAdapter(api_key=api_key)
    elif provider_name.lower() == "claude":
        from llm_adapters.claude_adapter import ClaudeAdapter

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return ClaudeAdapter(api_key=api_key)
    elif provider_name.lower() == "openai":
        from llm_adapters.openai_adapter import OpenAIAdapter

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return OpenAIAdapter(api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def run_simple_benchmark(args):
    """Run a simple benchmark with specified provider and prompt.

    Args:
        args: Command-line arguments
    """
    print("\n" + "=" * 80)
    print("LLM PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Load test data
    test_data = load_test_data(args.test_data)
    print(f"\nTest dataset: {len(test_data)} emails")

    # Get provider
    print(f"Provider: {args.provider}")
    provider = get_provider(args.provider)

    # Get prompt
    print(f"Prompt variation: {args.prompt}")
    prompt_desc = get_prompt_description(args.prompt)
    print(f"Description: {prompt_desc}")

    # Run benchmark
    print("\nRunning benchmark...")
    print("-" * 80)

    result = run_benchmark(
        provider=provider,
        provider_name=args.provider,
        test_data=test_data,
        prompt_id=args.prompt,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )

    # Print results
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)

    metrics = result["metrics"]
    print(f"\nProvider: {result['provider']}")
    print(f"Prompt: {result['prompt_id']}")
    print("\nTests:")
    print(f"  Total:      {result['total_tests']}")
    print(f"  Successful: {result['successful_tests']}")
    print(f"  Failed:     {result['failed_tests']}")

    print("\nPerformance:")
    print(f"  Accuracy:        {metrics['avg_accuracy']:.2%}")
    print(f"  Confidence:      {metrics['avg_confidence']:.2%}")
    print(f"  Completeness:    {metrics['avg_completeness']:.2%}")
    print(f"  Response Time:   {metrics['avg_response_time']:.2f}s")

    if metrics.get("field_accuracies"):
        print("\nField Accuracies:")
        for field, accuracy in metrics["field_accuracies"].items():
            print(f"  {field:20s}: {accuracy:.2%}")

    print("\n" + "=" * 80)
    print("Benchmark complete!")
    print("=" * 80)


def run_ab_test(args):
    """Run A/B test comparing two prompt variations.

    Args:
        args: Command-line arguments
    """
    print("\n" + "=" * 80)
    print("LLM PROMPT A/B TEST")
    print("=" * 80)

    # Load test data
    test_data = load_test_data(args.test_data)
    print(f"\nTest dataset: {len(test_data)} emails")

    # Get provider
    print(f"Provider: {args.provider}")
    provider = get_provider(args.provider)

    # Get prompts
    print(f"\nBaseline prompt:    {args.baseline}")
    baseline_desc = get_prompt_description(args.baseline)
    print(f"  Description: {baseline_desc}")

    print(f"\nTest prompt:        {args.test}")
    test_desc = get_prompt_description(args.test)
    print(f"  Description: {test_desc}")

    # Run A/B test
    print("\nRunning A/B test...")
    print("-" * 80)

    result = compare_prompts(
        provider=provider,
        provider_name=args.provider,
        baseline_prompt=args.baseline,
        comparison_prompt=args.test,
        test_data=test_data,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )

    # Print results
    print("\n" + "=" * 80)
    print("A/B TEST RESULTS")
    print("=" * 80)

    print(f"\nBaseline: {result['baseline']}")
    baseline_metrics = result["baseline_metrics"]
    print(f"  Accuracy:     {baseline_metrics['avg_accuracy']:.2%}")
    print(f"  Confidence:   {baseline_metrics['avg_confidence']:.2%}")
    print(f"  Speed:        {baseline_metrics['avg_response_time']:.2f}s")

    print(f"\nTest Prompt: {result['comparison']}")
    comparison_metrics = result["comparison_metrics"]
    print(f"  Accuracy:     {comparison_metrics['avg_accuracy']:.2%}")
    print(f"  Confidence:   {comparison_metrics['avg_confidence']:.2%}")
    print(f"  Speed:        {comparison_metrics['avg_response_time']:.2f}s")

    print("\nImprovement:")
    acc_improvement = result["accuracy_improvement"]
    conf_improvement = result["confidence_improvement"]
    speed_improvement = result["speed_improvement"]

    print(f"  Accuracy:     {acc_improvement:+.1f}%")
    print(f"  Confidence:   {conf_improvement:+.1f}%")
    print(f"  Speed:        {speed_improvement:+.1f}%")

    winner = result["winner"]
    print(f"\nWinner: {winner}")

    if winner == result["comparison"]:
        print("✅ Test prompt performs better!")
    elif winner == result["baseline"]:
        print("⚠️ Baseline prompt still performs better")

    print("\n" + "=" * 80)
    print("A/B test complete!")
    print("=" * 80)


def list_available_prompts():
    """List all available prompt variations."""
    print("\n" + "=" * 80)
    print("AVAILABLE PROMPT VARIATIONS")
    print("=" * 80 + "\n")

    prompt_ids = list_prompt_ids()

    for prompt_id in prompt_ids:
        description = get_prompt_description(prompt_id)
        print(f"{prompt_id:20s}: {description}")

    print("\n" + "=" * 80)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Benchmark LLM performance on Korean and English text extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run basic benchmark
  python scripts/benchmark_llm_performance.py

  # Run with specific provider and prompt
  python scripts/benchmark_llm_performance.py --provider gemini --prompt korean_optimized

  # Compare two prompts (A/B test)
  python scripts/benchmark_llm_performance.py --compare --baseline baseline --test korean_optimized

  # List available prompts
  python scripts/benchmark_llm_performance.py --list-prompts

  # Use custom test data
  python scripts/benchmark_llm_performance.py --test-data data/my_test_emails.json
        """,
    )

    # Mode selection
    parser.add_argument(
        "--compare", action="store_true", help="Run A/B test comparing two prompts"
    )

    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List all available prompt variations",
    )

    # Provider selection
    parser.add_argument(
        "--provider",
        type=str,
        default="gemini",
        choices=["gemini", "claude", "openai"],
        help="LLM provider to use (default: gemini)",
    )

    # Prompt selection
    parser.add_argument(
        "--prompt",
        type=str,
        default=BASELINE,
        choices=[
            BASELINE,
            KOREAN_OPTIMIZED,
            EXPLICIT_FORMAT,
            FEW_SHOT,
            STRUCTURED_OUTPUT,
        ],
        help=f"Prompt variation to use (default: {BASELINE})",
    )

    # A/B test options
    parser.add_argument(
        "--baseline",
        type=str,
        default=BASELINE,
        choices=[
            BASELINE,
            KOREAN_OPTIMIZED,
            EXPLICIT_FORMAT,
            FEW_SHOT,
            STRUCTURED_OUTPUT,
        ],
        help=f"Baseline prompt for A/B test (default: {BASELINE})",
    )

    parser.add_argument(
        "--test",
        type=str,
        default=KOREAN_OPTIMIZED,
        choices=[
            BASELINE,
            KOREAN_OPTIMIZED,
            EXPLICIT_FORMAT,
            FEW_SHOT,
            STRUCTURED_OUTPUT,
        ],
        help=f"Test prompt for A/B test (default: {KOREAN_OPTIMIZED})",
    )

    # Data options
    parser.add_argument(
        "--test-data",
        type=Path,
        default=None,
        help="Path to JSON file with test data (default: use built-in samples)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save results (default: data/test_metrics/benchmarks/)",
    )

    args = parser.parse_args()

    # Handle list-prompts mode
    if args.list_prompts:
        list_available_prompts()
        return 0

    try:
        # Handle compare mode
        if args.compare:
            run_ab_test(args)
        else:
            # Handle simple benchmark mode
            run_simple_benchmark(args)

        return 0

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
