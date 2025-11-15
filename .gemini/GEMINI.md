# CollabIQ Project Overview for Gemini

This document provides a comprehensive overview of the CollabIQ project, designed to serve as instructional context for the Gemini CLI agent.

## 1. Project Overview

CollabIQ is an **automated collaboration tracking system** that extracts collaboration activities from Korean/English emails and syncs them to Notion databases. It leverages Multi-LLM orchestration (Gemini, Claude, OpenAI) for intelligent entity extraction, semantic company matching, and dynamic classification. The system is built with robust error handling, secure secrets management (Infisical integration), and a comprehensive CLI for administration.

**Key Features:**
*   **Multi-LLM Orchestration:** Supports Gemini, Claude, and OpenAI with failover, health monitoring, quality-based routing, and cost tracking.
*   **Intelligent Entity Extraction:** Extracts 5 key entities (person, startup, partner, details, date) from emails with high accuracy.
*   **Smart Company Matching:** Semantically matches companies against Notion database entries.
*   **Automated Classification:** Classifies collaboration type and intensity, and generates concise summaries.
*   **Robust Error Handling:** Implements automatic retries, circuit breakers, and a Dead Letter Queue (DLQ).
*   **Notion Integration:** Handles duplicate detection, schema-aware field mapping, and relationship resolution.
*   **Secure Secrets Management:** Integrates with Infisical for centralized secret management, with fallback to local `.env` files.

**Core Technologies:**
*   **Language:** Python 3.12+
*   **LLMs:** Google Gemini, Anthropic Claude, OpenAI (with `anthropic` and `openai` SDKs)
*   **CLI Framework:** `Typer`, `rich`, `click`
*   **Notion Integration:** `notion-client` (official Notion Python SDK)
*   **Data Validation:** `pydantic`
*   **Retry Logic:** `tenacity` (with exponential backoff)
*   **Fuzzy Matching:** `rapidfuzz`
*   **Package Manager:** UV
*   **Testing:** `pytest`
*   **Linting/Formatting:** `ruff`, `mypy`

### Data Handling and Caching
*   **Email Extractions:** File-based JSON output to `data/extractions/{email_id}.json`.
*   **Notion Caching:** File-based JSON cache in `data/notion_cache/` for schema and data (with separate TTLs).
*   **LLM Metrics:** File-based JSON for provider health metrics and cost tracking in `data/llm_health/`.
*   **E2E Test Results:** File-based JSON for error reports, performance metrics, and test results in `data/e2e_test/`.
*   **Notion User List:** File-based JSON cache for Notion user lists (with TTL).

## 2. Building and Running

### Prerequisites
*   Python 3.12 or higher
*   UV package manager (install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)
*   At least one LLM API key (Gemini, Anthropic, or OpenAI)
*   Notion API integration token and database IDs
*   Gmail OAuth2 credentials

### Installation
```bash
# Clone repository
git clone <repo-url> # Replace <repo-url> with the actual repository URL
cd CollabIQ

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials.
# For detailed setup, refer to docs/setup/quickstart.md
```

### Setup
1.  **Configure `.env`**: Add your API keys and credentials.
2.  **Setup Gmail OAuth2**:
    ```bash
    uv run python scripts/authenticate_gmail.py
    ```
3.  **Verify Configuration**:
    ```bash
    uv run collabiq verify-infisical
    ```

### Running the Application (CLI Usage)
CollabIQ provides a comprehensive CLI for all operations. All commands are run using `uv run collabiq <command>`.

**Examples:**
*   **System Health Check:** `uv run collabiq status --detailed`
*   **Email Pipeline:** `uv run collabiq email fetch --limit 10`
*   **Notion Integration:** `uv run collabiq notion verify`
*   **Error Management:** `uv run collabiq errors retry --all`
*   **E2E Testing:** `uv run collabiq test e2e --limit 5`
*   **LLM Provider Management:** `uv run collabiq llm compare --detailed`

For complete CLI documentation, see `docs/CLI_REFERENCE.md`.

## 3. Testing

### Running Tests
```bash
# Run all tests
make test

# Run with coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run a specific test suite
uv run pytest tests/unit/test_gemini_adapter.py -v
```

### Linting and Formatting
```bash
# Lint code
make lint

# Format code
make format
```

## 4. Development Conventions

*   **Code Style:** Follow standard Python 3.12+ conventions.
*   **Specification-First:** Features begin with detailed specification documents.
*   **Workflow:** Implementation follows a `plan → tasks → code` workflow.
*   **Quality Assurance:** All changes require corresponding tests and documentation updates.
*   **Pre-commit Hooks:** Automated `ruff` and `mypy` checks are enforced via pre-commit hooks to maintain code quality.

## 6. Implementation Guidelines

*   **Modular Design:** Adhere to the existing modular structure within the `src/` directory, ensuring clear separation of concerns for new features or modifications.
*   **Pydantic Models:** Utilize Pydantic for defining and validating data structures, especially for API interactions and internal data flow, to maintain type safety and data integrity.
*   **LLM Abstraction:** When interacting with LLMs, leverage the `llm_provider` abstraction layer and extend existing `llm_adapters` or create new ones if a new provider is introduced. Avoid direct LLM API calls outside of the adapter layer.
*   **Error Handling:** Implement error handling using the patterns established in the `error_handling` module, including circuit breakers, retry mechanisms (e.g., `tenacity`), and structured logging.
*   **Configuration Management:** Manage application settings and secrets through the `config` module, utilizing Infisical integration where appropriate, or falling back to `.env` for local development.
*   **CLI Development:** For new CLI commands, follow the patterns established in `src/collabiq/commands/` and leverage `Typer` for command-line interface creation.

## 7. Testing Guidelines

*   **Test Organization:** Place tests in the appropriate subdirectories within `tests/`:
    *   `unit/`: For isolated testing of individual functions or classes.
    *   `integration/`: For testing interactions between multiple modules or external services (mocked).
    *   `e2e/`: For end-to-end tests that simulate real-world scenarios with actual API calls (where feasible and configured).
    *   `manual/`: For tests requiring specific manual setup or verification.
*   **Pytest Framework:** Use `pytest` for all testing. Leverage `conftest.py` for shared fixtures and test configurations.
*   **Test Coverage:** Strive for high test coverage, especially for new code. Use `pytest --cov=src --cov-report=html` to generate coverage reports.
*   **Fixtures:** Utilize `pytest` fixtures to set up test environments, mock dependencies, and provide reusable test data.
*   **Mocking:** Employ mocking judiciously for external dependencies (e.g., Notion API, Gmail API, LLM APIs) in unit and integration tests to ensure test isolation and speed.
*   **Pre-commit Hooks:** Ensure all new tests pass the pre-commit hooks (ruff, mypy) before committing.

## 5. Project Structure

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
│   └── models/                # Pydantic data models
├── tests/                     # Comprehensive test suites (unit, integration, e2e, manual)
├── docs/                      # Project documentation (setup, architecture, validation)
├── scripts/                   # Utility scripts
├── data/                      # Runtime data (emails, extractions, cache, DLQ)
└── .env.example               # Environment variable template
```
