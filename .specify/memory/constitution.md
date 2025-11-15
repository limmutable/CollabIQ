# CollabIQ Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Library-First
Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries

### II. CLI Interface
Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced

### IV. Integration Testing
Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas

### V. Observability
Text I/O ensures debuggability; Structured logging required

## Additional Constraints
Technology stack: Python 3.12+, LLMs: Google Gemini, Anthropic Claude, OpenAI (with `anthropic` and `openai` SDKs), CLI Framework: `Typer`, `rich`, `click`, Notion Integration: `notion-client`, Data Validation: `pydantic`, Retry Logic: `tenacity`, Fuzzy Matching: `rapidfuzz`, Package Manager: UV, Testing: `pytest`, Linting/Formatting: `ruff`, `mypy`

## Development Workflow
Code review requirements, testing gates, deployment approval process. All changes require corresponding tests and documentation updates. Pre-commit hooks enforce `ruff` and `mypy` checks.

## Governance
Constitution supersedes all other practices; Amendments require documentation, approval, migration plan. All PRs/reviews must verify compliance; Complexity must be justified.

**Version**: 1.0.0 | **Ratified**: 2025-11-13 | **Last Amended**: 2025-11-13
