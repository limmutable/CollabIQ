"""
Notion Client Wrapper

Wraps the official Notion Python SDK with:
- Rate limiting (3 req/sec via token bucket)
- Error handling and translation to custom exceptions
- Logging for all API calls
- Retry logic for transient failures

This is the main entry point for all Notion API interactions.

MIGRATION NOTE (2024-11-02):
Migrated to Notion API version 2025-09-03 which introduced data sources.
- Databases no longer have properties directly
- Properties are now on data sources (databases can have multiple data sources)
- query_database() now retrieves database -> data source -> queries data source
- retrieve_data_source() added for accessing data source metadata
See: https://developers.notion.com/docs/upgrade-guide-2025-09-03
"""

import os
from typing import Any, Dict, Optional

from notion_client import AsyncClient
from notion_client.errors import APIResponseError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    NotionAPIError,
    NotionAuthenticationError,
    NotionObjectNotFoundError,
    NotionPermissionError,
    NotionRateLimitError,
)
from .logging_config import get_logger, log_api_call
from .rate_limiter import RateLimiter


logger = get_logger(__name__)


class NotionClient:
    """
    Wrapper around Notion AsyncClient with rate limiting and error handling.

    Attributes:
        client: Notion AsyncClient instance
        rate_limiter: Rate limiter for API calls
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_per_second: float = 3.0,
    ):
        """
        Initialize Notion client wrapper.

        Args:
            api_key: Notion API key (defaults to NOTION_API_KEY env var)
            rate_per_second: Maximum API calls per second (default: 3.0)

        Raises:
            NotionAuthenticationError: If API key is missing
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("NOTION_API_KEY")

        if not self.api_key:
            raise NotionAuthenticationError(
                "Notion API key not provided. Set NOTION_API_KEY environment variable or pass api_key parameter.",
                details={"suggestion": "export NOTION_API_KEY=secret_..."},
            )

        # Initialize Notion client
        self.client = AsyncClient(auth=self.api_key)

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(rate_per_second=rate_per_second)

        logger.info(
            "Notion client initialized",
            extra={"rate_limit_per_sec": rate_per_second},
        )

    async def retrieve_database(self, database_id: str) -> Dict[str, Any]:
        """
        Retrieve database metadata and schema.

        Args:
            database_id: Notion database ID

        Returns:
            Database object from Notion API

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Database not found or not shared
            NotionPermissionError: Insufficient permissions
            NotionRateLimitError: Rate limit exceeded
            NotionAPIError: Other API errors
        """
        log_api_call(logger, "databases.retrieve", database_id=database_id)

        async with self.rate_limiter:
            try:
                response = await self._retrieve_database_with_retry(database_id)
                return response
            except APIResponseError as e:
                raise self._translate_api_error(e, database_id=database_id)

    @retry(
        retry=retry_if_exception_type(APIResponseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _retrieve_database_with_retry(self, database_id: str) -> Dict[str, Any]:
        """
        Retrieve database with retry logic for transient failures.

        Args:
            database_id: Notion database ID

        Returns:
            Database object from Notion API

        Raises:
            APIResponseError: If all retries exhausted
        """
        return await self.client.databases.retrieve(database_id=database_id)

    async def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[list] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Query database for records.

        Note: Migrated to Notion API 2025-09-03 data sources model.
        This method retrieves the database's data source(s) and queries the first one.

        Args:
            database_id: Notion database ID
            filter_conditions: Filter conditions (optional)
            sorts: Sort configuration (optional)
            start_cursor: Pagination cursor (optional)
            page_size: Number of records per page (default: 100, max: 100)

        Returns:
            Query response with records and pagination info

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Database not found
            NotionPermissionError: Insufficient permissions
            NotionRateLimitError: Rate limit exceeded
            NotionAPIError: Other API errors
        """
        log_api_call(
            logger,
            "data_sources.query",
            database_id=database_id,
            page_size=page_size,
            has_cursor=start_cursor is not None,
        )

        async with self.rate_limiter:
            try:
                # First, get the database to retrieve data source IDs
                db = await self._retrieve_database_with_retry(database_id)
                data_sources = db.get("data_sources", [])

                if not data_sources:
                    raise NotionAPIError(
                        message=f"Database has no data sources (database_id={database_id})",
                        status_code=None,
                        response_body="No data sources found in database",
                        details={"database_id": database_id},
                    )

                # Query the first data source
                # TODO: In the future, we might need to query all data sources for multi-source databases
                data_source_id = data_sources[0]["id"]

                response = await self._query_data_source_with_retry(
                    data_source_id=data_source_id,
                    filter_conditions=filter_conditions,
                    sorts=sorts,
                    start_cursor=start_cursor,
                    page_size=page_size,
                )
                return response
            except APIResponseError as e:
                raise self._translate_api_error(e, database_id=database_id)

    @retry(
        retry=retry_if_exception_type(APIResponseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _query_data_source_with_retry(
        self,
        data_source_id: str,
        filter_conditions: Optional[Dict[str, Any]],
        sorts: Optional[list],
        start_cursor: Optional[str],
        page_size: int,
    ) -> Dict[str, Any]:
        """Query data source with retry logic (Notion API 2025-09-03)."""
        query_params = {
            "data_source_id": data_source_id,
            "page_size": page_size,
        }

        if filter_conditions:
            query_params["filter"] = filter_conditions
        if sorts:
            query_params["sorts"] = sorts
        if start_cursor:
            query_params["start_cursor"] = start_cursor

        return await self.client.data_sources.query(**query_params)

    async def retrieve_data_source(self, data_source_id: str) -> Dict[str, Any]:
        """
        Retrieve data source metadata and schema (Notion API 2025-09-03).

        Args:
            data_source_id: Notion data source ID

        Returns:
            Data source object from Notion API

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Data source not found or not shared
            NotionPermissionError: Insufficient permissions
            NotionRateLimitError: Rate limit exceeded
            NotionAPIError: Other API errors
        """
        log_api_call(logger, "data_sources.retrieve", data_source_id=data_source_id)

        async with self.rate_limiter:
            try:
                response = await self._retrieve_data_source_with_retry(data_source_id)
                return response
            except APIResponseError as e:
                raise self._translate_api_error(e)

    @retry(
        retry=retry_if_exception_type(APIResponseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _retrieve_data_source_with_retry(
        self, data_source_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve data source with retry logic for transient failures.

        Args:
            data_source_id: Notion data source ID

        Returns:
            Data source object from Notion API

        Raises:
            APIResponseError: If all retries exhausted
        """
        return await self.client.data_sources.retrieve(data_source_id=data_source_id)

    async def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve page/record by ID.

        Args:
            page_id: Notion page ID

        Returns:
            Page object from Notion API

        Raises:
            NotionAuthenticationError: Invalid API key
            NotionObjectNotFoundError: Page not found
            NotionPermissionError: Insufficient permissions
            NotionRateLimitError: Rate limit exceeded
            NotionAPIError: Other API errors
        """
        log_api_call(logger, "pages.retrieve", page_id=page_id)

        async with self.rate_limiter:
            try:
                response = await self._retrieve_page_with_retry(page_id)
                return response
            except APIResponseError as e:
                raise self._translate_api_error(e, page_id=page_id)

    @retry(
        retry=retry_if_exception_type(APIResponseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _retrieve_page_with_retry(self, page_id: str) -> Dict[str, Any]:
        """Retrieve page with retry logic."""
        return await self.client.pages.retrieve(page_id=page_id)

    def _translate_api_error(
        self,
        error: APIResponseError,
        database_id: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> Exception:
        """
        Translate Notion API errors to custom exceptions.

        Args:
            error: Notion API error
            database_id: Database ID if applicable
            page_id: Page ID if applicable

        Returns:
            Appropriate custom exception
        """
        status_code = error.code if hasattr(error, "code") else None
        response_status = error.status if hasattr(error, "status") else None
        message = str(error)

        details = {}
        if database_id:
            details["database_id"] = database_id
        if page_id:
            details["page_id"] = page_id

        # Map error codes to custom exceptions
        if status_code == "unauthorized" or response_status == 401:
            return NotionAuthenticationError(
                message="Notion API authentication failed. Check your API key.",
                status_code=response_status,
                response_body=message,
                details=details,
                original_error=error,
            )

        if status_code == "object_not_found" or response_status == 404:
            object_type = "database" if database_id else "page" if page_id else "object"
            object_id = database_id or page_id or "unknown"
            return NotionObjectNotFoundError(
                object_type=object_type,
                object_id=object_id,
                message=f"{object_type.capitalize()} not found or not shared with integration.",
                status_code=response_status,
                response_body=message,
                details=details,
                original_error=error,
            )

        if status_code == "restricted_resource" or response_status == 403:
            return NotionPermissionError(
                message="Insufficient permissions. Ensure database is shared with integration.",
                status_code=response_status,
                response_body=message,
                details=details,
                original_error=error,
            )

        if status_code == "rate_limited" or response_status == 429:
            # Extract retry_after from headers if available
            retry_after = None
            if hasattr(error, "response") and hasattr(error.response, "headers"):
                retry_after = error.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        retry_after = float(retry_after)
                    except (ValueError, TypeError):
                        retry_after = None

            return NotionRateLimitError(
                message="Notion API rate limit exceeded.",
                retry_after=retry_after,
                status_code=response_status,
                response_body=message,
                details=details,
                original_error=error,
            )

        # Generic API error
        return NotionAPIError(
            message=f"Notion API error: {message}",
            status_code=response_status,
            response_body=message,
            details=details,
            original_error=error,
        )

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """
        Get current rate limiter statistics.

        Returns:
            Dictionary with rate limit stats
        """
        return self.rate_limiter.get_stats()

    async def close(self):
        """Close the Notion client."""
        await self.client.aclose()
        logger.info("Notion client closed")
