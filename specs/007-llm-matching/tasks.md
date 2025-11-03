# Implementation Tasks: LLM-Based Company Matching

**Feature**: Phase 2b - LLM-Based Company Matching
**Branch**: `007-llm-matching`
**Generated**: 2025-11-02

---

## Task Summary

**Total Tasks**: 30
**MVP Scope**: US1 + US2 (P1 stories - 15 tasks)
**Test Strategy**: TDD required (contract tests → integration tests → implementation)

### Tasks by User Story

- Setup: 3 tasks (T001-T003)
- Foundational: 2 tasks (T004-T005)
- **US1 (P1)**: 7 tasks (T006-T012) - Match Primary Startup
- **US2 (P1)**: 8 tasks (T013-T020) - Match Beneficiary Company
- US3 (P2): 4 tasks (T021-T024) - Handle Name Variations
- US4 (P2): 3 tasks (T025-T027) - Handle No-Match Scenarios
- US5 (P3): 2 tasks (T028-T029) - LLM Context Formatting
- Polish: 1 task (T030)

---

## Phase 1: Setup

**Goal**: Initialize project structure and dependencies for Phase 2b extension

- [x] T001 Verify Phase 1b and Phase 2a dependencies are available (GeminiAdapter, NotionIntegrator)
- [x] T002 [P] Create test fixture directory for mocked Notion data at tests/fixtures/mock_notion_data.json
- [x] T003 [P] Create contract test file skeleton at tests/contract/test_gemini_adapter_matching_contract.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Extend core data model to support company matching (required for all user stories)

**Independent Test**: Pydantic validation passes for ExtractedEntities with new fields

- [x] T004 Extend ExtractedEntities model in src/llm_provider/types.py with 4 new optional fields (matched_company_id, matched_partner_id, startup_match_confidence, partner_match_confidence)
- [x] T005 Add Pydantic validators for confidence range (0.0-1.0) and Notion page ID format (32/36 chars) in src/llm_provider/types.py

**Checkpoint**: ✅ ExtractedEntities schema extended, backward compatible with Phase 1b, Pydantic validation passes

---

## Phase 3: User Story 1 - Match Primary Startup Company (Priority: P1)

**Goal**: Match extracted startup names to Notion Companies database entries with high confidence (≥0.90)

**Why P1**: Core MVP functionality - every email mentions at least one startup. Without this, matching cannot function.

**Independent Test**:
- Given sample-001.txt "브레이크앤컴퍼니 x 신세계 PoC"
- When GeminiAdapter.extract_entities() is called with company_context
- Then matched_company_id is populated with correct Notion ID
- And startup_match_confidence ≥ 0.90

### Tests (TDD Red Phase)

- [x] T006 [P] [US1] Write contract test for GeminiAdapter.extract_entities() accepting optional company_context parameter in tests/contract/test_gemini_adapter_matching_contract.py
- [x] T007 [P] [US1] Write contract test for backward compatibility (company_context=None returns None for matched fields) in tests/contract/test_gemini_adapter_matching_contract.py
- [x] T008 [P] [US1] Write integration test for exact startup matching using sample-001.txt in tests/integration/test_company_matching_integration.py

### Implementation

- [x] T009 [US1] Update GeminiAdapter.__init__() to accept optional company_context parameter in src/llm_adapters/gemini_adapter.py
- [x] T010 [US1] Modify extraction prompt template to include company list context section in src/llm_adapters/prompts/extraction_prompt.txt
- [x] T011 [US1] Update GeminiAdapter.extract_entities() to inject company_context into prompt and parse matched_company_id from Gemini response in src/llm_adapters/gemini_adapter.py
- [x] T012 [US1] Add confidence threshold logic (≥0.90 = auto-accept, <0.70 = return null) in src/llm_adapters/gemini_adapter.py

**Checkpoint**: ✅ US1 complete - Primary startup matching works with confidence scores, tests pass (red → green)

