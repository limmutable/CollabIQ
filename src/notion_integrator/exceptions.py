"""
Custom Exception Hierarchy for Notion Integration

Defines all exceptions used in the Notion integration system with clear
error messages and context for debugging.

Exception Hierarchy:
    NotionIntegratorError (base)
    ├── NotionAPIError (API communication failures)
    │   ├── NotionAuthenticationError (auth failures)
    │   ├── NotionRateLimitError (rate limit exceeded)
    │   ├── NotionObjectNotFoundError (database/page not found)
    │   └── NotionPermissionError (insufficient permissions)
    ├── CacheError (cache operations)
    │   ├── CacheReadError (cache read failures)
    │   ├── CacheWriteError (cache write failures)
    │   └── CacheCorruptedError (corrupted cache data)
    ├── RelationshipError (relationship resolution)
    │   ├── CircularReferenceError (circular relationships)
    │   └── RelationshipDepthExceededError (max depth exceeded)
    └── DataError (data validation and processing)
        ├── SchemaValidationError (schema validation failures)
        ├── RecordValidationError (record validation failures)
        └── DataFormattingError (LLM format generation failures)
"""

from typing import Any, Dict, Optional


class NotionIntegratorError(Exception):
    """
    Base exception for all Notion integrator errors.

    Attributes:
        message: Human-readable error message
        details: Additional context (database IDs, page IDs, etc.)
        original_error: Original exception if wrapped
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize base exception.

        Args:
            message: Error message
            details: Additional context for debugging
            original_error: Original exception if this wraps another error
        """
        self.message = message
        self.details = details or {}
        self.original_error = original_error

        # Build complete error message
        full_message = message
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            full_message = f"{message} ({detail_str})"
        if original_error:
            full_message = f"{full_message}: {str(original_error)}"

        super().__init__(full_message)


# ==============================================================================
# Notion API Errors
# ==============================================================================


class NotionAPIError(NotionIntegratorError):
    """
    Base exception for Notion API communication failures.

    Raised when API requests fail due to network, server, or API errors.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if available
            response_body: Response body for debugging
            **kwargs: Additional details passed to base class
        """
        details = kwargs.get("details", {})
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:200]  # Truncate for readability

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


