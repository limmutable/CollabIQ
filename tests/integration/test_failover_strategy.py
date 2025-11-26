"""Integration tests for FailoverStrategy.

Tests the failover strategy with mocked providers to verify:
- Sequential provider attempts in priority order
- Automatic skipping of unhealthy providers
- Health tracking integration
- Error handling and recovery
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.exceptions import AllProvidersFailedError
from llm_orchestrator.strategies.failover import FailoverStrategy
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

    for name in ["gemini", "claude", "openai"]:
        provider = MagicMock()
        provider.extract_entities = AsyncMock(return_value=ExtractedEntities(
            person_in_charge=f"Person from {name}",
            startup_name=f"Startup from {name}",
            partner_org="Partner",
            details="Details",
            date=None,
            confidence=ConfidenceScores(
                person=0.9, startup=0.9, partner=0.9, details=0.9, date=0.0
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        ))
        providers[name] = provider

    return providers


class TestFailoverBasics:
    """Test basic failover functionality."""

    @pytest.mark.asyncio
    async def test_uses_first_provider_when_available(self, mock_providers, health_tracker):
        """Test that failover uses the first provider in priority order."""
        strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should use gemini (first in priority)
        assert provider_used == "gemini"
        assert result.startup_name == "Startup from gemini"

        # Only gemini should have been called
        assert mock_providers["gemini"].extract_entities.call_count == 1
        assert mock_providers["claude"].extract_entities.call_count == 0
        assert mock_providers["openai"].extract_entities.call_count == 0

    @pytest.mark.asyncio
    async def test_tries_providers_in_priority_order(self, mock_providers, health_tracker):
        """Test that providers are tried in specified priority order."""
        # Make first provider fail
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError(
            "Gemini failed"
        )

        strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should use claude (second in priority)
        assert provider_used == "claude"
        assert result.startup_name == "Startup from claude"

        # Gemini and Claude should have been called
        assert mock_providers["gemini"].extract_entities.call_count == 1
        assert mock_providers["claude"].extract_entities.call_count == 1
        assert mock_providers["openai"].extract_entities.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_first_successful_result(self, mock_providers, health_tracker):
        """Test that failover returns first successful result."""
        # Make first two fail
        mock_providers["gemini"].extract_entities.side_effect = LLMTimeoutError()
        mock_providers["claude"].extract_entities.side_effect = LLMAPIError(
            "Claude failed"
        )

        strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should use openai (third in priority)
        assert provider_used == "openai"
        assert result.startup_name == "Startup from openai"


class TestHealthTracking:
    """Test integration with HealthTracker."""

    @pytest.mark.asyncio
    async def test_skips_unhealthy_providers(self, mock_providers, health_tracker):
        """Test that unhealthy providers are skipped."""
        # Mark gemini as unhealthy by recording failures
        for _ in range(3):
            health_tracker.record_failure("gemini", "Error")

        # Verify gemini is unhealthy
        assert health_tracker.is_healthy("gemini") is False

        strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should skip gemini and use claude
        assert provider_used == "claude"
        assert mock_providers["gemini"].extract_entities.call_count == 0
        assert mock_providers["claude"].extract_entities.call_count == 1

    @pytest.mark.asyncio
    async def test_records_success_in_health_tracker(self, mock_providers, health_tracker):
        """Test that successful calls are recorded in health tracker."""
        strategy = FailoverStrategy(priority_order=["gemini"])

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Check health metrics were updated
        metrics = health_tracker.get_metrics("gemini")
        assert metrics.success_count == 1
        assert metrics.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_records_failure_in_health_tracker(self, mock_providers, health_tracker):
        """Test that failed calls are recorded in health tracker."""
        # Make provider fail
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError("API Error")

        strategy = FailoverStrategy(priority_order=["gemini", "claude"])

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Check gemini failure was recorded
        gemini_metrics = health_tracker.get_metrics("gemini")
        assert gemini_metrics.failure_count == 1
        assert gemini_metrics.consecutive_failures == 1

        # Check claude success was recorded
        claude_metrics = health_tracker.get_metrics("claude")
        assert claude_metrics.success_count == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_raises_all_providers_failed_when_all_fail(
        self, mock_providers, health_tracker
    ):
        """Test that AllProvidersFailedError is raised when all providers fail."""
        # Make all providers fail
        for provider in mock_providers.values():
            provider.extract_entities.side_effect = LLMAPIError("Provider failed")

        strategy = FailoverStrategy(priority_order=["gemini", "claude", "openai"])

        with pytest.raises(AllProvidersFailedError) as exc_info:
            await strategy.execute(
                providers=mock_providers,
                email_text="test email",
                health_tracker=health_tracker,
            )

        assert "All providers failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handles_unexpected_exceptions(self, mock_providers, health_tracker):
        """Test that unexpected exceptions are handled gracefully."""
        # Make first provider raise unexpected exception
        mock_providers["gemini"].extract_entities.side_effect = ValueError(
            "Unexpected error"
        )

        strategy = FailoverStrategy(priority_order=["gemini", "claude"])

        result, provider_used = await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
        )

        # Should still try next provider
        assert provider_used == "claude"

        # Should record failure
        gemini_metrics = health_tracker.get_metrics("gemini")
        assert gemini_metrics.failure_count == 1

    @pytest.mark.asyncio
    async def test_skips_unconfigured_providers(self, health_tracker):
        """Test that providers in priority order but not in providers dict are skipped."""
        # Only configure gemini, not claude
        providers = {"gemini": MagicMock()}
        providers["gemini"].extract_entities = AsyncMock(return_value=ExtractedEntities(
            person_in_charge="Person",
            startup_name="Startup",
            partner_org="Partner",
            details="Details",
            date=None,
            confidence=ConfidenceScores(
                person=0.9, startup=0.9, partner=0.9, details=0.9, date=0.0
            ),
            email_id="test123",
            extracted_at=datetime.now(timezone.utc),
        ))

        # Priority includes claude, but it's not in providers dict
        strategy = FailoverStrategy(priority_order=["claude", "gemini"])

        result, provider_used = await strategy.execute(
            providers=providers, email_text="test email", health_tracker=health_tracker
        )

        # Should skip claude and use gemini
        assert provider_used == "gemini"


class TestCompanyContext:
    """Test company context parameter passing."""

    @pytest.mark.asyncio
    async def test_passes_company_context_to_provider(self, mock_providers, health_tracker):
        """Test that company_context is passed to provider's extract_entities."""
        strategy = FailoverStrategy(priority_order=["gemini"])

        company_context = "## Companies\n- Startup A\n- Partner B"

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
            company_context=company_context,
        )

        # Verify company_context was passed
        call_kwargs = mock_providers["gemini"].extract_entities.call_args[1]
        assert call_kwargs["company_context"] == company_context

    @pytest.mark.asyncio
    async def test_passes_email_id_to_provider(self, mock_providers, health_tracker):
        """Test that email_id is passed to provider's extract_entities."""
        strategy = FailoverStrategy(priority_order=["gemini"])

        email_id = "msg_12345"

        await strategy.execute(
            providers=mock_providers,
            email_text="test email",
            health_tracker=health_tracker,
            email_id=email_id,
        )

        # Verify email_id was passed
        call_kwargs = mock_providers["gemini"].extract_entities.call_args[1]
        assert call_kwargs["email_id"] == email_id
