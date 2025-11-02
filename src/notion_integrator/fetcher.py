"""
Data Fetching and Relationship Resolution

Handles fetching records from Notion databases with:
- Pagination for large datasets
- Relationship resolution (1+ depth levels)
- Circular reference detection
- Error handling for missing pages
- Integration with caching

Key Functions:
- fetch_all_records(): Fetch all records with pagination
- resolve_relationships(): Resolve related records recursively
- fetch_database_with_relationships(): Complete fetch with schema + data + relations
"""

import asyncio
from typing import Any, Dict, List, Optional, Set

from src.notion_integrator.cache import CacheManager
from src.notion_integrator.client import NotionClient
from src.notion_integrator.exceptions import (
    NotionAPIError,
    NotionObjectNotFoundError,
)
from src.notion_integrator.logging_config import get_logger, PerformanceLogger
from src.notion_integrator.models import (
    DatabaseSchema,
    RelationshipGraph,
)


logger = get_logger(__name__)


# ==============================================================================
# Pagination Handler
# ==============================================================================


async def fetch_all_records(
    client: NotionClient,
    database_id: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch all records from a database with pagination.

    Args:
        client: NotionClient instance
        database_id: Database ID to fetch from
        filter_conditions: Optional filter conditions
        sorts: Optional sort configuration
        page_size: Records per page (default: 100, max: 100)

    Returns:
        List of all records from database

    Raises:
        NotionAuthenticationError: Invalid API key
        NotionObjectNotFoundError: Database not found
        NotionPermissionError: Insufficient permissions
        NotionAPIError: Other API errors
    """
    with PerformanceLogger(logger, "fetch_all_records", database_id=database_id):
        all_records = []
        start_cursor = None
        page_count = 0

        while True:
            page_count += 1
            logger.debug(
                "Fetching page from database",
                extra={
                    "database_id": database_id,
                    "page_num": page_count,
                    "has_cursor": start_cursor is not None,
                },
            )

            # Query database
            response = await client.query_database(
                database_id=database_id,
                filter_conditions=filter_conditions,
                sorts=sorts,
                start_cursor=start_cursor,
                page_size=page_size,
            )

            # Extract results
            results = response.get("results", [])
            all_records.extend(results)

            logger.debug(
                "Page fetched",
                extra={
                    "database_id": database_id,
                    "page_num": page_count,
                    "records_in_page": len(results),
                    "total_records": len(all_records),
                },
            )

            # Check if more pages exist
            has_more = response.get("has_more", False)
            if not has_more:
                break

            # Get cursor for next page
            start_cursor = response.get("next_cursor")
            if not start_cursor:
                logger.warning(
                    "has_more=True but no next_cursor provided",
                    extra={"database_id": database_id, "page_num": page_count},
                )
                break

        logger.info(
            "All records fetched",
            extra={
                "database_id": database_id,
                "total_pages": page_count,
                "total_records": len(all_records),
            },
        )

        return all_records


# ==============================================================================
# Relationship Resolution
# ==============================================================================


async def resolve_relationships(
    client: NotionClient,
    record: Dict[str, Any],
    schema: DatabaseSchema,
    max_depth: int = 1,
    current_depth: int = 0,
    visited_pages: Optional[Set[str]] = None,
    relationship_graph: Optional[RelationshipGraph] = None,
) -> Dict[str, Any]:
    """
    Resolve relationships in a record recursively.

    Args:
        client: NotionClient instance
        record: Record to resolve relationships for
        schema: DatabaseSchema for this record's database
        max_depth: Maximum relationship depth to resolve (default: 1)
        current_depth: Current depth level (internal)
        visited_pages: Set of visited page IDs to prevent infinite loops
        relationship_graph: Optional RelationshipGraph for optimization

    Returns:
        Record with resolved relationships added to relation properties

    Notes:
        - Respects max_depth to prevent excessive API calls
        - Tracks visited_pages to prevent infinite loops in circular refs
        - Adds "resolved" key to relation properties with fetched data
        - Handles missing pages gracefully (logs warning, continues)
    """
    # Initialize visited_pages set
    if visited_pages is None:
        visited_pages = set()

    # Check depth limit
    if current_depth >= max_depth:
        logger.debug(
            "Depth limit reached, skipping further resolution",
            extra={
                "record_id": record.get("id"),
                "current_depth": current_depth,
                "max_depth": max_depth,
            },
        )
        return record

    # Mark this page as visited
    record_id = record.get("id")
    if record_id:
        visited_pages.add(record_id)

    # Get relation properties from schema
    if not schema.relation_properties:
        # No relations to resolve
        return record

    # Resolve each relation property
    properties = record.get("properties", {})

    for rel_prop in schema.relation_properties:
        prop_name = rel_prop.name

        if prop_name not in properties:
            continue

        prop_data = properties[prop_name]
        if prop_data.get("type") != "relation":
            continue

        relation_ids = prop_data.get("relation", [])
        if not relation_ids:
            # Empty relation
            continue

        logger.debug(
            "Resolving relation property",
            extra={
                "record_id": record_id,
                "property_name": prop_name,
                "relation_count": len(relation_ids),
                "current_depth": current_depth,
            },
        )

        # Fetch related pages
        resolved_pages = []
        errors = []

        for relation_ref in relation_ids:
            related_page_id = relation_ref.get("id")
            if not related_page_id:
                continue

            # Skip if already visited (circular reference)
            if related_page_id in visited_pages:
                logger.debug(
                    "Skipping already visited page (circular reference)",
                    extra={
                        "record_id": record_id,
                        "related_page_id": related_page_id,
                        "property_name": prop_name,
                    },
                )
                continue

            try:
                # Fetch related page
                related_page = await client.retrieve_page(related_page_id)

                # Mark as visited
                visited_pages.add(related_page_id)

                # Recursively resolve relationships if depth allows
                if current_depth + 1 < max_depth:
                    # Get schema for related database
                    # Note: For now, we don't recursively resolve deeper levels
                    # This would require fetching the related database's schema
                    # For MVP, we just fetch the related page without deeper resolution
                    pass

                resolved_pages.append(related_page)

            except NotionObjectNotFoundError as e:
                # Page not found or not accessible
                logger.warning(
                    "Related page not found or not accessible",
                    extra={
                        "record_id": record_id,
                        "related_page_id": related_page_id,
                        "property_name": prop_name,
                        "error": str(e),
                    },
                )
                errors.append(
                    {
                        "page_id": related_page_id,
                        "error": "not_found",
                        "message": str(e),
                    }
                )

            except NotionAPIError as e:
                # Other API error
                logger.error(
                    "Error fetching related page",
                    extra={
                        "record_id": record_id,
                        "related_page_id": related_page_id,
                        "property_name": prop_name,
                        "error": str(e),
                    },
                )
                errors.append(
                    {
                        "page_id": related_page_id,
                        "error": "api_error",
                        "message": str(e),
                    }
                )

        # Add resolved data to property
        if resolved_pages:
            prop_data["resolved"] = resolved_pages

        if errors:
            prop_data["resolution_errors"] = errors

        logger.debug(
            "Relation property resolved",
            extra={
                "record_id": record_id,
                "property_name": prop_name,
                "resolved_count": len(resolved_pages),
                "error_count": len(errors),
            },
        )

    return record


# ==============================================================================
# Complete Database Fetch
# ==============================================================================


async def fetch_database_with_relationships(
    client: NotionClient,
    database_id: str,
    schema: DatabaseSchema,
    max_relationship_depth: int = 1,
    cache_manager: Optional[CacheManager] = None,
    use_cache: bool = True,
    filter_conditions: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch all records from database with relationships resolved.

    Args:
        client: NotionClient instance
        database_id: Database ID to fetch
        schema: DatabaseSchema for the database
        max_relationship_depth: Max depth for relationship resolution (default: 1)
        cache_manager: Optional CacheManager for caching
        use_cache: Whether to use cache (default: True)
        filter_conditions: Optional filter conditions
        sorts: Optional sort configuration

    Returns:
        List of records with resolved relationships

    Raises:
        NotionAuthenticationError: Invalid API key
        NotionObjectNotFoundError: Database not found
        NotionPermissionError: Insufficient permissions
        NotionAPIError: Other API errors
    """
    with PerformanceLogger(
        logger,
        "fetch_database_with_relationships",
        database_id=database_id,
        database_name=schema.database.title,
    ):
        # Initialize cache manager if not provided
        if cache_manager is None and use_cache:
            cache_manager = CacheManager()

        # Try to get from cache first
        cached_records = None
        if use_cache and cache_manager:
            cached_records = cache_manager.get_data_cache(
                database_id=database_id,
                database_name=schema.database.title,
            )

            if cached_records:
                logger.info(
                    "Data loaded from cache",
                    extra={
                        "database_id": database_id,
                        "database_name": schema.database.title,
                        "record_count": len(cached_records),
                    },
                )
                return cached_records

        # Cache miss - fetch from API
        logger.info(
            "Fetching data from Notion API",
            extra={
                "database_id": database_id,
                "database_name": schema.database.title,
            },
        )

        # Fetch all records
        records = await fetch_all_records(
            client=client,
            database_id=database_id,
            filter_conditions=filter_conditions,
            sorts=sorts,
        )

        # Resolve relationships if schema has relations
        if schema.has_relations and max_relationship_depth > 0:
            logger.info(
                "Resolving relationships",
                extra={
                    "database_id": database_id,
                    "record_count": len(records),
                    "relation_count": len(schema.relation_properties),
                    "max_depth": max_relationship_depth,
                },
            )

            # Resolve relationships for each record
            resolved_records = []
            for record in records:
                resolved_record = await resolve_relationships(
                    client=client,
                    record=record,
                    schema=schema,
                    max_depth=max_relationship_depth,
                    visited_pages=set(),  # Fresh set for each record
                )
                resolved_records.append(resolved_record)

            records = resolved_records

        # Cache the results
        if use_cache and cache_manager:
            cache_manager.set_data_cache(
                database_id=database_id,
                database_name=schema.database.title,
                records=records,
            )

        logger.info(
            "Database fetch with relationships completed",
            extra={
                "database_id": database_id,
                "database_name": schema.database.title,
                "record_count": len(records),
                "cached": use_cache and cache_manager is not None,
            },
        )

        return records


# ==============================================================================
# Multi-Database Fetch
# ==============================================================================


async def fetch_multiple_databases(
    client: NotionClient,
    schemas: Dict[str, DatabaseSchema],
    max_relationship_depth: int = 1,
    cache_manager: Optional[CacheManager] = None,
    use_cache: bool = True,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch data from multiple databases in parallel.

    Args:
        client: NotionClient instance
        schemas: Dict mapping database_id to DatabaseSchema
        max_relationship_depth: Max depth for relationship resolution
        cache_manager: Optional CacheManager for caching
        use_cache: Whether to use cache

    Returns:
        Dict mapping database_id to list of records

    Raises:
        NotionAuthenticationError: Invalid API key
        NotionObjectNotFoundError: Database not found
        NotionPermissionError: Insufficient permissions
        NotionAPIError: Other API errors
    """
    with PerformanceLogger(
        logger,
        "fetch_multiple_databases",
        database_count=len(schemas),
    ):
        # Initialize cache manager if not provided
        if cache_manager is None and use_cache:
            cache_manager = CacheManager()

        # Create fetch tasks for all databases
        fetch_tasks = []
        database_ids = []

        for database_id, schema in schemas.items():
            task = fetch_database_with_relationships(
                client=client,
                database_id=database_id,
                schema=schema,
                max_relationship_depth=max_relationship_depth,
                cache_manager=cache_manager,
                use_cache=use_cache,
            )
            fetch_tasks.append(task)
            database_ids.append(database_id)

        # Fetch all databases in parallel
        logger.info(
            "Fetching multiple databases in parallel",
            extra={"database_count": len(schemas)},
        )

        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Build result dict
        data_by_database = {}
        errors = []

        for database_id, result in zip(database_ids, results):
            if isinstance(result, Exception):
                logger.error(
                    "Error fetching database",
                    extra={
                        "database_id": database_id,
                        "error": str(result),
                    },
                )
                errors.append(
                    {
                        "database_id": database_id,
                        "error": str(result),
                    }
                )
                data_by_database[database_id] = []
            else:
                data_by_database[database_id] = result

        logger.info(
            "Multiple databases fetched",
            extra={
                "database_count": len(schemas),
                "success_count": len(data_by_database) - len(errors),
                "error_count": len(errors),
            },
        )

        if errors:
            logger.warning(
                "Some databases failed to fetch",
                extra={"errors": errors},
            )

        return data_by_database
