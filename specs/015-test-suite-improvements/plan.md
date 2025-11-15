# Implementation Plan: Test Suites Improvements

**Branch**: `015-test-suite-improvements` | **Date**: 2025-11-11 | **Spec**: /Users/jlim/Projects/CollabIQ/specs/015-test-suite-improvements/spec.md
**Input**: Feature specification from `/specs/015-test-suite-improvements/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan details the implementation of the "Test Suites Improvements" feature as specified in `/Users/jlim/Projects/CollabIQ/specs/015-test-suite-improvements/spec.md`. It focuses on enhancing the CollabIQ project's testing infrastructure, including end-to-end automated testing, date extraction robustness, LLM performance optimization for Korean text, granular test coverage, formalized performance testing, and expanded negative testing and fuzzing capabilities.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: `pytest`, `pytest-cov`, `tenacity`, `rapidfuzz`, `notion-client`, `anthropic`, `openai`  
**Storage**: File-based JSON for email extractions, Notion caching, LLM metrics, E2E test results, Notion user list  
**Testing**: `pytest` (unit, integration, E2E), `pytest-cov` (for coverage), `tenacity` (for retry logic in E2E tests), `rapidfuzz` (for fuzzy matching in E2E tests)  
**Target Platform**: Linux server  
**Project Type**: Single project (Python CLI application)  
**Performance Goals**: Average email processing time under 5 seconds, LLM response times under 3 seconds  
**Constraints**: N/A  
**Scale/Scope**: Focused on improving testing infrastructure for existing CollabIQ system, handling low email volume (0-5 emails/day).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ COMPLIANT (with remediation applied)

The project constitution defines 5 core principles:

1. **Library-First**: ✅ New modules (date_parser, llm_benchmarking, test_utils) structured as standalone libraries per spec
2. **CLI Interface**: ✅ All new libraries include CLI interfaces with text I/O protocol (see Library Interfaces section)
3. **Test-First**: ✅ Tasks organized with TDD workflow: write tests → fail → implement
4. **Integration Testing**: ✅ Contract tests planned for all new library interfaces
5. **Observability**: ✅ Structured logging maintained throughout

**Technology Stack Compliance**: Python 3.12+, pytest, pydantic, tenacity, rapidfuzz, notion-client, anthropic, openai, Typer, rich, click - all aligned with constitution requirements.

## Project Structure

### Documentation (this feature)

```text
specs/015-test-suite-improvements/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── collabiq/              # Main CLI application logic (existing)
│   ├── commands/          # CLI commands
│   ├── formatters/        # Output formatters
│   │
│   ├── date_parser/       # NEW LIBRARY: Date parsing and normalization
│   │   ├── __init__.py    # Library exports: parse_date(), normalize_date()
│   │   ├── parser.py      # Core date parsing logic (supports Korean/English)
│   │   ├── models.py      # Pydantic models: ParsedDate, DateFormat
│   │   ├── cli.py         # CLI interface: stdin (raw text) → stdout (JSON/text)
│   │   └── README.md      # Library documentation with examples
│   │
│   ├── llm_benchmarking/  # NEW LIBRARY: LLM performance benchmarking
│   │   ├── __init__.py    # Library exports: run_benchmark(), compare_prompts()
│   │   ├── suite.py       # Benchmarking suite logic
│   │   ├── prompts.py     # Prompt variations for testing
│   │   ├── ab_testing.py  # A/B testing framework for prompt comparison
│   │   ├── metrics.py     # Performance metrics: accuracy, confidence, speed
│   │   ├── cli.py         # CLI interface: args (provider, dataset) → stdout (results)
│   │   └── README.md      # Library documentation with usage examples
│   │
│   └── test_utils/        # NEW LIBRARY: Testing utilities
│       ├── __init__.py    # Library exports: cleanup_notion(), fuzz_input(), assert_performance()
│       ├── notion_cleanup.py  # Robust Notion test entry cleanup with idempotency
│       ├── performance_monitor.py  # Performance metric collection and assertions
│       ├── fuzz_generator.py  # Input generation for fuzz testing
│       ├── cli.py         # CLI interface for cleanup/monitoring operations
│       └── README.md      # Library documentation
│
├── config/                # Configuration & secrets management (existing)
├── llm_provider/          # LLM abstraction layer (existing)
├── llm_adapters/          # Specific LLM provider implementations (existing)
├── llm_orchestrator/      # Multi-LLM orchestration (existing)
├── email_receiver/        # Gmail API integration (existing)
├── content_normalizer/    # Email cleaning pipeline (existing)
├── notion_integrator/     # Notion API client (existing)
├── error_handling/        # Unified retry system & circuit breakers (existing)
└── models/                # Pydantic data models (existing)

