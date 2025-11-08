"""Integration tests for LLMOrchestrator.

Tests the complete orchestration system with mocked providers to verify:
- End-to-end entity extraction with failover
- Provider status monitoring
- Strategy switching
- Provider health testing
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.llm_adapters.health_tracker import HealthTracker
from src.llm_orchestrator.exceptions import (
    AllProvidersFailedError,
    InvalidProviderError,
    InvalidStrategyError,
)
from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.types import OrchestrationConfig
from src.llm_provider.exceptions import LLMAPIError
from src.llm_provider.types import ConfidenceScores, ExtractedEntities


@pytest.fixture
def orchestration_config():
    """Create orchestration configuration for testing."""
    return OrchestrationConfig(
        default_strategy="failover",
        provider_priority=["gemini", "claude", "openai"],
        unhealthy_threshold=3,
        timeout_seconds=90.0,
    )


@pytest.fixture
def mock_providers():
    """Create mock LLM providers."""
    providers = {}

    for name in ["gemini", "claude", "openai"]:
        provider = MagicMock()
        provider.extract_entities.return_value = ExtractedEntities(
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
        )
        providers[name] = provider

    return providers


@pytest.fixture
def orchestrator(mock_providers, orchestration_config, tmp_path):
    """Create LLMOrchestrator for testing."""
    health_tracker = HealthTracker(
        data_dir=tmp_path / "health", unhealthy_threshold=3
    )

    return LLMOrchestrator(
        providers=mock_providers,
        config=orchestration_config,
        health_tracker=health_tracker,
    )


class TestOrchestratorBasics:
    """Test basic orchestrator functionality."""

    def test_extract_entities_uses_default_strategy(self, orchestrator):
        """Test that extract_entities uses the default strategy (failover)."""
        result = orchestrator.extract_entities("test email")

        # Should use gemini (first in priority)
        assert result.startup_name == "Startup from gemini"

    def test_extract_entities_with_strategy_override(
        self, orchestrator, mock_providers
    ):
        """Test that strategy can be overridden per call."""
        # Make gemini fail to test failover
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError(
            "Gemini failed"
        )

        result = orchestrator.extract_entities("test email", strategy="failover")

        # Should use claude (second in priority)
        assert result.startup_name == "Startup from claude"

    def test_extract_entities_passes_company_context(
        self, orchestrator, mock_providers
    ):
        """Test that company_context is passed to provider."""
        company_context = "## Companies\n- Company A"

        orchestrator.extract_entities(
            "test email", company_context=company_context
        )

        # Verify company_context was passed
        call_kwargs = mock_providers["gemini"].extract_entities.call_args[1]
        assert call_kwargs["company_context"] == company_context

    def test_extract_entities_raises_invalid_strategy_error(self, orchestrator):
        """Test that invalid strategy raises InvalidStrategyError."""
        with pytest.raises(InvalidStrategyError) as exc_info:
            orchestrator.extract_entities("test email", strategy="invalid_strategy")

        assert "invalid_strategy" in str(exc_info.value)


class TestProviderStatus:
    """Test provider status monitoring."""

    def test_get_provider_status_returns_all_providers(self, orchestrator):
        """Test that get_provider_status returns status for all providers."""
        status = orchestrator.get_provider_status()

        assert len(status) == 3
        assert "gemini" in status
        assert "claude" in status
        assert "openai" in status

    def test_get_provider_status_includes_health_metrics(self, orchestrator):
        """Test that provider status includes health metrics."""
        # Record some successes
        orchestrator.extract_entities("test email 1")
        orchestrator.extract_entities("test email 2")

        status = orchestrator.get_provider_status()

        gemini_status = status["gemini"]
        assert gemini_status.provider_name == "gemini"
        assert gemini_status.health_status == "healthy"
        assert gemini_status.enabled is True
        assert gemini_status.total_api_calls == 2
        assert gemini_status.circuit_breaker_state == "closed"

    def test_get_provider_status_reflects_failures(
        self, orchestrator, mock_providers
    ):
        """Test that provider status reflects failures."""
        # Make gemini fail 3 times
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError(
            "API Error"
        )

        for _ in range(3):
            try:
                orchestrator.extract_entities("test email")
            except (LLMAPIError, AllProvidersFailedError):
                pass

        status = orchestrator.get_provider_status()

        gemini_status = status["gemini"]
        assert gemini_status.health_status == "unhealthy"
        assert gemini_status.circuit_breaker_state == "open"


class TestStrategyManagement:
    """Test strategy switching."""

    def test_set_strategy_changes_active_strategy(self, orchestrator):
        """Test that set_strategy changes the active strategy."""
        assert orchestrator.get_active_strategy() == "failover"

        orchestrator.set_strategy("failover")

        assert orchestrator.get_active_strategy() == "failover"

    def test_set_strategy_raises_invalid_strategy_error(self, orchestrator):
        """Test that invalid strategy raises InvalidStrategyError."""
        with pytest.raises(InvalidStrategyError):
            orchestrator.set_strategy("invalid_strategy")


class TestProviderTesting:
    """Test provider health testing."""

    def test_test_provider_returns_true_for_healthy(self, orchestrator):
        """Test that test_provider returns True for healthy provider."""
        assert orchestrator.test_provider("gemini") is True

    def test_test_provider_returns_false_for_unhealthy(
        self, orchestrator, mock_providers
    ):
        """Test that test_provider returns False for unhealthy provider."""
        # Make gemini fail 3 times to mark it unhealthy
        mock_providers["gemini"].extract_entities.side_effect = LLMAPIError(
            "API Error"
        )

        for _ in range(3):
            try:
                orchestrator.extract_entities("test email")
            except (LLMAPIError, AllProvidersFailedError):
                pass

        assert orchestrator.test_provider("gemini") is False

    def test_test_provider_raises_invalid_provider_error(self, orchestrator):
        """Test that testing unknown provider raises InvalidProviderError."""
        with pytest.raises(InvalidProviderError):
            orchestrator.test_provider("unknown_provider")


class TestOrchestratorFromConfig:
    """Test orchestrator creation from configuration."""

    @patch("src.llm_adapters.gemini_adapter.GeminiAdapter")
    @patch("src.llm_adapters.claude_adapter.ClaudeAdapter")
    @patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY": "test_gemini_key",
            "ANTHROPIC_API_KEY": "test_claude_key",
        },
    )
    def test_from_config_creates_orchestrator(
        self, mock_claude_adapter, mock_gemini_adapter, orchestration_config, tmp_path
    ):
        """Test that from_config creates orchestrator with providers."""
        # Create orchestrator
        orchestrator = LLMOrchestrator.from_config(
            config=orchestration_config, data_dir=tmp_path / "health"
        )

        # Verify providers were created
        assert "gemini" in orchestrator.get_available_providers()
        assert "claude" in orchestrator.get_available_providers()

        # Verify adapters were initialized
        assert mock_gemini_adapter.called
        assert mock_claude_adapter.called

    @patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "",
        },
        clear=True,
    )
    def test_from_config_skips_providers_without_api_keys(
        self, orchestration_config, tmp_path
    ):
        """Test that providers without API keys are skipped."""
        orchestrator = LLMOrchestrator.from_config(
            config=orchestration_config, data_dir=tmp_path / "health"
        )

        # Should have no providers (no API keys available)
        assert len(orchestrator.get_available_providers()) == 0


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_active_strategy(self, orchestrator):
        """Test that get_active_strategy returns current strategy."""
        assert orchestrator.get_active_strategy() == "failover"

    def test_get_available_providers(self, orchestrator):
        """Test that get_available_providers returns provider list."""
        providers = orchestrator.get_available_providers()

        assert len(providers) == 3
        assert "gemini" in providers
        assert "claude" in providers
        assert "openai" in providers
