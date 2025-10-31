"""
Unit tests for quoted thread detection in ContentNormalizer.

Tests cover:
- T063: Angle bracket quote detection ("> " prefix)
- T064: "On [date] wrote:" header detection
- T065: Nested quote removal
- T066: No quotes means no change
"""

from pathlib import Path

import pytest

try:
    from src.content_normalizer.normalizer import ContentNormalizer
except ImportError:
    from content_normalizer.normalizer import ContentNormalizer


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_emails"


@pytest.fixture
def quoted_thread_samples():
    """Load all quoted thread test fixtures."""
    samples = {}
    for fixture_file in FIXTURES_DIR.glob("quoted_thread_*.txt"):
        key = fixture_file.stem.replace("quoted_thread_", "")
        samples[key] = fixture_file.read_text(encoding="utf-8")
    return samples


@pytest.fixture
def normalizer():
    """Create Content Normalizer instance for testing."""
    return ContentNormalizer()


def test_detect_angle_bracket_quotes(normalizer, quoted_thread_samples):
    """
    T063: Test detection of angle bracket quoted content ("> " prefix).

    Given an email with angle bracket quotes,
    When detect_quoted_thread() is called,
    Then quoted content location should be detected.
    """
    email_body = quoted_thread_samples["angle_bracket"]

    # Detect quoted thread
    quote_start = normalizer.detect_quoted_thread(email_body)

    assert quote_start is not None, "Should detect angle bracket quotes"
    assert quote_start > 0, "Quote should not start at beginning"
    # Pattern detects "On Oct 30" header which includes the angle bracket quotes
    assert "On Oct 30" in email_body[quote_start:], "Should detect quoted section"
    assert ">" in email_body[quote_start:], "Should include angle bracket quotes"


def test_detect_nested_quotes(normalizer, quoted_thread_samples):
    """
    T065: Test detection of nested quoted content (multiple levels).

    Given an email with nested quotes (> and > >),
    When detect_quoted_thread() is called,
    Then all nested quote levels should be detected.
    """
    email_body = quoted_thread_samples["nested"]

    # Detect quoted thread
    quote_start = normalizer.detect_quoted_thread(email_body)

    assert quote_start is not None, "Should detect nested quotes"
    # Verify both levels are in the detected section
    quoted_section = email_body[quote_start:]
    # Pattern detects header "On Wed, Oct 30" which precedes the angle brackets
    assert "On Wed, Oct 30" in quoted_section or "> I think" in quoted_section, "Should detect quoted section"
    assert "> >" in quoted_section, "Should detect nested quote marker"


def test_detect_on_date_header(normalizer, quoted_thread_samples):
    """
    T064: Test detection of "On [date] wrote:" reply headers.

    Given an email with "On [date]... wrote:" header,
    When detect_quoted_thread() is called,
    Then reply header should be detected.
    """
    email_body = quoted_thread_samples["on_date_header"]

    # Detect quoted thread
    quote_start = normalizer.detect_quoted_thread(email_body)

    assert quote_start is not None, "Should detect 'On [date] wrote:' header"
    assert "On Monday, Nov 1" in email_body[quote_start:], "Should detect date header"


def test_detect_korean_quoted_thread(normalizer, quoted_thread_samples):
    """
    Test detection of Korean quoted thread patterns.

    Given an email with Korean date format quotes,
    When detect_quoted_thread() is called,
    Then Korean quote pattern should be detected.
    """
    email_body = quoted_thread_samples["korean"]

    # Detect quoted thread
    quote_start = normalizer.detect_quoted_thread(email_body)

    assert quote_start is not None, "Should detect Korean quoted thread"
    assert "2025년" in email_body[quote_start:], "Should detect Korean date format"


def test_no_quotes_no_change(normalizer, quoted_thread_samples):
    """
    T066: Test that emails without quotes remain unchanged.

    Given an email with no quoted content,
    When detect_quoted_thread() is called,
    Then no quote should be detected.
    """
    email_body = quoted_thread_samples["no_quotes"]

    # Detect quoted thread (should return None)
    quote_start = normalizer.detect_quoted_thread(email_body)

    assert quote_start is None, "Should not detect quotes in fresh email"

    # Remove quoted thread (should return original)
    cleaned_body = normalizer.remove_quoted_thread(email_body)

    assert cleaned_body == email_body, "Should not modify email without quotes"


