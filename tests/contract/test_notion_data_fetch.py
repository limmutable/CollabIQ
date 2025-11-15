"""
Contract Tests for Notion Data Fetching

Tests the data fetching operations with pagination and relationship resolution:
- Query database with pagination
- Handle multiple pages of results
- Resolve relationships between databases
- Handle circular references
- Depth limiting for relationships
- Error handling during fetch operations

These tests use mocked NotionClient to verify contract without API calls.
"""

import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

from notion_integrator.exceptions import (
    NotionAuthenticationError,
    NotionObjectNotFoundError,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_notion_client():
    """Mock NotionClient for testing."""
    client = MagicMock()
    client.query_database = AsyncMock()
    client.retrieve_database = AsyncMock()
    client.retrieve_page = AsyncMock()
    return client


@pytest.fixture
def mock_companies_page_1() -> Dict[str, Any]:
    """Mock first page of companies query response."""
    return {
        "object": "list",
        "results": [
            {
                "object": "page",
                "id": "company-1",
                "created_time": "2025-01-01T00:00:00.000Z",
                "last_edited_time": "2025-11-01T00:00:00.000Z",
                "properties": {
                    "Name": {
                        "id": "title",
                        "type": "title",
                        "title": [{"type": "text", "text": {"content": "Acme Corp"}}],
                    },
                    "Founded Year": {"id": "year", "type": "number", "number": 2010},
                    "Shinsegae affiliates?": {
                        "id": "ssg",
                        "type": "checkbox",
                        "checkbox": True,
                    },
                    "Is Portfolio?": {
                        "id": "portfolio",
                        "type": "checkbox",
                        "checkbox": False,
                    },
                    "Related CollabIQ": {
                        "id": "rel1",
                        "type": "relation",
                        "relation": [{"id": "collabiq-1"}],
                    },
                },
            },
            {
                "object": "page",
                "id": "company-2",
                "created_time": "2025-01-02T00:00:00.000Z",
                "last_edited_time": "2025-11-02T00:00:00.000Z",
                "properties": {
                    "Name": {
                        "id": "title",
                        "type": "title",
                        "title": [{"type": "text", "text": {"content": "Beta Inc"}}],
                    },
                    "Founded Year": {"id": "year", "type": "number", "number": 2015},
                    "Shinsegae affiliates?": {
                        "id": "ssg",
                        "type": "checkbox",
                        "checkbox": False,
                    },
                    "Is Portfolio?": {
                        "id": "portfolio",
                        "type": "checkbox",
                        "checkbox": True,
                    },
                    "Related CollabIQ": {
                        "id": "rel1",
                        "type": "relation",
                        "relation": [{"id": "collabiq-2"}],
                    },
                },
            },
        ],
        "next_cursor": "cursor-page-2",
        "has_more": True,
    }


@pytest.fixture
def mock_companies_page_2() -> Dict[str, Any]:
    """Mock second page of companies query response."""
    return {
        "object": "list",
        "results": [
            {
                "object": "page",
                "id": "company-3",
                "created_time": "2025-01-03T00:00:00.000Z",
                "last_edited_time": "2025-11-03T00:00:00.000Z",
                "properties": {
                    "Name": {
                        "id": "title",
                        "type": "title",
                        "title": [{"type": "text", "text": {"content": "Gamma Ltd"}}],
                    },
                    "Founded Year": {"id": "year", "type": "number", "number": 2020},
                    "Shinsegae affiliates?": {
                        "id": "ssg",
                        "type": "checkbox",
                        "checkbox": True,
                    },
                    "Is Portfolio?": {
                        "id": "portfolio",
                        "type": "checkbox",
                        "checkbox": True,
                    },
                    "Related CollabIQ": {
                        "id": "rel1",
                        "type": "relation",
                        "relation": [],
                    },
                },
            },
        ],
        "next_cursor": None,
        "has_more": False,
    }


@pytest.fixture
def mock_collabiq_page() -> Dict[str, Any]:
    """Mock CollabIQ page response."""
    return {
        "object": "page",
        "id": "collabiq-1",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "CollabIQ Record 1"}}],
            },
            "Description": {
                "id": "desc",
                "type": "rich_text",
                "rich_text": [
                    {"type": "text", "text": {"content": "First CollabIQ record"}}
                ],
            },
        },
    }


