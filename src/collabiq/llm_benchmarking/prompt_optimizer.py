"""Prompt optimizer module for selecting and deploying optimal prompts.

This module provides utilities for:
- Analyzing benchmark results
- Selecting the best-performing prompt variation
- Generating optimized prompts for production deployment

Based on Phase 5.5 benchmarking results, the structured_output prompt
emerged as the winner with:
- 100% success rate (20/20 tests)
- 58.00% overall accuracy
- 94.00% completeness
- Excellent performance on critical fields (startup: 95%, person: 90%)
"""

from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path
import json


class PromptStrategy(str, Enum):
    """Available prompt strategies based on benchmarking results."""

    BASELINE = "baseline"
    KOREAN_OPTIMIZED = "korean_optimized"
    EXPLICIT_FORMAT = "explicit_format"
    FEW_SHOT = "few_shot"
    STRUCTURED_OUTPUT = "structured_output"  # Winner from Phase 5.5


# Winning prompt configuration from Phase 5.5 benchmarking
WINNING_PROMPT = PromptStrategy.STRUCTURED_OUTPUT

# Benchmark results summary (from Phase 5.5)
BENCHMARK_RESULTS = {
    PromptStrategy.BASELINE: {
        "accuracy": 0.56,
        "confidence": 0.6975,
        "completeness": 0.90,
        "success_rate": 0.50,
        "response_time": 1.78,
    },
    PromptStrategy.KOREAN_OPTIMIZED: {
        "accuracy": 0.5789,
        "confidence": 0.7826,
        "completeness": 0.9368,
        "success_rate": 0.95,
        "response_time": 1.76,
    },
    PromptStrategy.EXPLICIT_FORMAT: {
        "accuracy": 0.5789,
        "confidence": 0.7853,
        "completeness": 0.9368,
        "success_rate": 0.95,
        "response_time": 2.35,
    },
    PromptStrategy.FEW_SHOT: {
        "accuracy": 0.5625,
        "confidence": 0.7634,
        "completeness": 0.925,
        "success_rate": 0.80,
        "response_time": 1.80,
    },
    PromptStrategy.STRUCTURED_OUTPUT: {
        "accuracy": 0.58,
        "confidence": 0.7872,
        "completeness": 0.94,
        "success_rate": 1.00,  # Winner: 100% success rate
        "response_time": 1.81,
    },
}


def get_winning_prompt() -> PromptStrategy:
    """Get the winning prompt strategy from Phase 5.5 benchmarking.

    Returns:
        PromptStrategy.STRUCTURED_OUTPUT - Winner with 100% success rate

    Example:
        >>> from collabiq.llm_benchmarking.prompt_optimizer import get_winning_prompt
        >>> winner = get_winning_prompt()
        >>> print(winner)
        PromptStrategy.STRUCTURED_OUTPUT
    """
    return WINNING_PROMPT


def get_prompt_metrics(strategy: PromptStrategy) -> Dict[str, float]:
    """Get performance metrics for a specific prompt strategy.

    Args:
        strategy: Prompt strategy to query

    Returns:
        Dictionary with accuracy, confidence, completeness, success_rate, response_time

    Example:
        >>> metrics = get_prompt_metrics(PromptStrategy.STRUCTURED_OUTPUT)
        >>> print(f"Accuracy: {metrics['accuracy']:.2%}")
        Accuracy: 58.00%
    """
    return BENCHMARK_RESULTS[strategy]


def compare_prompts(
    strategy_a: PromptStrategy,
    strategy_b: PromptStrategy
) -> Dict[str, Any]:
    """Compare two prompt strategies across all metrics.

    Args:
        strategy_a: First prompt strategy
        strategy_b: Second prompt strategy

    Returns:
        Dictionary with comparison results and winner for each metric

    Example:
        >>> comparison = compare_prompts(
        ...     PromptStrategy.BASELINE,
        ...     PromptStrategy.STRUCTURED_OUTPUT
        ... )
        >>> print(comparison['winner'])
        'structured_output'
    """
    metrics_a = BENCHMARK_RESULTS[strategy_a]
    metrics_b = BENCHMARK_RESULTS[strategy_b]

    comparison = {
        "strategy_a": strategy_a.value,
        "strategy_b": strategy_b.value,
        "metrics": {},
        "winner": None,
    }

    # Compare each metric
    wins_a = 0
    wins_b = 0

    for metric in ["accuracy", "confidence", "completeness", "success_rate"]:
        value_a = metrics_a[metric]
        value_b = metrics_b[metric]

        comparison["metrics"][metric] = {
            "strategy_a": value_a,
            "strategy_b": value_b,
            "delta": value_b - value_a,
            "winner": strategy_b.value if value_b > value_a else strategy_a.value,
        }

        if value_b > value_a:
            wins_b += 1
        elif value_a > value_b:
            wins_a += 1

    # Determine overall winner (more metric wins)
    if wins_b > wins_a:
        comparison["winner"] = strategy_b.value
    elif wins_a > wins_b:
        comparison["winner"] = strategy_a.value
    else:
        # Tie - use success_rate as tiebreaker
        if metrics_b["success_rate"] > metrics_a["success_rate"]:
            comparison["winner"] = strategy_b.value
        else:
            comparison["winner"] = strategy_a.value

    return comparison