---

## Phase 4: User Story 2 - Match Beneficiary Company (Priority: P1)

**Goal**: Match partner organizations (SSG affiliates OR portfolio companies) and determine collaboration type

**Why P1**: Equally critical as US1 - both companies must be matched for feature to deliver value. Determines collaboration classification ([A] vs [C]).

**Independent Test**:
- Given sample-004.txt "NXN Labs - SI GenAI 이미지생성 파일럿"
- When GeminiAdapter.extract_entities() is called with company_context
- Then matched_partner_id is populated with correct Notion ID
- And partner_match_confidence ≥ 0.90
- And partner_classification is identified (SSG Affiliate or Portfolio)

### Tests (TDD Red Phase)

- [x] T013 [P] [US2] Write contract test for matched_partner_id field population in tests/contract/test_gemini_adapter_matching_contract.py
- [x] T014 [P] [US2] Write integration test for SSG affiliate matching using sample-004.txt (신세계인터내셔널) in tests/integration/test_company_matching_integration.py
- [x] T015 [P] [US2] Write integration test for Portfolio×Portfolio matching using sample-006.txt (플록스 × 스마트푸드네트워크) in tests/integration/test_company_matching_integration.py
- [x] T016 [P] [US2] Write integration test for English name matching using english_002.txt ("Shinsegae International") in tests/integration/test_company_matching_integration.py

### Implementation

- [x] T017 [US2] Extend prompt template to instruct LLM to match partner_org in addition to startup_name in src/llm_adapters/prompts/extraction_prompt.txt
- [x] T018 [US2] Update Gemini response schema to include matched_partner_id and partner_match_confidence fields in src/llm_adapters/gemini_adapter.py
- [x] T019 [US2] Add logic to extract partner classification (SSG Affiliate vs Portfolio) from Notion company context in src/llm_adapters/gemini_adapter.py
- [x] T020 [US2] Apply confidence threshold to partner matches (same logic as startup matching) in src/llm_adapters/gemini_adapter.py

**Checkpoint**: ✅ US2 complete - Beneficiary matching works for both SSG and Portfolio, classification detected, tests pass

---

## Phase 5: User Story 3 - Handle Company Name Variations (Priority: P2)

**Goal**: Match abbreviations, typos, and alternate spellings with moderate confidence (0.70-0.89)

**Why P2**: Important for real-world usage but not blocking MVP. Reduces manual review queue size.

**Independent Test**:
- Given test email "SSG푸드와 협업 진행"
- When GeminiAdapter.extract_entities() is called
- Then matched_partner_id matches "신세계푸드"
- And partner_match_confidence is between 0.75-0.89

### Tests (TDD Red Phase)

- [x] T021 [P] [US3] Write integration test for abbreviation matching ("SSG푸드" → "신세계푸드") in tests/integration/test_company_matching_integration.py
- [x] T022 [P] [US3] Write integration test for typo tolerance ("브레이크언컴퍼니" → "브레이크앤컴퍼니") in tests/integration/test_company_matching_integration.py

### Implementation

- [x] T023 [US3] Enhance prompt template with fuzzy matching guidance (abbreviations, typos, context words) in src/llm_adapters/prompts/extraction_prompt.txt
- [x] T024 [US3] Add semantic similarity confidence calibration (0.70-0.89 range for fuzzy matches) in src/llm_adapters/gemini_adapter.py

**Checkpoint**: ✅ US3 complete - Fuzzy matching handles common variations, moderate confidence scores, tests pass

---

## Phase 6: User Story 4 - Handle No-Match Scenarios (Priority: P2)

**Goal**: Return null matched_company_id with low confidence (<0.70) for unknown companies

**Why P2**: Prevents false positives, improves data quality, but MVP can function without this.

**Independent Test**:
- Given email "신생스타트업과 초기 미팅" (unknown company)
- When GeminiAdapter.extract_entities() is called
- Then matched_company_id is null
- And startup_match_confidence < 0.70

