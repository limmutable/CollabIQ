# Implementation Plan: MVP End-to-End Testing & Error Resolution

**Branch**: `008-mvp-e2e-test` | **Date**: 2025-11-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-mvp-e2e-test/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature validates the complete MVP pipeline (email reception → entity extraction → company matching → classification → Notion write) with real data from collab@signite.co, identifies all errors categorized by severity, and fixes all critical and high-severity errors before proceeding to Phase 2e. The technical approach involves creating an end-to-end test harness that processes real emails, collects comprehensive error data with full context, and systematically addresses issues to achieve ≥95% pipeline success rate.

## Technical Context

**Language/Version**: Python 3.12 (established in project)
**Primary Dependencies**: pytest (testing framework), existing MVP components (email_receiver, llm_adapters, notion_integrator, content_normalizer), Gmail/Gemini/Notion APIs
**Storage**: File-based (JSON files for error reports, performance metrics, test results in data/e2e_test/ directory)
**Testing**: pytest for test harness, manual execution with real APIs (not automated in CI)
**Target Platform**: Local development environment (macOS, Linux)
**Project Type**: Single (monolithic Python application with CLI interface)
**Performance Goals**: Measure baselines (not optimize); collect timing data for each pipeline stage; identify bottlenecks taking >5 seconds
**Constraints**: Must use real emails from collab@signite.co; must not pollute production Notion database (resolved: use production database with manual cleanup script - deletes test entries by email_id after testing); must preserve Korean text encoding (UTF-8)
**Scale/Scope**: All available real emails from collab@signite.co (currently <10 emails); focus on MVP pipeline only (Phases 1a, 1b, 2a, 2b, 2c, 2d)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅ PASS
- [x] Feature specification (`spec.md`) exists and is complete
- [x] User scenarios with acceptance criteria defined (4 user stories with Given/When/Then scenarios)
- [x] Functional requirements documented (FR-001 through FR-015)
- [x] Success criteria defined (SC-001 through SC-010)
- [x] Requirements are technology-agnostic (no implementation details in spec)

### II. Incremental Delivery via Independent User Stories ✅ PASS
- [x] User stories are prioritized (P1: validation & identification, P2: fixing, P3: performance)
- [x] Each user story is independently testable
  - US1 (P1): Run pipeline with 10 emails → verify Notion entries created
  - US2 (P1): Run with 50+ emails → produce categorized error report
  - US3 (P2): Apply fixes → re-run tests → verify errors resolved
  - US4 (P3): Instrument pipeline → collect metrics → establish baselines
- [x] User Story 1 (P1) constitutes viable MVP (pipeline validation confirms readiness)
- [x] Implementation will proceed in priority order (P1 → P2 → P3)
- [x] Each story completion results in deployable increment (error-free MVP after P2)

### III. Test-Driven Development (TDD) - MANDATORY ⚠️ CONDITIONAL
- [ ] Tests required: **YES** - This feature IS about testing, but TDD applies only to the test harness itself
- [x] Test harness components (error collector, performance tracker, report generator) will follow TDD
- [x] The E2E tests themselves are validation scripts, not unit-testable
- [ ] Integration tests for test harness utilities: REQUIRED
- [x] Contract tests: N/A (no new APIs, only internal test utilities)

**Clarification**: TDD applies to building the test infrastructure (e.g., error report generator should have failing tests first). The E2E validation scripts are the "test" artifacts themselves and don't require meta-tests.

### IV. Design Artifact Completeness ✅ PASS (In Progress)
- [x] `plan.md` with constitution check, technical context ← (current step)
- [ ] `research.md` with test database setup strategy ← (Phase 0, next)
- [ ] `data-model.md` with error/metric entities ← (Phase 1)
- [ ] `quickstart.md` with E2E test execution steps ← (Phase 1)
- [ ] `contracts/` with test harness interfaces ← (Phase 1)
- [ ] `tasks.md` generation blocked until above complete ← (Phase 2, `/speckit.tasks`)

### V. Simplicity & Justification ✅ PASS
- [x] Defaulting to simplest approach: pytest-based test scripts, file-based error logging
- [x] No unnecessary abstractions: using existing MVP components directly
- [x] YAGNI principle: building only what spec requires (validation, error reporting, fixes)
- [x] No complexity violations anticipated

**GATE STATUS**: ✅ **PASS** - May proceed to Phase 0 (Research)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
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
├── email_receiver/          # Existing: Gmail API integration
├── llm_adapters/            # Existing: Gemini API adapter
├── content_normalizer/      # Existing: Email cleaning
├── notion_integrator/       # Existing: Notion read/write operations
└── e2e_test/                # NEW: End-to-end test harness (this feature)
    ├── __init__.py
    ├── runner.py            # Main E2E test orchestrator
    ├── error_collector.py   # Error tracking and categorization
    ├── performance_tracker.py  # Timing and resource metrics
    ├── report_generator.py  # Test summary and error reports
    └── validators.py        # Data integrity checks

tests/
├── e2e/                     # NEW: End-to-end validation scripts
│   ├── test_full_pipeline.py      # US1: Complete pipeline validation
│   ├── test_error_collection.py   # US2: Error identification
│   ├── test_duplicate_handling.py # Duplicate detection validation
│   └── test_korean_encoding.py    # Korean text preservation
├── manual/                  # Existing: Manual test scripts with real APIs
│   └── run_e2e_validation.py  # NEW: Manual E2E test runner
├── integration/             # Existing: Integration tests
│   └── test_e2e_harness.py   # NEW: Test harness utilities (TDD)
└── fixtures/
    └── e2e_test_data/       # NEW: Expected behaviors and ground truth

data/
└── e2e_test/                # NEW: Test run outputs
    ├── runs/                # Test run metadata and results
    ├── errors/              # Error reports by severity
    ├── metrics/             # Performance metrics by stage
    └── reports/             # Summary reports

scripts/
└── run_e2e_tests.py         # NEW: CLI command for E2E validation
```

**Structure Decision**: Single project (Option 1) - This feature adds testing infrastructure to the existing monolithic Python application. The `src/e2e_test/` module contains reusable test harness utilities, while `tests/e2e/` contains actual validation scripts. This follows the existing project structure where source code lives in `src/` and test code lives in `tests/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - All constitution principles are satisfied. This feature follows the simplest approach: pytest-based validation scripts, file-based error/metric storage, and direct use of existing MVP components.
