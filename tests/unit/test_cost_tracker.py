"""Unit tests for CostTracker.

Tests cost tracking functionality including:
- Usage recording
- Cost calculation with provider-specific pricing
- Metrics persistence and loading
- Atomic file writes
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from llm_orchestrator.cost_tracker import CostTracker
from llm_orchestrator.types import ProviderConfig


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def provider_configs():
    """Create sample provider configurations with pricing."""
    return {
        "claude": ProviderConfig(
            provider_name="claude",
            display_name="Claude Sonnet 4.5",
            model_id="claude-sonnet-4-5-20250929",
            api_key_env_var="ANTHROPIC_API_KEY",
            enabled=True,
            priority=1,
            timeout_seconds=60.0,
            max_retries=3,
            input_token_price=3.0,  # $3 per 1M tokens
            output_token_price=15.0,  # $15 per 1M tokens
        ),
        "openai": ProviderConfig(
            provider_name="openai",
            display_name="GPT-5 Mini",
            model_id="gpt-5-mini",
            api_key_env_var="OPENAI_API_KEY",
            enabled=True,
            priority=2,
            timeout_seconds=60.0,
            max_retries=3,
            input_token_price=0.15,  # $0.15 per 1M tokens
            output_token_price=0.60,  # $0.60 per 1M tokens
        ),
        "gemini": ProviderConfig(
            provider_name="gemini",
            display_name="Gemini 2.0 Flash",
            model_id="gemini-2.0-flash-exp",
            api_key_env_var="GEMINI_API_KEY",
            enabled=True,
            priority=3,
            timeout_seconds=60.0,
            max_retries=3,
            input_token_price=0.0,  # Free tier
            output_token_price=0.0,
        ),
    }


class TestCostTrackerInitialization:
    """Test CostTracker initialization and setup."""

    def test_initialization_creates_data_dir(self, temp_data_dir):
        """Test that initialization creates data directory."""
        data_dir = temp_data_dir / "llm_health"
        assert not data_dir.exists()

        tracker = CostTracker(data_dir=data_dir)

        assert data_dir.exists()
        assert (
            data_dir / "cost_metrics.json"
        ).exists() is False  # Not created until first write

    def test_initialization_with_provider_configs(
        self, temp_data_dir, provider_configs
    ):
        """Test initialization with provider configurations."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        assert tracker.provider_configs == provider_configs
        assert len(tracker.metrics) == 0  # No metrics until usage recorded


