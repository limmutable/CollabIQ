#!/usr/bin/env python
"""Demo script to showcase Provider Health Monitoring & Visibility features.

This script demonstrates:
1. CostTracker - recording usage and calculating costs
2. CLI status command - displaying health and cost metrics
3. Integration with orchestrator

Note: Requires GEMINI_API_KEY environment variable to be set.
"""

import os
from datetime import datetime, timezone

from src.llm_orchestrator.cost_tracker import CostTracker
from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.types import OrchestrationConfig, ProviderConfig

print("\n" + "=" * 80)
print("Provider Health Monitoring & Visibility - Demo")
print("=" * 80 + "\n")

# =============================================================================
# 1. Demonstrate CostTracker
# =============================================================================

print("[1] CostTracker - Recording API usage and calculating costs\n")

provider_configs = {
    "gemini": ProviderConfig(
        provider_name="gemini",
        display_name="Google Gemini 2.0 Flash",
        model_id="gemini-2.0-flash-exp",
        api_key_env_var="GEMINI_API_KEY",
        enabled=True,
        priority=1,
        timeout_seconds=60.0,
        max_retries=3,
        input_token_price=0.0,  # Free tier
        output_token_price=0.0,
    ),
    "claude": ProviderConfig(
        provider_name="claude",
        display_name="Claude Sonnet 4.5",
        model_id="claude-sonnet-4-5-20250929",
        api_key_env_var="ANTHROPIC_API_KEY",
        enabled=True,
        priority=2,
        timeout_seconds=60.0,
        max_retries=3,
        input_token_price=3.0,  # $3 per 1M input tokens
        output_token_price=15.0,  # $15 per 1M output tokens
    ),
    "openai": ProviderConfig(
        provider_name="openai",
        display_name="GPT-5 Mini",
        model_id="gpt-5-mini",
        api_key_env_var="OPENAI_API_KEY",
        enabled=True,
        priority=3,
        timeout_seconds=60.0,
        max_retries=3,
        input_token_price=0.15,  # $0.15 per 1M input tokens
        output_token_price=0.60,  # $0.60 per 1M output tokens
    ),
}

# Create CostTracker with sample provider configs
cost_tracker = CostTracker(
    data_dir="data/llm_health",
    provider_configs=provider_configs,
)

# Simulate some API usage
print("Simulating API usage:")
print("  - Claude: 10,000 input tokens, 5,000 output tokens")
cost_tracker.record_usage("claude", input_tokens=10000, output_tokens=5000)

print("  - OpenAI: 5,000 input tokens, 2,500 output tokens")
cost_tracker.record_usage("openai", input_tokens=5000, output_tokens=2500)

print("  - Gemini: 8,000 input tokens, 4,000 output tokens (free)")
cost_tracker.record_usage("gemini", input_tokens=8000, output_tokens=4000)

print("\nCost Metrics:")
for provider_name, metrics in cost_tracker.get_all_metrics().items():
    print(f"\n  {provider_name.title()}:")
    print(f"    API Calls: {metrics.total_api_calls}")
    print(f"    Input Tokens: {metrics.total_input_tokens:,}")
    print(f"    Output Tokens: {metrics.total_output_tokens:,}")
    print(f"    Total Cost: ${metrics.total_cost_usd:.6f}")
    print(f"    Avg Cost/Email: ${metrics.average_cost_per_email:.6f}")

# Calculate expected costs manually for verification
claude_cost = (10000 / 1_000_000) * 3.0 + (5000 / 1_000_000) * 15.0
openai_cost = (5000 / 1_000_000) * 0.15 + (2500 / 1_000_000) * 0.60

print("\nExpected Costs (verification):")
print(f"  Claude: ${claude_cost:.6f}")
print(f"  OpenAI: ${openai_cost:.6f}")
print(f"  Gemini: $0.000000 (free tier)")

# =============================================================================
# 2. Demonstrate Orchestrator Integration
# =============================================================================

print("\n" + "=" * 80)
print("[2] Orchestrator - Provider status and health metrics\n")

# Check if Gemini is configured
if not os.getenv("GEMINI_API_KEY"):
    print("⚠ GEMINI_API_KEY not set. Skipping orchestrator demo.")
    print("\nTo test orchestrator integration:")
    print("  export GEMINI_API_KEY=your_api_key")
    print("  python demo_health_monitoring.py")
else:
    # Create orchestrator
    config = OrchestrationConfig(
        default_strategy="failover",
        provider_priority=["gemini", "claude", "openai"],
    )

    orchestrator = LLMOrchestrator.from_config(config)

    # Get provider status
    provider_status = orchestrator.get_provider_status()

    print("Provider Health Status:")
    for provider_name, status in provider_status.items():
        print(f"\n  {provider_name.title()}:")
        print(f"    Health: {status.health_status}")
        print(f"    Circuit Breaker: {status.circuit_breaker_state}")
        print(f"    Success Rate: {status.success_rate:.1%}")
        print(f"    Total API Calls: {status.total_api_calls}")
        print(f"    Avg Response Time: {status.average_response_time_ms:.0f}ms")

    # Display cost tracking integration
    if orchestrator.cost_tracker:
        print("\n\nCost Tracking (via Orchestrator):")
        cost_metrics = orchestrator.cost_tracker.get_all_metrics()
        for provider_name in provider_status.keys():
            metrics = cost_metrics.get(provider_name)
            if metrics and metrics.total_api_calls > 0:
                print(f"\n  {provider_name.title()}:")
                print(f"    Total Cost: ${metrics.total_cost_usd:.6f}")
                print(f"    Avg Cost/Email: ${metrics.average_cost_per_email:.6f}")

# =============================================================================
# 3. CLI Commands Demo
# =============================================================================

print("\n" + "=" * 80)
print("[3] CLI Commands - How to use\n")

print("Available commands:")
print()
print("  # View basic health status")
print("  collabiq llm status")
print()
print("  # View detailed status with cost metrics")
print("  collabiq llm status --detailed")
print()
print("  # Test specific provider")
print("  collabiq llm test gemini")
print("  collabiq llm test claude")
print()
print("  # Set orchestration strategy")
print("  collabiq llm set-strategy failover")
print()

print("=" * 80)
print("\nDemo complete!")
print("\nNext steps:")
print("  1. Run 'collabiq llm status' to see real provider health")
print("  2. Run 'collabiq llm status --detailed' for cost metrics")
print("  3. Process some emails to generate real usage data")
print()
