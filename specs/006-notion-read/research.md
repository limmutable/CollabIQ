# Technical Research: Notion Read Operations

**Feature**: 006-notion-read
**Date**: 2025-11-02
**Purpose**: Document technical decisions, library choices, and implementation patterns for Notion API integration

## Research Questions

1. Which Notion SDK/library to use for Python?
2. How to implement rate limiting for 3 req/sec constraint?
3. Best practices for caching API responses with TTL?
4. How to handle Notion's paginated responses efficiently?
5. Optimal data format for LLM consumption?
6. How to detect and resolve circular relationships?

---

## Decision 1: Notion SDK

### Decision
Use **`notion-client`** (official Notion Python SDK)

### Rationale
- **Official Support**: Maintained by Notion team, guaranteed API compatibility
- **Type Safety**: Full type hints, works well with mypy/pyright
- **Async Support**: Built-in async/await for better performance
- **Active Maintenance**: Regular updates matching Notion API changes
- **Documentation**: Comprehensive official docs with examples

### Alternatives Considered

| Library | Pros | Cons | Rejected Because |
|---------|------|------|------------------|
| **notion-sdk-py** (community) | More Pythonic API | Unofficial, slower updates | Risk of API drift, less reliable |
| **requests + manual** | Full control | High maintenance, fragile | Reinventing the wheel, error-prone |
| **notional** | Higher-level abstractions | Adds complexity layer | Violates Simplicity principle |

### Implementation Notes
```python
# Installation
uv add notion-client

# Usage pattern
from notion_client import Client
client = Client(auth=os.environ["NOTION_API_KEY"])
```

---

## Decision 2: Rate Limiting Implementation

### Decision
**Token Bucket Algorithm** with `asyncio.Semaphore` and time-based token refill

### Rationale
- **Precise Control**: Can enforce exactly 3 req/sec limit
- **Burst Handling**: Allows small bursts while maintaining average rate
- **Simple Implementation**: ~50 lines of code, no external dependencies
- **Async-Friendly**: Works seamlessly with `notion-client`'s async API

### Alternatives Considered

| Approach | Pros | Cons | Rejected Because |
|----------|------|------|------------------|
| **`ratelimit` library** | Ready-made solution | Adds dependency, sync-only | Doesn't work well with async, over-engineered |
| **`aioli miter`** | Async-native | Another dependency, less control | Unnecessary abstraction |
| **Simple `time.sleep()`** | Dead simple | Inefficient, blocks unnecessarily | Wastes time, poor async support |

### Implementation Pattern
```python
import asyncio
import time

class RateLimiter:
    def __init__(self, rate_per_second: float):
        self.rate = rate_per_second
        self.tokens = rate_per_second
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
```

---

## Decision 3: Caching Strategy

### Decision
**File-based JSON cache** with separate schema and data caches, each with TTL metadata

### Rationale
- **No Dependencies**: Uses stdlib `json` module
- **Simple Inspection**: Cache files are human-readable for debugging
- **Separate TTLs**: Schema cache can have longer TTL (24h) than data cache (6h)
- **Easy Backup**: Cache directory can be version-controlled or backed up
- **Atomic Writes**: Use temp file + rename for crash safety

### Alternatives Considered

| Approach | Pros | Cons | Rejected Because |
|----------|------|------|------------------|
| **Redis** | Fast, distributed | External dependency, overkill | Violates Simplicity, unnecessary for single-server |
| **SQLite** | Structured queries | Adds DB complexity | Over-engineered for key-value caching |
| **Pickle** | Python-native | Not human-readable, security risk | Hard to debug, potential security issues |
| **In-memory only** | Fastest | Lost on restart | Defeats purpose of reducing API calls |

### Cache Structure
```python
# Schema cache: data/notion_cache/schema_companies.json
{
    "database_id": "abc123...",
    "database_title": "Companies",
    "cached_at": "2025-11-02T10:30:00Z",
    "ttl_hours": 24,
    "properties": {
        "Name": {"type": "title", "id": "prop_1"},
        "Shinsegae affiliates?": {"type": "checkbox", "id": "prop_2"},
        "Is Portfolio?": {"type": "checkbox", "id": "prop_3"},
        "Related CollabIQ": {"type": "relation", "id": "prop_4", "relation_db": "xyz789..."}
    }
}

# Data cache: data/notion_cache/data_companies.json
{
    "database_id": "abc123...",
    "cached_at": "2025-11-02T10:35:00Z",
    "ttl_hours": 6,
    "record_count": 123,
    "records": [
        {
            "id": "page_1",
            "properties": {
                "Name": "Company A",
                "Shinsegae affiliates?": false,
                "Is Portfolio?": true
            }
        }
    ]
}
```

