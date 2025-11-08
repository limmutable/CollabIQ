# Tasks: Admin CLI Enhancement

**Input**: Design documents from `/specs/011-admin-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This feature requires TDD (Test-Driven Development) as specified in the constitution. Tests MUST be written first and verified to fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to repository root:
- **Source**: `src/collabiq/` - CLI implementation
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/unit/`
- **Config**: `pyproject.toml` - Package configuration

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and CLI infrastructure setup

- [X] T001 Add typer and rich dependencies to pyproject.toml
- [X] T002 [P] Configure collabiq entry point in pyproject.toml [project.scripts] section
- [X] T003 [P] Create src/collabiq/ directory structure (commands/, formatters/, utils/)
- [X] T004 [P] Create tests/contract/test_cli_interface.py (empty, for contract tests)
- [X] T005 [P] Create tests/integration/ test files for CLI workflows (empty placeholders)
- [X] T006 [P] Create tests/unit/ test files for formatters and utils (empty placeholders)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CLI infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement main CLI app in src/collabiq/__init__.py with typer.Typer() setup
- [X] T008 [P] Implement base formatters in src/collabiq/formatters/tables.py (Rich table helper)
- [X] T009 [P] Implement progress indicators in src/collabiq/formatters/progress.py (spinners, bars)
- [X] T010 [P] Implement color output handler in src/collabiq/formatters/colors.py (NO_COLOR support)
- [X] T011 [P] Implement JSON output formatter in src/collabiq/formatters/json_output.py
- [X] T012 [P] Implement interrupt handler in src/collabiq/utils/interrupt.py (SIGINT/SIGTERM)
- [X] T013 [P] Implement input validation helpers in src/collabiq/utils/validation.py
- [X] T014 [P] Implement CLI audit logger in src/collabiq/utils/logging.py
- [X] T015 Create command group stub files in src/collabiq/commands/ (__init__.py, email.py, notion.py, test.py, errors.py, status.py, llm.py, config.py)
- [X] T016 Register all command groups in src/collabiq/__init__.py main app
- [X] T017 Add global callback for --debug, --quiet, --no-color flags in src/collabiq/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single Entry Point for All Operations (Priority: P1) 🎯 MVP

**Goal**: Deliver a unified `collabiq` command with organized help text and all command groups accessible

**Independent Test**: Run `collabiq --help` and verify all command groups (email, notion, test, errors, status, llm, config) are listed with clear descriptions. Test basic commands like `collabiq status` work without errors.

### Contract Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US1] Contract test for main app help text in tests/contract/test_cli_interface.py
- [ ] T019 [P] [US1] Contract test for command group registration in tests/contract/test_cli_interface.py
- [ ] T020 [P] [US1] Contract test for global options (--help, --debug, --quiet, --no-color) in tests/contract/test_cli_interface.py

### Implementation for User Story 1

- [ ] T021 [US1] Complete main CLI app implementation with all command group registrations
- [ ] T022 [US1] Add comprehensive help text to main app and all command groups
- [ ] T023 [US1] Implement global options handler (--debug logging setup, --quiet output suppression, --no-color)
- [ ] T024 [US1] Verify CLI installation works with `uv pip install -e .` and `collabiq --help`

**Checkpoint**: At this point, User Story 1 should be fully functional - `collabiq --help` shows all groups with proper help text

---

## Phase 4: User Story 2 - Email Pipeline Management (Priority: P1)

**Goal**: Enable admins to manage email operations (fetch, clean, list, verify, process) through `collabiq email` commands

**Independent Test**: Run `collabiq email fetch --limit 5` to download 5 emails, then `collabiq email list` to view them, and verify both commands complete successfully with proper output formatting.

### Contract Tests for User Story 2

- [ ] T025 [P] [US2] Contract test for `collabiq email fetch` signature and options in tests/contract/test_cli_interface.py
- [ ] T026 [P] [US2] Contract test for `collabiq email clean` in tests/contract/test_cli_interface.py
- [ ] T027 [P] [US2] Contract test for `collabiq email list` with filtering options in tests/contract/test_cli_interface.py
- [ ] T028 [P] [US2] Contract test for `collabiq email verify` in tests/contract/test_cli_interface.py
- [ ] T029 [P] [US2] Contract test for `collabiq email process` in tests/contract/test_cli_interface.py

### Integration Tests for User Story 2

