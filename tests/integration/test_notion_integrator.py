"""
Integration Tests for NotionIntegrator

Tests the high-level NotionIntegrator API:
- Initialization with configuration
- Schema discovery
- Data fetching
- LLM formatting
- get_data orchestration
- Cache refresh

These tests use mocked NotionClient to avoid real API calls.
"""

import pytest
from unittest.mock import AsyncMock, patch

from notion_integrator.integrator import NotionIntegrator
from notion_integrator.models import DatabaseSchema, LLMFormattedData


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_notion_api_response():
    """Mock Notion API response for database."""
    return {
        "object": "database",
        "id": "test-db-id",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "title": [{"type": "text", "text": {"content": "Test DB"}}],
        "url": "https://www.notion.so/workspace/test-db",
        "data_sources": [{"id": "test-ds-id", "type": "database_source"}],
    }


@pytest.fixture
def mock_notion_data_source_response():
    """
    Mock Notion API response for data source retrieval.

    Simulates the response structure from Notion's data_sources.retrieve endpoint.
    """
    return {
        "object": "data_source",
        "id": "test-ds-id",
        "properties": {
            "Name": {
                "id": "title",
                "name": "Name",
                "type": "title",
                "title": {},
            },
            "Shinsegae affiliates?": {
                "id": "ssg",
                "name": "Shinsegae affiliates?",
                "type": "checkbox",
                "checkbox": {},
            },
            "Is Portfolio?": {
                "id": "portfolio",
                "name": "Is Portfolio?",
                "type": "checkbox",
                "checkbox": {},
            },
        },
    }


@pytest.fixture
def mock_query_response():
    """Mock query response with records."""
    return {
        "object": "list",
        "results": [
            {
                "object": "page",
                "id": "page-1",
                "created_time": "2025-01-01T00:00:00.000Z",
                "last_edited_time": "2025-11-01T00:00:00.000Z",
                "url": "https://notion.so/page-1",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [
                            {"type": "text", "text": {"content": "Test Company"}}
                        ],
                    },
                    "Shinsegae affiliates?": {
                        "type": "checkbox",
                        "checkbox": True,
                    },
                    "Is Portfolio?": {
                        "type": "checkbox",
                        "checkbox": False,
                    },
                },
            }
        ],
        "next_cursor": None,
        "has_more": False,
    }


# ==============================================================================
# Initialization Tests
# ==============================================================================


def test_integrator_initialization():
    """Test NotionIntegrator initialization."""
    with patch("notion_integrator.integrator.NotionClient"):
        integrator = NotionIntegrator(
            api_key="test-key",
            rate_per_second=3.0,
            use_cache=True,
            default_max_depth=1,
        )

        assert integrator.use_cache is True
        assert integrator.default_max_depth == 1


def test_integrator_initialization_env_var():
    """Test initialization with environment variable."""
    with (
        patch("notion_integrator.integrator.NotionClient"),
        patch.dict("os.environ", {"NOTION_API_KEY": "env-key"}),
    ):
        NotionIntegrator()
        # Should not raise - uses env var


# ==============================================================================
# Schema Discovery Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_discover_database_schema(mock_notion_api_response, mock_notion_data_source_response):
    """Test schema discovery through integrator."""
    with patch("notion_integrator.integrator.NotionClient") as MockClient:
        # Setup mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.retrieve_database = AsyncMock(
            return_value=mock_notion_api_response
        )
        mock_client_instance.retrieve_data_source = AsyncMock(
            return_value=mock_notion_data_source_response
        )

        # Create integrator
        integrator = NotionIntegrator(api_key="test-key", use_cache=False)

        # Discover schema
        schema = await integrator.discover_database_schema(database_id="test-db-id")

        # Verify
        assert isinstance(schema, DatabaseSchema)
        assert schema.database.id == "test-db-id"
        assert schema.database.title == "Test DB"


