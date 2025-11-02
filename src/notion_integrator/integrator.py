"""
NotionIntegrator - High-Level API

Orchestrates all Notion operations with a clean, simple interface:
- Schema discovery with caching
- Data fetching with pagination and relationships
- LLM-ready formatting
- Error handling and retry logic
- Cache management

Example Usage:
    >>> integrator = NotionIntegrator(api_key="secret_...")
    >>>
    >>> # Get complete formatted data
    >>> data = await integrator.get_data(
    ...     companies_db_id="abc123",
    ...     collabiq_db_id="xyz789"
    ... )
    >>> print(data.summary_markdown)
    >>>
    >>> # Manual cache refresh
    >>> await integrator.refresh_cache(companies_db_id="abc123")
"""

from typing import Any, Dict, List, Optional

from src.notion_integrator.cache import CacheManager
from src.notion_integrator.client import NotionClient
from src.notion_integrator.fetcher import (
    fetch_database_with_relationships,
    fetch_multiple_databases,
)
from src.notion_integrator.formatter import format_for_llm, format_multiple_databases
from src.notion_integrator.logging_config import get_logger, PerformanceLogger
from src.notion_integrator.models import DatabaseSchema, LLMFormattedData
from src.notion_integrator.schema import discover_schema


logger = get_logger(__name__)


