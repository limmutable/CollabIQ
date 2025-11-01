#!/usr/bin/env python3
"""End-to-end test: Fetch emails from collab@signite.co and extract entities.

This script demonstrates the full MVP pipeline:
1. Fetch real emails from collab@signite.co using Gmail API
2. Clean email content (remove signatures, quotes)
3. Extract entities using Gemini API
4. Display results

Usage:
    uv run python scripts/test_e2e_extraction.py --max-emails 2
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_receiver.gmail_receiver import GmailReceiver
from src.content_normalizer.normalizer import ContentNormalizer
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.config.settings import get_settings


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end test: Fetch emails and extract entities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-emails",
        type=int,
        default=2,
        help="Maximum number of emails to process (default: 2)"
    )
    parser.add_argument(
        "--query",
        default="to:collab@signite.co",
        help="Gmail search query (default: to:collab@signite.co)"
    )
    parser.add_argument(
        "--save-emails",
        action="store_true",
        help="Save cleaned emails to data/cleaned/"
    )
    parser.add_argument(
        "--save-extractions",
        action="store_true",
        help="Save extracted entities to data/extractions/"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("CollabIQ End-to-End Extraction Test")
    print("=" * 80)
    print()

    # Initialize components
    settings = get_settings()

    print("Step 1: Initializing Gmail receiver...")
    credentials_path = settings.get_gmail_credentials_path()
    gmail_receiver = GmailReceiver(
        credentials_path=credentials_path,
        token_path=settings.gmail_token_path
    )
    gmail_receiver.connect()
    print("✓ Connected to Gmail API")
    print()

    print("Step 2: Initializing content normalizer...")
    normalizer = ContentNormalizer()
    print("✓ Content normalizer ready")
    print()

    print("Step 3: Initializing Gemini adapter...")
    gemini_api_key = settings.get_secret_or_env("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found in environment or Infisical")
        print("   Please set it in your .env file or Infisical")
        print("   Get your API key at: https://aistudio.google.com/app/apikey")
        return 1

    gemini_adapter = GeminiAdapter(
        api_key=gemini_api_key,
        model=settings.gemini_model,
        timeout=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )
    print(f"✓ Gemini adapter ready (model: {settings.gemini_model})")
    print()

    # Fetch emails
    print(f"Step 4: Fetching {args.max_emails} email(s) from collab@signite.co...")
    print(f"Query: {args.query}")
    emails = gmail_receiver.fetch_emails(
        query=args.query,
        max_emails=args.max_emails
    )
    print(f"✓ Retrieved {len(emails)} email(s)")
    print()

    if len(emails) == 0:
        print("No emails found. Try sending a test email to collab@signite.co")
        return 0

    # Process each email
    print("=" * 80)
    print(f"Processing {len(emails)} email(s)...")
    print("=" * 80)
    print()

    for i, raw_email in enumerate(emails, 1):
        print(f"{'─' * 80}")
        print(f"Email {i}/{len(emails)}")
        print(f"{'─' * 80}")
        print(f"From:    {raw_email.metadata.sender}")
        print(f"Subject: {raw_email.metadata.subject}")
        print(f"Date:    {raw_email.metadata.received_at}")
        print()

        # Step 5: Clean email content
        print("  Step 5: Cleaning email content...")
        cleaning_result = normalizer.clean(raw_email.body)
        cleaned_body = cleaning_result.cleaned_body

        if args.save_emails:
            # Save cleaned email
            cleaned_dir = Path("data/cleaned") / datetime.now().strftime("%Y/%m")
            cleaned_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cleaned_file = cleaned_dir / f"{timestamp}_{raw_email.metadata.message_id.strip('<>')}.txt"
            cleaned_file.write_text(cleaned_body, encoding="utf-8")
            print(f"  ✓ Saved cleaned email to: {cleaned_file}")

        print(f"  ✓ Cleaned (original: {len(raw_email.body)} chars → cleaned: {len(cleaned_body)} chars)")
        print()

        # Step 6: Extract entities with Gemini
        print("  Step 6: Extracting entities with Gemini API...")
        try:
            extracted = gemini_adapter.extract_entities(cleaned_body)
            print("  ✓ Extraction complete")
            print()

            # Display results
            print("  " + "─" * 76)
            print("  Extracted Entities:")
            print("  " + "─" * 76)
            print(f"  담당자 (Person):      {extracted.person_in_charge or 'N/A'} (confidence: {extracted.confidence.person:.2f})")
            print(f"  스타트업 (Startup):   {extracted.startup_name or 'N/A'} (confidence: {extracted.confidence.startup:.2f})")
            print(f"  협업기관 (Partner):   {extracted.partner_org or 'N/A'} (confidence: {extracted.confidence.partner:.2f})")
            print(f"  날짜 (Date):          {extracted.date or 'N/A'} (confidence: {extracted.confidence.date:.2f})")
            print()
            print(f"  세부내용 (Details):   {extracted.details or 'N/A'}")
            print(f"  (confidence: {extracted.confidence.details:.2f})")
            print("  " + "─" * 76)
            print()

            # Save extraction if requested
            if args.save_extractions:
                extraction_dir = Path("data/extractions") / datetime.now().strftime("%Y/%m")
                extraction_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extraction_file = extraction_dir / f"{timestamp}_{raw_email.metadata.message_id.strip('<>')}.json"
                extraction_file.write_text(extracted.model_dump_json(indent=2), encoding="utf-8")
                print(f"  ✓ Saved extraction to: {extraction_file}")
                print()

        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
            print()
            continue

    print("=" * 80)
    print("✅ End-to-end test complete!")
    print("=" * 80)
    print()
    print(f"Summary:")
    print(f"  - Fetched: {len(emails)} email(s)")
    print(f"  - Cleaned: {len(emails)} email(s)")
    print(f"  - Extracted: {len(emails)} entity set(s)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
