"""Abstract base class for LLM providers.

This module defines the LLMProvider interface that all concrete LLM adapters
must implement. This abstraction enables swapping between different LLM services
(Gemini, GPT-4, Claude) without changing business logic.
"""

from abc import ABC, abstractmethod

from .types import ExtractedEntities


class LLMProvider(ABC):
    """Abstract base class for LLM-based entity extraction.

    All concrete LLM adapters (GeminiAdapter, GPT4Adapter, ClaudeAdapter) must
    implement this interface to ensure consistent behavior across providers.

    Example:
        >>> from llm_adapters.gemini_adapter import GeminiAdapter
        >>> llm: LLMProvider = GeminiAdapter(api_key="AIza...")
        >>> email_text = "어제 신세계와 본봄 파일럿 킥오프"
        >>> entities = llm.extract_entities(email_text)
        >>> print(entities.startup_name)
        '본봄'
    """

    @abstractmethod
    async def extract_entities(self, email_text: str) -> ExtractedEntities:
        """Extract 5 key entities from email text with confidence scores.

        This method sends the email text to the LLM API and parses the response
        into structured ExtractedEntities format.

        Args:
            email_text: Cleaned email body (Korean/English/mixed)
                       Non-empty string, max 10,000 characters
                       Signatures, disclaimers, quoted text already removed

        Returns:
            ExtractedEntities: Pydantic model with 5 entities + confidence scores
                - person_in_charge: 담당자 (or None if missing)
                - startup_name: 스타트업명 (or None if missing)
                - partner_org: 협업기관 (or None if missing)
                - details: 협업내용 (original text preserved)
                - date: 날짜 (parsed to datetime)
                - confidence: ConfidenceScores (0.0-1.0 per field)
                - email_id: Unique identifier
                - extracted_at: UTC timestamp

        Raises:
            LLMAPIError: Base exception for all LLM API errors
            LLMRateLimitError: Rate limit exceeded (429)
                              Caller should retry with exponential backoff
            LLMTimeoutError: Request timeout (408)
                            Caller may retry with increased timeout
            LLMAuthenticationError: Authentication failed (401/403)
                                   No retry - requires API key fix
            LLMValidationError: Malformed API response
                               Response doesn't match expected schema

        Example:
            >>> llm = GeminiAdapter(api_key="AIza...", model="gemini-2.0-flash-exp")
            >>> email = "TableManager kicked off pilot with Shinsegae yesterday"
            >>> entities = await llm.extract_entities(email)
            >>> entities.startup_name
            'TableManager'
            >>> entities.confidence.startup >= 0.85
            True
        """
        pass

    async def generate_summary(self, email_text: str) -> str:
        """Generate a 1-4 line summary of the email content.

        Args:
            email_text: Cleaned email body

        Returns:
            str: Summary text (1-4 lines)
        """
        raise NotImplementedError("generate_summary not implemented by this provider")