class NotionAuthenticationError(NotionAPIError):
    """
    Authentication failed - invalid or missing API key.

    Common causes:
    - Invalid NOTION_API_KEY
    - Expired integration token
    - Token not set in environment
    """

    def __init__(self, message: str = "Notion API authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class NotionRateLimitError(NotionAPIError):
    """
    Rate limit exceeded - too many requests.

    Includes retry_after hint if provided by API.
    """

    def __init__(
        self,
        message: str = "Notion API rate limit exceeded",
        retry_after: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry (from Retry-After header)
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(message, **{**kwargs, "details": details})
        self.retry_after = retry_after


class NotionObjectNotFoundError(NotionAPIError):
    """
    Notion object not found - invalid database/page ID or not shared.

    Common causes:
    - Database not shared with integration
    - Invalid database/page ID
    - Object deleted
    """

    def __init__(
        self,
        object_type: str,
        object_id: str,
        message: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize object not found error.

        Args:
            object_type: Type of object (database, page, etc.)
            object_id: ID of the missing object
            message: Custom error message
            **kwargs: Additional details
        """
        msg = message or f"{object_type} not found or not accessible"
        details = kwargs.get("details", {})
        details.update({"object_type": object_type, "object_id": object_id})

        super().__init__(msg, **{**kwargs, "details": details})


class NotionPermissionError(NotionAPIError):
    """
    Insufficient permissions - integration lacks required access.

    Common causes:
    - Integration doesn't have read capability
    - Database not shared with integration
    - Workspace permissions changed
    """

    def __init__(
        self, message: str = "Insufficient permissions for Notion operation", **kwargs
    ):
        super().__init__(message, **kwargs)


# ==============================================================================
# Cache Errors
# ==============================================================================


class CacheError(NotionIntegratorError):
    """
    Base exception for cache operation failures.
    """

    pass


class CacheReadError(CacheError):
    """
    Failed to read from cache.

    Common causes:
    - File not found
    - Corrupted JSON
    - Permission denied
    """

    def __init__(
        self,
        cache_path: str,
        message: str = "Failed to read cache",
        **kwargs,
    ):
        """
        Initialize cache read error.

        Args:
            cache_path: Path to cache file
            message: Error message
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details["cache_path"] = cache_path

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


class CacheWriteError(CacheError):
    """
    Failed to write to cache.

    Common causes:
    - Disk full
    - Permission denied
    - Invalid path
    """

    def __init__(
        self,
        cache_path: str,
        message: str = "Failed to write cache",
        **kwargs,
    ):
        """
        Initialize cache write error.

        Args:
            cache_path: Path to cache file
            message: Error message
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details["cache_path"] = cache_path

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


class CacheCorruptedError(CacheError):
    """
    Cache data is corrupted or invalid.

    Common causes:
    - Invalid JSON structure
    - Missing required fields
    - Type validation failures
    """

    def __init__(
        self,
        cache_path: str,
        message: str = "Cache data is corrupted",
        **kwargs,
    ):
        """
        Initialize cache corrupted error.

        Args:
            cache_path: Path to corrupted cache file
            message: Error message
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details["cache_path"] = cache_path

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


# ==============================================================================
# Relationship Errors
# ==============================================================================


class RelationshipError(NotionIntegratorError):
    """
    Base exception for relationship resolution failures.
    """

    pass


class CircularReferenceError(RelationshipError):
    """
    Circular relationship detected.

    Raised when relationship resolution encounters a cycle that would
    cause infinite recursion.
    """

    def __init__(
        self,
        page_id: str,
        path: list[str],
        message: str = "Circular relationship detected",
        **kwargs,
    ):
        """
        Initialize circular reference error.

        Args:
            page_id: ID of page where cycle was detected
            path: List of page IDs in the circular path
            message: Error message
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details.update({"page_id": page_id, "circular_path": " -> ".join(path)})

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


class RelationshipDepthExceededError(RelationshipError):
    """
    Maximum relationship depth exceeded.

    Raised when relationship resolution exceeds configured max_depth
    to prevent performance issues.
    """

    def __init__(
        self,
        current_depth: int,
        max_depth: int,
        message: str = "Relationship depth exceeded",
        **kwargs,
    ):
        """
        Initialize depth exceeded error.

        Args:
            current_depth: Depth reached
            max_depth: Maximum allowed depth
            message: Error message
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details.update({"current_depth": current_depth, "max_depth": max_depth})

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


# ==============================================================================
# Data Errors
# ==============================================================================


class DataError(NotionIntegratorError):
    """
    Base exception for data validation and processing failures.
    """

    pass


class SchemaValidationError(DataError):
    """
    Schema validation failed.

    Common causes:
    - Missing required properties
    - Invalid property types
    - Unexpected schema structure
    """

    def __init__(
        self,
        database_id: str,
        message: str = "Schema validation failed",
        validation_errors: Optional[list] = None,
        **kwargs,
    ):
        """
        Initialize schema validation error.

        Args:
            database_id: ID of database with invalid schema
            message: Error message
            validation_errors: List of validation error messages
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details["database_id"] = database_id
        if validation_errors:
            details["validation_errors"] = validation_errors

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


class RecordValidationError(DataError):
    """
    Record validation failed.

    Common causes:
    - Missing required fields
    - Invalid field values
    - Type mismatches
    """

    def __init__(
        self,
        page_id: str,
        message: str = "Record validation failed",
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """
        Initialize record validation error.

        Args:
            page_id: ID of invalid record
            message: Error message
            field_errors: Map of field names to error messages
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details["page_id"] = page_id
        if field_errors:
            details["field_errors"] = field_errors

        super().__init__(
            message, details=details, original_error=kwargs.get("original_error")
        )


class DataFormattingError(DataError):
    """
    LLM data formatting failed.

    Common causes:
    - Missing required classification fields
    - Invalid company records
    - Markdown generation failures
    """

    def __init__(
        self,
        message: str = "Failed to format data for LLM",
        **kwargs,
    ):
        """
        Initialize data formatting error.

        Args:
            message: Error message
            **kwargs: Additional details
        """
        super().__init__(
            message,
            details=kwargs.get("details"),
            original_error=kwargs.get("original_error"),
        )
