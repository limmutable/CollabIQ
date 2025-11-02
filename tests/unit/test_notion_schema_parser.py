"""
Unit Tests for Notion Schema Parser

Tests the schema parsing logic in isolation, focusing on:
- Property type identification
- Relationship detection
- Classification field mapping
- Properties grouping by type
- Schema validation logic

These tests use minimal fixtures and don't require API calls.
"""

import pytest
from datetime import datetime

from src.notion_integrator.models import (
    DatabaseSchema,
    NotionDatabase,
    NotionProperty,
    Relationship,
    RelationshipGraph,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_properties():
    """Sample Notion properties for testing."""
    return {
        "Name": NotionProperty(
            id="title",
            name="Name",
            type="title",
            config={},
        ),
        "Description": NotionProperty(
            id="prop_desc",
            name="Description",
            type="rich_text",
            config={},
        ),
        "Founded Year": NotionProperty(
            id="prop_year",
            name="Founded Year",
            type="number",
            config={"number": {"format": "number"}},
        ),
        "Shinsegae affiliates?": NotionProperty(
            id="prop_ssg",
            name="Shinsegae affiliates?",
            type="checkbox",
            config={},
        ),
        "Is Portfolio?": NotionProperty(
            id="prop_portfolio",
            name="Is Portfolio?",
            type="checkbox",
            config={},
        ),
        "Industry": NotionProperty(
            id="prop_industry",
            name="Industry",
            type="select",
            config={
                "select": {
                    "options": [
                        {"id": "opt1", "name": "Technology", "color": "blue"},
                        {"id": "opt2", "name": "Retail", "color": "red"},
                    ]
                }
            },
        ),
        "Tags": NotionProperty(
            id="prop_tags",
            name="Tags",
            type="multi_select",
            config={
                "multi_select": {
                    "options": [
                        {"id": "tag1", "name": "Startup", "color": "green"},
                        {"id": "tag2", "name": "Series A", "color": "yellow"},
                    ]
                }
            },
        ),
        "Related CollabIQ": NotionProperty(
            id="prop_relation1",
            name="Related CollabIQ",
            type="relation",
            config={
                "relation": {
                    "database_id": "xyz789-uvw012-abc345",
                    "type": "dual_property",
                }
            },
        ),
        "Partners": NotionProperty(
            id="prop_relation2",
            name="Partners",
            type="relation",
            config={
                "relation": {
                    "database_id": "partner-db-id",
                    "type": "single_property",
                }
            },
        ),
    }


@pytest.fixture
def sample_database(sample_properties):
    """Sample NotionDatabase for testing."""
    return NotionDatabase(
        id="abc123-def456-ghi789",
        title="Companies",
        url="https://www.notion.so/workspace/abc123",
        created_time=datetime(2025, 1, 1),
        last_edited_time=datetime(2025, 11, 1),
        properties=sample_properties,
    )


# ==============================================================================
# Property Type Identification Tests
# ==============================================================================


def test_group_properties_by_type(sample_properties):
    """Test grouping properties by type."""
    from src.notion_integrator.schema import group_properties_by_type

    grouped = group_properties_by_type(sample_properties)

    # Verify all types present
    assert "title" in grouped
    assert "rich_text" in grouped
    assert "number" in grouped
    assert "checkbox" in grouped
    assert "select" in grouped
    assert "multi_select" in grouped
    assert "relation" in grouped

    # Verify counts
    assert len(grouped["title"]) == 1
    assert len(grouped["rich_text"]) == 1
    assert len(grouped["number"]) == 1
    assert len(grouped["checkbox"]) == 2
    assert len(grouped["select"]) == 1
    assert len(grouped["multi_select"]) == 1
    assert len(grouped["relation"]) == 2

    # Verify property names
    assert grouped["title"][0].name == "Name"
    assert grouped["checkbox"][0].name == "Shinsegae affiliates?"
    assert grouped["checkbox"][1].name == "Is Portfolio?"
    assert grouped["relation"][0].name == "Related CollabIQ"
    assert grouped["relation"][1].name == "Partners"


def test_identify_relation_properties(sample_properties):
    """Test identifying relation properties."""
    from src.notion_integrator.schema import identify_relation_properties

    relations = identify_relation_properties(sample_properties)

    assert len(relations) == 2
    assert relations[0].name == "Related CollabIQ"
    assert relations[1].name == "Partners"
    assert relations[0].type == "relation"
    assert relations[1].type == "relation"

    # Verify relation config
    assert "database_id" in relations[0].config["relation"]
    assert relations[0].config["relation"]["database_id"] == "xyz789-uvw012-abc345"


def test_identify_relation_properties_none():
    """Test identifying relation properties when none exist."""
    from src.notion_integrator.schema import identify_relation_properties

    properties = {
        "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        "Description": NotionProperty(
            id="desc", name="Description", type="rich_text", config={}
        ),
    }

    relations = identify_relation_properties(properties)

    assert len(relations) == 0


