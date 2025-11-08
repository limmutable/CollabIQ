"""Integration tests for BestMatchStrategy.

Tests the best-match strategy with mocked providers to verify:
- Parallel provider queries using asyncio
- Aggregate confidence calculation across all entity fields
- Result selection based on highest aggregate confidence
- Tie-breaking when multiple results have same confidence
- Health tracking integration
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.llm_adapters.health_tracker import HealthTracker
from src.llm_orchestrator.exceptions import AllProvidersFailedError
from src.llm_orchestrator.strategies.best_match import BestMatchStrategy
from src.llm_provider.exceptions import LLMAPIError, LLMTimeoutError
from src.llm_provider.types import ConfidenceScores, ExtractedEntities


@pytest.fixture
def health_tracker(tmp_path):
    """Create HealthTracker for testing."""
    return HealthTracker(data_dir=tmp_path / "health", unhealthy_threshold=3)


@pytest.fixture
def mock_providers():
    """Create mock LLM providers with different confidence scores."""
    providers = {}

    # Gemini - medium confidence
    gemini = MagicMock()
    gemini.extract_entities.return_value = ExtractedEntities(
        person_in_charge="John Doe",
        startup_name="Gemini Startup",
        partner_org="Gemini Partner",
        details="Gemini details",
        date=None,
        confidence=ConfidenceScores(
            person=0.75, startup=0.70, partner=0.65, details=0.60, date=0.50
        ),
        email_id="test123",
        extracted_at=datetime.now(timezone.utc),
    )
    providers["gemini"] = gemini

    # Claude - high confidence (should win)
    claude = MagicMock()
    claude.extract_entities.return_value = ExtractedEntities(
        person_in_charge="Jane Smith",
        startup_name="Claude Startup",
        partner_org="Claude Partner",
        details="Claude details",
        date=None,
        confidence=ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        ),
        email_id="test123",
        extracted_at=datetime.now(timezone.utc),
    )
    providers["claude"] = claude

    # OpenAI - low confidence
    openai = MagicMock()
    openai.extract_entities.return_value = ExtractedEntities(
        person_in_charge="Bob Johnson",
        startup_name="OpenAI Startup",
        partner_org="OpenAI Partner",
        details="OpenAI details",
        date=None,
        confidence=ConfidenceScores(
            person=0.60, startup=0.55, partner=0.50, details=0.45, date=0.40
        ),
        email_id="test123",
        extracted_at=datetime.now(timezone.utc),
    )
    providers["openai"] = openai

    return providers


class TestBestMatchBasics:
    """Test basic best-match functionality."""

    def test_selects_highest_confidence_result(self, mock_providers, health_tracker):
        """Test that best-match selects the result with highest aggregate confidence."""
        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        result, provider_used = strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should select Claude (highest confidence)
        assert provider_used == "claude"
        assert result.startup_name == "Claude Startup"

        # All providers should have been called (parallel queries)
        assert mock_providers["gemini"].extract_entities.call_count == 1
        assert mock_providers["claude"].extract_entities.call_count == 1
        assert mock_providers["openai"].extract_entities.call_count == 1

    def test_queries_all_providers_in_parallel(self, mock_providers, health_tracker):
        """Test that all providers are queried in parallel."""
        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        result, provider_used = strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # All providers should have been called exactly once
        for provider in mock_providers.values():
            assert provider.extract_entities.call_count == 1

    def test_skips_unhealthy_providers(self, mock_providers, health_tracker):
        """Test that unhealthy providers are skipped."""
        # Mark gemini as unhealthy
        for _ in range(3):
            health_tracker.record_failure("gemini", "Error")

        assert health_tracker.is_healthy("gemini") is False

        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        result, provider_used = strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should only query healthy providers
        assert mock_providers["gemini"].extract_entities.call_count == 0
        assert mock_providers["claude"].extract_entities.call_count == 1
        assert mock_providers["openai"].extract_entities.call_count == 1

        # Should select Claude (highest confidence among healthy providers)
        assert provider_used == "claude"


class TestAggregateConfidence:
    """Test aggregate confidence calculation."""

    def test_uses_weighted_average_for_confidence(self, mock_providers, health_tracker):
        """Test that aggregate confidence uses weighted average."""
        # Create provider with high confidence in important fields
        high_priority_provider = MagicMock()
        high_priority_provider.extract_entities.return_value = ExtractedEntities(
            person_in_charge="High Priority",
            startup_name="High Startup",
            partner_org="High Partner",
            details="Details",
            date=None,
            confidence=ConfidenceScores(
                person=0.95,  # weight=1.5
                startup=0.95,  # weight=1.5
                partner=0.95,  # weight=1.0
                details=0.60,  # weight=0.8
                date=0.40,  # weight=0.5
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )

        # Create provider with high confidence in less important fields
        low_priority_provider = MagicMock()
        low_priority_provider.extract_entities.return_value = ExtractedEntities(
            person_in_charge="Low Priority",
            startup_name="Low Startup",
            partner_org="Low Partner",
            details="Details",
            date=None,
            confidence=ConfidenceScores(
                person=0.60,  # weight=1.5
                startup=0.60,  # weight=1.5
                partner=0.60,  # weight=1.0
                details=0.95,  # weight=0.8
                date=0.95,  # weight=0.5
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )

        providers = {
            "high_priority": high_priority_provider,
            "low_priority": low_priority_provider,
        }

        strategy = BestMatchStrategy(provider_names=["high_priority", "low_priority"])

        result, provider_used = strategy.execute(
            providers=providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should select high_priority (weighted average favors person/startup/partner)
        assert provider_used == "high_priority"


class TestTieBreaking:
    """Test tie-breaking logic."""

    def test_tie_breaking_uses_priority_order(self, health_tracker):
        """Test that tie-breaking uses priority order when confidence is equal."""
        # Create two providers with identical confidence
        provider1 = MagicMock()
        provider1.extract_entities.return_value = ExtractedEntities(
            person_in_charge="Provider 1",
            startup_name="Startup 1",
            partner_org="Partner 1",
            details="Details 1",
            date=None,
            confidence=ConfidenceScores(
                person=0.85, startup=0.85, partner=0.85, details=0.85, date=0.85
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )

        provider2 = MagicMock()
        provider2.extract_entities.return_value = ExtractedEntities(
            person_in_charge="Provider 2",
            startup_name="Startup 2",
            partner_org="Partner 2",
            details="Details 2",
            date=None,
            confidence=ConfidenceScores(
                person=0.85, startup=0.85, partner=0.85, details=0.85, date=0.85
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )

        providers = {"provider1": provider1, "provider2": provider2}

        # provider2 has higher priority (appears first in list)
        strategy = BestMatchStrategy(provider_names=["provider2", "provider1"])

        result, provider_used = strategy.execute(
            providers=providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should select provider2 (first in priority order)
        assert provider_used == "provider2"
        assert result.startup_name == "Startup 2"

    def test_tie_breaking_uses_health_tracker_success_rate(
        self, mock_providers, health_tracker
    ):
        """Test that tie-breaking prefers provider with higher historical success rate."""
        # Make providers have same confidence
        for provider in mock_providers.values():
            provider.extract_entities.return_value = ExtractedEntities(
                person_in_charge="Person",
                startup_name="Startup",
                partner_org="Partner",
                details="Details",
                date=None,
                confidence=ConfidenceScores(
                    person=0.85, startup=0.85, partner=0.85, details=0.85, date=0.85
                ),
                email_id="test123",
                extracted_at=datetime.now(timezone.utc),
            )

        # Give gemini better historical success rate
        for _ in range(10):
            health_tracker.record_success("gemini", 100.0)

        # Give claude lower success rate
        for _ in range(5):
            health_tracker.record_success("claude", 100.0)
        for _ in range(2):
            health_tracker.record_failure("claude", "Error")

        strategy = BestMatchStrategy(provider_names=["claude", "gemini", "openai"])

        result, provider_used = strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should prefer gemini (higher success rate)
        assert provider_used == "gemini"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_handles_partial_failures(self, mock_providers, health_tracker):
        """Test that strategy handles when some providers fail."""
        # Make gemini fail
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError(
            "Gemini failed"
        )

        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        result, provider_used = strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should select best among successful providers (Claude)
        assert provider_used == "claude"

        # Should record gemini failure
        gemini_metrics = health_tracker.get_metrics("gemini")
        assert gemini_metrics.failure_count == 1

    def test_raises_all_providers_failed_when_all_fail(
        self, mock_providers, health_tracker
    ):
        """Test that AllProvidersFailedError is raised when all providers fail."""
        # Make all providers fail
        for provider in mock_providers.values():
            provider.extract_entities.side_effect = LLMAPIError("Provider failed")

        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        with pytest.raises(AllProvidersFailedError) as exc_info:
            strategy.execute(
                providers=mock_providers,
                email_text="test email",
                health_tracker=health_tracker,
            )

        assert "All providers failed" in str(exc_info.value)

    def test_handles_timeout_errors(self, mock_providers, health_tracker):
        """Test that timeout errors are handled gracefully."""
        # Make gemini timeout
        mock_providers["gemini"].extract_entities.side_effect = LLMTimeoutError()

        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        result, provider_used = strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should select best among successful providers
        assert provider_used == "claude"


class TestCompanyContext:
    """Test company context parameter passing."""

    def test_passes_company_context_to_all_providers(
        self, mock_providers, health_tracker
    ):
        """Test that company_context is passed to all providers."""
        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        company_context = "## Companies\n- Startup A\n- Partner B"

        strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
            company_context=company_context,
        )

        # Verify company_context was passed to all providers
        for provider in mock_providers.values():
            call_kwargs = provider.extract_entities.call_args[1]
            assert call_kwargs["company_context"] == company_context

    def test_passes_email_id_to_all_providers(self, mock_providers, health_tracker):
        """Test that email_id is passed to all providers."""
        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        email_id = "msg_12345"

        strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
            email_id=email_id,
        )

        # Verify email_id was passed to all providers
        for provider in mock_providers.values():
            call_kwargs = provider.extract_entities.call_args[1]
            assert call_kwargs["email_id"] == email_id


class TestHealthTracking:
    """Test integration with HealthTracker."""

    def test_records_success_for_all_providers(self, mock_providers, health_tracker):
        """Test that successful calls are recorded for all queried providers."""
        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # All providers should have success recorded
        for provider_name in ["gemini", "claude", "openai"]:
            metrics = health_tracker.get_metrics(provider_name)
            assert metrics.success_count == 1
            assert metrics.consecutive_failures == 0

    def test_records_failures_correctly(self, mock_providers, health_tracker):
        """Test that failures are recorded in health tracker."""
        # Make gemini fail
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError(
            "Gemini failed"
        )

        strategy = BestMatchStrategy(provider_names=["gemini", "claude", "openai"])

        strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Check gemini failure was recorded
        gemini_metrics = health_tracker.get_metrics("gemini")
        assert gemini_metrics.failure_count == 1

        # Check other providers recorded success
        claude_metrics = health_tracker.get_metrics("claude")
        assert claude_metrics.success_count == 1

        openai_metrics = health_tracker.get_metrics("openai")
        assert openai_metrics.success_count == 1


class TestSingleProvider:
    """Test edge case with single provider."""

    def test_works_with_single_provider(self, health_tracker):
        """Test that best-match works with just one provider."""
        provider = MagicMock()
        provider.extract_entities.return_value = ExtractedEntities(
            person_in_charge="Person",
            startup_name="Startup",
            partner_org="Partner",
            details="Details",
            date=None,
            confidence=ConfidenceScores(
                person=0.85, startup=0.85, partner=0.85, details=0.85, date=0.85
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )

        providers = {"only_provider": provider}

        strategy = BestMatchStrategy(provider_names=["only_provider"])

        result, provider_used = strategy.execute(
            providers=providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should use the only provider
        assert provider_used == "only_provider"
        assert provider.extract_entities.call_count == 1