### Tests (TDD Red Phase)

- [x] T025 [P] [US4] Write integration test for unknown company scenario (no match in database) in tests/integration/test_company_matching_integration.py
- [x] T026 [P] [US4] Write integration test for ambiguous company name (multiple partial matches) in tests/integration/test_company_matching_integration.py

### Implementation

- [x] T027 [US4] Add no-match handling logic (confidence <0.70 returns null ID, logs for manual review) in src/llm_adapters/gemini_adapter.py

**Checkpoint**: ✅ US4 complete - No-match scenarios handled gracefully, null IDs with low confidence, tests pass

---

## Phase 7: User Story 5 - Provide LLM-Ready Company Context (Priority: P3)

**Goal**: Optimize company list formatting for LLM prompt injection (≤500 tokens for 10 companies)

**Why P3**: Nice-to-have optimization - Phase 2a already provides basic formatting. Improves semantic understanding.

**Independent Test**:
- Given 10 test companies (6 portfolio + 4 SSG)
- When company context is formatted for LLM
- Then output ≤500 tokens
- And includes all company names grouped by classification

### Implementation

- [ ] T028 [P] [US5] Create helper function to format company context with token budget enforcement (≤2000 tokens) in src/llm_adapters/gemini_adapter.py or new module
- [ ] T029 [P] [US5] Add token counting logic and truncation strategy (prioritize active/portfolio over archived) if needed in same module

**Checkpoint**: ✅ US5 complete - LLM context formatting optimized, token budget respected

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Final validation, documentation, and cleanup

- [x] T030 Run accuracy validation on 10-email test dataset, measure against SC-001 (≥85% accuracy) and SC-002 (confidence calibration), document results in specs/007-llm-matching/VALIDATION_RESULTS.md

**Checkpoint**: ✅ Feature complete - All 5 user stories delivered, success criteria validated, ready for merge

---

## Dependencies & Execution Order

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
    ┌─────────────────┴─────────────────┐
    ▼                                   ▼
Phase 3 (US1)                      Phase 4 (US2)
Match Primary                     Match Beneficiary
    │                                   │
    └─────────────┬─────────────────────┘
                  ▼
              MVP COMPLETE ✅
                  │
                  ├──────────────┬──────────────┐
                  ▼              ▼              ▼
            Phase 5 (US3)   Phase 6 (US4)   Phase 7 (US5)
            Variations      No-Match         Context Format
                  │              │              │
                  └──────────────┴──────────────┘
                                 ▼
                            Phase 8 (Polish)
```

**Key Insights**:
- **US1 and US2 are independent**: Can be implemented in parallel by different developers
- **US3, US4, US5 depend on US1+US2**: But are independent of each other (can be parallelized)
- **MVP = US1 + US2**: Delivers complete matching for both companies, enables Phase 2c

---

## Parallel Execution Examples

### Example 1: MVP Phase (US1 + US2 in parallel)

**Developer A** (US1 - Primary Startup):
```bash
# Run US1 tests
pytest tests/contract/test_gemini_adapter_matching_contract.py::test_startup_matching -v
pytest tests/integration/test_company_matching_integration.py::test_exact_startup_match -v

# Implement US1
# T009-T012: Modify GeminiAdapter for startup matching
```

**Developer B** (US2 - Beneficiary Company):
```bash
# Run US2 tests (in parallel with Dev A)
pytest tests/contract/test_gemini_adapter_matching_contract.py::test_partner_matching -v
pytest tests/integration/test_company_matching_integration.py::test_ssg_affiliate_match -v