# ==============================================================================
# Pagination Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_fetch_all_records_with_pagination(
    mock_notion_client, mock_companies_page_1, mock_companies_page_2
):
    """Test fetching all records with pagination handling."""
    from notion_integrator.fetcher import fetch_all_records

    # Setup mock to return two pages
    mock_notion_client.query_database.side_effect = [
        mock_companies_page_1,
        mock_companies_page_2,
    ]

    # Fetch all records
    records = await fetch_all_records(
        client=mock_notion_client,
        database_id="companies-db-id",
    )

    # Verify pagination handled correctly
    assert len(records) == 3
    assert records[0]["id"] == "company-1"
    assert records[1]["id"] == "company-2"
    assert records[2]["id"] == "company-3"

    # Verify query_database called twice
    assert mock_notion_client.query_database.call_count == 2

    # First call without cursor
    first_call = mock_notion_client.query_database.call_args_list[0]
    assert first_call.kwargs["database_id"] == "companies-db-id"
    assert first_call.kwargs.get("start_cursor") is None

    # Second call with cursor
    second_call = mock_notion_client.query_database.call_args_list[1]
    assert second_call.kwargs["start_cursor"] == "cursor-page-2"


@pytest.mark.asyncio
async def test_fetch_all_records_single_page(mock_notion_client, mock_companies_page_2):
    """Test fetching records when only one page exists."""
    from notion_integrator.fetcher import fetch_all_records

    # Setup mock to return single page
    mock_notion_client.query_database.return_value = mock_companies_page_2

    # Fetch all records
    records = await fetch_all_records(
        client=mock_notion_client,
        database_id="companies-db-id",
    )

    # Verify single page handled correctly
    assert len(records) == 1
    assert records[0]["id"] == "company-3"

    # Verify query_database called once
    assert mock_notion_client.query_database.call_count == 1


@pytest.mark.asyncio
async def test_fetch_all_records_empty_database(mock_notion_client):
    """Test fetching from empty database."""
    from notion_integrator.fetcher import fetch_all_records

    # Setup mock to return empty results
    mock_notion_client.query_database.return_value = {
        "object": "list",
        "results": [],
        "next_cursor": None,
        "has_more": False,
    }

    # Fetch all records
    records = await fetch_all_records(
        client=mock_notion_client,
        database_id="empty-db-id",
    )

    # Verify empty list returned
    assert len(records) == 0
    assert mock_notion_client.query_database.call_count == 1


# ==============================================================================
# Relationship Resolution Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_resolve_relationships_simple(
    mock_notion_client, mock_companies_page_1, mock_collabiq_page
):
    """Test resolving simple one-level relationships."""
    from notion_integrator.fetcher import resolve_relationships
    from notion_integrator.schema import create_database_schema
    from notion_integrator.models import NotionDatabase, NotionProperty

    # Create schema with relation property
    companies_db = NotionDatabase(
        id="companies-db-id",
        title="Companies",
        url="https://notion.so/companies",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Related CollabIQ": NotionProperty(
                id="rel1",
                name="Related CollabIQ",
                type="relation",
                config={
                    "relation": {
                        "database_id": "collabiq-db-id",
                        "type": "dual_property",
                    }
                },
            ),
        },
    )
    schema = create_database_schema(companies_db)

    # Setup mock to return related page
    mock_notion_client.retrieve_page.return_value = mock_collabiq_page

    # Get record from page 1
    record = mock_companies_page_1["results"][0]

    # Resolve relationships
    resolved_record = await resolve_relationships(
        client=mock_notion_client,
        record=record,
        schema=schema,
        max_depth=1,
    )

    # Verify relationship resolved
    assert "Related CollabIQ" in resolved_record["properties"]
    relation_data = resolved_record["properties"]["Related CollabIQ"]
    assert relation_data["type"] == "relation"
    assert len(relation_data["relation"]) == 1
    assert relation_data["resolved"][0]["id"] == "collabiq-1"
    assert (
        relation_data["resolved"][0]["properties"]["Name"]["title"][0]["text"][
            "content"
        ]
        == "CollabIQ Record 1"
    )

    # Verify retrieve_page called once
    assert mock_notion_client.retrieve_page.call_count == 1


@pytest.mark.asyncio
async def test_resolve_relationships_depth_limit(mock_notion_client):
    """Test relationship resolution respects depth limit."""
    from notion_integrator.fetcher import resolve_relationships
    from notion_integrator.schema import create_database_schema
    from notion_integrator.models import NotionDatabase, NotionProperty

    # Create schema with relation
    db = NotionDatabase(
        id="db-id",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Related": NotionProperty(
                id="rel1",
                name="Related",
                type="relation",
                config={"relation": {"database_id": "related-db-id"}},
            ),
        },
    )
    schema = create_database_schema(db)

    # Create record with relation
    record = {
        "object": "page",
        "id": "page-1",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Page 1"}}],
            },
            "Related": {
                "id": "rel1",
                "type": "relation",
                "relation": [{"id": "related-page-1"}],
            },
        },
    }

    # Resolve with depth=0 (no resolution)
    resolved_record = await resolve_relationships(
        client=mock_notion_client,
        record=record,
        schema=schema,
        max_depth=0,
    )

    # Verify no API calls made
    assert mock_notion_client.retrieve_page.call_count == 0
    assert "Related" in resolved_record["properties"]
    assert "resolved" not in resolved_record["properties"]["Related"]


