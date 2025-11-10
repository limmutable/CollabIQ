# Implementation Tasks: Enhanced Notion Field Mapping

**Feature**: 014-enhanced-field-mapping
**Branch**: `014-enhanced-field-mapping`
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

## Task Summary

| Phase | Story | Task Count | Parallel | MVP |
|-------|-------|------------|----------|-----|
| Setup | - | 2 | 2 | ✅ |
| Foundational | - | 3 | 2 | ✅ |
| User Story 1 (P1) | Company Fuzzy Matching | 8 | 4 | ✅ MVP |
| User Story 2 (P1) | Auto-Create Companies | 5 | 3 | ✅ MVP |
| User Story 3 (P2) | Person Name Matching | 6 | 3 | - |
| User Story 4 (P3) | CLI Testing Commands | 4 | 3 | - |
| User Story 5 (P4) | Algorithm Evaluation | 6 | 3 | - (Optional) |
| Polish | Cross-cutting | 3 | 2 | - |
| **Total** | **5 stories** | **37 tasks** | **22 parallel** | **18 MVP** |

**MVP Scope**: User Stories 1+2 (Company matching with auto-creation) = 18 tasks

---

## Dependencies & Execution Order

### Story Completion Order

```
Setup (Phase 1)
  ↓
Foundational (Phase 2) - Required for all user stories
  ↓
├─→ [US1] Company Fuzzy Matching (P1) ← MVP Start
│   ↓
├─→ [US2] Auto-Create Companies (P1) ← depends on US1 interface, MVP Complete
│   ↓
├─→ [US3] Person Name Matching (P2) ← independent of US1/US2
│   ↓
├─→ [US4] CLI Testing Commands (P3) ← depends on US1, US2, US3
│   ↓
└─→ [US5] Algorithm Evaluation (P4 - OPTIONAL) ← depends on US1/US2
    ↓
Polish (Final Phase)
```

### Parallel Execution Opportunities

- **Setup Phase**: Both tasks can run in parallel
- **Foundational Phase**: T003 and T004 can run in parallel (different files)
- **User Story 1**: T006-T009 (tests) can run in parallel, then T010-T013 (implementation) in parallel
- **User Story 2**: T015-T017 (tests) can run in parallel
- **User Story 3**: T020-T022 (tests) can run in parallel, then T023-T025 (implementation) in parallel
- **User Story 4**: T027-T029 (commands) can run in parallel
- **User Story 5**: T031-T033 (evaluation infrastructure) can run in parallel

---

## Phase 1: Setup

**Goal**: Initialize models and configuration for fuzzy matching feature

**Tasks**:

- [ ] T001 [P] Create CompanyMatch Pydantic model in src/models/matching.py with fields: page_id, company_name, similarity_score, match_type, confidence_level, was_created, match_method
- [ ] T002 [P] Create PersonMatch Pydantic model in src/models/matching.py with fields: user_id, user_name, similarity_score, match_type, confidence_level, is_ambiguous, alternative_matches

**Validation**: Models import successfully and pass type checking

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Create shared infrastructure needed by all user stories

**Tasks**:

- [ ] T003 [P] Create CompanyMatcher interface (abstract base class) in src/notion_integrator/fuzzy_matcher.py defining match() method signature
- [ ] T004 [P] Create PersonMatcher interface (abstract base class) in src/notion_integrator/person_matcher.py defining match() and list_users() method signatures
- [ ] T005 Create user list cache structure in data/notion_cache/users_list.json with schema: {version, cached_at, ttl_seconds, users[]}

**Validation**: Interfaces are importable, cache directory exists

---

## Phase 3: User Story 1 - Company Name Fuzzy Matching (Priority: P1)

**Story Goal**: Enable fuzzy matching of extracted company names to Companies database using Jaro-Winkler algorithm (rapidfuzz)

**Independent Test Criteria**:
- Given test company names with variations (e.g., "웨이크(산스)" → "웨이크"), fuzzy matcher returns correct page_id with similarity ≥0.85
- Achieves ≥90% match accuracy on 20+ test cases (per SC-001)
- Completes matching in <2 seconds for 1000+ companies (per SC-007)

**Tasks**:

### Tests (TDD - Write First)