# ==============================================================================
# Classification Field Detection Tests
# ==============================================================================


def test_identify_classification_fields_both_present(sample_properties):
    """Test identifying both classification fields."""
    from src.notion_integrator.schema import identify_classification_fields

    classification = identify_classification_fields(sample_properties)

    assert "is_shinsegae_affiliate" in classification
    assert "is_portfolio_company" in classification
    assert classification["is_shinsegae_affiliate"] == "prop_ssg"
    assert classification["is_portfolio_company"] == "prop_portfolio"


def test_identify_classification_fields_only_ssg():
    """Test identifying only Shinsegae affiliate field."""
    from src.notion_integrator.schema import identify_classification_fields

    properties = {
        "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        "Shinsegae affiliates?": NotionProperty(
            id="prop_ssg",
            name="Shinsegae affiliates?",
            type="checkbox",
            config={},
        ),
    }

    classification = identify_classification_fields(properties)

    assert "is_shinsegae_affiliate" in classification
    assert "is_portfolio_company" not in classification
    assert classification["is_shinsegae_affiliate"] == "prop_ssg"


def test_identify_classification_fields_only_portfolio():
    """Test identifying only portfolio field."""
    from src.notion_integrator.schema import identify_classification_fields

    properties = {
        "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        "Is Portfolio?": NotionProperty(
            id="prop_portfolio",
            name="Is Portfolio?",
            type="checkbox",
            config={},
        ),
    }

    classification = identify_classification_fields(properties)

    assert "is_shinsegae_affiliate" not in classification
    assert "is_portfolio_company" in classification
    assert classification["is_portfolio_company"] == "prop_portfolio"


def test_identify_classification_fields_none():
    """Test when no classification fields present."""
    from src.notion_integrator.schema import identify_classification_fields

    properties = {
        "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        "Active": NotionProperty(
            id="active", name="Active", type="checkbox", config={}
        ),
    }

    classification = identify_classification_fields(properties)

    assert len(classification) == 0


def test_identify_classification_fields_case_insensitive():
    """Test classification field detection is case-insensitive."""
    from src.notion_integrator.schema import identify_classification_fields

    properties = {
        "shinsegae affiliates?": NotionProperty(
            id="prop_ssg",
            name="shinsegae affiliates?",
            type="checkbox",
            config={},
        ),
        "is portfolio?": NotionProperty(
            id="prop_portfolio",
            name="is portfolio?",
            type="checkbox",
            config={},
        ),
    }

    classification = identify_classification_fields(properties)

    assert "is_shinsegae_affiliate" in classification
    assert "is_portfolio_company" in classification


# ==============================================================================
# Schema Creation Tests
# ==============================================================================


def test_create_database_schema(sample_database):
    """Test creating DatabaseSchema from NotionDatabase."""
    from src.notion_integrator.schema import create_database_schema

    schema = create_database_schema(sample_database)

    # Verify schema structure
    assert isinstance(schema, DatabaseSchema)
    assert schema.database == sample_database
    assert len(schema.properties_by_type) > 0
    assert len(schema.relation_properties) == 2
    assert len(schema.classification_fields) == 2

    # Verify computed fields
    assert schema.has_relations is True
    assert schema.property_count == 9


def test_create_database_schema_no_relations():
    """Test creating schema for database without relations."""
    from src.notion_integrator.schema import create_database_schema

    db = NotionDatabase(
        id="abc123",
        title="Simple DB",
        url="https://notion.so/abc123",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        },
    )

    schema = create_database_schema(db)

    assert schema.has_relations is False
    assert len(schema.relation_properties) == 0


# ==============================================================================
# Relationship Graph Tests
# ==============================================================================


