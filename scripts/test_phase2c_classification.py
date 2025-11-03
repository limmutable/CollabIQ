#!/usr/bin/env python3
"""Example script demonstrating Phase 2c Classification & Summarization workflow.

This script demonstrates:
1. Dynamic schema fetching from Notion
2. Type classification (deterministic based on company matching)
3. Intensity classification (LLM-based Korean semantic analysis)
4. Summary generation (preserving 5 key entities)
5. Confidence scoring and manual review routing

Usage:
    uv run python scripts/test_phase2c_classification.py

Requirements:
    - GEMINI_API_KEY in environment
    - NOTION_TOKEN in environment
    - COLLABIQ_DB_ID in environment
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def main():
    """Run Phase 2c classification workflow demonstration."""
    print("=" * 80)
    print("Phase 2c: Classification & Summarization - Demo Script")
    print("=" * 80)
    print()

    # Step 1: Load dependencies
    print("Step 1: Loading dependencies...")
    from src.models.classification_service import ClassificationService
    from src.notion_integrator.client import NotionIntegrator
    from src.llm_provider.gemini_adapter import GeminiAdapter
    import os

    # Verify environment variables
    required_env_vars = ["GEMINI_API_KEY", "NOTION_TOKEN", "COLLABIQ_DB_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these in your .env file or environment:")
        print("  - GEMINI_API_KEY: Your Gemini API key")
        print("  - NOTION_TOKEN: Your Notion integration token")
        print("  - COLLABIQ_DB_ID: Notion database ID for CollabIQ")
        return 1

    notion_token = os.getenv("NOTION_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    collabiq_db_id = os.getenv("COLLABIQ_DB_ID")

    print("✓ Environment variables loaded")
    print()

    # Step 2: Initialize services
    print("Step 2: Initializing services...")
    try:
        notion_integrator = NotionIntegrator(notion_token)
        gemini_adapter = GeminiAdapter(api_key=gemini_api_key)
        classification_service = ClassificationService(
            notion_integrator=notion_integrator,
            gemini_adapter=gemini_adapter,
            collabiq_db_id=collabiq_db_id,
        )
        print("✓ NotionIntegrator initialized")
        print("✓ GeminiAdapter initialized")
        print("✓ ClassificationService initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return 1

    # Step 3: Load sample email
    print("Step 3: Loading sample email...")
    sample_email_path = project_root / "tests" / "fixtures" / "sample_emails" / "sample-001.txt"
    if not sample_email_path.exists():
        print(f"❌ Sample email not found: {sample_email_path}")
        return 1

    with open(sample_email_path, "r", encoding="utf-8") as f:
        email_content = f.read()

    print(f"✓ Loaded sample email: {sample_email_path.name}")
    print(f"  Email length: {len(email_content)} characters")
    print()

    # Step 4: Fetch collaboration types from Notion
    print("Step 4: Fetching collaboration types from Notion...")
    try:
        collaboration_types = await classification_service.get_collaboration_types()
        print(f"✓ Fetched {len(collaboration_types)} collaboration types:")
        for code, value in collaboration_types.items():
            print(f"  - {code}: {value}")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch collaboration types: {e}")
        return 1

    # Step 5: Run classification workflow
    print("Step 5: Running classification workflow...")
    print("-" * 80)
    try:
        result = await classification_service.extract_with_classification(
            email_content=email_content,
            email_id="sample-001-demo",
            matched_company_id="abc123def456ghi789jkl012mno345pq",  # Notion ID (32 chars)
            matched_partner_id="xyz789uvw012abc345def678ghi901jk",  # Notion ID (32 chars)
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
        )
        print("✓ Classification workflow completed")
        print()
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 6: Display results
    print("=" * 80)
    print("CLASSIFICATION RESULTS")
    print("=" * 80)
    print()

    print("📧 Email Information:")
    print(f"  Email ID: {result.email_id}")
    print(f"  Extracted at: {result.extracted_at}")
    print()

    print("👤 Extracted Entities (Phase 1b):")
    print(f"  Person in charge: {result.person_in_charge}")
    print(f"  Startup name: {result.startup_name}")
    print(f"  Partner org: {result.partner_org}")
    print(f"  Details: {result.details}")
    print(f"  Date: {result.date}")
    print(f"  Entity confidence: person={result.confidence.person:.2f}, "
          f"startup={result.confidence.startup:.2f}, partner={result.confidence.partner:.2f}")
    print()

    print("🏢 Company Matching (Phase 2b):")
    print(f"  Matched company ID: {result.matched_company_id[:16]}..." if result.matched_company_id else "  Matched company ID: None")
    print(f"  Matched partner ID: {result.matched_partner_id[:16]}..." if result.matched_partner_id else "  Matched partner ID: None")
    print()

    print("🏷️  Type Classification (Phase 2c - Deterministic):")
    print(f"  Collaboration type: {result.collaboration_type}")
    print(f"  Type confidence: {result.type_confidence:.2f}")
    print(f"  Classification timestamp: {result.classification_timestamp}")
    print()

    print("📊 Intensity Classification (Phase 2c - LLM):")
    print(f"  Collaboration intensity: {result.collaboration_intensity}")
    print(f"  Intensity confidence: {result.intensity_confidence:.2f}")
    print(f"  Reasoning: {result.intensity_reasoning}")
    print()

    print("📝 Summary Generation (Phase 2c - LLM):")
    if result.collaboration_summary:
        print(f"  Summary: {result.collaboration_summary}")
        print(f"  Word count: {result.summary_word_count}")
        if result.key_entities_preserved:
            preserved_count = sum(result.key_entities_preserved.values())
            print(f"  Entities preserved: {preserved_count}/5")
            for entity, preserved in result.key_entities_preserved.items():
                status = "✓" if preserved else "✗"
                print(f"    {status} {entity}")
    else:
        print("  Summary: Not generated")
    print()

    print("🎯 Confidence Scoring (Phase 2c):")
    needs_review = result.needs_manual_review()
    review_status = "❌ Manual review required" if needs_review else "✅ Auto-accept (high confidence)"
    print(f"  Manual review needed: {review_status}")
    print(f"  Overall confidence: type={result.type_confidence:.2f}, intensity={result.intensity_confidence:.2f}")
    print()

    # Step 7: Demonstrate JSON serialization
    print("=" * 80)
    print("JSON SERIALIZATION (for Notion API)")
    print("=" * 80)
    print()

    import json
    result_dict = result.model_dump(mode='json')
    print(json.dumps(result_dict, indent=2, ensure_ascii=False)[:1000] + "...")
    print()

    # Step 8: Summary
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("✓ Phase 2c classification workflow completed successfully!")
    print()
    print("Key Features Demonstrated:")
    print("  1. Dynamic schema fetching from Notion (cached for session)")
    print("  2. Deterministic type classification (Portfolio + SSG → [A]PortCoXSSG)")
    print("  3. LLM-based intensity classification (Korean semantic analysis)")
    print("  4. Summary generation (3-5 sentences, preserves 5 key entities)")
    print("  5. Confidence scoring (0.85 threshold for manual review)")
    print()
    print("Next Steps:")
    print("  - Review the classification results above")
    print("  - Adjust thresholds if needed (0.85 default for manual review)")
    print("  - Test with your own email samples")
    print("  - Integrate into your email processing pipeline")
    print()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