- [ ] T006 [P] [US1] Write contract test for FuzzyCompanyMatcher.match() in tests/contract/test_fuzzy_company_matcher.py verifying exact match returns similarity 1.0
- [ ] T007 [P] [US1] Write contract test for FuzzyCompanyMatcher.match() in tests/contract/test_fuzzy_company_matcher.py verifying fuzzy match (≥0.85) returns valid page_id
- [ ] T008 [P] [US1] Write unit test for Jaro-Winkler similarity calculation in tests/unit/test_fuzzy_matching_algorithm.py with Korean text cases (워크 vs 웍, parentheticals, spacing)
- [ ] T009 [P] [US1] Write unit test for name normalization (trim whitespace) in tests/unit/test_korean_name_normalization.py

### Implementation

- [ ] T010 [P] [US1] Implement RapidfuzzMatcher class in src/notion_integrator/fuzzy_matcher.py inheriting from CompanyMatcher interface, using rapidfuzz.fuzz.ratio()
- [ ] T011 [P] [US1] Implement exact match search in RapidfuzzMatcher._find_exact_match() method checking case-sensitive equality
- [ ] T012 [P] [US1] Implement fuzzy match search in RapidfuzzMatcher._find_fuzzy_match() method computing similarity for all companies and returning best match if ≥0.85
- [ ] T013 [US1] Implement match() method orchestration in RapidfuzzMatcher: exact match → fuzzy match → return CompanyMatch with confidence level based on similarity score

**Story Checkpoint**:
- [ ] [US1] Run contract tests: `pytest tests/contract/test_fuzzy_company_matcher.py -v`
- [ ] [US1] Run unit tests: `pytest tests/unit/test_fuzzy_matching_algorithm.py tests/unit/test_korean_name_normalization.py -v`
- [ ] [US1] Verify 90% accuracy on test dataset (SC-001)
- [ ] [US1] Verify <2 second latency for 1000 companies (SC-007)

---

## Phase 4: User Story 2 - Auto-Create Missing Companies (Priority: P1)

**Story Goal**: Automatically create new company entries in Companies database when no fuzzy match exists (similarity < 0.85)

**Independent Test Criteria**:
- Given company name not in database (e.g., "완전히새로운회사123"), system creates new entry and returns valid page_id
- Relation field is successfully populated with new page_id
- Subsequent emails with same company reuse existing entry (no duplicates per FR-014)

**Tasks**:

### Tests (TDD - Write First)

- [ ] T015 [P] [US2] Write contract test for NotionWriter.create_company() in tests/contract/test_fuzzy_company_matcher.py verifying new entry creation returns valid page_id
- [ ] T016 [P] [US2] Write integration test for auto-creation workflow in tests/integration/test_company_autocreate.py verifying no match (< 0.85) triggers creation
- [ ] T017 [P] [US2] Write integration test for duplicate prevention in tests/integration/test_company_autocreate.py verifying exact match check prevents duplicates

### Implementation

- [ ] T018 [US2] Extend RapidfuzzMatcher.match() to call NotionWriter.create_company() when similarity < 0.85 and return CompanyMatch with was_created=True
- [ ] T019 [US2] Implement NotionWriter.create_company(company_name) method in src/notion_integrator/writer.py creating Companies database entry with title property

**Story Checkpoint**:
- [ ] [US2] Run integration tests: `pytest tests/integration/test_company_autocreate.py -v`
- [ ] [US2] Verify auto-created companies are properly formatted (SC-003)
- [ ] [US2] Verify duplicate prevention works correctly (FR-014)
- [ ] [US2] End-to-end test: Process email with new company → verify relation field populated

---

## Phase 5: User Story 3 - Person Name Matching (Priority: P2)

**Story Goal**: Match extracted person names to Notion workspace users and populate 담당자 people field with user UUIDs

**Independent Test Criteria**:
- Given person name "김철수", matcher returns correct user UUID when Notion user exists
- Achieves ≥85% match rate on test dataset (per SC-002)
- No false positives (low confidence matches are logged but not used if < 0.70)
- Ambiguous matches (multiple similar users) are detected and logged

**Tasks**:

### Tests (TDD - Write First)

- [ ] T020 [P] [US3] Write contract test for PersonMatcher.match() in tests/contract/test_person_matcher.py verifying exact match returns user UUID with similarity 1.0
- [ ] T021 [P] [US3] Write contract test for PersonMatcher.list_users() in tests/contract/test_person_matcher.py verifying all workspace users are returned with UUIDs
- [ ] T022 [P] [US3] Write integration test for ambiguity detection in tests/integration/test_person_matching_integration.py verifying is_ambiguous=True when top 2 scores differ by <0.10

