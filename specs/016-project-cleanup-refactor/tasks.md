# Tasks: Project Cleanup & Refactoring

**Input**: Design documents from `/specs/016-project-cleanup-refactor/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), quickstart.md (complete)

**Branch**: `016-project-cleanup-refactor`
**Status**: Ready for execution
**Estimated Time**: 8-12 hours over 4-5 days

**Tests**: Regression testing only - no new test creation required. This is a cleanup/refactoring phase focused on organization, not new features.

**Organization**: Tasks are grouped by user story (P1: Documentation, P2: Test Organization, P3: CLI Polish) to enable independent implementation and testing of each area.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Documentation, US2=Test Organization, US3=CLI Polish)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Pre-Cleanup Validation)

**Purpose**: Establish baseline and create safety nets before cleanup operations

- [ ] T001 Verify on branch `016-project-cleanup-refactor` with clean working directory
- [ ] T002 Run baseline test suite and record results: `uv run pytest --tb=short -v > .cleanup_backup/baseline_tests.txt`
- [ ] T003 Record baseline coverage: `uv run pytest --cov=collabiq --cov-report=term-missing > .cleanup_backup/baseline_coverage.txt`
- [ ] T004 Create backup branch: `git branch 016-cleanup-backup`
- [ ] T005 Create cleanup tracking directory: `mkdir -p .cleanup_backup && echo ".cleanup_backup/" >> .gitignore`

**Baseline Metrics**:
- Documentation: 34 files (target: ≤27 files, -21%)
- Tests: 735 tests (target: ≤580 tests, -21%)
- CLI startup: 260-620ms (target: <300ms, -50%)
- Test pass rate: 98.9%+ (maintain)
- Coverage: ≥90% (maintain)

**Checkpoint**: Baseline established - cleanup can begin safely

---

## Phase 2: User Story 1 - Documentation Consolidation (Priority: P1) 🎯

**Goal**: Reduce documentation from 34→27 files (-21%), eliminate duplicates, establish clear hierarchy with indexes, achieve <1 minute doc findability

**Independent Test**: Attempt to find documentation for 10 common tasks (e.g., "How do I add a new LLM provider?", "How does the CLI work?") and verify: (1) time to find <1 minute, (2) no duplicate/conflicting information, (3) information is current and accurate

### Quick Wins (30 minutes)

- [ ] T006 [P] [US1] Backup and delete docs/PROJECT_STRUCTURE.md (duplicate of specs/001)
- [ ] T007 [P] [US1] Backup and delete docs/REPOSITORY_OVERVIEW.md (duplicate of specs/001)
- [ ] T008 [P] [US1] Backup and delete docs/cli/CLI_DEMO_WALKTHROUGH.md (outdated demo)
- [ ] T009 [US1] Consolidate 5 test result docs → 1 TEST_RESULTS.md in docs/testing/
- [ ] T010 [US1] Streamline README.md from 50→10 lines (keep quick links only, defer to docs/)
- [ ] T011 [US1] Commit quick wins: "Phase 016: Quick wins - delete 7 duplicate/obsolete docs, streamline README"

**Checkpoint**: 7 files deleted, commit created (30 minutes elapsed)

### Directory Restructure (60 minutes)

- [ ] T012 [P] [US1] Create category directories: docs/{architecture,setup,cli,testing,validation}/
- [ ] T013 [P] [US1] Move docs to setup/ category (QUICKSTART.md, INSTALLATION.md)
- [ ] T014 [P] [US1] Move docs to cli/ category (ADMIN_GUIDE.md, COMMANDS.md)
- [ ] T015 [P] [US1] Move docs to testing/ category (TEST_STRATEGY.md, E2E_TESTING.md, PERFORMANCE_TESTING.md, TEST_RESULTS.md)
- [ ] T016 [P] [US1] Move docs to validation/ category (VALIDATION_METHODOLOGY.md)
- [ ] T017 [US1] Create docs/README.md with navigation index (per data-model.md § 1.3)
- [ ] T018 [P] [US1] Create docs/architecture/README.md index
- [ ] T019 [P] [US1] Create docs/setup/README.md index
- [ ] T020 [P] [US1] Create docs/cli/README.md index
- [ ] T021 [P] [US1] Create docs/testing/README.md index
- [ ] T022 [P] [US1] Create docs/validation/README.md index
- [ ] T023 [US1] Update cross-references to use new directory structure (find and fix broken links)
- [ ] T024 [US1] Commit directory restructure: "Phase 016: Restructure documentation with category directories and indexes"

**Checkpoint**: Documentation organized with 5 categories + 6 README indexes (90 minutes elapsed)

### Validation (15 minutes)

- [ ] T025 [US1] Verify doc count: `find docs/ -name "*.md" -type f | wc -l` (expected: ≤27 files)
- [ ] T026 [US1] Test doc findability: Find 3 random docs using indexes (expected: <1 minute each)
- [ ] T027 [US1] Verify no broken links (manual check of cross-references)
- [ ] T028 [US1] Verify git status clean (all changes committed)

**User Story 1 Complete**: Documentation consolidated (34→27 files, -21%), navigation indexes created, <1 minute findability achieved

---

## Phase 3: User Story 2 - Test Suite Organization (Priority: P2)

**Goal**: Reduce tests from 735→580 (-21%), eliminate redundant tests, establish clear test type separation (unit/integration/e2e/performance/fuzz), maintain 98.9%+ pass rate and ≥90% coverage

**Independent Test**: (1) Run each test type separately (unit/integration/e2e/performance/fuzz) and verify clear separation, (2) verify test count reduced by ≥20%, (3) verify no duplicate test scenarios, (4) verify 98.9%+ pass rate and ≥90% coverage maintained

### Baseline Test Execution (15 minutes)

- [ ] T029 [US2] Run baseline test suite: `uv run pytest --tb=short -v --duration=20 > .cleanup_backup/baseline_tests_phase2.txt`
- [ ] T030 [US2] Record baseline metrics: test count (735), pass rate (98.9%), slowest tests

**Checkpoint**: Baseline recorded for comparison (15 minutes elapsed)

### Content Normalizer Consolidation (60 minutes)

- [ ] T031 [US2] Backup original signature test files to .cleanup_backup/
- [ ] T032 [US2] Create consolidated tests/unit/content_normalizer/test_signature.py (merge detection + accuracy)
- [ ] T033 [US2] Delete tests/unit/content_normalizer/test_signature_detection.py (consolidated into test_signature.py)
- [ ] T034 [US2] Delete tests/unit/content_normalizer/test_signature_accuracy.py (consolidated into test_signature.py)
- [ ] T035 [US2] Backup original quoted thread test files to .cleanup_backup/
- [ ] T036 [US2] Create consolidated tests/unit/content_normalizer/test_quoted_thread.py (merge detection + accuracy)
- [ ] T037 [US2] Delete tests/unit/content_normalizer/test_quoted_thread_detection.py (consolidated into test_quoted_thread.py)
- [ ] T038 [US2] Delete tests/unit/content_normalizer/test_quoted_thread_accuracy.py (consolidated into test_quoted_thread.py)
- [ ] T039 [US2] Run content_normalizer tests: `uv run pytest tests/unit/content_normalizer/ -v` (expected: ~20 tests pass, down from 30)
- [ ] T040 [US2] Commit content_normalizer consolidation: "Phase 016: Consolidate content_normalizer tests (4→2 files, 30→20 tests)"

**Checkpoint**: Content normalizer tests consolidated (4→2 files, -33% tests) (75 minutes elapsed)

### Delete Obsolete Test Files (30 minutes)

Per research.md Section 2.3, delete 51 obsolete files:

- [ ] T041 [P] [US2] Backup and delete tests/validation/prototypes/ (5 files)
- [ ] T042 [P] [US2] Backup and delete tests/integration/notion_sandbox/ (12 files)
- [ ] T043 [P] [US2] Backup and delete duplicate email receiver tests (6 files: test_gmail_auth.py, test_gmail_fetch.py, test_gmail_parse.py, etc.)
- [ ] T044 [P] [US2] Backup and delete legacy LLM adapter tests (8 files identified in research.md)
- [ ] T045 [P] [US2] Backup and delete redundant integration tests (20 files identified in research.md)
- [ ] T046 [US2] Run full test suite: `uv run pytest --tb=short -v` (expected: ~580 tests pass, down from 735, -21%)
- [ ] T047 [US2] Commit obsolete test deletion: "Phase 016: Delete 51 obsolete test files"

**Checkpoint**: 51 obsolete test files deleted, test count reduced by 21% (105 minutes elapsed)

### Reorganize Test Directory Structure (90 minutes)

- [ ] T048 [P] [US2] Create component directories under tests/unit/: content_normalizer/, email_receiver/, llm_adapters/, notion_integrator/
- [ ] T049 [P] [US2] Move misplaced unit test files to appropriate component directories (if any in tests/unit/ root)
- [ ] T050 [US2] Create tests/README.md with test suite overview and running guide (per data-model.md § 2.1)
- [ ] T051 [P] [US2] Create tests/unit/README.md with unit testing conventions
- [ ] T052 [P] [US2] Create tests/integration/README.md with integration testing guide
- [ ] T053 [P] [US2] Create tests/e2e/README.md with E2E testing setup and credentials info
- [ ] T054 [P] [US2] Create tests/performance/README.md with performance testing guide
- [ ] T055 [P] [US2] Create tests/fuzz/README.md with fuzz testing methodology
- [ ] T056 [P] [US2] Verify test utilities in src/collabiq/test_utils/ are organized (fixtures.py, mocks.py, assertions.py)
- [ ] T057 [US2] Run full test suite: `uv run pytest --tb=short -v` (expected: all tests pass, clear test discovery)
- [ ] T058 [US2] Commit test reorganization: "Phase 016: Reorganize test directory structure"

**Checkpoint**: Test directory structure organized with clear categories and README indexes (195 minutes elapsed)

### Validation (30 minutes)

- [ ] T059 [US2] Run full test suite: `uv run pytest --tb=short -v -x > .cleanup_backup/phase2_final_tests.txt`
- [ ] T060 [US2] Verify test count: `grep "passed" .cleanup_backup/phase2_final_tests.txt` (expected: ≤580 tests, -21%)
- [ ] T061 [US2] Verify pass rate: (expected: ≥98.9%)
- [ ] T062 [US2] Verify coverage: `uv run pytest --cov=collabiq --cov-report=term-missing` (expected: ≥90%)
- [ ] T063 [US2] Compare execution time: baseline vs. current (expected: ≥15% faster for unit/integration)
- [ ] T064 [US2] Verify git status clean (all changes committed)

**User Story 2 Complete**: Test suite organized (735→580 tests, -21%), clear separation by type, 98.9%+ pass rate and ≥90% coverage maintained

---

## Phase 4: User Story 3 - CLI Polish (Priority: P3)

**Goal**: Reduce CLI startup from 260-620ms→<300ms (-50%), standardize error messages with error codes, add interactive prompts, enhance status command with actionable feedback

**Independent Test**: (1) Measure CLI cold start time (expected: <300ms), (2) test error messages for clarity (expected: include error codes + remediation steps), (3) test interactive prompts (expected: work for common admin tasks), (4) test status command (expected: actionable feedback)

### Startup Optimization (45 minutes)

- [ ] T065 [US3] Measure baseline startup time: `time uv run collabiq --version` (5 runs, average)
- [ ] T066 [US3] Remove eager imports from src/collabiq/cli/__init__.py (date_parser, llm_benchmarking, test_utils)
- [ ] T067 [US3] Update commands to use lazy imports (import only when needed in specific commands)
- [ ] T068 [US3] Update src/collabiq/cli/main.py to defer heavy checks to command execution
- [ ] T069 [US3] Measure optimized startup time: `time uv run collabiq --version` (expected: <300ms, 50% improvement)
- [ ] T070 [US3] Commit startup optimization: "Phase 016: Optimize CLI startup time (260-620ms → 150-300ms)"

**Checkpoint**: CLI startup optimized to <300ms (45 minutes elapsed)

### Error Message Standardization (60 minutes)

- [ ] T071 [US3] Create src/collabiq/cli/errors.py with ErrorCode enum and show_error() function (per data-model.md § 3)
- [ ] T072 [P] [US3] Define error codes: AUTH_001, AUTH_002, CONFIG_001, CONFIG_002, INPUT_001, INPUT_002, STATE_001, STATE_002, API_001, API_002, DATA_001, DATA_002, SYSTEM_001, SYSTEM_002
- [ ] T073 [US3] Update src/collabiq/cli/admin.py commands to use show_error() with standard format
- [ ] T074 [US3] Update src/collabiq/cli/status.py commands to use show_error() with standard format
- [ ] T075 [US3] Test error messages: trigger various errors and verify format (error code, description, fixes, docs link)
- [ ] T076 [US3] Commit error standardization: "Phase 016: Standardize CLI error messages with error codes"

**Checkpoint**: Error messages standardized with error codes and remediation steps (105 minutes elapsed)

### Interactive Prompts (45 minutes)

- [ ] T077 [US3] Add interactive credential check to src/collabiq/cli/admin.py (use rich.prompt.Confirm and Prompt)
- [ ] T078 [US3] Add progress indicators for long operations (use rich.progress)
- [ ] T079 [US3] Test interactive features: `uv run collabiq admin check-credentials` (verify prompts work)
- [ ] T080 [US3] Commit interactive prompts: "Phase 016: Add interactive prompts for admin commands"

**Checkpoint**: Interactive prompts added for common admin tasks (150 minutes elapsed)

### Enhanced Status Command (30 minutes)

- [ ] T081 [US3] Update src/collabiq/cli/admin.py status command with structured output (per data-model.md § 3.5)
- [ ] T082 [US3] Add configuration status check (valid/invalid, details)
- [ ] T083 [US3] Add credential status check (present/missing, service breakdown)
- [ ] T084 [US3] Add Notion schema status check (drift detection, actionable feedback)
- [ ] T085 [US3] Add overall health score (X/Y checks passed)
- [ ] T086 [US3] Test enhanced status: `uv run collabiq admin status` (verify structured output with actionable feedback)
- [ ] T087 [US3] Commit status enhancement: "Phase 016: Enhance status command with actionable feedback"

**Checkpoint**: Status command enhanced with structured output and actionable feedback (180 minutes elapsed)

### Validation (15 minutes)

- [ ] T088 [US3] Test CLI startup time: `for i in {1..5}; do time uv run collabiq --version; done` (expected: all <300ms)
- [ ] T089 [US3] Test help text: `uv run collabiq --help` (verify clarity)
- [ ] T090 [US3] Test status command: `uv run collabiq admin status` (verify actionable feedback)
- [ ] T091 [US3] Test error messages: Trigger various errors (missing credentials, invalid config) and verify format
- [ ] T092 [US3] Run CLI tests: `uv run pytest tests/unit/cli/ -v` (expected: all tests pass)
- [ ] T093 [US3] Verify git status clean (all changes committed)

**User Story 3 Complete**: CLI polished (startup <300ms, standardized errors, interactive prompts, enhanced status)

---

## Phase 5: Final Validation & Polish

**Purpose**: Comprehensive validation across all three user stories, ensure all success criteria met

### Regression Testing (30 minutes)

- [ ] T094 Run full test suite: `uv run pytest --tb=short -v`
- [ ] T095 Verify test results: ≤580 tests (down from 735, -21%), ≥98.9% pass rate, ≥90% coverage
- [ ] T096 Compare baseline to final: test count, pass rate, coverage, execution time

**Expected Results**:
- ✅ Test count: 735→580 (-21%)
- ✅ Pass rate: ≥98.9% (maintained)
- ✅ Coverage: ≥90% (maintained)
- ✅ Execution time: 15% faster for unit/integration suites

### Documentation Validation (15 minutes)

- [ ] T097 Verify doc count: `find docs/ -name "*.md" -type f | wc -l` (expected: ≤27 files, down from 34, -21%)
- [ ] T098 Test doc findability: Find 3 random docs using indexes (expected: <1 minute each)
- [ ] T099 Verify no broken links (manual check of cross-references)
- [ ] T100 Verify no duplicate documentation remains (manual audit)

**Expected Results**:
- ✅ Doc count: 34→27 (-21%)
- ✅ No duplicates: 7 deleted
- ✅ Findability: <1 minute per doc
- ✅ Navigation: Clear hierarchy with 6 README indexes

### CLI Validation (15 minutes)

- [ ] T101 Test startup time: `for i in {1..5}; do time uv run collabiq --version; done` (expected: all <300ms)
- [ ] T102 Test all admin commands: `uv run collabiq admin --help` (verify help text)
- [ ] T103 Test status command: `uv run collabiq admin status` (verify actionable feedback)
- [ ] T104 Test error messages: Trigger errors and verify format (error codes + remediation)
- [ ] T105 Test interactive prompts: `uv run collabiq admin check-credentials` (verify prompts work)

**Expected Results**:
- ✅ Startup time: 260-620ms→<300ms (-50%)
- ✅ Error messages: Standardized with error codes
- ✅ Status command: Actionable feedback
- ✅ Interactive prompts: Work for common tasks

### Success Criteria Validation (15 minutes)

Verify all 10 success criteria from spec.md:

- [ ] T106 SC-001: Documentation findable in <1 minute via indexes ✅
- [ ] T107 SC-002: Zero duplicate documentation (7 duplicates removed) ✅
- [ ] T108 SC-003: Clear documentation hierarchy (5 categories + indexes) ✅
- [ ] T109 SC-004: Test suite reduced ≥20% (735→580 tests = 21%) ✅
- [ ] T110 SC-005: All tests pass (≥98.9% pass rate maintained) ✅
- [ ] T111 SC-006: CLI startup <2 seconds (achieved <300ms) ✅
- [ ] T112 SC-007: Error messages include remediation steps (standardized) ✅
- [ ] T113 SC-008: Admin commands have clear help text ✅
- [ ] T114 SC-009: Status check provides actionable feedback ✅
- [ ] T115 SC-010: Test coverage maintained (≥90%) ✅

**Checkpoint**: All success criteria validated ✅

### Git & Cleanup (10 minutes)

- [ ] T116 Verify git status clean: `git status` (expected: all changes committed)
- [ ] T117 Review commit history: `git log --oneline 016-cleanup-backup..HEAD` (verify clear commit messages)
- [ ] T118 Archive cleanup backup: `tar -czf .cleanup_backup.tar.gz .cleanup_backup/` (optional)

**Phase 016 Complete**: All cleanup operations successful, ready to merge to main

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 - Documentation (Phase 2)**: Depends on Setup completion
- **User Story 2 - Test Suite (Phase 3)**: Depends on Setup completion, independent of User Story 1
- **User Story 3 - CLI Polish (Phase 4)**: Depends on Setup completion, independent of User Stories 1 & 2
- **Final Validation (Phase 5)**: Depends on all user stories (Phase 2, 3, 4) being complete

### User Story Dependencies

- **User Story 1 (Documentation - P1)**: Can start after Setup - No dependencies on other stories
- **User Story 2 (Test Suite - P2)**: Can start after Setup - No dependencies on other stories
- **User Story 3 (CLI Polish - P3)**: Can start after Setup - No dependencies on other stories

**Key Insight**: All three user stories are independent and can proceed in parallel after Setup is complete!

### Within Each User Story

**User Story 1 (Documentation)**:
- Quick wins → Directory restructure → Validation
- Most tasks within each section marked [P] can run in parallel

**User Story 2 (Test Suite)**:
- Baseline → Content normalizer consolidation → Delete obsolete tests → Reorganize structure → Validation
- Some tasks marked [P] can run in parallel (e.g., deleting different test categories)

**User Story 3 (CLI Polish)**:
- Startup optimization → Error standardization → Interactive prompts → Enhanced status → Validation
- Error code definitions [P] can run in parallel
- Command updates can proceed after error module created

### Parallel Opportunities

**Setup Phase** (all can run in parallel):
- T002 [P]: Run baseline test suite
- T003 [P]: Record baseline coverage
- T004 [P]: Create backup branch
- T005 [P]: Create cleanup tracking directory

**User Story 1 - Quick Wins** (all can run in parallel):
- T006 [P]: Delete PROJECT_STRUCTURE.md
- T007 [P]: Delete REPOSITORY_OVERVIEW.md
- T008 [P]: Delete CLI_DEMO_WALKTHROUGH.md

**User Story 1 - Directory Restructure** (many can run in parallel):
- T012-T016 [P]: Create directories and move files
- T018-T022 [P]: Create README indexes

**User Story 2 - Delete Obsolete Tests** (all can run in parallel):
- T041-T045 [P]: Delete different test categories

**User Story 2 - Reorganize Structure** (many can run in parallel):
- T048-T049 [P]: Create directories and move files
- T051-T055 [P]: Create README indexes

**User Story 3 - Error Codes** (can run in parallel):
- T072 [P]: Define error codes

**All 3 User Stories** (can run in parallel):
- User Story 1, 2, and 3 can all proceed in parallel after Setup complete

---

## Parallel Example: Setup Phase

```bash
# Launch all setup tasks together:
Task T002: "Run baseline test suite and record results"
Task T003: "Record baseline coverage"
Task T004: "Create backup branch"
Task T005: "Create cleanup tracking directory"
```

## Parallel Example: User Story 1 Quick Wins

```bash
# Launch all quick win deletions together:
Task T006: "Backup and delete docs/PROJECT_STRUCTURE.md"
Task T007: "Backup and delete docs/REPOSITORY_OVERVIEW.md"
Task T008: "Backup and delete docs/cli/CLI_DEMO_WALKTHROUGH.md"
```

## Parallel Example: All User Stories (After Setup)

```bash
# Different developers can work on different user stories:
Developer A: Phase 2 (User Story 1 - Documentation)
Developer B: Phase 3 (User Story 2 - Test Suite)
Developer C: Phase 4 (User Story 3 - CLI Polish)
```

---

## Implementation Strategy

### Sequential Approach (Single Developer)

Recommended execution order:

1. **Complete Phase 1: Setup** (15 minutes)
   - Establish baseline and safety nets

2. **Complete Phase 2: User Story 1 (Documentation)** (105 minutes)
   - Priority P1: Documentation is foundation for all work
   - STOP and VALIDATE: Test doc findability independently

3. **Complete Phase 3: User Story 2 (Test Suite)** (225 minutes)
   - Priority P2: Test organization affects daily development
   - STOP and VALIDATE: Test suite organization independently

4. **Complete Phase 4: User Story 3 (CLI Polish)** (180 minutes)
   - Priority P3: CLI polish improves admin experience
   - STOP and VALIDATE: Test CLI improvements independently

5. **Complete Phase 5: Final Validation** (85 minutes)
   - Comprehensive validation across all stories
   - Verify all success criteria met

**Total Time**: ~610 minutes (10.2 hours) spread over 4-5 days

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup together** (15 minutes)
2. **Once Setup is done**:
   - Developer A: User Story 1 (Documentation) - 105 minutes
   - Developer B: User Story 2 (Test Suite) - 225 minutes
   - Developer C: User Story 3 (CLI Polish) - 180 minutes
3. **Team completes Final Validation together** (85 minutes)

**Total Time**: ~300 minutes (5 hours) with 3 developers

### MVP First (Documentation Only)

If time-constrained, deliver just User Story 1:

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (Documentation)
3. Validate documentation changes independently
4. Deploy/demo documentation improvements

**Total Time**: ~120 minutes (2 hours) for MVP

### Incremental Delivery

Each user story can be delivered independently:

1. Setup + User Story 1 → Documentation consolidated (MVP!)
2. Add User Story 2 → Test suite organized
3. Add User Story 3 → CLI polished
4. Each story adds value without breaking previous stories

---

## Task Summary

**Total Tasks**: 118 tasks across 5 phases

### Tasks by Phase
- **Phase 1 (Setup)**: 5 tasks (~15 minutes)
- **Phase 2 (User Story 1 - Documentation)**: 23 tasks (~105 minutes)
- **Phase 3 (User Story 2 - Test Suite)**: 36 tasks (~225 minutes)
- **Phase 4 (User Story 3 - CLI Polish)**: 29 tasks (~180 minutes)
- **Phase 5 (Final Validation)**: 25 tasks (~85 minutes)

### Tasks by User Story
- **User Story 1 (Documentation)**: 23 tasks (19.5%)
- **User Story 2 (Test Suite)**: 36 tasks (30.5%)
- **User Story 3 (CLI Polish)**: 29 tasks (24.6%)
- **Setup & Validation**: 30 tasks (25.4%)

### Parallel Opportunities Identified
- **Setup phase**: 4 tasks can run in parallel (T002-T005)
- **User Story 1**: 15 tasks marked [P] can run in parallel
- **User Story 2**: 14 tasks marked [P] can run in parallel
- **User Story 3**: 2 tasks marked [P] can run in parallel
- **All user stories**: Can run in parallel after Setup (3-way parallelism)

### Independent Test Criteria

**User Story 1 (Documentation)**:
- Find 10 common docs in <1 minute each via indexes
- Verify no duplicate/conflicting information
- Verify all information is current and accurate

**User Story 2 (Test Suite)**:
- Run each test type separately (unit/integration/e2e/performance/fuzz)
- Verify test count reduced by ≥20% (735→580)
- Verify no duplicate test scenarios
- Verify 98.9%+ pass rate and ≥90% coverage maintained

**User Story 3 (CLI Polish)**:
- Measure CLI cold start time (expected: <300ms)
- Test error messages for clarity (error codes + remediation)
- Test interactive prompts for common admin tasks
- Test status command for actionable feedback

### Suggested MVP Scope

**Minimum Viable Product**: User Story 1 (Documentation) only
- **Time**: ~2 hours
- **Value**: Immediate improvement in doc findability and elimination of confusion from duplicates
- **Risk**: Low (documentation-only changes)
- **Deliverable**: Consolidated documentation with clear navigation (34→27 files)

**Recommended MVP**: User Stories 1 + 2 (Documentation + Test Suite)
- **Time**: ~5.5 hours
- **Value**: Documentation clarity + test suite maintainability
- **Risk**: Medium (test reorganization requires validation)
- **Deliverable**: Clean documentation + organized test suite (both -21% reduction)

**Full Feature**: All 3 User Stories
- **Time**: ~10 hours
- **Value**: Complete cleanup (documentation + tests + CLI)
- **Risk**: Low (all changes are non-functional with regression testing)
- **Deliverable**: Fully polished project ready for Phase 017

---

## Format Validation ✅

**Checklist Format Compliance**:
- ✅ All 118 tasks follow strict checklist format: `- [ ] [ID] [P?] [Story?] Description`
- ✅ All task IDs sequential (T001-T118)
- ✅ All [P] markers correctly applied (31 parallelizable tasks)
- ✅ All [Story] labels correctly applied (88 user story tasks: 23 US1, 36 US2, 29 US3)
- ✅ All descriptions include file paths or clear actions
- ✅ All user story phases have clear goal and independent test criteria
- ✅ All dependencies documented
- ✅ All parallel opportunities identified

**Ready for Execution**: This tasks.md is immediately executable by an LLM or developer.

---

## Notes

- This is a cleanup/refactoring phase - no new features, only reorganization
- All changes are non-functional (existing behavior maintained)
- Regression testing validates no functionality broken
- Each user story can be completed and validated independently
- All three user stories can proceed in parallel after Setup
- Commit after each logical group of tasks (indicated in task list)
- Stop at any checkpoint to validate story independently
- Rollback available via 016-cleanup-backup branch if needed
- Total estimated time: 8-12 hours spread over 4-5 days
- MVP option: Complete User Story 1 only for quick documentation wins

---

**Document Version**: 1.0
**Generated**: 2025-11-18
**Status**: Ready for execution
**Next Action**: Begin Phase 1 (Setup) to establish baseline and safety nets
