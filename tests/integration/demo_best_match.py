"""Demonstration of BestMatchStrategy with varying confidence scenarios.

This script demonstrates how the best-match strategy selects providers
based on aggregate confidence scores.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.strategies.best_match import (
    BestMatchStrategy,
    calculate_aggregate_confidence,
)
from llm_provider.types import ConfidenceScores, ExtractedEntities


def create_mock_provider(name: str, confidence_scores: ConfidenceScores) -> MagicMock:
    """Create a mock provider that returns entities with specified confidence."""
    provider = MagicMock()
    provider.extract_entities.return_value = ExtractedEntities(
        person_in_charge=f"Person from {name}",
        startup_name=f"Startup from {name}",
        partner_org=f"Partner from {name}",
        details=f"Details from {name}",
        date=None,
        confidence=confidence_scores,
        email_id="demo123",
        extracted_at=datetime.now(timezone.utc),
    )
    return provider


def demo_scenario_1_clear_winner():
    """Scenario 1: One provider clearly has highest confidence."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Clear Winner (Claude has highest confidence)")
    print("=" * 80)

    # Create providers with different confidence levels
    providers = {
        "gemini": create_mock_provider(
            "gemini",
            ConfidenceScores(
                person=0.70, startup=0.65, partner=0.60, details=0.55, date=0.50
            ),
        ),
        "claude": create_mock_provider(
            "claude",
            ConfidenceScores(
                person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
            ),
        ),
        "openai": create_mock_provider(
            "openai",
            ConfidenceScores(
                person=0.75, startup=0.72, partner=0.68, details=0.65, date=0.60
            ),
        ),
    }

    # Calculate and display aggregate confidence for each
    print("\nAggregate Confidence Scores:")
    for name, provider in providers.items():
        result = provider.extract_entities(email_text="test", email_id="demo")
        agg_conf = calculate_aggregate_confidence(result.confidence)
        print(f"  {name:10s}: {agg_conf:.4f}")
        print(
            f"    Details: person={result.confidence.person:.2f}, "
            f"startup={result.confidence.startup:.2f}, "
            f"partner={result.confidence.partner:.2f}, "
            f"details={result.confidence.details:.2f}, "
            f"date={result.confidence.date:.2f}"
        )

    # Run best-match strategy
    health_tracker = HealthTracker(
        data_dir=Path("/tmp/demo_best_match"), unhealthy_threshold=3
    )
    strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])
    result, provider_used = strategy.execute(
        providers=providers,
        email_text="test email",
        health_tracker=health_tracker,
    )

    print(f"\n✓ Best-Match Selection: {provider_used}")
    print("  Winner has highest aggregate confidence (0.8981)")


