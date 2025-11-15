"""Unit tests for confidence scoring.

Tests cover:
- Confidence score validation (0.0-1.0 range)
- Missing entities have confidence 0.0
- has_low_confidence method
- Pydantic model validation
"""

import pytest
from pydantic import ValidationError

from llm_provider.types import ConfidenceScores, ExtractedEntities


def test_confidence_scores_valid_range():
    """Test that confidence scores accept values in 0.0-1.0 range."""
    scores = ConfidenceScores(
        person=0.95,
        startup=0.92,
        partner=0.88,
        details=0.90,
        date=0.85,
    )
    assert 0.0 <= scores.person <= 1.0
    assert 0.0 <= scores.startup <= 1.0
    assert 0.0 <= scores.partner <= 1.0
    assert 0.0 <= scores.details <= 1.0
    assert 0.0 <= scores.date <= 1.0


def test_confidence_scores_reject_negative():
    """Test that confidence scores reject negative values."""
    with pytest.raises(ValidationError):
        ConfidenceScores(
            person=-0.1,
            startup=0.92,
            partner=0.88,
            details=0.90,
            date=0.85,
        )


def test_confidence_scores_reject_above_one():
    """Test that confidence scores reject values above 1.0."""
    with pytest.raises(ValidationError):
        ConfidenceScores(
            person=1.5,
            startup=0.92,
            partner=0.88,
            details=0.90,
            date=0.85,
        )


def test_confidence_scores_accept_zero():
    """Test that confidence scores accept 0.0 (for missing entities)."""
    scores = ConfidenceScores(
        person=0.0,  # Missing entity
        startup=0.95,
        partner=0.0,  # Missing entity
        details=0.90,
        date=0.0,  # Missing entity
    )
    assert scores.person == 0.0
    assert scores.partner == 0.0
    assert scores.date == 0.0


def test_confidence_scores_accept_one():
    """Test that confidence scores accept 1.0 (perfect confidence)."""
    scores = ConfidenceScores(
        person=1.0,
        startup=1.0,
        partner=1.0,
        details=1.0,
        date=1.0,
    )
    assert scores.person == 1.0


def test_has_low_confidence_default_threshold():
    """Test has_low_confidence with default threshold (0.85)."""
    # All scores above threshold
    scores_high = ConfidenceScores(
        person=0.95,
        startup=0.92,
        partner=0.88,
        details=0.90,
        date=0.85,
    )
    assert not scores_high.has_low_confidence()

    # One score below threshold
    scores_low = ConfidenceScores(
        person=0.95,
        startup=0.92,
        partner=0.80,  # Below 0.85
        details=0.90,
        date=0.85,
    )
    assert scores_low.has_low_confidence()


def test_has_low_confidence_custom_threshold():
    """Test has_low_confidence with custom threshold."""
    scores = ConfidenceScores(
        person=0.75,
        startup=0.80,
        partner=0.70,
        details=0.78,
        date=0.85,
    )

    # All scores above 0.70
    assert not scores.has_low_confidence(threshold=0.70)

    # Some scores below 0.80
    assert scores.has_low_confidence(threshold=0.80)


def test_has_low_confidence_with_missing_entities():
    """Test has_low_confidence with missing entities (confidence 0.0)."""
    scores = ConfidenceScores(
        person=0.0,  # Missing
        startup=0.95,
        partner=0.90,
        details=0.88,
        date=0.85,
    )

    # Should flag as low confidence due to person=0.0
    assert scores.has_low_confidence()


def test_extracted_entities_missing_fields_zero_confidence():
    """Test that missing entity fields should have confidence 0.0."""
    entities = ExtractedEntities(
        person_in_charge=None,  # Missing
        startup_name="TableManager",
        partner_org=None,  # Missing
        details="collaboration discussion",
        date=None,  # Missing
        confidence=ConfidenceScores(
            person=0.0,  # Must be 0.0 for missing
            startup=0.95,
            partner=0.0,  # Must be 0.0 for missing
            details=0.88,
            date=0.0,  # Must be 0.0 for missing
        ),
        email_id="test_001",
    )

    # Verify missing fields have None value
    assert entities.person_in_charge is None
    assert entities.partner_org is None
    assert entities.date is None

    # Verify missing fields have 0.0 confidence
    assert entities.confidence.person == 0.0
    assert entities.confidence.partner == 0.0
    assert entities.confidence.date == 0.0


def test_extracted_entities_confidence_validation():
    """Test that ExtractedEntities validates confidence scores."""
    # Valid confidence scores
    entities = ExtractedEntities(
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
        email_id="test_002",
    )
    assert entities.confidence.person == 0.95

    # Invalid confidence scores (should raise ValidationError)
    with pytest.raises(ValidationError):
        ExtractedEntities(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계인터내셔널",
            details="파일럿 킥오프",
            date=None,
            confidence=ConfidenceScores(
                person=1.5,  # Invalid: above 1.0
                startup=0.92,
                partner=0.88,
                details=0.90,
                date=0.0,
            ),
            email_id="test_003",
        )


def test_confidence_scores_boundary_values():
    """Test confidence scores at boundary values (0.0, 0.5, 1.0)."""
    scores = ConfidenceScores(
        person=0.0,  # Minimum
        startup=0.5,  # Middle
        partner=1.0,  # Maximum
        details=0.999,  # Near maximum
        date=0.001,  # Near minimum
    )
    assert scores.person == 0.0
    assert scores.startup == 0.5
    assert scores.partner == 1.0
    assert scores.details == 0.999
    assert scores.date == 0.001
