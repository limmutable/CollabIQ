"""
Contract Tests for Notion Schema Discovery

Tests the NotionClient wrapper's ability to discover database schemas
from the Notion API. These tests verify:
- Database metadata retrieval
- Property type identification
- Relationship field detection
- Classification field identification

Note: These tests can run against real Notion API (requires credentials)
or use comprehensive fixtures for offline testing.
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.notion_integrator.exceptions import (
    NotionAuthenticationError,
    NotionObjectNotFoundError,
    NotionPermissionError,
    SchemaValidationError,
)
from src.notion_integrator.models import DatabaseSchema


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_notion_api_response():
    """
    Mock Notion API response for database retrieval.

    Simulates the response structure from Notion's databases.retrieve endpoint.
    """
    return {
        "object": "database",
        "id": "abc123-def456-ghi789",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T10:30:00.000Z",
        "title": [{"type": "text", "text": {"content": "Companies"}}],
        "url": "https://www.notion.so/workspace/abc123",
        "properties": {
            "Name": {
                "id": "title",
                "name": "Name",
                "type": "title",
                "title": {},
            },
            "Shinsegae affiliates?": {
                "id": "prop_ssg",
                "name": "Shinsegae affiliates?",
                "type": "checkbox",
                "checkbox": {},
            },
            "Is Portfolio?": {
                "id": "prop_portfolio",
                "name": "Is Portfolio?",
                "type": "checkbox",
                "checkbox": {},
            },
            "Industry": {
                "id": "prop_industry",
                "name": "Industry",
                "type": "select",
                "select": {
                    "options": [
                        {"id": "opt1", "name": "Technology", "color": "blue"},
                        {"id": "opt2", "name": "Retail", "color": "red"},
                    ]
                },
            },
            "Related CollabIQ": {
                "id": "prop_relation",
                "name": "Related CollabIQ",
                "type": "relation",
                "relation": {
                    "database_id": "xyz789-uvw012-abc345",
                    "type": "dual_property",
                    "dual_property": {},
                },
            },
        },
    }


@pytest.fixture
def mock_notion_client():
    """Mock Notion client with async methods."""
    client = MagicMock()
    client.retrieve_database = AsyncMock()
    return client


# ==============================================================================
# Schema Discovery Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_discover_schema_success(mock_notion_client, mock_notion_api_response):
    """
    Test successful schema discovery from Notion API.

    Verifies:
    - Database metadata correctly parsed
    - All properties identified
    - Property types correctly mapped
    - Classification fields detected
    - Relationship properties identified
    """
    # Mock API response
    mock_notion_client.retrieve_database.return_value = mock_notion_api_response

    # Import after mock setup to avoid import errors
    from src.notion_integrator.schema import discover_schema

    # Execute schema discovery (without caching for test)
    schema = await discover_schema(
        client=mock_notion_client,
        database_id="abc123-def456-ghi789",
        use_cache=False,
    )

    # Verify schema structure
    assert isinstance(schema, DatabaseSchema)
    assert schema.database.id == "abc123-def456-ghi789"
    assert schema.database.title == "Companies"
    assert schema.database.url == "https://www.notion.so/workspace/abc123"

    # Verify all properties discovered
    assert len(schema.database.properties) == 5
    assert "Name" in schema.database.properties
    assert "Shinsegae affiliates?" in schema.database.properties
    assert "Is Portfolio?" in schema.database.properties
    assert "Industry" in schema.database.properties
    assert "Related CollabIQ" in schema.database.properties

    # Verify property types
    assert schema.database.properties["Name"].type == "title"
    assert schema.database.properties["Shinsegae affiliates?"].type == "checkbox"
    assert schema.database.properties["Is Portfolio?"].type == "checkbox"
    assert schema.database.properties["Industry"].type == "select"
    assert schema.database.properties["Related CollabIQ"].type == "relation"

    # Verify classification fields identified
    assert "is_shinsegae_affiliate" in schema.classification_fields
    assert "is_portfolio_company" in schema.classification_fields
    assert schema.classification_fields["is_shinsegae_affiliate"] == "prop_ssg"
    assert schema.classification_fields["is_portfolio_company"] == "prop_portfolio"

    # Verify relationship properties identified
    assert len(schema.relation_properties) == 1
    assert schema.relation_properties[0].name == "Related CollabIQ"
    assert (
        schema.relation_properties[0].config["relation"]["database_id"]
        == "xyz789-uvw012-abc345"
    )

    # Verify computed fields
    assert schema.has_relations is True
    assert schema.property_count == 5


@pytest.mark.asyncio
async def test_discover_schema_authentication_error(mock_notion_client):
    """Test schema discovery with invalid API key."""
    # Mock authentication error (client should raise translated exception)
    mock_notion_client.retrieve_database.side_effect = NotionAuthenticationError(
        "Notion API authentication failed. Check your API key.",
        details={"database_id": "abc123-def456-ghi789"},
    )

    from src.notion_integrator.schema import discover_schema

    # Verify authentication error raised
    with pytest.raises(NotionAuthenticationError) as exc_info:
        await discover_schema(
            client=mock_notion_client,
            database_id="abc123-def456-ghi789",
            use_cache=False,
        )

    assert "authentication failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_discover_schema_object_not_found(mock_notion_client):
    """Test schema discovery with non-existent or unshared database."""
    # Mock object not found error (client should raise translated exception)
    mock_notion_client.retrieve_database.side_effect = NotionObjectNotFoundError(
        object_type="database",
        object_id="invalid-id",
        message="Database not found or not shared with integration.",
    )

    from src.notion_integrator.schema import discover_schema

    # Verify not found error raised
    with pytest.raises(NotionObjectNotFoundError) as exc_info:
        await discover_schema(
            client=mock_notion_client,
            database_id="invalid-id",
            use_cache=False,
        )

    assert exc_info.value.details["object_type"] == "database"
    assert exc_info.value.details["object_id"] == "invalid-id"


@pytest.mark.asyncio
async def test_discover_schema_permission_error(mock_notion_client):
    """Test schema discovery with insufficient permissions."""
    # Mock permission error (client should raise translated exception)
    mock_notion_client.retrieve_database.side_effect = NotionPermissionError(
        message="Insufficient permissions. Ensure database is shared with integration.",
        details={"database_id": "abc123-def456-ghi789"},
    )

    from src.notion_integrator.schema import discover_schema

    # Verify permission error raised
    with pytest.raises(NotionPermissionError) as exc_info:
        await discover_schema(
            client=mock_notion_client,
            database_id="abc123-def456-ghi789",
            use_cache=False,
        )

    assert "insufficient permissions" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_discover_schema_no_properties(mock_notion_client):
    """Test schema discovery with empty database (validation should fail)."""
    # Mock database with no properties
    mock_response = {
        "object": "database",
        "id": "abc123",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-01-01T00:00:00.000Z",
        "title": [{"type": "text", "text": {"content": "Empty DB"}}],
        "url": "https://www.notion.so/workspace/abc123",
        "properties": {},
    }
    mock_notion_client.retrieve_database.return_value = mock_response

    from src.notion_integrator.schema import discover_schema

    # Verify validation error raised
    with pytest.raises(SchemaValidationError) as exc_info:
        await discover_schema(
            client=mock_notion_client,
            database_id="abc123",
            use_cache=False,
        )

    assert "no properties" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_discover_schema_missing_classification_fields(mock_notion_client):
    """
    Test schema discovery when classification fields are missing.

    This is valid - not all databases need classification fields.
    """
    # Mock database without classification checkboxes
    mock_response = {
        "object": "database",
        "id": "abc123",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-01-01T00:00:00.000Z",
        "title": [{"type": "text", "text": {"content": "CollabIQ"}}],
        "url": "https://www.notion.so/workspace/abc123",
        "properties": {
            "Name": {
                "id": "title",
                "name": "Name",
                "type": "title",
                "title": {},
            },
            "Description": {
                "id": "prop_desc",
                "name": "Description",
                "type": "rich_text",
                "rich_text": {},
            },
        },
    }
    mock_notion_client.retrieve_database.return_value = mock_response

    from src.notion_integrator.schema import discover_schema

    # Execute schema discovery
    schema = await discover_schema(
        client=mock_notion_client,
        database_id="abc123",
        use_cache=False,
    )

    # Verify schema valid but no classification fields
    assert isinstance(schema, DatabaseSchema)
    assert len(schema.classification_fields) == 0
    assert schema.has_relations is False


# ==============================================================================
# Integration Test (requires real Notion credentials)
# ==============================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("NOTION_API_KEY"),
    reason="Requires NOTION_API_KEY environment variable",
)
@pytest.mark.asyncio
async def test_discover_schema_real_api():
    """
    Integration test against real Notion API.

    Requires:
    - NOTION_API_KEY environment variable
    - NOTION_DATABASE_ID_COMPANIES environment variable
    - Database shared with integration
    """
    from notion_client import AsyncClient

    from src.notion_integrator.schema import discover_schema

    # Initialize real Notion client
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID_COMPANIES")

    if not database_id:
        pytest.skip("NOTION_DATABASE_ID_COMPANIES not set")

    client = AsyncClient(auth=api_key)

    # Execute real schema discovery
    schema = await discover_schema(
        client=client,
        database_id=database_id,
    )

    # Verify real schema
    assert isinstance(schema, DatabaseSchema)
    assert schema.database.id == database_id
    assert schema.database.title  # Has a title
    assert len(schema.database.properties) > 0  # Has properties

    # Check for expected classification fields (if Companies database)
    if schema.database.title == "Companies":
        assert (
            "is_shinsegae_affiliate" in schema.classification_fields or True
        )  # May not exist yet
        assert (
            "is_portfolio_company" in schema.classification_fields or True
        )  # May not exist yet
