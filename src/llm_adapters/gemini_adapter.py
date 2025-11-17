"""Gemini adapter implementation for LLM-based entity extraction.

This module provides a concrete implementation of the LLMProvider interface
using Google's Gemini 2.0 Flash API for entity extraction from emails.
"""

import json
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from google import generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import ValidationError

from llm_provider.base import LLMProvider
from llm_provider.types import ConfidenceScores, ExtractedEntities
from llm_provider.exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from collabiq.date_parser.parser import parse_date

try:
    from error_handling.structured_logger import logger as error_logger
    from error_handling.models import ErrorRecord, ErrorSeverity, ErrorCategory
    from error_handling import (
        retry_with_backoff,
        GEMINI_RETRY_CONFIG,
        gemini_circuit_breaker,
    )
except ImportError:
    # Graceful fallback if error_handling module not available
    error_logger = None
    ErrorRecord = None
    ErrorSeverity = None
    ErrorCategory = None
    retry_with_backoff = None
    GEMINI_RETRY_CONFIG = None
    gemini_circuit_breaker = None


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
        >>> from llm_adapters.gemini_adapter import GeminiAdapter
        >>> from config.settings import get_settings
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
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """Initialize Gemini adapter.

        Args:
            api_key: Gemini API key from Google AI Studio
            model: Gemini model name (default: "gemini-2.0-flash-exp")
            timeout: Request timeout in seconds (default: 60)
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

    @(
        retry_with_backoff(GEMINI_RETRY_CONFIG)
        if retry_with_backoff and GEMINI_RETRY_CONFIG
        else lambda f: f
    )
    def extract_entities(
        self,
        email_text: str,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> ExtractedEntities:
        """Extract 5 key entities from email text with optional company matching (with automatic retry).

        Args:
            email_text: Cleaned email body (Korean/English/mixed)
            company_context: Optional markdown-formatted company list from
                           NotionIntegrator.format_for_llm(). If provided,
                           enables company matching and populates matched_*
                           fields in return value. If None, behaves as Phase 1b
                           (extraction only, matched fields = None).
            email_id: Optional email message ID (Gmail message ID). If not provided,
                    generates ID from email_text hash (for backward compatibility).

        Returns:
            ExtractedEntities: Pydantic model with 5 entities + confidence scores
                             + matched fields (if company_context provided)

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
        response_data = self._call_with_retry(email_text, company_context)

        # Parse response to ExtractedEntities
        entities = self._parse_response(
            response_data, email_text, company_context, email_id
        )

        return entities

    def _build_prompt(
        self, email_text: str, company_context: Optional[str] = None
    ) -> str:
        """Build prompt with system instructions + few-shot examples + company context + email.

        Args:
            email_text: Email text to extract entities from
            company_context: Optional markdown-formatted company list for matching

        Returns:
            str: Complete prompt with examples, company context (if provided), and email text
        """
        # Start with base prompt template
        prompt = self.prompt_template

        # Add company context section if provided (Phase 2b)
        if company_context:
            prompt += "\n\n# Company Database for Matching\n\n"
            prompt += company_context
            prompt += "\n\n"
            prompt += "# Company Matching Instructions\n\n"
            prompt += "For startup_name and partner_org extracted above:\n"
            prompt += "- Match each to entries in the company database above\n"
            prompt += (
                "- Return matched_company_id and matched_partner_id (Notion page IDs)\n"
            )
            prompt += "- Return startup_match_confidence and partner_match_confidence (0.0-1.0)\n\n"
            prompt += "Confidence Scoring Rules (calibrate carefully):\n\n"

            prompt += "**Exact Match (0.95-1.00)**:\n"
            prompt += "- Character-for-character identical match\n"
            prompt += "- Example: '브레이크앤컴퍼니' in email exactly matches '브레이크앤컴퍼니' in database\n\n"

            prompt += "**Normalized Match (0.90-0.94)**:\n"
            prompt += "- Exact match after normalization (spacing, punctuation, capitalization)\n"
            prompt += "- Example: 'Break&Company' matches 'Break & Company'\n"
            prompt += "- Example: '신세계 인터내셔널' matches '신세계인터내셔널'\n\n"

            prompt += "**Semantic Match (0.75-0.89)**:\n"
            prompt += "- Clear abbreviation or well-known alternate name\n"
            prompt += (
                "- Example: 'SSG푸드' matches '신세계푸드' (common abbreviation)\n"
            )
            prompt += (
                "- Example: 'Shinsegae' matches '신세계' (English/Korean equivalent)\n"
            )
            prompt += "- Example: '신세계' matches '신세계인터내셔널' (parent/subsidiary relationship)\n\n"

            prompt += "**Fuzzy Match (0.70-0.74)**:\n"
            prompt += "- Minor typo (1-2 character difference) or partial name\n"
            prompt += "- Example: '브레이크언컴퍼니' matches '브레이크앤컴퍼니' (typo: 언→앤)\n"
            prompt += (
                "- Example: '스마트푸드' matches '스마트푸드네트워크' (partial name)\n"
            )
            prompt += "- Requires contextual inference to resolve ambiguity\n\n"

            prompt += "**No Match (<0.70)**:\n"
            prompt += "- Company not found in database\n"
            prompt += "- Too ambiguous or multiple possible matches\n"
            prompt += "- Significant spelling difference (>2 characters)\n"
            prompt += "- IMPORTANT: Return null for matched_company_id/matched_partner_id if confidence <0.70\n\n"

            prompt += "**Special Cases**:\n"
            prompt += "- If you correct a typo in the extracted name, use Fuzzy Match confidence (0.70-0.74)\n"
            prompt += "- If multiple companies partially match, choose the most contextually appropriate\n"
            prompt += "- When in doubt, prefer lower confidence scores to indicate uncertainty\n"

        # Add email text
        prompt += f"\n\n# Now extract from the following email:\n\n{email_text}"

        return prompt

    def _call_gemini_api(
        self, email_text: str, company_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call Gemini API with structured output.

        Args:
            email_text: Email text to extract entities from
            company_context: Optional company list for matching

        Returns:
            dict: Parsed JSON response from Gemini

        Raises:
            Exception: Any API error (will be handled by _handle_api_error)
        """
        prompt = self._build_prompt(email_text, company_context)

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

        # Add matching fields to schema if company_context provided (Phase 2b)
        if company_context:
            response_schema["properties"]["matched_company_id"] = {
                "type": "string",
                "nullable": True,
            }
            response_schema["properties"]["matched_partner_id"] = {
                "type": "string",
                "nullable": True,
            }
            response_schema["properties"]["startup_match_confidence"] = {
                "type": "number",
                "nullable": True,
            }
            response_schema["properties"]["partner_match_confidence"] = {
                "type": "number",
                "nullable": True,
            }

        # Call Gemini API with timeout using ThreadPoolExecutor
        def _call_api():
            return self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,  # Low temperature for consistent extraction
                ),
            )

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call_api)
                response = future.result(timeout=self.timeout)
        except FuturesTimeoutError:
            raise LLMTimeoutError(
                f"Gemini API call timed out after {self.timeout} seconds",
                timeout_seconds=self.timeout,
            )

        # Parse JSON response
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Failed to parse JSON response: {e}") from e

    def _parse_response(
        self,
        response_data: Dict[str, Any],
        email_text: str,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> ExtractedEntities:
        """Parse Gemini API response to ExtractedEntities.

        Args:
            response_data: Parsed JSON response from Gemini
            email_text: Original email text (used for generating email_id if not provided)
            company_context: Optional company context (affects matching fields)
            email_id: Optional email message ID. If not provided, generates from email_text hash.

        Returns:
            ExtractedEntities: Pydantic model with extracted entities

        Raises:
            LLMValidationError: If response format is invalid
        """
        try:
            return self._build_extracted_entities(
                response_data, email_text, company_context, email_id
            )
        except ValidationError as e:
            # Handle Pydantic validation errors gracefully
            # Log validation errors and mark as "needs_review" by setting confidence to 0.0
            logger.warning(f"Validation error parsing extraction response: {e}")

            if error_logger and ErrorRecord and ErrorSeverity and ErrorCategory:
                error_record = ErrorRecord(
                    timestamp=datetime.now(UTC),
                    severity=ErrorSeverity.WARNING,
                    category=ErrorCategory.PERMANENT,
                    message="Entity extraction validation failed - marked for manual review",
                    error_type="ValidationError",
                    stack_trace=str(e),
                    context={
                        "email_id": email_id
                        or f"email_{hash(email_text) % 1000000:06d}",
                        "operation": "extract_entities",
                        "validation_errors": e.errors()
                        if hasattr(e, "errors")
                        else str(e),
                        "needs_manual_review": True,
                    },
                    retry_count=0,
                )
                error_logger.log_error(error_record)

            # Return a minimal ExtractedEntities with "needs_review" flag (low confidence)
            # This allows processing to continue while flagging the extraction as problematic
            return self._create_needs_review_entity(
                response_data, email_text, email_id, e
            )

    def _build_extracted_entities(
        self,
        response_data: Dict[str, Any],
        email_text: str,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> ExtractedEntities:
        """Build ExtractedEntities from response data (with validation).

        Args:
            response_data: Parsed JSON response from Gemini
            email_text: Original email text
            company_context: Optional company context
            email_id: Optional email message ID

        Returns:
            ExtractedEntities: Validated entity extraction

        Raises:
            ValidationError: If Pydantic validation fails
        """
        try:
            # Extract values and confidence scores (Phase 1b fields)
            person_data = response_data.get("person_in_charge", {})
            startup_data = response_data.get("startup_name", {})
            partner_data = response_data.get("partner_org", {})
            details_data = response_data.get("details", {})
            date_data = response_data.get("date", {})

            # Parse date string to datetime (using enhanced date_parser)
            date_str = date_data.get("value")
            if date_str:
                parsed_result = parse_date(date_str)
                parsed_date = parsed_result.parsed_date if parsed_result else None
            else:
                parsed_date = None

            # Use provided email_id or generate from email text hash (backward compatibility)
            if email_id is None:
                email_id = f"email_{hash(email_text) % 1000000:06d}"

            # Extract matching fields (Phase 2b) - only if company_context was provided
            matched_company_id = None
            matched_partner_id = None
            startup_match_confidence = None
            partner_match_confidence = None

            if company_context:
                # Get matching data from response
                matched_company_id = response_data.get("matched_company_id")
                matched_partner_id = response_data.get("matched_partner_id")
                startup_match_confidence = response_data.get("startup_match_confidence")
                partner_match_confidence = response_data.get("partner_match_confidence")

                # Apply confidence threshold (T012): <0.70 = null ID
                if (
                    startup_match_confidence is not None
                    and startup_match_confidence < 0.70
                ):
                    matched_company_id = None
                    logger.info(
                        f"Low startup match confidence ({startup_match_confidence:.2f}), "
                        "setting matched_company_id to null"
                    )

                if (
                    partner_match_confidence is not None
                    and partner_match_confidence < 0.70
                ):
                    matched_partner_id = None
                    logger.info(
                        f"Low partner match confidence ({partner_match_confidence:.2f}), "
                        "setting matched_partner_id to null"
                    )

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
                # Phase 2b matching fields
                matched_company_id=matched_company_id,
                matched_partner_id=matched_partner_id,
                startup_match_confidence=startup_match_confidence,
                partner_match_confidence=partner_match_confidence,
            )

            return entities

        except ValidationError:
            # Re-raise ValidationError to be caught by _parse_response
            raise
        except (KeyError, TypeError, ValueError) as e:
            raise LLMValidationError(f"Invalid response format: {e}") from e

    def _create_needs_review_entity(
        self,
        response_data: Dict[str, Any],
        email_text: str,
        email_id: Optional[str],
        validation_error: ValidationError,
    ) -> ExtractedEntities:
        """Create a minimal ExtractedEntities marked for manual review.

        This is called when validation fails (e.g., malformed company UUID).
        Returns an entity with all confidence scores set to 0.0 to flag as "needs_review".

        Args:
            response_data: Original response data (may be malformed)
            email_text: Original email text
            email_id: Email message ID
            validation_error: The validation error that occurred

        Returns:
            ExtractedEntities: Minimal entity marked for review (all confidences = 0.0)
        """
        # Use provided email_id or generate from email text hash
        if email_id is None:
            email_id = f"email_{hash(email_text) % 1000000:06d}"

        # Extract whatever values we can from the malformed response (best effort)
        person_data = response_data.get("person_in_charge", {})
        startup_data = response_data.get("startup_name", {})
        partner_data = response_data.get("partner_org", {})
        details_data = response_data.get("details", {})
        date_data = response_data.get("date", {})

        # Parse date if possible (using enhanced date_parser)
        date_str = date_data.get("value") if isinstance(date_data, dict) else None
        parsed_date = None
        if date_str:
            try:
                parsed_result = parse_date(date_str)
                parsed_date = parsed_result.parsed_date if parsed_result else None
            except Exception:
                pass

        # Create entity with all confidence scores at 0.0 (needs manual review)
        return ExtractedEntities(
            person_in_charge=person_data.get("value")
            if isinstance(person_data, dict)
            else None,
            startup_name=startup_data.get("value")
            if isinstance(startup_data, dict)
            else None,
            partner_org=partner_data.get("value")
            if isinstance(partner_data, dict)
            else None,
            details=details_data.get("value")
            if isinstance(details_data, dict)
            else None,
            date=parsed_date,
            confidence=ConfidenceScores(
                person=0.0,
                startup=0.0,
                partner=0.0,
                details=0.0,
                date=0.0,
            ),
            email_id=email_id,
            # Set matched IDs to None (validation failed, so no matching)
            matched_company_id=None,
            matched_partner_id=None,
            startup_match_confidence=None,
            partner_match_confidence=None,
        )

    def _call_with_retry(
        self, email_text: str, company_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call Gemini API with exponential backoff retry.

        Args:
            email_text: Email text to extract entities from
            company_context: Optional company list for matching

        Returns:
            dict: Parsed JSON response from Gemini

        Raises:
            LLMAPIError: After max retries exhausted
        """
        for attempt in range(self.max_retries):
            try:
                return self._call_gemini_api(email_text, company_context)

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
                        f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})"
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
                        raise LLMAPIError(
                            f"API error after {self.max_retries} retries: {e}"
                        ) from e
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
            raise LLMTimeoutError(
                "Request timeout", timeout_seconds=self.timeout
            ) from error
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
            error,
            (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied),
        ) or (hasattr(error, "status_code") and error.status_code in (401, 403))
