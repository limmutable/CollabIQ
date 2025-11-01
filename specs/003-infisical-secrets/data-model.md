# Data Model: Infisical Secret Management Integration

**Feature**: 003-infisical-secrets
**Date**: 2025-11-01
**Status**: Design Complete
**Prerequisites**: [research.md](research.md)

## Overview

This document defines the data structures and relationships for Infisical secret management integration. All entities are derived from functional requirements (FR-001 through FR-013) and user stories in [spec.md](spec.md).

---

## Entity Definitions

### 1. InfisicalConfig

**Purpose**: Configuration parameters for initializing Infisical SDK client

**Attributes**:
| Attribute | Type | Required | Default | Description | Validation Rules |
|-----------|------|----------|---------|-------------|------------------|
| `enabled` | bool | Yes | False | Whether Infisical integration is active | Must be explicitly set to True to enable |
| `host` | str | No | "https://app.infisical.com" | Infisical API endpoint URL | Must be valid URL (https://) |
| `project_id` | str | Conditional | None | Infisical project identifier | Required if enabled=True |
| `environment_slug` | str | Conditional | None | Environment name (dev/staging/prod) | Required if enabled=True, must be one of: dev, staging, prod |
| `client_id` | str | Conditional | None | Universal Auth machine identity client ID | Required if enabled=True |
| `client_secret` | str | Conditional | None | Universal Auth machine identity client secret | Required if enabled=True, never logged |
| `cache_ttl` | int | No | 60 | Secret cache time-to-live in seconds | Range: 0-3600 (0=disabled, 60=default) |

**Relationships**:
- Used by: InfisicalClient (initialization parameters)
- Loaded from: Environment variables via Pydantic Settings

**State Transitions**: N/A (immutable configuration)

**Example**:
```python
InfisicalConfig(
    enabled=True,
    host="https://app.infisical.com",
    project_id="65abc123def456",
    environment_slug="dev",
    client_id="machine-identity-abc123",
    client_secret="secret-xyz789",  # Never logged
    cache_ttl=60
)
```

---

### 2. SecretCache

**Purpose**: In-memory cache for retrieved secrets with TTL-based expiration

**Attributes**:
| Attribute | Type | Required | Default | Description | Validation Rules |
|-----------|------|----------|---------|-------------|------------------|
| `secrets` | dict[str, str] | Yes | {} | Key-value pairs of secret names to values | Keys must be non-empty strings |
| `last_updated` | datetime | Yes | None | Timestamp of last cache refresh | UTC timezone |
| `ttl_seconds` | int | Yes | 60 | Time-to-live for cache validity | Range: 0-3600 |

**Relationships**:
- Managed by: InfisicalClient (internal state)
- Populated from: Infisical API responses

**State Transitions**:
```
Empty → Populated (on first fetch)
Populated → Stale (after TTL expires)
Stale → Refreshed (on next access)
```

**Behavior**:
- **Cache hit** (secrets present + not expired): Return cached value immediately
- **Cache miss** (secrets empty OR expired): Fetch from Infisical API, update cache, return value
- **Cache fallback** (API unreachable + cache stale): Return stale cached value with warning log

**Example**:
```python
SecretCache(
    secrets={
        "GMAIL_API_KEY": "ya29.a0AfH6SMB...",
        "GEMINI_API_KEY": "AIzaSyD...",
        "NOTION_API_KEY": "secret_ntn..."
    },
    last_updated=datetime(2025, 11, 1, 10, 30, 0, tzinfo=timezone.utc),
    ttl_seconds=60
)
```

**Expiration Check**:
```python
def is_expired(self) -> bool:
    return (datetime.utcnow() - self.last_updated).total_seconds() > self.ttl_seconds
```

---

### 3. SecretValue

**Purpose**: Individual secret with metadata about retrieval source and freshness

**Attributes**:
| Attribute | Type | Required | Default | Description | Validation Rules |
|-----------|------|----------|---------|-------------|------------------|
| `key` | str | Yes | None | Secret name (e.g., "GMAIL_API_KEY") | Must match pattern: [A-Z][A-Z0-9_]* |
| `value` | str | Yes | None | Secret value (sensitive data) | Non-empty string, never logged |
| `environment` | str | Yes | None | Environment where secret retrieved (dev/staging/prod) | Must be one of: dev, staging, prod |
| `source` | str | Yes | None | Source of secret value | One of: "infisical", "cache", "env_file" |
| `is_cached` | bool | Yes | False | Whether value came from cache (not fresh) | True = cached, False = fresh from API |
| `retrieved_at` | datetime | Yes | None | When secret was retrieved | UTC timezone |

**Relationships**:
- Retrieved by: InfisicalClient (via get_secret method)
- Consumed by: Settings class (field override)

**Example**:
```python
SecretValue(
    key="GMAIL_API_KEY",
    value="ya29.a0AfH6SMB...",  # Never logged
    environment="dev",
    source="infisical",
    is_cached=False,
    retrieved_at=datetime(2025, 11, 1, 10, 30, 5, tzinfo=timezone.utc)
)
```

---

### 4. InfisicalClient

**Purpose**: Wrapper around Infisical Python SDK providing caching, error handling, and fallback logic

**Attributes**:
| Attribute | Type | Required | Default | Description | Validation Rules |
|-----------|------|----------|---------|-------------|------------------|
| `_sdk_client` | InfisicalSDKClient | Yes | None | Underlying Infisical SDK instance | Initialized on construction |
| `_config` | InfisicalConfig | Yes | None | Configuration for client | Validated on construction |
| `_cache` | SecretCache | Yes | SecretCache({}, None, 60) | In-memory secret cache | Managed internally |
| `_authenticated` | bool | Yes | False | Whether Universal Auth login succeeded | Set to True after login() |

**Relationships**:
- Uses: InfisicalConfig (initialization)
- Manages: SecretCache (internal state)
- Returns: SecretValue (get_secret method)

**State Transitions**:
```
Uninitialized → Authenticating (on __init__)
Authenticating → Authenticated (on successful login)
Authenticated → Ready (after first secret fetch)
Ready → Disconnected (on API error, falls back to cache)
```

**Methods**:
| Method | Input | Output | Errors | Description |
|--------|-------|--------|--------|-------------|
| `get_secret(secret_name: str)` | Secret name | SecretValue | SecretNotFoundError, InfisicalConnectionError | Retrieve single secret with cache fallback |
| `get_all_secrets()` | None | dict[str, str] | InfisicalConnectionError | Fetch all secrets for environment |
| `refresh_cache()` | None | None | InfisicalConnectionError | Force cache refresh |
| `is_connected()` | None | bool | None | Test Infisical API connectivity |

**Example Usage**:
```python
# Initialization
client = InfisicalClient(config=InfisicalConfig(...))

# Retrieve secret
gmail_key = client.get_secret("GMAIL_API_KEY")
print(f"Retrieved from {gmail_key.source}")  # "infisical" or "cache"

# Test connectivity
if client.is_connected():
    print("Infisical API reachable")
```

---

## Relationships Diagram

```
┌─────────────────────────┐
│   InfisicalConfig       │
│                         │
│ - enabled: bool         │
│ - host: str             │
│ - project_id: str       │
│ - environment_slug: str │
│ - client_id: str        │
│ - client_secret: str    │
│ - cache_ttl: int        │
└───────────┬─────────────┘
            │ used by
            │
            ▼
┌─────────────────────────┐         ┌──────────────────────────┐
│   InfisicalClient       │ manages │     SecretCache          │
│                         │◄────────┤                          │
│ - _sdk_client           │         │ - secrets: dict          │
│ - _config               │         │ - last_updated: datetime │
│ - _cache                │         │ - ttl_seconds: int       │
│ - _authenticated: bool  │         └──────────────────────────┘
└───────────┬─────────────┘
            │ returns
            │
            ▼
┌─────────────────────────┐
│     SecretValue         │
│                         │
│ - key: str              │
│ - value: str            │
│ - environment: str      │
│ - source: str           │
│ - is_cached: bool       │
│ - retrieved_at: datetime│
└─────────────────────────┘
```

---

## Validation Rules

### Cross-Entity Validation

1. **InfisicalConfig Conditional Requirements**:
   - If `enabled=True`, then `project_id`, `environment_slug`, `client_id`, `client_secret` MUST be non-None
   - If `enabled=False`, other fields are ignored

2. **SecretCache Expiration**:
   - Cache is valid if: `(now - last_updated) <= ttl_seconds`
   - If `ttl_seconds=0`, cache is always expired (no caching)

3. **SecretValue Source Tracking**:
   - If `source="infisical"` and `is_cached=True`, this is a contradiction (should be `source="cache"`)
   - Valid combinations:
     - `source="infisical"` + `is_cached=False` (fresh from API)
     - `source="cache"` + `is_cached=True` (from cache)
     - `source="env_file"` + `is_cached=False` (fallback to .env)

4. **Environment Slug Consistency**:
   - InfisicalConfig.environment_slug MUST match environment where secrets are retrieved
   - Dev machine identity MUST NOT access prod environment secrets

---

## Data Flow

### Scenario 1: First Secret Retrieval (Cache Miss)

```
1. Settings.__init__() creates InfisicalClient(config)
2. InfisicalClient authenticates via Universal Auth
3. Settings calls client.get_secret("GMAIL_API_KEY")
4. InfisicalClient checks cache → MISS (empty)
5. InfisicalClient calls Infisical API → fetch secret
6. InfisicalClient updates cache: { "GMAIL_API_KEY": "value" }
7. InfisicalClient returns SecretValue(source="infisical", is_cached=False)
8. Settings uses secret value for gmail_api_key field
```

### Scenario 2: Cached Secret Retrieval (Cache Hit)

```
1. Settings calls client.get_secret("GMAIL_API_KEY")
2. InfisicalClient checks cache → HIT (found + not expired)
3. InfisicalClient returns SecretValue(source="cache", is_cached=True)
4. Total time: <10ms (no API call)
```

### Scenario 3: Infisical Unavailable (Fallback)

```
1. Settings calls client.get_secret("GMAIL_API_KEY")
2. InfisicalClient checks cache → MISS or EXPIRED
3. InfisicalClient calls Infisical API → Connection Error
4. InfisicalClient checks cache again → uses stale cache if available
5. If no cache: InfisicalClient falls back to os.getenv("GMAIL_API_KEY")
6. InfisicalClient returns SecretValue(source="env_file", is_cached=False)
7. Log WARNING: "Infisical unavailable, using .env fallback"
```

---

## Implementation Constraints

### Performance

- **Cache read latency**: <10ms (in-memory dictionary lookup)
- **API call latency**: 100-300ms (network dependent)
- **Total startup latency**: <500ms (SC-003) achieved via caching

### Security

- **No plaintext logging**: Secret values MUST NEVER appear in logs
- **Memory-only cache**: Secrets not persisted to disk
- **Environment isolation**: Dev machine identity cannot access prod secrets

### Compatibility

- **Backward compatibility**: .env file fallback ensures existing deployments continue working
- **Optional flag**: INFISICAL_ENABLED=false disables integration entirely

---

## Future Enhancements (Out of Scope for MVP)

- **Disk-persisted cache**: Survive application restarts
- **Secret rotation monitoring**: Detect when secrets change in Infisical
- **Multi-project support**: Fetch secrets from multiple Infisical projects
- **Folder-based organization**: Group secrets by service/component

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-01
**Next Artifact**: [contracts/infisical_client.yaml](contracts/infisical_client.yaml)