class NotionIntegrator:
    """
    High-level API for Notion integration.

    Orchestrates schema discovery, data fetching, formatting, and caching
    with a simple interface. Handles errors gracefully and provides
    comprehensive logging.

    Attributes:
        client: NotionClient instance
        cache_manager: CacheManager instance
        default_max_depth: Default relationship depth (1)
        use_cache: Whether to use caching (True)

    Example:
        >>> integrator = NotionIntegrator(api_key="secret_...")
        >>> data = await integrator.get_data(
        ...     companies_db_id="abc123",
        ...     collabiq_db_id="xyz789"
        ... )
        >>> print(f"Found {data.metadata.total_companies} companies")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_per_second: float = 3.0,
        cache_dir: Optional[str] = None,
        schema_ttl_hours: int = 24,
        data_ttl_hours: int = 6,
        use_cache: bool = True,
        default_max_depth: int = 1,
    ):
        """
        Initialize NotionIntegrator.

        Args:
            api_key: Notion API key (defaults to NOTION_API_KEY env var)
            rate_per_second: API rate limit (default: 3.0)
            cache_dir: Cache directory (defaults to NOTION_CACHE_DIR env var)
            schema_ttl_hours: Schema cache TTL in hours (default: 24)
            data_ttl_hours: Data cache TTL in hours (default: 6)
            use_cache: Whether to use caching (default: True)
            default_max_depth: Default relationship depth (default: 1)

        Raises:
            NotionAuthenticationError: If API key is missing/invalid
        """
        # Initialize client
        self.client = NotionClient(api_key=api_key, rate_per_second=rate_per_second)

        # Initialize cache manager
        self.cache_manager = CacheManager(
            cache_dir=cache_dir,
            schema_ttl_hours=schema_ttl_hours,
            data_ttl_hours=data_ttl_hours,
        )

        # Configuration
        self.use_cache = use_cache
        self.default_max_depth = default_max_depth

        logger.info(
            "NotionIntegrator initialized",
            extra={
                "rate_per_second": rate_per_second,
                "use_cache": use_cache,
                "default_max_depth": default_max_depth,
            },
        )

    async def discover_database_schema(
        self,
        database_id: str,
        use_cache: Optional[bool] = None,
    ) -> DatabaseSchema:
        """
        Discover schema from a Notion database.

        Args:
            database_id: Database ID to discover
            use_cache: Whether to use cache (defaults to instance setting)

        Returns:
            DatabaseSchema with complete structure

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Database not found
            NotionPermissionError: Insufficient permissions
            SchemaValidationError: Invalid schema structure
        """
        use_cache_flag = use_cache if use_cache is not None else self.use_cache

        return await discover_schema(
            client=self.client,
            database_id=database_id,
            cache_manager=self.cache_manager if use_cache_flag else None,
            use_cache=use_cache_flag,
        )

    async def fetch_all_records(
        self,
        database_id: str,
        schema: Optional[DatabaseSchema] = None,
        max_relationship_depth: Optional[int] = None,
        use_cache: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all records from a database with relationships.

        Args:
            database_id: Database ID to fetch
            schema: DatabaseSchema (will discover if not provided)
            max_relationship_depth: Max depth for relationships (defaults to instance setting)
            use_cache: Whether to use cache (defaults to instance setting)

        Returns:
            List of records with resolved relationships

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Database not found
            NotionPermissionError: Insufficient permissions
            NotionAPIError: Other API errors
        """
        # Discover schema if not provided
        if schema is None:
            schema = await self.discover_database_schema(
                database_id=database_id,
                use_cache=use_cache,
            )

        # Use instance defaults if not specified
        use_cache_flag = use_cache if use_cache is not None else self.use_cache
        max_depth = (
            max_relationship_depth
            if max_relationship_depth is not None
            else self.default_max_depth
        )

        # Fetch records
        return await fetch_database_with_relationships(
            client=self.client,
            database_id=database_id,
            schema=schema,
            max_relationship_depth=max_depth,
            cache_manager=self.cache_manager if use_cache_flag else None,
            use_cache=use_cache_flag,
        )

    async def format_for_llm(
        self,
        database_id: str,
        records: Optional[List[Dict[str, Any]]] = None,
        schema: Optional[DatabaseSchema] = None,
        max_relationship_depth: Optional[int] = None,
        use_cache: Optional[bool] = None,
    ) -> LLMFormattedData:
        """
        Format database records for LLM consumption.

        Args:
            database_id: Database ID
            records: Records to format (will fetch if not provided)
            schema: DatabaseSchema (will discover if not provided)
            max_relationship_depth: Max depth for relationships (defaults to instance setting)
            use_cache: Whether to use cache (defaults to instance setting)

        Returns:
            LLMFormattedData with JSON + Markdown

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Database not found
            NotionPermissionError: Insufficient permissions
            NotionAPIError: Other API errors
        """
        # Discover schema if not provided
        if schema is None:
            schema = await self.discover_database_schema(
                database_id=database_id,
                use_cache=use_cache,
            )

        # Fetch records if not provided
        if records is None:
            records = await self.fetch_all_records(
                database_id=database_id,
                schema=schema,
                max_relationship_depth=max_relationship_depth,
                use_cache=use_cache,
            )

        # Format for LLM
        return format_for_llm(records, schema)

    async def get_data(
        self,
        companies_db_id: str,
        collabiq_db_id: Optional[str] = None,
        max_relationship_depth: Optional[int] = None,
        use_cache: Optional[bool] = None,
    ) -> LLMFormattedData:
        """
        Get complete formatted data from Notion databases.

        High-level method that orchestrates:
        1. Schema discovery (with caching)
        2. Data fetching (with pagination & relationships)
        3. LLM formatting (JSON + Markdown)

        Args:
            companies_db_id: Companies database ID
            collabiq_db_id: Optional CollabIQ database ID
            max_relationship_depth: Max depth for relationships (defaults to instance setting)
            use_cache: Whether to use cache (defaults to instance setting)

        Returns:
            LLMFormattedData with complete formatted dataset

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Database not found
            NotionPermissionError: Insufficient permissions
            NotionAPIError: Other API errors

        Example:
            >>> data = await integrator.get_data(
            ...     companies_db_id="abc123",
            ...     collabiq_db_id="xyz789"
            ... )
            >>> print(data.summary_markdown)
            >>> for company in data.companies:
            ...     print(f"- {company.name}: {company.classification.collaboration_type_hint}")
        """
        with PerformanceLogger(
            logger,
            "get_data",
            companies_db_id=companies_db_id,
            collabiq_db_id=collabiq_db_id,
        ):
            # Determine database IDs to fetch
            database_ids = [companies_db_id]
            if collabiq_db_id:
                database_ids.append(collabiq_db_id)

            # Discover schemas
            logger.info(
                "Discovering schemas",
                extra={"database_count": len(database_ids)},
            )

            schemas = {}
            for db_id in database_ids:
                schema = await self.discover_database_schema(
                    database_id=db_id,
                    use_cache=use_cache,
                )
                schemas[db_id] = schema

            # Fetch data from all databases
            logger.info(
                "Fetching data from databases",
                extra={"database_count": len(database_ids)},
            )

            use_cache_flag = use_cache if use_cache is not None else self.use_cache
            max_depth = (
                max_relationship_depth
                if max_relationship_depth is not None
                else self.default_max_depth
            )

            data_by_database = await fetch_multiple_databases(
                client=self.client,
                schemas=schemas,
                max_relationship_depth=max_depth,
                cache_manager=self.cache_manager if use_cache_flag else None,
                use_cache=use_cache_flag,
            )

            # Format data
            logger.info(
                "Formatting data for LLM",
                extra={"database_count": len(data_by_database)},
            )

            formatted_data_by_db = format_multiple_databases(
                data_by_database=data_by_database,
                schemas=schemas,
            )

            # Return primary database's formatted data
            # If both databases provided, combine them (future enhancement)
            primary_db_id = companies_db_id
            formatted_data = formatted_data_by_db[primary_db_id]

            logger.info(
                "Data retrieval and formatting complete",
                extra={
                    "total_companies": formatted_data.metadata.total_companies,
                    "ssg_count": formatted_data.metadata.shinsegae_affiliate_count,
                    "portfolio_count": formatted_data.metadata.portfolio_company_count,
                },
            )

            return formatted_data

    async def refresh_cache(
        self,
        database_id: str,
        refresh_schema: bool = True,
        refresh_data: bool = True,
    ) -> None:
        """
        Manually refresh cache for a database.

        Invalidates existing cache and forces fresh fetch from API.

        Args:
            database_id: Database ID to refresh
            refresh_schema: Whether to refresh schema cache (default: True)
            refresh_data: Whether to refresh data cache (default: True)

        Example:
            >>> # Force refresh both schema and data
            >>> await integrator.refresh_cache(database_id="abc123")
            >>>
            >>> # Refresh only data cache
            >>> await integrator.refresh_cache(database_id="abc123", refresh_schema=False)
        """
        logger.info(
            "Refreshing cache",
            extra={
                "database_id": database_id,
                "refresh_schema": refresh_schema,
                "refresh_data": refresh_data,
            },
        )

        # Get database name for cache operations
        schema = await self.discover_database_schema(
            database_id=database_id,
            use_cache=False,  # Force fresh fetch
        )

        database_name = schema.database.title

        # Invalidate caches
        if refresh_schema:
            self.cache_manager.invalidate_schema_cache(database_name)
            logger.info(
                "Schema cache invalidated", extra={"database_name": database_name}
            )

        if refresh_data:
            self.cache_manager.invalidate_data_cache(database_name)
            logger.info(
                "Data cache invalidated", extra={"database_name": database_name}
            )

    async def close(self):
        """Close the Notion client and clean up resources."""
        await self.client.close()
        logger.info("NotionIntegrator closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
