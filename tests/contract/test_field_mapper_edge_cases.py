"""Contract tests for FieldMapper edge case handling.

Tests verify field mapping behavior for null fields, text truncation,
invalid relation IDs, and Korean text with special characters.

TDD: These tests are written FIRST and should FAIL before implementation.
"""

import pytest
from unittest.mock import Mock

from notion_integrator.field_mapper import FieldMapper
from tests.fixtures import create_valid_extracted_data


class TestFieldMapperEdgeCases:
    """Contract tests for FieldMapper edge case handling."""

    @pytest.fixture
    def mock_schema(self):
        """Create a mock database schema."""
        # Create property mocks with both dict access and attribute access
        properties = {}
        property_defs = {
            "협력주체": {"type": "title"},
            "담당자": {"type": "people"},
            "스타트업명": {"type": "relation"},
            "협업기관": {"type": "relation"},
            "협업내용": {"type": "rich_text"},
            "날짜": {"type": "date"},
            "협업형태": {"type": "select"},
            "협업강도": {"type": "select"},
            "요약": {"type": "rich_text"},
            "type_confidence": {"type": "number"},
            "intensity_confidence": {"type": "number"},
            "email_id": {"type": "rich_text"},
            "classification_timestamp": {"type": "date"},
        }

        for name, prop_def in property_defs.items():
            prop_mock = Mock()
            prop_mock.type = prop_def["type"]
            prop_mock.get = lambda key, default=None, d=prop_def: d.get(key, default)
            properties[name] = prop_mock

        # Create schema mock with database.properties structure
        schema_mock = Mock()
        database_mock = Mock()
        database_mock.properties = properties
        schema_mock.database = database_mock

        return schema_mock

    @pytest.fixture
    def field_mapper(self, mock_schema):
        """Create FieldMapper instance with mock schema."""
        return FieldMapper(mock_schema)

    def test_null_field_handling(self, field_mapper):
        """T043: Test that null/None fields are omitted from output.

        Contract:
        - Fields with None values are NOT included in properties dict
        - Required fields (협력주체, email_id) are still present
        - Optional fields (person_in_charge, details, etc.) are omitted when None
        """
        # Create data with several null fields
        data = create_valid_extracted_data(
            person_in_charge=None,  # Optional field
            details=None,  # Optional field
            collaboration_summary=None,  # Optional field
            matched_company_id=None,  # Optional relation
            matched_partner_id=None,  # Optional relation
            collaboration_type=None,  # Optional select
            collaboration_intensity=None,  # Optional select
            date=None,  # Optional date
            type_confidence=None,  # Optional number
            intensity_confidence=None,  # Optional number
        )

        properties = field_mapper.map_to_notion_properties(data)

        # Required fields should always be present
        assert "협력주체" in properties, "Title field must be present"
        assert "Email ID" in properties, "Email ID must be present"

        # Optional null fields should be omitted
        assert "담당자" not in properties, "person_in_charge (None) should be omitted"
        assert "협업내용" not in properties, "details (None) should be omitted"
        assert "요약" not in properties, (
            "collaboration_summary (None) should be omitted"
        )
        assert "스타트업명" not in properties, (
            "matched_company_id (None) should be omitted"
        )
        assert "협업기관" not in properties, (
            "matched_partner_id (None) should be omitted"
        )
        assert "협업형태" not in properties, (
            "collaboration_type (None) should be omitted"
        )
        assert "협업강도" not in properties, (
            "collaboration_intensity (None) should be omitted"
        )
        assert "날짜" not in properties, "date (None) should be omitted"
        assert "type_confidence" not in properties, (
            "type_confidence (None) should be omitted"
        )
        assert "intensity_confidence" not in properties, (
            "intensity_confidence (None) should be omitted"
        )

    def test_text_truncation(self, field_mapper):
        """T044: Test that long text fields are truncated to 2000 characters.

        Contract:
        - Text exactly at 2000 chars is preserved as-is
        - Text longer than 2000 chars would be truncated (prevented by Pydantic)
        - Korean/UTF-8 characters are handled correctly

        Note: Pydantic model has max_length=2000 for details field, so we test
        that FieldMapper correctly handles max-length text without errors.
        """
        # Create text at exactly 2000 characters (Pydantic's max for details)
        long_text = "가" * 2000  # Korean character repeated 2000 times
        # For summary, use 750 chars (Pydantic's max for collaboration_summary)
        long_summary = "나" * 750

        data = create_valid_extracted_data(
            details=long_text,
            collaboration_summary=long_summary,
        )

        properties = field_mapper.map_to_notion_properties(data)

        # Check details field is preserved at full length
        details_content = properties["협업내용"]["rich_text"][0]["text"]["content"]
        assert len(details_content) <= 2000, "details field must not exceed 2000 chars"
        assert details_content == long_text, (
            "Text at 2000 chars should be preserved exactly"
        )

        # Check summary field is preserved at full length
        summary_content = properties["요약"]["rich_text"][0]["text"]["content"]
        assert len(summary_content) <= 2000, (
            "summary field must not exceed 2000 chars (Notion limit)"
        )
        assert summary_content == long_summary, (
            "Text within limits should be preserved exactly"
        )

    def test_invalid_relation_id_handling(self, field_mapper):
        """T045: Test that None relation IDs are omitted gracefully.

        Contract:
        - None relation IDs are omitted from properties dict
        - No error is raised when relation ID is None
        - Invalid IDs (wrong length) are prevented by Pydantic validation (earlier in pipeline)

        Note: Pydantic model has min_length=32 validation, so invalid IDs
        never reach FieldMapper. This test verifies handling of None values.
        """
        # Test None relation ID (valid scenario - no match found)
        data = create_valid_extracted_data(
            matched_company_id=None,
            matched_partner_id=None,
        )

        properties = field_mapper.map_to_notion_properties(data)

        # None IDs should be omitted
        assert "스타트업명" not in properties, (
            "None matched_company_id should be omitted"
        )
        assert "협업기관" not in properties, "None matched_partner_id should be omitted"

        # Other fields should still be present
        assert "협력주체" in properties, "Title field should still be present"
        assert "Email ID" in properties, "Email ID should still be present"

    def test_valid_relation_id_formats(self, field_mapper):
        """T045b: Test that valid relation ID formats are accepted.

        Contract:
        - 32-char UUIDs (no hyphens) are valid
        - 36-char UUIDs (with hyphens) are valid
        """
        # Test valid UUID formats
        valid_ids = [
            "12345678901234567890123456789012",  # 32 chars (no hyphens)
            "12345678-1234-1234-1234-123456789012",  # 36 chars (with hyphens)
        ]

        for valid_id in valid_ids:
            data = create_valid_extracted_data(matched_company_id=valid_id)

            properties = field_mapper.map_to_notion_properties(data)

            assert "스타트업명" in properties, (
                f"Valid relation ID '{valid_id}' should be included"
            )
            assert properties["스타트업명"]["relation"][0]["id"] == valid_id, (
                "Relation ID should match input"
            )

    def test_korean_text_with_special_characters(self, field_mapper):
        """T046: Test Korean text with emojis and special characters.

        Contract:
        - Korean characters (한글) are preserved
        - Emojis (🚀, 🎉, etc.) are preserved
        - Special punctuation (¿, ¡, etc.) is preserved
        - Mixed content (Korean + emoji + English) is preserved
        - No encoding errors or corruption
        """
        # Create text with various special characters
        special_text = "한글 텍스트 🚀 with emojis 🎉 and punctuation: ¿¡…—·•"
        # Long summary to meet 50+ char requirement
        special_summary = (
            "한글 텍스트 🚀 with emojis 🎉 and special punctuation marks: ¿¡…—·• "
            "브레이크앤컴퍼니와 신세계푸드의 협력 관계를 설명하는 요약입니다. "
            "이 요약은 특수문자와 이모지를 포함하고 있습니다."
        )

        data = create_valid_extracted_data(
            details=special_text,
            collaboration_summary=special_summary,
            person_in_charge="김철수 🧑‍💼",
            matched_person_id="12345678-1234-5678-1234-567812345678"
        )

        properties = field_mapper.map_to_notion_properties(data)

        # Verify special characters are preserved
        details_content = properties["협업내용"]["rich_text"][0]["text"]["content"]
        assert details_content == special_text, (
            "Korean text with special characters must be preserved exactly"
        )

        summary_content = properties["요약"]["rich_text"][0]["text"]["content"]
        assert summary_content == special_summary, (
            "Korean text in summary must be preserved exactly"
        )

        person_content_id = properties["담당자"]["people"][0]["id"]
        assert person_content_id == "12345678-1234-5678-1234-567812345678", (
            "Person ID must be preserved exactly"
        )