# ==============================================================================
# Data Fetching Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_fetch_all_records(mock_notion_api_response, mock_query_response, mock_notion_data_source_response):
    """Test fetching all records through integrator."""
    with patch("notion_integrator.integrator.NotionClient") as MockClient:
        # Setup mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.retrieve_database = AsyncMock(
            return_value=mock_notion_api_response
        )
        mock_client_instance.query_database = AsyncMock(
            return_value=mock_query_response
        )
        mock_client_instance.retrieve_data_source = AsyncMock(
            return_value=mock_notion_data_source_response
        )

        # Create integrator
        integrator = NotionIntegrator(api_key="test-key", use_cache=False)

        # Fetch records
        records = await integrator.fetch_all_records(database_id="test-db-id")

        # Verify
        assert len(records) == 1
        assert records[0]["id"] == "page-1"


# ==============================================================================
# LLM Formatting Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_format_for_llm(mock_notion_api_response, mock_query_response, mock_notion_data_source_response):
    """Test LLM formatting through integrator."""
    with patch("notion_integrator.integrator.NotionClient") as MockClient:
        # Setup mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.retrieve_database = AsyncMock(
            return_value=mock_notion_api_response
        )
        mock_client_instance.query_database = AsyncMock(
            return_value=mock_query_response
        )
        mock_client_instance.retrieve_data_source = AsyncMock(
            return_value=mock_notion_data_source_response
        )

        # Create integrator
        integrator = NotionIntegrator(api_key="test-key", use_cache=False)

        # Format for LLM
        formatted = await integrator.format_for_llm(database_id="test-db-id")

        # Verify
        assert isinstance(formatted, LLMFormattedData)
        assert formatted.metadata.total_companies == 1
        assert len(formatted.companies) == 1
        assert len(formatted.summary_markdown) > 0


# ==============================================================================
# get_data Orchestration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_data_single_database(mock_notion_api_response, mock_query_response, mock_notion_data_source_response):
    """Test get_data with single database."""
    with patch("notion_integrator.integrator.NotionClient") as MockClient:
        # Setup mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.retrieve_database = AsyncMock(
            return_value=mock_notion_api_response
        )
        mock_client_instance.query_database = AsyncMock(
            return_value=mock_query_response
        )
        mock_client_instance.retrieve_data_source = AsyncMock(
            return_value=mock_notion_data_source_response
        )

        # Create integrator
        integrator = NotionIntegrator(api_key="test-key", use_cache=False)

        # Get data
        data = await integrator.get_data(companies_db_id="test-db-id")

        # Verify
        assert isinstance(data, LLMFormattedData)
        assert data.metadata.total_companies == 1
        assert data.metadata.shinsegae_affiliate_count == 1
        assert data.metadata.portfolio_company_count == 0


# ==============================================================================
# Cache Management Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_refresh_cache(mock_notion_api_response, mock_notion_data_source_response):
    """Test cache refresh."""
    with patch("notion_integrator.integrator.NotionClient") as MockClient:
        # Setup mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.retrieve_database = AsyncMock(
            return_value=mock_notion_api_response
        )
        mock_client_instance.retrieve_data_source = AsyncMock(
            return_value=mock_notion_data_source_response
        )

        # Create integrator
        integrator = NotionIntegrator(api_key="test-key", use_cache=True)

        # Refresh cache
        await integrator.refresh_cache(database_id="test-db-id")

        # Should not raise - cache invalidated


# ==============================================================================
# Context Manager Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_integrator_as_context_manager(mock_notion_api_response, mock_notion_data_source_response):
    """Test NotionIntegrator as async context manager."""
    with patch("notion_integrator.integrator.NotionClient") as MockClient:
        # Setup mock client
        mock_client_instance = MockClient.return_value
        mock_client_instance.retrieve_database = AsyncMock(
            return_value=mock_notion_api_response
        )
        mock_client_instance.retrieve_data_source = AsyncMock(
            return_value=mock_notion_data_source_response
        )
        mock_client_instance.close = AsyncMock()

        # Use as context manager
        async with NotionIntegrator(api_key="test-key", use_cache=False) as integrator:
            schema = await integrator.discover_database_schema(database_id="test-db-id")
            assert isinstance(schema, DatabaseSchema)

        # Verify close was called
        mock_client_instance.close.assert_called_once()
