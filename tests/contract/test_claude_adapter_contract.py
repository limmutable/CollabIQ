"""Contract tests for ClaudeAdapter.

This module ensures ClaudeAdapter adheres to the LLMProvider interface contract.
All tests verify the interface compliance defined in llm-provider-interface.md.
"""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from llm_provider.base import LLMProvider
from llm_provider.exceptions import LLMAPIError
from llm_provider.types import ExtractedEntities


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "test_anthropic_api_key"


@pytest.fixture
@patch("llm_adapters.claude_adapter.anthropic.Anthropic")
def claude_adapter(mock_anthropic_class, mock_api_key):
    """Create ClaudeAdapter instance for testing."""
    # Import here to avoid issues if module doesn't exist yet
    from llm_adapters.claude_adapter import ClaudeAdapter

    # Mock the Anthropic client
    mock_anthropic_class.return_value = MagicMock()
    return ClaudeAdapter(api_key=mock_api_key)


class TestClaudeAdapterContract:
    """Contract tests ensuring ClaudeAdapter implements LLMProvider interface."""

    def test_claude_adapter_inherits_from_llm_provider(self, claude_adapter):
        """Verify ClaudeAdapter inherits from LLMProvider."""
        assert isinstance(claude_adapter, LLMProvider)

    def test_claude_adapter_has_extract_entities_method(self, claude_adapter):
        """Verify ClaudeAdapter has extract_entities method."""
        assert hasattr(claude_adapter, "extract_entities")
        assert callable(claude_adapter.extract_entities)

    def test_extract_entities_accepts_email_text(self, claude_adapter):
        """Contract 1: extract_entities accepts email_text string parameter."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"person_in_charge": "김철수", "startup_name": "본봄", '
                '"partner_org": "신세계", "details": "킥오프", '
                '"date": "2025-11-07", "confidence": {"person": 0.9, '
                '"startup": 0.9, "partner": 0.9, "details": 0.9, "date": 0.9}}'
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        claude_adapter.client.messages.create.return_value = mock_response

        # Call with email_text string
        result = claude_adapter.extract_entities("sample email text")

        # Verify it returns ExtractedEntities
        assert isinstance(result, ExtractedEntities)

    def test_extract_entities_returns_extracted_entities(self, claude_adapter):
        """Contract 2: extract_entities returns ExtractedEntities with all attributes."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"person_in_charge": "김철수", "startup_name": "본봄", '
                '"partner_org": "신세계", "details": "킥오프", '
                '"date": "2025-11-07", "confidence": {"person": 0.9, '
                '"startup": 0.9, "partner": 0.9, "details": 0.9, "date": 0.9}}'
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        claude_adapter.client.messages.create.return_value = mock_response

        result = claude_adapter.extract_entities("collaboration update email")

        # Verify all required attributes exist
        assert hasattr(result, "person_in_charge")
        assert hasattr(result, "startup_name")
        assert hasattr(result, "partner_org")
        assert hasattr(result, "details")
        assert hasattr(result, "date")
        assert hasattr(result, "confidence")
        assert hasattr(result, "email_id")
        assert hasattr(result, "extracted_at")

    def test_extract_entities_raises_llm_api_error_on_failure(self, claude_adapter):
        """Contract 3: extract_entities raises LLMAPIError on failure."""
        # Simulate API error
        claude_adapter.client.messages.create.side_effect = Exception("API Error")

        with pytest.raises(LLMAPIError):
            claude_adapter.extract_entities("email text")

    def test_confidence_scores_are_0_to_1(self, claude_adapter):
        """Contract 4: Confidence scores are in range [0.0, 1.0]."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"person_in_charge": "김철수", "startup_name": "본봄", '
                '"partner_org": "신세계", "details": "킥오프", '
                '"date": "2025-11-07", "confidence": {"person": 0.95, '
                '"startup": 0.92, "partner": 0.88, "details": 0.90, "date": 0.85}}'
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        claude_adapter.client.messages.create.return_value = mock_response

        result = claude_adapter.extract_entities("sample email")

        # Verify confidence scores are in valid range
        assert 0.0 <= result.confidence.person <= 1.0
        assert 0.0 <= result.confidence.startup <= 1.0
        assert 0.0 <= result.confidence.partner <= 1.0
        assert 0.0 <= result.confidence.details <= 1.0
        assert 0.0 <= result.confidence.date <= 1.0

    def test_missing_entities_return_none_with_zero_confidence(self, claude_adapter):
        """Contract 5: Missing entities return None with confidence 0.0."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"person_in_charge": null, "startup_name": "본봄", '
                '"partner_org": null, "details": "킥오프", '
                '"date": null, "confidence": {"person": 0.0, '
                '"startup": 0.9, "partner": 0.0, "details": 0.9, "date": 0.0}}'
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        claude_adapter.client.messages.create.return_value = mock_response

        result = claude_adapter.extract_entities("email with missing person")

        # Verify None values have 0.0 confidence
        if result.person_in_charge is None:
            assert result.confidence.person == 0.0

        if result.partner_org is None:
            assert result.confidence.partner == 0.0

        if result.date is None:
            assert result.confidence.date == 0.0

    def test_interface_cannot_be_instantiated_directly(self):
        """Contract 6: LLMProvider interface cannot be instantiated."""
        with pytest.raises(TypeError):
            LLMProvider()
