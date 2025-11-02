# API Contract: NotionIntegrator

**Feature**: 006-notion-read
**Module**: `src/notion_integrator/`
**Purpose**: Define the interface contract for Notion API integration component

---

## Overview

The NotionIntegrator provides a high-level interface for interacting with Notion databases, abstracting away API details, rate limiting, caching, and error handling.

---

## Public Interface

### Class: `NotionIntegrator`

Main entry point for all Notion operations.

#### Constructor

```python
class NotionIntegrator:
    def __init__(
        self,
        api_key: str,
        cache_dir: str = "data/notion_cache",
        rate_limit_per_sec: float = 3.0,
        schema_cache_ttl_hours: int = 24,
        data_cache_ttl_hours: int = 6,
        max_relationship_depth: int = 1
    ):
        """
        Initialize Notion integrator.

        Args:
            api_key: Notion API integration token
            cache_dir: Directory for cache storage
            rate_limit_per_sec: Maximum API requests per second
            schema_cache_ttl_hours: Schema cache TTL in hours
            data_cache_ttl_hours: Data cache TTL in hours
            max_relationship_depth: Maximum depth for resolving relationships

        Raises:
            ValueError: If api_key is empty or invalid
            PermissionError: If cache_dir is not writable
        """
```

**Contract**:
- MUST validate `api_key` is not empty
- MUST create `cache_dir` if it doesn't exist
- MUST fail fast if cache_dir is not writable
- MUST initialize rate limiter with specified limit

---

### Method: `discover_schema`

Retrieve complete schema for a database.

```python
async def discover_schema(
    self,
    database_id: str,
    force_refresh: bool = False
) -> DatabaseSchema:
    """
    Discover and return database schema.

    Args:
        database_id: Notion database ID (UUID format)
        force_refresh: If True, bypass cache and fetch fresh

    Returns:
        DatabaseSchema with complete property definitions

    Raises:
        ValueError: If database_id is invalid format
        NotionAPIError: If API request fails
        PermissionError: If integration lacks database access
        CacheError: If cache read/write fails (falls back to API)
    """
```

**Contract**:
- MUST check cache first unless `force_refresh=True`
- MUST validate `database_id` is UUID format
- MUST respect rate limits during API calls
- MUST write to cache on successful fetch
- MUST return complete schema with all properties
- MUST include relationship property configurations
- **Cache Behavior**: Use cached schema if age < TTL and not `force_refresh`

**Success Criteria**:
- Schema discovery completes in <10 seconds
- Returns all properties with correct types
- Identifies all relational fields with target databases

---

### Method: `fetch_all_records`

Fetch all records from a database with optional relationship resolution.

```python
async def fetch_all_records(
    self,
    database_id: str,
    resolve_relationships: bool = True,
    force_refresh: bool = False,
    filters: Optional[Dict[str, Any]] = None,
    max_records: Optional[int] = None
) -> List[NotionRecord]:
    """
    Fetch all records from database.

    Args:
        database_id: Notion database ID
        resolve_relationships: If True, resolve relation properties
        force_refresh: If True, bypass cache
        filters: Notion API filter object (optional)
        max_records: Maximum records to fetch (optional, for testing)

    Returns:
        List of NotionRecord objects with all property values

    Raises:
        ValueError: If database_id is invalid
        NotionAPIError: If API request fails
        RelationshipError: If circular relationship detected
        CacheError: If cache read/write fails (falls back to API)
    """
```

**Contract**:
- MUST check cache first unless `force_refresh=True`
- MUST handle pagination automatically
- MUST resolve relationships if `resolve_relationships=True` up to `max_relationship_depth`
- MUST detect and prevent circular relationship loops
- MUST respect rate limits throughout fetch process
- MUST write to cache on successful fetch
- **Pagination**: Automatically fetch all pages using `start_cursor`
- **Relationship Resolution**: Fetch related pages and embed in `_resolved` field
- **Circular Reference Handling**: Track visited page IDs, stop at max depth or when revisiting

**Success Criteria**:
- Fetches all records (handles pagination)
- Completes in <60 seconds for 500 records
- Correctly resolves relationships without infinite loops
- Preserves all property values including Unicode text

---

### Method: `format_for_llm`

Format retrieved data for LLM consumption.

