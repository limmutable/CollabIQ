#!/usr/bin/env python3
"""CLI tool for extracting entities from emails using Gemini.

This tool provides command-line access to the GeminiAdapter for manual
entity extraction from cleaned email files.

Usage:
    # Single email extraction
    uv run python src/cli/extract_entities.py --email path/to/email.txt

    # Output to file
    uv run python src/cli/extract_entities.py --email email.txt --output result.json

    # Show confidence warnings
    uv run python src/cli/extract_entities.py --email email.txt --show-confidence
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add src directory to path to match pytest pythonpath configuration
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_adapters.gemini_adapter import GeminiAdapter
from llm_provider.types import ExtractedEntities
from llm_provider.exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from config.settings import get_settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_gemini_adapter() -> GeminiAdapter:
    """Initialize GeminiAdapter with settings from config.

    Returns:
        GeminiAdapter: Configured adapter instance

    Raises:
        LLMAuthenticationError: If API key is missing or invalid
    """
    settings = get_settings()

    # Get API key from Infisical or .env
    api_key = settings.get_secret_or_env("GEMINI_API_KEY")

    if not api_key:
        raise LLMAuthenticationError(
            "GEMINI_API_KEY not found. "
            "Please set it in Infisical or .env file. "
            "Get your API key at: https://aistudio.google.com/app/apikey"
        )

    logger.info(f"Initializing GeminiAdapter (model={settings.gemini_model})")

    return GeminiAdapter(
        api_key=api_key,
        model=settings.gemini_model,
        timeout=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )


def extract_from_file(
    adapter: GeminiAdapter,
    email_file: Path,
    show_confidence: bool = False,
    confidence_threshold: float = 0.85,
) -> ExtractedEntities:
    """Extract entities from email file.

    Args:
        adapter: GeminiAdapter instance
        email_file: Path to email file
        show_confidence: Whether to show confidence warnings
        confidence_threshold: Threshold for low-confidence warnings

    Returns:
        ExtractedEntities: Extracted entities with confidence scores

    Raises:
        FileNotFoundError: If email file doesn't exist
        LLMAPIError: If extraction fails
    """
    # Read email file
    if not email_file.exists():
        raise FileNotFoundError(f"Email file not found: {email_file}")

    logger.info(f"Reading email from: {email_file}")
    email_text = email_file.read_text(encoding="utf-8")

    # Extract entities
    logger.info("Extracting entities...")
    entities = adapter.extract_entities(email_text)

    logger.info(f"Extraction complete (email_id={entities.email_id})")

    # Show confidence warnings if requested
    if show_confidence and entities.confidence.has_low_confidence(confidence_threshold):
        logger.warning("⚠️  Some fields have low confidence scores:")

        if entities.confidence.person < confidence_threshold:
            logger.warning(
                f"  - person_in_charge: {entities.person_in_charge or 'null'} "
                f"(confidence: {entities.confidence.person:.2f})"
            )
        if entities.confidence.startup < confidence_threshold:
            logger.warning(
                f"  - startup_name: {entities.startup_name or 'null'} "
                f"(confidence: {entities.confidence.startup:.2f})"
            )
        if entities.confidence.partner < confidence_threshold:
            logger.warning(
                f"  - partner_org: {entities.partner_org or 'null'} "
                f"(confidence: {entities.confidence.partner:.2f})"
            )
        if entities.confidence.details < confidence_threshold:
            logger.warning(
                f"  - details: {entities.details or 'null'} "
                f"(confidence: {entities.confidence.details:.2f})"
            )
        if entities.confidence.date < confidence_threshold:
            logger.warning(
                f"  - date: {entities.date or 'null'} "
                f"(confidence: {entities.confidence.date:.2f})"
            )

    return entities


def save_output(entities: ExtractedEntities, output_file: Optional[Path]) -> None:
    """Save extraction output to file or stdout.

    Args:
        entities: Extracted entities to save
        output_file: Output file path (None for stdout)
    """
    # Convert to JSON
    output_json = entities.model_dump_json(indent=2)

    if output_file:
        output_file.write_text(output_json, encoding="utf-8")
        logger.info(f"Output saved to: {output_file}")
    else:
        print(output_json)


def main() -> int:
    """Main CLI entry point.

    Returns:
        int: Exit code (0=success, 1=error)
    """
    parser = argparse.ArgumentParser(
        description="Extract entities from emails using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from single email
  %(prog)s --email tests/fixtures/sample_emails/korean_001.txt

  # Save output to file
  %(prog)s --email email.txt --output result.json

  # Show confidence warnings
  %(prog)s --email email.txt --show-confidence

  # Custom confidence threshold
  %(prog)s --email email.txt --show-confidence --threshold 0.90
        """,
    )

    parser.add_argument(
        "--email",
        type=Path,
        required=True,
        help="Path to email file to extract entities from",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--show-confidence",
        action="store_true",
        help="Show warnings for low-confidence fields",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Confidence threshold for warnings (default: 0.85)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    try:
        # Initialize adapter
        adapter = setup_gemini_adapter()

        # Extract entities
        entities = extract_from_file(
            adapter,
            args.email,
            show_confidence=args.show_confidence,
            confidence_threshold=args.threshold,
        )

        # Save output
        save_output(entities, args.output)

        logger.info("✓ Extraction completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1

    except LLMAuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        logger.error("Please check your GEMINI_API_KEY configuration")
        return 1

    except LLMRateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        logger.error("Please wait 60 seconds and try again (free tier: 10 req/min)")
        return 1

    except LLMTimeoutError as e:
        logger.error(f"Timeout error: {e}")
        logger.error(
            "The request took too long. Try again or increase timeout in settings"
        )
        return 1

    except LLMValidationError as e:
        logger.error(f"Validation error: {e}")
        return 1

    except LLMAPIError as e:
        logger.error(f"API error: {e}")
        logger.error("An unexpected error occurred. Check Gemini API status")
        return 1

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
