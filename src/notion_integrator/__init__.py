"""
Notion Integrator Module

Read-only integration with Notion API to retrieve company data for LLM-based
email processing. Supports schema discovery, data retrieval with relationships,
local caching with TTL, and rate limit compliance.

Key Features:
- Dynamic schema discovery from Notion databases
- Pagination and relationship resolution
- File-based JSON caching with separate TTLs
- Token bucket rate limiting (3 req/sec)
- LLM-ready data formatting (JSON + Markdown)

Main Components:
- NotionIntegrator: High-level API for Notion operations
- client: Notion API wrapper with rate limiting
- schema: Schema discovery logic
- fetcher: Data retrieval with pagination
- cache: File-based caching with TTL
- formatter: LLM-ready data formatting
- models: Pydantic data models

Usage:
    >>> from notion_integrator import NotionIntegrator
    >>> integrator = NotionIntegrator(api_key="secret_...")
    >>> data = await integrator.get_data(
    ...     companies_db_id="abc123",
    ...     collabiq_db_id="xyz789"
    ... )
    >>> print(data.summary_markdown)
"""

__all__ = [
    "NotionIntegrator",
    "CompanyClassification",
    "CompanyRecord",
    "FormatMetadata",
    "LLMFormattedData",
]

__version__ = "0.1.0"


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "NotionIntegrator":
        from .integrator import NotionIntegrator

        return NotionIntegrator
    if name == "CompanyClassification":
        from .models import CompanyClassification

        return CompanyClassification
    if name == "CompanyRecord":
        from .models import CompanyRecord

        return CompanyRecord
    if name == "FormatMetadata":
        from .models import FormatMetadata

        return FormatMetadata
    if name == "LLMFormattedData":
        from .models import LLMFormattedData

        return LLMFormattedData
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