```python
def format_for_llm(
    self,
    companies_records: List[NotionRecord],
    collabiq_records: List[NotionRecord],
    format_type: str = "json"
) -> LLMFormattedData:
    """
    Format Notion data for LLM prompt inclusion.

    Args:
        companies_records: Records from Companies database
        collabiq_records: Records from CollabIQ database
        format_type: Output format ("json" or "markdown")

    Returns:
        LLMFormattedData with structured company list and summary

    Raises:
        ValueError: If format_type is unsupported
        DataError: If required classification fields are missing
    """
```

**Contract**:
- MUST extract "Shinsegae affiliates?" and "Is Portfolio?" fields
- MUST create `CompanyClassification` for each company
- MUST generate both JSON structure and Markdown summary
- MUST handle missing classification fields gracefully (default to False)
- MUST include relationship data if present
- **Classification**: Clearly mark each company with both boolean flags
- **Output Structure**: Follow `LLMFormattedData` model from data-model.md

**Success Criteria**:
- All companies have classification fields populated
- Markdown summary is readable and includes company lists by type
- JSON structure allows programmatic company lookup

---

### Method: `get_data`

High-level method that combines schema discovery, data fetching, and formatting.

```python
async def get_data(
    self,
    companies_db_id: str,
    collabiq_db_id: str,
    force_refresh: bool = False
) -> LLMFormattedData:
    """
    Get all data from both databases, formatted for LLM.

    Args:
        companies_db_id: Companies database ID
        collabiq_db_id: CollabIQ database ID
        force_refresh: If True, bypass all caches

    Returns:
        LLMFormattedData ready for LLM prompt inclusion

    Raises:
        NotionAPIError: If any API request fails
        DataError: If data is incomplete or invalid
    """
```

**Contract**:
- MUST discover schemas for both databases
- MUST fetch all records from both databases
- MUST resolve relationships between databases
- MUST format output for LLM consumption
- **Orchestration**: Coordinates all operations in correct order
- **Error Handling**: Falls back to cached data if API fails

**Success Criteria**:
- Completes end-to-end in <60 seconds for 500 records (cache miss)
- Completes in <1 second if cache hit
- Returns complete, formatted data ready for LLM

---

### Method: `refresh_cache`

Manually refresh cache for a database.

```python
async def refresh_cache(
    self,
    database_id: str,
    refresh_schema: bool = True,
    refresh_data: bool = True
) -> Dict[str, bool]:
    """
    Manually refresh cache for debugging/testing.

    Args:
        database_id: Database to refresh
        refresh_schema: If True, refresh schema cache
        refresh_data: If True, refresh data cache

    Returns:
        Dict with keys {"schema_refreshed", "data_refreshed"}

    Raises:
        NotionAPIError: If refresh fails
    """
```

**Contract**:
- MUST force fresh fetch from API
- MUST update cache files with new data
- MUST return success status for each refresh type
- **Use Case**: Testing, troubleshooting, manual cache invalidation

---

## Error Handling

### Exception Hierarchy

```python
class NotionIntegratorError(Exception):
    """Base exception for all Notion integrator errors."""
    pass

class NotionAPIError(NotionIntegratorError):
    """Raised when Notion API returns an error."""
    def __init__(self, message: str, status_code: int, request_id: str):
        self.message = message
        self.status_code = status_code
        self.request_id = request_id

class CacheError(NotionIntegratorError):
    """Raised when cache read/write fails."""
    def __init__(self, message: str, cache_path: str):
        self.message = message
        self.cache_path = cache_path

class RelationshipError(NotionIntegratorError):
    """Raised when relationship resolution fails."""
    def __init__(self, message: str, page_id: str):
        self.message = message
        self.page_id = page_id

class DataError(NotionIntegratorError):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: str):
        self.message = message
        self.field = field
```

### Error Behavior

**API Errors**:
- **Transient (rate limit, timeout)**: Retry with exponential backoff (max 3 attempts)
- **Permanent (404, 403)**: Fail immediately with clear error message
- **Network errors**: Retry, then fall back to cache if available

**Cache Errors**:
- **Corrupted cache**: Log warning, delete cache, fetch fresh
- **Missing cache**: Normal behavior, fetch from API
- **Unwritable cache dir**: Log error, continue without caching

**Relationship Errors**:
- **Circular reference**: Stop resolution, log warning, return partial data
- **Missing referenced page**: Mark as `{id, _deleted: true}` in output
- **Permission denied**: Log warning, skip resolution, continue

---

## Rate Limiting Contract