- [ ] T030 [P] [US2] Integration test for fetch → clean → list workflow in tests/integration/test_cli_email_workflow.py
- [ ] T031 [P] [US2] Integration test for full email process pipeline in tests/integration/test_cli_email_workflow.py

### Implementation for User Story 2

- [ ] T032 [P] [US2] Implement `collabiq email fetch` command in src/collabiq/commands/email.py
- [ ] T033 [P] [US2] Implement `collabiq email clean` command in src/collabiq/commands/email.py
- [ ] T034 [P] [US2] Implement `collabiq email list` command in src/collabiq/commands/email.py
- [ ] T035 [P] [US2] Implement `collabiq email verify` command in src/collabiq/commands/email.py
- [ ] T036 [US2] Implement `collabiq email process` command (orchestrates fetch, clean, extract, write) in src/collabiq/commands/email.py
- [ ] T037 [US2] Add progress indicators for long-running email operations (fetch, clean, process)
- [ ] T038 [US2] Add error handling and remediation suggestions for email commands
- [ ] T039 [US2] Add JSON output support (--json) for all email commands
- [ ] T040 [US2] Add color-coded output (green success, yellow warnings, red errors) for email commands

**Checkpoint**: All email commands functional - can fetch, clean, list, verify, and process emails with proper formatting

---

## Phase 5: User Story 3 - Notion Integration Management (Priority: P2)

**Goal**: Enable admins to manage Notion integration (verify, schema, test-write, cleanup) through `collabiq notion` commands

**Independent Test**: Run `collabiq notion verify` and verify it checks connection, authentication, database access, and schema. Then run `collabiq notion test-write` to create and automatically cleanup a test entry.

### Contract Tests for User Story 3

- [ ] T041 [P] [US3] Contract test for `collabiq notion verify` in tests/contract/test_cli_interface.py
- [ ] T042 [P] [US3] Contract test for `collabiq notion schema` in tests/contract/test_cli_interface.py
- [ ] T043 [P] [US3] Contract test for `collabiq notion test-write` in tests/contract/test_cli_interface.py
- [ ] T044 [P] [US3] Contract test for `collabiq notion cleanup-tests` in tests/contract/test_cli_interface.py

### Integration Tests for User Story 3

- [ ] T045 [P] [US3] Integration test for verify → test-write → cleanup workflow in tests/integration/test_cli_notion_workflow.py

### Implementation for User Story 3

- [ ] T046 [P] [US3] Implement `collabiq notion verify` command in src/collabiq/commands/notion.py
- [ ] T047 [P] [US3] Implement `collabiq notion schema` command in src/collabiq/commands/notion.py
- [ ] T048 [P] [US3] Implement `collabiq notion test-write` command in src/collabiq/commands/notion.py
- [ ] T049 [US3] Implement `collabiq notion cleanup-tests` command with confirmation prompt in src/collabiq/commands/notion.py
- [ ] T050 [US3] Add table formatting for schema display
- [ ] T051 [US3] Add JSON output support for all notion commands
- [ ] T052 [US3] Add error handling and remediation for Notion API errors

**Checkpoint**: All Notion commands functional - can verify, inspect schema, test writes, and cleanup

---

## Phase 6: User Story 4 - LLM Provider Management (Priority: P2)

**Goal**: Enable admins to view LLM provider status, test connectivity, manage orchestration policies, and monitor usage through `collabiq llm` commands

**Independent Test**: Run `collabiq llm status` and verify it shows all configured LLM providers (or Gemini only if Phase 3b not implemented) with health status, response times, and error rates. Then test a provider with `collabiq llm test gemini`.

### Contract Tests for User Story 4

- [ ] T053 [P] [US4] Contract test for `collabiq llm status` in tests/contract/test_cli_interface.py
- [ ] T054 [P] [US4] Contract test for `collabiq llm test <provider>` in tests/contract/test_cli_interface.py
- [ ] T055 [P] [US4] Contract test for `collabiq llm policy` in tests/contract/test_cli_interface.py
- [ ] T056 [P] [US4] Contract test for `collabiq llm set-policy <strategy>` in tests/contract/test_cli_interface.py
- [ ] T057 [P] [US4] Contract test for `collabiq llm usage` in tests/contract/test_cli_interface.py
- [ ] T058 [P] [US4] Contract test for `collabiq llm disable/enable <provider>` in tests/contract/test_cli_interface.py

### Implementation for User Story 4

