"""Integration test for end-to-end Notion write workflow.

Tests the complete pipeline: extract → classify → write → verify Notion entry.

TDD: This test is written FIRST and should FAIL before implementation.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from notion_integrator import NotionWriter, NotionIntegrator
from llm_provider.types import ExtractedEntitiesWithClassification, WriteResult
from tests.fixtures import create_valid_extracted_data


class TestNotionWriteE2E:
    """Integration test for end-to-end Notion write workflow."""

    @pytest.fixture
    def sample_email_path(self):
        """Path to sample-001.txt test fixture."""
        return Path("tests/fixtures/emails/sample-001.txt")

    @pytest.fixture
    def sample_extracted_json_path(self):
        """Path to extracted entities JSON for sample-001.txt."""
        return Path("data/extractions/sample-001_entities.json")

    @pytest.fixture
    def mock_notion_integrator(self):
        """Create a mock NotionIntegrator with schema."""
        mock = Mock(spec=NotionIntegrator)

        # Mock schema discovery
        mock_schema = Mock()
        mock_schema.properties = {
            "협력주체": {"type": "title", "id": "title"},
            "담당자": {"type": "rich_text", "id": "담당자_id"},
            "스타트업명": {"type": "relation", "id": "스타트업명_id"},
            "협업기관": {"type": "relation", "id": "협업기관_id"},
            "협업내용": {"type": "rich_text", "id": "협업내용_id"},
            "날짜": {"type": "date", "id": "날짜_id"},
            "협업형태": {"type": "select", "id": "협업형태_id"},
            "협업강도": {"type": "select", "id": "협업강도_id"},
            "요약": {"type": "rich_text", "id": "요약_id"},
            "type_confidence": {"type": "number", "id": "type_conf_id"},
            "intensity_confidence": {"type": "number", "id": "intensity_conf_id"},
            "email_id": {"type": "rich_text", "id": "email_id"},
            "classification_timestamp": {"type": "date", "id": "class_time_id"},
        }
        mock.discover_database_schema = AsyncMock(return_value=mock_schema)

        # Mock Notion API client
        mock.notion_client = Mock()

        return mock

    @pytest.fixture
    def sample_extracted_data(self):
        """Sample extracted and classified data for integration test."""
        return create_valid_extracted_data(email_id="sample-001")

    @pytest.mark.asyncio
    async def test_e2e_write_workflow_success(
        self, mock_notion_integrator, sample_extracted_data
    ):
        """T020: Test complete E2E workflow from extraction to Notion entry creation.

        Workflow:
        1. Load extracted entities with classification (from Phase 2c output)
        2. Initialize NotionWriter with database schema
        3. Call create_collabiq_entry()
        4. Verify WriteResult indicates success
        5. Verify all fields were mapped correctly
        6. Verify Korean text preserved
        7. Verify relation fields linked to company IDs
        8. Verify auto-generated 협력주체 field

        This test verifies the COMPLETE user journey for User Story 1.
        """
        # Mock successful Notion API response
        created_page_id = "notion-created-page-id-success"
        mock_response = {
            "id": created_page_id,
            "object": "page",
            "created_time": "2025-10-28T10:35:00.000Z",
            "properties": {
                "협력주체": {
                    "id": "title",
                    "type": "title",
                    "title": [{"text": {"content": "브레이크앤컴퍼니-신세계푸드"}}]
                },
                "담당자": {
                    "id": "담당자_id",
                    "type": "rich_text",
                    "rich_text": [{"text": {"content": "김철수"}}]
                },
                "협업형태": {
                    "id": "협업형태_id",
                    "type": "select",
                    "select": {"name": "[A]PortCoXSSG"}
                },
            }
        }

        mock_notion_integrator.notion_client.pages.create = AsyncMock(
            return_value=mock_response
        )

        # Step 1: Initialize NotionWriter
        writer = NotionWriter(
            notion_integrator=mock_notion_integrator,
            collabiq_db_id="test-collabiq-db-id"
        )

        # Step 2: Execute write operation (this WILL FAIL until implementation exists)
        result = await writer.create_collabiq_entry(sample_extracted_data)

        # Step 3: Verify WriteResult
        assert isinstance(result, WriteResult), \
            "E2E workflow must return WriteResult"
        assert result.success is True, \
            "E2E workflow must succeed for valid data"
        assert result.page_id == created_page_id, \
            "WriteResult must contain created page ID"
        assert result.email_id == "sample-001", \
            "WriteResult must preserve email_id for tracking"
        assert result.retry_count == 0, \
            "First attempt should succeed with 0 retries"
        assert result.is_duplicate is False, \
            "New entry should not be marked as duplicate"
        assert result.error_type is None, \
            "Successful write should have no error_type"
        assert result.error_message is None, \
            "Successful write should have no error_message"

        # Step 4: Verify Notion API was called with correct payload
        mock_notion_integrator.notion_client.pages.create.assert_called_once()
        call_args = mock_notion_integrator.notion_client.pages.create.call_args

        # Verify database_id parameter
        assert call_args.kwargs["parent"]["database_id"] == "test-collabiq-db-id", \
            "Must write to correct CollabIQ database"

        # Verify properties payload
        properties = call_args.kwargs["properties"]

        # Verify 협력주체 (title field - auto-generated)
        assert "협력주체" in properties, \
            "협력주체 title field must be present"
        assert properties["협력주체"]["title"][0]["text"]["content"] == "브레이크앤컴퍼니-신세계푸드", \
            "협력주체 must be auto-generated as '{startup}-{partner}'"

        # Verify 담당자 (rich_text field - Korean text)
        assert "담당자" in properties, \
            "담당자 field must be present"
        assert properties["담당자"]["rich_text"][0]["text"]["content"] == "김철수", \
            "Korean text must be preserved without encoding errors"

        # Verify 스타트업명 (relation field - matched company ID)
        assert "스타트업명" in properties, \
            "스타트업명 relation field must be present"
        assert properties["스타트업명"]["relation"][0]["id"] == "abc123def456ghi789jkl012mno345pq", \
            "스타트업명 must link to matched startup company ID"

        # Verify 협업기관 (relation field - matched company ID)
        assert "협업기관" in properties, \
            "협업기관 relation field must be present"
        assert properties["협업기관"]["relation"][0]["id"] == "stu901vwx234yz056abc123def456ghi", \
            "협업기관 must link to matched partner company ID"

        # Verify 협업형태 (select field - classification result)
        assert "협업형태" in properties, \
            "협업형태 select field must be present"
        assert properties["협업형태"]["select"]["name"] == "[A]PortCoXSSG", \
            "협업형태 must match classification result"

        # Verify 협업강도 (select field - classification result)
        assert "협업강도" in properties, \
            "협업강도 select field must be present"
        assert properties["협업강도"]["select"]["name"] == "협력", \
            "협업강도 must match classification intensity"

        # Verify 요약 (rich_text field - Korean summary)
        assert "요약" in properties, \
            "요약 field must be present"
        summary_text = properties["요약"]["rich_text"][0]["text"]["content"]
        assert "브레이크앤컴퍼니" in summary_text, \
            "요약 must preserve Korean startup name"
        assert "신세계푸드" in summary_text, \
            "요약 must preserve Korean partner name"

        # Verify type_confidence (number field)
        assert "type_confidence" in properties, \
            "type_confidence field must be present"
        assert properties["type_confidence"]["number"] == 0.95, \
            "type_confidence must match classification confidence score"

        # Verify 날짜 (date field - ISO 8601 date only)
        assert "날짜" in properties, \
            "날짜 date field must be present"
        assert properties["날짜"]["date"]["start"] == "2025-10-28", \
            "날짜 must be in YYYY-MM-DD format (no time)"

    @pytest.mark.asyncio
    async def test_e2e_write_workflow_with_retry_on_failure(
        self, mock_notion_integrator, sample_extracted_data
    ):
        """Test E2E workflow handles transient failures with retry.

        Workflow:
        1. First API call fails (rate limit or timeout)
        2. System retries automatically
        3. Second attempt succeeds
        4. WriteResult reflects retry_count=1
        """
        from notion_client.errors import APIResponseError

        # Mock API to fail once, then succeed
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                raise APIResponseError(
                    response=Mock(status_code=429),
                    message="Rate limited",
                    code="rate_limited"
                )
            else:
                # Second call succeeds
                return {
                    "id": "notion-page-retry-success",
                    "object": "page",
                    "properties": {}
                }

        mock_notion_integrator.notion_client.pages.create = AsyncMock(
            side_effect=side_effect
        )

        # Execute write operation
        writer = NotionWriter(
            notion_integrator=mock_notion_integrator,
            collabiq_db_id="test-collabiq-db-id"
        )
        result = await writer.create_collabiq_entry(sample_extracted_data)

        # Verify retry succeeded
        assert result.success is True, \
            "E2E workflow must eventually succeed after retry"
        assert result.page_id == "notion-page-retry-success", \
            "WriteResult must contain page ID from successful retry"
        assert result.retry_count == 1, \
            "WriteResult must reflect 1 retry attempt"
        assert result.error_type is None, \
            "Successful retry should clear error_type"

    @pytest.mark.asyncio
    async def test_all_notion_property_types_formatted_correctly(
        self, mock_notion_integrator
    ):
        """T047: Test that all Notion property types are formatted correctly.

        Property Types Tested:
        - title: 협력주체 (auto-generated)
        - rich_text: 담당자, 협업내용, 요약, email_id
        - relation: 스타트업명, 협업기관
        - select: 협업형태, 협업강도
        - date: 날짜, classification_timestamp
        - number: type_confidence, intensity_confidence

        This test verifies ALL field mappings work together in one complete write.
        """
        # Create data with ALL fields populated
        data = create_valid_extracted_data(
            email_id="complete-fields-test",
            startup_name="완전한스타트업",
            partner_org="완전한파트너",
            person_in_charge="김완전",
            details="완전한 협업 내용 설명",
            collaboration_summary="완전한스타트업과 완전한파트너의 투자 협력 관계가 성사되었습니다. 김완전 담당자가 주도하고 있습니다.",  # 50+ chars
            matched_company_id="co123456789012345678901234567890",  # 33 chars (valid UUID length)
            matched_partner_id="pa123456789012345678901234567890",  # 33 chars (valid UUID length)
            collaboration_type="[A]완전한협업",
            collaboration_intensity="투자",
            date="2025-10-29",
            type_confidence=0.98,
            intensity_confidence=0.97,
            classification_timestamp="2025-10-29T12:00:00Z",
        )

        # Mock successful Notion API response
        mock_notion_integrator.notion_client.pages.create = AsyncMock(
            return_value={"id": "all-fields-page-id", "object": "page", "properties": {}}
        )

        # Execute write
        writer = NotionWriter(
            notion_integrator=mock_notion_integrator,
            collabiq_db_id="test-db-id"
        )
        result = await writer.create_collabiq_entry(data)

        # Verify success
        assert result.success is True
        assert result.page_id == "all-fields-page-id"

        # Extract properties from API call
        properties = mock_notion_integrator.notion_client.pages.create.call_args.kwargs["properties"]

        # Verify title field
        assert properties["협력주체"]["title"][0]["text"]["content"] == "완전한스타트업-완전한파트너"

        # Verify rich_text fields
        assert properties["담당자"]["rich_text"][0]["text"]["content"] == "김완전"
        assert properties["협업내용"]["rich_text"][0]["text"]["content"] == "완전한 협업 내용 설명"
        assert properties["요약"]["rich_text"][0]["text"]["content"] == "완전한스타트업과 완전한파트너의 투자 협력 관계가 성사되었습니다. 김완전 담당자가 주도하고 있습니다."
        assert properties["email_id"]["rich_text"][0]["text"]["content"] == "complete-fields-test"

        # Verify relation fields
        assert properties["스타트업명"]["relation"][0]["id"] == "co123456789012345678901234567890"
        assert properties["협업기관"]["relation"][0]["id"] == "pa123456789012345678901234567890"

        # Verify select fields
        assert properties["협업형태"]["select"]["name"] == "[A]완전한협업"
        assert properties["협업강도"]["select"]["name"] == "투자"

        # Verify date fields (YYYY-MM-DD format)
        assert properties["날짜"]["date"]["start"] == "2025-10-29"
        assert properties["classification_timestamp"]["date"]["start"] == "2025-10-29"

        # Verify number fields
        assert properties["type_confidence"]["number"] == 0.98
        assert properties["intensity_confidence"]["number"] == 0.97

    @pytest.mark.asyncio
    async def test_graceful_degradation_missing_optional_fields(
        self, mock_notion_integrator
    ):
        """T048: Test graceful degradation when optional fields are missing.

        Scenario:
        - Missing relation IDs (no company match found)
        - Missing person_in_charge
        - Missing collaboration_summary
        - Entry should still be created successfully
        - Only required fields + available optional fields are included
        """
        # Create data with missing optional fields
        data = create_valid_extracted_data(
            email_id="missing-optionals-test",
            person_in_charge=None,  # Missing
            collaboration_summary=None,  # Missing
            matched_company_id=None,  # Company matching failed
            matched_partner_id=None,  # Partner matching failed
            date=None,  # Missing
        )

        # Mock successful Notion API response
        mock_notion_integrator.notion_client.pages.create = AsyncMock(
            return_value={"id": "partial-fields-page-id", "object": "page", "properties": {}}
        )

        # Execute write
        writer = NotionWriter(
            notion_integrator=mock_notion_integrator,
            collabiq_db_id="test-db-id"
        )
        result = await writer.create_collabiq_entry(data)

        # Verify success despite missing optionals
        assert result.success is True, \
            "Entry creation should succeed even with missing optional fields"
        assert result.page_id == "partial-fields-page-id"

        # Extract properties from API call
        properties = mock_notion_integrator.notion_client.pages.create.call_args.kwargs["properties"]

        # Required fields should be present
        assert "협력주체" in properties, "Title field is required"
        assert "email_id" in properties, "email_id is required"
        assert "협업내용" in properties, "details is required"
        assert "협업형태" in properties, "collaboration_type is required"
        assert "협업강도" in properties, "collaboration_intensity is required"

        # Missing optional fields should be omitted
        assert "담당자" not in properties, "person_in_charge should be omitted when None"
        assert "요약" not in properties, "collaboration_summary should be omitted when None"
        assert "스타트업명" not in properties, "matched_company_id should be omitted when None"
        assert "협업기관" not in properties, "matched_partner_id should be omitted when None"
        assert "날짜" not in properties, "date should be omitted when None"
