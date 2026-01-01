# Technology Stack & Implementation Guide

**Status**: ✅ ACTIVE - Living document tracking implementation decisions
**Version**: 1.8.0
**Date**: 2026-01-01
**Last Updated**: Phase 018 Complete (Cloud Deployment)

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
- **Async Runtime**: asyncio (standard library) - **Full Pipeline Async**

### Core Libraries

| Library | Version | Purpose | Phase Added |
|---------|---------|---------|-------------|
| `pydantic` | ≥2.12.3 | Data validation, settings management | Phase 0 |
| `pydantic-settings` | ≥2.11.0 | Environment variable configuration | Phase 1a |
| `google-api-python-client` | ≥2.185.0 | Gmail API client | Phase 1a |
| `google-auth` | ≥2.41.1 | OAuth2 authentication | Phase 1a |
| `google-auth-oauthlib` | ≥1.2.2 | OAuth2 token management | Phase 1a |
| `google-cloud-storage` | ≥2.14.0 | GCS State Persistence | Phase 018 |
| `google-generativeai` | ≥0.8.5 | Gemini API client (Async support) | Phase 1b |
| `dateparser` | ≥1.2.0 | Multi-language date parsing | Phase 1b |
| `notion-client` | ≥2.6.0 | Notion API client (Async support) | Phase 2a |
| `email-validator` | ≥2.3.0 | Email address validation | Phase 1a |
| `rapidfuzz` | ≥3.14.1 | Fuzzy string matching (company matching, person matching) | Phase 1a, Phase 3d (014) |
| `typer` | ≥0.20.0 | CLI framework | Phase 1a |
| `rich` | ≥14.2.0 | CLI rich formatting | Phase 1a |
| `infisicalsdk` | Latest | Secret management SDK | Phase 3 (003-infisical-secrets) |
| `anthropic` | ≥0.42.0 | Claude API client (Anthropic SDK) | Phase 012 (Multi-LLM) |
| `openai` | ≥1.60.0 | OpenAI API client | Phase 012 (Multi-LLM) |
| `Jaro-Winkler` | Latest | Fuzzy string matching for consensus | Phase 012 (Multi-LLM) |

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
./scripts/setup/verify_setup.sh

# Run CLI
uv run collabiq verify
```

### Google Cloud Run Deployment (Phase 018 - Implemented)

**Architecture**: Cloud Run Jobs (Batch Processing)
**Registry**: Google Artifact Registry
**Secrets**: Google Secret Manager

**Configuration**: `Dockerfile`
- Multi-stage build using `python:3.12-slim-bookworm`
- UV package manager for fast, reproducible builds
- Optimized image size (~250MB)

**Deployment Workflow**:
1. **Build**: `docker build -t ... .`
2. **Push**: `docker push ...`
3. **Deploy Job**:
   ```bash
   gcloud run jobs create collabiq-processor \
     --image=${IMAGE_URL} \
     --command="collabiq" \
     --args="run" \
     --max-retries=3
   ```

**State Persistence**:
- **Daemon State**: Stored in Google Cloud Storage (`gs://{bucket}/daemon/state.json`) to prevent duplicate processing.
- **Environment Variable**: `GCS_STATE_BUCKET` must be set.

For full deployment instructions, see [docs/deployment/google-cloud-guide.md](../deployment/google-cloud-guide.md).


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

**Migration Effort**: Estimated 2-3 days (Future Phase)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.8.0 | 2026-01-01 | Phase 018 completion - Updated Deployment Configuration for Cloud Run Jobs, added `google-cloud-storage` dependency. |
| 1.7.0 | 2025-11-26 | Phase 017 test fixes - Fixed async/await in E2E and performance tests, corrected pytest fixtures, updated test coverage to 993 tests with 99%+ pass rate |
| 1.6.0 | 2025-11-22 | Phase 017 completion - Production readiness fixes, daemon mode, async pipeline |
| 1.5.0 | 2025-11-15 | Phase 015 completion - Updated test coverage section (99.6% pass rate), added Phase 015 technical debt, updated testing strategy with breakdown of 731 passing tests |
| 1.4.0 | 2025-11-09 | Phase 013 completion - Added Multi-LLM Support section (Anthropic, OpenAI, Gemini), quality metrics tracking, health monitoring, intelligent routing. Updated CLI commands, project structure, and core dependencies. |
| 1.3.0 | 2025-11-08 | Phase 010 completion - Added error handling & retry logic section, documented known technical debt for error classifier and test failures |
| 1.2.0 | 2025-11-03 | Phase 2c completion - Added classification & summarization patterns |
| 1.1.0 | 2025-11-01 | Phase 1b completion - Added Gemini entity extraction, CLI tool, accuracy validation |
| 1.0.0 | 2025-11-01 | Initial version after Phase 1a completion |

---

**Document Version**: 1.8.0
**Last Updated**: 2026-01-01
**Next Review**: After Phase 019 completion (Basic Reporting)