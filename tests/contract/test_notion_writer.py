"""Contract tests for NotionWriter class.

Tests verify the API contract (method signatures, return types, error handling)
without requiring actual Notion API calls.

TDD: These tests are written FIRST and should FAIL before implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Optional

from notion_integrator import NotionWriter
from llm_provider.types import WriteResult, ExtractedEntitiesWithClassification
from tests.fixtures import create_valid_extracted_data


class TestNotionWriterContract:
    """Contract tests for NotionWriter.create_collabiq_entry() method."""

    @pytest.fixture
    def mock_notion_integrator(self):
        """Create a mock NotionIntegrator instance."""
        mock = Mock()
        mock.notion_client = Mock()

        # Mock schema discovery (async)
        mock_schema = Mock()
        mock_schema.properties = {
            "협력주체": {"type": "title"},
            "담당자": {"type": "rich_text"},
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
        mock.discover_database_schema = AsyncMock(return_value=mock_schema)

        return mock

    @pytest.fixture
    def notion_writer(self, mock_notion_integrator):
        """Create NotionWriter instance with mock dependencies."""
        return NotionWriter(
            notion_integrator=mock_notion_integrator, collabiq_db_id="test-db-id-123"
        )

    @pytest.fixture
    def sample_extracted_data(self):
        """Sample ExtractedEntitiesWithClassification for testing."""
        return create_valid_extracted_data()

    def test_create_collabiq_entry_method_signature(
        self, notion_writer, sample_extracted_data
    ):
        """T011: Verify create_collabiq_entry() method exists with correct signature.

        Contract:
        - Method name: create_collabiq_entry
        - Parameter: extracted_data (ExtractedEntitiesWithClassification)
        - Returns: WriteResult
        - Async: Yes (coroutine)
        """
        # Verify method exists
        assert hasattr(notion_writer, "create_collabiq_entry"), (
            "NotionWriter must have create_collabiq_entry method"
        )

        # Verify method is callable
        method = getattr(notion_writer, "create_collabiq_entry")
        assert callable(method), "create_collabiq_entry must be callable"

        # Verify method is async (coroutine)
        import inspect

        assert inspect.iscoroutinefunction(method), (
            "create_collabiq_entry must be an async method (coroutine)"
        )

    @pytest.mark.asyncio
    async def test_create_collabiq_entry_success_case(
        self, notion_writer, sample_extracted_data, mock_notion_integrator
    ):
        """T012: Verify create_collabiq_entry() returns WriteResult on success.

        Contract:
        - Returns WriteResult with success=True
        - Includes page_id from Notion API response
        - Includes email_id for tracking
        - retry_count should be 0 for successful first attempt
        - is_duplicate should be False for new entry
        """
        # Mock successful Notion API response
        mock_response = {
            "id": "notion-page-created-id-789",
            "object": "page",
            "properties": {},
        }
        mock_notion_integrator.notion_client.pages.create = AsyncMock(
            return_value=mock_response
        )

        # Execute method (this WILL FAIL until implementation exists)
        result = await notion_writer.create_collabiq_entry(sample_extracted_data)

        # Verify contract
        assert isinstance(result, WriteResult), (
            "create_collabiq_entry must return WriteResult instance"
        )
        assert result.success is True, (
            "WriteResult.success must be True for successful creation"
        )
        assert result.page_id == "notion-page-created-id-789", (
            "WriteResult.page_id must match Notion API response ID"
        )
        assert result.email_id == "msg_001_test", (
            "WriteResult.email_id must match input email_id"
        )
        assert result.retry_count == 0, (
            "WriteResult.retry_count must be 0 for first successful attempt"
        )
        assert result.is_duplicate is False, (
            "WriteResult.is_duplicate must be False for new entry"
        )
        assert result.error_type is None, (
            "WriteResult.error_type must be None on success"
        )
        assert result.error_message is None, (
            "WriteResult.error_message must be None on success"
        )

    @pytest.mark.asyncio
    async def test_create_collabiq_entry_error_case(
        self, notion_writer, sample_extracted_data, mock_notion_integrator
    ):
        """T013: Verify create_collabiq_entry() returns WriteResult on error.

        Contract:
        - Returns WriteResult with success=False
        - Includes error_type (exception class name)
        - Includes error_message (human-readable description)
        - Includes status_code if HTTP error
        - retry_count reflects number of attempts made
        - page_id should be None on failure
        """
        # Mock Notion API error response
        from notion_client.errors import APIResponseError

        # Create a properly structured mock error
        mock_response = Mock()
        mock_response.status_code = 400

        mock_error = APIResponseError(
            response=mock_response,
            message="Invalid property value",
            code="validation_error",
        )
        # Ensure attributes are accessible
        mock_error.response = mock_response
        mock_error.message = "Invalid property value"
        mock_error.code = "validation_error"

        mock_notion_integrator.notion_client.pages.create = AsyncMock(
            side_effect=mock_error
        )

        # Execute method (this WILL FAIL until implementation exists)
        result = await notion_writer.create_collabiq_entry(sample_extracted_data)

        # Verify contract
        assert isinstance(result, WriteResult), (
            "create_collabiq_entry must return WriteResult even on error"
        )
        assert result.success is False, (
            "WriteResult.success must be False when API call fails"
        )
        assert result.page_id is None, "WriteResult.page_id must be None on failure"
        assert result.email_id == "msg_001_test", (
            "WriteResult.email_id must match input email_id even on error"
        )
        assert result.error_type == "APIResponseError", (
            "WriteResult.error_type must be exception class name"
        )
        assert result.error_message is not None, (
            "WriteResult.error_message must contain error description"
        )
        assert "Invalid property value" in result.error_message, (
            "WriteResult.error_message must include API error message"
        )
        assert result.status_code == 400, (
            "WriteResult.status_code must match HTTP status code"
        )
        assert result.retry_count > 0, (
            "WriteResult.retry_count must reflect retry attempts"
        )
        assert result.is_duplicate is False, (
            "WriteResult.is_duplicate must be False (error != duplicate)"
        )

    @pytest.mark.asyncio
    async def test_check_duplicate_method_signature(self, notion_writer):
        """T032: Verify check_duplicate() method exists with correct signature.

        Contract:
        - Method name: check_duplicate
        - Parameter: email_id (str)
        - Returns: Optional[str] (existing page_id or None)
        - Async: Yes (coroutine)
        """
        # Verify method exists
        assert hasattr(notion_writer, "check_duplicate"), (
            "NotionWriter must have check_duplicate method"
        )

        # Verify method is callable
        method = getattr(notion_writer, "check_duplicate")
        assert callable(method), "check_duplicate must be callable"

        # Verify method is async (coroutine)
        import inspect

        assert inspect.iscoroutinefunction(method), (
            "check_duplicate must be an async method (coroutine)"
        )

    @pytest.mark.asyncio
    async def test_check_duplicate_when_duplicate_exists(
        self, notion_writer, mock_notion_integrator
    ):
        """T033: Verify check_duplicate() returns existing page_id when duplicate found.

        Contract:
        - Returns existing page_id (str) when email_id matches
        - Queries Notion database by email_id field
        - Returns first matching result
        """
        # Mock query response with existing entry
        mock_notion_integrator.notion_client.databases.query = AsyncMock(
            return_value={
                "results": [
                    {
                        "id": "existing-page-id-abc123",
                        "properties": {
                            "email_id": {
                                "rich_text": [{"text": {"content": "test-email-001"}}]
                            }
                        },
                    }
                ]
            }
        )

        result = await notion_writer.check_duplicate("test-email-001")

        assert isinstance(result, str), (
            "check_duplicate must return str when duplicate exists"
        )
        assert result == "existing-page-id-abc123", (
            "check_duplicate must return existing page_id"
        )

        # Verify query was called with correct filter
        mock_notion_integrator.notion_client.databases.query.assert_called_once()
        call_kwargs = (
            mock_notion_integrator.notion_client.databases.query.call_args.kwargs
        )
        assert "database_id" in call_kwargs
        assert "filter" in call_kwargs

    @pytest.mark.asyncio
    async def test_check_duplicate_when_no_duplicate(
        self, notion_writer, mock_notion_integrator
    ):
        """T034: Verify check_duplicate() returns None when no duplicate found.

        Contract:
        - Returns None when no matching email_id found
        - Handles empty results gracefully
        """
        # Mock query response with no results
        mock_notion_integrator.notion_client.databases.query = AsyncMock(
            return_value={"results": []}
        )

        result = await notion_writer.check_duplicate("non-existent-email")

        assert result is None, (
            "check_duplicate must return None when no duplicate exists"
        )
