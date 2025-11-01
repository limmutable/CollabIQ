"""Contract tests for LLMProvider interface.

These tests verify that any concrete implementation of LLMProvider
(GeminiAdapter, GPT4Adapter, etc.) adheres to the interface contract.

Contract Test Cases:
1. extract_entities accepts email_text string
2. extract_entities returns ExtractedEntities
3. extract_entities raises LLMAPIError on failure
4. Confidence scores are 0.0-1.0
5. Missing entities return None + confidence 0.0
"""

import pytest
from unittest.mock import Mock

from src.llm_provider.base import LLMProvider
from src.llm_provider.types import ExtractedEntities, ConfidenceScores
from src.llm_provider.exceptions import LLMAPIError


class MockLLMProvider(LLMProvider):
    """Mock implementation for contract testing."""

    def __init__(self, return_value: ExtractedEntities = None, should_raise: Exception = None):
        """Initialize mock provider.

        Args:
            return_value: ExtractedEntities to return (or None for default)
            should_raise: Exception to raise (or None for success)
        """
        self.return_value = return_value
        self.should_raise = should_raise

    def extract_entities(self, email_text: str) -> ExtractedEntities:
        """Mock extract_entities implementation."""
        if self.should_raise:
            raise self.should_raise

        if self.return_value:
            return self.return_value

        # Default return value
        return ExtractedEntities(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계인터내셔널",
            details="파일럿 킥오프",
            date=None,
            confidence=ConfidenceScores(
                person=0.95,
                startup=0.92,
                partner=0.88,
                details=0.90,
                date=0.0,
            ),
            email_id="test_001",
        )


def test_extract_entities_accepts_email_text():
    """Test 1: extract_entities accepts email_text string."""
    provider = MockLLMProvider()
    result = provider.extract_entities("sample email text")
    assert isinstance(result, ExtractedEntities)


def test_extract_entities_returns_extracted_entities():
    """Test 2: extract_entities returns ExtractedEntities."""
    provider = MockLLMProvider()
    result = provider.extract_entities("collaboration update email")

    # Verify all required attributes exist
    assert hasattr(result, "person_in_charge")
    assert hasattr(result, "startup_name")
    assert hasattr(result, "partner_org")
    assert hasattr(result, "details")
    assert hasattr(result, "date")
    assert hasattr(result, "confidence")
    assert hasattr(result, "email_id")
    assert hasattr(result, "extracted_at")


def test_extract_entities_raises_llm_api_error_on_failure():
    """Test 3: extract_entities raises LLMAPIError on API failure."""
    provider = MockLLMProvider(should_raise=LLMAPIError("API down"))

    with pytest.raises(LLMAPIError):
        provider.extract_entities("email text")


def test_confidence_scores_are_0_to_1():
    """Test 4: Confidence scores are 0.0-1.0."""
    provider = MockLLMProvider()
    result = provider.extract_entities("sample email")

    # Verify all confidence scores are in valid range
    assert 0.0 <= result.confidence.person <= 1.0
    assert 0.0 <= result.confidence.startup <= 1.0
    assert 0.0 <= result.confidence.partner <= 1.0
    assert 0.0 <= result.confidence.details <= 1.0
    assert 0.0 <= result.confidence.date <= 1.0


def test_missing_entities_return_none_with_zero_confidence():
    """Test 5: Missing entities return None + confidence 0.0."""
    # Create entity with missing person_in_charge
    entities = ExtractedEntities(
        person_in_charge=None,
        startup_name="TableManager",
        partner_org="Shinsegae",
        details="pilot program",
        date=None,
        confidence=ConfidenceScores(
            person=0.0,  # Missing → confidence 0.0
            startup=0.95,
            partner=0.90,
            details=0.85,
            date=0.0,  # Missing → confidence 0.0
        ),
        email_id="test_002",
    )

    provider = MockLLMProvider(return_value=entities)
    result = provider.extract_entities("email with missing person")

    # Verify missing entities have None value + 0.0 confidence
    assert result.person_in_charge is None
    assert result.confidence.person == 0.0
    assert result.date is None
    assert result.confidence.date == 0.0


def test_interface_cannot_be_instantiated_directly():
    """Test 6: LLMProvider is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        LLMProvider()