---

## Decision 4: Pagination Handling

### Decision
**Async generator pattern** with automatic pagination using `start_cursor`

### Rationale
- **Memory Efficient**: Streams results instead of loading all in memory
- **Progress Tracking**: Can log/report progress during long fetches
- **Early Termination**: Can stop fetching if limit reached
- **Notion Native**: Uses Notion's `start_cursor` pagination exactly as designed

### Implementation Pattern
```python
async def fetch_all_pages(database_id: str):
    """Async generator that yields all pages from database."""
    start_cursor = None

    while True:
        response = await client.databases.query(
            database_id=database_id,
            start_cursor=start_cursor,
            page_size=100  # Max allowed by Notion API
        )

        for page in response["results"]:
            yield page

        if not response["has_more"]:
            break

        start_cursor = response["next_cursor"]
```

---

## Decision 5: LLM Data Format

### Decision
**Hybrid JSON + Markdown** with structured company list and embedded classification metadata

### Rationale
- **Structured Lookup**: JSON for precise company searches
- **Human-Readable**: Markdown for LLM-friendly descriptions
- **Classification Fields Prominent**: Both checkboxes clearly visible
- **Relationship Clarity**: Nested structure shows connections
- **Token Efficient**: Compact representation for prompt inclusion

### Format Example
```json
{
  "companies": [
    {
      "id": "company_1",
      "name": "Company A",
      "classification": {
        "is_shinsegae_affiliate": false,
        "is_portfolio_company": true
      },
      "source_database": "Companies",
      "related_records": [...]
    }
  ],
  "summary_markdown": "# Company Classification\n\n## Portfolio Companies\n- Company A (PortCo)\n\n## Shinsegae Affiliates\n- Company B (SSG)\n\n..."
}
```

### Alternatives Considered

| Format | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| **Pure JSON** | Structured, parseable | Verbose, less LLM-friendly | Wastes tokens, harder for LLM to scan |
| **Pure Markdown** | LLM-friendly | No structured lookup | Can't programmatically search |
| **CSV** | Compact | Limited structure | Can't represent nested relationships |

---

## Decision 6: Circular Relationship Handling

### Decision
**Visited Set Tracking** with configurable max depth (default: 1)

### Rationale
- **Simple & Effective**: Track visited record IDs to prevent loops
- **Configurable Depth**: Allows controlling fetch depth vs completeness trade-off
- **Clear Termination**: Guaranteed to stop at max depth or when all records visited
- **Debuggable**: Can log when circular reference detected

### Implementation Pattern
```python
async def resolve_relationships(
    page_id: str,
    depth: int = 1,
    max_depth: int = 1,
    visited: set = None
) -> dict:
    if visited is None:
        visited = set()

    if depth > max_depth or page_id in visited:
        return {"id": page_id, "_truncated": True}

    visited.add(page_id)

    page = await client.pages.retrieve(page_id)

    # Recursively resolve relation properties
    for prop_name, prop_value in page["properties"].items():
        if prop_value["type"] == "relation":
            related_ids = prop_value["relation"]
            prop_value["_resolved"] = [
                await resolve_relationships(
                    rel["id"],
                    depth + 1,
                    max_depth,
                    visited
                )
                for rel in related_ids
            ]

    return page
```

---

## Decision 7: Retry Logic with Exponential Backoff

### Decision
Use **`tenacity`** library for retry logic

### Rationale
- **Declarative**: Clean decorator-based retry configuration
- **Standard Library**: Widely used, well-tested
- **Flexible**: Supports exponential backoff, jitter, retry conditions
- **Logging Integration**: Built-in logging of retry attempts

### Implementation Pattern
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from notion_client import APIResponseError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((APIResponseError, ConnectionError)),
    reraise=True
)
async def fetch_with_retry(database_id: str):
    return await client.databases.retrieve(database_id)
