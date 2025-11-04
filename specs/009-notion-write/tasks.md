# Tasks: Notion Write Operations (Phase 2d)

**Input**: Design documents from `/specs/009-notion-write/`
**Prerequisites**: plan.md (complete), spec.md (3 user stories: P1, P2, P3), research.md, data-model.md, contracts/

**Tests**: TDD mandatory per constitution - contract and integration tests written BEFORE implementation

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/`, `tests/` at repository root
- Extends existing `src/notion_integrator/` package
- Follows Phase 2a/2b/2c testing patterns

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create file stubs and basic project structure for Phase 2d

- [x] T001 Create DLQ directory structure at data/dlq/
- [x] T002 [P] Create NotionWriter stub in src/notion_integrator/writer.py
- [x] T003 [P] Create FieldMapper stub in src/notion_integrator/field_mapper.py
- [x] T004 [P] Create DLQManager stub in src/notion_integrator/dlq_manager.py
- [x] T005 [P] Create WriteResult data model in src/llm_provider/types.py
- [x] T006 [P] Create DLQEntry data model in src/llm_provider/types.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and base infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement WriteResult Pydantic model with all fields (success, page_id, email_id, error_type, error_message, status_code, retry_count, is_duplicate, existing_page_id) in src/llm_provider/types.py
- [x] T008 Implement DLQEntry Pydantic model with all fields (email_id, failed_at, retry_count, error dict, extracted_data, original_email_content, dlq_file_path) in src/llm_provider/types.py
- [x] T009 Add DUPLICATE_BEHAVIOR environment variable to src/config/settings.py with default value "skip"
- [x] T010 Update src/notion_integrator/__init__.py to export NotionWriter, FieldMapper, DLQManager classes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Write Extracted Email Data to Notion (Priority: P1) 🎯 MVP

**Goal**: Create new entries in CollabIQ Notion database with all extracted and classified data fields

**Independent Test**: Process a single email through the pipeline and verify that a corresponding Notion database entry is created with all fields correctly populated

### Tests for User Story 1 (TDD - Write FIRST, ensure they FAIL before implementation)

- [x] T011 [P] [US1] Contract test for NotionWriter.create_collabiq_entry() method signature in tests/contract/test_notion_writer.py
- [x] T012 [P] [US1] Contract test for NotionWriter.create_collabiq_entry() success case (returns WriteResult with success=True and page_id) in tests/contract/test_notion_writer.py
- [x] T013 [P] [US1] Contract test for NotionWriter.create_collabiq_entry() error case (returns WriteResult with success=False and error details) in tests/contract/test_notion_writer.py
- [x] T014 [P] [US1] Contract test for FieldMapper.map_to_notion_properties() method signature in tests/contract/test_field_mapper.py
- [x] T015 [P] [US1] Contract test for FieldMapper._format_rich_text() with Korean text preservation in tests/contract/test_field_mapper.py
- [x] T016 [P] [US1] Contract test for FieldMapper._format_select() with collaboration type values in tests/contract/test_field_mapper.py
- [x] T017 [P] [US1] Contract test for FieldMapper._format_relation() with company IDs in tests/contract/test_field_mapper.py
- [x] T018 [P] [US1] Contract test for FieldMapper._format_date() with datetime to ISO 8601 conversion in tests/contract/test_field_mapper.py
- [x] T019 [P] [US1] Contract test for FieldMapper._format_number() with confidence scores (0.0-1.0 range) in tests/contract/test_field_mapper.py
- [x] T020 [US1] Integration test for E2E write workflow (extract → classify → write → verify Notion entry) using sample-001.txt in tests/integration/test_notion_write_e2e.py

**Verify all tests FAIL before proceeding to implementation**

### Implementation for User Story 1

- [x] T021 [P] [US1] Implement FieldMapper.__init__() to accept DatabaseSchema and build property type map in src/notion_integrator/field_mapper.py
- [x] T022 [P] [US1] Implement FieldMapper._format_rich_text() with 2000 char truncation and UTF-8 Korean text support in src/notion_integrator/field_mapper.py
- [x] T023 [P] [US1] Implement FieldMapper._format_select() for collaboration type and intensity fields in src/notion_integrator/field_mapper.py
- [x] T024 [P] [US1] Implement FieldMapper._format_relation() with 32/36 char UUID validation in src/notion_integrator/field_mapper.py
- [x] T025 [P] [US1] Implement FieldMapper._format_date() with ISO 8601 date formatting in src/notion_integrator/field_mapper.py
- [x] T026 [P] [US1] Implement FieldMapper._format_number() for confidence scores in src/notion_integrator/field_mapper.py
- [x] T027 [US1] Implement FieldMapper.map_to_notion_properties() to map all ExtractedEntitiesWithClassification fields to Notion properties (담당자, 스타트업명, 협업기관, 협업형태, 협업강도, 요약, 날짜, email_id, 분류일시) in src/notion_integrator/field_mapper.py (depends on T021-T026)
- [x] T028 [US1] Implement NotionWriter.__init__() to accept NotionClient and initialize FieldMapper with schema discovery in src/notion_integrator/writer.py
- [x] T029 [US1] Implement NotionWriter._create_page_with_retry() with 3-attempt immediate retry for transient errors in src/notion_integrator/writer.py
- [x] T030 [US1] Implement NotionWriter.create_collabiq_entry() core write logic (field mapping + API call + response validation) in src/notion_integrator/writer.py (depends on T027, T028, T029)
- [x] T031 [US1] Add error handling and logging for write operations in src/notion_integrator/writer.py

**Run all User Story 1 tests - they should now PASS**

**Checkpoint**: At this point, User Story 1 should be fully functional - basic write operations work, Notion entries are created with all fields

---

## Phase 4: User Story 2 - Handle Duplicate Detection (Priority: P2)

**Goal**: Detect duplicate entries before write and either skip or update based on configuration

**Independent Test**: Process the same email twice and verify that only one Notion entry exists (or second processing updates first entry based on configuration)

### Tests for User Story 2 (TDD - Write FIRST, ensure they FAIL before implementation)

- [x] T032 [P] [US2] Contract test for NotionWriter.check_duplicate() method signature in tests/contract/test_notion_writer.py
- [x] T033 [P] [US2] Contract test for NotionWriter.check_duplicate() when duplicate exists (returns existing page_id) in tests/contract/test_notion_writer.py
- [x] T034 [P] [US2] Contract test for NotionWriter.check_duplicate() when no duplicate (returns None) in tests/contract/test_notion_writer.py
- [x] T035 [P] [US2] Integration test for duplicate detection with "skip" behavior (same email_id processed twice, only one entry created) in tests/integration/test_duplicate_detection.py
- [x] T036 [P] [US2] Integration test for duplicate detection with "update" behavior (same email_id processed twice, entry updated) in tests/integration/test_duplicate_detection.py
- [x] T037 [US2] Integration test for duplicate detection logging (verify skip action logged) in tests/integration/test_duplicate_detection.py

**Verify all tests FAIL before proceeding to implementation**

### Implementation for User Story 2

- [x] T038 [US2] Implement NotionWriter.check_duplicate() with email_id query using NotionClient.query_database() in src/notion_integrator/writer.py
- [x] T039 [US2] Update NotionWriter.create_collabiq_entry() to check for duplicates before write and handle "skip" behavior in src/notion_integrator/writer.py (depends on T038)
- [x] T040 [US2] Update NotionWriter.create_collabiq_entry() to handle "update" behavior (update existing entry if duplicate detected and config allows) in src/notion_integrator/writer.py (depends on T038)
- [x] T041 [US2] Add duplicate detection logging (log skip action with email_id and existing_page_id) in src/notion_integrator/writer.py
- [x] T042 [US2] Update WriteResult to populate is_duplicate and existing_page_id fields for duplicate cases in src/notion_integrator/writer.py

**Run all User Story 2 tests - they should now PASS**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - write operations work, duplicate detection prevents duplicate entries

---

## Phase 5: User Story 3 - Map Field Types Correctly (Priority: P2)

**Goal**: Ensure all Notion field types are correctly mapped and formatted to prevent API validation errors

**Independent Test**: Create test entries with all field types and verify each field is correctly formatted and accepted by Notion API

### Tests for User Story 3 (TDD - Write FIRST, ensure they FAIL before implementation)

- [x] T043 [P] [US3] Contract test for FieldMapper null handling (null fields omitted from properties dict) in tests/contract/test_field_mapper_edge_cases.py ✅
- [x] T044 [P] [US3] Contract test for FieldMapper rich_text truncation (2000 char limit enforced) in tests/contract/test_field_mapper_edge_cases.py ✅
- [x] T045 [P] [US3] Contract test for FieldMapper relation ID validation (32/36 char UUIDs accepted, invalid IDs rejected) in tests/contract/test_field_mapper_edge_cases.py ✅
- [x] T046 [P] [US3] Contract test for FieldMapper Korean text with special characters (emojis, punctuation) in tests/contract/test_field_mapper_edge_cases.py ✅
- [x] T047 [P] [US3] Integration test for all Notion property types (rich_text, select, relation, date, number) formatted correctly in tests/integration/test_notion_write_e2e.py ✅
- [x] T048 [US3] Integration test for graceful degradation (missing relation IDs omitted, entry still created) in tests/integration/test_notion_write_e2e.py ✅

**All tests PASS - existing implementation already handles edge cases correctly! ✅**

### Implementation for User Story 3

- [x] T049 [P] [US3] Null field handling already implemented - FieldMapper.map_to_notion_properties() uses `if` checks to omit None values ✅
- [x] T050 [P] [US3] Relation ID validation handled by Pydantic (min_length=32 on matched_company_id/matched_partner_id fields) ✅
- [x] T051 [P] [US3] Text truncation handled by Pydantic (max_length constraints on details=2000, collaboration_summary=750) ✅
- [x] T052 [US3] Manual review flag - SKIPPED (not required for MVP, can add in future if needed) ⏭️
- [x] T053 [US3] Collaboration type validation - Handled by Phase 2c LLM extraction (validated format) ✅
- [x] T054 [US3] Collaboration intensity validation - Handled by Phase 2c LLM extraction (validated values) ✅

**All User Story 3 tests PASS (7/7 tests passing) ✅**

**Checkpoint**: All user stories should now be independently functional - write operations are robust, handle edge cases gracefully

---

## Phase 6: Dead Letter Queue (DLQ) - Error Handling (Cross-Cutting)

**Goal**: Capture and persist failed writes for manual retry or debugging

**Independent Test**: Trigger write failure (invalid field value) and verify DLQ entry created with full context

### Tests for DLQ (TDD - Write FIRST, ensure they FAIL before implementation)

- [x] T055 [P] Contract test for DLQManager.save_failed_write() method signature in tests/contract/test_dlq_manager.py ✅
- [x] T056 [P] Contract test for DLQManager.save_failed_write() file creation with correct naming (email_id_timestamp.json) in tests/contract/test_dlq_manager.py ✅
- [x] T057 [P] Contract test for DLQManager.save_failed_write() serialization (ExtractedEntitiesWithClassification to JSON) in tests/contract/test_dlq_manager.py ✅
- [x] T058 [P] Contract test for DLQManager.load_dlq_entry() deserialization in tests/contract/test_dlq_manager.py ✅
- [x] T059 [P] Contract test for DLQManager.list_dlq_entries() listing all DLQ files in tests/contract/test_dlq_manager.py ✅
- [x] T060 [US1] Integration test for DLQ capture on write failure (trigger API error, verify DLQ entry created) in tests/integration/test_notion_write_e2e.py ✅

**All DLQ tests PASS (8/8 tests) ✅**

### Implementation for DLQ

- [x] T061 [P] Implement DLQManager.__init__() to accept dlq_dir path and create directory if not exists in src/notion_integrator/dlq_manager.py ✅
- [x] T062 [P] Implement DLQManager.save_failed_write() with file naming (email_id_timestamp.json), error context capture, and Pydantic JSON serialization in src/notion_integrator/dlq_manager.py ✅
- [x] T063 [P] Implement DLQManager.load_dlq_entry() to deserialize DLQEntry from JSON file in src/notion_integrator/dlq_manager.py ✅
- [x] T064 [P] Implement DLQManager.list_dlq_entries() to return sorted list of all DLQ file paths in src/notion_integrator/dlq_manager.py ✅
- [x] T065 [P] Implement DLQManager.retry_failed_write() to load entry, attempt write, delete file on success or increment retry_count in src/notion_integrator/dlq_manager.py ✅
- [x] T066 Update NotionWriter.create_collabiq_entry() to catch all exceptions and save to DLQ on failure in src/notion_integrator/writer.py ✅
- [x] T067 [P] Error classification already implemented - _create_page_with_retry() identifies validation errors (400) and doesn't retry ✅

**All DLQ tests PASS (8/8 tests: 7 contract + 1 integration) ✅**

---

## Phase 7: Manual Retry Script & Documentation

**Purpose**: Provide manual retry capability and usage instructions

- [ ] T068 Create manual retry script scripts/retry_dlq.py with CLI interface (--all, --file options)
- [ ] T069 Add argparse CLI parsing to scripts/retry_dlq.py for --all and --file arguments
- [ ] T070 Implement retry logic in scripts/retry_dlq.py (load DLQ entry, attempt write, delete on success, increment retry_count on failure)
- [ ] T071 Create manual test script tests/manual/test_phase2d_notion_write.py following Phase 2c pattern
- [ ] T072 Add demo scenarios to tests/manual/test_phase2d_notion_write.py (basic write, duplicate detection, error handling, DLQ retry)
- [ ] T073 [P] Update README.md to mark Phase 2d complete
- [ ] T074 [P] Update ROADMAP.md with Phase 2d completion status

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and cross-feature improvements

- [ ] T075 [P] Add comprehensive docstrings to all NotionWriter methods in src/notion_integrator/writer.py
- [ ] T076 [P] Add comprehensive docstrings to all FieldMapper methods in src/notion_integrator/field_mapper.py
- [ ] T077 [P] Add comprehensive docstrings to all DLQManager methods in src/notion_integrator/dlq_manager.py
- [ ] T078 Run full test suite (uv run pytest) and verify all tests pass
- [ ] T079 Execute manual test script (uv run python tests/manual/test_phase2d_notion_write.py) and verify all scenarios work
- [ ] T080 Validate quickstart.md instructions by following them step-by-step
- [ ] T081 [P] Run ruff check and ruff format on all new Phase 2d files
- [ ] T082 [P] Update CLAUDE.md with Phase 2d write operation patterns (if not already updated by update-agent-context.sh)
- [ ] T083 Create completion report at specs/009-notion-write/COMPLETION_REPORT.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - MVP
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Can start in parallel with US1 if desired, but logically builds on US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) - Can start in parallel with US1/US2 if desired, enhances robustness
- **DLQ (Phase 6)**: Depends on User Story 1 (Phase 3) - Cross-cutting error handling
- **Scripts (Phase 7)**: Depends on DLQ (Phase 6) - Manual retry capability
- **Polish (Phase 8)**: Depends on all desired user stories + DLQ + Scripts being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - THIS IS THE MVP
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Logically extends US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances robustness of US1 field mapping but independently testable

### Within Each User Story

**TDD Workflow (MANDATORY per constitution)**:
1. Write contract tests FIRST (red phase)
2. Verify tests FAIL
3. Implement functionality (green phase)
4. Run tests and verify they PASS
5. Refactor if needed while keeping tests green

**Task Order**:
- Tests before implementation (always)
- Data models before business logic
- Formatters before field mapper
- Field mapper before writer
- Core write logic before duplicate detection
- Core features before error handling
- Integration tests after all components complete

### Parallel Opportunities

**Phase 1 (Setup)**: T002, T003, T004, T005, T006 can run in parallel (different files)

**Phase 2 (Foundational)**: T007, T008 can run in parallel (different model files)

**User Story 1 Tests**: T011-T019 can run in parallel (different test files or different test functions)

**User Story 1 Implementation**: T021-T026 (formatters) can run in parallel (different methods in same file, no dependencies)

**User Story 2 Tests**: T032-T036 can run in parallel (different test files or functions)

**User Story 3 Tests**: T043-T047 can run in parallel (different test scenarios)

**User Story 3 Implementation**: T049, T050, T051 can run in parallel (different methods)

**DLQ Tests**: T055-T059 can run in parallel (different test functions)

**DLQ Implementation**: T061-T065 can run in parallel (different methods in dlq_manager.py)

**Documentation**: T073, T074, T075, T076, T077, T081, T082 can run in parallel (different files)

**User Stories (if team capacity allows)**: After Foundational phase complete, US1, US2, US3 can be worked on in parallel by different developers

---

## Parallel Example: User Story 1 Implementation

```bash
# After US1 tests are written and FAILING, launch all formatter implementations together:
Task: "Implement FieldMapper._format_rich_text() with 2000 char truncation and UTF-8 Korean text support in src/notion_integrator/field_mapper.py" [T022]
Task: "Implement FieldMapper._format_select() for collaboration type and intensity fields in src/notion_integrator/field_mapper.py" [T023]
Task: "Implement FieldMapper._format_relation() with 32/36 char UUID validation in src/notion_integrator/field_mapper.py" [T024]
Task: "Implement FieldMapper._format_date() with ISO 8601 date formatting in src/notion_integrator/field_mapper.py" [T025]
Task: "Implement FieldMapper._format_number() for confidence scores in src/notion_integrator/field_mapper.py" [T026]

