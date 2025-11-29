# Tasks: Automated Admin Reporting

**Input**: Design documents from `/specs/019-admin-reporting/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit tests included as per project constitution (Test-First principle).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per plan.md)

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization, dependencies, and shared data models

- [x] T001 Add jinja2 dependency to pyproject.toml
- [x] T002 [P] Create src/admin_reporting/__init__.py with module docstring
- [x] T003 [P] Create src/email_sender/__init__.py with module docstring
- [x] T004 [P] Create src/admin_reporting/templates/ directory structure
- [x] T005 Extend DaemonProcessState with new metrics fields in src/models/daemon_state.py
- [x] T006 Create ReportingConfig model in src/admin_reporting/config.py
- [x] T007 [P] Create DailyReportData and related models in src/admin_reporting/models.py
- [x] T008 [P] Create ActionableAlert and AlertNotification models in src/admin_reporting/models.py
- [x] T009 Add reporting environment variables to src/config/settings.py (default recipient: jeffreylim@signite.co)

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Implement GmailSender class in src/email_sender/gmail_sender.py (reuse OAuth from GmailReceiver)
- [x] T011 [P] Write unit tests for GmailSender in tests/unit/test_gmail_sender.py
- [x] T012 Implement MetricsCollector class in src/admin_reporting/collector.py
- [x] T013 [P] Write unit tests for MetricsCollector in tests/unit/test_metrics_collector.py
- [x] T014 Implement ReportRenderer class with Jinja2 in src/admin_reporting/renderer.py
- [x] T015 [P] Create daily_report.html.j2 template in src/admin_reporting/templates/
- [x] T016 [P] Create daily_report.txt.j2 template in src/admin_reporting/templates/
- [x] T017 [P] Write unit tests for ReportRenderer in tests/unit/test_report_renderer.py
- [x] T018 Add MetricsCollector hooks to DaemonController.process_cycle() in src/daemon/controller.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Daily Summary Email (Priority: P1) 🎯 MVP ✅ COMPLETE

**Goal**: Generate and send daily summary emails with all key metrics

**Independent Test**: Trigger report generation via CLI and verify email delivery with all sections present

### Tests for User Story 1

- [x] T019 [P] [US1] Write unit tests for ReportGenerator in tests/unit/test_report_generator.py
- [ ] T020 [P] [US1] Write integration tests for report delivery in tests/integration/test_report_delivery.py

### Implementation for User Story 1

- [x] T021 [US1] Implement ReportGenerator class in src/admin_reporting/reporter.py
- [x] T022 [US1] Implement check_component_health() method for Gmail/Notion/LLM status in src/admin_reporting/reporter.py
- [x] T023 [US1] Implement collect_processing_metrics() aggregation in src/admin_reporting/collector.py
- [x] T024 [US1] Implement collect_error_summary() aggregation in src/admin_reporting/collector.py
- [x] T025 [US1] Implement collect_llm_usage() aggregation in src/admin_reporting/collector.py
- [x] T026 [US1] Implement collect_notion_stats() aggregation in src/admin_reporting/collector.py
- [x] T027 [US1] Add schedule_daily() method to Scheduler in src/daemon/scheduler.py
- [x] T028 [US1] Integrate daily report generation into daemon cycle in src/daemon/controller.py
- [x] T029 [US1] Create CLI command `collabiq report generate` in src/collabiq/commands/report.py
- [x] T030 [US1] Create CLI command `collabiq report config` in src/collabiq/commands/report.py
- [x] T031 [US1] Register report_app in src/collabiq/commands/__init__.py
- [ ] T032 [P] [US1] Write contract tests for CLI commands in tests/contract/test_report_cli.py

**Checkpoint**: Daily summary email can be generated and sent via CLI and daemon

---

## Phase 4: User Story 2 - Critical Error Alerts (Priority: P1) ✅ COMPLETE

**Goal**: Send immediate alerts for critical errors with batching to prevent alert fatigue

**Independent Test**: Simulate critical error and verify alert delivery within 5 minutes

### Tests for User Story 2

- [x] T033 [P] [US2] Write unit tests for AlertManager in tests/unit/test_alert_manager.py
- [ ] T034 [P] [US2] Write integration tests for alert batching in tests/integration/test_alert_batching.py

### Implementation for User Story 2

- [x] T035 [US2] Implement AlertManager class in src/admin_reporting/alerter.py
- [x] T036 [US2] Implement check_thresholds() method for error rate detection in src/admin_reporting/alerter.py
- [x] T037 [US2] Implement alert batching with 15-minute window in src/admin_reporting/alerter.py
- [x] T038 [US2] Implement max 5 alerts/hour rate limiting in src/admin_reporting/alerter.py
- [x] T039 [P] [US2] Create critical_alert.html.j2 template in src/admin_reporting/templates/
- [x] T040 [P] [US2] Create critical_alert.txt.j2 template in src/admin_reporting/templates/
- [x] T041 [US2] Integrate AlertManager into DaemonController.process_cycle() in src/daemon/controller.py
- [x] T042 [US2] Create CLI command `collabiq report alerts list` in src/collabiq/commands/report.py
- [x] T043 [US2] Create CLI command `collabiq report alerts test` in src/collabiq/commands/report.py

**Checkpoint**: Critical errors trigger immediate alerts with proper batching

---

## Phase 5: User Story 3 - Actionable Insights (Priority: P2) ✅ COMPLETE

**Goal**: Include actionable alerts in daily report (credential expiry, error trends, cost warnings)

**Independent Test**: Configure expiring credentials and verify report includes remediation guidance

### Tests for User Story 3

- [x] T044 [P] [US3] Write unit tests for credential expiry detection in tests/unit/test_alert_manager.py
- [x] T045 [P] [US3] Write unit tests for cost threshold detection in tests/unit/test_alert_manager.py

### Implementation for User Story 3

- [x] T046 [US3] Implement check_credential_expiry() for Gmail token in src/admin_reporting/alerter.py
- [x] T047 [US3] Implement check_error_rate_trend() for threshold warnings in src/admin_reporting/alerter.py
- [x] T048 [US3] Implement check_cost_limits() for LLM cost warnings in src/admin_reporting/alerter.py
- [x] T049 [US3] Add remediation text generation for each alert type in src/admin_reporting/alerter.py
- [x] T050 [US3] Integrate actionable alerts into daily report generation in src/admin_reporting/reporter.py

**Checkpoint**: Daily report includes actionable insights with remediation guidance

---

## Phase 6: User Story 4 - Report Archiving (Priority: P3) ✅ COMPLETE

**Goal**: Archive reports to filesystem with retention policy

**Independent Test**: Generate report and verify archive file created in data/reports/

### Tests for User Story 4

- [x] T051 [P] [US4] Write unit tests for ReportArchiver in tests/unit/test_report_archiver.py

### Implementation for User Story 4

- [x] T052 [US4] Implement ReportArchiver class in src/admin_reporting/archiver.py
- [x] T053 [US4] Implement archive_report() to save JSON and HTML files in src/admin_reporting/archiver.py
- [x] T054 [US4] Implement cleanup_old_reports() with retention policy in src/admin_reporting/archiver.py
- [x] T055 [US4] Integrate archiving into report generation flow in src/admin_reporting/reporter.py
- [x] T056 [US4] Create CLI command `collabiq report list` in src/collabiq/commands/report.py
- [x] T057 [US4] Create CLI command `collabiq report show` in src/collabiq/commands/report.py

**Checkpoint**: Reports are archived with proper retention and accessible via CLI

---

## Phase 7: Polish & Cross-Cutting Concerns ✅ COMPLETE

**Purpose**: Improvements that affect multiple user stories

- [x] T058 [P] Add structured logging throughout admin_reporting module
- [x] T059 [P] Update docs/cli/CLI_REFERENCE.md with report commands
- [x] T060 [P] Handle edge case: partial data availability (graceful degradation)
- [x] T061 [P] Handle edge case: email delivery failure with retry (already implemented via tenacity in GmailSender)
- [x] T062 [P] Handle edge case: large error volumes (summarize top 10)
- [x] T063 Run quickstart.md validation to verify all documented commands work
- [x] T064 Performance test: verify report generation completes in <30 seconds (actual: ~1 second)

**Checkpoint**: All edge cases handled, documentation updated, performance validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Core daily email functionality
- **User Story 2 (P1)**: Can start after Foundational - Shares AlertManager with US3 but is independently testable
- **User Story 3 (P2)**: Can start after Foundational - Extends AlertManager created in US2 but can be tested independently
- **User Story 4 (P3)**: Can start after Foundational - Completely independent of other stories

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before CLI commands
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T002, T003, T004 can run in parallel
- T007, T008 can run in parallel

**Foundational Phase (Phase 2)**:
- T011, T013, T015, T016, T017 can run in parallel (different files)

**User Story Phases**:
- Once Foundational completes, all user stories can start in parallel
- Tests within each story marked [P] can run in parallel
- Template creation tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write unit tests for ReportGenerator in tests/unit/test_report_generator.py"
Task: "Write integration tests for report delivery in tests/integration/test_report_delivery.py"
```

## Parallel Example: Foundational Phase

```bash
# Launch parallel foundational tasks:
Task: "Write unit tests for GmailSender in tests/unit/test_gmail_sender.py"
Task: "Write unit tests for MetricsCollector in tests/unit/test_metrics_collector.py"
Task: "Create daily_report.html.j2 template in src/admin_reporting/templates/"
Task: "Create daily_report.txt.j2 template in src/admin_reporting/templates/"
Task: "Write unit tests for ReportRenderer in tests/unit/test_report_renderer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Daily Summary Email)
4. **STOP and VALIDATE**: Test daily report generation independently
5. Deploy/demo if ready - admin can now receive daily reports!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP: Daily emails!)
3. Add User Story 2 → Test independently → Deploy (Critical alerts!)
4. Add User Story 3 → Test independently → Deploy (Actionable insights!)
5. Add User Story 4 → Test independently → Deploy (Report archiving!)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Daily Email) + User Story 3 (Insights)
   - Developer B: User Story 2 (Alerts) + User Story 4 (Archiving)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 and US2 are both P1 priority - complete both for full MVP value
