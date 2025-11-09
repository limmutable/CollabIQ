"""Integration tests for quality-based routing.

Tests quality-aware provider selection in FailoverStrategy,
verifying that providers are selected based on quality metrics
when quality routing is enabled.
"""

import pytest
from unittest.mock import Mock, patch

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.quality_tracker import QualityTracker
from llm_orchestrator.strategies.failover import FailoverStrategy
from llm_orchestrator.types import ProviderQualitySummary
from llm_provider.types import ExtractedEntities, ConfidenceScores


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, provider_name: str, should_fail: bool = False):
        self.provider_name = provider_name
        self.should_fail = should_fail
        self.last_input_tokens = 100
        self.last_output_tokens = 50

    def extract_entities(self, email_text: str, **kwargs) -> ExtractedEntities:
        """Mock extraction that returns test data."""
        if self.should_fail:
            raise Exception(f"Mock failure from {self.provider_name}")

        return ExtractedEntities(
            person_in_charge=f"Person from {self.provider_name}",
            startup_name="Test Startup",
            partner_org="Test Partner",
            details="Test details",
            date="2025-11-09",
            confidence=ConfidenceScores(
                person=0.9,
                startup=0.9,
                partner=0.9,
                details=0.9,
                date=0.9,
            ),
            email_id="test_email_001",
            provider_name=self.provider_name,
        )


@pytest.fixture
def quality_tracker(tmp_path):
    """Create QualityTracker with test data."""
    tracker = QualityTracker(data_dir=tmp_path / "llm_health")

    # Initialize metrics for three providers with different quality levels
    # Claude: highest quality (0.92)
    tracker.metrics["claude"] = ProviderQualitySummary(
        provider_name="claude",
        total_extractions=100,
        successful_validations=95,
        failed_validations=5,
        validation_success_rate=95.0,
        average_overall_confidence=0.92,
        confidence_std_deviation=0.05,
        average_field_completeness=95.0,
        average_fields_extracted=4.8,
    )

    # Gemini: medium quality (0.85)
    tracker.metrics["gemini"] = ProviderQualitySummary(
        provider_name="gemini",
        total_extractions=100,
        successful_validations=88,
        failed_validations=12,
        validation_success_rate=88.0,
        average_overall_confidence=0.85,
        confidence_std_deviation=0.08,
        average_field_completeness=88.0,
        average_fields_extracted=4.4,
    )

    # OpenAI: lowest quality (0.78)
    tracker.metrics["openai"] = ProviderQualitySummary(
        provider_name="openai",
        total_extractions=100,
        successful_validations=80,
        failed_validations=20,
        validation_success_rate=80.0,
        average_overall_confidence=0.78,
        confidence_std_deviation=0.10,
        average_field_completeness=82.0,
        average_fields_extracted=4.1,
    )

    return tracker


@pytest.fixture
def health_tracker(tmp_path):
    """Create HealthTracker instance."""
    return HealthTracker(data_dir=tmp_path / "llm_health")


def test_quality_routing_selects_highest_quality_provider(quality_tracker, health_tracker):
    """Test that quality routing selects provider with highest quality score."""
    # Create providers
    providers = {
        "gemini": MockProvider("gemini"),
        "claude": MockProvider("claude"),
        "openai": MockProvider("openai"),
    }

    # Create strategy with quality routing enabled
    strategy = FailoverStrategy(
        priority_order=["gemini", "claude", "openai"],  # Priority order differs from quality
        quality_tracker=quality_tracker,
    )

    # Execute strategy
    entities, provider_used = strategy.execute(
        providers=providers,
        email_text="Test email text",
        health_tracker=health_tracker,
    )

    # Should select Claude (highest quality 0.92) despite Gemini being first in priority
    assert provider_used == "claude"
    assert entities.person_in_charge == "Person from claude"


def test_quality_routing_disabled_uses_priority_order(health_tracker):
    """Test that without quality_tracker, strategy uses priority order."""
    # Create providers
    providers = {
        "gemini": MockProvider("gemini"),
        "claude": MockProvider("claude"),
        "openai": MockProvider("openai"),
    }

    # Create strategy WITHOUT quality routing
    strategy = FailoverStrategy(
        priority_order=["gemini", "claude", "openai"],
        quality_tracker=None,  # Quality routing disabled
    )

    # Execute strategy
    entities, provider_used = strategy.execute(
        providers=providers,
        email_text="Test email text",
        health_tracker=health_tracker,
    )

    # Should use priority order (Gemini first)
    assert provider_used == "gemini"


