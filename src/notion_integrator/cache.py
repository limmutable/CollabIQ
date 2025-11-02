"""
Cache Management for Notion Data

File-based caching system with TTL for schemas and data:
- Atomic writes using temp file + rename pattern
- Separate TTL for schemas (24h) and data (6h)
- JSON serialization with UTF-8 encoding
- Cache validation and corruption handling

Cache Structure:
- Schema cache: data/notion_cache/schema_{database_name}.json
- Data cache: data/notion_cache/data_{database_name}.json
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import (
    CacheCorruptedError,
    CacheReadError,
    CacheWriteError,
)
from .logging_config import get_logger, log_cache_operation
from .models import DataCache, DatabaseSchema


logger = get_logger(__name__)


class CacheManager:
    """
    Manages file-based caching for Notion schemas and data.

    Attributes:
        cache_dir: Directory for cache files
        schema_ttl_hours: TTL for schema cache (default: 24 hours)
        data_ttl_hours: TTL for data cache (default: 6 hours)
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        schema_ttl_hours: int = 24,
        data_ttl_hours: int = 6,
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Cache directory path (defaults to data/notion_cache)
            schema_ttl_hours: Schema cache TTL in hours (default: 24)
            data_ttl_hours: Data cache TTL in hours (default: 6)
        """
        self.cache_dir = Path(
            cache_dir or os.getenv("NOTION_CACHE_DIR", "data/notion_cache")
        )
        self.schema_ttl_hours = schema_ttl_hours
        self.data_ttl_hours = data_ttl_hours

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Cache manager initialized",
            extra={
                "cache_dir": str(self.cache_dir),
                "schema_ttl_hours": schema_ttl_hours,
                "data_ttl_hours": data_ttl_hours,
            },
        )

    # ==========================================================================
    # Schema Cache Operations
    # ==========================================================================

    def get_schema_cache(
        self,
        database_id: str,
        database_name: str,
    ) -> Optional[DatabaseSchema]:
        """
        Get cached schema if valid.

        Args:
            database_id: Database ID
            database_name: Database name for cache filename

        Returns:
            DatabaseSchema if cache valid, None otherwise
        """
        cache_path = self._get_cache_path("schema", database_name)

        log_cache_operation(
            logger,
            operation="read",
            cache_type="schema",
            database_name=database_name,
        )

        try:
            # Read cache file
            cache_data = self._read_cache_file(cache_path)
            if not cache_data:
                log_cache_operation(
                    logger,
                    operation="read",
                    cache_type="schema",
                    database_name=database_name,
                    hit=False,
                )
                return None

            # Validate and parse cache
            cache = DataCache(**cache_data)

            # Check if expired
            if cache.is_expired:
                logger.info(
                    "Schema cache expired",
                    extra={
                        "database_name": database_name,
                        "age_hours": cache.age_hours,
                        "ttl_hours": cache.ttl_hours,
                    },
                )
                log_cache_operation(
                    logger,
                    operation="read",
                    cache_type="schema",
                    database_name=database_name,
                    hit=False,
                    reason="expired",
                )
                return None

            # Deserialize schema from cache content
            schema = self._deserialize_schema(cache.content)

            log_cache_operation(
                logger,
                operation="read",
                cache_type="schema",
                database_name=database_name,
                hit=True,
                age_hours=cache.age_hours,
            )

            return schema

        except CacheReadError:
            log_cache_operation(
                logger,
                operation="read",
                cache_type="schema",
                database_name=database_name,
                hit=False,
                reason="read_error",
            )
            return None
        except CacheCorruptedError:
            log_cache_operation(
                logger,
                operation="read",
                cache_type="schema",
                database_name=database_name,
                hit=False,
                reason="corrupted",
            )
            # Delete corrupted cache
            self._delete_cache_file(cache_path)
            return None

    def set_schema_cache(
        self,
        schema: DatabaseSchema,
    ) -> None:
        """
        Cache database schema.

        Args:
            schema: DatabaseSchema to cache

        Raises:
            CacheWriteError: If cache write fails
        """
        database_name = schema.database.title
        cache_path = self._get_cache_path("schema", database_name)

        log_cache_operation(
            logger,
            operation="write",
            cache_type="schema",
            database_name=database_name,
        )

        try:
            # Serialize schema
            serialized_schema = self._serialize_schema(schema)

            # Create cache entry
            cache = DataCache.create(
                cache_type="schema",
                database_id=schema.database.id,
                database_name=database_name,
                ttl_hours=self.schema_ttl_hours,
                content=serialized_schema,
                metadata={
                    "property_count": schema.property_count,
                    "has_relations": schema.has_relations,
                    "relation_count": len(schema.relation_properties),
                },
            )

            # Write to cache
            self._write_cache_file(cache_path, cache.model_dump())

            logger.info(
                "Schema cached successfully",
                extra={
                    "database_name": database_name,
                    "ttl_hours": self.schema_ttl_hours,
                },
            )

        except Exception as e:
            raise CacheWriteError(
                cache_path=str(cache_path),
                message=f"Failed to write schema cache: {e}",
                original_error=e,
            )

    # ==========================================================================
    # Data Cache Operations
    # ==========================================================================

    def get_data_cache(
        self,
        database_id: str,
        database_name: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached data if valid.

        Args:
            database_id: Database ID
            database_name: Database name for cache filename

        Returns:
            List of records if cache valid, None otherwise
        """
        cache_path = self._get_cache_path("data", database_name)

        log_cache_operation(
            logger,
            operation="read",
            cache_type="data",
            database_name=database_name,
        )

        try:
            # Read cache file
            cache_data = self._read_cache_file(cache_path)
            if not cache_data:
                log_cache_operation(
                    logger,
                    operation="read",
                    cache_type="data",
                    database_name=database_name,
                    hit=False,
                )
                return None

            # Validate and parse cache
            cache = DataCache(**cache_data)

            # Check if expired
            if cache.is_expired:
                logger.info(
                    "Data cache expired",
                    extra={
                        "database_name": database_name,
                        "age_hours": cache.age_hours,
                        "ttl_hours": cache.ttl_hours,
                    },
                )
                log_cache_operation(
                    logger,
                    operation="read",
                    cache_type="data",
                    database_name=database_name,
                    hit=False,
                    reason="expired",
                )
                return None

            # Return cached data
            log_cache_operation(
                logger,
                operation="read",
                cache_type="data",
                database_name=database_name,
                hit=True,
                age_hours=cache.age_hours,
                record_count=len(cache.content)
                if isinstance(cache.content, list)
                else 0,
            )

            return cache.content if isinstance(cache.content, list) else []

        except CacheReadError:
            log_cache_operation(
                logger,
                operation="read",
                cache_type="data",
                database_name=database_name,
                hit=False,
                reason="read_error",
            )
            return None
        except CacheCorruptedError:
            log_cache_operation(
                logger,
                operation="read",
                cache_type="data",
                database_name=database_name,
                hit=False,
                reason="corrupted",
            )
            # Delete corrupted cache
            self._delete_cache_file(cache_path)
            return None

    def set_data_cache(
        self,
        database_id: str,
        database_name: str,
        records: List[Dict[str, Any]],
    ) -> None:
        """
        Cache database records.

        Args:
            database_id: Database ID
            database_name: Database name
            records: List of records to cache

        Raises:
            CacheWriteError: If cache write fails
        """
        cache_path = self._get_cache_path("data", database_name)

        log_cache_operation(
            logger,
            operation="write",
            cache_type="data",
            database_name=database_name,
            record_count=len(records),
        )

        try:
            # Create cache entry
            cache = DataCache.create(
                cache_type="data",
                database_id=database_id,
                database_name=database_name,
                ttl_hours=self.data_ttl_hours,
                content=records,
                metadata={
                    "record_count": len(records),
                },
            )

            # Write to cache
            self._write_cache_file(cache_path, cache.model_dump())

            logger.info(
                "Data cached successfully",
                extra={
                    "database_name": database_name,
                    "record_count": len(records),
                    "ttl_hours": self.data_ttl_hours,
                },
            )

        except Exception as e:
            raise CacheWriteError(
                cache_path=str(cache_path),
                message=f"Failed to write data cache: {e}",
                original_error=e,
            )

    # ==========================================================================
    # Cache Invalidation
    # ==========================================================================

    def invalidate_schema_cache(self, database_name: str) -> bool:
        """
        Invalidate (delete) schema cache.

        Args:
            database_name: Database name

        Returns:
            True if cache was deleted, False if not found
        """
        cache_path = self._get_cache_path("schema", database_name)

        log_cache_operation(
            logger,
            operation="invalidate",
            cache_type="schema",
            database_name=database_name,
        )

        return self._delete_cache_file(cache_path)

    def invalidate_data_cache(self, database_name: str) -> bool:
        """
        Invalidate (delete) data cache.

        Args:
            database_name: Database name

        Returns:
            True if cache was deleted, False if not found
        """
        cache_path = self._get_cache_path("data", database_name)

        log_cache_operation(
            logger,
            operation="invalidate",
            cache_type="data",
            database_name=database_name,
        )

        return self._delete_cache_file(cache_path)

    def invalidate_all_caches(self, database_name: str) -> None:
        """
        Invalidate all caches for a database.

        Args:
            database_name: Database name
        """
        self.invalidate_schema_cache(database_name)
        self.invalidate_data_cache(database_name)

        logger.info(
            "All caches invalidated",
            extra={"database_name": database_name},
        )

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def _get_cache_path(self, cache_type: str, database_name: str) -> Path:
        """
        Get cache file path.

        Args:
            cache_type: "schema" or "data"
            database_name: Database name

        Returns:
            Path to cache file
        """
        # Sanitize database name for filename
        safe_name = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in database_name
        )
        filename = f"{cache_type}_{safe_name}.json"
        return self.cache_dir / filename

    def _read_cache_file(self, cache_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read cache file.

        Args:
            cache_path: Path to cache file

        Returns:
            Parsed JSON data or None if file doesn't exist

        Raises:
            CacheReadError: If file exists but can't be read
            CacheCorruptedError: If JSON is invalid
        """
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise CacheCorruptedError(
                cache_path=str(cache_path),
                message="Cache file contains invalid JSON",
                original_error=e,
            )
        except Exception as e:
            raise CacheReadError(
                cache_path=str(cache_path),
                message=f"Failed to read cache file: {e}",
                original_error=e,
            )

    def _write_cache_file(self, cache_path: Path, data: Dict[str, Any]) -> None:
        """
        Write cache file atomically.

        Uses temp file + rename pattern for atomic writes.

        Args:
            cache_path: Path to cache file
            data: Data to write

        Raises:
            CacheWriteError: If write fails
        """
        temp_path = cache_path.with_suffix(".tmp")

        try:
            # Write to temp file
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Atomic rename
            temp_path.replace(cache_path)

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise CacheWriteError(
                cache_path=str(cache_path),
                message=f"Failed to write cache file: {e}",
                original_error=e,
            )

    def _delete_cache_file(self, cache_path: Path) -> bool:
        """
        Delete cache file.

        Args:
            cache_path: Path to cache file

        Returns:
            True if file was deleted, False if not found
        """
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def _serialize_schema(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """
        Serialize DatabaseSchema to dict for caching.

        Args:
            schema: DatabaseSchema to serialize

        Returns:
            Serializable dict
        """
        return schema.model_dump(mode="json")

    def _deserialize_schema(self, data: Dict[str, Any]) -> DatabaseSchema:
        """
        Deserialize DatabaseSchema from cached dict.

        Args:
            data: Cached schema data

        Returns:
            DatabaseSchema instance

        Raises:
            CacheCorruptedError: If deserialization fails
        """
        try:
            return DatabaseSchema(**data)
        except Exception as e:
            raise CacheCorruptedError(
                cache_path="schema cache",
                message=f"Failed to deserialize schema: {e}",
                original_error=e,
            )
