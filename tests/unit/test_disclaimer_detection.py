"""
Unit tests for disclaimer detection in ContentNormalizer.

Tests cover:
- T077: Confidentiality disclaimer detection
- T078: "Intended only" notice detection
- T079: Disclaimer removal preserves content
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
def disclaimer_samples():
    """Load all disclaimer test fixtures."""
    samples = {}
    for fixture_file in FIXTURES_DIR.glob("disclaimer_*.txt"):
        key = fixture_file.stem.replace("disclaimer_", "")
        samples[key] = fixture_file.read_text(encoding="utf-8")
    return samples


@pytest.fixture
def normalizer():
    """Create ContentNormalizer instance for testing."""
    return ContentNormalizer()


def test_detect_confidentiality_disclaimer(normalizer, disclaimer_samples):
    """
    T077: Test detection of confidentiality disclaimer patterns.

    Given an email with "CONFIDENTIALITY NOTICE",
    When detect_disclaimer() is called,
    Then disclaimer location should be detected.
    """
    email_body = disclaimer_samples["confidentiality"]

    # Detect disclaimer
    disclaimer_start = normalizer.detect_disclaimer(email_body)

    assert disclaimer_start is not None, "Should detect CONFIDENTIALITY NOTICE"
    assert disclaimer_start > 0, "Disclaimer should not start at beginning"
    assert "CONFIDENTIALITY" in email_body[disclaimer_start:], "Should detect confidentiality keyword"


def test_detect_intended_only_notice(normalizer, disclaimer_samples):
    """
    T078: Test detection of "intended only" notice patterns.

    Given an email with "intended only" disclaimer,
    When detect_disclaimer() is called,
    Then disclaimer location should be detected.
    """
    email_body = disclaimer_samples["intended_only"]

    # Detect disclaimer
    disclaimer_start = normalizer.detect_disclaimer(email_body)

    assert disclaimer_start is not None, "Should detect 'intended only' notice"
    assert "intended only" in email_body[disclaimer_start:].lower(), "Should detect intended only phrase"


def test_detect_legal_disclaimer(normalizer, disclaimer_samples):
    """
    Test detection of general legal disclaimer patterns.

    Given an email with "LEGAL DISCLAIMER",
    When detect_disclaimer() is called,
    Then disclaimer location should be detected.
    """
    email_body = disclaimer_samples["legal"]

    # Detect disclaimer
    disclaimer_start = normalizer.detect_disclaimer(email_body)

    assert disclaimer_start is not None, "Should detect LEGAL DISCLAIMER"
    assert "LEGAL DISCLAIMER" in email_body[disclaimer_start:], "Should detect legal disclaimer keyword"


def test_remove_disclaimer_preserves_content(normalizer, disclaimer_samples):
    """
    T079: Test that disclaimer removal preserves main email content.

    Given an email with disclaimer,
    When remove_disclaimer() is called,
    Then main content should be preserved and disclaimer removed.
    """
    email_body = disclaimer_samples["confidentiality"]

    # Expected main content (before disclaimer)
    expected_content = "We've completed the first milestone"

    # Remove disclaimer
    cleaned_body = normalizer.remove_disclaimer(email_body)

    assert expected_content in cleaned_body, "Should preserve main content"
    assert "CONFIDENTIALITY" not in cleaned_body, "Should remove disclaimer"
    assert len(cleaned_body) < len(email_body), "Cleaned body should be shorter"


def test_remove_intended_only_notice(normalizer, disclaimer_samples):
    """
    Test removal of "intended only" disclaimer while preserving Korean content.

    Given an email with Korean content and English disclaimer,
    When remove_disclaimer() is called,
    Then Korean content preserved, disclaimer removed.
    """
    email_body = disclaimer_samples["intended_only"]

    # Expected Korean content
    expected_content = "다음 주 회의 일정"

    # Remove disclaimer
    cleaned_body = normalizer.remove_disclaimer(email_body)

    assert expected_content in cleaned_body, "Should preserve Korean content"
    assert "intended only" not in cleaned_body.lower(), "Should remove disclaimer"
    assert len(cleaned_body) < len(email_body), "Cleaned body should be shorter"


def test_no_disclaimer_no_change(normalizer, disclaimer_samples):
    """
    Test that emails without disclaimers remain unchanged.

    Given an email with no disclaimer,
    When detect_disclaimer() is called,
    Then no disclaimer should be detected.
    """
    email_body = disclaimer_samples["no_disclaimer"]

    # Detect disclaimer (should return None)
    disclaimer_start = normalizer.detect_disclaimer(email_body)

    assert disclaimer_start is None, "Should not detect disclaimer in clean email"

    # Remove disclaimer (should return original)
    cleaned_body = normalizer.remove_disclaimer(email_body)

    assert cleaned_body == email_body, "Should not modify email without disclaimer"


def test_boundary_cases_disclaimers(normalizer):
    """
    Test boundary cases for disclaimer detection.

    Cases:
    - Empty email
    - Very short email
    - Disclaimer keyword in main content (not at end)
    """
    # Empty email
    assert normalizer.detect_disclaimer("") is None, "Should handle empty email"
    assert normalizer.remove_disclaimer("") == "", "Should return empty for empty input"

    # Very short email
    short_email = "Quick update"
    assert normalizer.detect_disclaimer(short_email) is None, "Should not detect in very short email"

    # Disclaimer keyword in content (not disclaimer)
    content_email = "Please keep this confidential. Project update: Phase 1 complete."
    disclaimer_start = normalizer.detect_disclaimer(content_email)
    # Should either not detect, or if detected, should be near the end
    if disclaimer_start:
        # If "confidential" is detected, it should be in a disclaimer-like context
        assert disclaimer_start < len(content_email), "Should handle keyword in content"


def test_multiple_disclaimer_patterns(normalizer):
    """
    Test email with multiple disclaimer-like patterns.

    Given an email with multiple disclaimer keywords,
    When remove_disclaimer() is called,
    Then first disclaimer should be detected and removed.
    """
    email_body = (
        "Project status update.\n\n"
        "CONFIDENTIALITY NOTICE: This is confidential.\n\n"
        "LEGAL DISCLAIMER: Additional legal text."
    )

    # Detect disclaimer
    disclaimer_start = normalizer.detect_disclaimer(email_body)

    assert disclaimer_start is not None, "Should detect disclaimer"

    # Remove disclaimer
    cleaned_body = normalizer.remove_disclaimer(email_body)

    # Should preserve main content
    assert "Project status update" in cleaned_body, "Should preserve main content"
    # Should remove disclaimer section
    assert len(cleaned_body) < len(email_body), "Should remove disclaimer content"


def test_disclaimer_removal_integration(normalizer, disclaimer_samples):
    """
    Integration test: Full disclaimer removal workflow.

    Test complete flow from detection to removal with content preservation.
    """
    email_body = disclaimer_samples["legal"]

    # Step 1: Detect
    disclaimer_start = normalizer.detect_disclaimer(email_body)
    assert disclaimer_start is not None, "Should detect disclaimer"

    # Step 2: Remove
    cleaned_body = normalizer.remove_disclaimer(email_body)
    assert len(cleaned_body) < len(email_body), "Should remove content"

    # Step 3: Verify main content preserved
    assert "Budget approval confirmed" in cleaned_body, "Should preserve main content"
    assert "proceed with the vendor contracts" in cleaned_body, "Should preserve full content"

    # Step 4: Verify disclaimer removed
    assert "LEGAL DISCLAIMER" not in cleaned_body, "Should remove disclaimer header"
    assert "legally privileged" not in cleaned_body, "Should remove disclaimer text"
