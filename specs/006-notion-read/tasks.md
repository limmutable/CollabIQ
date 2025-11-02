# Tasks: Notion Read Operations

**Input**: Design documents from `/specs/006-notion-read/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per TDD principle (required by constitution). All tests MUST be written FIRST and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (established structure)
- Module: `src/notion_integrator/` (new module for this feature)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [X] T001 Install production dependencies via uv: notion-client, tenacity
- [X] T002 Create src/notion_integrator/ directory structure with __init__.py
- [X] T003 [P] Create cache directory data/notion_cache/ with appropriate permissions
- [X] T004 [P] Add Notion-related environment variables to .env.example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Pydantic models in src/notion_integrator/models.py (NotionDatabase, NotionProperty, NotionRecord, DatabaseSchema, DataCache, RelationshipGraph)
- [X] T006 [P] Implement rate limiter with token bucket algorithm in src/notion_integrator/rate_limiter.py
- [X] T007 [P] Create custom exception hierarchy in src/notion_integrator/exceptions.py (NotionAPIError, CacheError, RelationshipError, DataError)
- [X] T008 Configure logging for notion_integrator module in src/notion_integrator/logging_config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Database Schema Discovery (Priority: P1) 🎯 MVP

**Goal**: Discover complete schema from both Notion databases including all properties, types, and relational fields

**Independent Test**: Trigger schema discovery and verify system correctly identifies all database properties, field types, and relationships. Should return complete DatabaseSchema objects with all property definitions.

### Tests for User Story 1 (TDD - Write FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for schema discovery in tests/contract/test_notion_schema_discovery.py (test against real Notion API or comprehensive fixtures)
- [X] T010 [P] [US1] Unit test for schema parser in tests/unit/test_notion_schema_parser.py (test property type identification, relationship detection)

### Implementation for User Story 1

- [X] T011 [US1] Implement NotionClient wrapper with authentication in src/notion_integrator/client.py (integrate rate limiter, handle API errors)
- [X] T012 [US1] Implement schema discovery in src/notion_integrator/schema.py (fetch database metadata, parse properties, identify relational fields)
- [X] T013 [US1] Add schema caching logic in src/notion_integrator/cache.py (cache operations for DatabaseSchema, TTL validation)
- [X] T014 [US1] Implement schema validation and relationship graph building in src/notion_integrator/schema.py
- [X] T015 [US1] Add logging for schema discovery operations (INFO: schema fetched, WARNING: schema cache expired)

**Checkpoint**: At this point, schema discovery should work independently - can fetch and cache schemas from both databases

---

## Phase 4: User Story 2 - Complete Data Retrieval with Relationships (Priority: P1) 🎯 MVP

**Goal**: Fetch all records from both databases with pagination, resolve relationships, handle circular references

**Independent Test**: Fetch data and verify related fields are properly resolved (e.g., CollabIQ record includes referenced Company data). Should handle pagination automatically and respect configured relationship depth.

### Tests for User Story 2 (TDD - Write FIRST)

- [X] T016 [P] [US2] Contract test for data fetching with pagination in tests/contract/test_notion_data_fetch.py (test pagination, relationship resolution)
- [X] T017 [P] [US2] Integration test for relationship resolution in tests/integration/test_notion_relationships.py (test circular reference detection, depth limiting)

### Implementation for User Story 2

- [X] T018 [US2] Implement pagination handler in src/notion_integrator/fetcher.py (async generator pattern, handle start_cursor)
- [X] T019 [US2] Implement record fetcher in src/notion_integrator/fetcher.py (fetch all pages from database, map properties to NotionRecord model)
- [X] T020 [US2] Implement relationship resolver in src/notion_integrator/fetcher.py (resolve relation properties, track visited pages for circular reference detection, respect max depth)
- [X] T021 [US2] Add data caching logic in src/notion_integrator/cache.py (cache operations for record data, separate from schema cache)
- [X] T022 [US2] Integrate schema discovery with data fetching (use cached schema to parse records correctly)
- [X] T023 [US2] Add logging for data fetch operations (INFO: records fetched, WARNING: circular relationship detected)

**Checkpoint**: At this point, both schema discovery AND data retrieval work - MVP complete (can fetch complete data from Notion)

---

## Phase 5: User Story 3 - Local Data Caching (Priority: P2)

**Goal**: Cache schemas and data locally with TTL, automatic refresh on expiration, atomic writes

**Independent Test**: Verify cache file creation with timestamps, cache hit when data is fresh, cache miss and refresh when expired. Should reduce API calls significantly (80%+ cache hit rate).

### Tests for User Story 3 (TDD - Write FIRST)

- [ ] T024 [P] [US3] Integration test for cache behavior in tests/integration/test_notion_cache.py (test TTL expiration, cache hit/miss, atomic writes)
- [ ] T025 [P] [US3] Unit test for cache validation in tests/unit/test_cache_validation.py (test corrupted cache handling, JSON validation)

### Implementation for User Story 3

- [ ] T026 [US3] Implement cache write operations in src/notion_integrator/cache.py (atomic write with temp file + rename, include timestamps and TTL metadata)
- [ ] T027 [US3] Implement cache read operations in src/notion_integrator/cache.py (validate JSON, check TTL, detect staleness)
- [ ] T028 [US3] Implement cache invalidation logic in src/notion_integrator/cache.py (handle force_refresh, detect schema changes)
- [ ] T029 [US3] Add cache integrity validation in src/notion_integrator/cache.py (validate JSON on read, delete if corrupted, rebuild)
- [ ] T030 [US3] Integrate caching with schema discovery and data fetching (check cache before API calls, write after successful fetch)
- [ ] T031 [US3] Add logging for cache operations (DEBUG: cache hit/miss, WARNING: cache corrupted, INFO: cache refreshed)

**Checkpoint**: Caching should work independently - subsequent calls should use cache, reducing API calls

---

## Phase 6: User Story 4 - API Rate Limit Compliance (Priority: P2)

**Goal**: Respect Notion's 3 req/sec limit, implement exponential backoff on rate limit errors, queue requests

**Independent Test**: Simulate high-volume scenarios and verify request timing never exceeds rate limits. Should handle bursts gracefully and recover from rate limit errors.

### Tests for User Story 4 (TDD - Write FIRST)

- [ ] T032 [P] [US4] Integration test for rate limiting in tests/integration/test_notion_rate_limiting.py (test 3 req/sec enforcement, burst tolerance, queue behavior)
- [ ] T033 [P] [US4] Unit test for rate limiter in tests/unit/test_rate_limiter.py (test token bucket algorithm, timing accuracy)

### Implementation for User Story 4

- [ ] T034 [US4] Enhance rate limiter with request queuing in src/notion_integrator/rate_limiter.py (queue requests when limit approached)
- [ ] T035 [US4] Implement rate limit error handling in src/notion_integrator/client.py (detect 429 errors, trigger exponential backoff via tenacity)
- [ ] T036 [US4] Add rate limit monitoring in src/notion_integrator/rate_limiter.py (track current rate, queue length, expose stats via get_rate_limit_stats())
- [ ] T037 [US4] Integrate rate limiter with all API calls in src/notion_integrator/client.py (wrap all Notion API calls with rate limiter)
- [ ] T038 [US4] Add logging for rate limit events (DEBUG: request queued, WARNING: approaching limit, ERROR: rate limit violation)

**Checkpoint**: Rate limiting should work independently - can make many API calls without violations

---

## Phase 7: User Story 5 - LLM-Ready Data Formatting (Priority: P2)

**Goal**: Format retrieved data for LLM consumption with prominent classification fields (Shinsegae affiliates?, Is Portfolio?), generate JSON + Markdown hybrid output

**Independent Test**: Verify output format matches LLMFormattedData structure, contains all necessary fields, includes both classification flags, generates readable Markdown summary.

### Tests for User Story 5 (TDD - Write FIRST)

- [X] T039 [P] [US5] Unit test for data formatting in tests/unit/test_notion_formatter.py (test JSON structure, Markdown generation, classification field extraction)
- [ ] T040 [P] [US5] Integration test for end-to-end formatting in tests/integration/test_notion_llm_format.py (test complete workflow from fetch to formatted output) - Note: Unit tests cover formatter in isolation; integration test would be nice-to-have

### Implementation for User Story 5

- [X] T041 [P] [US5] Create LLM format models in src/notion_integrator/models.py (LLMFormattedData, CompanyRecord, CompanyClassification, RelatedRecord, FormatMetadata) - Already existed from Phase 2
- [X] T042 [US5] Implement classification field extractor in src/notion_integrator/formatter.py (extract "Shinsegae affiliates?" and "Is Portfolio?" checkboxes, compute collaboration_type_hint)
- [X] T043 [US5] Implement JSON formatter in src/notion_integrator/formatter.py (convert NotionRecord to CompanyRecord, nest related records)
- [X] T044 [US5] Implement Markdown summary generator in src/notion_integrator/formatter.py (create company lists by type, generate collaboration type hints)
- [X] T045 [US5] Implement format_for_llm method in src/notion_integrator/formatter.py (combine JSON + Markdown, populate metadata)
- [X] T046 [US5] Add Unicode handling tests and validation in src/notion_integrator/formatter.py (ensure Korean/Japanese/emoji preserved)
- [X] T047 [US5] Add logging for formatting operations (INFO: formatted N companies, DEBUG: classification counts)

**Checkpoint**: LLM formatting should work independently - can take raw Notion data and produce LLM-ready output

---

## Phase 8: User Story 6 - Error Recovery and Resilience (Priority: P3)

**Goal**: Gracefully handle API failures, network issues, missing data, permission errors with fallback to cache

**Independent Test**: Simulate various failure scenarios (timeout, invalid credentials, API errors) and verify appropriate fallback behavior and error logging.

### Tests for User Story 6 (TDD - Write FIRST)

- [ ] T048 [P] [US6] Integration test for error recovery in tests/integration/test_notion_error_recovery.py (test retry logic, cache fallback, permission errors)
- [ ] T049 [P] [US6] Unit test for error handling in tests/unit/test_notion_error_handling.py (test exception hierarchy, error message clarity)

### Implementation for User Story 6

- [ ] T050 [US6] Implement retry decorators using tenacity in src/notion_integrator/client.py (exponential backoff, max 3 attempts, retry on transient errors only)
- [ ] T051 [US6] Implement cache fallback logic in src/notion_integrator/cache.py (use stale cache when API unreachable, log warnings)
- [ ] T052 [US6] Add graceful degradation for missing data in src/notion_integrator/fetcher.py (handle deleted pages, missing permissions, mark as _deleted or _inaccessible)
- [ ] T053 [US6] Implement comprehensive error logging in src/notion_integrator/client.py (ERROR: API failures with request IDs, WARNING: using stale cache)
- [ ] T054 [US6] Add error recovery tests for edge cases in tests/integration/test_notion_edge_cases.py (empty databases, Unicode edge cases, schema changes)

**Checkpoint**: Error recovery should work independently - system remains stable despite API failures

---

## Phase 9: Integration & High-Level API

**Purpose**: Integrate all user stories into cohesive NotionIntegrator class, provide high-level interface

- [ ] T055 Create NotionIntegrator main class in src/notion_integrator/__init__.py (initialize with config, expose public methods)
- [ ] T056 Implement discover_schema method in NotionIntegrator (integrate US1 components)
- [ ] T057 Implement fetch_all_records method in NotionIntegrator (integrate US2 + US4 components)
- [ ] T058 Implement format_for_llm method in NotionIntegrator (integrate US5 components)
- [ ] T059 Implement get_data high-level method in NotionIntegrator (orchestrate schema discovery + data fetch + formatting, integrate US3 caching, US6 error handling)
- [ ] T060 Implement refresh_cache method in NotionIntegrator (manual cache invalidation for testing/troubleshooting)
- [ ] T061 [P] Add comprehensive integration test in tests/integration/test_notion_integrator_full.py (test complete end-to-end workflow)

---

## Phase 10: CLI Integration

**Purpose**: Expose NotionIntegrator functionality via CLI commands

- [ ] T062 [P] Add notion subcommand group to src/collabiq/__init__.py
- [ ] T063 [P] Implement `collabiq notion fetch` command in src/collabiq/__init__.py (calls get_data, displays summary)
- [ ] T064 [P] Implement `collabiq notion refresh` command in src/collabiq/__init__.py (calls refresh_cache with --force flag)
- [ ] T065 [P] Implement `collabiq notion schema` command in src/collabiq/__init__.py (calls discover_schema, displays schema info)
- [ ] T066 [P] Implement `collabiq notion export` command in src/collabiq/__init__.py (exports formatted data to file)

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final touches

- [ ] T067 [P] Update README.md with Notion integration section and usage examples
- [ ] T068 [P] Validate quickstart.md steps work end-to-end (test all commands and examples)
- [ ] T069 [P] Add type hints and docstrings to all public methods in src/notion_integrator/
- [ ] T070 [P] Run ruff format and ruff check on src/notion_integrator/
- [ ] T071 [P] Run mypy type checking on src/notion_integrator/
- [ ] T072 [P] Update ARCHITECTURE.md with notion_integrator module documentation
- [ ] T073 [P] Add notion_integrator to project dependencies documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User Story 1 (P1) - Schema Discovery: Can start after Foundational
  - User Story 2 (P1) - Data Retrieval: Depends on User Story 1 (needs schema)
  - User Story 3 (P2) - Caching: Can integrate with US1 & US2 in parallel
  - User Story 4 (P2) - Rate Limiting: Can integrate with US1 & US2 in parallel
  - User Story 5 (P2) - LLM Formatting: Depends on US2 (needs data)
  - User Story 6 (P3) - Error Recovery: Can integrate with all above in parallel
- **Integration (Phase 9)**: Depends on all user stories being complete
- **CLI (Phase 10)**: Depends on Integration phase
- **Polish (Phase 11)**: Depends on all above phases

### Critical Path (Sequential)

1. Setup → Foundational → US1 (Schema Discovery) → US2 (Data Retrieval) → US5 (LLM Formatting) → Integration → CLI → Polish

### Parallel Opportunities

**Within Foundational (Phase 2)**:
- T006 (rate limiter), T007 (exceptions), T008 (logging) can all run in parallel

**After US1 & US2 Complete**:
- US3 (Caching), US4 (Rate Limiting), US6 (Error Recovery) can all be integrated in parallel

**Within Each User Story**:
- Tests can be written in parallel
- Models can be created in parallel
- Implementation tasks are mostly sequential due to dependencies

**CLI Phase (Phase 10)**:
- All CLI commands (T062-T066) can be implemented in parallel

**Polish Phase (Phase 11)**:
- All polish tasks (T067-T073) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch foundational tasks together:
Task: "Implement rate limiter with token bucket algorithm in src/notion_integrator/rate_limiter.py"
Task: "Create custom exception hierarchy in src/notion_integrator/exceptions.py"
Task: "Configure logging for notion_integrator module in src/notion_integrator/logging_config.py"
```

