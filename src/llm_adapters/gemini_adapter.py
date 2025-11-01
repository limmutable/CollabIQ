"""Gemini adapter implementation for LLM-based entity extraction.

This module provides a concrete implementation of the LLMProvider interface
using Google's Gemini 2.0 Flash API for entity extraction from emails.
"""

import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from google import generativeai as genai
from google.api_core import exceptions as google_exceptions

from src.llm_provider.base import LLMProvider
from src.llm_provider.types import ConfidenceScores, ExtractedEntities
from src.llm_provider.exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from src.llm_provider.date_utils import parse_date


logger = logging.getLogger(__name__)


class GeminiAdapter(LLMProvider):
    """Gemini API adapter for entity extraction.

    This adapter implements the LLMProvider interface using Google's Gemini 2.0 Flash API.
    Features:
    - Structured JSON output with confidence scores
    - Few-shot prompting for improved accuracy
    - Exponential backoff retry for transient errors
    - Comprehensive error handling

    Example:
        >>> from src.llm_adapters.gemini_adapter import GeminiAdapter
        >>> from src.config.settings import get_settings
        >>>
        >>> settings = get_settings()
        >>> adapter = GeminiAdapter(
        ...     api_key=settings.get_secret_or_env("GEMINI_API_KEY"),
        ...     model=settings.gemini_model,
        ... )
        >>> email_text = "어제 신세계와 본봄 파일럿 킥오프"
        >>> entities = adapter.extract_entities(email_text)
        >>> print(entities.startup_name)
        '본봄'
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """Initialize Gemini adapter.

        Args:
            api_key: Gemini API key from Google AI Studio
            model: Gemini model name (default: "gemini-2.0-flash-exp")
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            LLMAuthenticationError: If API key is invalid
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # Configure Gemini client
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "extraction_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

        logger.info(f"Initialized GeminiAdapter with model={model}, timeout={timeout}s")

    def extract_entities(self, email_text: str) -> ExtractedEntities:
        """Extract 5 key entities from email text with confidence scores.

        Args:
            email_text: Cleaned email body (Korean/English/mixed)

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
                f"email_text too long ({len(email_text)} chars). Maximum length is 10,000 characters."
            )

        # Call Gemini API with retry
        response_data = self._call_with_retry(email_text)

        # Parse response to ExtractedEntities
        entities = self._parse_response(response_data, email_text)

        return entities

    def _build_prompt(self, email_text: str) -> str:
        """Build prompt with system instructions + few-shot examples + email.

        Args:
            email_text: Email text to extract entities from

        Returns:
            str: Complete prompt with examples and email text
        """
        return f"{self.prompt_template}\n\n{email_text}"

    def _call_gemini_api(self, email_text: str) -> Dict[str, Any]:
        """Call Gemini API with structured output.

        Args:
            email_text: Email text to extract entities from

        Returns:
            dict: Parsed JSON response from Gemini

        Raises:
            Exception: Any API error (will be handled by _handle_api_error)
        """
        prompt = self._build_prompt(email_text)

        # Define response schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                "person_in_charge": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "nullable": True},
                        "confidence": {"type": "number"},
                    },
                    "required": ["value", "confidence"],
                },
                "startup_name": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "nullable": True},
                        "confidence": {"type": "number"},
                    },
                    "required": ["value", "confidence"],
                },
                "partner_org": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "nullable": True},
                        "confidence": {"type": "number"},
                    },
                    "required": ["value", "confidence"],
                },
                "details": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "nullable": True},
                        "confidence": {"type": "number"},
                    },
                    "required": ["value", "confidence"],
                },
                "date": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "nullable": True},
                        "confidence": {"type": "number"},
                    },
                    "required": ["value", "confidence"],
                },
            },
            "required": [
                "person_in_charge",
                "startup_name",
                "partner_org",
                "details",
                "date",
            ],
        }

        # Call Gemini API
        response = self.client.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1,  # Low temperature for consistent extraction
            ),
        )

        # Parse JSON response
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Failed to parse JSON response: {e}") from e

    def _parse_response(self, response_data: Dict[str, Any], email_text: str) -> ExtractedEntities:
        """Parse Gemini API response to ExtractedEntities.

        Args:
            response_data: Parsed JSON response from Gemini
            email_text: Original email text (used for generating email_id)

        Returns:
            ExtractedEntities: Pydantic model with extracted entities

        Raises:
            LLMValidationError: If response format is invalid
        """
        try:
            # Extract values and confidence scores
            person_data = response_data.get("person_in_charge", {})
            startup_data = response_data.get("startup_name", {})
            partner_data = response_data.get("partner_org", {})
            details_data = response_data.get("details", {})
            date_data = response_data.get("date", {})

            # Parse date string to datetime
            date_str = date_data.get("value")
            parsed_date = parse_date(date_str) if date_str else None

            # Generate email_id from email text hash
            email_id = f"email_{hash(email_text) % 1000000:06d}"

            # Build ExtractedEntities
            entities = ExtractedEntities(
                person_in_charge=person_data.get("value"),
                startup_name=startup_data.get("value"),
                partner_org=partner_data.get("value"),
                details=details_data.get("value"),
                date=parsed_date,
                confidence=ConfidenceScores(
                    person=person_data.get("confidence", 0.0),
                    startup=startup_data.get("confidence", 0.0),
                    partner=partner_data.get("confidence", 0.0),
                    details=details_data.get("confidence", 0.0),
                    date=date_data.get("confidence", 0.0),
                ),
                email_id=email_id,
            )

            return entities

        except (KeyError, TypeError, ValueError) as e:
            raise LLMValidationError(f"Invalid response format: {e}") from e

    def _call_with_retry(self, email_text: str) -> Dict[str, Any]:
        """Call Gemini API with exponential backoff retry.

        Args:
            email_text: Email text to extract entities from

        Returns:
            dict: Parsed JSON response from Gemini

        Raises:
            LLMAPIError: After max retries exhausted
        """
        for attempt in range(self.max_retries):
            try:
                return self._call_gemini_api(email_text)

            except Exception as e:
                # Check if this is the last attempt
                is_last_attempt = attempt == self.max_retries - 1

                # Handle specific error types
                if self._is_rate_limit_error(e):
                    if is_last_attempt:
                        raise LLMRateLimitError(
                            f"Rate limit exceeded after {self.max_retries} retries"
                        ) from e
                    # Exponential backoff with jitter
                    delay = min(60, (2**attempt) + random.uniform(0, 1))
                    logger.warning(
                        f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt+1}/{self.max_retries})"
                    )
                    time.sleep(delay)

                elif self._is_timeout_error(e):
                    if is_last_attempt:
                        raise LLMTimeoutError(
                            f"Request timeout after {self.max_retries} retries",
                            timeout_seconds=self.timeout,
                        ) from e
                    delay = min(60, 2**attempt)
                    logger.warning(f"Timeout error, retrying in {delay}s")
                    time.sleep(delay)

                elif self._is_auth_error(e):
                    # No retry for auth errors
                    raise LLMAuthenticationError("Authentication failed") from e

                else:
                    # Generic API error
                    if is_last_attempt:
                        raise LLMAPIError(f"API error after {self.max_retries} retries: {e}") from e
                    delay = min(60, 2**attempt)
                    logger.warning(f"API error, retrying in {delay}s: {e}")
                    time.sleep(delay)

        # Should never reach here, but just in case
        raise LLMAPIError(f"Failed after {self.max_retries} retries")

    def _handle_api_error(self, error: Exception) -> None:
        """Handle API error and raise appropriate LLM exception.

        Args:
            error: Original exception from Gemini API

        Raises:
            LLMRateLimitError: For rate limit errors (429)
            LLMTimeoutError: For timeout errors
            LLMAuthenticationError: For auth errors (401/403)
            LLMAPIError: For other API errors
        """
        if self._is_rate_limit_error(error):
            raise LLMRateLimitError("Rate limit exceeded") from error
        elif self._is_timeout_error(error):
            raise LLMTimeoutError("Request timeout", timeout_seconds=self.timeout) from error
        elif self._is_auth_error(error):
            raise LLMAuthenticationError("Authentication failed") from error
        else:
            raise LLMAPIError(f"API error: {error}") from error

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error (429)."""
        return isinstance(error, google_exceptions.ResourceExhausted) or (
            hasattr(error, "status_code") and error.status_code == 429
        )

    def _is_timeout_error(self, error: Exception) -> bool:
        """Check if error is a timeout error."""
        return isinstance(error, (TimeoutError, google_exceptions.DeadlineExceeded))

    def _is_auth_error(self, error: Exception) -> bool:
        """Check if error is an authentication error (401/403)."""
        return isinstance(
            error, (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied)
        ) or (hasattr(error, "status_code") and error.status_code in (401, 403))
