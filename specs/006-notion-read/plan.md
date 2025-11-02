# Implementation Plan: Notion Read Operations

**Branch**: `006-notion-read` | **Date**: 2025-11-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-notion-read/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements read-only integration with Notion API to retrieve company data from two databases ("Companies" and "CollabIQ") for LLM-based email processing. The system must discover database schemas dynamically, fetch all records with relationship resolution, implement local caching with TTL, respect API rate limits (3 req/sec), and format data for LLM consumption including company classification fields ("Shinsegae affiliates?" and "Is Portfolio?") to support collaboration type identification.

**Technical Approach**: Python-based NotionIntegrator component using the official Notion SDK (`notion-client`), file-based JSON caching with timestamp tracking, rate limiting via token bucket algorithm, and JSON/Markdown hybrid output format optimized for LLM prompts.

## Technical Context

**Language/Version**: Python 3.12 (established in project)
**Primary Dependencies**: `notion-client` (official Notion Python SDK), `pydantic` (data validation), `tenacity` (retry logic with exponential backoff)
**Storage**: File-based JSON cache in `data/notion_cache/` directory (schema cache + data cache with separate TTLs)
**Testing**: pytest with contract tests for Notion API integration, integration tests for cache behavior, unit tests for rate limiting and data formatting
**Target Platform**: macOS/Linux server (existing CollabIQ environment)
**Project Type**: Single project (extends existing `src/` structure)
**Performance Goals**: Schema discovery <10s, data retrieval <60s for 500 records, 95% cache hit rate, zero rate limit violations
**Constraints**: Notion API rate limit 3 req/sec, must handle 1000 records with 50 fields each, Unicode support (Korean/Japanese/emoji), relationship depth configurable (default 1 level)
**Scale/Scope**: 2 Notion databases, ~100-500 company records, ~20-50 fields per database, 1-5 relational fields, P1-P3 user stories over 2-3 days

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development
✅ **PASS**: Complete specification exists at [spec.md](spec.md) with:
- 6 user stories with acceptance criteria (P1-P3 priorities)
- 38 functional requirements (FR-001 through FR-038)
- 12 success criteria (SC-001 through SC-012)
- Technology-agnostic requirements
- No implementation started

### Principle II: Incremental Delivery via Independent User Stories
✅ **PASS**: User stories are prioritized and independently testable:
- **P1 - Schema Discovery**: Delivers complete data model, testable via schema validation
- **P1 - Data Retrieval with Relationships**: Delivers complete data access, testable via data completeness verification
- **P2 - Local Data Caching**: Delivers performance optimization, testable via cache hit rates
- **P2 - API Rate Limit Compliance**: Delivers stability, testable via rate limit monitoring
- **P2 - LLM-Ready Data Formatting**: Delivers LLM integration, testable via format validation
- **P3 - Error Recovery**: Delivers resilience, testable via fault injection

MVP = P1 stories (Schema Discovery + Data Retrieval) = Complete Notion integration with basic functionality

### Principle III: Test-Driven Development (TDD)
⚠️ **NEEDS VERIFICATION**: Specification requests integration tests (FR-027: logging, FR-032: visibility). TDD will be followed for:
- Contract tests for Notion API wrapper
- Integration tests for cache behavior
- Integration tests for rate limiting
- Unit tests for data formatting

**Tests will be written before implementation per TDD principle.**

### Principle IV: Design Artifact Completeness
✅ **PASS**: Planning phase completed all required artifacts:
- ✅ `plan.md` (this file)
- ✅ `research.md` (Phase 0 - completed)
- ✅ `data-model.md` (Phase 1 - completed)
- ✅ `quickstart.md` (Phase 1 - completed)
- ✅ `contracts/` (Phase 1 - completed: notion-api-wrapper.md, llm-data-format.md)
- ⏸️ `tasks.md` (Phase 2 - via `/speckit.tasks` command, not in planning scope)

### Principle V: Simplicity & Justification
✅ **PASS**: Solution uses minimal abstractions:
- Official Notion SDK (no custom API wrapper beyond necessary)
- File-based caching (no database overhead)
- Standard Python patterns (no custom frameworks)
- Direct JSON serialization (no ORM complexity)

**No complexity violations to justify.**

## Project Structure

### Documentation (this feature)

```text
specs/006-notion-read/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── notion-api-wrapper.md     # NotionIntegrator interface contract
│   └── llm-data-format.md        # LLM output format specification
├── checklists/
│   └── requirements.md  # Already created during /speckit.specify
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── notion_integrator/          # NEW: Notion integration module
│   ├── __init__.py
│   ├── client.py              # Notion API wrapper with rate limiting
│   ├── schema.py              # Schema discovery logic
│   ├── fetcher.py             # Data retrieval with pagination & relationships
│   ├── cache.py               # File-based caching with TTL
│   ├── formatter.py           # LLM-ready data formatting
│   └── models.py              # Pydantic data models
│
├── secrets_manager/           # EXISTING: Used for Notion API credentials
│   └── infisical_manager.py
│
└── collabiq/                  # EXISTING: CLI entry point
    └── __init__.py            # UPDATE: Add notion-related CLI commands

data/
└── notion_cache/              # NEW: Cache storage directory
    ├── schema_companies.json
    ├── schema_collabiq.json
    ├── data_companies.json
    └── data_collabiq.json

tests/
├── contract/
│   └── test_notion_api_integration.py    # NEW: Notion API contract tests
├── integration/
│   ├── test_notion_cache.py              # NEW: Cache behavior tests
│   └── test_notion_rate_limiting.py      # NEW: Rate limit compliance tests
└── unit/
    ├── test_notion_schema_parser.py      # NEW: Schema parsing tests
    └── test_notion_formatter.py          # NEW: Data formatting tests
```

**Structure Decision**: Extending existing single-project structure with new `src/notion_integrator/` module. This follows the established pattern of `src/email_receiver/`, `src/secrets_manager/`, etc. Cache storage goes in `data/` directory (existing pattern from `data/extractions/`). Tests follow existing `tests/{contract,integration,unit}/` structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No complexity violations. All constitution principles pass or are in expected progress state.
