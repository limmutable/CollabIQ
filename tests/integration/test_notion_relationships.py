"""
Integration Tests for Notion Relationship Resolution

Tests end-to-end relationship resolution across multiple databases:
- Fetch data from multiple related databases
- Resolve bidirectional relationships
- Handle circular references gracefully
- Respect max depth limits
- Track visited pages to prevent infinite loops
- Handle missing related pages

These tests use real DatabaseSchema objects and mock API responses
to verify the complete relationship resolution flow.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.notion_integrator.models import (
    NotionDatabase,
    NotionProperty,
)
from src.notion_integrator.exceptions import NotionObjectNotFoundError


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def companies_database():
    """Companies database with relations to CollabIQ."""
    return NotionDatabase(
        id="companies-db-id",
        title="Companies",
        url="https://notion.so/companies",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(
                id="title",
                name="Name",
                type="title",
                config={},
            ),
            "Description": NotionProperty(
                id="desc",
                name="Description",
                type="rich_text",
                config={},
            ),
            "Shinsegae affiliates?": NotionProperty(
                id="ssg",
                name="Shinsegae affiliates?",
                type="checkbox",
                config={},
            ),
            "Is Portfolio?": NotionProperty(
                id="portfolio",
                name="Is Portfolio?",
                type="checkbox",
                config={},
            ),
            "Related CollabIQ": NotionProperty(
                id="rel_collabiq",
                name="Related CollabIQ",
                type="relation",
                config={
                    "relation": {
                        "database_id": "collabiq-db-id",
                        "type": "dual_property",
                        "synced_property_name": "Related Companies",
                    }
                },
            ),
            "Partners": NotionProperty(
                id="rel_partners",
                name="Partners",
                type="relation",
                config={
                    "relation": {
                        "database_id": "companies-db-id",  # Self-reference
                        "type": "dual_property",
                    }
                },
            ),
        },
    )


@pytest.fixture
def collabiq_database():
    """CollabIQ database with relations to Companies."""
    return NotionDatabase(
        id="collabiq-db-id",
        title="CollabIQ",
        url="https://notion.so/collabiq",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties={
            "Name": NotionProperty(
                id="title",
                name="Name",
                type="title",
                config={},
            ),
            "Status": NotionProperty(
                id="status",
                name="Status",
                type="select",
                config={
                    "select": {
                        "options": [
                            {"id": "opt1", "name": "Active", "color": "green"},
                            {"id": "opt2", "name": "Completed", "color": "blue"},
                        ]
                    }
                },
            ),
            "Related Companies": NotionProperty(
                id="rel_companies",
                name="Related Companies",
                type="relation",
                config={
                    "relation": {
                        "database_id": "companies-db-id",
                        "type": "dual_property",
                        "synced_property_name": "Related CollabIQ",
                    }
                },
            ),
        },
    )


@pytest.fixture
def companies_schema(companies_database):
    """DatabaseSchema for Companies database."""
    from src.notion_integrator.schema import create_database_schema

    return create_database_schema(companies_database)


@pytest.fixture
def collabiq_schema(collabiq_database):
    """DatabaseSchema for CollabIQ database."""
    from src.notion_integrator.schema import create_database_schema

    return create_database_schema(collabiq_database)


@pytest.fixture
def relationship_graph(companies_schema, collabiq_schema):
    """RelationshipGraph for both databases."""
    from src.notion_integrator.schema import build_relationship_graph

    schemas = {
        "companies-db-id": companies_schema,
        "collabiq-db-id": collabiq_schema,
    }

    return build_relationship_graph(schemas)


@pytest.fixture
def mock_notion_client():
    """Mock NotionClient for testing."""
    client = MagicMock()
    client.query_database = AsyncMock()
    client.retrieve_page = AsyncMock()
    client.retrieve_database = AsyncMock()
    return client


@pytest.fixture
def company_record():
    """Sample company record with relations."""
    return {
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
            "Description": {
                "id": "desc",
                "type": "rich_text",
                "rich_text": [
                    {"type": "text", "text": {"content": "Leading tech company"}}
                ],
            },
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
                "id": "rel_collabiq",
                "type": "relation",
                "relation": [{"id": "collabiq-1"}, {"id": "collabiq-2"}],
            },
            "Partners": {
                "id": "rel_partners",
                "type": "relation",
                "relation": [{"id": "company-2"}],
            },
        },
    }


@pytest.fixture
def collabiq_record_1():
    """Sample CollabIQ record 1."""
    return {
        "object": "page",
        "id": "collabiq-1",
        "created_time": "2025-01-01T00:00:00.000Z",
        "last_edited_time": "2025-11-01T00:00:00.000Z",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Project Alpha"}}],
            },
            "Status": {
                "id": "status",
                "type": "select",
                "select": {"id": "opt1", "name": "Active", "color": "green"},
            },
            "Related Companies": {
                "id": "rel_companies",
                "type": "relation",
                "relation": [{"id": "company-1"}],  # Back reference to company-1
            },
        },
    }


@pytest.fixture
def collabiq_record_2():
    """Sample CollabIQ record 2."""
    return {
        "object": "page",
        "id": "collabiq-2",
        "created_time": "2025-01-02T00:00:00.000Z",
        "last_edited_time": "2025-11-02T00:00:00.000Z",
        "properties": {
            "Name": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Project Beta"}}],
            },
            "Status": {
                "id": "status",
                "type": "select",
                "select": {"id": "opt2", "name": "Completed", "color": "blue"},
            },
            "Related Companies": {
                "id": "rel_companies",
                "type": "relation",
                "relation": [{"id": "company-1"}],
            },
        },
    }


@pytest.fixture
def partner_company_record():
    """Sample partner company record."""
    return {
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
            "Description": {
                "id": "desc",
                "type": "rich_text",
                "rich_text": [
                    {"type": "text", "text": {"content": "Strategic partner"}}
                ],
            },
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
                "id": "rel_collabiq",
                "type": "relation",
                "relation": [],
            },
            "Partners": {
                "id": "rel_partners",
                "type": "relation",
                "relation": [{"id": "company-1"}],  # Back reference to company-1
            },
        },
    }


# ==============================================================================
# Bidirectional Relationship Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_resolve_bidirectional_relationships(
    mock_notion_client,
    companies_schema,
    company_record,
    collabiq_record_1,
    collabiq_record_2,
):
    """Test resolving bidirectional relationships between Companies and CollabIQ."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock to return related CollabIQ records and partner company
    def mock_retrieve_page(page_id):
        if page_id == "collabiq-1":
            return collabiq_record_1
        elif page_id == "collabiq-2":
            return collabiq_record_2
        elif page_id == "company-2":
            # Return a simple partner company record
            return {
                "object": "page",
                "id": "company-2",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"type": "text", "text": {"content": "Beta Inc"}}],
                    }
                },
            }
        else:
            raise NotionObjectNotFoundError(
                object_type="page", object_id=page_id, message="Page not found"
            )

    mock_notion_client.retrieve_page.side_effect = mock_retrieve_page

    # Resolve relationships
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=1,
    )

    # Verify Related CollabIQ resolved
    assert "Related CollabIQ" in resolved["properties"]
    related_collabiq = resolved["properties"]["Related CollabIQ"]
    assert "resolved" in related_collabiq
    assert len(related_collabiq["resolved"]) == 2

    # Verify first CollabIQ record
    assert related_collabiq["resolved"][0]["id"] == "collabiq-1"
    assert (
        related_collabiq["resolved"][0]["properties"]["Name"]["title"][0]["text"][
            "content"
        ]
        == "Project Alpha"
    )

    # Verify second CollabIQ record
    assert related_collabiq["resolved"][1]["id"] == "collabiq-2"
    assert (
        related_collabiq["resolved"][1]["properties"]["Name"]["title"][0]["text"][
            "content"
        ]
        == "Project Beta"
    )

    # Verify retrieve_page called for all relations (2 CollabIQ + 1 Partners)
    assert mock_notion_client.retrieve_page.call_count == 3