- [ ] T059 [US4] Implement Phase 3b availability check helper in src/collabiq/commands/llm.py
- [ ] T060 [P] [US4] Implement `collabiq llm status` with graceful degradation (Phase 3a: Gemini only, Phase 3b: multi-LLM) in src/collabiq/commands/llm.py
- [ ] T061 [P] [US4] Implement `collabiq llm test <provider>` in src/collabiq/commands/llm.py
- [ ] T062 [P] [US4] Implement `collabiq llm policy` in src/collabiq/commands/llm.py
- [ ] T063 [P] [US4] Implement `collabiq llm set-policy <strategy>` in src/collabiq/commands/llm.py
- [ ] T064 [P] [US4] Implement `collabiq llm usage` in src/collabiq/commands/llm.py
- [ ] T065 [P] [US4] Implement `collabiq llm disable <provider>` in src/collabiq/commands/llm.py
- [ ] T066 [P] [US4] Implement `collabiq llm enable <provider>` in src/collabiq/commands/llm.py
- [ ] T067 [US4] Add table formatting for multi-provider status display
- [ ] T068 [US4] Add JSON output support for all LLM commands
- [ ] T069 [US4] Add informative messages for Phase 3a (before Phase 3b implemented)

**Checkpoint**: All LLM commands functional - works with current Gemini setup, ready for Phase 3b multi-LLM

---

## Phase 7: User Story 5 - End-to-End Testing (Priority: P2)

**Goal**: Enable admins to run E2E tests on the complete pipeline through `collabiq test` commands

**Independent Test**: Run `collabiq test e2e --limit 3` on three test emails and verify a detailed report is generated showing pass/fail for each pipeline stage (reception, extraction, matching, classification, validation, write).

### Contract Tests for User Story 5

- [ ] T070 [P] [US5] Contract test for `collabiq test e2e` with all options in tests/contract/test_cli_interface.py
- [ ] T071 [P] [US5] Contract test for `collabiq test select-emails` in tests/contract/test_cli_interface.py
- [ ] T072 [P] [US5] Contract test for `collabiq test validate` in tests/contract/test_cli_interface.py

### Integration Tests for User Story 5

- [ ] T073 [P] [US5] Integration test for E2E test execution and reporting in tests/integration/test_cli_e2e_workflow.py
- [ ] T074 [P] [US5] Integration test for interrupt and resume workflow in tests/integration/test_cli_e2e_workflow.py

### Implementation for User Story 5

- [ ] T075 [P] [US5] Implement `collabiq test e2e` command with --all, --limit, --email-id options in src/collabiq/commands/test.py
- [ ] T076 [P] [US5] Implement `collabiq test e2e --resume <run-id>` for resumption after interrupt in src/collabiq/commands/test.py
- [ ] T077 [P] [US5] Implement `collabiq test select-emails` in src/collabiq/commands/test.py
- [ ] T078 [P] [US5] Implement `collabiq test validate` (quick health checks) in src/collabiq/commands/test.py
- [ ] T079 [US5] Add detailed progress tracking for E2E tests (current email, stage, ETA)
- [ ] T080 [US5] Add interrupt handler integration for E2E tests (save state on Ctrl+C)
- [ ] T081 [US5] Add stage-by-stage result table formatting
- [ ] T082 [US5] Add JSON output for E2E test reports
- [ ] T083 [US5] Add test report saving to data/e2e_test/reports/

**Checkpoint**: All test commands functional - can run E2E tests, validate system, select test emails

---

## Phase 8: User Story 6 - Error Management and DLQ Operations (Priority: P3)

**Goal**: Enable admins to view, inspect, retry, and clear failed operations through `collabiq errors` commands

**Independent Test**: Simulate a failure (disconnect network during email processing), verify it appears in `collabiq errors list`, inspect details with `collabiq errors show <id>`, then retry with `collabiq errors retry <id>` and confirm success.

### Contract Tests for User Story 6

- [ ] T084 [P] [US6] Contract test for `collabiq errors list` with filtering options in tests/contract/test_cli_interface.py
- [ ] T085 [P] [US6] Contract test for `collabiq errors show <error-id>` in tests/contract/test_cli_interface.py
- [ ] T086 [P] [US6] Contract test for `collabiq errors retry` in tests/contract/test_cli_interface.py
- [ ] T087 [P] [US6] Contract test for `collabiq errors clear` in tests/contract/test_cli_interface.py

### Implementation for User Story 6