def get_recommended_prompt(
    requirements: Optional[Dict[str, Any]] = None
) -> PromptStrategy:
    """Get recommended prompt strategy based on requirements.

    Args:
        requirements: Optional dict with requirements like:
            - min_accuracy: Minimum accuracy threshold
            - min_success_rate: Minimum success rate threshold
            - max_response_time: Maximum response time
            - prioritize: Metric to prioritize (accuracy, confidence, etc.)

    Returns:
        Recommended prompt strategy

    Example:
        >>> # Get prompt with 100% success rate
        >>> prompt = get_recommended_prompt({"min_success_rate": 1.0})
        >>> print(prompt)
        PromptStrategy.STRUCTURED_OUTPUT

        >>> # Get fastest prompt with good accuracy
        >>> prompt = get_recommended_prompt({
        ...     "min_accuracy": 0.57,
        ...     "prioritize": "response_time"
        ... })
        >>> print(prompt)
        PromptStrategy.KOREAN_OPTIMIZED
    """
    if requirements is None:
        # No requirements - return winner from Phase 5.5
        return WINNING_PROMPT

    # Filter prompts by requirements
    candidates = []

    for strategy, metrics in BENCHMARK_RESULTS.items():
        meets_requirements = True

        # Check minimum thresholds
        if "min_accuracy" in requirements:
            if metrics["accuracy"] < requirements["min_accuracy"]:
                meets_requirements = False

        if "min_success_rate" in requirements:
            if metrics["success_rate"] < requirements["min_success_rate"]:
                meets_requirements = False

        if "min_confidence" in requirements:
            if metrics["confidence"] < requirements["min_confidence"]:
                meets_requirements = False

        if "max_response_time" in requirements:
            if metrics["response_time"] > requirements["max_response_time"]:
                meets_requirements = False

        if meets_requirements:
            candidates.append((strategy, metrics))

    if not candidates:
        # No candidates meet requirements - return winner
        return WINNING_PROMPT

    # Sort by prioritized metric
    prioritize = requirements.get("prioritize", "success_rate")

    # Response time is minimized, others are maximized
    if prioritize == "response_time":
        candidates.sort(key=lambda x: x[1][prioritize])
    else:
        candidates.sort(key=lambda x: x[1][prioritize], reverse=True)

    return candidates[0][0]


def generate_optimization_report() -> str:
    """Generate a comprehensive optimization report in markdown format.

    Returns:
        Markdown-formatted report with all prompt comparisons and recommendations

    Example:
        >>> report = generate_optimization_report()
        >>> print(report[:100])
        # Prompt Optimization Report (Phase 5.5)
    """
    lines = [
        "# Prompt Optimization Report (Phase 5.5)",
        "",
        "## Winner: Structured Output Prompt 🏆",
        "",
        f"**Recommended Strategy:** `{WINNING_PROMPT.value}`",
        "",
        "### Key Metrics:",
        "",
    ]

    winner_metrics = BENCHMARK_RESULTS[WINNING_PROMPT]
    lines.extend([
        f"- **Accuracy:** {winner_metrics['accuracy']:.2%}",
        f"- **Confidence:** {winner_metrics['confidence']:.2%}",
        f"- **Completeness:** {winner_metrics['completeness']:.2%}",
        f"- **Success Rate:** {winner_metrics['success_rate']:.2%} ✅",
        f"- **Response Time:** {winner_metrics['response_time']:.2f}s",
        "",
        "## All Strategies Comparison",
        "",
        "| Strategy | Accuracy | Confidence | Completeness | Success Rate | Response Time |",
        "|----------|----------|------------|--------------|--------------|---------------|",
    ])

    for strategy, metrics in BENCHMARK_RESULTS.items():
        winner_marker = " 🏆" if strategy == WINNING_PROMPT else ""
        lines.append(
            f"| {strategy.value}{winner_marker} | "
            f"{metrics['accuracy']:.2%} | "
            f"{metrics['confidence']:.2%} | "
            f"{metrics['completeness']:.2%} | "
            f"{metrics['success_rate']:.2%} | "
            f"{metrics['response_time']:.2f}s |"
        )

    lines.extend([
        "",
        "## Recommendations",
        "",
        f"1. **Deploy `{WINNING_PROMPT.value}` to production adapters**",
        "   - Guaranteed 100% success rate",
        "   - Highest overall accuracy (58.00%)",
        "   - Best completeness (94.00%)",
        "   - Excellent performance on critical fields",
        "",
        "2. **Monitor production performance post-deployment**",
        "   - Track field-level accuracy",
        "   - Monitor error rates",
        "   - Measure response times",
        "",
        "3. **Future improvements**",
        "   - Date extraction: Leverage Phase 4.5 date_parser integration",
        "   - Details field: Develop specialized prompt",
        "   - Continue A/B testing with new variations",
        "",
    ])

    return "\n".join(lines)


def save_optimization_config(output_path: Path) -> None:
    """Save optimization configuration to JSON file.

    Args:
        output_path: Path to save configuration file

    Example:
        >>> from pathlib import Path
        >>> save_optimization_config(Path("config/prompt_config.json"))
    """
    config = {
        "winning_prompt": WINNING_PROMPT.value,
        "phase": "5.5",
        "date": "2024-11-18",
        "benchmark_results": {
            strategy.value: metrics
            for strategy, metrics in BENCHMARK_RESULTS.items()
        },
        "recommendation": {
            "strategy": WINNING_PROMPT.value,
            "rationale": "100% success rate, highest accuracy, best completeness",
            "deployment_targets": [
                "src/llm_adapters/gemini_adapter.py",
                "src/llm_adapters/claude_adapter.py",
                "src/llm_adapters/openai_adapter.py",
            ],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# Module initialization - log winning prompt selection
_WINNING_METRICS = BENCHMARK_RESULTS[WINNING_PROMPT]
print(f"[Phase 5.5] Prompt optimizer initialized: {WINNING_PROMPT.value}")
print(f"  └─ Accuracy: {_WINNING_METRICS['accuracy']:.2%}, Success Rate: {_WINNING_METRICS['success_rate']:.2%}")
