"""Shared test fixtures for contract and integration tests.

Provides valid ExtractedEntitiesWithClassification instances that match
all Pydantic validation requirements.
"""

from llm_provider.types import ExtractedEntitiesWithClassification, ConfidenceScores
from datetime import datetime


def create_valid_extracted_data(**overrides) -> ExtractedEntitiesWithClassification:
    """Create a valid ExtractedEntitiesWithClassification instance for testing.

    Args:
        **overrides: Optional field overrides

    Returns:
        ExtractedEntitiesWithClassification with all required fields
    """
    default_data = {
        "email_id": "msg_001_test",
        "person_in_charge": "김철수",
        "startup_name": "브레이크앤컴퍼니",
        "partner_org": "신세계푸드",
        "details": "브레이크앤컴퍼니와 신세계푸드 간의 협력 관련 세부 내용입니다.",
        "date": datetime(2025, 10, 28),
        "confidence": ConfidenceScores(
            person=0.95,
            startup=0.92,
            partner=0.88,
            details=0.90,
            date=0.85,
        ),
        # Phase 2b fields - Notion page IDs must be 32 characters minimum
        "matched_company_id": "abc123def456ghi789jkl012mno345pq",  # 32 chars
        "matched_partner_id": "stu901vwx234yz056abc123def456ghi",  # 32 chars
        "matched_person_id": "user456789abc012def345ghi678jkl90",  # 32 chars (Notion user UUID)
        "startup_match_confidence": 0.93,
        "partner_match_confidence": 0.91,
        # Phase 2c classification fields
        "collaboration_type": "[A]PortCoXSSG",
        "type_confidence": 0.95,
        "collaboration_intensity": "협력",
        "intensity_confidence": 0.90,
        "intensity_reasoning": "Email indicates collaborative partnership between companies",
        # Phase 2c summary fields - must be 50+ chars and 50+ words
        "collaboration_summary": (
            "브레이크앤컴퍼니와 신세계푸드가 협력 관계를 맺었습니다. "
            "주요 내용은 제품 개발과 유통입니다. 김철수 담당자가 이 협력을 주도하고 있습니다. "
            "양사는 2025년 10월 28일부터 협력을 시작했습니다. "
            "이번 협력은 스타트업 생태계에 긍정적인 영향을 미칠 것으로 예상됩니다."
        ),
        "summary_word_count": 52,
        "key_entities_preserved": {
            "startup": True,
            "partner": True,
            "person": True,
            "details": True,
            "date": True,
        },
        "classification_timestamp": "2025-10-28T10:30:00Z",
    }

    # Apply overrides
    default_data.update(overrides)

    # If person_in_charge is explicitly set to None, matched_person_id should also be None
    if "person_in_charge" in overrides and overrides["person_in_charge"] is None:
        default_data["matched_person_id"] = None

    return ExtractedEntitiesWithClassification(**default_data)
