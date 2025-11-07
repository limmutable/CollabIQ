"""
Unit tests for ContentNormalizer main pipeline.

Tests the three-stage cleaning pipeline integration.
"""

from datetime import datetime

import pytest

try:
    from src.content_normalizer.normalizer import ContentNormalizer
    from src.models.raw_email import RawEmail, EmailMetadata
    from src.models.cleaned_email import CleaningStatus
except ImportError:
    from content_normalizer.normalizer import ContentNormalizer
    from models.raw_email import RawEmail, EmailMetadata
    from models.cleaned_email import CleaningStatus


@pytest.fixture
def normalizer():
    """Create ContentNormalizer instance."""
    return ContentNormalizer()


def test_three_stage_pipeline_all_noise_types(normalizer):
    """
    Test three-stage pipeline removes all noise types in correct order.

    Email contains: disclaimer + quoted thread + signature
    Pipeline should remove in order: disclaimer → quotes → signature
    """
    email_body = """
Project update for Q4.

We're making good progress.

> On Oct 30, John wrote:
> Previous discussion here

Best regards,
Alice

CONFIDENTIALITY NOTICE: This email is confidential.
"""

    result = normalizer.clean(email_body)

    # Should preserve main content
    assert "Project update" in result.cleaned_body
    assert "making good progress" in result.cleaned_body

    # Should remove all noise
    assert "On Oct 30" not in result.cleaned_body
    assert "Best regards" not in result.cleaned_body
    assert "CONFIDENTIALITY" not in result.cleaned_body

    # Should track what was removed
    assert result.removed_content.disclaimer_removed
    assert result.removed_content.quoted_thread_removed
    assert result.removed_content.signature_removed


def test_empty_email_after_cleaning(normalizer):
    """
    Test FR-012: Email that becomes empty after cleaning.

    Given an email with only signature,
    When cleaned,
    Then should return empty with proper tracking.
    """
    email_body = "Best regards,\nJohn Smith"

    result = normalizer.clean(email_body)

    assert result.cleaned_body == "" or result.cleaned_body.strip() == ""
    assert result.removed_content.original_length > 0
    assert result.removed_content.cleaned_length == 0


def test_process_raw_email_integration(normalizer, tmp_path):
    """
    Test process_raw_email creates CleanedEmail properly.
    """
    # Create a RawEmail
    raw_email = RawEmail(
        metadata=EmailMetadata(
            message_id="<test@example.com>",
            sender="sender@example.com",
            subject="Test Subject",
            received_at=datetime(2025, 10, 31, 12, 0, 0),
        ),
        body="Project update.\n\nBest regards,\nJohn",
    )

    # Process it
    cleaned_email = normalizer.process_raw_email(raw_email)

    # Verify CleanedEmail
    assert cleaned_email.original_message_id == "<test@example.com>"
    assert "Project update" in cleaned_email.cleaned_body
    assert "Best regards" not in cleaned_email.cleaned_body
    assert cleaned_email.status == CleaningStatus.SUCCESS
    assert not cleaned_email.is_empty


def test_save_cleaned_email(normalizer, tmp_path):
    """
    Test save_cleaned_email creates proper file structure.
    """
    # Create a CleanedEmail
    from models.cleaned_email import CleanedEmail, RemovedContent

    cleaned_email = CleanedEmail(
        original_message_id="<test@example.com>",
        cleaned_body="Test content",
        removed_content=RemovedContent(
            original_length=100,
            cleaned_length=12,
            signature_removed=True,
            quoted_thread_removed=False,
            disclaimer_removed=False,
        ),
        processed_at=datetime(2025, 10, 31, 14, 30, 0),
        status=CleaningStatus.SUCCESS,
        is_empty=False,
    )

    # Save it
    file_path = normalizer.save_cleaned_email(cleaned_email, base_dir=tmp_path)

    # Verify file structure: YYYY/MM/YYYYMMDD_HHMMSS_message_id.json
    assert file_path.exists()
    assert file_path.parent.name == "10"  # October
    assert file_path.parent.parent.name == "2025"
    assert "20251031_143000" in file_path.name
    assert "test_at_example.com" in file_path.name

    # Verify JSON content
    import json

    saved_data = json.loads(file_path.read_text())
    assert saved_data["original_message_id"] == "<test@example.com>"
    assert saved_data["cleaned_body"] == "Test content"