- [ ] T088 [P] [US6] Implement `collabiq errors list` with filtering (--severity, --since, --limit) in src/collabiq/commands/errors.py
- [ ] T089 [P] [US6] Implement `collabiq errors show <error-id>` with full details in src/collabiq/commands/errors.py
- [ ] T090 [P] [US6] Implement `collabiq errors retry` (--all, --id, --since) in src/collabiq/commands/errors.py
- [ ] T091 [P] [US6] Implement `collabiq errors clear` (--resolved, --before) in src/collabiq/commands/errors.py
- [ ] T092 [US6] Add table formatting for error list display
- [ ] T093 [US6] Add detailed error display with remediation suggestions
- [ ] T094 [US6] Add progress indicator for bulk retry operations
- [ ] T095 [US6] Add JSON output support for all error commands

**Checkpoint**: All error management commands functional - can list, inspect, retry, and clear errors

---

## Phase 9: User Story 7 - System Health Monitoring (Priority: P3)

**Goal**: Enable admins to check overall system health, component status, and metrics through `collabiq status` commands

**Independent Test**: Run `collabiq status` and verify it shows overall health (healthy/degraded/critical) and status for all components (Gmail, Notion, Gemini) in under 5 seconds.

### Contract Tests for User Story 7

- [ ] T096 [P] [US7] Contract test for `collabiq status` basic output in tests/contract/test_cli_interface.py
- [ ] T097 [P] [US7] Contract test for `collabiq status --detailed` in tests/contract/test_cli_interface.py
- [ ] T098 [P] [US7] Contract test for `collabiq status --watch` in tests/contract/test_cli_interface.py

### Implementation for User Story 7

- [ ] T099 [US7] Implement parallel health checks (async Gmail, Notion, Gemini checks) in src/collabiq/commands/status.py
- [ ] T100 [US7] Implement `collabiq status` basic output with component status table in src/collabiq/commands/status.py
- [ ] T101 [US7] Implement `collabiq status --detailed` with extended metrics in src/collabiq/commands/status.py
- [ ] T102 [US7] Implement `collabiq status --watch` with 30-second refresh in src/collabiq/commands/status.py
- [ ] T103 [US7] Add overall health indicator (healthy/degraded/critical) calculation
- [ ] T104 [US7] Add component status highlighting (red for offline, yellow for degraded)
- [ ] T105 [US7] Add remediation suggestions for degraded components
- [ ] T106 [US7] Add JSON output support for status commands
- [ ] T107 [US7] Optimize status command to complete in <5 seconds (parallel checks, caching)

**Checkpoint**: Status commands functional - shows system health with real-time monitoring capability

---

## Phase 10: User Story 8 - Configuration Management (Priority: P3)

**Goal**: Enable admins to view, validate, and test configuration through `collabiq config` commands

**Independent Test**: Run `collabiq config show` and verify all configuration values are displayed with secrets masked (e.g., `GEMINI_API_KEY=AIza...***`) and source indicators (Infisical/env/default).

### Contract Tests for User Story 8

- [ ] T108 [P] [US8] Contract test for `collabiq config show` in tests/contract/test_cli_interface.py
- [ ] T109 [P] [US8] Contract test for `collabiq config validate` in tests/contract/test_cli_interface.py
- [ ] T110 [P] [US8] Contract test for `collabiq config test-secrets` in tests/contract/test_cli_interface.py
- [ ] T111 [P] [US8] Contract test for `collabiq config get <key>` in tests/contract/test_cli_interface.py

### Implementation for User Story 8

- [ ] T112 [P] [US8] Implement secret masking helper (show first 4 and last 3 chars) in src/collabiq/commands/config.py
- [ ] T113 [P] [US8] Implement `collabiq config show` with categorization (Gmail, Notion, Gemini, LLM, System) in src/collabiq/commands/config.py
- [ ] T114 [P] [US8] Implement `collabiq config validate` (check required settings) in src/collabiq/commands/config.py
- [ ] T115 [P] [US8] Implement `collabiq config test-secrets` (verify Infisical connection) in src/collabiq/commands/config.py
- [ ] T116 [P] [US8] Implement `collabiq config get <key>` in src/collabiq/commands/config.py
- [ ] T117 [US8] Add table formatting for config display with source indicators
- [ ] T118 [US8] Add validation error reporting with fix suggestions
- [ ] T119 [US8] Add JSON output support for all config commands
- [ ] T120 [US8] Ensure secret masking works in both interactive and JSON modes

