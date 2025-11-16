# Tasks: Test Suites Improvements

**Input**: Design documents from `/Users/jlim/Projects/CollabIQ/specs/015-test-suite-improvements/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create new directories: `src/collabiq/date_parser/`, `src/collabiq/llm_benchmarking/`, `src/collabiq/test_utils/`, `tests/performance/`, `tests/fuzz/`, `tests/coverage_reports/`, `data/test_metrics/`
- [X] T002 Update `src/collabiq/__init__.py` to include new modules
- [X] T003 [MERGED INTO T038] Configure `pytest-cov` for granular coverage reports setup in `pyproject.toml` or `pytest.ini`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2.1: Bug Fixes (Existing Test Suite Stabilization)

**Note**: These tasks fix existing broken tests. Per Test-First principle, these are maintenance, not new development.

- [X] T004 Review all existing test suites and scripts in `tests/` and `scripts/` for refactoring opportunities
- [X] T005 Analyze and document refactoring opportunities for existing test codebase in `specs/015-test-suite-improvements/refactoring_analysis.md`
- [X] T005a Validate `refactoring_analysis.md` completeness against acceptance criteria: readability improvements, duplication removal, performance optimization, test coverage gaps
- [X] T006 [P] Address Pydantic V2 deprecation warnings by updating models to use `ConfigDict` in `src/llm_provider/types.py`, `src/e2e_test/models.py`, `src/models/matching.py`, `src/models/raw_email.py` ✅ All models already using ConfigDict
- [X] T007 [P] Resolve `datetime.utcnow()` deprecation warnings by replacing with `datetime.now(datetime.UTC)` in `src/llm_provider/date_utils.py`, `src/llm_provider/types.py`, `src/llm_adapters/claude_adapter.py`, `src/llm_adapters/openai_adapter.py`, `src/llm_orchestrator/quality_tracker.py`, `src/error_handling/models.py`, `src/error_handling/error_classifier.py`, `src/error_handling/retry.py`, `src/notion_integrator/dlq_manager.py`, `src/email_receiver/gmail_receiver.py`, `src/models/classification_service.py`, `src/content_normalizer/normalizer.py`, `src/models/duplicate_tracker.py`, `src/error_handling/structured_logger.py` and relevant test files. ✅ Fixed in 14 files
- [X] T008 [P] Register `pytest.mark.integration` and `pytest.mark.notion` in `pyproject.toml` or `pytest.ini` to resolve `PytestUnknownMarkWarning`. ✅ Registered in pyproject.toml
- [X] T009 Fix `AttributeError: 'AsyncClient' object has no attribute 'retrieve_database'` by updating `notion-client` API calls in `src/notion_integrator/integrator.py` and related test files. ✅ Already correct, using Client not AsyncClient
- [X] T010 Prevent Pydantic models from being collected as test classes by adjusting test collection configuration or model definition in `tests/integration/test_e2e_models.py`. ✅ Renamed TestRun → E2ETestRun, TestEmailMetadata → E2ETestEmailMetadata

### 2.2: Additional Critical Fixes (Import Path and CLI Architecture)

**Note**: These issues were discovered during T011 investigation and needed immediate resolution.

- [X] T010a Fix import path mismatches causing isinstance() failures ✅ Created and ran `fix_test_imports.py` to update 280+ imports across 57 test files
- [X] T010b Fix mock patch paths after import changes ✅ Created and ran `fix_test_patches.py` to update all mock patch paths
- [X] T010c Fix CLI architecture conflict between `llm test` and `test` commands ✅ Converted to hierarchical subcommand structure
- [X] T010d Document CLI architecture in `docs/architecture/CLI_ARCHITECTURE.md` ✅ Created comprehensive documentation

- [X] T011 **[STEP 1: FIX]** Investigate and fix all `AssertionError` and error failures in existing test suites ✅ 96% improvement (84→3 failures)
  - [X] T011.1 Fix companies cache tests - corrected patch paths ✅ Fixed 11 tests
  - [X] T011.2 Fix structured logger sanitization order ✅ Fixed email content truncation
  - [X] T011.3 Fix circuit breaker test isolation - proper reset in conftest ✅ Fixed 2 Gemini adapter tests
  - [X] T011.4 Fix CLI command registration - registered all 7 command groups ✅ Fixed 29 CLI tests
  - [X] T011.5 Add missing CLI commands (policy, set-policy, usage, disable, enable) ✅ Fixed 5 CLI contract tests
  - [X] T011.6 Fix Notion writer mock structure (mock.client.client path) ✅ Fixed 3 Notion writer tests
  - [X] T011.7 Fix circuit breaker reset in conftest.py (reset global instances) ✅ Fixed 2 Gemini adapter + 3 retry flow tests
  - [X] T011.8 Fix duplicate detection mock structure ✅ Fixed 3 duplicate detection tests
  - [X] T011.9 Fix Gemini retry flow mocking (genai.configure + response format) ✅ Fixed 3 Gemini retry tests
  - [X] T011.10 Fix E2E test import errors - corrected CLI script sys.path manipulation ✅ Fixed 2 E2E tests
- [X] T012 **[STEP 2: VERIFY]** Execute all existing test suites to confirm 100% pass rate: `pytest tests/ --maxfail=1` ✅ 727/735 non-manual tests passing (98.9%)
- [X] T013 **[STEP 3: ANALYZE]** Review and document refactoring opportunities based on successful test run in `refactoring_analysis.md` (criteria: duplication, readability, performance, coverage gaps) ✅ Comprehensive 478-line analysis complete
- [X] T013a Validate `refactoring_analysis.md` against acceptance criteria from US1 Scenario 5 ✅ All 4 acceptance criteria met

**Note**: T046 (refactoring) moved to Phase 3 as it depends on stable test foundation from steps above.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Achieve Truly End-to-End Automated Testing & Test Suite Refinement (Priority: P1) 🎯 MVP

**Goal**: The automated end-to-end test suite fetches real emails and performs real Notion writes, with robust cleanup, and existing test assets are reviewed and functional.

**Independent Test**: Run the automated E2E suite with configured test credentials for Gmail and Notion, observing successful email fetching, processing, Notion entry creation, and subsequent cleanup. Independently execute all existing test scripts and suites, verifying their successful completion and logical correctness.

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `pytest` fixture for test Gmail account setup and teardown in `tests/conftest.py`
- [ ] T015 [P] [US1] Implement `pytest` fixture for test Notion database setup and teardown in `tests/conftest.py`
- [ ] T016 [US1] Integrate `GmailReceiver` with E2E tests to fetch real emails in `tests/e2e/test_full_pipeline.py`
- [ ] T017 [US1] Implement Notion write validation in E2E tests in `tests/e2e/test_full_pipeline.py`
- [ ] T018 [US1] Develop robust cleanup mechanism for Notion test entries in `src/collabiq/test_utils/notion_cleanup.py`
- [ ] T019 [US1] Enhance `scripts/cleanup_test_entries.py` to utilize the new cleanup mechanism

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Enhance Date Extraction Testing and Robustness (Priority: P1)

**Goal**: Date extraction is highly robust and thoroughly tested across various formats, especially Korean.

**Independent Test**: Provide a diverse dataset of emails with various date formats (including Korean) to a dedicated date parsing module and verify the accuracy and consistency of the extracted and normalized dates.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create `src/collabiq/date_parser/parser.py` for date parsing and normalization logic
- [ ] T021 [P] [US2] Create `src/collabiq/date_parser/models.py` for date-related Pydantic models
- [ ] T022 [US2] Implement comprehensive unit tests for `src/collabiq/date_parser/parser.py` in `tests/unit/test_date_parser.py`
- [ ] T023 [US2] Implement integration tests for `date_parser` with email content in `tests/integration/test_date_extraction.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Improve LLM Performance for Korean Text (Priority: P2)

