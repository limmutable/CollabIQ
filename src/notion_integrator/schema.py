"""
Schema Discovery and Management

Handles discovery, parsing, and validation of Notion database schemas:
- Database metadata retrieval
- Property type identification
- Relationship detection
- Classification field mapping
- Relationship graph building

Key Functions:
- discover_schema(): High-level schema discovery
- create_database_schema(): Convert NotionDatabase to DatabaseSchema
- build_relationship_graph(): Build relationship graph from multiple schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .cache import CacheManager
from .client import NotionClient
from .exceptions import SchemaValidationError
from .logging_config import get_logger, PerformanceLogger
from .models import (
    DatabaseSchema,
    NotionDatabase,
    NotionProperty,
    Relationship,
    RelationshipGraph,
)


logger = get_logger(__name__)


# ==============================================================================
# High-Level Schema Discovery
# ==============================================================================


async def discover_schema(
    client: NotionClient,
    database_id: str,
    cache_manager: Optional[CacheManager] = None,
    use_cache: bool = True,
) -> DatabaseSchema:
    """
    Discover complete schema from a Notion database with optional caching.

    Args:
        client: NotionClient instance
        database_id: Database ID to discover
        cache_manager: Optional CacheManager for caching (defaults to new instance)
        use_cache: Whether to use cache (default: True)

    Returns:
        DatabaseSchema with complete structure

    Raises:
        NotionAuthenticationError: Invalid API key
        NotionObjectNotFoundError: Database not found
        NotionPermissionError: Insufficient permissions
        SchemaValidationError: Invalid schema structure
    """
    with PerformanceLogger(logger, "schema_discovery", database_id=database_id):
        # Initialize cache manager if not provided
        if cache_manager is None and use_cache:
            cache_manager = CacheManager()

        # Try to get from cache first
        if use_cache and cache_manager:
            # We need database name for cache lookup, so do a quick fetch first
            db_response = await client.retrieve_database(database_id)

            # Get data source for properties (Notion API 2025-09-03)
            data_sources = db_response.get("data_sources", [])
            if not data_sources:
                raise SchemaValidationError(
                    database_id=database_id,
                    message="Database has no data sources",
                    validation_errors=["No data sources found"],
                )

            # Retrieve the first data source to get properties
            data_source_id = data_sources[0]["id"]
            data_source_response = await client.retrieve_data_source(data_source_id)

            notion_db = parse_database_response(db_response, data_source_response)
            database_name = notion_db.title

            cached_schema = cache_manager.get_schema_cache(database_id, database_name)
            if cached_schema:
                logger.info(
                    "Schema loaded from cache",
                    extra={
                        "database_id": database_id,
                        "database_name": database_name,
                    },
                )
                return cached_schema

            # Cache miss - create schema and cache it
            schema = create_database_schema(notion_db, data_source_id)
            validate_schema(schema)
            cache_manager.set_schema_cache(schema)

        else:
            # No caching - fetch fresh
            db_response = await client.retrieve_database(database_id)

            # Get data source for properties (Notion API 2025-09-03)
            data_sources = db_response.get("data_sources", [])
            if not data_sources:
                raise SchemaValidationError(
                    database_id=database_id,
                    message="Database has no data sources",
                    validation_errors=["No data sources found"],
                )

            # Retrieve the first data source to get properties
            data_source_id = data_sources[0]["id"]
            data_source_response = await client.retrieve_data_source(data_source_id)

            notion_db = parse_database_response(db_response, data_source_response)
            schema = create_database_schema(notion_db, data_source_id)
            validate_schema(schema)

        logger.info(
            "Schema discovery completed",
            extra={
                "database_id": database_id,
                "database_name": schema.database.title,
                "property_count": schema.property_count,
                "has_relations": schema.has_relations,
                "relation_count": len(schema.relation_properties),
                "has_classification": len(schema.classification_fields) > 0,
                "cached": use_cache and cache_manager is not None,
            },
        )

        return schema


# ==============================================================================
# Database Response Parsing
# ==============================================================================


def parse_database_response(
    db_response: Dict[str, Any],
    data_source_response: Optional[Dict[str, Any]] = None,
) -> NotionDatabase:
    """
    Parse Notion API database and data source responses to NotionDatabase model.

    Note: Migrated to Notion API 2025-09-03. Databases no longer have properties;
    properties are now on data sources. This function requires both responses.

    Args:
        db_response: Raw response from databases.retrieve
        data_source_response: Raw response from data_sources.retrieve (optional for backward compat)

    Returns:
        NotionDatabase instance

    Raises:
        SchemaValidationError: If response structure is invalid
    """
    try:
        # Extract database ID
        db_id = db_response["id"]

        # Extract title
        title_array = db_response.get("title", [])
        if title_array and len(title_array) > 0:
            title = title_array[0].get("text", {}).get("content", "Untitled")
        else:
            title = "Untitled"

        # Extract URL
        url = db_response.get("url", "")

        # Parse timestamps
        created_time = datetime.fromisoformat(
            db_response["created_time"].replace("Z", "+00:00")
        )
        last_edited_time = datetime.fromisoformat(
            db_response["last_edited_time"].replace("Z", "+00:00")
        )

        # Parse properties from data source (new API 2025-09-03)
        if data_source_response:
            properties_dict = data_source_response.get("properties", {})
        else:
            # Fallback: try to get from database response (old API, will be empty in new API)
            properties_dict = db_response.get("properties", {})

        if not properties_dict:
            raise SchemaValidationError(
                database_id=db_id,
                message="Database has no properties",
                validation_errors=["Properties dictionary is empty"],
            )

        properties = {}
        for prop_name, prop_data in properties_dict.items():
            prop = parse_property(prop_name, prop_data)
            properties[prop_name] = prop

        # Create NotionDatabase
        return NotionDatabase(
            id=db_id,
            title=title,
            url=url,
            created_time=created_time,
            last_edited_time=last_edited_time,
            properties=properties,
        )

    except KeyError as e:
        raise SchemaValidationError(
            database_id=db_response.get("id", "unknown"),
            message=f"Missing required field in database response: {e}",
            validation_errors=[str(e)],
            original_error=e,
        )
    except Exception as e:
        raise SchemaValidationError(
            database_id=db_response.get("id", "unknown"),
            message=f"Failed to parse database response: {e}",
            original_error=e,
        )


def parse_property(name: str, prop_data: Dict[str, Any]) -> NotionProperty:
    """
    Parse property data from Notion API response.

    Args:
        name: Property name
        prop_data: Property data from API

    Returns:
        NotionProperty instance
    """
    prop_id = prop_data.get("id", "")
    prop_type = prop_data.get("type", "unknown")

    # Extract type-specific configuration
    config = {}
    if prop_type in prop_data:
        config[prop_type] = prop_data[prop_type]

    return NotionProperty(
        id=prop_id,
        name=name,
        type=prop_type,
        config=config,
    )


# ==============================================================================
# Schema Creation and Analysis
# ==============================================================================


def create_database_schema(
    database: NotionDatabase, data_source_id: Optional[str] = None
) -> DatabaseSchema:
    """
    Create DatabaseSchema from NotionDatabase with analysis.

    Args:
        database: NotionDatabase instance
        data_source_id: Data source ID for querying (Notion API 2025-09-03)

    Returns:
        DatabaseSchema with analyzed structure
    """
    # Group properties by type
    properties_by_type = group_properties_by_type(database.properties)

    # Identify relation properties
    relation_properties = identify_relation_properties(database.properties)

    # Identify classification fields
    classification_fields = identify_classification_fields(database.properties)

    return DatabaseSchema(
        database=database,
        data_source_id=data_source_id,
        properties_by_type=properties_by_type,
        relation_properties=relation_properties,
        classification_fields=classification_fields,
    )


def group_properties_by_type(
    properties: Dict[str, NotionProperty],
) -> Dict[str, List[NotionProperty]]:
    """
    Group properties by their type.

    Args:
        properties: Dictionary of properties

    Returns:
        Dictionary mapping type to list of properties
    """
    grouped: Dict[str, List[NotionProperty]] = {}

    for prop in properties.values():
        if prop.type not in grouped:
            grouped[prop.type] = []
        grouped[prop.type].append(prop)

    return grouped


def identify_relation_properties(
    properties: Dict[str, NotionProperty],
) -> List[NotionProperty]:
    """
    Identify all relation properties in database.

    Args:
        properties: Dictionary of properties

    Returns:
        List of relation properties
    """
    return [prop for prop in properties.values() if prop.type == "relation"]


def identify_classification_fields(
    properties: Dict[str, NotionProperty],
) -> Dict[str, str]:
    """
    Identify classification fields (Shinsegae affiliates?, Is Portfolio?).

    Args:
        properties: Dictionary of properties

    Returns:
        Dictionary mapping classification keys to property IDs
    """
    classification = {}

    for prop in properties.values():
        # Check for Shinsegae affiliate field (case-insensitive)
        if prop.name.lower() == "shinsegae affiliates?" and prop.type == "checkbox":
            classification["is_shinsegae_affiliate"] = prop.id

        # Check for Portfolio field (case-insensitive)
        if prop.name.lower() == "is portfolio?" and prop.type == "checkbox":
            classification["is_portfolio_company"] = prop.id

    return classification


# ==============================================================================
# Relationship Graph Building
# ==============================================================================


def build_relationship_graph(schemas: Dict[str, DatabaseSchema]) -> RelationshipGraph:
    """
    Build relationship graph from multiple database schemas.

    Args:
        schemas: Dictionary mapping database ID to DatabaseSchema

    Returns:
        RelationshipGraph showing all relationships

    Raises:
        SchemaValidationError: If invalid relationships detected
    """
    databases = {db_id: schema.database for db_id, schema in schemas.items()}
    relationships: List[Relationship] = []
    adjacency_list: Dict[str, List[str]] = {db_id: [] for db_id in databases}

    # Extract relationships from all databases
    for db_id, schema in schemas.items():
        for rel_prop in schema.relation_properties:
            # Get target database ID from relation config
            rel_config = rel_prop.config.get("relation", {})
            target_db_id = rel_config.get("database_id")

            if not target_db_id:
                logger.warning(
                    "Relation property missing target database",
                    extra={
                        "database_id": db_id,
                        "property_name": rel_prop.name,
                    },
                )
                continue

            # Check if bidirectional
            is_bidirectional = rel_config.get("type") == "dual_property"

            # Create relationship
            relationship = Relationship(
                source_db_id=db_id,
                source_property=rel_prop,
                target_db_id=target_db_id,
                is_bidirectional=is_bidirectional,
            )
            relationships.append(relationship)

            # Update adjacency list
            if target_db_id not in adjacency_list[db_id]:
                adjacency_list[db_id].append(target_db_id)

    return RelationshipGraph(
        databases=databases,
        relationships=relationships,
        adjacency_list=adjacency_list,
    )


# ==============================================================================
# Schema Validation
# ==============================================================================


def validate_schema(schema: DatabaseSchema) -> None:
    """
    Validate database schema for completeness and correctness.

    Args:
        schema: DatabaseSchema to validate

    Raises:
        SchemaValidationError: If schema is invalid
    """
    errors = []

    # Check database has properties
    if schema.property_count == 0:
        errors.append("Database has no properties")

    # Check for title property
    if "title" not in schema.properties_by_type:
        errors.append("Database missing title property")

    # Validate relation properties have target database
    for rel_prop in schema.relation_properties:
        rel_config = rel_prop.config.get("relation", {})
        if "database_id" not in rel_config:
            errors.append(
                f"Relation property '{rel_prop.name}' missing target database_id"
            )

    # Validate classification fields are checkboxes
    checkbox_props = {
        prop.id: prop for prop in schema.properties_by_type.get("checkbox", [])
    }

    for classification_key, prop_id in schema.classification_fields.items():
        if prop_id not in checkbox_props:
            errors.append(
                f"Classification field '{classification_key}' (ID: {prop_id}) is not a checkbox property"
            )

    if errors:
        raise SchemaValidationError(
            database_id=schema.database.id,
            message="Schema validation failed",
            validation_errors=errors,
        )

    logger.debug(
        "Schema validation passed",
        extra={
            "database_id": schema.database.id,
            "database_name": schema.database.title,
        },
    )