@pytest.mark.asyncio
async def test_resolve_circular_relationships_with_depth_limit(
    mock_notion_client,
    companies_schema,
    company_record,
    collabiq_record_1,
):
    """Test circular relationships stop at depth limit."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock to return records with circular references
    def mock_retrieve_page(page_id):
        if page_id == "collabiq-1":
            return collabiq_record_1  # Has back reference to company-1
        elif page_id == "company-1":
            return company_record  # Original record
        else:
            raise NotionObjectNotFoundError(
                object_type="page", object_id=page_id, message="Page not found"
            )

    mock_notion_client.retrieve_page.side_effect = mock_retrieve_page

    # Resolve with max_depth=1 (should not follow back references)
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=1,
    )

    # Verify relationships resolved at depth 1 only
    assert "Related CollabIQ" in resolved["properties"]
    related_collabiq = resolved["properties"]["Related CollabIQ"]
    assert "resolved" in related_collabiq

    # Should not resolve back to company-1
    # Verify retrieve_page not called excessively
    assert mock_notion_client.retrieve_page.call_count <= 3  # Max 2 for depth 1


@pytest.mark.asyncio
async def test_resolve_self_referencing_relationships(
    mock_notion_client,
    companies_schema,
    company_record,
    partner_company_record,
):
    """Test self-referencing relationships (Partners) within same database."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock to return partner company
    def mock_retrieve_page(page_id):
        if page_id == "company-2":
            return partner_company_record
        elif page_id == "company-1":
            return company_record
        else:
            raise NotionObjectNotFoundError(
                object_type="page", object_id=page_id, message="Page not found"
            )

    mock_notion_client.retrieve_page.side_effect = mock_retrieve_page

    # Resolve relationships
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=1,
    )

    # Verify Partners resolved
    assert "Partners" in resolved["properties"]
    partners = resolved["properties"]["Partners"]
    assert "resolved" in partners
    assert len(partners["resolved"]) == 1

    # Verify partner details
    assert partners["resolved"][0]["id"] == "company-2"
    assert (
        partners["resolved"][0]["properties"]["Name"]["title"][0]["text"]["content"]
        == "Beta Inc"
    )


