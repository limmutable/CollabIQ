"""Integration tests for date parser usage in LLM adapters.

This test suite verifies that all LLM adapters correctly use the enhanced
date_parser library (Phase 4.5 integration) instead of the legacy date_utils.

Tests cover:
- Korean date formats (full dates, partial dates, week notation)
- English date formats
- ISO 8601 dates
- Invalid/missing dates
- Confidence scoring availability
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from llm_adapters.gemini_adapter import GeminiAdapter
from llm_adapters.claude_adapter import ClaudeAdapter
from llm_adapters.openai_adapter import OpenAIAdapter


# Sample email texts with various date formats
KOREAN_FULL_DATE = "2024년 11월 15일에 미팅이 있습니다."
KOREAN_WEEK = "11월 2주에 PoC 시작 예정입니다."
KOREAN_PARTIAL = "11월 15일에 킥오프 예정입니다."
ENGLISH_DATE = "Meeting scheduled for November 15, 2024"
ISO_DATE = "Meeting on 2024-11-15"
NO_DATE = "일반적인 내용입니다."


class TestGeminiAdapterDateParsing:
    """Test Gemini adapter's integration with enhanced date_parser."""

    @pytest.fixture
    def adapter(self):
        """Create Gemini adapter instance."""
        return GeminiAdapter(api_key="test-key", model="gemini-2.0-flash-exp")

    def test_korean_full_date_parsing(self, adapter):
        """Test parsing Korean full date format (2024년 11월 15일)."""
        mock_response = {
            "person_in_charge": {"value": "김철수", "confidence": 0.95},
            "startup_name": {"value": "본봄", "confidence": 0.90},
            "partner_org": {"value": "신세계", "confidence": 0.90},
            "details": {"value": "미팅", "confidence": 0.85},
            "date": {"value": "2024년 11월 15일", "confidence": 0.95},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities(KOREAN_FULL_DATE)

        # Verify date was parsed correctly
        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15
        assert result.confidence.date == 0.95

    def test_korean_week_notation(self, adapter):
        """Test parsing Korean week notation (11월 2주)."""
        mock_response = {
            "person_in_charge": {"value": "김철수", "confidence": 0.95},
            "startup_name": {"value": "본봄", "confidence": 0.90},
            "partner_org": {"value": "신세계", "confidence": 0.90},
            "details": {"value": "PoC 시작", "confidence": 0.85},
            "date": {"value": "11월 2주", "confidence": 0.80},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities(KOREAN_WEEK)

        # Verify date was parsed (week notation → second Monday of November)
        assert result.date is not None
        assert result.date.month == 11
        # Week 2 should be between 8th and 14th
        assert 8 <= result.date.day <= 14

    def test_korean_partial_date(self, adapter):
        """Test parsing Korean partial date without year (11월 15일)."""
        mock_response = {
            "person_in_charge": {"value": "김철수", "confidence": 0.95},
            "startup_name": {"value": "본봄", "confidence": 0.90},
            "partner_org": {"value": "신세계", "confidence": 0.90},
            "details": {"value": "킥오프", "confidence": 0.85},
            "date": {"value": "11월 15일", "confidence": 0.85},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities(KOREAN_PARTIAL)

        # Verify date was parsed with current year
        assert result.date is not None
        assert result.date.month == 11
        assert result.date.day == 15
        # Year should default to current year
        assert result.date.year in [datetime.now().year, datetime.now().year + 1]

    def test_english_date_format(self, adapter):
        """Test parsing English date format."""
        mock_response = {
            "person_in_charge": {"value": "John Doe", "confidence": 0.95},
            "startup_name": {"value": "TechCo", "confidence": 0.90},
            "partner_org": {"value": "BigCorp", "confidence": 0.90},
            "details": {"value": "Meeting", "confidence": 0.85},
            "date": {"value": "November 15, 2024", "confidence": 0.95},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities(ENGLISH_DATE)

        # Verify date was parsed correctly
        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15

    def test_iso_date_format(self, adapter):
        """Test parsing ISO 8601 date format."""
        mock_response = {
            "person_in_charge": {"value": "John Doe", "confidence": 0.95},
            "startup_name": {"value": "TechCo", "confidence": 0.90},
            "partner_org": {"value": "BigCorp", "confidence": 0.90},
            "details": {"value": "Meeting", "confidence": 0.85},
            "date": {"value": "2024-11-15", "confidence": 1.0},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities(ISO_DATE)

        # Verify date was parsed correctly
        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15

    def test_missing_date(self, adapter):
        """Test handling emails without dates."""
        mock_response = {
            "person_in_charge": {"value": "김철수", "confidence": 0.95},
            "startup_name": {"value": "본봄", "confidence": 0.90},
            "partner_org": {"value": "신세계", "confidence": 0.90},
            "details": {"value": "일반 내용", "confidence": 0.85},
            "date": {"value": None, "confidence": 0.0},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities(NO_DATE)

        # Verify date is None when not found
        assert result.date is None
        assert result.confidence.date == 0.0

    def test_invalid_date_format(self, adapter):
        """Test handling invalid date strings."""
        mock_response = {
            "person_in_charge": {"value": "김철수", "confidence": 0.95},
            "startup_name": {"value": "본봄", "confidence": 0.90},
            "partner_org": {"value": "신세계", "confidence": 0.90},
            "details": {"value": "테스트", "confidence": 0.85},
            "date": {"value": "invalid date string", "confidence": 0.3},
        }

        with patch.object(adapter, "_call_gemini_api", return_value=mock_response):
            result = adapter.extract_entities("테스트 이메일")

        # Enhanced date_parser should return None for invalid dates
        assert result.date is None


class TestClaudeAdapterDateParsing:
    """Test Claude adapter's integration with enhanced date_parser."""

    @pytest.fixture
    def adapter(self):
        """Create Claude adapter instance."""
        return ClaudeAdapter(api_key="test-key")

    def test_korean_date_parsing(self, adapter):
        """Test Claude adapter parses Korean dates correctly."""
        # Mock the Claude API response
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"person_in_charge": "김철수", "startup_name": "본봄", "partner_org": "신세계", "details": "미팅", "date": "2024년 11월 15일"}')]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch.object(adapter.client.messages, "create", return_value=mock_message):
            result = adapter.extract_entities(KOREAN_FULL_DATE)

        # Verify date was parsed
        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15

    def test_iso_date_parsing(self, adapter):
        """Test Claude adapter parses ISO dates correctly."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"person_in_charge": "John", "startup_name": "TechCo", "partner_org": "Corp", "details": "Meeting", "date": "2024-11-15"}')]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch.object(adapter.client.messages, "create", return_value=mock_message):
            result = adapter.extract_entities(ISO_DATE)

        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15


class TestOpenAIAdapterDateParsing:
    """Test OpenAI adapter's integration with enhanced date_parser."""

    @pytest.fixture
    def adapter(self):
        """Create OpenAI adapter instance."""
        return OpenAIAdapter(api_key="test-key")

    def test_korean_date_parsing(self, adapter):
        """Test OpenAI adapter parses Korean dates correctly."""
        # Mock the OpenAI API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"person_in_charge": "김철수", "startup_name": "본봄", "partner_org": "신세계", "details": "미팅", "date": "2024년 11월 15일"}'
                )
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)

        with patch.object(
            adapter.client.chat.completions, "create", return_value=mock_response
        ):
            result = adapter.extract_entities(KOREAN_FULL_DATE)

        # Verify date was parsed
        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15

    def test_iso_date_parsing(self, adapter):
        """Test OpenAI adapter parses ISO dates correctly."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"person_in_charge": "John", "startup_name": "TechCo", "partner_org": "Corp", "details": "Meeting", "date": "2024-11-15"}'
                )
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)

        with patch.object(
            adapter.client.chat.completions, "create", return_value=mock_response
        ):
            result = adapter.extract_entities(ISO_DATE)

        assert result.date is not None
        assert result.date.year == 2024
        assert result.date.month == 11
        assert result.date.day == 15


class TestDateParserIntegration:
    """Test that adapters actually use date_parser, not old date_utils."""

    def test_gemini_imports_date_parser(self):
        """Verify Gemini adapter imports from date_parser."""
        from llm_adapters import gemini_adapter

        # Check that parse_date is imported from date_parser
        assert hasattr(gemini_adapter, "parse_date")
        # Verify it's the enhanced parse_date (returns ParsedDate, not datetime)
        from collabiq.date_parser.parser import parse_date as enhanced_parse_date

        assert gemini_adapter.parse_date is enhanced_parse_date

    def test_claude_imports_date_parser(self):
        """Verify Claude adapter imports from date_parser."""
        from llm_adapters import claude_adapter

        assert hasattr(claude_adapter, "parse_date")
        from collabiq.date_parser.parser import parse_date as enhanced_parse_date

        assert claude_adapter.parse_date is enhanced_parse_date

    def test_openai_imports_date_parser(self):
        """Verify OpenAI adapter imports from date_parser."""
        from llm_adapters import openai_adapter

        assert hasattr(openai_adapter, "parse_date")
        from collabiq.date_parser.parser import parse_date as enhanced_parse_date

        assert openai_adapter.parse_date is enhanced_parse_date


class TestDateParserConfidence:
    """Test that enhanced date_parser provides confidence scoring."""

    def test_confidence_available_from_parse_date(self):
        """Verify parse_date returns ParsedDate with confidence."""
        from collabiq.date_parser.parser import parse_date

        # Parse a clear date
        result = parse_date("2024년 11월 15일")
        assert result is not None
        assert hasattr(result, "confidence")
        assert 0.0 <= result.confidence <= 1.0
        # High confidence for clear format
        assert result.confidence >= 0.9

    def test_confidence_for_ambiguous_dates(self):
        """Verify lower confidence for ambiguous dates."""
        from collabiq.date_parser.parser import parse_date

        # Parse week notation (more ambiguous)
        result = parse_date("11월 2주")
        assert result is not None
        assert hasattr(result, "confidence")
        # Should have reasonable confidence but maybe not 1.0
        assert 0.7 <= result.confidence <= 1.0
