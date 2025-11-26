"""
Unit tests for FieldMapper person matching integration.

Tests the integration of NotionPersonMatcher with FieldMapper to populate
the 담당자 (person in charge) people field in Notion.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from notion_integrator.field_mapper import FieldMapper
from notion_integrator.person_matcher import NotionPersonMatcher
from llm_provider.types import ExtractedEntitiesWithClassification, ConfidenceScores
from models.matching import PersonMatch


class TestFieldMapperPersonMatching:
    """Test FieldMapper integration with person matching."""

    @pytest.fixture
    def mock_schema(self):
        """Mock database schema for FieldMapper initialization."""
        schema = MagicMock()
        schema.database.properties = {
            "협력주체": MagicMock(type="title"),
            "담당자": MagicMock(type="people"),
            "협업내용": MagicMock(type="rich_text"),
            "스타트업명": MagicMock(type="relation"),
            "협업기관": MagicMock(type="relation"),
            "협업형태": MagicMock(type="select"),
            "협업강도": MagicMock(type="select"),
            "날짜": MagicMock(type="date"),
            "Email ID": MagicMock(type="rich_text"),
        }
        return schema

    @pytest.fixture
    def mock_person_matcher(self):
        """Mock PersonMatcher for testing."""
        from unittest.mock import Mock
        matcher = Mock(spec=NotionPersonMatcher)
        # Explicitly configure match as a regular (non-async) mock
        matcher.match = Mock()
        # Ensure match_async doesn't exist so the code uses match()
        delattr(matcher, 'match_async') if hasattr(matcher, 'match_async') else None
        return matcher

    @pytest.fixture
    def extracted_data_with_person(self):
        """Sample extracted data with person_in_charge."""
        return ExtractedEntitiesWithClassification(
            email_id="test_email_123",
            person_in_charge="김철수",
            startup_name="웨이크",
            partner_org="네트워크",
            details="협업 내용",
            date=datetime(2025, 11, 1),
            confidence=ConfidenceScores(
                person=0.95,
                startup=0.92,
                partner=0.88,
                details=0.90,
                date=0.85,
            ),
            collaboration_type="[A]PortCoXSSG",
            collaboration_intensity="협력",
        )

    @pytest.mark.asyncio
    async def test_person_matching_populates_matched_person_id(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: Person matching populates matched_person_id field.

        Given: ExtractedData with person_in_charge
        When: _match_and_populate_person() is called
        Then: matched_person_id is populated with user_id from match result
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )

        # Mock person match result
        mock_person_matcher.match.return_value = PersonMatch(
            user_id="user123" + "0" * 24,
            user_name="김철수",
            similarity_score=1.0,
            match_type="exact",
            confidence_level="high",
            is_ambiguous=False,
            alternative_matches=[],
            match_method="character",
        )

        # Act
        await field_mapper._match_and_populate_person(extracted_data_with_person)

        # Assert
        assert extracted_data_with_person.matched_person_id == "user123" + "0" * 24
        mock_person_matcher.match.assert_called_once_with(
            person_name="김철수",
            similarity_threshold=0.70,
        )

    def test_person_matching_skips_if_no_person_in_charge(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: Person matching skips if person_in_charge is None.

        Given: ExtractedData with person_in_charge = None
        When: _match_and_populate_person() is called
        Then: No matching is performed
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )
        extracted_data_with_person.person_in_charge = None

        # Act
        field_mapper._match_and_populate_person(extracted_data_with_person)

        # Assert
        mock_person_matcher.match.assert_not_called()

    def test_person_matching_skips_if_already_matched(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: Person matching skips if matched_person_id already set.

        Given: ExtractedData with matched_person_id already populated
        When: _match_and_populate_person() is called
        Then: No matching is performed (avoids duplicate work)
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )
        extracted_data_with_person.matched_person_id = "existing_id" + "0" * 20

        # Act
        field_mapper._match_and_populate_person(extracted_data_with_person)

        # Assert
        mock_person_matcher.match.assert_not_called()

    def test_person_no_match_leaves_field_empty(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: No match leaves matched_person_id as None.

        Given: Person matcher returns match_type='none'
        When: _match_and_populate_person() is called
        Then: matched_person_id remains None
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )

        # Mock no match result
        mock_person_matcher.match.return_value = PersonMatch(
            user_id=None,
            user_name="",
            similarity_score=0.65,
            match_type="none",
            confidence_level="none",
            is_ambiguous=False,
            alternative_matches=[],
            match_method="character",
        )

        # Act
        field_mapper._match_and_populate_person(extracted_data_with_person)

        # Assert
        assert extracted_data_with_person.matched_person_id is None

    def test_map_to_notion_properties_formats_people_field(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: map_to_notion_properties() formats matched_person_id as people field.

        Given: ExtractedData with matched_person_id
        When: map_to_notion_properties() is called
        Then: Properties include 담당자 people field with correct format
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )
        extracted_data_with_person.matched_person_id = "user456" + "0" * 24

        # Act
        properties = field_mapper.map_to_notion_properties(extracted_data_with_person)

        # Assert
        assert "담당자" in properties
        assert properties["담당자"] == {"people": [{"id": "user456" + "0" * 24}]}

    def test_map_to_notion_properties_skips_people_field_if_no_match(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: map_to_notion_properties() skips 담당자 field if no match.

        Given: ExtractedData with matched_person_id = None
        When: map_to_notion_properties() is called
        Then: Properties do not include 담당자 field
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )
        extracted_data_with_person.matched_person_id = None

        # Act
        properties = field_mapper.map_to_notion_properties(extracted_data_with_person)

        # Assert
        assert "담당자" not in properties

    @pytest.mark.asyncio
    async def test_async_workflow_calls_person_matching(
        self, mock_schema, mock_person_matcher, extracted_data_with_person
    ):
        """
        Test: map_to_notion_properties_async() calls person matching.

        Given: FieldMapper with person_matcher configured
        When: map_to_notion_properties_async() is called
        Then: _match_and_populate_person() is called
        """
        # Arrange
        field_mapper = FieldMapper(
            schema=mock_schema,
            person_matcher=mock_person_matcher,
        )

        # Mock person match result
        mock_person_matcher.match.return_value = PersonMatch(
            user_id="user789" + "0" * 24,
            user_name="김철수",
            similarity_score=0.95,
            match_type="fuzzy",
            confidence_level="high",
            is_ambiguous=False,
            alternative_matches=[],
            match_method="character",
        )

        # Act
        properties = await field_mapper.map_to_notion_properties_async(
            extracted_data_with_person
        )

        # Assert
        mock_person_matcher.match.assert_called_once()
        assert extracted_data_with_person.matched_person_id == "user789" + "0" * 24
        assert "담당자" in properties
