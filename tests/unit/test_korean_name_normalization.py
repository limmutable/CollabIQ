"""
Unit tests for Korean company name normalization.

Tests whitespace trimming and basic normalization rules before fuzzy matching.
Per spec: "Minimal normalization - trim whitespace only" (data-model.md).
"""

import pytest


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for matching.

    Normalization rules (MVP - minimal):
    1. Trim leading/trailing whitespace
    2. No other transformations (preserve case, punctuation, internal spacing)

    Args:
        name: Raw company name (may have extra whitespace)

    Returns:
        Normalized company name

    Raises:
        ValueError: If name is empty or whitespace-only after normalization
    """
    normalized = name.strip()

    if not normalized:
        raise ValueError("Company name cannot be empty or whitespace-only")

    return normalized


class TestWhitespaceTrimming:
    """Test whitespace trimming normalization."""

    def test_trim_leading_whitespace(self):
        """Test: Leading whitespace is removed."""
        assert normalize_company_name("  웨이크") == "웨이크"
        assert normalize_company_name("\t웨이크") == "웨이크"
        assert normalize_company_name("\n웨이크") == "웨이크"

    def test_trim_trailing_whitespace(self):
        """Test: Trailing whitespace is removed."""
        assert normalize_company_name("웨이크  ") == "웨이크"
        assert normalize_company_name("웨이크\t") == "웨이크"
        assert normalize_company_name("웨이크\n") == "웨이크"

    def test_trim_both_sides(self):
        """Test: Both leading and trailing whitespace removed."""
        assert normalize_company_name("  웨이크  ") == "웨이크"
        assert normalize_company_name("\t웨이크\n") == "웨이크"

    def test_no_change_if_no_extra_whitespace(self):
        """Test: Names without extra whitespace are unchanged."""
        assert normalize_company_name("웨이크") == "웨이크"
        assert normalize_company_name("스타트업A") == "스타트업A"


class TestInternalWhitespacePreservation:
    """Test that internal whitespace is preserved (not collapsed)."""

    def test_preserve_internal_single_space(self):
        """Test: Single internal spaces are preserved."""
        assert normalize_company_name("스타트업 A") == "스타트업 A"
        assert normalize_company_name("네트워크 코리아") == "네트워크 코리아"

    def test_preserve_internal_multiple_spaces(self):
        """Test: Multiple internal spaces are preserved (no collapsing)."""
        # MVP: Minimal normalization - do NOT collapse internal spaces
        assert normalize_company_name("스타트업  A") == "스타트업  A"
        assert normalize_company_name("A   B   C") == "A   B   C"


class TestCasePreservation:
    """Test that case is preserved (no lowercasing)."""

    def test_preserve_uppercase(self):
        """Test: Uppercase letters are preserved."""
        assert normalize_company_name("ABC Company") == "ABC Company"
        assert normalize_company_name("SSG") == "SSG"

    def test_preserve_lowercase(self):
        """Test: Lowercase letters are preserved."""
        assert normalize_company_name("abc company") == "abc company"

    def test_preserve_mixed_case(self):
        """Test: Mixed case is preserved."""
        assert normalize_company_name("WeWork Korea") == "WeWork Korea"


class TestPunctuationPreservation:
    """Test that punctuation is preserved."""

    def test_preserve_parentheses(self):
        """Test: Parentheses are preserved."""
        assert normalize_company_name("웨이크(산스)") == "웨이크(산스)"
        assert normalize_company_name("(주)스타트업") == "(주)스타트업"

    def test_preserve_hyphens(self):
        """Test: Hyphens are preserved."""
        assert normalize_company_name("스타트업-코리아") == "스타트업-코리아"

    def test_preserve_ampersands(self):
        """Test: Ampersands are preserved."""
        assert normalize_company_name("A & B Company") == "A & B Company"

    def test_preserve_periods(self):
        """Test: Periods are preserved."""
        assert normalize_company_name("ABC Co.") == "ABC Co."


class TestKoreanTextHandling:
    """Test proper handling of Korean text (UTF-8 encoding)."""

    def test_korean_characters_preserved(self):
        """Test: Korean characters are preserved correctly."""
        assert normalize_company_name("웨이크") == "웨이크"
        assert normalize_company_name("스마트푸드네트워크") == "스마트푸드네트워크"

    def test_mixed_korean_english(self):
        """Test: Mixed Korean/English text is handled."""
        assert normalize_company_name("WeWork 코리아") == "WeWork 코리아"
        assert normalize_company_name("삼성 Samsung") == "삼성 Samsung"

    def test_korean_with_numbers(self):
        """Test: Korean text with numbers is handled."""
        assert normalize_company_name("스타트업123") == "스타트업123"


class TestErrorCases:
    """Test error handling for invalid inputs."""

    def test_empty_string_raises_error(self):
        """Test: Empty string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            normalize_company_name("")

    def test_whitespace_only_raises_error(self):
        """Test: Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            normalize_company_name("   ")

        with pytest.raises(ValueError):
            normalize_company_name("\t\n  ")

    def test_single_space_raises_error(self):
        """Test: Single space raises ValueError."""
        with pytest.raises(ValueError):
            normalize_company_name(" ")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_character_name(self):
        """Test: Single character names are valid."""
        assert normalize_company_name("A") == "A"
        assert normalize_company_name("김") == "김"

    def test_very_long_name(self):
        """Test: Very long names are handled correctly."""
        long_name = "A" * 200
        assert normalize_company_name(long_name) == long_name

    def test_unicode_whitespace_variants(self):
        """Test: Different Unicode whitespace characters are trimmed."""
        # Various Unicode whitespace characters
        assert normalize_company_name("\u0020웨이크") == "웨이크"  # Regular space
        assert normalize_company_name("\u00A0웨이크") == "웨이크"  # Non-breaking space
        # Note: Python's str.strip() handles these automatically


@pytest.mark.parametrize(
    "input_name,expected_output",
    [
        # Basic trimming
        ("  웨이크", "웨이크"),
        ("웨이크  ", "웨이크"),
        ("  웨이크  ", "웨이크"),
        # Preservation tests
        ("스타트업 A", "스타트업 A"),  # Internal space preserved
        ("ABC Company", "ABC Company"),  # Case preserved
        ("웨이크(산스)", "웨이크(산스)"),  # Punctuation preserved
        # Complex cases
        ("  (주)스타트업  ", "(주)스타트업"),
        ("\tWeWork 코리아\n", "WeWork 코리아"),
        ("  A & B  ", "A & B"),
    ],
)
def test_normalization_parametrized(input_name: str, expected_output: str):
    """
    Parametrized test for normalization rules.

    Args:
        input_name: Input company name (may have extra whitespace)
        expected_output: Expected normalized output
    """
    assert normalize_company_name(input_name) == expected_output
