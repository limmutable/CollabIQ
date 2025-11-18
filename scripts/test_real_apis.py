#!/usr/bin/env python3
"""Quick test script for real API integration.

This script tests the LLMOrchestrator with real Claude and OpenAI APIs.
Before running, ensure you've set these environment variables in .env:
- ANTHROPIC_API_KEY
- OPENAI_API_KEY
- GEMINI_API_KEY (should already be set)

Usage:
    python test_real_apis.py
"""

import logging
from pathlib import Path

from src.config.settings import get_settings
from src.llm_orchestrator.orchestrator import LLMOrchestrator
from src.llm_orchestrator.types import OrchestrationConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_api_keys() -> dict[str, bool]:
    """Check which API keys are available."""
    settings = get_settings()

    keys = {
        "GEMINI_API_KEY": bool(settings.get_secret_or_env("GEMINI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(settings.get_secret_or_env("ANTHROPIC_API_KEY")),
        "OPENAI_API_KEY": bool(settings.get_secret_or_env("OPENAI_API_KEY")),
    }

    logger.info("API Key Status:")
    for key, available in keys.items():
        status = "✓ Available" if available else "✗ Missing"
        logger.info(f"  {key}: {status}")

    return keys


def test_failover_strategy(orchestrator: LLMOrchestrator) -> None:
    """Test failover strategy with real APIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Failover Strategy")
    logger.info("=" * 80)

    # Korean email text (similar to MVP test case)
    email_text = """
    어제 신세계와 본봄 킥오프 미팅 진행했습니다.
    담당자는 김민수 이사님이고, 다음 주 월요일에 후속 미팅 예정입니다.
    """

    logger.info(f"Email text: {email_text.strip()}")
    logger.info("\nExecuting failover strategy...")

    try:
        entities = orchestrator.extract_entities(
            email_text=email_text,
            strategy="failover",
            email_id="real_test_failover_001",
        )

        logger.info("\n✓ Extraction successful!")
        logger.info(
            f"  Person: {entities.person_in_charge} (confidence: {entities.confidence.person:.2f})"
        )
        logger.info(
            f"  Startup: {entities.startup_name} (confidence: {entities.confidence.startup:.2f})"
        )
        logger.info(
            f"  Partner: {entities.partner_org} (confidence: {entities.confidence.partner:.2f})"
        )
        logger.info(
            f"  Date: {entities.date} (confidence: {entities.confidence.date:.2f})"
        )

    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}", exc_info=True)


def test_consensus_strategy(orchestrator: LLMOrchestrator) -> None:
    """Test consensus strategy with real APIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Consensus Strategy")
    logger.info("=" * 80)

    # Check if we have at least 2 providers
    available_providers = orchestrator.get_available_providers()
    if len(available_providers) < 2:
        logger.warning(
            f"⚠ Consensus requires at least 2 providers, only {len(available_providers)} available"
        )
        logger.warning("  Skipping consensus test")
        return

    email_text = """
    어제 카카오벤처스의 이지은 심사역님과 미팅했습니다.
    스타트업 '스마트팜코리아'에 대한 투자 검토를 논의했고,
    다음 주 수요일에 2차 미팅 예정입니다.
    """

    logger.info(f"Email text: {email_text.strip()}")
    logger.info(
        f"\nExecuting consensus strategy across {len(available_providers)} providers..."
    )

    try:
        entities = orchestrator.extract_entities(
            email_text=email_text,
            strategy="consensus",
            email_id="real_test_consensus_001",
        )

        logger.info("\n✓ Consensus extraction successful!")
        logger.info(
            f"  Person: {entities.person_in_charge} (confidence: {entities.confidence.person:.2f})"
        )
        logger.info(
            f"  Startup: {entities.startup_name} (confidence: {entities.confidence.startup:.2f})"
        )
        logger.info(
            f"  Partner: {entities.partner_org} (confidence: {entities.confidence.partner:.2f})"
        )
        logger.info(
            f"  Date: {entities.date} (confidence: {entities.confidence.date:.2f})"
        )

    except Exception as e:
        logger.error(f"✗ Consensus extraction failed: {e}", exc_info=True)


def test_best_match_strategy(orchestrator: LLMOrchestrator) -> None:
    """Test best-match strategy with real APIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Best-Match Strategy")
    logger.info("=" * 80)

    # Check if we have at least 2 providers
    available_providers = orchestrator.get_available_providers()
    if len(available_providers) < 2:
        logger.warning(
            f"⚠ Best-match requires at least 2 providers, only {len(available_providers)} available"
        )
        logger.warning("  Skipping best-match test")
        return

    email_text = """
    오늘 아침 서울대학교 기술지주회사의 박준호 팀장님과
    바이오테크 스타트업 '제노믹스랩' 관련 협의했습니다.
    특허 기술이전 계약 검토 중이며, 11월 15일 최종 미팅 예정입니다.
    """

    logger.info(f"Email text: {email_text.strip()}")
    logger.info(
        f"\nExecuting best-match strategy across {len(available_providers)} providers..."
    )

    try:
        entities = orchestrator.extract_entities(
            email_text=email_text,
            strategy="best_match",
            email_id="real_test_bestmatch_001",
        )

        logger.info("\n✓ Best-match extraction successful!")
        logger.info(
            f"  Person: {entities.person_in_charge} (confidence: {entities.confidence.person:.2f})"
        )
        logger.info(
            f"  Startup: {entities.startup_name} (confidence: {entities.confidence.startup:.2f})"
        )
        logger.info(
            f"  Partner: {entities.partner_org} (confidence: {entities.confidence.partner:.2f})"
        )
        logger.info(
            f"  Date: {entities.date} (confidence: {entities.confidence.date:.2f})"
        )

    except Exception as e:
        logger.error(f"✗ Best-match extraction failed: {e}", exc_info=True)


def test_cost_tracking(orchestrator: LLMOrchestrator) -> None:
    """Test cost tracking functionality."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Cost Tracking")
    logger.info("=" * 80)

    if not orchestrator.cost_tracker:
        logger.warning("⚠ Cost tracker not initialized")
        return

    # Get cost metrics
    cost_metrics = orchestrator.cost_tracker.get_all_metrics()

    logger.info("\nCost Summary:")
    total_cost = 0.0
    total_calls = 0

    for provider_name, metrics in cost_metrics.items():
        logger.info(f"\n  {provider_name.upper()}:")
        logger.info(f"    Total calls: {metrics.total_api_calls}")
        logger.info(f"    Input tokens: {metrics.total_input_tokens:,}")
        logger.info(f"    Output tokens: {metrics.total_output_tokens:,}")
        logger.info(f"    Total cost: ${metrics.total_cost_usd:.6f}")
        logger.info(f"    Average cost/call: ${metrics.average_cost_per_call:.6f}")

        total_cost += metrics.total_cost_usd
        total_calls += metrics.total_api_calls

    logger.info("\n  TOTAL ACROSS ALL PROVIDERS:")
    logger.info(f"    Total calls: {total_calls}")
    logger.info(f"    Total cost: ${total_cost:.6f}")
    if total_calls > 0:
        logger.info(f"    Average cost/call: ${total_cost / total_calls:.6f}")


def test_provider_health(orchestrator: LLMOrchestrator) -> None:
    """Test provider health monitoring."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Provider Health Status")
    logger.info("=" * 80)

    status = orchestrator.get_provider_status()

    for provider_name, pstatus in status.items():
        logger.info(f"\n  {provider_name.upper()}:")
        logger.info(f"    Health: {pstatus.health_status}")
        logger.info(f"    Circuit breaker: {pstatus.circuit_breaker_state}")
        logger.info(f"    Success rate: {pstatus.success_rate:.2%}")
        logger.info(f"    Avg response time: {pstatus.average_response_time_ms:.0f}ms")
        logger.info(f"    Total API calls: {pstatus.total_api_calls}")

        if pstatus.last_success:
            logger.info(f"    Last success: {pstatus.last_success}")
        if pstatus.last_failure:
            logger.info(f"    Last failure: {pstatus.last_failure}")


def main():
    """Run all real API tests."""
    logger.info("=" * 80)
    logger.info("LLM Orchestrator - Real API Integration Test")
    logger.info("=" * 80)

    # Check API keys
    api_keys = check_api_keys()

    missing_keys = [key for key, available in api_keys.items() if not available]
    if missing_keys:
        logger.warning(f"\n⚠ Missing API keys: {', '.join(missing_keys)}")
        logger.warning("The orchestrator will skip providers without API keys.")
        logger.warning("To add API keys, update your .env file:")
        for key in missing_keys:
            logger.warning(f"  {key}=your_api_key_here")

    # Create orchestration config
    config = OrchestrationConfig(
        default_strategy="failover",
        provider_priority=["gemini", "claude", "openai"],
        unhealthy_threshold=3,
        timeout_seconds=90.0,
        fuzzy_match_threshold=0.85,
        consensus_min_agreement=2,
        abstention_confidence_threshold=0.25,
    )

    # Create orchestrator
    logger.info("\nInitializing LLMOrchestrator...")
    orchestrator = LLMOrchestrator.from_config(
        config=config,
        data_dir=Path("data/llm_health"),
    )

    available_providers = orchestrator.get_available_providers()
    logger.info(
        f"✓ Orchestrator initialized with {len(available_providers)} providers: {', '.join(available_providers)}"
    )

    if not available_providers:
        logger.error(
            "✗ No providers available. Please add at least one API key to .env"
        )
        return

    # Run tests
    test_failover_strategy(orchestrator)
    test_consensus_strategy(orchestrator)
    test_best_match_strategy(orchestrator)
    test_cost_tracking(orchestrator)
    test_provider_health(orchestrator)

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info("All tests completed! Check the logs above for details.")
    logger.info("\nNext steps:")
    logger.info("1. Review the extraction results for accuracy")
    logger.info("2. Check cost metrics in data/llm_health/cost_metrics.json")
    logger.info("3. Check health metrics in data/llm_health/health_metrics.json")
    logger.info("4. Try the CLI commands:")
    logger.info("   - python -m src.collabiq.cli llm status --detailed")
    logger.info("   - python -m src.collabiq.cli llm test gemini")
    logger.info("   - python -m src.collabiq.cli llm set-strategy consensus")


if __name__ == "__main__":
    main()
