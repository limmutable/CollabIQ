"""
Unit tests for CompaniesCache service.

Tests caching logic, API fetching, and cache invalidation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from notion_integrator.companies_cache import CompaniesCache
from notion_integrator.exceptions import NotionAPIError


class TestCompaniesCacheFetch:
    """Test fetching companies from API and cache."""

    @pytest.mark.asyncio
    async def test_fetch_from_api_returns_companies(self):
        """
        Test: Fetching from API returns list of (page_id, name) tuples.

        Given: Companies database has 3 companies
        When: get_companies() is called with use_cache=False
        Then: Returns 3 (page_id, name) tuples
        """
        # Arrange
        mock_client = MagicMock()
        companies_db_id = "abc123"
        cache = CompaniesCache(mock_client, companies_db_id)

        # Mock API response
        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            },
            {
                "id": "page2" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "네트워크"}}],
                    }
                },
            },
            {
                "id": "page3" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "스타트업"}}],
                    }
                },
            },
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            # Act
            companies = await cache.get_companies(use_cache=False)

            # Assert
            assert len(companies) == 3
            assert companies[0] == ("page1" + "0" * 26, "웨이크")
            assert companies[1] == ("page2" + "0" * 26, "네트워크")
            assert companies[2] == ("page3" + "0" * 26, "스타트업")

    @pytest.mark.asyncio
    async def test_fetch_skips_records_without_name(self):
        """
        Test: Records without Name property are skipped.

        Given: 3 records, but 1 has no Name property
        When: get_companies() is called
        Then: Returns only 2 companies
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        cache = CompaniesCache(mock_client, companies_db_id)

        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            },
            {
                "id": "page2" + "0" * 26,
                "properties": {},  # No Name property
            },
            {
                "id": "page3" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "네트워크"}}],
                    }
                },
            },
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            companies = await cache.get_companies(use_cache=False)

            assert len(companies) == 2
            assert companies[0] == ("page1" + "0" * 26, "웨이크")
            assert companies[1] == ("page3" + "0" * 26, "네트워크")

    @pytest.mark.asyncio
    async def test_fetch_raises_error_on_api_failure(self):
        """
        Test: API failure raises NotionAPIError.

        Given: fetch_all_records raises an exception
        When: get_companies() is called
        Then: Raises NotionAPIError
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        cache = CompaniesCache(mock_client, companies_db_id)

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            side_effect=Exception("API error"),
        ):
            with pytest.raises(NotionAPIError, match="Failed to fetch companies"):
                await cache.get_companies(use_cache=False)


class TestCompaniesCacheCaching:
    """Test cache read/write operations."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(self):
        """
        Test: Valid cache returns cached data without API call.

        Given: Cache contains valid companies data
        When: get_companies() is called with use_cache=True
        Then: Returns cached data without calling API
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()

        # Mock cache hit
        mock_cache_manager.get_data_cache.return_value = [
            {"page_id": "page1" + "0" * 26, "name": "웨이크"},
            {"page_id": "page2" + "0" * 26, "name": "네트워크"},
        ]

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
        ) as mock_fetch:
            companies = await cache.get_companies(use_cache=True)

            # Should return cached data
            assert len(companies) == 2
            assert companies[0] == ("page1" + "0" * 26, "웨이크")
            assert companies[1] == ("page2" + "0" * 26, "네트워크")

            # Should not call API
            mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_fetches_from_api(self):
        """
        Test: Cache miss triggers API fetch.

        Given: Cache is empty or invalid
        When: get_companies() is called with use_cache=True
        Then: Fetches from API and updates cache
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()

        # Mock cache miss
        mock_cache_manager.get_data_cache.return_value = None

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            }
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            companies = await cache.get_companies(use_cache=True)

            # Should fetch from API
            assert len(companies) == 1
            assert companies[0] == ("page1" + "0" * 26, "웨이크")

            # Should update cache
            mock_cache_manager.set_data_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_write_saves_correct_format(self):
        """
        Test: Cache write saves companies in correct format.

        Given: Fetched companies from API
        When: Cache is updated
        Then: Saves as list of {page_id, name} dicts
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_data_cache.return_value = None

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            }
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            await cache.get_companies(use_cache=True)

            # Verify cache write format
            mock_cache_manager.set_data_cache.assert_called_once_with(
                database_id=companies_db_id,
                database_name="Companies",
                records=[{"page_id": "page1" + "0" * 26, "name": "웨이크"}],
            )


class TestCompaniesCacheRefresh:
    """Test cache refresh and invalidation."""

    @pytest.mark.asyncio
    async def test_refresh_invalidates_and_fetches(self):
        """
        Test: Refresh invalidates cache and fetches fresh data.

        Given: Cache exists with stale data
        When: refresh() is called
        Then: Invalidates cache and fetches fresh data from API
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            }
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            companies = await cache.refresh()

            # Should invalidate cache
            mock_cache_manager.invalidate_data_cache.assert_called_once_with(
                "Companies"
            )

            # Should fetch fresh data
            assert len(companies) == 1
            assert companies[0] == ("page1" + "0" * 26, "웨이크")

    def test_invalidate_cache_clears_cache(self):
        """
        Test: invalidate_cache() clears cached data.

        Given: Cache exists
        When: invalidate_cache() is called
        Then: Cache is cleared without fetching new data
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        cache.invalidate_cache()

        # Should invalidate cache
        mock_cache_manager.invalidate_data_cache.assert_called_once_with("Companies")


class TestCompaniesCacheEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_database_returns_empty_list(self):
        """
        Test: Empty Companies database returns empty list.

        Given: Companies database has no records
        When: get_companies() is called
        Then: Returns empty list
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        cache = CompaniesCache(mock_client, companies_db_id)

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=[],
        ):
            companies = await cache.get_companies(use_cache=False)

            assert companies == []

    @pytest.mark.asyncio
    async def test_malformed_cache_triggers_api_fetch(self):
        """
        Test: Malformed cache data triggers fresh API fetch.

        Given: Cache contains invalid format (not a list)
        When: get_companies() is called with use_cache=True
        Then: Falls back to API fetch
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()

        # Mock malformed cache (not a list)
        mock_cache_manager.get_data_cache.return_value = {"invalid": "format"}

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            }
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            companies = await cache.get_companies(use_cache=True)

            # Should fall back to API fetch
            assert len(companies) == 1
            assert companies[0] == ("page1" + "0" * 26, "웨이크")

    @pytest.mark.asyncio
    async def test_cache_write_failure_does_not_raise(self):
        """
        Test: Cache write failure is logged but doesn't raise exception.

        Given: Cache write fails due to disk error
        When: get_companies() fetches and tries to cache
        Then: Returns data successfully (cache failure is non-critical)
        """
        mock_client = MagicMock()
        companies_db_id = "abc123"
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_data_cache.return_value = None

        # Mock cache write failure
        mock_cache_manager.set_data_cache.side_effect = Exception("Disk full")

        cache = CompaniesCache(mock_client, companies_db_id, mock_cache_manager)

        mock_records = [
            {
                "id": "page1" + "0" * 26,
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"text": {"content": "웨이크"}}],
                    }
                },
            }
        ]

        with patch(
            "notion_integrator.companies_cache.fetch_all_records",
            new_callable=AsyncMock,
            return_value=mock_records,
        ):
            # Should not raise exception despite cache write failure
            companies = await cache.get_companies(use_cache=True)

            assert len(companies) == 1
            assert companies[0] == ("page1" + "0" * 26, "웨이크")
