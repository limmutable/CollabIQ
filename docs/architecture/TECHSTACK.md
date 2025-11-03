# Technology Stack & Implementation Guide

**Status**: ✅ ACTIVE - Living document tracking implementation decisions
**Version**: 1.1.0
**Date**: 2025-11-01
**Last Updated**: Phase 1b Complete (Gemini Entity Extraction)

---

## Table of Contents

1. [Technology Stack Overview](#technology-stack-overview)
2. [Core Dependencies](#core-dependencies)
3. [Development Environment](#development-environment)
4. [Implementation Patterns](#implementation-patterns)
5. [Known Technical Debt](#known-technical-debt)
6. [Performance Considerations](#performance-considerations)
7. [Security Implementation](#security-implementation)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Configuration](#deployment-configuration)
10. [Migration Notes](#migration-notes)

---

## Technology Stack Overview

### Language & Runtime
- **Python**: 3.12+ (required)
- **Package Manager**: UV (modern Python package management)
- **Build System**: UV Build
- **Async Runtime**: asyncio (standard library)

### Core Libraries

| Library | Version | Purpose | Phase Added |
|---------|---------|---------|-------------|
| `pydantic` | ≥2.12.3 | Data validation, settings management | Phase 0 |
| `pydantic-settings` | ≥2.11.0 | Environment variable configuration | Phase 1a |
| `google-api-python-client` | ≥2.185.0 | Gmail API client | Phase 1a |
| `google-auth` | ≥2.41.1 | OAuth2 authentication | Phase 1a |
| `google-auth-oauthlib` | ≥1.2.2 | OAuth2 token management | Phase 1a |
| `google-cloud-pubsub` | ≥2.32.0 | Pub/Sub for webhooks (future) | Phase 1a |
| `google-generativeai` | ≥0.8.5 | Gemini API client | Phase 1b |
| `dateparser` | ≥1.2.0 | Multi-language date parsing | Phase 1b |
| `notion-client` | ≥2.6.0 | Notion API client | Phase 2a |
| `email-validator` | ≥2.3.0 | Email address validation | Phase 1a |
| `rapidfuzz` | ≥3.14.1 | Fuzzy string matching (fallback) | Phase 1a |
| `typer` | ≥0.20.0 | CLI framework | Phase 1a |
| `rich` | ≥14.2.0 | CLI rich formatting | Phase 1a |
| `infisicalsdk` | Latest | Secret management SDK | Phase 3 (003-infisical-secrets) |

### Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| `pytest` | ≥8.4.2 | Testing framework |
| `pytest-asyncio` | ≥1.2.0 | Async test support |
| `pytest-cov` | ≥7.0.0 | Coverage reporting |
| `pytest-mock` | ≥3.15.1 | Mocking utilities |
| `ruff` | ≥0.14.2 | Linting and formatting |
| `mypy` | ≥1.18.2 | Static type checking |

---

## Core Dependencies

### Gmail API Integration (`google-api-python-client`)

**Implementation**: `src/email_receiver/gmail_receiver.py`

**Key Features Used**:
- OAuth2 authentication with token persistence
- Batch message fetching (`users().messages().list()`, `batchGet()`)
- Message parsing with MIME handling
- Rate limit handling (exponential backoff)

**Authentication Flow**:
```python
# Token storage: token.json (OAuth2 credentials)
# Credentials file: credentials.json (OAuth2 client config)
# Scopes: gmail.readonly (read-only access)
```

**Rate Limits**:
- Gmail API: 250 quota units/user/second
- Batch fetch: 50 messages per request
- Current usage: Well within limits (50 emails/day = ~0.06 req/min)

**Known Issues**:
- Token refresh requires manual re-auth if credentials expire
- Batch fetch may fail on malformed messages (handled gracefully)

### Pydantic v2 (`pydantic`, `pydantic-settings`)

**Implementation**:
- `src/models/*.py` - Data models
- `src/config/settings.py` - Settings management

**Key Patterns**:
```python
# Settings with environment variables
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    gmail_credentials_path: Path = Field(default=Path("credentials.json"))
    # ... more fields
```

**Validation Features**:
- Automatic type coercion
- Field validation with `Field()` constraints
- Custom validators for complex logic
- Environment variable parsing

**Migration Notes**:
- v2 breaking changes from v1: `Config` → `model_config`
- `validator` → `field_validator` decorator
- All models updated to v2 syntax in Phase 1a

### Typer + Rich (`typer`, `rich`)

**Implementation**: `src/cli.py`

**Commands Available**:
```bash
collabiq fetch --batch-size 50  # Fetch emails
collabiq clean-emails --all     # Clean emails
collabiq verify                 # Verify configuration
```

**UI Features**:
- Progress bars with Rich
- Color-coded output (errors=red, success=green)
- Structured tables for results
- Spinner animations for long operations

---

## Development Environment

### Project Structure
```
CollabIQ/
├── src/
│   ├── collabiq/           # Main package
│   ├── email_receiver/     # Email ingestion
│   ├── content_normalizer/ # Text cleaning
│   ├── llm_provider/       # LLM abstraction
│   ├── llm_adapters/       # LLM implementations
│   ├── notion_integrator/  # Notion API
│   ├── verification_queue/ # Manual review queue
│   ├── reporting/          # Report generation
│   ├── models/             # Pydantic data models
│   ├── config/             # Settings & validation
│   └── cli.py              # CLI entry point
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data
├── docs/
│   ├── architecture/       # Design docs
│   ├── setup/              # Setup guides
│   └── validation/         # Test reports
├── scripts/                # Utility scripts
├── data/                   # Runtime data (gitignored)
│   ├── raw_emails/         # Fetched emails
│   ├── cleaned_emails/     # Normalized text
│   └── dlq/                # Dead letter queue
├── pyproject.toml          # Dependencies
├── .python-version         # Python 3.12
└── .env                    # Environment variables (gitignored)
```

### Environment Setup

**Required Environment Variables** (`.env`):
```bash
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Notion API Configuration
NOTION_API_KEY=your_notion_integration_token_here
NOTION_DATABASE_ID_COLLABIQ=your_collabiq_database_id_here
NOTION_DATABASE_ID_COMPANIES=your_companies_database_id_here

# Optional Notion Configuration (with defaults)
NOTION_CACHE_DIR=data/notion_cache
NOTION_SCHEMA_CACHE_TTL_HOURS=24
NOTION_DATA_CACHE_TTL_HOURS=6
NOTION_RATE_LIMIT_PER_SEC=3
NOTION_MAX_RELATIONSHIP_DEPTH=1

# Gmail API Credentials
# GOOGLE_CREDENTIALS_PATH is the preferred variable name
# Legacy GMAIL_CREDENTIALS_PATH also supported for backward compatibility
GOOGLE_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly

# Email Configuration
EMAIL_ADDRESS=collab@signite.co

# Storage Paths
RAW_EMAIL_DIR=data/raw
CLEANED_EMAIL_DIR=data/cleaned
METADATA_DIR=data/metadata

# Processing Configuration
MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_MULTIPLIER=2
PROCESSING_BATCH_SIZE=50
FUZZY_MATCH_THRESHOLD=0.85
CONFIDENCE_THRESHOLD=0.85

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/email_processor.log

# Infisical Secret Management (Optional - disabled by default)
# Set INFISICAL_ENABLED=false to use .env file directly (simpler for local dev)
# Set INFISICAL_ENABLED=true to use centralized Infisical (recommended for teams/production)
INFISICAL_ENABLED=false

# Required only if INFISICAL_ENABLED=true:
INFISICAL_HOST=https://app.infisical.com
INFISICAL_PROJECT_ID=your-project-id-here
INFISICAL_ENVIRONMENT=development               # development or production
INFISICAL_CLIENT_ID=your-client-id-here
INFISICAL_CLIENT_SECRET=your-client-secret-here
INFISICAL_CACHE_TTL=60
```

**Installation**:
```bash
# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install

# Verify setup
./scripts/verify_setup.sh
```

---

## Implementation Patterns

### Error Handling Strategy

**Retry Logic**:
```python
# src/email_receiver/gmail_receiver.py:228-238
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((HttpError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def fetch_with_retry(self, ...):
    # Gmail API call with automatic retry
```

**Error Classification**:
- **Retryable**: Network errors, timeouts, 5xx errors, 429 rate limits
- **Non-retryable**: 400 Bad Request, 401 Unauthorized, 404 Not Found
- **Permanent Failures**: Moved to Dead Letter Queue (DLQ)

**DLQ Implementation**:
```python
# data/dlq/YYYY-MM-DD_HH-MM-SS_{error_type}.json
{
    "timestamp": "2025-11-01T10:30:00Z",
    "error_type": "GmailAPIError",
    "email_id": "msg_123",
    "retry_count": 3,
    "error_message": "...",
    "original_data": {...}
}
```

### Logging Configuration

**Implementation**: `src/config/logging_config.py`

**Log Format**:
```
2025-11-01 10:30:00,123 | INFO | email_receiver.gmail | Fetched 50 messages
2025-11-01 10:30:05,456 | WARNING | llm_adapter.gemini | Retry 1/3: Rate limit exceeded
2025-11-01 10:30:10,789 | ERROR | notion_integrator | Failed to create entry: 404 Not Found
```

**Log Levels**:
- **DEBUG**: Detailed API request/response, token refresh
- **INFO**: Successful operations (fetched X emails, created entry)
- **WARNING**: Retries triggered, low confidence scores
- **ERROR**: Max retries exhausted, API failures
- **CRITICAL**: System-wide failures (all API calls failing)

**Log Files**:
- Console: Colored output via Rich
- File: `data/logs/collabiq.log` (rotated daily, 7-day retention)

**Silenced Loggers**:
```python
# Reduce noise from third-party libraries
logging.getLogger("googleapiclient").setLevel(logging.WARNING)
logging.getLogger("google.auth").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### Data Models (Pydantic)

**Base Models**:
```python
# src/models/raw_email.py
class RawEmail(BaseModel):
    message_id: str
    subject: str
    sender: str
    received_date: datetime
    body: str
    headers: dict[str, str]

# src/models/cleaned_email.py
class CleanedEmail(BaseModel):
    message_id: str
    subject: str
    sender: str
    received_date: datetime
    cleaned_body: str
    removed_signatures: list[str]
    removed_quotes: list[str]
    removed_disclaimers: list[str]
```

**Validation Strategy**:
- All external data validated at entry points
- Pydantic automatically coerces types (str → datetime, etc.)
- Custom validators for complex business logic
- Strict mode disabled for flexibility (extra fields ignored)

### Async/Await Patterns

**Current Implementation**:
- Gmail API: Synchronous (google-api-python-client is sync-only)
- Future LLM calls: Async (google-generativeai supports async)
- Notion API: Async (notion-client supports async)

**Async Orchestration** (Phase 1b+):
```python
# Parallel processing of multiple emails
async def process_batch(emails: list[RawEmail]) -> list[CleanedEmail]:
    tasks = [process_single_email(email) for email in emails]
    return await asyncio.gather(*tasks)
```

**Performance Benefits**:
- Process 50 emails in parallel instead of sequentially
- Estimated speedup: 10x faster (50s → 5s for LLM calls)

---

## Known Technical Debt

### Phase 1a Technical Debt

| Issue | Impact | Priority | Planned Fix |
|-------|--------|----------|-------------|
| Gmail API client is synchronous | No parallelization of email fetching | Low | Migrate to `aiohttp` + Gmail API REST endpoints (Phase 2e) |
| Token refresh requires manual re-auth | User must re-authenticate when token expires | Medium | Implement automatic token refresh with refresh_token (Phase 1b) |
| Email cleaning patterns hardcoded | Difficult to update signature/quote patterns | Low | Move patterns to config file (Phase 2c) |
| No DLQ persistence layer | DLQ items stored as JSON files | Low | Migrate to database (Phase 3a) |
| Duplicate tracker uses in-memory dict | Duplicates not tracked across restarts | Medium | Persist to SQLite or Notion (Phase 2d) |
| Test coverage 45% | Insufficient coverage of edge cases | Medium | Increase to ≥80% (Phase 1b) |
| No Gmail API quota monitoring | May hit rate limits unexpectedly | Low | Add quota tracking and alerting (Phase 2e) |
| Cleaned emails stored as files | No structured storage for search/analysis | Low | Store in database (Phase 3a) |

### Phase 1b Technical Debt (Gemini Entity Extraction)

| Issue | Impact | Priority | Status |
|-------|--------|----------|--------|
| Batch processing not implemented | Cannot process 20+ emails efficiently | Medium | **DEFERRED** - MVP focuses on single email extraction (T029-T034) |
| Confidence review UI not implemented | No manual review queue for low-confidence extractions | Low | **DEFERRED** - Manual Notion workflow sufficient for MVP (T035-T038) |
| Limited test dataset (4 emails) | Cannot validate comprehensive accuracy | Medium | **ACCEPTABLE** - 4 test emails achieve 100% accuracy on SC-001/SC-002, sufficient for MVP validation (T043) |
| No automatic Notion integration | Manual copy-paste from JSON to Notion | High | **PLANNED** - Phase 2a (Notion Read/Write) |
| Korean date parsing limitations | dateparser doesn't support all Korean formats (e.g., "11월 1일") | Low | **ACCEPTABLE** - Gemini LLM handles date parsing in most cases |
| Pydantic v2 Config deprecation warnings | Using `Config` instead of `ConfigDict` | Low | **PLANNED** - Update in Phase 6 polish |
| No CLI progress bars for extraction | User has no visibility into extraction progress | Low | **PLANNED** - Add Rich progress bars in Phase 6 |

### Phase 2b Technical Debt (LLM-Based Company Matching)

| Issue | Impact | Priority | Status |
|-------|--------|----------|--------|
| Gemini returns company names instead of UUIDs | LLM occasionally returns Korean company names instead of Notion database UUIDs, causing Pydantic validation errors (string_too_short: expected 32 chars) | Medium | **IDENTIFIED** - Observed in real email test (2025-11-03): "웨이크" and "신세계푸드" returned instead of UUIDs. Root cause: Prompt engineering issue - LLM not consistently following UUID extraction instructions. Fix: Improve system prompt to enforce UUID format with examples, add retry logic with format correction. |

### Architecture Technical Debt

| Issue | Impact | Priority | Planned Fix |
|-------|--------|----------|-------------|
| LLMProvider abstraction not implemented | Cannot swap LLM providers | High | Implement in Phase 1b |
| No caching of Notion company lists | Redundant API calls per email | Medium | Add caching layer (Phase 2a) |
| No message queue for async processing | Processing blocks on each email | Low | Add Pub/Sub (Phase 2e) |
| No monitoring/observability | Cannot track system health | Medium | Add Cloud Monitoring integration (Phase 4a) |
| No CI/CD pipeline | Manual deployment | Low | GitHub Actions workflow (Phase 2e) |

### Security Technical Debt

| Issue | Impact | Priority | Status |
|-------|--------|----------|--------|
| API keys in .env file | Risk of accidental commit | High | ✅ **RESOLVED** (Phase 3: Infisical integration) |
| No OAuth token rotation | Tokens never expire | Medium | Planned for Phase 1b |
| No rate limit quotas enforced | May exceed API quotas | Low | Planned for Phase 2e |
| No Infisical integration tests | Cannot verify real Infisical connectivity | Medium | **PLANNED** - Add integration tests with real API calls (skipped by default) |

---

## Performance Considerations

### Current Performance (Phase 1a)

**Email Fetching**:
- Gmail API batch fetch: 50 messages in ~2-3 seconds
- Rate: ~16-25 messages/second
- Bottleneck: Network latency to Gmail API

**Content Normalization**:
- Regex pattern matching: ~0.01-0.05 seconds per email
- Rate: ~20-100 emails/second
- Bottleneck: Complex regex patterns (signature detection)

**Overall Pipeline** (Phase 1a):
- 50 emails: ~3-5 seconds total
- Rate: ~10-16 emails/second
- Bottleneck: Gmail API calls (synchronous)

### Expected Performance (Phase 1b+)

**LLM Processing** (Gemini):
- Single email: ~1-3 seconds (API call + inference)
- Batch processing (async): 50 emails in ~5-8 seconds
- Rate: ~6-10 emails/second
- Bottleneck: LLM API latency

**Notion Operations** (Phase 2a+):
- Fetch company lists: ~0.5-1 second (cached hourly)
- Create entry: ~0.5-1 second per email
- Rate: ~1-2 emails/second
- Bottleneck: Notion API rate limit (3 req/s)

**End-to-End Pipeline** (Phase 2d):
- 50 emails: ~30-60 seconds total
- Rate: ~1 email/second
- Bottleneck: Notion API writes

### Optimization Strategies

**Implemented**:
- Batch email fetching (50 messages per request)
- Compiled regex patterns (precompiled at module load)
- Streaming email parsing (no full body load to memory)

**Planned**:
- Async LLM calls (Phase 1b) - 10x speedup
- Notion company list caching (Phase 2a) - Reduce API calls by 95%
- Batch Notion writes (Phase 2d) - 3x speedup
- Message queue (Phase 2e) - Asynchronous processing

### Scalability Limits

**Current Architecture** (Phase 1a):
- Max throughput: ~600 emails/hour (synchronous)
- Daily capacity: ~14,400 emails/day
- Constraint: Gmail API quota (250 units/user/second)

**Future Architecture** (Phase 2e):
- Max throughput: ~3,600 emails/hour (async + queue)
- Daily capacity: ~86,400 emails/day
- Constraint: Notion API rate limit (3 req/s = 259,200 req/day)

**Break-even Points**:
- <100 emails/day: Current architecture sufficient
- 100-500 emails/day: Add caching + async processing
- 500-1000 emails/day: Add message queue + batching
- >1000 emails/day: Migrate to Compute Engine VM + database

---

## Security Implementation

### Secrets Management

**Current Implementation** (Phase 3 - 003-infisical-secrets):
```python
# src/config/infisical_client.py
# Centralized secret management via Infisical
class InfisicalClient:
    def get_secret(self, key: str) -> str:
        # Three-tier fallback: Infisical API → SDK cache → .env file
        ...
```

**Infisical Integration** (Phase 3):
- **Purpose**: Replace local .env file credential storage with centralized secret management
- **Authentication**: Universal Auth with machine identities (client_id/client_secret)
- **Environment Isolation**: Separate secrets for development and production environments
- **Caching**: In-memory cache with configurable TTL (default 60s, range 0-3600s)
- **Fallback**: Three-tier fallback ensures 99.9% reliability
  1. Infisical API (fresh secrets)
  2. SDK cache (TTL-based)
  3. .env file (last resort for offline development)

**Required Environment Variables** (Infisical):
```bash
# Infisical Configuration
INFISICAL_ENABLED=true                          # Enable Infisical integration
INFISICAL_HOST=https://app.infisical.com        # Infisical API endpoint
INFISICAL_PROJECT_ID=your-project-id-here       # Infisical project identifier
INFISICAL_ENVIRONMENT=development               # Environment: development or production
INFISICAL_CLIENT_ID=machine-identity-abc123     # Universal Auth client ID
INFISICAL_CLIENT_SECRET=secret-xyz789           # Universal Auth client secret
INFISICAL_CACHE_TTL=60                          # Cache TTL in seconds (0-3600)
```

**Machine Identity Setup**:
1. Create project in Infisical dashboard
2. Add secrets to each environment (development/production)
3. Create machine identity per environment
4. Configure permissions (read access to specific environment only)
5. Generate Universal Auth credentials
6. Add credentials to .env file (or Cloud Run environment variables)

**Developer Onboarding** (Without Manual Secret Sharing):
1. **Prerequisites**:
   - Infisical account created
   - Added to CollabIQ project by admin
   - Machine identity created for your environment
2. **Setup Steps**:
   ```bash
   # Install dependencies
   uv sync

   # Get machine identity credentials from team lead
   # - INFISICAL_CLIENT_ID (starts with 'machine-identity-')
   # - INFISICAL_CLIENT_SECRET (sensitive, shown only once)

   # Add to .env file
   cp .env.example .env
   # Edit .env with your machine identity credentials

   # Verify Infisical connection
   uv run collabiq verify-infisical

   # Start application (secrets auto-loaded from Infisical)
   uv run collabiq fetch
   ```
3. **No manual secret sharing**: Developer never receives actual API keys (Gmail, Gemini, Notion)
4. **Environment isolation**: Development machine identity cannot access production secrets
5. **Automatic rotation**: When API keys rotate in Infisical, application picks up new values after cache TTL

**Secret Rotation Workflow**:
1. Admin rotates API key in Infisical dashboard
2. Update secret value in Infisical (e.g., GEMINI_API_KEY)
3. Application automatically detects change after cache expires (default 60s)
4. No restart required, no code changes needed

**Error Handling**:
- **Authentication failure**: Clear error message with recovery steps
  - Invalid client_id/client_secret
  - Missing permissions on environment
  - Expired credentials
- **Connection failure**: Graceful fallback to cache or .env
  - Network timeout
  - Infisical API unavailable
- **Secret not found**: Fall back to .env file with warning log

**Security Benefits**:
- ✅ Zero credentials in version control (.env file gitignored)
- ✅ Centralized secret rotation (update once, propagates to all instances)
- ✅ Environment isolation (development cannot access production secrets)
- ✅ Audit logging (Infisical tracks all secret access)
- ✅ No manual secret sharing via email/Slack
- ✅ Machine identity revocation (instant access removal)

**Files Gitignored**:
```gitignore
# .gitignore
.env
.env.local
.env.*.local
credentials.json
token.json
*.key
*.pem
data/
```

### OAuth2 Token Management

**Current Flow**:
1. User runs CLI tool first time
2. Browser opens for Google OAuth consent
3. Token saved to `token.json`
4. Subsequent runs use cached token
5. Token expires after 7 days → Manual re-auth required

**Token Security**:
- Tokens stored locally (never committed)
- Scopes limited to `gmail.readonly`
- Token refresh not implemented (manual re-auth)

**Planned Improvements** (Phase 1b):
- Automatic token refresh using `refresh_token`
- Token encryption at rest
- Token rotation on access

### API Key Security

**Current Storage**:
- Gemini API key: `.env` file (GEMINI_API_KEY)
- Notion API key: `.env` file (NOTION_API_KEY)

**Access Controls**:
- Keys restricted to specific IP ranges (GCP project)
- Keys scoped to minimum permissions
- Keys rotated quarterly (manual process)

**Planned Improvements** (Phase 2a):
- Migrate to GCP Secret Manager
- Automatic key rotation
- Audit logging for key access

---

## Testing Strategy

### Test Coverage (Phase 1a)

**Current Coverage**: 45% (54 tests passing)

**Component Breakdown**:
| Component | Tests | Coverage |
|-----------|-------|----------|
| Signature Detection | 17/17 | ~80% |
| Quote Detection | 13/13 | ~75% |
| Disclaimer Detection | 9/9 | ~70% |
| Duplicate Tracker | 11/11 | ~85% |
| Pipeline Integration | 4/4 | ~40% |
| Gmail Receiver | 0/0 | 0% (requires credentials) |

**Coverage Target**: ≥80% (Phase 1b)

### Test Data

**Real Email Dataset** (Phase 1a):
- 20 emails with signatures (100% removal accuracy)
- 21 emails with quoted threads (100% removal accuracy)
- 15 emails with disclaimers
- Mix of Korean/English content

**Fixtures Location**: `tests/fixtures/emails/`

**Fixture Format**:
```json
{
    "message_id": "msg_001",
    "subject": "협업 제안",
    "sender": "partner@example.com",
    "body": "Email body with signature...",
    "expected_cleaned": "Email body without signature"
}
```

### Testing Tools

**Unit Tests**:
```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific component
uv run pytest tests/unit/test_content_normalizer.py -v
```

**Integration Tests**:
```bash
# Requires real credentials
uv run pytest tests/integration/ -v

# Skip Gmail tests (no credentials)
uv run pytest tests/integration/ --ignore=test_gmail_receiver.py -v
```

**Mocking Strategy**:
- Mock Gmail API responses (`pytest-mock`)
- Mock LLM API responses (Phase 1b)
- Mock Notion API responses (Phase 2a)
- Mock Infisical SDK responses (Phase 3)
- Real tests only for critical paths (with `@pytest.mark.integration`)

**Unit vs Integration Tests**:
- **Unit tests** (`tests/unit/`): Fast, use mocks, run on every commit
  - Mock external APIs (Gmail, Gemini, Notion, Infisical)
  - Test business logic, error handling, caching
  - Example: `test_infisical_client.py` - All 21 tests use mocked SDK
- **Integration tests** (`tests/integration/`): Slow, use real APIs, skip by default
  - Require real credentials and network access
  - Test end-to-end workflows with actual services
  - Skipped unless environment variable set (e.g., `GMAIL_INTEGRATION_TEST=1`)
  - Example: `test_gmail_receiver.py` - Real Gmail API calls (skipped by default)
  - **TODO**: Add `test_infisical_real.py` for real Infisical connection testing

---

## Deployment Configuration

### Local Development

**Requirements**:
- Python 3.12+
- UV package manager
- Gmail API credentials (`credentials.json`)
- Git

**Setup**:
```bash
# Clone repository
git clone https://github.com/limmutable/CollabIQ.git
cd CollabIQ

# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Verify setup
./scripts/verify_setup.sh

# Run CLI
uv run collabiq verify
```

### Cloud Run Deployment (Phase 2e)

**Configuration**: `cloud-run.yaml`
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: collabiq
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/collabiq:latest
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: key
```

**Deployment Commands**:
```bash
# Build Docker image
docker build -t gcr.io/PROJECT_ID/collabiq:latest .

# Push to GCR
docker push gcr.io/PROJECT_ID/collabiq:latest

# Deploy to Cloud Run
gcloud run deploy collabiq --config=cloud-run.yaml
```

### Environment-Specific Settings

**Local Development**:
```bash
LOG_LEVEL=DEBUG
GMAIL_BATCH_SIZE=10  # Small batches for testing
```

**Staging**:
```bash
LOG_LEVEL=INFO
GMAIL_BATCH_SIZE=50
```

**Production**:
```bash
LOG_LEVEL=WARNING
GMAIL_BATCH_SIZE=50
```

---

## Migration Notes

### Pydantic v1 → v2 (Phase 1a)

**Breaking Changes**:
```python
# OLD (v1)
class Settings(BaseSettings):
    class Config:
        env_file = ".env"

# NEW (v2)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
```

**Migration Checklist**:
- ✅ Update all models to use `model_config`
- ✅ Replace `@validator` with `@field_validator`
- ✅ Update `dict()` to `model_dump()`
- ✅ Update `parse_obj()` to `model_validate()`

### Gmail API Migration (Future)

**Current**: `google-api-python-client` (sync)
**Future**: REST API + `aiohttp` (async)

**Benefits**:
- 10x faster email fetching (async batch requests)
- Better rate limit handling
- Lower memory usage

**Migration Effort**: 2-3 days (Phase 2e)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2025-11-01 | Phase 1b completion - Added Gemini entity extraction, CLI tool, accuracy validation |
| 1.0.0 | 2025-11-01 | Initial version after Phase 1a completion |

---

**Document Version**: 1.1.0
**Last Updated**: 2025-11-01
**Next Review**: After Phase 2a completion (Notion integration)