tests/
├── unit/                  # Unit tests for individual functions or classes
├── integration/           # Integration tests for interactions between modules
├── contract/              # Contract tests for library interfaces (existing)
├── e2e/                   # End-to-end tests for full pipeline logic
├── performance/           # NEW: Performance test suite with threshold assertions
├── fuzz/                  # NEW: Fuzz testing configurations and data
└── coverage_reports/      # NEW: Granular coverage reports (unit/integration/e2e)

scripts/
├── cleanup_test_entries.py # Enhanced: Uses test_utils library
├── run_e2e_with_real_components.py # Enhanced: Real Gmail/Notion integration
├── benchmark_llm_performance.py # NEW: Wrapper for llm_benchmarking CLI
└── fuzz_test_inputs.py    # NEW: Wrapper for test_utils fuzz CLI

data/
├── llm_health/            # Existing: LLM health and cost metrics
├── e2e_test/              # Existing: E2E test results
└── test_metrics/          # NEW: Performance and fuzz test results
```

**Structure Decision**: Per constitution Library-First principle, new modules (`date_parser`, `llm_benchmarking`, `test_utils`) are structured as standalone libraries. Each library:
- Is self-contained with clear boundaries
- Has dedicated CLI interface (`cli.py`) following text I/O protocol
- Includes comprehensive README with examples
- Supports both programmatic API and CLI usage
- Can be independently tested via contract tests

### Data Model references

- **Test Email Data**: Stored as file-based JSON in `data/extractions/{email_id}.json` after processing.
- **Test Notion Entries**: Created and managed within a dedicated Notion database, with caching in `data/notion_cache/`.
- **Date Formats**: Processed and normalized by the new `date_parser` module, with results integrated into extracted entities.
- **LLM Performance Metrics**: Stored as file-based JSON in `data/llm_health/` and `data/test_metrics/`.
- **Code Coverage Reports**: Generated into `tests/coverage_reports/`.
- **Performance Metrics**: Stored in `data/test_metrics/`.
- **Negative Test Cases**: Input data and expected outcomes for robustness testing, potentially stored in `tests/fuzz/` or inline within test files.

### Library Interfaces

Per constitution principle II, each new library provides both programmatic and CLI interfaces:

#### Date Parser Library
- **Python API**: `from src.collabiq.date_parser import parse_date, normalize_date`
- **CLI**: `python -m src.collabiq.date_parser.cli <text>` → JSON output
- **Storage**: None (stateless transformation library)

#### LLM Benchmarking Library
- **Python API**: `from src.collabiq.llm_benchmarking import run_benchmark, compare_prompts`
- **CLI**: `python -m src.collabiq.llm_benchmarking.cli --provider=<name> --dataset=<path>` → JSON metrics
- **Storage**: Results stored in `data/test_metrics/benchmarks/`

#### Test Utils Library
- **Python API**: `from src.collabiq.test_utils import cleanup_notion, monitor_performance, generate_fuzz_input`
- **CLI**: `python -m src.collabiq.test_utils.cli <command> <args>` → JSON output
- **Storage**: Cleanup logs in `data/test_metrics/cleanup/`, performance metrics in `data/test_metrics/performance/`

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations to justify at this time.