"""
Companies Cache Management

Provides caching of Companies database entries for fuzzy matching.
Maintains a list of (page_id, company_name) tuples with TTL-based refresh.

Key Features:
- Fetch all companies from Notion Companies database
- Store in data/notion_cache/companies_list.json
- 6-hour TTL (same as data cache)
- Delta refresh support (invalidate when needed)
- Thread-safe for concurrent access

Usage:
    >>> cache = CompaniesCache(notion_integrator, companies_db_id)
    >>> candidates = await cache.get_companies()
    >>> # [(page_id, name), (page_id, name), ...]
    >>> await cache.refresh()  # Force refresh
"""

from typing import List, Optional, Tuple

from .cache import CacheManager
from .client import NotionClient
from .exceptions import NotionAPIError
from .fetcher import fetch_all_records
from .logging_config import get_logger, PerformanceLogger


logger = get_logger(__name__)


class CompaniesCache:
    """
    Manages caching of Companies database entries for fuzzy matching.

    Provides a list of (page_id, company_name) tuples that can be used
    as candidates for the fuzzy matcher. Handles caching with TTL and
    provides manual refresh capability.

    Attributes:
        client: NotionClient instance for API access
        companies_db_id: Companies database ID
        cache_manager: CacheManager for file-based caching
        ttl_hours: Cache TTL in hours (default: 6)
    """

    def __init__(
        self,
        client: NotionClient,
        companies_db_id: str,
        cache_manager: Optional[CacheManager] = None,
        ttl_hours: int = 6,
    ):
        """
        Initialize CompaniesCache.

        Args:
            client: NotionClient instance
            companies_db_id: Companies database ID
            cache_manager: Optional CacheManager (creates new if not provided)
            ttl_hours: Cache TTL in hours (default: 6)
        """
        self.client = client
        self.companies_db_id = companies_db_id
        self.cache_manager = cache_manager or CacheManager(data_ttl_hours=ttl_hours)
        self.ttl_hours = ttl_hours

        logger.info(
            "CompaniesCache initialized",
            extra={
                "companies_db_id": companies_db_id,
                "ttl_hours": ttl_hours,
            },
        )

    async def get_companies(
        self,
        use_cache: bool = True,
    ) -> List[Tuple[str, str]]:
        """
        Get list of companies as (page_id, company_name) tuples.

        Checks cache first. If cache is invalid or use_cache=False,
        fetches from Notion API and updates cache.

        Args:
            use_cache: Whether to use cached data (default: True)

        Returns:
            List of (page_id, company_name) tuples

        Raises:
            NotionAPIError: If API fetch fails

        Example:
            >>> candidates = await cache.get_companies()
            >>> # [("abc123...", "웨이크"), ("xyz789...", "네트워크")]
        """
        with PerformanceLogger(
            logger,
            "get_companies",
            companies_db_id=self.companies_db_id,
        ):
            # Try cache first
            if use_cache:
                cached_companies = self._get_from_cache()
                if cached_companies is not None:
                    logger.info(
                        "Companies loaded from cache",
                        extra={
                            "companies_db_id": self.companies_db_id,
                            "company_count": len(cached_companies),
                        },
                    )
                    return cached_companies

            # Cache miss - fetch from API
            logger.info(
                "Fetching companies from Notion API",
                extra={"companies_db_id": self.companies_db_id},
            )

            companies = await self._fetch_from_api()

            # Update cache
            if use_cache:
                self._save_to_cache(companies)

            logger.info(
                "Companies fetched and cached",
                extra={
                    "companies_db_id": self.companies_db_id,
                    "company_count": len(companies),
                },
            )

            return companies

    async def refresh(self) -> List[Tuple[str, str]]:
        """
        Force refresh of companies cache from Notion API.

        Invalidates existing cache and fetches fresh data.

        Returns:
            List of (page_id, company_name) tuples

        Raises:
            NotionAPIError: If API fetch fails

        Example:
            >>> # Force refresh after creating new company
            >>> await cache.refresh()
        """
        logger.info(
            "Refreshing companies cache",
            extra={"companies_db_id": self.companies_db_id},
        )

        # Invalidate cache
        self.cache_manager.invalidate_data_cache("Companies")

        # Fetch fresh data
        return await self.get_companies(use_cache=False)

    def invalidate_cache(self) -> None:
        """
        Invalidate companies cache without fetching new data.

        Use this when you know the cache is stale but don't need
        the data immediately (e.g., after creating a company but
        not using it right away).

        Example:
            >>> # After creating company, invalidate for next fetch
            >>> cache.invalidate_cache()
        """
        logger.info(
            "Invalidating companies cache",
            extra={"companies_db_id": self.companies_db_id},
        )
        self.cache_manager.invalidate_data_cache("Companies")

    async def _fetch_from_api(self) -> List[Tuple[str, str]]:
        """
        Fetch all companies from Notion API.

        Returns:
            List of (page_id, company_name) tuples

        Raises:
            NotionAPIError: If API fetch fails
        """
        try:
            # Fetch all records from Companies database
            records = await fetch_all_records(
                client=self.client,
                database_id=self.companies_db_id,
            )

            # Extract (page_id, name) tuples
            companies = []
            for record in records:
                page_id = record.get("id")
                if not page_id:
                    continue

                # Extract company name from title property
                # Companies database uses "Name" as title property
                properties = record.get("properties", {})
                name_prop = properties.get("Name", {})

                # Handle title property format
                if name_prop.get("type") == "title":
                    title_array = name_prop.get("title", [])
                    if title_array and len(title_array) > 0:
                        company_name = title_array[0].get("text", {}).get("content", "")
                        if company_name:
                            companies.append((page_id, company_name))

            logger.info(
                "Companies fetched from API",
                extra={
                    "companies_db_id": self.companies_db_id,
                    "total_records": len(records),
                    "valid_companies": len(companies),
                },
            )

            return companies

        except Exception as e:
            logger.error(
                "Failed to fetch companies from API",
                extra={
                    "companies_db_id": self.companies_db_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise NotionAPIError(
                message=f"Failed to fetch companies: {e}",
                status_code=None,
                notion_code=None,
            )

    def _get_from_cache(self) -> Optional[List[Tuple[str, str]]]:
        """
        Get companies from cache if valid.

        Returns:
            List of (page_id, company_name) tuples or None if cache invalid
        """
        try:
            # Use existing CacheManager infrastructure
            cached_data = self.cache_manager.get_data_cache(
                database_id=self.companies_db_id,
                database_name="Companies",
            )

            if not cached_data:
                return None

            # Validate format: list of {page_id, name} dicts
            if not isinstance(cached_data, list):
                logger.warning(
                    "Invalid cache format (not a list)",
                    extra={"companies_db_id": self.companies_db_id},
                )
                return None

            # Convert from cache format to tuple format
            companies = []
            for item in cached_data:
                if isinstance(item, dict):
                    page_id = item.get("page_id")
                    name = item.get("name")
                    if page_id and name:
                        companies.append((page_id, name))

            if not companies:
                logger.warning(
                    "Cache contains no valid companies",
                    extra={"companies_db_id": self.companies_db_id},
                )
                return None

            return companies

        except Exception as e:
            logger.warning(
                "Error reading companies from cache",
                extra={
                    "companies_db_id": self.companies_db_id,
                    "error": str(e),
                },
            )
            return None

    def _save_to_cache(self, companies: List[Tuple[str, str]]) -> None:
        """
        Save companies to cache.

        Args:
            companies: List of (page_id, company_name) tuples
        """
        try:
            # Convert to cache format: list of {page_id, name} dicts
            cache_data = [
                {"page_id": page_id, "name": name} for page_id, name in companies
            ]

            # Use existing CacheManager infrastructure
            self.cache_manager.set_data_cache(
                database_id=self.companies_db_id,
                database_name="Companies",
                records=cache_data,
            )

            logger.info(
                "Companies saved to cache",
                extra={
                    "companies_db_id": self.companies_db_id,
                    "company_count": len(companies),
                },
            )

        except Exception as e:
            logger.warning(
                "Failed to save companies to cache",
                extra={
                    "companies_db_id": self.companies_db_id,
                    "error": str(e),
                },
            )
            # Don't raise - cache write failure is not critical
