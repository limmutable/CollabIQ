# Implementation Plan: Production Readiness Fixes

**Branch**: `017-production-readiness-fixes` | **Date**: 2025-11-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-production-readiness-fixes/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Phase 017 addresses critical production blockers to enable fully autonomous operation of CollabIQ. The phase implements six key enhancements: (1) Person matching using Notion workspace users API with Korean name fuzzy matching to automatically populate the 담당자 field, (2) Multi-LLM orchestration to improve collaboration summary quality in the "협업내용" field, (3) Automatic Gmail token refresh for unattended operation beyond 30 days, (4) Improved LLM prompt engineering to reduce UUID validation errors below 5%, (5) Autonomous daemon mode with configurable monitoring intervals, and (6) Comprehensive E2E testing with Markdown report generation. These fixes build on existing infrastructure from Phases 012 (multi-LLM), 014 (fuzzy matching), and 015-016 (test suite baseline).

## Technical Context

**Language/Version**: Python 3.12+ (established in project)
**Primary Dependencies**:
- **Existing**: `notion-client` (Notion API), `google-api-python-client` (Gmail), `pydantic` (validation), `tenacity` (retry), `rapidfuzz` (fuzzy matching), `typer` + `rich` (CLI), `anthropic` + `openai` (LLM SDKs)
- **New**: `cryptography` (token encryption), NEEDS CLARIFICATION: daemon process management library (e.g., `python-daemon`, `systemd` integration, or custom signal handling)

**Storage**: File-based (JSON for user cache, daemon state, test reports, token storage with encryption)
**Testing**: pytest + pytest-cov (existing 989 test suite at 86.5% baseline)
**Target Platform**: Linux/macOS server for daemon mode, CLI for manual operation
**Project Type**: Single project (CLI application with library components)
**Performance Goals**:
- Person matching: <2 seconds per email
- Multi-LLM summary: <8 seconds per email
- Token refresh: <5 seconds
- 50 emails with all enhancements: <12 minutes
- Daemon graceful shutdown: <10 seconds

**Constraints**:
- API rate limits: Gmail, Notion, LLM providers (exponential backoff required)
- Token security: Encryption at rest for OAuth2 tokens
- State persistence: File-based for daemon restart resilience
- Daemon stability: 24+ hours continuous operation without crashes
- Test quality: Maintain ≥86.5% pass rate baseline

**Scale/Scope**:
- 6 user stories (P1-P6)
- 40 functional requirements
- 989+ existing tests + new validation tests
- Est. 5-7 days implementation
- Production deployment readiness

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Library-First ✅ PASS
**Requirement**: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required.

**Assessment**:
- ✅ Person matching logic will be in `src/collabiq/notion_integrator/person_matcher.py` (self-contained)
- ✅ Token management will be in `src/collabiq/email_receiver/token_manager.py` (independently testable)
- ✅ Daemon controller will be in `src/collabiq/daemon/controller.py` (clear purpose)
- ✅ Multi-LLM summary enhancement builds on existing `src/collabiq/adapters/llm_orchestrator.py` (already self-contained)
- ✅ Test report generator will be standalone utility in `src/collabiq/testing/report_generator.py`

**Status**: PASS - All components follow library-first pattern with clear boundaries

### II. CLI Interface ✅ PASS
**Requirement**: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats.

**Assessment**:
- ✅ Daemon mode: `collabiq run --daemon --interval 15m` (Typer CLI)
- ✅ Test execution: `collabiq test run --report markdown` (text output)
- ✅ Person matching: Integrated into existing `collabiq process` command
- ✅ Token refresh: Integrated into existing email fetch flow, status via `collabiq config show`
- ✅ All operations log to stdout/stderr with structured output

**Status**: PASS - All functionality exposed via CLI with proper I/O protocol

### III. Test-First (NON-NEGOTIABLE) ✅ PASS
**Requirement**: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced.

**Assessment**:
- ✅ User Story 6 explicitly requires comprehensive testing with Markdown reports
- ✅ All 6 user stories have acceptance scenarios that define test cases
- ✅ Baseline established: 989 tests at 86.5% pass rate (Phase 015)
- ✅ Success criteria SC-011: Must maintain ≥86.5% pass rate
- ✅ Each enhancement (person matching, token refresh, daemon) will have unit + integration + E2E tests

**Status**: PASS - Test-first approach mandated by spec and constitution

### IV. Integration Testing ✅ PASS
**Requirement**: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas.

**Assessment**:
- ✅ Notion workspace users API: New contract test required (FR-001)
- ✅ Gmail token refresh: OAuth2 flow integration test required (FR-014-019)
- ✅ Multi-LLM orchestration: Integration test for consensus/best-match strategies (FR-008-013)
- ✅ Daemon lifecycle: Integration test for SIGTERM/SIGINT handling (FR-029)
- ✅ E2E validation: User Story 6 explicitly requires E2E tests (FR-037)

**Status**: PASS - Integration tests explicitly planned for all new contracts

### V. Observability ✅ PASS
**Requirement**: Text I/O ensures debuggability; Structured logging required.

**Assessment**:
- ✅ Daemon logging: FR-030 requires timestamp, email count, success/failure status logging
- ✅ Person matching: FR-006 requires warning logs for low confidence matches
- ✅ Token refresh: FR-018 requires critical alerts for refresh failures
- ✅ UUID extraction: FR-024 requires error rate tracking and metrics logging
- ✅ Test reports: FR-036 requires detailed failure logs in Markdown format

**Status**: PASS - Comprehensive logging requirements throughout spec

### Overall Gate Status: ✅ **PASS** - Proceed to Phase 0 Research