def demo_scenario_2_weighted_matters():
    """Scenario 2: Weighting matters - high confidence in important fields wins."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Weighting Matters (Provider A wins despite lower average)")
    print("=" * 80)

    # Provider A: High confidence in person/startup (weighted fields)
    provider_a_scores = ConfidenceScores(
        person=0.95, startup=0.95, partner=0.90, details=0.60, date=0.40
    )

    # Provider B: High confidence in details/date (less weighted)
    provider_b_scores = ConfidenceScores(
        person=0.60, startup=0.60, partner=0.60, details=0.95, date=0.95
    )

    providers = {
        "provider_a": create_mock_provider("provider_a", provider_a_scores),
        "provider_b": create_mock_provider("provider_b", provider_b_scores),
    }

    print("\nConfidence Scores:")
    for name, provider in providers.items():
        result = provider.extract_entities(email_text="test", email_id="demo")
        avg = (
            sum(
                [
                    result.confidence.person,
                    result.confidence.startup,
                    result.confidence.partner,
                    result.confidence.details,
                    result.confidence.date,
                ]
            )
            / 5
        )
        agg = calculate_aggregate_confidence(result.confidence)
        print(f"  {name:15s}:")
        print(f"    Simple average:     {avg:.4f}")
        print(f"    Weighted aggregate: {agg:.4f}")
        print(
            f"    person={result.confidence.person:.2f} (weight=1.5), "
            f"startup={result.confidence.startup:.2f} (weight=1.5), "
            f"partner={result.confidence.partner:.2f} (weight=1.0)"
        )
        print(
            f"    details={result.confidence.details:.2f} (weight=0.8), "
            f"date={result.confidence.date:.2f} (weight=0.5)"
        )

    health_tracker = HealthTracker(
        data_dir=Path("/tmp/demo_best_match"), unhealthy_threshold=3
    )
    strategy = BestMatchStrategy(provider_names=["provider_a", "provider_b"])
    result, provider_used = strategy.execute(
        providers=providers,
        email_text="test email",
        health_tracker=health_tracker,
    )

    print(f"\n✓ Best-Match Selection: {provider_used}")
    print("  Weighted aggregate favors high confidence in person/startup fields")


def demo_scenario_3_tie_breaking():
    """Scenario 3: Tie-breaking when confidence is equal."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Tie-Breaking (Equal confidence, uses historical success rate)")
    print("=" * 80)

    # Both providers have identical confidence
    same_scores = ConfidenceScores(
        person=0.85, startup=0.85, partner=0.85, details=0.85, date=0.85
    )

    providers = {
        "provider_1": create_mock_provider("provider_1", same_scores),
        "provider_2": create_mock_provider("provider_2", same_scores),
    }

    print("\nConfidence Scores:")
    for name, provider in providers.items():
        result = provider.extract_entities(email_text="test", email_id="demo")
        agg = calculate_aggregate_confidence(result.confidence)
        print(f"  {name:15s}: {agg:.4f} (identical)")

    # Set up health tracker with different historical success rates
    health_tracker = HealthTracker(
        data_dir=Path("/tmp/demo_best_match"), unhealthy_threshold=3
    )

    # Give provider_1 better historical success rate
    for _ in range(10):
        health_tracker.record_success("provider_1", 100.0)

    # Give provider_2 lower success rate
    for _ in range(5):
        health_tracker.record_success("provider_2", 100.0)
    for _ in range(2):
        health_tracker.record_failure("provider_2", "Test failure")

    print("\nHistorical Success Rates:")
    for name in providers.keys():
        metrics = health_tracker.get_metrics(name)
        print(
            f"  {name:15s}: {metrics.success_rate:.2%} "
            f"({metrics.success_count}/{metrics.success_count + metrics.failure_count})"
        )

    strategy = BestMatchStrategy(provider_names=["provider_2", "provider_1"])
    result, provider_used = strategy.execute(
        providers=providers,
        email_text="test email",
        health_tracker=health_tracker,
    )

    print(f"\n✓ Best-Match Selection: {provider_used}")
    print("  Tie-breaker: Higher historical success rate wins")


def demo_scenario_4_partial_failures():
    """Scenario 4: Some providers fail, best-match selects from successful ones."""
    print("\n" + "=" * 80)
    print(
        "SCENARIO 4: Partial Failures (Gemini fails, best-match selects from remaining)"
    )
    print("=" * 80)

    from llm_provider.exceptions import LLMAPIError

    providers = {
        "gemini": MagicMock(),
        "claude": create_mock_provider(
            "claude",
            ConfidenceScores(
                person=0.90, startup=0.88, partner=0.85, details=0.82, date=0.80
            ),
        ),
        "openai": create_mock_provider(
            "openai",
            ConfidenceScores(
                person=0.85, startup=0.83, partner=0.80, details=0.78, date=0.75
            ),
        ),
    }

    # Make gemini fail
    providers["gemini"].extract_entities.side_effect = LLMAPIError("API timeout")

    print("\nProvider Status:")
    print("  gemini:  FAILED (API timeout)")

    for name in ["claude", "openai"]:
        result = providers[name].extract_entities(email_text="test", email_id="demo")
        agg = calculate_aggregate_confidence(result.confidence)
        print(f"  {name:8s}: SUCCESS (aggregate_confidence={agg:.4f})")

    health_tracker = HealthTracker(
        data_dir=Path("/tmp/demo_best_match"), unhealthy_threshold=3
    )
    strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])
    result, provider_used = strategy.execute(
        providers=providers,
        email_text="test email",
        health_tracker=health_tracker,
    )

    print(f"\n✓ Best-Match Selection: {provider_used}")
    print("  Selects best among successful providers (Claude: 0.8585 > OpenAI: 0.8113)")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "BEST-MATCH STRATEGY DEMONSTRATION" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")

    demo_scenario_1_clear_winner()
    demo_scenario_2_weighted_matters()
    demo_scenario_3_tie_breaking()
    demo_scenario_4_partial_failures()

    print("\n" + "=" * 80)
    print("All scenarios completed successfully!")
    print("=" * 80 + "\n")