def test_quality_routing_falls_back_to_priority_when_no_metrics(health_tracker):
    """Test fallback to priority order when no quality metrics available."""
    # Create empty quality tracker (no metrics)
    empty_quality_tracker = QualityTracker()

    # Create providers
    providers = {
        "gemini": MockProvider("gemini"),
        "claude": MockProvider("claude"),
        "openai": MockProvider("openai"),
    }

    # Create strategy with quality routing enabled but no metrics
    strategy = FailoverStrategy(
        priority_order=["gemini", "claude", "openai"],
        quality_tracker=empty_quality_tracker,
    )

    # Execute strategy
    entities, provider_used = strategy.execute(
        providers=providers,
        email_text="Test email text",
        health_tracker=health_tracker,
    )

    # Should fall back to priority order (Gemini first)
    assert provider_used == "gemini"


def test_quality_routing_skips_unhealthy_providers(quality_tracker, health_tracker):
    """Test that quality routing still respects health checks."""
    # Create providers
    providers = {
        "gemini": MockProvider("gemini"),
        "claude": MockProvider("claude"),
        "openai": MockProvider("openai"),
    }

    # Mark Claude as unhealthy (circuit breaker OPEN)
    for _ in range(10):  # Trigger circuit breaker
        health_tracker.record_failure("claude", "Test failure")

    # Create strategy with quality routing
    strategy = FailoverStrategy(
        priority_order=["gemini", "claude", "openai"],
        quality_tracker=quality_tracker,
    )

    # Execute strategy
    entities, provider_used = strategy.execute(
        providers=providers,
        email_text="Test email text",
        health_tracker=health_tracker,
    )

    # Should NOT use Claude (unhealthy) even though it has highest quality
    # Should fall back to Gemini (second best quality, healthy)
    assert provider_used != "claude"
    assert provider_used == "gemini"


def test_quality_routing_tries_next_provider_on_failure(quality_tracker, health_tracker):
    """Test that quality routing tries next provider if first fails."""
    # Create providers where Claude fails
    providers = {
        "gemini": MockProvider("gemini"),
        "claude": MockProvider("claude", should_fail=True),
        "openai": MockProvider("openai"),
    }

    # Create strategy with quality routing
    strategy = FailoverStrategy(
        priority_order=["gemini", "claude", "openai"],
        quality_tracker=quality_tracker,
    )

    # Execute strategy
    entities, provider_used = strategy.execute(
        providers=providers,
        email_text="Test email text",
        health_tracker=health_tracker,
    )

    # Should try Claude first (highest quality) but fail
    # Then should fall back to Gemini (second in failover order)
    assert provider_used == "gemini"


def test_select_provider_by_quality_ranking(quality_tracker):
    """Test select_provider_by_quality returns correct ranking."""
    candidates = ["gemini", "claude", "openai"]

    # Select best provider
    best_provider = quality_tracker.select_provider_by_quality(candidates)

    # Should return Claude (highest quality score)
    assert best_provider == "claude"


def test_select_provider_by_quality_with_subset(quality_tracker):
    """Test quality selection with subset of providers."""
    # Only consider Gemini and OpenAI (exclude Claude)
    candidates = ["gemini", "openai"]

    best_provider = quality_tracker.select_provider_by_quality(candidates)

    # Should return Gemini (higher quality than OpenAI)
    assert best_provider == "gemini"


def test_select_provider_by_quality_no_metrics():
    """Test quality selection with no metrics returns None."""
    empty_tracker = QualityTracker()
    candidates = ["gemini", "claude", "openai"]

    best_provider = empty_tracker.select_provider_by_quality(candidates)

    assert best_provider is None


def test_select_provider_by_quality_empty_candidates(quality_tracker):
    """Test quality selection with empty candidates returns None."""
    best_provider = quality_tracker.select_provider_by_quality([])

    assert best_provider is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