### Implementation

- [ ] T023 [P] [US3] Implement NotionPersonMatcher class in src/notion_integrator/person_matcher.py inheriting from PersonMatcher interface
- [ ] T024 [P] [US3] Implement list_users() method in NotionPersonMatcher using NotionClient.users.list() with caching (24h TTL) to data/notion_cache/users_list.json
- [ ] T025 [US3] Implement match() method in NotionPersonMatcher: load cached users → compute similarity → detect ambiguity (difference < 0.10) → return PersonMatch with user_id if ≥0.70 or None

**Story Checkpoint**:
- [ ] [US3] Run contract tests: `pytest tests/contract/test_person_matcher.py -v`
- [ ] [US3] Run integration tests: `pytest tests/integration/test_person_matching_integration.py -v`
- [ ] [US3] Verify 85% match rate on test dataset (SC-002)
- [ ] [US3] Verify low-confidence matches (0.70-0.85) are logged (SC-004)
- [ ] [US3] Verify ambiguous matches are detected and logged (FR-012)

---

## Phase 6: User Story 4 - CLI Testing Commands (Priority: P3)

**Story Goal**: Provide CLI commands for administrators to test company/person matching without running full pipeline

**Independent Test Criteria**:
- `collabiq notion match-company` displays best match, similarity score, and page_id
- `collabiq notion match-person` displays matched user(s), UUIDs, and similarity scores
- `collabiq notion list-users` displays all workspace users with UUIDs
- Commands respond in <1 second (per SC-008)
- `--dry-run` flag simulates creation without writing to Notion

**Tasks**:

- [ ] T027 [P] [US4] Implement match-company command in src/collabiq/commands/notion.py using @app.command decorator with name, --dry-run, --threshold arguments
- [ ] T028 [P] [US4] Implement match-person command in src/collabiq/commands/notion.py using @app.command decorator with name, --show-alternatives arguments
- [ ] T029 [P] [US4] Implement list-users command in src/collabiq/commands/notion.py using @app.command decorator with --refresh, --format arguments (table/json)
- [ ] T030 [US4] Add rich formatting to CLI output using tables for match results, color-coded confidence levels (high=green, medium=yellow, low=red)

**Story Checkpoint**:
- [ ] [US4] Test match-company command: `collabiq notion match-company "웨이크(산스)"`
- [ ] [US4] Test match-person command: `collabiq notion match-person "김철수"`
- [ ] [US4] Test list-users command: `collabiq notion list-users`
- [ ] [US4] Verify commands respond in <1 second (SC-008)
- [ ] [US4] Verify --dry-run flag works correctly (FR-018)

---

## Phase 7: User Story 5 - Algorithm Evaluation (Priority: P4 - OPTIONAL)

**Story Goal**: Generate comparative evaluation report for rapidfuzz vs LLM vs hybrid approaches to inform production optimization decisions

**Independent Test Criteria**:
- Evaluation runs on 20+ emails with ground truth labels
- Report shows accuracy, precision, recall, F1, latency, cost for each approach
- Report recommends optimal algorithm based on ≥90% accuracy threshold
- Evaluation completes without errors

**Tasks**:

### Evaluation Infrastructure

- [ ] T031 [P] [US5] Create ground truth dataset in tests/fixtures/evaluation/ground_truth.json with 20+ email test cases: {extracted_name, correct_match, match_type}
- [ ] T032 [P] [US5] Implement LLMMatcher class in src/notion_integrator/fuzzy_matcher.py using llm_orchestrator for semantic matching with prompt template for company ranking
- [ ] T033 [P] [US5] Implement HybridMatcher class in src/notion_integrator/fuzzy_matcher.py: rapidfuzz first (≥0.85) → LLM fallback (≥0.70) → auto-create

### Evaluation Tests

- [ ] T034 [US5] Implement evaluate_matcher() function in tests/evaluation/test_matching_comparison.py computing accuracy, precision, recall, F1, latency, cost metrics
- [ ] T035 [US5] Write comparative evaluation test in tests/evaluation/test_matching_comparison.py running RapidfuzzMatcher, LLMMatcher, HybridMatcher on ground truth dataset
- [ ] T036 [US5] Implement generate_comparison_report() function in tests/evaluation/test_matching_comparison.py creating evaluation-report.md with metrics table and recommendations

