# CollabIQ - Gemini AI Context

Last updated: 2025-11-21

## Project Overview

CollabIQ is an email-to-Notion automation system that processes collaboration emails and stores structured data in Notion databases.

## Active Technologies
- Python 3.12+ + uv (package manager), Google Cloud SDK (CLI tools), potentially `google-cloud-storage`, `google-cloud-run` client libraries. (018-deploy-google-cloud)
- File-based JSON for extractions, caching, metrics (current project); will need persistent storage on Google Cloud (e.g., Cloud Storage, Persistent Disks for Compute Engine). (018-deploy-google-cloud)

- **Python 3.12+** with UV package manager
- **Core Libraries**: pytest, pytest-cov, pytest-asyncio, pydantic, tenacity, rapidfuzz
- **APIs**: Gmail, Notion, Gemini (primary LLM), Claude, OpenAI
- **CLI Framework**: Typer + Rich
- **Storage**: File-based JSON for extractions, caching, metrics

## Key Features

1. **Multi-LLM Orchestration**: Failover, consensus, best-match strategies with Gemini, Claude, OpenAI
2. **Email Processing**: Gmail OAuth2 → Content cleaning → LLM extraction → Notion write
3. **Smart Matching**: Fuzzy company/person matching with confidence scoring
4. **CLI Tools**: Configuration management, testing, validation commands
5. **Test Suite**: 989 tests across 9 categories (unit, integration, e2e, contract, performance, fuzz)

## Recent Changes (Phases 014-017)

- **Phase 017** (2025-11-22): Production Readiness Fixes
  - Resolved async event loop issues in LLM orchestration
  - Verified Notion schema integration (Person matching relaxed)
  - 100% E2E Success Rate in Production Mode (5/5 emails)

- **Phase 016** (2025-11-19): Project cleanup & refactoring

  - Documentation reorganization with 6 README indexes
  - CLI config command registration
  - Test suite documentation (103 test files)

- **Phase 015** (2025-11-09): Test suite improvements

  - Real E2E testing with production Gmail/Notion
  - 989 tests, 86.5% baseline pass rate

- **Phase 014** (2025-11-08): Enhanced field mapping
  - Fuzzy company/person matching with rapidfuzz
  - Notion user caching, Companies database CRUD

## Essential Commands

```bash
# Development
uv sync                          # Install dependencies
uv run pytest                    # Run all tests
uv run pytest -m "not e2e"       # Skip E2E tests
ruff check . && ruff format .    # Lint & format

# CLI Operations
uv run collabiq config show      # Show configuration
uv run collabiq config validate  # Validate settings
```

## Project Structure

The project follows a modular structure:

```
CollabIQ/
├── src/
│   ├── collabiq/              # Main CLI application logic
│   ├── config/                # Configuration & secrets management
│   ├── llm_provider/          # LLM abstraction layer
│   ├── llm_adapters/          # Specific LLM provider implementations (Gemini, Claude, OpenAI)
│   ├── llm_orchestrator/      # Multi-LLM orchestration, health & cost tracking
│   ├── email_receiver/        # Gmail API integration
│   ├── content_normalizer/    # Email cleaning pipeline
│   ├── notion_integrator/     # Notion API client (read + write)
│   ├── error_handling/        # Unified retry system & circuit breakers
│   ├── models/                # Pydantic data models
│   ├── reporting/             # Reporting and metrics generation
│   ├── verification_queue/    # Queue system for human verification
│   └── e2e_test/              # E2E testing utilities and logic
├── tests/                     # Comprehensive test suites (unit, integration, e2e, manual)
├── docs/                      # Project documentation (setup, architecture, validation)
├── scripts/                   # Utility scripts
├── data/                      # Runtime data (emails, extractions, cache, DLQ)
└── .env.example               # Environment variable template
```

## Documentation Structure

- **Setup**: [docs/setup/quickstart.md](docs/setup/quickstart.md)
- **CLI**: [docs/cli/CLI_REFERENCE.md](docs/cli/CLI_REFERENCE.md)
- **Testing**: [tests/README.md](tests/README.md)
- **Architecture**: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- **Roadmap**: [docs/architecture/ROADMAP.md](docs/architecture/ROADMAP.md)
