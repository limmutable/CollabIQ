"""Integration tests for ConsensusStrategy.

Tests the consensus strategy with mocked providers to verify:
- Parallel provider queries using asyncio
- Fuzzy matching for entity value merging
- Weighted voting for conflict resolution
- Minimum provider response validation
- Confidence score recalculation
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.exceptions import AllProvidersFailedError
from llm_orchestrator.strategies.consensus import ConsensusStrategy
from llm_provider.exceptions import LLMAPIError, LLMTimeoutError
from llm_provider.types import ConfidenceScores, ExtractedEntities


@pytest.fixture
def health_tracker(tmp_path):
    """Create HealthTracker for testing."""
    return HealthTracker(data_dir=tmp_path / "health", unhealthy_threshold=3)


@pytest.fixture
def mock_providers():
    """Create mock LLM providers."""
    providers = {}

    # Gemini - high confidence result
    gemini = MagicMock()
    gemini.extract_entities = MagicMock(
        return_value=ExtractedEntities(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계인터내셔널",
            details="11월 1주 PoC 시작 예정",
            date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            confidence=ConfidenceScores(
                person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )
    )
    providers["gemini"] = gemini

    # Claude - similar result with slight variations
    claude = MagicMock()
    claude.extract_entities = MagicMock(
        return_value=ExtractedEntities(
            person_in_charge="김철수",  # Same
            startup_name="본봄",  # Same
            partner_org="신세계",  # Slightly different (fuzzy match)
            details="11월 첫째주 PoC 시작",  # Slightly different
            date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            confidence=ConfidenceScores(
                person=0.90, startup=0.93, partner=0.85, details=0.88, date=0.90
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )
    )
    providers["claude"] = claude

    # OpenAI - different result (minority opinion)
    openai = MagicMock()
    openai.extract_entities = MagicMock(
        return_value=ExtractedEntities(
            person_in_charge="김영희",  # Different
            startup_name="본봄",  # Same
            partner_org="신세계",  # Same as Claude
            details="PoC 시작 예정",  # Less detailed
            date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            confidence=ConfidenceScores(
                person=0.75, startup=0.89, partner=0.82, details=0.70, date=0.85
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        )
    )
    providers["openai"] = openai

    return providers


class TestConsensusBasics:
    """Test basic consensus functionality."""

    @pytest.mark.asyncio
    async def test_queries_multiple_providers_in_parallel(
        self, mock_providers, health_tracker
    ):
        """Test that consensus queries all providers in parallel."""
        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # All providers should have been called
        assert mock_providers["gemini"].extract_entities.call_count == 1
        assert mock_providers["claude"].extract_entities.call_count == 1
        assert mock_providers["openai"].extract_entities.call_count == 1

        # Result should be merged (provider_used = "consensus")
        assert provider_used == "consensus"

    @pytest.mark.asyncio
    async def test_merges_results_with_fuzzy_matching(
        self, mock_providers, health_tracker
    ):
        """Test that consensus merges similar results using fuzzy matching."""
        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Startup name should be "본봄" (all agree)
        assert result.startup_name == "본봄"

        # Partner org should be merged from "신세계인터내셔널" and "신세계"
        # Fuzzy matching should recognize these as similar
        # Majority vote: "신세계" (2 votes) vs "신세계인터내셔널" (1 vote)
        # But weighted by confidence, "신세계인터내셔널" has higher confidence (0.88)
        # Expected: higher confidence + specificity wins
        assert result.partner_org in ["신세계인터내셔널", "신세계"]

        # Person should use majority/weighted vote
        # "김철수": 2 votes (gemini 0.95, claude 0.90)
        # "김영희": 1 vote (openai 0.75)
        assert result.person_in_charge == "김철수"

    @pytest.mark.asyncio
    async def test_recalculates_confidence_scores(
        self, mock_providers, health_tracker
    ):
        """Test that consensus recalculates confidence based on agreement."""
        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Confidence scores should be recalculated based on agreement
        # Fields with high agreement should have higher confidence
        # startup_name: all 3 agree → high confidence
        assert result.confidence.startup >= 0.85

        # person_in_charge: 2 agree → medium-high confidence
        assert result.confidence.person >= 0.80

        # All confidence scores should be valid (0.0-1.0)
        assert 0.0 <= result.confidence.person <= 1.0
        assert 0.0 <= result.confidence.startup <= 1.0
        assert 0.0 <= result.confidence.partner <= 1.0
        assert 0.0 <= result.confidence.details <= 1.0
        assert 0.0 <= result.confidence.date <= 1.0


class TestMinimumProviderValidation:
    """Test minimum provider response validation."""

    @pytest.mark.asyncio
    async def test_requires_minimum_two_responses(
        self, mock_providers, health_tracker
    ):
        """Test that consensus requires at least 2 provider responses."""
        # Make 2 providers fail, only 1 succeeds
        mock_providers["gemini"].extract_entities = MagicMock(
            side_effect=LLMAPIError("Gemini failed")
        )
        mock_providers["claude"].extract_entities = MagicMock(
            side_effect=LLMAPIError("Claude failed")
        )

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        # Should raise error because only 1 provider succeeded (< minimum 2)
        with pytest.raises(AllProvidersFailedError) as exc_info:
            await strategy.execute(
                providers=mock_providers,
                email_text="test email",
                health_tracker=health_tracker,
            )

        assert "Insufficient provider responses" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_succeeds_with_exactly_two_responses(
        self, mock_providers, health_tracker
    ):
        """Test that consensus succeeds with exactly 2 responses."""
        # Make 1 provider fail, 2 succeed
        mock_providers["openai"].extract_entities = MagicMock(
            side_effect=LLMTimeoutError()
        )

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should succeed with 2 responses
        assert provider_used == "consensus"
        assert result is not None

        # Only gemini and claude should have succeeded
        gemini_metrics = health_tracker.get_metrics("gemini")
        claude_metrics = health_tracker.get_metrics("claude")
        openai_metrics = health_tracker.get_metrics("openai")

        assert gemini_metrics.success_count == 1
        assert claude_metrics.success_count == 1
        assert openai_metrics.failure_count == 1


class TestHealthTracking:
    """Test integration with HealthTracker."""

    @pytest.mark.asyncio
    async def test_skips_unhealthy_providers(self, mock_providers, health_tracker):
        """Test that unhealthy providers are skipped."""
        # Mark gemini as unhealthy
        for _ in range(3):
            health_tracker.record_failure("gemini", "Error")

        assert health_tracker.is_healthy("gemini") is False

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Gemini should have been skipped
        assert mock_providers["gemini"].extract_entities.call_count == 0

        # Claude and OpenAI should have been called
        assert mock_providers["claude"].extract_entities.call_count == 1
        assert mock_providers["openai"].extract_entities.call_count == 1

        # Should still succeed with 2 healthy providers
        assert provider_used == "consensus"

    @pytest.mark.asyncio
    async def test_records_success_for_all_providers(
        self, mock_providers, health_tracker
    ):
        """Test that successful calls are recorded for all providers."""
        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # All providers should have success recorded
        for provider_name in ["gemini", "claude", "openai"]:
            metrics = health_tracker.get_metrics(provider_name)
            assert metrics.success_count == 1
            assert metrics.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_records_failures_for_failed_providers(
        self, mock_providers, health_tracker
    ):
        """Test that failures are recorded for failed providers."""
        # Make openai fail
        mock_providers["openai"].extract_entities = MagicMock(
            side_effect=LLMAPIError("OpenAI failed")
        )

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # OpenAI failure should be recorded
        openai_metrics = health_tracker.get_metrics("openai")
        assert openai_metrics.failure_count == 1
        assert openai_metrics.consecutive_failures == 1

        # Gemini and Claude success should be recorded
        gemini_metrics = health_tracker.get_metrics("gemini")
        claude_metrics = health_tracker.get_metrics("claude")
        assert gemini_metrics.success_count == 1
        assert claude_metrics.success_count == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_raises_error_when_all_providers_fail(
        self, mock_providers, health_tracker
    ):
        """Test that error is raised when all providers fail."""
        # Make all providers fail
        for provider in mock_providers.values():
            provider.extract_entities = MagicMock(side_effect=LLMAPIError("Failed"))

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        with pytest.raises(AllProvidersFailedError) as exc_info:
            await strategy.execute(
                providers=mock_providers,
                email_text="test email",
                health_tracker=health_tracker,
            )

        assert "Insufficient provider responses" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_error_when_all_providers_unhealthy(
        self, mock_providers, health_tracker
    ):
        """Test that error is raised when all providers are unhealthy."""
        # Mark all providers as unhealthy
        for provider_name in ["gemini", "claude", "openai"]:
            for _ in range(3):
                health_tracker.record_failure(provider_name, "Error")

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        with pytest.raises(AllProvidersFailedError) as exc_info:
            await strategy.execute(
                providers=mock_providers,
                email_text="test email",
                health_tracker=health_tracker,
            )

        # Error message is about insufficient healthy providers, not responses
        assert "Insufficient healthy providers" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handles_unexpected_exceptions(self, mock_providers, health_tracker):
        """Test that unexpected exceptions are handled gracefully."""
        # Make one provider raise unexpected exception
        mock_providers["openai"].extract_entities = MagicMock(
            side_effect=ValueError("Unexpected error")
        )

        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should still succeed with 2 providers
        assert provider_used == "consensus"

        # OpenAI failure should be recorded
        openai_metrics = health_tracker.get_metrics("openai")
        assert openai_metrics.failure_count == 1


class TestCompanyContext:
    """Test company context parameter passing."""

    @pytest.mark.asyncio
    async def test_passes_company_context_to_all_providers(
        self, mock_providers, health_tracker
    ):
        """Test that company_context is passed to all providers."""
        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        company_context = "## Companies\n- 본봄\n- 신세계인터내셔널"

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
            company_context=company_context,
        )

        # Verify company_context was passed to all providers
        for provider_name in ["gemini", "claude", "openai"]:
            call_kwargs = mock_providers[provider_name].extract_entities.call_args[1]
            assert call_kwargs["company_context"] == company_context

    @pytest.mark.asyncio
    async def test_passes_email_id_to_all_providers(
        self, mock_providers, health_tracker
    ):
        """Test that email_id is passed to all providers."""
        strategy = ConsensusStrategy(
            provider_names=["gemini", "claude", "openai"],
            fuzzy_threshold=0.85,
            min_agreement=2,
        )

        email_id = "msg_12345"

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
            email_id=email_id,
        )

        # Verify email_id was passed to all providers
        for provider_name in ["gemini", "claude", "openai"]:
            call_kwargs = mock_providers[provider_name].extract_entities.call_args[1]
            assert call_kwargs["email_id"] == email_id