**Story Checkpoint**:
- [ ] [US5] Run evaluation: `pytest tests/evaluation/test_matching_comparison.py -v`
- [ ] [US5] Review report: `cat specs/014-enhanced-field-mapping/evaluation-report.md`
- [ ] [US5] Verify all approaches meet 90% accuracy threshold (per SC-001)
- [ ] [US5] Identify failure cases for each approach

---

## Phase 8: Integration & Polish

**Goal**: Integrate fuzzy matching into FieldMapper and finalize cross-cutting concerns

**Tasks**:

- [ ] T037 [P] Enhance FieldMapper in src/notion_integrator/field_mapper.py: inject RapidfuzzMatcher and NotionPersonMatcher, call matchers for 스타트업명, 협력기관, 담당자 fields before Notion write
- [ ] T038 [P] Add logging for low-confidence matches in FieldMapper: log matches with 0.70-0.85 similarity for manual review with match details (FR-012, SC-004)
- [ ] T039 Run E2E test with 20+ real emails verifying ≥90% field population rate (SC-006): `collabiq test e2e --mode production --count 20`

**Final Validation**:
- [ ] All contract tests pass: `pytest tests/contract/ -v`
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] E2E test shows ≥90% company match rate (SC-001)
- [ ] E2E test shows ≥85% person match rate (SC-002)
- [ ] E2E test shows ≥90% field population rate (SC-006)
- [ ] Performance test: Fuzzy matching <2s for 1000 companies (SC-007)
- [ ] CLI commands respond in <1s (SC-008)

---

## Implementation Strategy

### MVP First (User Stories 1+2)

**Recommended approach**: Implement US1 and US2 completely before moving to other stories.

**Why**: US1+US2 together form a complete, independently valuable feature (company field population with auto-creation). This is the highest priority requirement and delivers immediate business value.

**MVP Execution Order**:
1. Phase 1: Setup (T001-T002) - 2 tasks
2. Phase 2: Foundational (T003-T005) - 3 tasks
3. Phase 3: US1 (T006-T013) - 8 tasks
4. Phase 4: US2 (T015-T019) - 5 tasks

**MVP Validation**: After completing Phase 4, run integration test to verify company fields are populated correctly.

### Incremental Story Delivery

After MVP:
- **Phase 5 (US3)**: Person matching - independent of company matching, can be implemented anytime
- **Phase 6 (US4)**: CLI commands - depends on US1/US2/US3 implementations
- **Phase 7 (US5)**: Algorithm evaluation - optional, only implement if needed for production optimization

### Parallel Execution Examples

**Setup Phase** (run in parallel):
```bash
# Terminal 1
Task T001: Create CompanyMatch model

# Terminal 2 (parallel)
Task T002: Create PersonMatch model
```

**User Story 1 Tests** (run in parallel after foundational):
```bash
# Terminal 1
Task T006: Contract test - exact match

# Terminal 2 (parallel)
Task T007: Contract test - fuzzy match

# Terminal 3 (parallel)
Task T008: Unit test - Jaro-Winkler

# Terminal 4 (parallel)
Task T009: Unit test - normalization
```

**User Story 1 Implementation** (run in parallel after tests pass):
```bash
# Terminal 1
Task T010: RapidfuzzMatcher class

# Terminal 2 (parallel)
Task T011: Exact match method

# Terminal 3 (parallel)
Task T012: Fuzzy match method
```

---

## Risk Mitigation

### Performance Risks

**Risk**: Fuzzy matching too slow for 1000+ companies
**Mitigation**: Implemented in T012 with performance test in validation
**Fallback**: Optimize with BK-tree indexing if needed (not in current scope)

### Accuracy Risks

**Risk**: 90% match rate not achievable with rapidfuzz alone
**Mitigation**: US5 (P4) provides path to LLM/hybrid if needed
**Validation**: SC-001 verified in final E2E test

### API Rate Limit Risks

**Risk**: Notion API rate limits hit during company creation
**Mitigation**: Reuse existing retry logic from Phase 010 (error_handling module)
**Constraint**: Documented in plan.md (3 req/s limit)

---

**Document Status**: ✅ READY FOR IMPLEMENTATION
**Next Step**: Begin Phase 1 (Setup) tasks T001-T002
**MVP Target**: Complete Phases 1-4 (18 tasks) for company field population

