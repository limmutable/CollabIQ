"""
Unit tests for signature detection in ContentNormalizer.

Tests cover:
- T048: Korean signature detection
- T049: English signature detection
- T050: Signature removal preserves content
- T051: No signature means no change
"""

from pathlib import Path

import pytest

try:
    from src.content_normalizer.normalizer import ContentNormalizer
    from src.models.raw_email import RawEmail, EmailMetadata
    from src.models.cleaned_email import CleanedEmail
except ImportError:
    from content_normalizer.normalizer import ContentNormalizer
    from models.raw_email import RawEmail, EmailMetadata
    from models.cleaned_email import CleanedEmail


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_emails"


@pytest.fixture
def korean_signature_samples():
    """Load all Korean signature test fixtures."""
    samples = []
    for i in range(1, 6):
        file_path = FIXTURES_DIR / f"korean_signature_{i}.txt"
        samples.append(file_path.read_text(encoding="utf-8"))
    return samples


@pytest.fixture
def english_signature_samples():
    """Load all English signature test fixtures."""
    samples = []
    for i in range(1, 6):
        file_path = FIXTURES_DIR / f"english_signature_{i}.txt"
        samples.append(file_path.read_text(encoding="utf-8"))
    return samples


@pytest.fixture
def normalizer():
    """Create ContentNormalizer instance for testing."""
    return ContentNormalizer()


def test_detect_korean_signature_sample_1(normalizer, korean_signature_samples):
    """
    T048: Test detection of Korean signature pattern 1.

    Pattern: "감사합니다.\n김철수 드림"
    Expected: Should detect signature at end of email
    """
    email_body = korean_signature_samples[0]

    # Detect signature
    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect Korean signature"
    assert signature_start > 0, "Signature should not start at beginning"
    assert "김철수 드림" in email_body[signature_start:], "Should detect name pattern"


def test_detect_korean_signature_sample_2(normalizer, korean_signature_samples):
    """
    T048: Test detection of Korean signature pattern 2.

    Pattern: "감사드립니다.\n이영희 올림"
    Expected: Should detect signature with different closing (올림)
    """
    email_body = korean_signature_samples[1]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect Korean signature"
    assert "이영희 올림" in email_body[signature_start:], "Should detect 올림 pattern"


def test_detect_korean_signature_sample_3(normalizer, korean_signature_samples):
    """
    T048: Test detection of Korean signature pattern 3.

    Pattern: "좋은 하루 보내세요.\n박민수 드림"
    Expected: Should detect greeting-style signature
    """
    email_body = korean_signature_samples[2]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect greeting signature"
    assert "박민수 드림" in email_body[signature_start:], (
        "Should detect name in greeting"
    )


def test_detect_korean_signature_sample_4(normalizer, korean_signature_samples):
    """
    T048: Test detection of Korean signature pattern 4.

    Pattern: "고맙습니다." (no name)
    Expected: Should detect signature even without name
    """
    email_body = korean_signature_samples[3]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect signature without name"
    assert "고맙습니다" in email_body[signature_start:], "Should detect closing phrase"


def test_detect_korean_signature_sample_5(normalizer, korean_signature_samples):
    """
    T048: Test detection of Korean signature pattern 5.

    Pattern: Contact block with separator line
    Expected: Should detect full contact signature block
    """
    email_body = korean_signature_samples[4]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect contact block signature"
    assert (
        "---" in email_body[signature_start:]
        or "정수진 부장" in email_body[signature_start:]
    ), "Should detect separator or name"


def test_detect_english_signature_sample_1(normalizer, english_signature_samples):
    """
    T049: Test detection of English signature pattern 1.

    Pattern: "Best regards,\nJohn Smith"
    Expected: Should detect formal closing with name
    """
    email_body = english_signature_samples[0]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect English signature"
    assert (
        "Best regards" in email_body[signature_start:]
        or "John Smith" in email_body[signature_start:]
    ), "Should detect closing or name"


def test_detect_english_signature_sample_2(normalizer, english_signature_samples):
    """
    T049: Test detection of English signature pattern 2.

    Pattern: "Sincerely,\nSarah Johnson\nSenior Account Manager"
    Expected: Should detect signature with title
    """
    email_body = english_signature_samples[1]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect signature with title"
    assert (
        "Sincerely" in email_body[signature_start:]
        or "Senior Account Manager" in email_body[signature_start:]
    ), "Should detect closing or title"