```

### Alternatives Considered

| Approach | Pros | Cons | Rejected Because |
|----------|------|------|------------------|
| **Manual retry loop** | No dependency | Boilerplate, error-prone | Reinvents wheel, violates DRY |
| **backoff library** | Alternative | Less popular, similar features | Tenacity more widely adopted |

---

## Best Practices Summary

### Notion API Integration
1. **Always use async API** for better performance with rate limiting
2. **Batch read operations** where possible (query vs individual page retrieves)
3. **Handle API version changes** gracefully (Notion-Version header)
4. **Log all API errors** with request IDs for debugging

### Caching
1. **Atomic cache writes**: Write to temp file, then rename
2. **Include metadata**: Timestamp, TTL, record count for validation
3. **Validate on read**: Check TTL before using cached data
4. **Graceful degradation**: Use stale cache if API unreachable

### Error Handling
1. **Distinguish transient vs permanent errors**: Retry transient, fail fast on permanent
2. **Provide actionable error messages**: Include what went wrong and how to fix
3. **Fall back to cached data**: When API fails but cache exists
4. **Log with context**: Include database IDs, record counts, error details

### Unicode Handling
1. **Use UTF-8 everywhere**: File writes, JSON serialization, logging
2. **Test with real Korean/Japanese text**: Don't assume ASCII
3. **Normalize Unicode**: Use NFC normalization for consistent comparison

### Rate Limiting
1. **Respect limits strictly**: Never exceed 3 req/sec
2. **Add buffer**: Target 2.8 req/sec to account for timing variance
3. **Monitor violations**: Log warnings if approaching limit
4. **Queue requests**: Don't drop requests, queue them

---

## Dependencies to Add

```bash
# Production dependencies
uv add notion-client    # Official Notion SDK
uv add tenacity         # Retry logic with exponential backoff

# Development dependencies (if not already present)
uv add --dev pytest-asyncio  # For async test support
```

---

## Configuration Requirements

### Environment Variables
```bash
# Required in .env or Infisical
NOTION_API_KEY=secret_...                    # Notion integration token
NOTION_DATABASE_ID_COMPANIES=abc123...       # Companies database ID
NOTION_DATABASE_ID_COLLABIQ=xyz789...        # CollabIQ database ID

# Optional configuration
NOTION_CACHE_DIR=data/notion_cache           # Cache directory (default)
NOTION_SCHEMA_CACHE_TTL_HOURS=24             # Schema cache TTL (default)
NOTION_DATA_CACHE_TTL_HOURS=6                # Data cache TTL (default)
NOTION_RATE_LIMIT_PER_SEC=3                  # Rate limit (default)
NOTION_MAX_RELATIONSHIP_DEPTH=1              # Relationship depth (default)
```

---

## Testing Strategy

### Contract Tests (test_notion_api_integration.py)
- **Purpose**: Verify Notion API wrapper behavior
- **Scope**: Schema discovery, data fetching, pagination
- **Requires**: Valid Notion API credentials (test database recommended)

### Integration Tests (test_notion_cache.py, test_notion_rate_limiting.py)
- **Purpose**: Verify caching behavior and rate limit compliance
- **Scope**: Cache TTL, stale data handling, rate limit enforcement
- **Mocking**: Mock Notion API responses, use real file system

### Unit Tests (test_notion_schema_parser.py, test_notion_formatter.py)
- **Purpose**: Verify data transformation logic
- **Scope**: Schema parsing, LLM format generation
- **Mocking**: Use fixture data, no external dependencies

---

## Risk Mitigation

### Risk 1: Rate Limit Violations
**Mitigation**: Implement strict rate limiter with buffer (2.8 req/sec target), extensive testing with rate limit monitoring

### Risk 2: Cache Corruption
**Mitigation**: Atomic writes via temp files, validate JSON on read, fall back to fresh fetch if corrupted

### Risk 3: API Changes Breaking Integration
**Mitigation**: Pin `notion-client` version, comprehensive integration tests, monitor Notion API changelog

### Risk 4: Large Database Performance
**Mitigation**: Async streaming with generators, pagination, progress logging, configurable fetch limits

### Risk 5: Unicode Handling Issues
**Mitigation**: UTF-8 everywhere, test with real Korean/Japanese data, Unicode normalization

---

## Performance Estimates

Based on constraints and requirements:

**Schema Discovery**:
- 2 databases × 1 API call each = 2 requests
- With 3 req/sec limit: ~1 second
- Target: <10 seconds ✅

**Data Retrieval** (500 records):
- 500 records ÷ 100 per page = 5 pages per database
- 2 databases × 5 pages = 10 API calls
- With 3 req/sec limit: ~4 seconds base
- Relationship resolution (1 level, assume 50 relations): +17 seconds
- Total: ~21 seconds
- Target: <60 seconds ✅

**Cache Hit Scenario**:
- 0 API calls, pure file I/O
- <100ms total
- Target: 80% cache hit rate ✅

---

## References

- [Notion API Documentation](https://developers.notion.com/)
- [notion-client Python SDK](https://github.com/ramnes/notion-sdk-py)
- [PEP 8 Python Style Guide](https://peps.python.org/pep-0008/)
- [Tenacity Retry Library](https://tenacity.readthedocs.io/)
