"""Demonstration of Quality Metrics Tracking and Routing.

This script demonstrates:
1. Processing emails with quality metrics tracking
2. Comparing provider performance
3. Enabling quality-based routing
"""

import logging
from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample Korean email for testing
SAMPLE_EMAIL_1 = """
어제 신세계와 본봄 킥오프 했는데
결과 공유 받아서 전달 드릴게요!

프랙시스 강승현 대표와 만나기로 했는데,
그 때 이야기해도 되겠죠?

감사합니다.
임정민 드림
"""

SAMPLE_EMAIL_2 = """
안녕하세요,

지난주 투자 심사 회의 결과 긍정적으로 검토 중입니다.
다음 주에 추가 미팅 일정 잡겠습니다.

스타트업: 웨이브온
파트너: KDB산업은행
담당자: 김민수

감사합니다.
"""

def main():
    print("\n" + "="*80)
    print("PHASE 1: Initial Processing (Priority-Based Routing)")
    print("="*80 + "\n")

    # Create orchestrator with quality routing DISABLED
    config = OrchestrationConfig(
        default_strategy="failover",
        provider_priority=["gemini", "claude", "openai"],
        enable_quality_routing=False,  # Disabled for first phase
    )

    orchestrator = LLMOrchestrator.from_config(config)

    print("Processing 3 emails with priority-based routing (gemini → claude → openai)...\n")

    # Process first email (will use Gemini - first in priority)
    print("Email 1: Processing...")
    entities_1 = orchestrator.extract_entities(
        email_text=SAMPLE_EMAIL_1,
        email_id="demo_email_001"
    )
    print(f"✓ Email 1 extracted by: {entities_1.provider_name}")
    print(f"  Person: {entities_1.person_in_charge}, Startup: {entities_1.startup_name}")
    print(f"  Confidence: {entities_1.confidence.person:.2f}\n")

    # Process second email
    print("Email 2: Processing...")
    entities_2 = orchestrator.extract_entities(
        email_text=SAMPLE_EMAIL_2,
        email_id="demo_email_002"
    )
    print(f"✓ Email 2 extracted by: {entities_2.provider_name}")
    print(f"  Person: {entities_2.person_in_charge}, Startup: {entities_2.startup_name}")
    print(f"  Confidence: {entities_2.confidence.person:.2f}\n")

    # Process third email
    print("Email 3: Processing...")
    entities_3 = orchestrator.extract_entities(
        email_text=SAMPLE_EMAIL_1,  # Reuse email
        email_id="demo_email_003"
    )
    print(f"✓ Email 3 extracted by: {entities_3.provider_name}")
    print(f"  Person: {entities_3.person_in_charge}, Startup: {entities_3.startup_name}")
    print(f"  Confidence: {entities_3.confidence.person:.2f}\n")

    print("\n" + "="*80)
    print("PHASE 2: Quality Metrics Summary")
    print("="*80 + "\n")

    # Get quality metrics
    quality_metrics = orchestrator.quality_tracker.get_all_metrics()

    print("Quality Metrics per Provider:\n")
    for provider_name, metrics in quality_metrics.items():
        if metrics.total_extractions > 0:
            print(f"{provider_name.upper()}:")
            print(f"  Extractions: {metrics.total_extractions}")
            print(f"  Avg Confidence: {metrics.average_overall_confidence:.2%}")
            print(f"  Field Completeness: {metrics.average_field_completeness:.1f}%")
            print(f"  Validation Success: {metrics.validation_success_rate:.1f}%")
            print()

    print("\n" + "="*80)
    print("PHASE 3: Provider Comparison")
    print("="*80 + "\n")

    # Compare providers
    try:
        comparison = orchestrator.quality_tracker.compare_providers(
            cost_tracker=orchestrator.cost_tracker
        )

        print("Quality Rankings:")
        for ranking in comparison.provider_rankings:
            print(f"  {ranking['rank']}. {ranking['provider_name'].upper()}: "
                  f"Quality Score = {ranking['quality_score']:.3f}")

        print("\nValue Rankings (Quality per Dollar):")
        for ranking in comparison.quality_to_cost_rankings:
            is_recommended = ranking['provider_name'] == comparison.recommended_provider
            marker = " ✓ RECOMMENDED" if is_recommended else ""
            print(f"  {ranking['rank']}. {ranking['provider_name'].upper()}: "
                  f"Value Score = {ranking['value_score']:.3f}{marker}")

        print(f"\nRecommendation: {comparison.recommended_provider.upper()}")
        print(f"Reason: {comparison.recommendation_reason}")

    except ValueError as e:
        print(f"Cannot compare yet: {e}")

    print("\n" + "="*80)
    print("PHASE 4: Quality-Based Routing (Re-process with highest quality provider)")
    print("="*80 + "\n")

    # Create new orchestrator with quality routing ENABLED
    config_with_quality = OrchestrationConfig(
        default_strategy="failover",
        provider_priority=["gemini", "claude", "openai"],
        enable_quality_routing=True,  # Enable quality routing
    )

    orchestrator_quality = LLMOrchestrator.from_config(config_with_quality)

    # Copy existing metrics to new orchestrator
    orchestrator_quality.quality_tracker.metrics = orchestrator.quality_tracker.metrics.copy()
    orchestrator_quality.cost_tracker.metrics = orchestrator.cost_tracker.metrics.copy()

    print("Quality routing is now ENABLED")
    print("System will select provider based on quality metrics...\n")

    # Process new email with quality routing
    print("Email 4: Processing with quality-based routing...")
    entities_4 = orchestrator_quality.extract_entities(
        email_text=SAMPLE_EMAIL_2,
        email_id="demo_email_004"
    )
    print(f"✓ Email 4 extracted by: {entities_4.provider_name} (selected by quality score)")
    print(f"  Person: {entities_4.person_in_charge}, Startup: {entities_4.startup_name}")
    print(f"  Confidence: {entities_4.confidence.person:.2f}\n")

    # Show which provider was selected by quality
    available_providers = orchestrator_quality.get_available_providers()
    selected_by_quality = orchestrator_quality.quality_tracker.select_provider_by_quality(
        available_providers
    )
    print(f"Quality-based selection: {selected_by_quality.upper() if selected_by_quality else 'None'}")
    print(f"Priority-based would have selected: {config_with_quality.provider_priority[0].upper()}\n")

    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("✓ Quality metrics tracking (confidence, completeness, validation)")
    print("✓ Provider comparison (quality score + value score)")
    print("✓ Quality-based routing (automatic selection of best provider)")
    print("✓ Cost tracking integration")
    print("\nNext steps:")
    print("- Run: collabiq llm status --detailed")
    print("- Run: collabiq llm compare")
    print("- Run: collabiq llm compare --detailed")
    print("- Run: collabiq llm set-quality-routing --enable")

if __name__ == "__main__":
    main()