def test_detect_english_signature_sample_3(normalizer, english_signature_samples):
    """
    T049: Test detection of English signature pattern 3.

    Pattern: "Thanks,\nEmma"
    Expected: Should detect informal closing
    """
    email_body = english_signature_samples[2]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect informal signature"
    assert (
        "Thanks" in email_body[signature_start:]
        or "Emma" in email_body[signature_start:]
    ), "Should detect closing or name"


def test_detect_english_signature_sample_4(normalizer, english_signature_samples):
    """
    T049: Test detection of English signature pattern 4.

    Pattern: Contact block with separator and full details
    Expected: Should detect full contact signature
    """
    email_body = english_signature_samples[3]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect contact block"
    assert any(
        marker in email_body[signature_start:]
        for marker in ["---", "David Chen", "Product Manager"]
    ), "Should detect separator or contact info"


def test_detect_english_signature_sample_5(normalizer, english_signature_samples):
    """
    T049: Test detection of English signature pattern 5.

    Pattern: Contact block with confidentiality notice
    Expected: Should detect signature with disclaimer
    """
    email_body = english_signature_samples[4]

    signature_start = normalizer.detect_signature(email_body)

    assert signature_start is not None, "Should detect signature with disclaimer"
    assert any(
        marker in email_body[signature_start:]
        for marker in ["Lisa Park", "CONFIDENTIALITY"]
    ), "Should detect name or disclaimer"


def test_remove_signature_preserves_content(normalizer, korean_signature_samples):
    """
    T050: Test that signature removal preserves main email content.

    Given an email with signature, when signature is removed,
    then main content should remain unchanged.
    """
    email_body = korean_signature_samples[0]

    # Expected main content (from korean_signature_1.txt before signature)
    expected_content = "지난주 회의에서 논의한 프로젝트 진행 상황을 공유드립니다"

    # Remove signature
    cleaned_body = normalizer.remove_signature(email_body)

    assert expected_content in cleaned_body, "Should preserve main content"
    assert "김철수 드림" not in cleaned_body, "Should remove signature"
    assert len(cleaned_body) < len(email_body), "Cleaned body should be shorter"


def test_no_signature_no_change(normalizer):
    """
    T051: Test that emails without signatures remain unchanged.

    Given an email with no signature, when processed,
    then content should remain exactly the same.
    """
    email_body = "This is a simple email with no signature.\nJust plain content here."

    # Detect signature (should return None)
    signature_start = normalizer.detect_signature(email_body)

    # Remove signature (should return original)
    cleaned_body = normalizer.remove_signature(email_body)

    assert signature_start is None, "Should not detect signature"
    assert cleaned_body == email_body, "Should not modify content without signature"


def test_signature_detection_boundary_cases(normalizer):
    """
    Additional test: Boundary cases for signature detection.

    Test cases:
    - Very short emails (< 2 lines)
    - Emails with signature-like words in main content
    - Empty emails
    """
    # Very short email
    short_email = "Thanks"
    assert normalizer.detect_signature(short_email) is None, (
        "Should not detect in very short email"
    )

    # Signature-like words in content (not at end)
    content_email = "Thanks for your help yesterday.\n\nI will send the report tomorrow.\n\nMain content here."
    signature_start = normalizer.detect_signature(content_email)
    if signature_start:
        # If detected, should be near the end, not at "Thanks for your help"
        assert signature_start > 30, "Should not detect 'Thanks' in main content"

    # Empty email
    assert normalizer.detect_signature("") is None, "Should handle empty email"
    assert normalizer.remove_signature("") == "", "Should return empty for empty input"


def test_signature_removal_integration(normalizer, english_signature_samples):
    """
    Integration test: Full signature removal workflow.

    Test complete flow from detection to removal with content preservation.
    """
    email_body = english_signature_samples[0]

    # Step 1: Detect
    signature_start = normalizer.detect_signature(email_body)
    assert signature_start is not None, "Should detect signature"

    # Step 2: Remove
    cleaned_body = normalizer.remove_signature(email_body)
    assert len(cleaned_body) < len(email_body), "Should remove content"

    # Step 3: Verify main content preserved
    assert "quarterly report" in cleaned_body, "Should preserve main content"

    # Step 4: Verify signature removed
    assert "Best regards" not in cleaned_body, "Should remove closing"
    assert "John Smith" not in cleaned_body, "Should remove name"