@pytest.mark.asyncio
async def test_resolve_relationships_circular_detection(mock_notion_client):
    """Test circular reference detection in relationship resolution."""
    from notion_integrator.fetcher import resolve_relationships
    from notion_integrator.schema import create_database_schema
    from notion_integrator.models import NotionDatabase, NotionProperty

    # Create schema with self-referencing relation
    db = NotionDatabase(
        id="db-id",
        title="DB",
        url="https://notion.so/db",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Related": NotionProperty(
                id="rel1",
                name="Related",
                type="relation",
                config={"relation": {"database_id": "db-id"}},  # Self-reference
            ),
        },
    )
    schema = create_database_schema(db)

    # Create record that references itself
    record = {
        "object": "page",
        "id": "page-1",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Page 1"}}],
            },
            "Related": {
                "id": "rel1",
                "type": "relation",
                "relation": [{"id": "page-1"}],  # Self-reference
            },
        },
    }

    # Setup mock to return same record (circular)
    mock_notion_client.retrieve_page.return_value = record

    # Resolve relationships
    await resolve_relationships(
        client=mock_notion_client,
        record=record,
        schema=schema,
        max_depth=2,
        visited_pages=set(),
    )

    # Verify circular reference detected and stopped
    # Should only fetch once, not infinitely
    assert mock_notion_client.retrieve_page.call_count <= 2


# ==============================================================================
# Error Handling Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_fetch_all_records_authentication_error(mock_notion_client):
    """Test handling authentication error during fetch."""
    from notion_integrator.fetcher import fetch_all_records

    # Setup mock to raise authentication error
    mock_notion_client.query_database.side_effect = NotionAuthenticationError(
        "Notion API authentication failed. Check your API key.",
        details={"database_id": "companies-db-id"},
    )

    # Verify error propagated
    with pytest.raises(NotionAuthenticationError) as exc_info:
        await fetch_all_records(
            client=mock_notion_client,
            database_id="companies-db-id",
        )

    assert "authentication" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_fetch_all_records_not_found_error(mock_notion_client):
    """Test handling not found error during fetch."""
    from notion_integrator.fetcher import fetch_all_records

    # Setup mock to raise not found error
    mock_notion_client.query_database.side_effect = NotionObjectNotFoundError(
        object_type="database",
        object_id="nonexistent-db-id",
        message="Database not found or not shared with integration.",
    )

    # Verify error propagated
    with pytest.raises(NotionObjectNotFoundError) as exc_info:
        await fetch_all_records(
            client=mock_notion_client,
            database_id="nonexistent-db-id",
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_resolve_relationships_page_not_found(
    mock_notion_client, mock_companies_page_1
):
    """Test handling missing related page gracefully."""
    from notion_integrator.fetcher import resolve_relationships
    from notion_integrator.schema import create_database_schema
    from notion_integrator.models import NotionDatabase, NotionProperty

    # Create schema
    db = NotionDatabase(
        id="companies-db-id",
        title="Companies",
        url="https://notion.so/companies",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Related CollabIQ": NotionProperty(
                id="rel1",
                name="Related CollabIQ",
                type="relation",
                config={"relation": {"database_id": "collabiq-db-id"}},
            ),
        },
    )
    schema = create_database_schema(db)

    # Setup mock to raise not found for related page
    mock_notion_client.retrieve_page.side_effect = NotionObjectNotFoundError(
        object_type="page",
        object_id="collabiq-1",
        message="Page not found or not shared with integration.",
    )

    # Get record
    record = mock_companies_page_1["results"][0]

    # Resolve relationships (should handle error gracefully)
    resolved_record = await resolve_relationships(
        client=mock_notion_client,
        record=record,
        schema=schema,
        max_depth=1,
    )

    # Verify record returned with error indicator
    assert "Related CollabIQ" in resolved_record["properties"]
    relation_data = resolved_record["properties"]["Related CollabIQ"]
    assert "error" in relation_data or "resolved" not in relation_data