## Parallel Example: After US1 & US2 MVP Complete

```bash
# Launch P2 user stories together:
Task: "Add data caching logic in src/notion_integrator/cache.py" (US3)
Task: "Enhance rate limiter with request queuing in src/notion_integrator/rate_limiter.py" (US4)
Task: "Implement retry decorators using tenacity in src/notion_integrator/client.py" (US6)
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Schema Discovery)
4. Complete Phase 4: User Story 2 (Data Retrieval)
5. **STOP and VALIDATE**: Test end-to-end (can discover schemas and fetch data from Notion)
6. This is the MVP - can integrate with LLM workflow

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Schema discovery works
3. Add US2 → Test independently → MVP complete (can fetch data)
4. Add US3 → Test independently → Performance improved (caching)
5. Add US4 → Test independently → Stability improved (rate limiting)
6. Add US5 → Test independently → LLM integration ready (formatted output)
7. Add US6 → Test independently → Resilience improved (error handling)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Schema Discovery)
   - Wait for US1 to complete (US2 depends on it)
3. After US1 complete:
   - Developer A: US2 (Data Retrieval)
   - Developer B: US3 (Caching) - can start integrating with US1
   - Developer C: US4 (Rate Limiting) - can start integrating with US1
4. After US2 complete:
   - Developer D: US5 (LLM Formatting)
   - Developer E: US6 (Error Recovery)
5. Stories complete and integrate independently

---

## Success Metrics per User Story

### User Story 1 - Schema Discovery
- ✅ Can fetch complete schema from both databases
- ✅ Identifies all property types correctly
- ✅ Detects all relational fields
- ✅ Completes in <10 seconds

### User Story 2 - Data Retrieval
- ✅ Fetches all records with pagination
- ✅ Resolves relationships correctly (95%+ success rate)
- ✅ Handles circular references without infinite loops
- ✅ Completes in <60 seconds for 500 records

### User Story 3 - Caching
- ✅ Creates cache files with timestamps
- ✅ Uses cache when fresh (TTL not expired)
- ✅ Refreshes cache when stale
- ✅ Achieves 80%+ cache hit rate

### User Story 4 - Rate Limiting
- ✅ Never exceeds 3 req/sec
- ✅ Handles rate limit errors gracefully
- ✅ Zero rate limit violations over 24 hours

### User Story 5 - LLM Formatting
- ✅ Produces valid JSON matching contract
- ✅ Generates readable Markdown summary
- ✅ Both classification fields present for all companies
- ✅ Handles Unicode correctly (Korean/Japanese/emoji)

### User Story 6 - Error Recovery
- ✅ Retries transient errors (max 3 attempts)
- ✅ Falls back to cache when API unreachable
- ✅ Logs errors with actionable messages
- ✅ System remains stable despite failures

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD REQUIRED**: Write tests FIRST, ensure they FAIL before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 & US2 together form the MVP (complete Notion data retrieval)
- US3-US6 are enhancements that improve performance, stability, and usability

---

## Total Task Count: 73 tasks

- Setup: 4 tasks
- Foundational: 4 tasks
- User Story 1 (P1): 7 tasks (2 tests + 5 implementation)
- User Story 2 (P1): 8 tasks (2 tests + 6 implementation)
- User Story 3 (P2): 8 tasks (2 tests + 6 implementation)
- User Story 4 (P2): 7 tasks (2 tests + 5 implementation)
- User Story 5 (P2): 9 tasks (2 tests + 7 implementation)
- User Story 6 (P3): 7 tasks (2 tests + 5 implementation)
- Integration: 7 tasks
- CLI: 5 tasks
- Polish: 7 tasks

**Test Count**: 12 test files (contract, integration, unit tests for all user stories)
**Parallel Opportunities**: 23 tasks marked [P] can run in parallel within their phases
**MVP Scope**: Phases 1-4 (Setup + Foundational + US1 + US2) = 23 tasks for MVP