**No violations requiring complexity justification.**

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
src/collabiq/
├── adapters/                  # LLM adapters (existing from Phase 012)
│   ├── llm_orchestrator.py   # Multi-LLM orchestration (enhance for summaries)
│   ├── gemini_adapter.py     # Existing
│   ├── claude_adapter.py     # Existing
│   └── openai_adapter.py     # Existing
├── email_receiver/           # Gmail integration (existing)
│   ├── gmail_client.py       # Existing
│   └── token_manager.py      # NEW: OAuth2 token refresh + encryption
├── notion_integrator/        # Notion API integration (existing)
│   ├── notion_client.py      # Existing
│   ├── person_matcher.py     # NEW: Korean name fuzzy matching + user cache
│   └── field_mapper.py       # Existing (Phase 014)
├── daemon/                   # NEW: Autonomous operation
│   ├── controller.py         # Daemon lifecycle management
│   ├── scheduler.py          # Interval-based email checking
│   └── state_manager.py      # Last processed email ID persistence
├── testing/                  # NEW: Test utilities
│   └── report_generator.py  # Markdown test report generation
├── commands/                 # CLI commands (existing from Phase 011)
│   ├── run.py               # Enhance with --daemon flag
│   └── test.py              # NEW: Test execution commands
└── models/                   # Data models (existing)
    ├── extraction.py         # Existing (enhance prompts for UUID)
    └── daemon_state.py       # NEW: Daemon state schema

tests/
├── unit/                     # 31 existing files + new tests
│   ├── test_person_matcher.py         # NEW
│   ├── test_token_manager.py          # NEW
│   ├── test_daemon_controller.py      # NEW
│   └── test_report_generator.py       # NEW
├── integration/              # 33 existing files + new tests
│   ├── test_notion_users_api.py       # NEW: Workspace users contract
│   ├── test_gmail_token_refresh.py    # NEW: OAuth2 flow
│   ├── test_llm_summary_quality.py    # NEW: Multi-LLM orchestration
│   └── test_daemon_lifecycle.py       # NEW: SIGTERM/SIGINT handling
├── e2e/                      # 3 existing files + new tests
│   ├── test_full_pipeline.py          # Existing (enhance validation)
│   ├── test_production_fixes.py       # NEW: Phase 017 validation
│   └── test_daemon_mode.py            # NEW: 24-hour stability test
├── contract/                 # 20 existing files
├── performance/              # 2 existing files
└── fuzz/                     # 2 existing files

data/                         # File-based storage (existing)
├── notion_cache/             # Existing
│   └── workspace_users.json  # NEW: Cached user list (24h TTL)
├── daemon/                   # NEW: Daemon state
│   ├── state.json            # Last processed email ID
│   └── daemon.pid            # Process ID for health checks
├── tokens/                   # NEW: Encrypted OAuth2 tokens
│   └── gmail_tokens.enc      # Encrypted access + refresh tokens
└── test_reports/             # NEW: Test execution reports
    └── phase_017_report.md   # Markdown test report
```

**Structure Decision**: Single project structure (Option 1) maintained. All enhancements integrate into existing `src/collabiq/` structure following library-first pattern. New directories: `daemon/` (autonomous operation), `testing/` (report generation). Enhanced directories: `email_receiver/` (token manager), `notion_integrator/` (person matcher), `commands/` (daemon CLI). File-based storage in `data/` for caching, state, and reports.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected.** All enhancements comply with constitution principles.

---

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design completion (research.md, data-model.md, contracts/)*

### I. Library-First ✅ PASS (Confirmed)
**Design Verification**:
- ✅ `person_matcher.py`: Self-contained module with clear fuzzy matching API
- ✅ `token_manager.py`: Independent token refresh + encryption library
- ✅ `daemon/controller.py`: Standalone daemon lifecycle manager
- ✅ `report_generator.py`: Standalone Markdown report generation
- ✅ All documented in data-model.md with clear boundaries

### II. CLI Interface ✅ PASS (Confirmed)
**Design Verification**:
- ✅ CLI contracts documented in `contracts/cli_commands.yaml`
- ✅ `collabiq run --daemon` exposes daemon controller
- ✅ `collabiq daemon status/stop` exposes daemon management
- ✅ `collabiq test run --report markdown` exposes test execution
- ✅ `collabiq config token-status` exposes token info
- ✅ All commands follow text I/O protocol (stdout/stderr)

### III. Test-First (NON-NEGOTIABLE) ✅ PASS (Confirmed)
**Design Verification**:
- ✅ Test scenarios documented in all API contracts
- ✅ Test execution command designed (collabiq test run)
- ✅ Test report model designed (TestExecutionReport)
- ✅ Integration tests planned for all new contracts
- ✅ E2E tests planned for Phase 017 validation

### IV. Integration Testing ✅ PASS (Confirmed)
**Design Verification**:
- ✅ `contracts/notion_users_api.yaml`: Contract test scenarios defined
- ✅ `contracts/gmail_token_refresh.yaml`: OAuth2 flow test scenarios defined
- ✅ LLM orchestration: Integration tests for consensus/best-match
- ✅ Daemon lifecycle: SIGTERM/SIGINT signal handling tests
- ✅ All test scenarios include Given-When-Then format

### V. Observability ✅ PASS (Confirmed)
**Design Verification**:
- ✅ Logging format specified in `contracts/cli_commands.yaml`
- ✅ Daemon cycle logs: timestamp, email count, success/failure status
- ✅ Person matching warnings: low confidence alerts
- ✅ Token refresh: success/failure logging
- ✅ Test reports: detailed failure logs in Markdown

### Overall Post-Design Gate Status: ✅ **PASS**

**Design Integrity**: All Phase 1 artifacts (research.md, data-model.md, contracts/) comply with constitution. Ready for Phase 2 task generation (`/speckit.tasks`).