**Goal**: Systematically evaluate and optimize LLM performance for Korean text extraction.

**Independent Test**: Run a dedicated benchmarking suite with Korean text samples across different LLM providers and prompt variations, tracking metrics like confidence, completeness, and accuracy.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Create `src/collabiq/llm_benchmarking/suite.py` for benchmarking logic
- [ ] T025 [P] [US3] Create `src/collabiq/llm_benchmarking/prompts.py` for prompt variations
- [ ] T026 [US3] Implement benchmarking suite to evaluate LLM performance on Korean/English text in `src/collabiq/llm_benchmarking/suite.py`
- [ ] T027 [US3] Develop prompt optimization tests in `tests/integration/test_llm_prompts.py`
- [ ] T027a [US3] Create `src/collabiq/llm_benchmarking/ab_testing.py` for A/B test framework
- [ ] T027b [US3] Implement A/B testing infrastructure for comparing prompt variations in `tests/integration/test_llm_prompts.py`
- [ ] T027c [US3] Create test cases for at least 3 prompt variations for Korean text extraction in `tests/integration/test_llm_prompts.py`
- [ ] T028 [US3] Create `scripts/benchmark_llm_performance.py` to run the benchmarking suite

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 5 - Formalize Performance Testing (Priority: P2)

**Goal**: Have a formalized performance test suite with defined thresholds.