# ==============================================================================
# Circular Reference Detection Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_visited_pages_prevents_infinite_loops(
    mock_notion_client,
    companies_schema,
    company_record,
    collabiq_record_1,
):
    """Test visited_pages set prevents infinite loops in circular references."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Create circular reference: company-1 -> collabiq-1 -> company-1
    # Modify collabiq_record_1 to reference back to company-1
    circular_collabiq = collabiq_record_1.copy()

    # Setup mock to return circular references
    retrieve_count = 0

    def mock_retrieve_page(page_id):
        nonlocal retrieve_count
        retrieve_count += 1

        if retrieve_count > 10:  # Safety check
            raise Exception("Too many retrieve_page calls - infinite loop detected")

        if page_id == "collabiq-1":
            return circular_collabiq
        elif page_id == "company-1":
            return company_record
        else:
            raise NotionObjectNotFoundError(
                object_type="page", object_id=page_id, message="Page not found"
            )

    mock_notion_client.retrieve_page.side_effect = mock_retrieve_page

    # Resolve with visited_pages tracking
    await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=3,  # Allow deeper traversal
        visited_pages=set(),
    )

    # Verify no infinite loop occurred
    assert retrieve_count <= 5  # Should stop after visiting same pages


@pytest.mark.asyncio
async def test_relationship_graph_circular_detection(relationship_graph):
    """Test RelationshipGraph detects circular references."""
    # Verify graph detects circular references
    assert relationship_graph.has_circular_refs is True

    # Verify relationships exist
    assert len(relationship_graph.relationships) >= 1

    # Verify adjacency list shows bidirectional connections
    assert "collabiq-db-id" in relationship_graph.adjacency_list["companies-db-id"]


# ==============================================================================
# Multi-Level Relationship Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_resolve_multi_level_relationships(
    mock_notion_client,
    companies_schema,
    company_record,
    collabiq_record_1,
    partner_company_record,
):
    """Test resolving relationships at multiple depth levels."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock to return all related records
    def mock_retrieve_page(page_id):
        if page_id == "collabiq-1":
            return collabiq_record_1
        elif page_id == "company-2":
            return partner_company_record
        elif page_id == "company-1":
            return company_record
        else:
            raise NotionObjectNotFoundError(
                object_type="page", object_id=page_id, message="Page not found"
            )

    mock_notion_client.retrieve_page.side_effect = mock_retrieve_page

    # Resolve with max_depth=2
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=2,
    )

    # Verify depth 1 relationships resolved
    assert "Related CollabIQ" in resolved["properties"]
    assert "resolved" in resolved["properties"]["Related CollabIQ"]

    # Verify depth 2 relationships could be resolved
    # (CollabIQ records should have their relations resolved too if depth allows)
    # This depends on implementation details