# Implement US2
# T017-T020: Extend for partner matching
```

**No conflicts**: US1 and US2 modify different sections of the same files but can merge cleanly.

---

### Example 2: Enhancement Phase (US3, US4, US5 in parallel)

After MVP complete, three developers can work in parallel:

**Developer A** (US3):
```bash
pytest tests/integration/test_company_matching_integration.py::test_abbreviation_match -v
# T023-T024: Fuzzy matching enhancements
```

**Developer B** (US4):
```bash
pytest tests/integration/test_company_matching_integration.py::test_unknown_company -v
# T027: No-match handling
```

**Developer C** (US5):
```bash
# T028-T029: Context formatting optimization (new module, no conflicts)
```

---

## Implementation Strategy

### Recommended Approach: Incremental Delivery

**Week 1**: MVP (US1 + US2)
- Days 1-2: Setup + Foundational (T001-T005)
- Days 3-4: US1 tests + implementation (T006-T012)
- Days 5-6: US2 tests + implementation (T013-T020)
- Day 7: Integration testing, merge to main

**Result**: ✅ Core matching works, ready for Phase 2c

**Week 2**: Enhancements (US3 + US4 + US5)
- Days 1-2: US3 fuzzy matching (T021-T024)
- Days 2-3: US4 no-match handling (T025-T027)
- Days 3-4: US5 context optimization (T028-T029)
- Day 5: Polish + validation (T030)

**Result**: ✅ Production-ready with ≥85% accuracy

---

## Success Criteria Mapping

| Success Criterion | Validation Task | Target |
|-------------------|----------------|--------|
| SC-001: ≥85% accuracy | T030 | Measure on 10 test emails |
| SC-002: Confidence calibration | T030 | ≥95% precision @ ≥0.90 |
| SC-003: ≤3s performance | T030 | Measure end-to-end latency |
| SC-004: ≥90% no-match precision | T026, T027, T030 | Validate false positive rate |
| SC-005: ≥80% fuzzy matching | T021-T024, T030 | Test abbreviations/typos |

---

## Testing Strategy

**Test-Driven Development (TDD) enforced per Constitution III**

### Test Execution Order (Red → Green → Refactor)

1. **Write failing tests first** (tasks marked with [P] in test phase)
2. **Run tests** - should FAIL (red phase)
3. **Implement minimum code** to pass tests (green phase)
4. **Refactor** for clarity (refactor phase)
5. **Re-run tests** - should PASS

### Test Types

**Contract Tests** (T006-T007, T013, etc.):
- Verify GeminiAdapter interface compliance
- Fast execution (<1s per test)
- No external API calls (mocked)

**Integration Tests** (T008, T014-T016, T021-T022, T025-T026):
- Real Gemini API calls (requires GEMINI_API_KEY)
- Mocked Notion data (tests/fixtures/mock_notion_data.json)
- Slower execution (~2-3s per test)

**Validation Tests** (T030):
- End-to-end on 10-email test dataset
- Measures accuracy against ground truth
- Generates validation report

---

## File Path Reference

**Modified Files**:
- `src/llm_provider/types.py` - ExtractedEntities model extension (T004-T005)
- `src/llm_adapters/gemini_adapter.py` - Main matching logic (T009-T012, T017-T020, T023-T024, T027-T029)
- `src/llm_adapters/prompts/extraction_prompt.txt` - Prompt template updates (T010, T017, T023)

**New Files**:
- `tests/contract/test_gemini_adapter_matching_contract.py` - Contract tests (T003, T006-T007, T013)
- `tests/integration/test_company_matching_integration.py` - Integration tests (T008, T014-T016, T021-T022, T025-T026)
- `tests/fixtures/mock_notion_data.json` - Test fixture (T002)
- `specs/007-llm-matching/VALIDATION_RESULTS.md` - Accuracy report (T030)

**Reused Files** (no modifications):
- `src/notion_integrator/integrator.py` - Fetch company data (Phase 2a)
- `src/notion_integrator/formatter.py` - Format for LLM (Phase 2a)
- `src/config/settings.py` - Configuration (existing)

---

**Tasks ready for execution** | MVP scope: T001-T020 (US1+US2) | Full feature: T001-T030 (all 5 user stories)