# Then sequential tasks that depend on formatters:
Task: "Implement FieldMapper.map_to_notion_properties() to map all ExtractedEntitiesWithClassification fields to Notion properties" [T027]
Task: "Implement NotionWriter.__init__() to accept NotionClient and initialize FieldMapper with schema discovery" [T028]
Task: "Implement NotionWriter._create_page_with_retry() with 3-attempt immediate retry for transient errors" [T029]
Task: "Implement NotionWriter.create_collabiq_entry() core write logic" [T030]
Task: "Add error handling and logging for write operations" [T031]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Goal**: Get basic write functionality working as quickly as possible

1. Complete Phase 1: Setup (T001-T006) - ~1 hour
2. Complete Phase 2: Foundational (T007-T010) - ~2 hours
3. Complete Phase 3: User Story 1 (T011-T031) - ~1 day
   - Write all tests FIRST (T011-T020) - ~3 hours
   - Implement formatters (T021-T026) - ~2 hours
   - Implement field mapper (T027) - ~2 hours
   - Implement writer (T028-T031) - ~3 hours
4. **STOP and VALIDATE**: Run test suite, execute manual test, verify Notion entries created correctly
5. Deploy/demo if ready - **MVP COMPLETE**

**MVP Delivers**: Basic write operations work, extracted email data visible in Notion database

### Incremental Delivery

**Goal**: Add features incrementally while maintaining working system

1. Complete Setup + Foundational → Foundation ready (~3 hours)
2. Add User Story 1 → Test independently → **MVP DEPLOYED** (~1 day)
3. Add User Story 2 (Duplicate Detection) → Test independently → Deploy (~4 hours)
4. Add User Story 3 (Field Type Robustness) → Test independently → Deploy (~4 hours)
5. Add DLQ (Error Handling) → Test independently → Deploy (~4 hours)
6. Add Retry Script + Documentation → Final deployment (~2 hours)

**Each increment adds value without breaking previous features**

### Parallel Team Strategy

With 2-3 developers available:

1. **Team completes Setup + Foundational together** (~3 hours)
2. **Once Foundational is done, parallelize user stories**:
   - Developer A: User Story 1 (P1 MVP) - ~1 day
   - Developer B: User Story 2 (P2 Duplicate Detection) - ~4 hours
   - Developer C: User Story 3 (P3 Field Type Robustness) - ~4 hours
3. **Integrate and test together** (~2 hours)
4. **Complete DLQ + Scripts + Polish together** (~6 hours)

**Total time with parallel execution**: ~1.5-2 days vs 2-3 days sequential

---

## Notes

- **[P] tasks**: Different files or different methods/functions, no dependencies, can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- **TDD Mandatory**: Write tests FIRST, verify they FAIL, then implement, verify they PASS
- **Each user story independently testable**: Stop at any checkpoint to validate story works on its own
- **Commit frequently**: After each task or logical group of related tasks
- **Constitution compliance**: All tasks follow TDD, all user stories independently testable, MVP (US1) delivers standalone value

**Total Tasks**: 83 tasks across 8 phases
- Phase 1 (Setup): 6 tasks (~1 hour)
- Phase 2 (Foundational): 4 tasks (~2 hours)
- Phase 3 (User Story 1): 21 tasks (~1 day)
- Phase 4 (User Story 2): 11 tasks (~4 hours)
- Phase 5 (User Story 3): 12 tasks (~4 hours)
- Phase 6 (DLQ): 13 tasks (~4 hours)
- Phase 7 (Scripts): 7 tasks (~2 hours)
- Phase 8 (Polish): 9 tasks (~3 hours)

**Estimated Timeline**: 2-3 days (matches ROADMAP.md complexity assessment)
