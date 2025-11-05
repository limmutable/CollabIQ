# Tasks: MVP End-to-End Testing & Error Resolution

**Input**: Design documents from `/specs/008-mvp-e2e-test/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Integration tests for test harness utilities are included (TDD approach for test infrastructure components).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for E2E test harness

- [X] T001 Create directory structure: `src/e2e_test/`, `tests/e2e/`, `tests/integration/`, `data/e2e_test/`, `scripts/`
- [X] T002 Create data subdirectories: `data/e2e_test/runs/`, `data/e2e_test/errors/{critical,high,medium,low}/`, `data/e2e_test/metrics/`, `data/e2e_test/reports/`
- [X] T003 [P] Add pytest to dependencies if not already present
- [X] T004 [P] Create `src/e2e_test/__init__.py` (empty package initializer)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and test infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create Pydantic models in `src/e2e_test/models.py` (TestRun, ErrorRecord, PerformanceMetric, TestEmailMetadata with all fields from data-model.md)
- [X] T006 [P] Write integration test for models in `tests/integration/test_e2e_models.py` (validate Pydantic schema constraints)
- [X] T007 Create email selection script `scripts/select_test_emails.py` (fetch all emails from collab@signite.co inbox, outputs to `data/e2e_test/test_email_ids.json`)
- [X] T008 Create manual cleanup script `scripts/cleanup_test_entries.py` (deletes Notion entries by email_id list, with confirmation prompt)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Complete Pipeline Validation (Priority: P1) 🎯 MVP

**Goal**: Validate that the entire MVP pipeline works end-to-end with real emails, producing correctly formatted Notion entries

**Independent Test**: Run pipeline with all available real emails from collab@signite.co (currently <10), verify all create valid Notion entries with correct Korean text and field values

### Tests for User Story 1 (TDD for test harness utilities)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Integration test for ErrorCollector in `tests/integration/test_error_collector.py` (test collect_error, persist_error, get_error_summary methods)
- [X] T010 [P] [US1] Integration test for Validator in `tests/integration/test_validators.py` (test Korean text validation, field format checks)

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement ErrorCollector in `src/e2e_test/error_collector.py` (collect_error with auto-severity categorization, persist_error, get_error_summary per contract)
- [X] T012 [P] [US1] Implement Validator in `src/e2e_test/validators.py` (validate_notion_entry method: check all required fields present, Korean text not corrupted, date format valid)
- [ ] T013 [US1] Implement E2ERunner core in `src/e2e_test/runner.py` (run_tests method: orchestrate pipeline, collect errors via ErrorCollector, validate outputs via Validator)
- [ ] T014 [US1] Implement basic ReportGenerator in `src/e2e_test/report_generator.py` (generate_summary method: create test run summary with success/failure counts, error breakdown by severity)
- [ ] T015 [US1] Create E2E validation script `tests/e2e/test_full_pipeline.py` (pytest test that calls runner.run_tests with 10 emails, asserts ≥95% success rate)
- [ ] T016 [US1] Create manual E2E test runner `tests/manual/run_e2e_validation.py` (CLI script that wraps E2ERunner, prints progress, saves report)
- [ ] T017 [US1] Create main CLI script `scripts/run_e2e_tests.py` (argparse: --limit N, --all, --email-id ID, calls manual runner)
- [ ] T018 [US1] Test with all available real emails (<10 currently), verify Notion entries created correctly (manual verification, check Korean text, all required fields)

**Checkpoint**: At this point, basic E2E pipeline validation works. Can process emails and detect errors.

---

## Phase 4: User Story 2 - Error Identification & Prioritization (Priority: P1)

**Goal**: Run pipeline with all available emails (<10 currently), capture all errors with full context, categorize by severity, and generate comprehensive error report

**Independent Test**: Process all available emails (<10 currently), produce error report with categorized errors (critical/high/medium/low), each error includes email_id, stack trace, input data snapshot

### Tests for User Story 2 (TDD for error categorization)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T019 [P] [US2] Integration test for auto-categorization in `tests/integration/test_error_severity.py` (test that APIErrors → critical, EncodingErrors → high, edge cases → medium/low)
- [ ] T020 [P] [US2] Integration test for error context capture in `tests/integration/test_error_context.py` (verify stack trace captured, input data sanitized)

### Implementation for User Story 2

- [ ] T021 [US2] Enhance ErrorCollector with auto-categorization rules in `src/e2e_test/error_collector.py` (implement severity logic from research.md: API auth → critical, Korean encoding → high, etc.)
- [ ] T022 [US2] Add update_error_status method to ErrorCollector in `src/e2e_test/error_collector.py` (update resolution_status, fix_commit, notes fields)
- [ ] T023 [US2] Enhance ReportGenerator in `src/e2e_test/report_generator.py` (add generate_error_report method: list all errors by severity, include reproduction context)
- [ ] T024 [US2] Create error collection validation script `tests/e2e/test_error_collection.py` (pytest test that processes diverse emails including known edge cases, verifies all errors captured)
- [ ] T025 [US2] Add --report flag to CLI script `scripts/run_e2e_tests.py` (generate detailed error report after test run)
- [ ] T026 [US2] Create error status update script `scripts/update_error_status.py` (CLI: --error-id, --status, --commit, updates error JSON file)
- [ ] T027 [US2] Run with all available emails (<10 currently), review error report, verify all errors have sufficient context for reproduction (manual review)

**Checkpoint**: Error identification and categorization complete. Have comprehensive catalog of all MVP issues.

---

## Phase 5: User Story 3 - Critical Error Resolution (Priority: P2)

**Goal**: Fix all critical and high-severity errors identified in US2, verify fixes work, achieve ≥95% pipeline success rate

**Independent Test**: Re-run same email test set (<10 currently) after fixes applied, verify critical/high errors no longer occur, success rate ≥95%

### Implementation for User Story 3

- [ ] T028 [US3] Analyze critical errors from US2 error report, prioritize fixes by impact (review `data/e2e_test/errors/critical/` and `errors/high/`)
- [ ] T029 [US3] Fix critical errors in affected MVP components (work through each critical error: identify root cause, apply fix, run regression tests)
- [ ] T030 [US3] Fix high-severity errors in affected MVP components (work through each high error: Korean encoding issues, date parsing, company matching bugs)
- [ ] T031 [US3] Update error statuses after fixes applied using `scripts/update_error_status.py` (mark errors as "fixed", include git commit hashes)
- [ ] T032 [US3] Create regression validation script `tests/e2e/test_regression.py` (re-run emails that previously failed with fixed errors, verify they now succeed)
- [ ] T033 [US3] Run full test suite with all available emails (<10 currently), verify ≥95% success rate (SC-001), verify critical/high errors resolved (manual verification)
- [ ] T034 [US3] Add success criteria validation script `scripts/validate_success_criteria.py` (check SC-001 through SC-009: success rate, data accuracy, error resolution, Korean text preservation)

**Checkpoint**: Critical and high-severity errors fixed. MVP pipeline is stable and reliable.

---

## Phase 6: User Story 4 - Performance & Resource Validation (Priority: P3)

**Goal**: Instrument pipeline with performance tracking, collect timing/resource metrics, establish baselines for each stage, identify bottlenecks

**Independent Test**: Process all available emails (<10 currently) with performance tracking enabled, produce metrics report showing average/p95/p99 times per stage, API call counts, token usage

### Tests for User Story 4 (TDD for performance tracking)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T035 [P] [US4] Integration test for PerformanceTracker in `tests/integration/test_performance_tracker.py` (test track_stage context manager, get_stage_statistics, export_metrics_csv)

### Implementation for User Story 4

- [ ] T036 [US4] Implement PerformanceTracker in `src/e2e_test/performance_tracker.py` (track_stage context manager using time.perf_counter(), record API calls and tokens per contract)
- [ ] T037 [US4] Add get_stage_statistics method to PerformanceTracker in `src/e2e_test/performance_tracker.py` (calculate mean, median, p95, p99, sum API calls/tokens)
- [ ] T038 [US4] Add export_metrics_csv method to PerformanceTracker in `src/e2e_test/performance_tracker.py` (flatten metrics to CSV format)
- [ ] T039 [US4] Integrate PerformanceTracker into E2ERunner in `src/e2e_test/runner.py` (wrap each pipeline stage with track_stage context manager)
- [ ] T040 [US4] Enhance ReportGenerator in `src/e2e_test/report_generator.py` (add performance section: average times per stage, API call summary, token usage, bottleneck identification)
- [ ] T041 [US4] Create performance metrics export script `scripts/export_metrics.py` (CLI: --run-id, --output, exports metrics to CSV)
- [ ] T042 [US4] Run with all available emails (<10 currently), collect performance metrics, generate report with baselines (verify SC-008: ≤10s average per email, identify stages >5s)

**Checkpoint**: Performance baselines established. Know where bottlenecks are for future optimization.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, additional validation, and final integration

- [ ] T043 [P] Create duplicate detection validation script `tests/e2e/test_duplicate_handling.py` (process same email multiple times, verify only one Notion entry exists or updated per config)
- [ ] T044 [P] Create Korean text encoding validation script `tests/e2e/test_korean_encoding.py` (process emails with Korean text, emojis, special chars, verify no mojibake in Notion)
- [ ] T045 [P] Add resume capability to E2ERunner in `src/e2e_test/runner.py` (resume_test_run method: load existing run, skip completed emails, continue from interruption)
- [ ] T046 [P] Add --resume flag to CLI script `scripts/run_e2e_tests.py` (allow resuming interrupted test runs)
- [ ] T047 Create quickstart validation checklist in `specs/008-mvp-e2e-test/quickstart.md` (verify all commands work, update any outdated instructions based on actual implementation)
- [ ] T048 Run final validation: all success criteria (SC-001 through SC-010), all existing tests pass, no regressions (final verification before feature completion)

**Checkpoint**: Feature complete! All acceptance criteria met, ready to merge.

---

## Dependencies (User Story Completion Order)

```
Phase 1 (Setup) ────────────────────────────┐
                                             ↓
Phase 2 (Foundational) ─────────────────────┼──────────────┐
                                             ↓              ↓
Phase 3 (US1: Pipeline Validation) ─────────┤              │
                                             ↓              │
Phase 4 (US2: Error Identification) ────────┤              │
                                             ↓              │
Phase 5 (US3: Error Resolution) ────────────┤              │
                                             │              ↓
Phase 6 (US4: Performance) ─────────────────┴──────────────┤
                                                            ↓
Phase 7 (Polish) ───────────────────────────────────────────┘
```

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3)
**US4 can start after Phase 2** (parallel to US1-US3 if resources available)
**Phase 7 requires all user stories complete**

---

## Parallel Execution Opportunities

### Within Phase 3 (US1)
- T009, T010 (tests) can run in parallel
- T011, T012 (ErrorCollector, Validator) can run in parallel after their tests pass

### Within Phase 4 (US2)
- T019, T020 (tests) can run in parallel
- T021, T023 (ErrorCollector enhancement, ReportGenerator) can run in parallel

### Within Phase 6 (US4)
- T036, T037, T038 (PerformanceTracker implementation) are sequential (single file)
- T041 (export script) can be parallel after T038

### Within Phase 7 (Polish)
- T043, T044, T045, T046 (validation scripts) can all run in parallel
- T047, T048 are final validation (sequential)

---

## Implementation Strategy

**MVP Scope** (Phases 1-3): US1 Pipeline Validation
- Validates that MVP pipeline works end-to-end with real emails
- Detects errors and creates basic reports
- **Delivers immediate value**: Confirms MVP readiness before Phase 2e

**Incremental Delivery**:
1. **After Phase 3**: Can validate pipeline works, know if major issues exist
2. **After Phase 4**: Have comprehensive error catalog, know what to fix
3. **After Phase 5**: Pipeline is stable (≥95% success), critical/high errors fixed
4. **After Phase 6**: Understand performance characteristics, have optimization roadmap

**Recommended Approach**: Implement US1 → US2 → US3 in sequence (each builds on previous), then do US4 (performance) in parallel with US3 fixes if resources available.

---

## Task Summary

**Total Tasks**: 48
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (US1)**: 10 tasks (2 tests + 8 implementation)
- **Phase 4 (US2)**: 9 tasks (2 tests + 7 implementation)
- **Phase 5 (US3)**: 7 tasks (all implementation/fixing)
- **Phase 6 (US4)**: 8 tasks (1 test + 7 implementation)
- **Phase 7 (Polish)**: 6 tasks

**Parallel Opportunities**: 15 tasks marked [P] (can run in parallel within their phase)

**Independent Test Criteria**:
- **US1**: Process 10 emails → verify Notion entries created correctly
- **US2**: Process 50+ emails → produce categorized error report
- **US3**: Re-run 50+ emails → verify ≥95% success rate, critical/high errors resolved
- **US4**: Process 50 emails with tracking → produce performance report with baselines

---

## Notes on Database Strategy

**Decision**: Use production Notion database with manual cleanup (research.md Option A)

**Cleanup Process**:
1. Before running E2E tests: Note starting state (number of entries in production CollabIQ database)
2. Run E2E tests: Creates new entries tagged with email_id from test set
3. After testing complete: Use `scripts/cleanup_test_entries.py` to delete entries by email_id list
4. Verify cleanup: Check production database, ensure test entries removed

**Safety Measures**:
- `cleanup_test_entries.py` requires explicit confirmation before deletion
- Script only deletes entries matching email_ids from `test_email_ids.json`
- Logs all deleted entry IDs for audit trail
- If cleanup fails mid-process, can be re-run safely (idempotent)

**Trade-offs Accepted** (per user decision):
- Risk: Failed tests may leave orphaned entries (mitigated by cleanup script)
- Risk: Manual cleanup is error-prone (mitigated by confirmation prompts and logging)
- Risk: Accidental deletion of real data (mitigated by email_id filtering - only deletes test entries)
- Benefit: No need to maintain separate test database or keep schemas in sync
- Benefit: Tests run against real production schema (catches schema drift issues)