**Checkpoint**: All config commands functional - can view, validate, and test configuration safely

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T121 [P] Add comprehensive docstrings to all CLI command functions
- [ ] T122 [P] Add usage examples to all command help text
- [ ] T123 [P] Verify all commands support --json flag and produce valid JSON
- [ ] T124 [P] Verify all commands respect --debug, --quiet, --no-color global flags
- [ ] T125 [P] Add unit tests for formatters in tests/unit/test_cli_formatters.py
- [ ] T126 [P] Add unit tests for utils in tests/unit/test_cli_utils.py
- [ ] T127 Run full E2E validation following quickstart.md guide
- [ ] T128 Performance testing: Verify status command completes <5s, E2E test on 10 emails <3min
- [ ] T129 Verify backward compatibility: existing `uv run python src/cli.py` scripts still work
- [ ] T130 Security audit: Verify secrets are masked in all output modes, audit log has proper permissions
- [ ] T131 Update CLAUDE.md if new patterns or conventions discovered during implementation
- [ ] T132 Final checkpoint: Verify all 8 user stories work independently and together

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - User Story 1 (P1): Single Entry Point - Must complete first (MVP foundation)
  - User Story 2 (P1): Email Pipeline - Can start after US1, no dependencies on other stories
  - User Story 3 (P2): Notion Integration - Can start after US1, integrates with US2 for full pipeline
  - User Story 4 (P2): LLM Provider Management - Can start after US1, independent of other stories
  - User Story 5 (P2): E2E Testing - Depends on US2 and US3 for full pipeline testing
  - User Story 6 (P3): Error Management - Can start after US1, independent of other stories
  - User Story 7 (P3): System Health - Can start after US1, integrates with all components
  - User Story 8 (P3): Configuration - Can start after US1, independent of other stories
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - **No dependencies on other stories** ✅ MVP
- **User Story 2 (P1)**: Can start after US1 - **No dependencies on other stories** ✅
- **User Story 3 (P2)**: Can start after US1 - Integrates with US2 for test-write verification but independently testable ✅
- **User Story 4 (P2)**: Can start after US1 - **No dependencies on other stories** ✅
- **User Story 5 (P2)**: Depends on US2 and US3 for meaningful E2E testing ⚠️
- **User Story 6 (P3)**: Can start after US1 - **No dependencies on other stories** ✅
- **User Story 7 (P3)**: Can start after US1 - Works better with US2, US3, US4 but independently testable ✅
- **User Story 8 (P3)**: Can start after US1 - **No dependencies on other stories** ✅

### Within Each User Story

- Contract tests MUST be written and FAIL before implementation
- Integration tests MUST be written and FAIL before implementation
- Tests (T018-T020, T025-T031, etc.) before implementation tasks
- Multiple commands within a story marked [P] can run in parallel
- Core implementation before error handling and formatting
- JSON output support and error handling added last within each story

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T002, T003, T004, T005, T006 can all run in parallel

**Foundational Phase (Phase 2)**:
- T008, T009, T010, T011, T012, T013, T014 can all run in parallel (different files)

**User Story 2 (Email)**:
- Contract tests: T025, T026, T027, T028, T029 in parallel
- Integration tests: T030, T031 in parallel
- Commands: T032, T033, T034, T035 in parallel (different commands)

**User Story 3 (Notion)**:
- Contract tests: T041, T042, T043, T044 in parallel
- Commands: T046, T047, T048 in parallel

**User Story 4 (LLM)**:
- Contract tests: T053, T054, T055, T056, T057, T058 in parallel
- Commands: T060, T061, T062, T063, T064, T065, T066 in parallel

**User Story 5 (Test)**:
- Contract tests: T070, T071, T072 in parallel
- Integration tests: T073, T074 in parallel
- Commands: T075, T076, T077, T078 in parallel

**User Story 6 (Errors)**:
- Contract tests: T084, T085, T086, T087 in parallel
- Commands: T088, T089, T090, T091 in parallel

**User Story 7 (Status)**:
- Contract tests: T096, T097, T098 in parallel

**User Story 8 (Config)**:
- Contract tests: T108, T109, T110, T111 in parallel
- Commands: T112, T113, T114, T115, T116 in parallel

**Polish Phase (Phase 11)**:
- T121, T122, T123, T124, T125, T126 can all run in parallel