class TestUsageRecording:
    """Test usage recording and cost calculation."""

    def test_record_usage_basic(self, temp_data_dir, provider_configs):
        """Test basic usage recording."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)

        metrics = tracker.get_metrics("claude")
        assert metrics.total_api_calls == 1
        assert metrics.total_input_tokens == 1000
        assert metrics.total_output_tokens == 500
        assert metrics.total_tokens == 1500

    def test_record_usage_calculates_cost_correctly(
        self, temp_data_dir, provider_configs
    ):
        """Test cost calculation using provider-specific pricing.

        Claude pricing: $3/1M input, $15/1M output
        Usage: 1,000,000 input + 500,000 output
        Expected cost: (1M / 1M) * $3 + (500K / 1M) * $15 = $3 + $7.50 = $10.50
        """
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        tracker.record_usage("claude", input_tokens=1_000_000, output_tokens=500_000)

        metrics = tracker.get_metrics("claude")
        assert metrics.total_cost_usd == pytest.approx(10.50, rel=1e-4)

    def test_record_usage_free_provider(self, temp_data_dir, provider_configs):
        """Test cost calculation for free provider (Gemini)."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        tracker.record_usage("gemini", input_tokens=1_000_000, output_tokens=500_000)

        metrics = tracker.get_metrics("gemini")
        assert metrics.total_cost_usd == 0.0

    def test_record_usage_multiple_calls(self, temp_data_dir, provider_configs):
        """Test cumulative usage over multiple API calls."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # First call
        tracker.record_usage("openai", input_tokens=100_000, output_tokens=50_000)

        # Second call
        tracker.record_usage("openai", input_tokens=200_000, output_tokens=100_000)

        metrics = tracker.get_metrics("openai")
        assert metrics.total_api_calls == 2
        assert metrics.total_input_tokens == 300_000
        assert metrics.total_output_tokens == 150_000

        # Cost: (300K / 1M) * $0.15 + (150K / 1M) * $0.60
        #     = $0.045 + $0.090 = $0.135
        expected_cost = 0.135
        assert metrics.total_cost_usd == pytest.approx(expected_cost, rel=1e-4)

    def test_record_usage_updates_average_cost_per_email(
        self, temp_data_dir, provider_configs
    ):
        """Test average cost per email calculation."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # First call: $0.003 + $0.0075 = $0.0105
        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)
        metrics1 = tracker.get_metrics("claude")
        assert metrics1.average_cost_per_email == pytest.approx(0.0105, rel=1e-4)

        # Second call: $0.006 + $0.015 = $0.021
        # Average: (0.0105 + 0.021) / 2 = 0.01575
        tracker.record_usage("claude", input_tokens=2000, output_tokens=1000)
        metrics2 = tracker.get_metrics("claude")
        assert metrics2.average_cost_per_email == pytest.approx(0.01575, rel=1e-4)

    def test_record_usage_without_provider_config(self, temp_data_dir):
        """Test usage recording for provider without config (cost = 0)."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs={})

        tracker.record_usage("unknown_provider", input_tokens=1000, output_tokens=500)

        metrics = tracker.get_metrics("unknown_provider")
        assert metrics.total_api_calls == 1
        assert metrics.total_input_tokens == 1000
        assert metrics.total_output_tokens == 500
        assert metrics.total_cost_usd == 0.0  # No config, so cost is $0

    def test_record_usage_updates_timestamp(self, temp_data_dir, provider_configs):
        """Test that last_updated timestamp is set."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        before = datetime.now(timezone.utc)
        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)
        after = datetime.now(timezone.utc)

        metrics = tracker.get_metrics("claude")
        assert before <= metrics.last_updated <= after


