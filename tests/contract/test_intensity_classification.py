"""Contract tests for Phase 2c intensity classification.

This module validates the intensity classification contracts:
- Gemini returns intensity in exactly ["이해", "협력", "투자", "인수"]
- intensity_confidence in range [0.0, 1.0]
- intensity_reasoning provided (1-2 sentence explanation)
"""

import pytest
from pydantic import ValidationError
from llm_provider.types import ExtractedEntitiesWithClassification, ConfidenceScores
from datetime import datetime


class TestIntensityClassificationContract:
    """Contract tests for intensity classification response schema."""

    def test_intensity_values_limited_to_four_korean_levels(self):
        """Verify intensity must be one of 4 Korean values."""
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
                collaboration_intensity="협업",  # Invalid - not one of 4
            )

    def test_intensity_confidence_range_validation(self):
        """Verify intensity_confidence must be in range [0.0, 1.0]."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid confidence scores
        for valid_conf in [0.0, 0.5, 0.85, 0.95, 1.0]:
            entity = ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                intensity_confidence=valid_conf,
            )
            assert entity.intensity_confidence == valid_conf

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
                intensity_confidence=1.5,  # > 1.0
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
                intensity_confidence=-0.1,  # < 0.0
            )

    def test_intensity_reasoning_optional_string(self):
        """Verify intensity_reasoning is an optional string field."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # With reasoning
        entity_with_reasoning = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_intensity="협력",
            intensity_reasoning="PoC 킥오프와 파일럿 테스트 계획을 논의하여 협력 단계로 분류",
        )
        assert entity_with_reasoning.intensity_reasoning is not None
        assert len(entity_with_reasoning.intensity_reasoning) > 0

        # Without reasoning (None is acceptable)
        entity_without_reasoning = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_intensity="협력",
            intensity_reasoning=None,
        )
        assert entity_without_reasoning.intensity_reasoning is None

    def test_intensity_classification_independent_of_type(self):
        """Verify intensity can be set independently of type classification."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Intensity without type
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_type=None,  # No type classification
            collaboration_intensity="협력",  # But has intensity
            intensity_confidence=0.88,
        )
        assert entity.collaboration_type is None
        assert entity.collaboration_intensity == "협력"
        assert entity.intensity_confidence == 0.88

    def test_needs_manual_review_considers_intensity_confidence(self):
        """Verify needs_manual_review() checks intensity_confidence."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # High intensity confidence (≥0.85) - no manual review
        entity_high = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_intensity="협력",
            intensity_confidence=0.90,
        )
        assert entity_high.needs_manual_review() is False

        # Low intensity confidence (<0.85) - needs manual review
        entity_low = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_intensity="협력",
            intensity_confidence=0.75,
        )
        assert entity_low.needs_manual_review() is True
