"""Contract tests for Phase 2c classification models.

This module validates the Pydantic model contracts:
- ExtractedEntitiesWithClassification extends ExtractedEntities
- All Phase 2c fields are optional (backward compatibility)
- Validation rules for type/intensity formats
- needs_manual_review() method behavior
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.llm_provider.types import (
    ExtractedEntities,
    ExtractedEntitiesWithClassification,
    ConfidenceScores,
)


class TestExtractedEntitiesWithClassification:
    """Contract tests for ExtractedEntitiesWithClassification model."""

    def test_extends_extracted_entities(self):
        """Verify ExtractedEntitiesWithClassification inherits from ExtractedEntities."""
        assert issubclass(ExtractedEntitiesWithClassification, ExtractedEntities)

    def test_all_phase2c_fields_optional(self):
        """Verify all Phase 2c fields are optional for backward compatibility."""
        # Should be able to create instance with only Phase 1b fields
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
        )

        # All Phase 2c fields should be None
        assert entity.collaboration_type is None
        assert entity.collaboration_intensity is None
        assert entity.type_confidence is None
        assert entity.intensity_confidence is None
        assert entity.collaboration_summary is None
        assert entity.summary_word_count is None
        assert entity.key_entities_preserved is None
        assert entity.classification_timestamp is None

    def test_collaboration_type_format_validation(self):
        """Verify collaboration_type must follow [X]* pattern."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid formats
        for valid_type in [
            "[A]PortCoXSSG",
            "[B]Non-PortCoXSSG",
            "[C]PortCoXPortCo",
            "[D]Other",
            "[1]NewType",
        ]:
            entity = ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_type=valid_type,
            )
            assert entity.collaboration_type == valid_type

        # Invalid format should raise ValidationError
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_type="InvalidFormat",  # Missing [X] prefix
            )

    def test_collaboration_intensity_validation(self):
        """Verify collaboration_intensity must be one of 4 Korean values."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid intensities
        for valid_intensity in ["이해", "협력", "투자", "인수"]:
            entity = ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_intensity=valid_intensity,
            )
            assert entity.collaboration_intensity == valid_intensity

        # Invalid intensity should raise ValidationError
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_intensity="Invalid",  # Not one of 4 valid values
            )

    def test_confidence_score_range_validation(self):
        """Verify type_confidence and intensity_confidence must be 0.0-1.0."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid confidence scores
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            type_confidence=0.95,
            intensity_confidence=0.88,
        )
        assert entity.type_confidence == 0.95
        assert entity.intensity_confidence == 0.88

        # Invalid confidence scores should raise ValidationError
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                type_confidence=1.5,  # > 1.0
            )

    def test_needs_manual_review_method(self):
        """Verify needs_manual_review() returns True for low confidence."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # High confidence (≥0.85) - no manual review needed
        entity_high = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            type_confidence=0.95,
            intensity_confidence=0.90,
        )
        assert entity_high.needs_manual_review() is False

        # Low type confidence (<0.85) - needs manual review
        entity_low_type = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            type_confidence=0.75,  # <0.85
            intensity_confidence=0.90,
        )
        assert entity_low_type.needs_manual_review() is True

        # Low intensity confidence (<0.85) - needs manual review
        entity_low_intensity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            type_confidence=0.95,
            intensity_confidence=0.70,  # <0.85
        )
        assert entity_low_intensity.needs_manual_review() is True

    def test_summary_word_count_validation(self):
        """Verify summary_word_count must be in range 50-150."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid word count
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            summary_word_count=100,
        )
        assert entity.summary_word_count == 100

        # Invalid word counts should raise ValidationError
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                summary_word_count=30,  # <50
            )

        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                summary_word_count=200,  # >150
            )