def test_remove_angle_bracket_quotes_preserves_content(normalizer, quoted_thread_samples):
    """
    Test that quote removal preserves main email content.

    Given an email with quoted thread,
    When remove_quoted_thread() is called,
    Then main content should be preserved and quotes removed.
    """
    email_body = quoted_thread_samples["angle_bracket"]

    # Expected main content (before quoted section)
    expected_content = "Thanks for the update on the project timeline"

    # Remove quoted thread
    cleaned_body = normalizer.remove_quoted_thread(email_body)

    assert expected_content in cleaned_body, "Should preserve main content"
    assert "> On Oct 30" not in cleaned_body, "Should remove quoted section"
    assert len(cleaned_body) < len(email_body), "Cleaned body should be shorter"


def test_remove_nested_quotes(normalizer, quoted_thread_samples):
    """
    T065: Test removal of nested quoted content.

    Given an email with multi-level quotes,
    When remove_quoted_thread() is called,
    Then all quote levels should be removed.
    """
    email_body = quoted_thread_samples["nested"]

    # Expected main content
    expected_content = "I agree with the proposed solution"

    # Remove quoted thread
    cleaned_body = normalizer.remove_quoted_thread(email_body)

    assert expected_content in cleaned_body, "Should preserve main content"
    assert "> On Wed" not in cleaned_body, "Should remove first level quotes"
    assert "> >" not in cleaned_body, "Should remove second level quotes"
    assert "Mike Chen" not in cleaned_body, "Should remove all quoted content"


def test_remove_on_date_header(normalizer, quoted_thread_samples):
    """
    Test removal of "On [date] wrote:" style quotes.

    Given an email with reply header,
    When remove_quoted_thread() is called,
    Then reply header and content should be removed.
    """
    email_body = quoted_thread_samples["on_date_header"]

    # Expected main content
    expected_content = "Perfect! I'll incorporate your feedback"

    # Remove quoted thread
    cleaned_body = normalizer.remove_quoted_thread(email_body)

    assert expected_content in cleaned_body, "Should preserve main content"
    assert "On Monday, Nov 1" not in cleaned_body, "Should remove date header"
    assert "Lisa Park wrote:" not in cleaned_body, "Should remove author line"


def test_boundary_cases_quoted_threads(normalizer):
    """
    Test boundary cases for quoted thread detection.

    Cases:
    - Email that is entirely quoted (no original content)
    - Quote markers in middle of content (not actual quotes)
    - Empty email
    """
    # Entirely quoted email
    entirely_quoted = "> This entire email is a quote\n> Nothing original here"
    result = normalizer.remove_quoted_thread(entirely_quoted)
    # Should either remove everything or return empty
    assert len(result) <= len(entirely_quoted), "Should handle entirely quoted email"

    # Quote marker in content (not at line start)
    fake_quote = "The formula is: x > y where x and y are positive"
    result = normalizer.remove_quoted_thread(fake_quote)
    assert result == fake_quote, "Should not remove non-quote '>' symbols"

    # Empty email
    assert normalizer.detect_quoted_thread("") is None, "Should handle empty email"
    assert normalizer.remove_quoted_thread("") == "", "Should return empty for empty input"


def test_quoted_thread_removal_integration(normalizer, quoted_thread_samples):
    """
    Integration test: Full quoted thread removal workflow.

    Test complete flow from detection to removal with content preservation.
    """
    email_body = quoted_thread_samples["angle_bracket"]

    # Step 1: Detect
    quote_start = normalizer.detect_quoted_thread(email_body)
    assert quote_start is not None, "Should detect quoted thread"

    # Step 2: Remove
    cleaned_body = normalizer.remove_quoted_thread(email_body)
    assert len(cleaned_body) < len(email_body), "Should remove content"

    # Step 3: Verify main content preserved
    assert "Thanks for the update" in cleaned_body, "Should preserve main content"
    assert "I'll review the attached" in cleaned_body, "Should preserve full content"

    # Step 4: Verify quotes removed
    assert "> On Oct 30" not in cleaned_body, "Should remove quote header"
    assert "John Smith wrote:" not in cleaned_body, "Should remove author line"
    assert "Phase 1" not in cleaned_body, "Should remove quoted content"
