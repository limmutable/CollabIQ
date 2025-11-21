# CollabIQ Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-19

## Active Technologies
- **Python 3.12+** with UV package manager
- **Core Libraries**: pytest, pytest-cov, pytest-asyncio, pydantic, tenacity, rapidfuzz
- **APIs**: Gmail (google-api-python-client), Notion (notion-client), Gemini (google-generativeai), Claude (anthropic), OpenAI (openai)
- **CLI Framework**: Typer + Rich for terminal formatting
- **Secrets Management**: Infisical SDK (optional) with .env fallback
- Python 3.12+ (established in project) (017-production-readiness-fixes)
- File-based (JSON for user cache, daemon state, test reports, token storage with encryption) (017-production-readiness-fixes)

## Project Structure

```text
CollabIQ/
├── src/collabiq/          # Main application code
│   ├── adapters/          # LLM adapters (Gemini, Claude, OpenAI)
│   ├── commands/          # CLI command groups
│   ├── email_receiver/    # Gmail integration
│   ├── error_handling/    # Error management & retry logic
│   ├── models/            # Data models & validators
│   └── notion_integrator/ # Notion API integration
├── tests/                 # Test suite (989 tests, 86.5% pass rate)
│   ├── unit/             # 31 test files - isolated components
│   ├── integration/      # 33 test files - component interactions
│   ├── e2e/              # 3 test files - full pipeline
│   ├── contract/         # 20 test files - API contracts
│   ├── performance/      # 2 test files - benchmarks
│   └── fuzz/             # 2 test files - randomized input testing
├── docs/                  # Comprehensive documentation
│   ├── architecture/     # System design & roadmap
│   ├── cli/              # CLI reference & commands
│   ├── setup/            # Installation & configuration
│   └── testing/          # Testing guides & results
└── specs/                 # Feature specifications (Phases 001-016)
```

## Essential Commands

### Development
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest -m "not e2e"       # Skip E2E tests

# Code quality
ruff check .                     # Lint
ruff format .                    # Format
```

### CLI Operations
```bash
# Configuration management
uv run collabiq config show          # Display all config
uv run collabiq config validate      # Check required settings
uv run collabiq config test-secrets  # Test Infisical connection
uv run collabiq config get KEY       # Get specific value
```

## Code Style

- **Language**: Python 3.12+ with type hints
- **Formatting**: Ruff (configured in pyproject.toml)
- **Testing**: pytest with fixtures in src/collabiq/test_utils/
- **Documentation**: Google-style docstrings

## Recent Changes (Phases 014-016)
- **Phase 016** (2025-11-19): Project cleanup & refactoring
  - Created 6 README indexes for navigation
  - Registered CLI config commands
  - Documented 103 test files across 9 categories
  - Consolidated documentation structure

- **Phase 015** (2025-11-09): Test suite improvements
  - Added real E2E testing with Gmail/Notion
  - Simplified to production credentials only
  - 989 tests, 86.5% baseline pass rate

- **Phase 014** (2025-11-08): Enhanced field mapping
  - Added rapidfuzz for company/person matching
  - Notion user list caching with TTL
  - Companies database CRUD operations

## Quick Reference

### Testing Strategy
- **Unit Tests**: Fast (<0.1s), fully mocked, run on every commit
- **Integration Tests**: Moderate (0.1-5s), may use test databases
- **E2E Tests**: Slow (5-30s), real APIs with credentials, pre-merge validation
- **Contract Tests**: Validate external API contracts (Notion, Gmail)
- **Performance Tests**: Benchmark critical paths with defined thresholds

See [tests/README.md](tests/README.md) for detailed testing documentation.

### Documentation Links
- **Setup**: [docs/setup/quickstart.md](docs/setup/quickstart.md)
- **CLI Reference**: [docs/cli/CLI_REFERENCE.md](docs/cli/CLI_REFERENCE.md)
- **Architecture**: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- **Testing Guide**: [docs/testing/E2E_TESTING.md](docs/testing/E2E_TESTING.md)
- **Roadmap**: [docs/architecture/ROADMAP.md](docs/architecture/ROADMAP.md)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