**After Foundational Phase**: US2, US3, US4, US6, US7, US8 can all start in parallel (if team capacity allows)

---

## Parallel Example: User Story 2 (Email Pipeline)

```bash
# Launch all contract tests for User Story 2 together:
Task: "Contract test for `collabiq email fetch` signature and options in tests/contract/test_cli_interface.py"
Task: "Contract test for `collabiq email clean` in tests/contract/test_cli_interface.py"
Task: "Contract test for `collabiq email list` with filtering options in tests/contract/test_cli_interface.py"
Task: "Contract test for `collabiq email verify` in tests/contract/test_cli_interface.py"
Task: "Contract test for `collabiq email process` in tests/contract/test_cli_interface.py"

# Launch all integration tests together:
Task: "Integration test for fetch → clean → list workflow in tests/integration/test_cli_email_workflow.py"
Task: "Integration test for full email process pipeline in tests/integration/test_cli_email_workflow.py"

# Launch all commands together (different command functions in same file):
Task: "Implement `collabiq email fetch` command in src/collabiq/commands/email.py"
Task: "Implement `collabiq email clean` command in src/collabiq/commands/email.py"
Task: "Implement `collabiq email list` command in src/collabiq/commands/email.py"
Task: "Implement `collabiq email verify` command in src/collabiq/commands/email.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T017) - CRITICAL
3. Complete Phase 3: User Story 1 - Single Entry Point (T018-T024)
4. Complete Phase 4: User Story 2 - Email Pipeline (T025-T040)
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. **MVP DELIVERED**: Unified CLI with email management (core admin functionality)

### Incremental Delivery (Recommended)

1. **Foundation** (Phases 1-2): Setup + Foundational → CLI infrastructure ready
2. **MVP** (Phase 3-4): US1 + US2 → Test independently → Deploy/Demo (unified CLI + email pipeline)
3. **Increment 1** (Phase 5): Add US3 (Notion) → Test independently → Deploy/Demo
4. **Increment 2** (Phase 6): Add US4 (LLM Management) → Test independently → Deploy/Demo
5. **Increment 3** (Phase 7): Add US5 (E2E Testing) → Test independently → Deploy/Demo
6. **Increment 4** (Phases 8-10): Add US6, US7, US8 → Test independently → Deploy/Demo
7. **Polish** (Phase 11): Final validation and refinement

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (critical path)
2. **Team completes User Story 1 together** (MVP foundation)
3. **Once US1 is done, parallelize**:
   - Developer A: User Story 2 (Email Pipeline)
   - Developer B: User Story 3 (Notion Integration)
   - Developer C: User Story 4 (LLM Management)
   - Developer D: User Story 6 (Error Management)
   - Developer E: User Story 7 (System Health)
   - Developer F: User Story 8 (Configuration)
4. **User Story 5 (E2E Testing)** starts after US2 and US3 complete
5. Stories complete and integrate independently

---

## Notes

- **[P] tasks**: Different files or non-conflicting code sections, can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- **TDD Required**: All contract and integration tests MUST be written first and verified to fail
- **Each user story must be independently completable and testable**
- **Verify tests fail before implementing** (red → green → refactor cycle)
- **Commit after each task or logical group**
- **Stop at any checkpoint to validate story independently**
- **Graceful degradation for LLM commands**: Works with Phase 3a (Gemini only), ready for Phase 3b (multi-LLM)
- **Performance targets**: Status <5s, E2E test on 10 emails <3min, non-processing commands <2s
- **Security**: Secrets must be masked in all output modes, audit log protected with 640 permissions

---

## Task Count Summary

- **Total Tasks**: 132
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 11 tasks
- **Phase 3 (US1 - Single Entry Point)**: 7 tasks
- **Phase 4 (US2 - Email Pipeline)**: 16 tasks
- **Phase 5 (US3 - Notion Integration)**: 12 tasks
- **Phase 6 (US4 - LLM Provider Management)**: 17 tasks
- **Phase 7 (US5 - E2E Testing)**: 14 tasks
- **Phase 8 (US6 - Error Management)**: 12 tasks
- **Phase 9 (US7 - System Health)**: 12 tasks
- **Phase 10 (US8 - Configuration Management)**: 13 tasks
- **Phase 11 (Polish)**: 12 tasks

**MVP Scope** (Phases 1-4): 40 tasks → Unified CLI with email management
**Parallel Opportunities**: 60+ tasks can run in parallel within their phases
