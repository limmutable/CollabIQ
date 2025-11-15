"""Contract tests for Phase 2c summary generation.

This module validates the summary generation contracts:
- Gemini returns summary_text (string, non-empty)
- Gemini returns summary_word_count (integer, 50-150 range)
- Gemini returns key_entities_preserved (dict with 5 boolean flags)
"""

import pytest
from pydantic import ValidationError
from llm_provider.types import ExtractedEntitiesWithClassification, ConfidenceScores
from datetime import datetime


class TestSummaryGenerationContract:
    """Contract tests for summary generation response schema."""

    def test_summary_text_is_string_and_non_empty(self):
        """Verify collaboration_summary must be a non-empty string."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid summary (non-empty string, ≥50 characters)
        valid_summary = "브레이크앤컴퍼니와 신세계푸드가 2025년 11월 1일 PoC 킥오프 미팅을 진행했습니다. 이번 협업에서는 간편식 제품 라인업 확대를 위한 파일럿 테스트를 계획하고 있습니다."
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_summary=valid_summary,
        )
        assert isinstance(entity.collaboration_summary, str)
        assert len(entity.collaboration_summary) >= 50

        # Empty string should raise ValidationError (min_length=50)
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_summary="",  # Too short
            )

    def test_summary_length_within_50_to_750_characters(self):
        """Verify collaboration_summary must be 50-750 characters."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid length (50-750 characters)
        valid_summary = "브레이크앤컴퍼니와 신세계푸드가 2025년 11월 1일 PoC 킥오프 미팅을 진행했습니다. 이번 협업에서는 간편식 제품 라인업 확대를 위한 파일럿 테스트를 계획하고 있습니다."
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_summary=valid_summary,
        )
        assert 50 <= len(entity.collaboration_summary) <= 750

        # Too short (< 50 characters)
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_summary="짧은 요약",  # 9 characters
            )

        # Too long (> 750 characters)
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                collaboration_summary="브" * 800,  # 800 characters
            )

    def test_summary_word_count_in_50_to_150_range(self):
        """Verify summary_word_count must be integer in range [50, 150]."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid word counts
        for valid_count in [50, 75, 100, 125, 150]:
            entity = ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                summary_word_count=valid_count,
            )
            assert entity.summary_word_count == valid_count
            assert 50 <= entity.summary_word_count <= 150

        # Word count below 50
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                summary_word_count=49,  # < 50
            )

        # Word count above 150
        with pytest.raises(ValidationError):
            ExtractedEntitiesWithClassification(
                person_in_charge="김철수",
                startup_name="본봄",
                partner_org="신세계",
                details="PoC 킥오프",
                date=datetime(2025, 11, 1),
                confidence=confidence,
                email_id="msg_001",
                summary_word_count=151,  # > 150
            )

    def test_key_entities_preserved_is_dict_with_five_boolean_flags(self):
        """Verify key_entities_preserved is dict with 5 boolean flags."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Valid key_entities_preserved dict
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            key_entities_preserved={
                "person_in_charge": True,
                "startup_name": True,
                "partner_org": True,
                "details": True,
                "date": True,
            },
        )
        assert isinstance(entity.key_entities_preserved, dict)
        assert len(entity.key_entities_preserved) == 5
        assert all(isinstance(v, bool) for v in entity.key_entities_preserved.values())

        # Partial preservation (some entities not preserved)
        entity_partial = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_002",
            key_entities_preserved={
                "person_in_charge": False,  # Not preserved
                "startup_name": True,
                "partner_org": True,
                "details": True,
                "date": True,
            },
        )
        assert entity_partial.key_entities_preserved["person_in_charge"] is False
        assert entity_partial.key_entities_preserved["startup_name"] is True

    def test_summary_fields_optional_for_backward_compatibility(self):
        """Verify summary fields are optional (None is acceptable)."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Entity without summary fields (Phase 1b/2b/2c-type-only)
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_summary=None,
            summary_word_count=None,
            key_entities_preserved=None,
        )
        assert entity.collaboration_summary is None
        assert entity.summary_word_count is None
        assert entity.key_entities_preserved is None

    def test_summary_independent_of_type_and_intensity(self):
        """Verify summary can be generated independently of type and intensity."""
        confidence = ConfidenceScores(
            person=0.95, startup=0.92, partner=0.88, details=0.90, date=0.85
        )

        # Summary without type or intensity
        entity = ExtractedEntitiesWithClassification(
            person_in_charge="김철수",
            startup_name="본봄",
            partner_org="신세계",
            details="PoC 킥오프",
            date=datetime(2025, 11, 1),
            confidence=confidence,
            email_id="msg_001",
            collaboration_type=None,
            collaboration_intensity=None,
            collaboration_summary="브레이크앤컴퍼니와 신세계푸드가 2025년 11월 1일 PoC 킥오프 미팅을 진행했습니다. 이번 협업에서는 간편식 제품 라인업 확대를 위한 파일럿 테스트를 계획하고 있습니다.",
            summary_word_count=75,
            key_entities_preserved={
                "person_in_charge": True,
                "startup_name": True,
                "partner_org": True,
                "details": True,
                "date": True,
            },
        )
        assert entity.collaboration_summary is not None
        assert entity.collaboration_type is None
        assert entity.collaboration_intensity is None