class TestMetricsRetrieval:
    """Test metrics retrieval methods."""

    def test_get_metrics_creates_default_for_new_provider(self, temp_data_dir):
        """Test get_metrics creates default metrics for unknown provider."""
        tracker = CostTracker(data_dir=temp_data_dir)

        metrics = tracker.get_metrics("new_provider")

        assert metrics.provider_name == "new_provider"
        assert metrics.total_api_calls == 0
        assert metrics.total_cost_usd == 0.0

    def test_get_all_metrics(self, temp_data_dir, provider_configs):
        """Test get_all_metrics returns all tracked providers."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)
        tracker.record_usage("openai", input_tokens=2000, output_tokens=1000)

        all_metrics = tracker.get_all_metrics()

        assert len(all_metrics) == 2
        assert "claude" in all_metrics
        assert "openai" in all_metrics
        assert all_metrics["claude"].total_api_calls == 1
        assert all_metrics["openai"].total_api_calls == 1


class TestPersistence:
    """Test metrics persistence and loading."""

    def test_metrics_persisted_to_json(self, temp_data_dir, provider_configs):
        """Test that metrics are saved to JSON file."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)

        metrics_file = temp_data_dir / "cost_metrics.json"
        assert metrics_file.exists()

        # Verify JSON structure
        with open(metrics_file, "r") as f:
            data = json.load(f)

        assert "claude" in data
        assert data["claude"]["total_api_calls"] == 1
        assert data["claude"]["total_input_tokens"] == 1000

    def test_metrics_loaded_on_initialization(self, temp_data_dir, provider_configs):
        """Test that existing metrics are loaded on initialization."""
        # Create tracker and record usage
        tracker1 = CostTracker(
            data_dir=temp_data_dir, provider_configs=provider_configs
        )
        tracker1.record_usage("claude", input_tokens=1000, output_tokens=500)

        # Create new tracker instance (should load existing metrics)
        tracker2 = CostTracker(
            data_dir=temp_data_dir, provider_configs=provider_configs
        )

        metrics = tracker2.get_metrics("claude")
        assert metrics.total_api_calls == 1
        assert metrics.total_input_tokens == 1000
        assert metrics.total_output_tokens == 500

    def test_atomic_write_prevents_corruption(self, temp_data_dir, provider_configs):
        """Test that atomic write prevents file corruption."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # Record multiple usages
        for i in range(10):
            tracker.record_usage("claude", input_tokens=1000, output_tokens=500)

        # Verify file is valid JSON
        metrics_file = temp_data_dir / "cost_metrics.json"
        with open(metrics_file, "r") as f:
            data = json.load(f)

        assert data["claude"]["total_api_calls"] == 10

    def test_load_handles_corrupted_file(self, temp_data_dir):
        """Test that corrupted file is handled gracefully."""
        # Create corrupted JSON file
        metrics_file = temp_data_dir / "cost_metrics.json"
        with open(metrics_file, "w") as f:
            f.write("{invalid json")

        # Should initialize with empty metrics instead of crashing
        tracker = CostTracker(data_dir=temp_data_dir)

        assert len(tracker.metrics) == 0


class TestResetMetrics:
    """Test metrics reset functionality."""

    def test_reset_metrics(self, temp_data_dir, provider_configs):
        """Test resetting metrics for a provider."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # Record some usage
        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)

        metrics_before = tracker.get_metrics("claude")
        assert metrics_before.total_api_calls == 1

        # Reset metrics
        tracker.reset_metrics("claude")

        metrics_after = tracker.get_metrics("claude")
        assert metrics_after.total_api_calls == 0
        assert metrics_after.total_cost_usd == 0.0
        assert metrics_after.total_input_tokens == 0

    def test_reset_metrics_persisted(self, temp_data_dir, provider_configs):
        """Test that reset metrics are persisted to disk."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # Record usage and reset
        tracker.record_usage("claude", input_tokens=1000, output_tokens=500)
        tracker.reset_metrics("claude")

        # Create new tracker and verify reset persisted
        tracker2 = CostTracker(
            data_dir=temp_data_dir, provider_configs=provider_configs
        )

        metrics = tracker2.get_metrics("claude")
        assert metrics.total_api_calls == 0


class TestCostCalculation:
    """Test cost calculation edge cases."""

    def test_calculate_cost_zero_tokens(self, temp_data_dir, provider_configs):
        """Test cost calculation with zero tokens."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        tracker.record_usage("claude", input_tokens=0, output_tokens=0)

        metrics = tracker.get_metrics("claude")
        assert metrics.total_cost_usd == 0.0

    def test_calculate_cost_input_only(self, temp_data_dir, provider_configs):
        """Test cost calculation with input tokens only."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # 1M input tokens, 0 output tokens
        # Cost: (1M / 1M) * $3 + 0 = $3.00
        tracker.record_usage("claude", input_tokens=1_000_000, output_tokens=0)

        metrics = tracker.get_metrics("claude")
        assert metrics.total_cost_usd == pytest.approx(3.0, rel=1e-4)

    def test_calculate_cost_output_only(self, temp_data_dir, provider_configs):
        """Test cost calculation with output tokens only."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # 0 input tokens, 1M output tokens
        # Cost: 0 + (1M / 1M) * $15 = $15.00
        tracker.record_usage("claude", input_tokens=0, output_tokens=1_000_000)

        metrics = tracker.get_metrics("claude")
        assert metrics.total_cost_usd == pytest.approx(15.0, rel=1e-4)

    def test_calculate_cost_small_usage(self, temp_data_dir, provider_configs):
        """Test cost calculation with very small token usage."""
        tracker = CostTracker(data_dir=temp_data_dir, provider_configs=provider_configs)

        # 100 input tokens, 50 output tokens (typical small email)
        # Cost: (100 / 1M) * $3 + (50 / 1M) * $15
        #     = $0.0003 + $0.00075 = $0.00105
        tracker.record_usage("claude", input_tokens=100, output_tokens=50)

        metrics = tracker.get_metrics("claude")
        assert metrics.total_cost_usd == pytest.approx(0.00105, rel=1e-4)
