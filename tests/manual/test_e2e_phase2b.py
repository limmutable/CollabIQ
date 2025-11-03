#!/usr/bin/env python3
"""Test Phase 2b (LLM-Based Company Matching) with real emails from collab@signite.co.

This script demonstrates end-to-end Phase 2b functionality:
1. Retrieve recent emails from Gmail (collab@signite.co)
2. Clean and normalize email content
3. Fetch company data from Notion databases
4. Extract entities and match companies using Gemini
5. Display matched results with confidence scores

Usage:
    uv run python tests/manual/test_e2e_phase2b.py [--limit N]

Options:
    --limit N    Number of emails to process (default: 5)
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from src.email_receiver.gmail_receiver import GmailReceiver
from src.content_normalizer.normalizer import ContentNormalizer
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.notion_integrator.integrator import NotionIntegrator


async def main():
    parser = argparse.ArgumentParser(description="Test Phase 2b with real emails")
    parser.add_argument("--limit", type=int, default=5, help="Number of emails to process")
    args = parser.parse_args()

    # Initialize settings
    settings = get_settings()

    print("=" * 80)
    print("Phase 2b Real-World Test: LLM-Based Company Matching")
    print("=" * 80)
    print()

    # Step 1: Initialize components
    print("Step 1: Initializing components...")

    credentials_path = settings.get_gmail_credentials_path()
    gmail_receiver = GmailReceiver(
        credentials_path=credentials_path,
        token_path=settings.gmail_token_path
    )
    gmail_receiver.connect()

    normalizer = ContentNormalizer()
    gemini_adapter = GeminiAdapter(
        api_key=settings.get_secret_or_env("GEMINI_API_KEY"),
        model=settings.gemini_model,
    )
    notion_integrator = NotionIntegrator()

    print(f"✓ GmailReceiver initialized and connected")
    print(f"✓ ContentNormalizer initialized")
    print(f"✓ GeminiAdapter initialized (model: {settings.gemini_model})")
    print(f"✓ NotionIntegrator initialized")
    print()

    # Step 2: Fetch company data from Notion
    print("Step 2: Fetching company data from Notion...")

    try:
        # Fetch from Companies database
        companies_db_id = settings.get_secret_or_env("NOTION_DATABASE_ID_COMPANIES")
        formatted_data = await notion_integrator.format_for_llm(companies_db_id)
        company_context = formatted_data.summary_markdown

        print(f"✓ Fetched companies from Notion")
        print(f"✓ Formatted as LLM-ready markdown ({len(company_context)} chars)")
        print()

        # Display company summary
        print("Company Database Summary:")
        print(f"  - Total: {formatted_data.metadata.total_companies}")
        print(f"  - Portfolio: {formatted_data.metadata.portfolio_company_count}")
        print(f"  - SSG Affiliates: {formatted_data.metadata.shinsegae_affiliate_count}")
        print()

    except Exception as e:
        print(f"✗ Error fetching Notion data: {e}")
        print("  Make sure NOTION_API_TOKEN and NOTION_COMPANIES_DB_ID are set")
        return 1

    # Step 3: Retrieve recent emails
    print(f"Step 3: Retrieving last {args.limit} emails from collab@signite.co...")

    try:
        # Query for recent emails sent to collab@signite.co (last 30 days)
        since_date = datetime.now() - timedelta(days=30)
        query = f"to:collab@signite.co after:{since_date.strftime('%Y/%m/%d')}"

        messages = gmail_receiver.fetch_emails(query=query, max_emails=args.limit)
        print(f"✓ Retrieved {len(messages)} emails")
        print()

    except Exception as e:
        print(f"✗ Error retrieving emails: {e}")
        print("  Make sure Gmail OAuth2 is set up (run scripts/authenticate_gmail.py)")
        return 1

    if not messages:
        print("No emails found. Try adjusting the date range or query.")
        return 0

    # Step 4: Process each email
    print(f"Step 4: Processing {len(messages)} emails with company matching...")
    print()

    results = []

    for i, email_data in enumerate(messages, 1):
        print(f"{'=' * 80}")
        print(f"Email {i}/{len(messages)}")
        print(f"{'=' * 80}")

        # Extract metadata from RawEmail object
        msg_id = email_data.metadata.message_id
        subject = email_data.metadata.subject
        sender = email_data.metadata.sender
        date = email_data.metadata.received_at

        print(f"Subject: {subject}")
        print(f"From: {sender}")
        print(f"Date: {date}")
        print()

        # Clean and normalize content
        body = email_data.body
        cleaning_result = normalizer.clean(body)
        cleaned_text = cleaning_result.cleaned_body

        print(f"Original length: {len(body)} chars")
        print(f"Cleaned length: {len(cleaned_text)} chars")
        print()

        # Extract entities WITHOUT company matching (Phase 1b)
        print("Phase 1b: Extracting entities (no matching)...")
        try:
            entities_no_match = gemini_adapter.extract_entities(cleaned_text)

            print(f"  담당자: {entities_no_match.person_in_charge or 'N/A'}")
            print(f"  스타트업명: {entities_no_match.startup_name or 'N/A'}")
            print(f"  협업기관: {entities_no_match.partner_org or 'N/A'}")
            print(f"  날짜: {entities_no_match.date or 'N/A'}")
            print()

        except Exception as e:
            print(f"  ✗ Extraction error: {e}")
            continue

        # Extract entities WITH company matching (Phase 2b)
        print("Phase 2b: Extracting entities WITH company matching...")
        try:
            entities_with_match = gemini_adapter.extract_entities(cleaned_text, company_context=company_context)

            print(f"  담당자: {entities_with_match.person_in_charge or 'N/A'}")
            print(f"  스타트업명: {entities_with_match.startup_name or 'N/A'}")
            print(f"    → Matched ID: {entities_with_match.matched_company_id or 'None'}")
            print(f"    → Confidence: {entities_with_match.startup_match_confidence or 'N/A'}")
            print(f"  협업기관: {entities_with_match.partner_org or 'N/A'}")
            print(f"    → Matched ID: {entities_with_match.matched_partner_id or 'None'}")
            print(f"    → Confidence: {entities_with_match.partner_match_confidence or 'N/A'}")
            print(f"  날짜: {entities_with_match.date or 'N/A'}")
            print()

            # Determine match quality
            startup_match_quality = "None"
            if entities_with_match.startup_match_confidence:
                if entities_with_match.startup_match_confidence >= 0.95:
                    startup_match_quality = "Exact"
                elif entities_with_match.startup_match_confidence >= 0.90:
                    startup_match_quality = "Normalized"
                elif entities_with_match.startup_match_confidence >= 0.75:
                    startup_match_quality = "Semantic"
                elif entities_with_match.startup_match_confidence >= 0.70:
                    startup_match_quality = "Fuzzy"
                else:
                    startup_match_quality = "Low (<0.70)"

            partner_match_quality = "None"
            if entities_with_match.partner_match_confidence:
                if entities_with_match.partner_match_confidence >= 0.95:
                    partner_match_quality = "Exact"
                elif entities_with_match.partner_match_confidence >= 0.90:
                    partner_match_quality = "Normalized"
                elif entities_with_match.partner_match_confidence >= 0.75:
                    partner_match_quality = "Semantic"
                elif entities_with_match.partner_match_confidence >= 0.70:
                    partner_match_quality = "Fuzzy"
                else:
                    partner_match_quality = "Low (<0.70)"

            print(f"Match Quality Analysis:")
            print(f"  Startup: {startup_match_quality}")
            print(f"  Partner: {partner_match_quality}")

            # Store result
            results.append({
                "email_id": msg_id,
                "subject": subject,
                "startup_name": entities_with_match.startup_name,
                "matched_company_id": entities_with_match.matched_company_id,
                "startup_confidence": entities_with_match.startup_match_confidence,
                "startup_match_quality": startup_match_quality,
                "partner_org": entities_with_match.partner_org,
                "matched_partner_id": entities_with_match.matched_partner_id,
                "partner_confidence": entities_with_match.partner_match_confidence,
                "partner_match_quality": partner_match_quality,
            })

        except Exception as e:
            print(f"  ✗ Matching error: {e}")
            continue

        print()

    # Step 5: Summary
    print(f"{'=' * 80}")
    print("Summary")
    print(f"{'=' * 80}")
    print()

    if results:
        # Calculate success rates
        total = len(results)
        startup_matches = sum(1 for r in results if r["matched_company_id"])
        partner_matches = sum(1 for r in results if r["matched_partner_id"])
        high_confidence_startup = sum(1 for r in results if r["startup_confidence"] and r["startup_confidence"] >= 0.90)
        high_confidence_partner = sum(1 for r in results if r["partner_confidence"] and r["partner_confidence"] >= 0.90)

        print(f"Total emails processed: {total}")
        print(f"Startup matches: {startup_matches}/{total} ({startup_matches/total*100:.1f}%)")
        print(f"  - High confidence (≥0.90): {high_confidence_startup}/{startup_matches if startup_matches > 0 else 1}")
        print(f"Partner matches: {partner_matches}/{total} ({partner_matches/total*100:.1f}%)")
        print(f"  - High confidence (≥0.90): {high_confidence_partner}/{partner_matches if partner_matches > 0 else 1}")
        print()

        # Match quality distribution
        print("Match Quality Distribution:")
        startup_qualities = [r["startup_match_quality"] for r in results]
        partner_qualities = [r["partner_match_quality"] for r in results]

        for quality in ["Exact", "Normalized", "Semantic", "Fuzzy", "Low (<0.70)", "None"]:
            startup_count = startup_qualities.count(quality)
            partner_count = partner_qualities.count(quality)
            if startup_count > 0 or partner_count > 0:
                print(f"  {quality}: {startup_count} startups, {partner_count} partners")

        # Save results
        output_file = Path("data/test_results") / f"phase2b_real_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print()
        print(f"✓ Results saved to: {output_file}")

    print()
    print("=" * 80)
    print("Phase 2b Real-World Test Complete!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