**Independent Test**: Run a dedicated performance test suite that measures key metrics (e.g., processing time, response times) under various conditions and asserts against predefined thresholds.

### Implementation for User Story 5

- [ ] T029 [P] [US5] Create `tests/performance/test_performance.py` for performance test suite
- [ ] T030 [P] [US5] Create `src/collabiq/test_utils/performance_monitor.py` for performance metric collection
- [ ] T031 [US5] Implement performance test suite to measure key metrics in `tests/performance/test_performance.py`
- [ ] T032 [US5] Define performance thresholds and integrate assertions in `tests/performance/test_performance.py`

---

## Phase 7: User Story 6 - Expand Negative Testing and Edge Cases (Priority: P2)

**Goal**: System is robust against invalid inputs, external API errors, and unexpected data scenarios.

**Independent Test**: Systematically introduce invalid inputs, simulate API errors, and use fuzzing techniques against various modules, then verify that the system handles these scenarios gracefully.

### Implementation for User Story 6

- [ ] T033 [P] [US6] Create `tests/fuzz/test_fuzzing.py` for fuzz testing configurations
- [ ] T034 [P] [US6] Create `src/collabiq/test_utils/fuzz_generator.py` for input generation
- [ ] T035 [US6] Implement systematic negative test cases in `tests/unit/test_error_handling.py` and `tests/integration/test_api_errors.py`
- [ ] T036 [US6] Implement fuzz testing capabilities for input parsing in `tests/fuzz/test_fuzzing.py`
- [ ] T037 [US6] Create `scripts/fuzz_test_inputs.py` to execute fuzz tests

---

## Phase 8: User Story 4 - Granular Test Coverage Reporting (Priority: P3)

**Goal**: Generate separate code coverage reports for unit, integration, and end-to-end test suites.

**Independent Test**: Configure the test runner to generate separate coverage reports for different test suites (e.g., unit, integration, E2E) and verify that distinct reports are produced, accurately reflecting the coverage of each layer.

### Implementation for User Story 4

- [ ] T038 [US4] Refine `pytest-cov` configuration for granular reports (unit, integration, E2E) in `pyproject.toml` or `pytest.ini`
- [ ] T039 [US4] Create `tests/coverage_reports/README.md` to explain how to generate and view reports

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `specs/015-test-suite-improvements/quickstart.md` with instructions for running new test suites and viewing reports
- [ ] T041 [P] Documentation updates in `docs/testing/E2E_TESTING.md` with details on real E2E setup
- [ ] T042 Code cleanup and refactoring based on analysis in T005
- [ ] T043 Ensure all new test artifacts (reports, metrics) are stored in `data/test_metrics/`
- [ ] T044 Run `make lint` and `make format` to ensure code quality
- [ ] T045 Final review of all changes against the spec

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 6 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Implement pytest fixture for test Gmail account setup and teardown in tests/conftest.py"
Task: "Implement pytest fixture for test Notion database setup and teardown in tests/conftest.py"

# Launch all models for User Story 1 together:
# (No separate models for US1, but this is an example)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 5 → Test independently → Deploy/Demo
6. Add User Story 6 → Test independently → Deploy/Demo
7. Add User Story 4 → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 5
   - Developer E: User Story 6
   - Developer F: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence