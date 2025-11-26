"""Integration tests for GeminiAdapter.

These tests verify the GeminiAdapter implementation with mocked Gemini API calls.
Tests cover Korean, English, and mixed language emails.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from llm_adapters.gemini_adapter import GeminiAdapter
from llm_provider.types import ExtractedEntities
from llm_provider.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMAuthenticationError,
)


# Load mock responses
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
with open(FIXTURES_DIR / "mocks" / "gemini_responses.json") as f:
    MOCK_RESPONSES = json.load(f)


@pytest.fixture
def gemini_adapter():
    """Create GeminiAdapter instance for testing."""
    return GeminiAdapter(
        api_key="mock-api-key-AIzaSyD1234567890",
        model="gemini-2.0-flash-exp",
        timeout=10,
        max_retries=3,
    )


@pytest.fixture
def korean_email_001():
    """Load Korean test email 001."""
    with open(FIXTURES_DIR / "sample_emails" / "korean_001.txt") as f:
        return f.read()


@pytest.fixture
def english_email_001():
    """Load English test email 001."""
    with open(FIXTURES_DIR / "sample_emails" / "english_001.txt") as f:
        return f.read()


@pytest.mark.asyncio
async def test_gemini_adapter_korean_email(gemini_adapter, korean_email_001):
    """Test extraction from Korean email with mocked API."""
    mock_response = MOCK_RESPONSES["korean_001"]

    with patch.object(gemini_adapter, "_call_gemini_api", return_value=mock_response):
        result = await gemini_adapter.extract_entities(korean_email_001)

        # Verify result is ExtractedEntities
        assert isinstance(result, ExtractedEntities)

        # Verify Korean extraction accuracy
        assert result.person_in_charge == "김철수"
        assert result.startup_name == "본봄"
        assert result.partner_org == "신세계인터내셔널"
        assert "파일럿 킥오프" in result.details
        assert result.confidence.person >= 0.85


@pytest.mark.asyncio
async def test_gemini_adapter_english_email(gemini_adapter, english_email_001):
    """Test extraction from English email with mocked API."""
    mock_response = MOCK_RESPONSES["english_001"]

    with patch.object(gemini_adapter, "_call_gemini_api", return_value=mock_response):
        result = await gemini_adapter.extract_entities(english_email_001)

        # Verify result is ExtractedEntities
        assert isinstance(result, ExtractedEntities)

        # Verify English extraction accuracy
        assert result.person_in_charge == "John Kim"
        assert result.startup_name == "TableManager"
        assert result.partner_org == "Shinsegae Food"
        assert "pilot" in result.details.lower()
        assert result.confidence.startup >= 0.85


@pytest.mark.asyncio
async def test_gemini_adapter_missing_person(gemini_adapter):
    """Test extraction from email with missing person_in_charge."""
    mock_response = MOCK_RESPONSES["english_002"]

    with patch.object(gemini_adapter, "_call_gemini_api", return_value=mock_response):
        email_text = "We had a kickoff meeting with Shinsegae International for BonBom."
        result = await gemini_adapter.extract_entities(email_text)

        # Verify missing person_in_charge
        assert result.person_in_charge is None
        assert result.confidence.person == 0.0

        # Verify other fields are extracted
        assert result.startup_name == "BonBom"
        assert result.partner_org == "Shinsegae International"


@pytest.mark.asyncio
async def test_gemini_adapter_rate_limit_error(gemini_adapter, korean_email_001):
    """Test rate limit error handling (429)."""
    # Create a mock error with status_code attribute (simulates HTTP 429)
    mock_error = Exception("Rate limit exceeded")
    mock_error.status_code = 429

    with patch.object(
        gemini_adapter,
        "_call_gemini_api",
        side_effect=mock_error,
    ):
        with pytest.raises(LLMRateLimitError):
            await gemini_adapter.extract_entities(korean_email_001)


@pytest.mark.asyncio
async def test_gemini_adapter_timeout_error(gemini_adapter, korean_email_001):
    """Test timeout error handling."""
    with patch.object(
        gemini_adapter,
        "_call_gemini_api",
        side_effect=TimeoutError("Request timeout"),
    ):
        with patch.object(
            gemini_adapter, "_handle_api_error", side_effect=LLMTimeoutError()
        ):
            with pytest.raises(LLMTimeoutError):
                await gemini_adapter.extract_entities(korean_email_001)


@pytest.mark.asyncio
async def test_gemini_adapter_authentication_error(gemini_adapter, korean_email_001):
    """Test authentication error handling (401/403)."""
    # Create a mock error with status_code attribute (simulates HTTP 401)
    mock_error = Exception("Invalid API key")
    mock_error.status_code = 401

    with patch.object(
        gemini_adapter,
        "_call_gemini_api",
        side_effect=mock_error,
    ):
        with pytest.raises(LLMAuthenticationError):
            await gemini_adapter.extract_entities(korean_email_001)


@pytest.mark.asyncio
async def test_gemini_adapter_validates_email_text(gemini_adapter):
    """Test input validation for email_text."""
    # Empty string should raise validation error
    with pytest.raises((ValueError, LLMAPIError)):
        await gemini_adapter.extract_entities("")


@pytest.mark.asyncio
async def test_gemini_adapter_confidence_scores_valid_range(gemini_adapter, korean_email_001):
    """Test that all confidence scores are in 0.0-1.0 range."""
    mock_response = MOCK_RESPONSES["korean_001"]

    with patch.object(gemini_adapter, "_call_gemini_api", return_value=mock_response):
        result = await gemini_adapter.extract_entities(korean_email_001)

        # Verify all confidence scores are valid
        assert 0.0 <= result.confidence.person <= 1.0
        assert 0.0 <= result.confidence.startup <= 1.0
        assert 0.0 <= result.confidence.partner <= 1.0
        assert 0.0 <= result.confidence.details <= 1.0
        assert 0.0 <= result.confidence.date <= 1.0