def test_build_relationship_graph_single_relation():
    """Test building relationship graph with one relation."""
    from src.notion_integrator.schema import (
        build_relationship_graph,
        create_database_schema,
    )

    companies_db = NotionDatabase(
        id="companies-id",
        title="Companies",
        url="https://notion.so/companies",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Related CollabIQ": NotionProperty(
                id="rel1",
                name="Related CollabIQ",
                type="relation",
                config={
                    "relation": {"database_id": "collabiq-id", "type": "dual_property"}
                },
            ),
        },
    )

    collabiq_db = NotionDatabase(
        id="collabiq-id",
        title="CollabIQ",
        url="https://notion.so/collabiq",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
        },
    )

    schemas = {
        "companies-id": create_database_schema(companies_db),
        "collabiq-id": create_database_schema(collabiq_db),
    }

    graph = build_relationship_graph(schemas)

    # Verify graph structure
    assert isinstance(graph, RelationshipGraph)
    assert len(graph.databases) == 2
    assert len(graph.relationships) == 1
    assert "companies-id" in graph.adjacency_list
    assert "collabiq-id" in graph.adjacency_list["companies-id"]


def test_relationship_graph_circular_detection():
    """Test circular reference detection in relationship graph."""
    # Create graph with circular reference
    db1 = NotionDatabase(
        id="db1",
        title="DB1",
        url="https://notion.so/db1",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Rel to DB2": NotionProperty(
                id="rel1",
                name="Rel to DB2",
                type="relation",
                config={"relation": {"database_id": "db2", "type": "dual_property"}},
            ),
        },
    )

    db2 = NotionDatabase(
        id="db2",
        title="DB2",
        url="https://notion.so/db2",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Rel to DB1": NotionProperty(
                id="rel2",
                name="Rel to DB1",
                type="relation",
                config={"relation": {"database_id": "db1", "type": "dual_property"}},
            ),
        },
    )

    # Build relationship graph
    rel1 = Relationship(
        source_db_id="db1",
        source_property=db1.properties["Rel to DB2"],
        target_db_id="db2",
        is_bidirectional=True,
    )

    rel2 = Relationship(
        source_db_id="db2",
        source_property=db2.properties["Rel to DB1"],
        target_db_id="db1",
        is_bidirectional=True,
    )

    graph = RelationshipGraph(
        databases={"db1": db1, "db2": db2},
        relationships=[rel1, rel2],
        adjacency_list={"db1": ["db2"], "db2": ["db1"]},
    )

    # Verify circular reference detected
    assert graph.has_circular_refs is True


def test_relationship_graph_no_circular():
    """Test no circular reference in linear graph."""
    db1 = NotionDatabase(
        id="db1",
        title="DB1",
        url="https://notion.so/db1",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={})
        },
    )

    db2 = NotionDatabase(
        id="db2",
        title="DB2",
        url="https://notion.so/db2",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        properties={
            "Name": NotionProperty(id="title", name="Name", type="title", config={}),
            "Rel to DB1": NotionProperty(
                id="rel1",
                name="Rel to DB1",
                type="relation",
                config={"relation": {"database_id": "db1"}},
            ),
        },
    )

    graph = RelationshipGraph(
        databases={"db1": db1, "db2": db2},
        relationships=[
            Relationship(
                source_db_id="db2",
                source_property=db2.properties["Rel to DB1"],
                target_db_id="db1",
                is_bidirectional=False,
            )
        ],
        adjacency_list={"db1": [], "db2": ["db1"]},
    )

    # Verify no circular reference
    assert graph.has_circular_refs is False


# ==============================================================================
# Schema Validation Tests
# ==============================================================================


def test_validate_schema_success(sample_database):
    """Test successful schema validation."""
    from src.notion_integrator.schema import validate_schema, create_database_schema

    schema = create_database_schema(sample_database)

    # Should not raise
    validate_schema(schema)


def test_validate_schema_empty_properties():
    """Test validation fails with empty properties."""
    from pydantic import ValidationError

    # Should raise due to Pydantic validation when creating NotionDatabase
    with pytest.raises(ValidationError) as exc_info:
        NotionDatabase(
            id="abc123",
            title="Empty DB",
            url="https://notion.so/abc123",
            created_time=datetime.now(),
            last_edited_time=datetime.now(),
            properties={},
        )

    # Verify error message mentions properties
    assert "properties" in str(exc_info.value).lower()