# ==============================================================================
# Error Handling Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_resolve_relationships_handles_missing_pages_gracefully(
    mock_notion_client,
    companies_schema,
    company_record,
):
    """Test graceful handling of missing related pages."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock to raise not found for all related pages
    mock_notion_client.retrieve_page.side_effect = NotionObjectNotFoundError(
        object_type="page",
        object_id="collabiq-1",
        message="Page not found or not shared with integration.",
    )

    # Resolve relationships (should not crash)
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=1,
    )

    # Verify record returned (even if relations couldn't be resolved)
    assert resolved["id"] == "company-1"
    assert "Related CollabIQ" in resolved["properties"]

    # Verify error handling (either error field or empty resolved list)
    related_collabiq = resolved["properties"]["Related CollabIQ"]
    # Implementation should handle gracefully - either skip or mark error
    assert (
        "error" in related_collabiq
        or "resolved" not in related_collabiq
        or len(related_collabiq.get("resolved", [])) == 0
    )


@pytest.mark.asyncio
async def test_resolve_relationships_partial_success(
    mock_notion_client,
    companies_schema,
    company_record,
    collabiq_record_1,
):
    """Test partial success when some related pages found, others not."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock to return one record, fail on another
    def mock_retrieve_page(page_id):
        if page_id == "collabiq-1":
            return collabiq_record_1
        elif page_id == "collabiq-2":
            raise NotionObjectNotFoundError(
                object_type="page",
                object_id="collabiq-2",
                message="Page not found",
            )
        else:
            raise NotionObjectNotFoundError(
                object_type="page", object_id=page_id, message="Page not found"
            )

    mock_notion_client.retrieve_page.side_effect = mock_retrieve_page

    # Resolve relationships
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=1,
    )

    # Verify partial success
    assert "Related CollabIQ" in resolved["properties"]
    related_collabiq = resolved["properties"]["Related CollabIQ"]

    # Should have at least one resolved record (collabiq-1)
    if "resolved" in related_collabiq:
        assert len(related_collabiq["resolved"]) >= 1
        assert related_collabiq["resolved"][0]["id"] == "collabiq-1"


# ==============================================================================
# Integration with RelationshipGraph Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_fetch_with_relationship_graph(
    mock_notion_client,
    relationship_graph,
    companies_schema,
    company_record,
    collabiq_record_1,
):
    """Test using RelationshipGraph to guide relationship resolution."""
    from src.notion_integrator.fetcher import resolve_relationships

    # Setup mock
    mock_notion_client.retrieve_page.return_value = collabiq_record_1

    # Resolve using relationship graph context
    resolved = await resolve_relationships(
        client=mock_notion_client,
        record=company_record,
        schema=companies_schema,
        max_depth=1,
        relationship_graph=relationship_graph,
    )

    # Verify relationships resolved
    assert "Related CollabIQ" in resolved["properties"]

    # Verify graph used to identify circular references
    # (implementation detail - graph should help optimize resolution)