### Guarantees
- MUST NOT exceed configured `rate_limit_per_sec`
- MUST queue requests if limit would be exceeded
- MUST use token bucket algorithm for burst tolerance
- MUST log warnings if queue length exceeds threshold

### Monitoring
- MUST track request count per second
- MUST expose `get_rate_limit_stats()` method for monitoring
- MUST log violations (should never happen)

---

## Caching Contract

### Cache Files
```
data/notion_cache/
├── schema_companies.json
├── schema_collabiq.json
├── data_companies.json
└── data_collabiq.json
```

### Cache Behavior
1. **Check**: Read cache file, validate TTL
2. **Hit**: Return cached data if valid
3. **Miss/Expired**: Fetch from API, write to cache
4. **Write**: Atomic write (temp file + rename)
5. **Invalidation**: Age-based (TTL) or manual (`force_refresh`)

### Cache Guarantees
- MUST use atomic writes (no partial writes)
- MUST validate JSON on read (delete if corrupted)
- MUST include timestamps and TTL in cache
- MUST handle concurrent access gracefully

---

## Performance Contract

### Timing Guarantees
- Schema discovery: <10 seconds (cache miss)
- Data fetch (500 records): <60 seconds (cache miss)
- Data fetch (500 records): <1 second (cache hit)
- Relationship resolution (50 relations, depth 1): <20 seconds

### Resource Limits
- Memory: <100 MB for processing 1000 records
- Disk: <5 MB cache size for 1000 records
- Network: Max 3 requests per second

### Scalability
- MUST handle 1000 records without degradation
- MUST handle 50 fields per record
- MUST handle 10 relationship properties per record

---

## Logging Contract

### Log Levels
- **DEBUG**: API request details, cache hits/misses
- **INFO**: Operation start/complete, timing metrics
- **WARNING**: Rate limit approaching, cache errors, stale data used
- **ERROR**: API failures, unrecoverable errors

### Required Log Messages

**Schema Discovery**:
```
INFO: Discovering schema for database {database_id}
INFO: Schema cached at {path}, expires in {hours}h
WARNING: Schema cache expired, fetching fresh
```

**Data Fetching**:
```
INFO: Fetching records from {database_id}
INFO: Fetched {count} records in {duration}s
INFO: Resolved {count} relationships (depth {depth})
WARNING: Circular relationship detected at page {page_id}
```

**Rate Limiting**:
```
DEBUG: Request queued (rate limit), waiting {seconds}s
WARNING: Rate limit queue length: {length} (threshold: 10)
ERROR: Rate limit violation detected (should not happen)
```

**Errors**:
```
ERROR: Notion API error {status}: {message} (request_id: {id})
ERROR: Cache write failed: {path} - {error}
WARNING: Using stale cache data (age: {hours}h)
```

---

## Testing Contract

### Contract Tests (Required)
- Test schema discovery returns all property types
- Test data fetching handles pagination correctly
- Test relationship resolution works for 1-3 levels
- Test rate limiting enforces 3 req/sec limit
- Test cache write/read cycle preserves data

### Mocking Strategy
- Use `responses` or `aioresponses` for HTTP mocking
- Use real file system for cache tests (temp directories)
- Use fixtures for Notion API response structures

### Test Databases
- Recommended: Create test Notion workspace with sample databases
- Alternative: Use comprehensive fixture data matching real structure

---

## Usage Example

```python
# Initialize integrator
integrator = NotionIntegrator(
    api_key=os.getenv("NOTION_API_KEY"),
    cache_dir="data/notion_cache"
)

# Get all data (high-level interface)
data = await integrator.get_data(
    companies_db_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
    collabiq_db_id=os.getenv("NOTION_DATABASE_ID_COLLABIQ")
)

# Access formatted output
print(f"Total companies: {data.metadata.total_companies}")
print(f"Portfolio companies: {data.metadata.portfolio_company_count}")
print(f"Shinsegae affiliates: {data.metadata.shinsegae_affiliate_count}")

# Use in LLM prompt
for company in data.companies:
    if company.classification.is_portfolio_company:
        print(f"{company.name} is a portfolio company")

# Manual operations (low-level interface)
schema = await integrator.discover_schema(database_id)
records = await integrator.fetch_all_records(database_id)
formatted = integrator.format_for_llm(companies_records, collabiq_records)
```

---

## Versioning

**Contract Version**: 1.0.0
**Breaking Changes**: Any signature change, exception type change, or behavior change
**Compatible Changes**: New optional parameters, additional return fields, new methods
