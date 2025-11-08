"""Claude adapter implementation for LLM-based entity extraction.

This module provides a concrete implementation of the LLMProvider interface
using Anthropic's Claude API for entity extraction from emails.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from pydantic import ValidationError

from src.llm_provider.base import LLMProvider
from src.llm_provider.exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from src.llm_provider.types import ConfidenceScores, ExtractedEntities
from src.llm_provider.date_utils import parse_date

logger = logging.getLogger(__name__)


class ClaudeAdapter(LLMProvider):
    """Claude API adapter for entity extraction.

    This adapter implements the LLMProvider interface using Anthropic's Claude API.
    Features:
    - Structured JSON output with confidence scores
    - Few-shot prompting for improved accuracy
    - Comprehensive error handling
    - Token usage tracking for cost monitoring

    Example:
        >>> from src.llm_adapters.claude_adapter import ClaudeAdapter
        >>> adapter = ClaudeAdapter(api_key=os.getenv("ANTHROPIC_API_KEY"))
        >>> email_text = "어제 신세계와 본봄 파일럿 킥오프"
        >>> entities = adapter.extract_entities(email_text)
        >>> print(entities.startup_name)
        '본봄'
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """Initialize Claude adapter.

        Args:
            api_key: Anthropic API key
            model: Claude model name (default: "claude-sonnet-4-5-20250929")
            timeout: Request timeout in seconds (default: 60)
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            LLMAuthenticationError: If API key is invalid
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize Claude client
        self.client = anthropic.Anthropic(api_key=api_key)

        # Load prompt template (reuse Gemini prompt for now)
        prompt_path = Path(__file__).parent / "prompts" / "extraction_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

        # Token usage tracking (for cost monitoring)
        self.last_input_tokens = 0
        self.last_output_tokens = 0

        logger.info(
            f"Initialized ClaudeAdapter with model={model}, timeout={timeout}s"
        )

    def extract_entities(
        self,
        email_text: str,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> ExtractedEntities:
        """Extract 5 key entities from email text with optional company matching.

        Args:
            email_text: Cleaned email body (Korean/English/mixed)
            company_context: Optional markdown-formatted company list from
                           NotionIntegrator.format_for_llm(). If provided,
                           enables company matching.
            email_id: Optional email message ID. If not provided,
                    generates ID from email_text hash.

        Returns:
            ExtractedEntities: Pydantic model with 5 entities + confidence scores

        Raises:
            LLMAPIError: Base exception for all LLM API errors
            LLMRateLimitError: Rate limit exceeded (429)
            LLMTimeoutError: Request timeout
            LLMAuthenticationError: Authentication failed (401/403)
            LLMValidationError: Malformed API response
        """
        # Validate input
        if not email_text or not email_text.strip():
            raise LLMValidationError("email_text cannot be empty")

        if len(email_text) > 10000:
            raise LLMValidationError(
                f"email_text too long ({len(email_text)} > 10000 characters)"
            )

        # Generate email_id if not provided
        if not email_id:
            email_id = hashlib.md5(email_text.encode("utf-8")).hexdigest()

        # Build prompt with company context if provided
        if company_context:
            prompt = f"{self.prompt_template}\n\n## Company Database\n{company_context}\n\n## Email to Extract\n{email_text}"
        else:
            prompt = f"{self.prompt_template}\n\n## Email to Extract\n{email_text}"

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
            )

            # Track token usage
            self.last_input_tokens = response.usage.input_tokens
            self.last_output_tokens = response.usage.output_tokens

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON response
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse Claude response as JSON: {response_text[:200]}"
                )
                raise LLMValidationError(
                    f"Invalid JSON in Claude response: {str(e)}"
                ) from e

            # Parse date if present
            date_value = None
            if data.get("date"):
                date_value = parse_date(data["date"])

            # Build ExtractedEntities
            entities = ExtractedEntities(
                person_in_charge=data.get("person_in_charge"),
                startup_name=data.get("startup_name"),
                partner_org=data.get("partner_org"),
                details=data.get("details", ""),
                date=date_value,
                confidence=ConfidenceScores(**data.get("confidence", {})),
                email_id=email_id,
                extracted_at=datetime.utcnow(),
                # Phase 2: Company matching fields (if context provided)
                matched_startup_id=data.get("matched_startup_id"),
                matched_startup_name=data.get("matched_startup_name"),
                matched_partner_id=data.get("matched_partner_id"),
                matched_partner_name=data.get("matched_partner_name"),
                match_confidence=data.get("match_confidence"),
            )

            logger.info(
                f"Successfully extracted entities from email_id={email_id} "
                f"(tokens: {self.last_input_tokens}+{self.last_output_tokens})"
            )

            return entities

        except anthropic.AuthenticationError as e:
            logger.error(f"Claude authentication error: {e}")
            raise LLMAuthenticationError(
                "Invalid Anthropic API key", original_error=e
            ) from e

        except anthropic.RateLimitError as e:
            logger.warning(f"Claude rate limit exceeded: {e}")
            raise LLMRateLimitError(
                "Claude API rate limit exceeded", original_error=e
            ) from e

        except anthropic.APITimeoutError as e:
            logger.error(f"Claude request timeout: {e}")
            raise LLMTimeoutError(
                f"Claude API timeout after {self.timeout}s",
                timeout_seconds=self.timeout,
                original_error=e,
            ) from e

        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}")
            raise LLMValidationError(
                f"Response validation failed: {str(e)}", original_error=e
            ) from e

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise LLMAPIError(
                f"Claude API error: {str(e)}", status_code=500, original_error=e
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error in ClaudeAdapter: {e}")
            raise LLMAPIError(
                f"Unexpected error: {str(e)}", status_code=500, original_error=e
            ) from e
