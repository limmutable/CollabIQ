# Tasks: Multi-LLM Provider Support

**Input**: Design documents from `/specs/012-multi-llm/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Contract tests are included as per TDD requirements in spec.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and directory structure

- [ ] T001 Add anthropic and openai SDK dependencies to pyproject.toml
- [ ] T002 Create src/llm_orchestrator/ directory structure (strategies/, __init__.py)
- [ ] T003 Create data/llm_health/ directory for health and cost metrics persistence
- [ ] T004 Create test directories tests/contract/, tests/integration/, tests/unit/ for LLM providers

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and shared utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create ProviderConfig Pydantic model in src/llm_orchestrator/models.py
- [ ] T006 [P] Create ProviderHealthMetrics Pydantic model in src/llm_orchestrator/models.py
- [ ] T007 [P] Create OrchestrationStrategyConfig Pydantic model in src/llm_orchestrator/models.py
- [ ] T008 [P] Create CostMetricsSummary Pydantic model in src/llm_orchestrator/models.py
- [ ] T009 [P] Create ExtractedEntitiesWithMetadata Pydantic model extending ExtractedEntities in src/llm_provider/types.py
- [ ] T010 Create orchestration exceptions (AllProvidersFailedError, NoHealthyProvidersError, OrchestrationTimeoutError, InvalidStrategyError) in src/llm_orchestrator/exceptions.py
- [ ] T011 Create configuration loader for provider_config.json in src/llm_orchestrator/config.py
- [ ] T012 Create configuration loader for orchestration_config.json in src/llm_orchestrator/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Automatic Failover on Provider Failure (Priority: P1) 🎯 MVP

**Goal**: System continues processing all incoming emails when the primary LLM provider is unavailable, with failover completing in under 2 seconds

**Independent Test**: Configure two providers (Gemini + Claude), send test emails, simulate Gemini API failure, verify emails continue processing successfully using Claude within 2 seconds

**Success Criteria**:
- SC-001: System continues processing when primary provider unavailable ✅
- SC-002: Failover completes in <2 seconds ✅
- SC-006: All providers pass contract tests ✅
- SC-007: Unhealthy providers automatically bypassed ✅

### Contracts & Tests for User Story 1

> **TDD REQUIREMENT**: Write tests FIRST, ensure they FAIL before implementation

- [ ] T013 [P] [US1] Create contract test suite for LLMProvider interface in tests/contract/test_llm_provider_interface.py (6 tests)
- [ ] T014 [P] [US1] Create contract test file for ClaudeAdapter in tests/contract/test_claude_adapter_contract.py
- [ ] T015 [P] [US1] Create contract test file for OpenAIAdapter in tests/contract/test_openai_adapter_contract.py
- [ ] T016 [P] [US1] Create integration test for failover strategy in tests/integration/test_failover_strategy.py
- [ ] T017 [P] [US1] Create integration test for provider health tracking in tests/integration/test_provider_health_tracking.py

### Provider Implementations for User Story 1

- [ ] T018 [P] [US1] Implement ClaudeAdapter class in src/llm_adapters/claude_adapter.py (inherits from LLMProvider, uses Claude SDK tool calling)
- [ ] T019 [P] [US1] Implement OpenAIAdapter class in src/llm_adapters/openai_adapter.py (inherits from LLMProvider, uses OpenAI Structured Outputs)
- [ ] T020 [P] [US1] Add authentication handling to ClaudeAdapter (ANTHROPIC_API_KEY from env)
- [ ] T021 [P] [US1] Add authentication handling to OpenAIAdapter (OPENAI_API_KEY from env)
- [ ] T022 [P] [US1] Add timeout and rate limit error handling to ClaudeAdapter
- [ ] T023 [P] [US1] Add timeout and rate limit error handling to OpenAIAdapter
- [ ] T024 [P] [US1] Implement confidence score generation (prompt-based) in ClaudeAdapter
- [ ] T025 [P] [US1] Implement confidence score generation (prompt-based) in OpenAIAdapter
- [ ] T026 [P] [US1] Add token usage extraction from API responses in ClaudeAdapter
- [ ] T027 [P] [US1] Add token usage extraction from API responses in OpenAIAdapter

### Health Tracking for User Story 1

- [ ] T028 [US1] Implement HealthTracker class in src/llm_adapters/health_tracker.py (file-based persistence)
- [ ] T029 [US1] Implement is_healthy() method with circuit breaker logic in HealthTracker
- [ ] T030 [US1] Implement record_success() method updating metrics in HealthTracker
- [ ] T031 [US1] Implement record_failure() method with circuit breaker state transitions in HealthTracker
- [ ] T032 [US1] Implement get_metrics() and get_all_metrics() methods in HealthTracker
- [ ] T033 [US1] Implement metrics persistence (atomic file writes) to data/llm_health/health_metrics.json
- [ ] T034 [US1] Implement metrics loading on HealthTracker initialization
- [ ] T035 [US1] Implement reset_metrics() method for manual recovery in HealthTracker
- [ ] T036 [P] [US1] Create unit tests for HealthTracker in tests/unit/test_health_tracker.py (7 test cases)

### Orchestration Strategy for User Story 1

- [ ] T037 [P] [US1] Create OrchestrationStrategy abstract base class in src/llm_orchestrator/strategies/base.py
- [ ] T038 [US1] Implement FailoverStrategy class in src/llm_orchestrator/strategies/failover.py
- [ ] T039 [US1] Add sequential provider attempts logic to FailoverStrategy (try priority order)
- [ ] T040 [US1] Add health checking before provider calls in FailoverStrategy
- [ ] T041 [US1] Add failure recording and auto-skip unhealthy providers in FailoverStrategy
- [ ] T042 [US1] Add <2 second failover performance optimization to FailoverStrategy

### Orchestrator for User Story 1

- [ ] T043 [US1] Implement LLMOrchestrator class in src/llm_orchestrator/orchestrator.py
- [ ] T044 [US1] Implement constructor accepting providers, config, health_tracker, cost_tracker
- [ ] T045 [US1] Implement extract_entities() method delegating to strategy in LLMOrchestrator
- [ ] T046 [US1] Add health metric recording (success/failure) after provider calls
- [ ] T047 [US1] Implement get_provider_status() method returning ProviderStatus dict
- [ ] T048 [US1] Implement set_strategy() method changing active strategy
- [ ] T049 [US1] Implement test_provider() method for connectivity testing
- [ ] T050 [P] [US1] Create contract tests for LLMOrchestrator in tests/contract/test_orchestrator_contract.py (7 test cases)

### Integration for User Story 1

- [ ] T051 [US1] Update existing GeminiAdapter to record token usage for cost tracking
- [ ] T052 [US1] Test end-to-end failover: Gemini → Claude → OpenAI with simulated failures
- [ ] T053 [US1] Verify failover completes in <2 seconds with performance benchmarks
- [ ] T054 [US1] Verify all three providers pass contract test suite

**Checkpoint**: User Story 1 complete - system has automatic failover with health tracking

---

## Phase 4: User Story 2 - Multi-Provider Consensus (Priority: P2)

**Goal**: Improve extraction accuracy by 10% through querying multiple providers and merging results using weighted voting

**Independent Test**: Enable consensus mode, process 100 test emails with known entities, verify accuracy improves by at least 10% compared to single-provider mode

**Success Criteria**:
- SC-003: Consensus mode improves accuracy by 10% ✅

### Tests for User Story 2

- [ ] T055 [P] [US2] Create integration test for consensus strategy in tests/integration/test_consensus_strategy.py
- [ ] T056 [P] [US2] Create unit tests for fuzzy matching logic in tests/unit/test_consensus_algorithm.py

### Consensus Algorithm for User Story 2

- [ ] T057 [P] [US2] Implement Jaro-Winkler string similarity function in src/llm_orchestrator/strategies/consensus.py
- [ ] T058 [P] [US2] Implement fuzzy matching logic (threshold 0.85) for entity values in consensus.py
- [ ] T059 [P] [US2] Implement weighted voting algorithm for conflict resolution in consensus.py
- [ ] T060 [P] [US2] Implement tie-breaking logic (majority → historical performance → abstention) in consensus.py

### Consensus Strategy for User Story 2

- [ ] T061 [US2] Implement ConsensusStrategy class in src/llm_orchestrator/strategies/consensus.py
- [ ] T062 [US2] Add parallel provider queries using asyncio.gather() in ConsensusStrategy
- [ ] T063 [US2] Add result merging logic calling fuzzy matching and weighted voting
- [ ] T064 [US2] Add validation requiring minimum 2 provider responses
- [ ] T065 [US2] Add confidence score recalculation for merged results

### Validation for User Story 2

- [ ] T066 [US2] Create test dataset of 100 emails with known correct entities
- [ ] T067 [US2] Run accuracy benchmark: single-provider vs consensus mode
- [ ] T068 [US2] Verify 10% accuracy improvement requirement met

**Checkpoint**: User Story 2 complete - consensus mode improves accuracy

---

## Phase 5: User Story 3 - Best-Match Selection (Priority: P3)

**Goal**: Query multiple providers and select the extraction result with highest aggregate confidence score

**Independent Test**: Configure best-match mode with 3 providers, send test emails, verify system selects and uses result with highest aggregate confidence

**Success Criteria**:
- SC-008: Best-match selects highest-confidence result ✅

### Tests for User Story 3

- [ ] T069 [P] [US3] Create integration test for best-match strategy in tests/integration/test_best_match_strategy.py
- [ ] T070 [P] [US3] Create unit test for aggregate confidence calculation in tests/unit/test_best_match_algorithm.py

### Best-Match Strategy for User Story 3

- [ ] T071 [P] [US3] Implement calculate_aggregate_confidence() function in src/llm_orchestrator/strategies/best_match.py
- [ ] T072 [US3] Implement BestMatchStrategy class in src/llm_orchestrator/strategies/best_match.py
- [ ] T073 [US3] Add parallel provider queries using asyncio.gather() in BestMatchStrategy
- [ ] T074 [US3] Add aggregate confidence calculation for each result
- [ ] T075 [US3] Add result selection logic (max confidence) with tie-breaking
- [ ] T076 [US3] Verify correct provider result selection with varying confidence scores

**Checkpoint**: User Story 3 complete - best-match strategy operational

---

## Phase 6: User Story 4 - Provider Health Monitoring & Visibility (Priority: P3)

**Goal**: Administrators can view real-time health status, error rates, response times, and cost metrics for all providers through CLI commands

**Independent Test**: Process emails over time, trigger failure scenarios, run `collabiq llm status --detailed` to verify accurate health metrics, error counts, response times, and costs displayed

**Success Criteria**:
- SC-004: Admin can view provider health via CLI ✅
- SC-005: Cost per email tracked and reported ✅

### Cost Tracking for User Story 4

- [ ] T077 [P] [US4] Implement CostTracker class in src/llm_orchestrator/cost_tracker.py (file-based persistence)
- [ ] T078 [P] [US4] Implement record_usage() method tracking tokens and cost in CostTracker
- [ ] T079 [P] [US4] Implement get_metrics() and get_all_metrics() methods in CostTracker
- [ ] T080 [P] [US4] Implement cost calculation using provider-specific pricing in CostTracker
- [ ] T081 [P] [US4] Implement persistence to data/llm_health/cost_metrics.json with atomic writes
- [ ] T082 [P] [US4] Create unit tests for CostTracker in tests/unit/test_cost_tracker.py

### CLI Commands for User Story 4

- [ ] T083 [US4] Update `collabiq llm status` command in src/collabiq/commands/llm.py to call orchestrator.get_provider_status()
- [ ] T084 [US4] Add health status display (healthy/unhealthy, circuit breaker state) to `llm status` output
- [ ] T085 [US4] Add success rate and error count display to `llm status` output
- [ ] T086 [US4] Add average response time display to `llm status` output
- [ ] T087 [US4] Add last success/failure timestamps to `llm status` output
- [ ] T088 [US4] Implement `collabiq llm status --detailed` flag showing cost metrics
- [ ] T089 [US4] Add total API calls, tokens, and cost per provider to `--detailed` output
- [ ] T090 [US4] Add average cost per email to `--detailed` output
- [ ] T091 [US4] Add orchestration strategy display (active strategy, priority order) to `--detailed` output
- [ ] T092 [US4] Update `collabiq llm test <provider>` command to call orchestrator.test_provider()
- [ ] T093 [US4] Update `collabiq llm set-strategy <strategy>` command to call orchestrator.set_strategy()
- [ ] T094 [US4] Add Rich formatted tables for health and cost metrics display

### Integration for User Story 4

- [ ] T095 [US4] Integrate cost tracking into orchestrator (call cost_tracker.record_usage() after extraction)
- [ ] T096 [US4] Test CLI commands with real provider data and metrics
- [ ] T097 [US4] Verify cost calculations accuracy against provider pricing

**Checkpoint**: User Story 4 complete - full admin visibility into provider health and costs

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, configuration examples, and final integration

- [ ] T098 Create default provider configuration file template at data/llm_health/provider_config.json.example
- [ ] T099 Create default orchestration configuration file template at data/llm_health/orchestration_config.json.example
- [ ] T100 Update .env.example with ANTHROPIC_API_KEY and OPENAI_API_KEY entries
- [ ] T101 Update CLAUDE.md with multi-LLM technology stack entries
- [ ] T102 Update README.md with multi-provider usage examples
- [ ] T103 [P] Add logging for orchestrator operations (strategy selection, provider calls, fallbacks)
- [ ] T104 [P] Add logging for health tracker state transitions (CLOSED → OPEN → HALF_OPEN)
- [ ] T105 [P] Add logging for cost tracking updates
- [ ] T106 Run full contract test suite across all providers (Gemini, Claude, OpenAI)
- [ ] T107 Run integration test suite for all strategies (failover, consensus, best-match)
- [ ] T108 Performance benchmark: verify failover <2s, consensus accuracy +10%
- [ ] T109 Create quickstart documentation for multi-LLM setup and usage
- [ ] T110 Final verification: all success criteria met (SC-001 through SC-008)

---

## Dependencies

### User Story Completion Order

```
Phase 1 (Setup) + Phase 2 (Foundation)
    ↓
Phase 3: User Story 1 (P1 - Failover) 🎯 MVP ← MUST COMPLETE FIRST
    ↓
    ├─→ Phase 4: User Story 2 (P2 - Consensus) ← Can run in parallel with US3 and US4
    ├─→ Phase 5: User Story 3 (P3 - Best-Match) ← Can run in parallel with US2 and US4
    └─→ Phase 6: User Story 4 (P3 - Monitoring) ← Can run in parallel with US2 and US3
            ↓
        Phase 7: Polish & Final Integration
```

### Key Dependencies

- **US2, US3, US4 depend on US1**: All three need the foundational provider implementations (ClaudeAdapter, OpenAIAdapter), HealthTracker, and LLMOrchestrator from US1
- **US2 and US3 are independent**: Consensus and Best-Match strategies can be implemented in parallel
- **US4 independent of US2/US3**: Health monitoring and CLI commands don't depend on consensus or best-match strategies

---

## Parallel Execution Opportunities

### Within Phase 2 (Foundation)
- T005-T009: All Pydantic models can be created in parallel (different entities)
- No dependencies between model definitions

### Within Phase 3 (User Story 1)

**Contracts & Tests** (T013-T017):
- All contract test files can be created in parallel

**Provider Implementations** (T018-T027):
- ClaudeAdapter tasks (T018, T020, T022, T024, T026) can run in parallel with OpenAIAdapter tasks (T019, T021, T023, T025, T027)
- Within each provider: authentication, error handling, confidence, and token extraction can be parallelized

**Health Tracking** (T028-T036):
- T036 (unit tests) can be created in parallel with T028-T035 (implementation)

**Orchestration** (T037-T050):
- T037 (base class) and T050 (contract tests) can run in parallel
- FailoverStrategy tasks (T038-T042) are sequential within themselves

### Within Phase 4 (User Story 2)
- T055-T056: Tests can be created in parallel
- T057-T060: Consensus algorithm components can be implemented in parallel
- T061-T065: ConsensusStrategy implementation is sequential

### Within Phase 5 (User Story 3)
- T069-T070: Tests can be created in parallel
- T071-T076: Best-match algorithm and strategy can be partially parallelized

### Within Phase 6 (User Story 4)
- T077-T082: CostTracker implementation can run in parallel with CLI commands (T083-T094)
- Within CLI commands (T083-T094): Display formatting tasks can be parallelized

### Within Phase 7 (Polish)
- T098-T102: Configuration and documentation tasks can all run in parallel
- T103-T105: Logging additions can run in parallel
- T106-T110: Testing and benchmarking tasks are sequential

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Phase 3 (User Story 1)** constitutes the complete MVP:
- ✅ ClaudeAdapter and OpenAIAdapter implementations
- ✅ HealthTracker with circuit breaking
- ✅ FailoverStrategy for automatic provider switching
- ✅ LLMOrchestrator coordinating providers
- ✅ Failover <2 seconds performance
- ✅ All providers pass contract tests

**Delivers**: Production-ready multi-provider failover ensuring business continuity

### Incremental Delivery

After MVP (US1), deliver user stories incrementally in priority order:

1. **US1 (P1)**: Automatic failover - MUST deliver first (foundation for all others)
2. **US2 (P2)**: Consensus mode - Delivers 10% accuracy improvement
3. **US3 (P3)**: Best-match selection - Optimization strategy
4. **US4 (P3)**: Health monitoring - Admin visibility and operational tooling

Each story is independently testable and deployable.

### Testing Strategy

**TDD Workflow** (strictly enforced):
1. Write contract/integration tests FIRST (ensure they FAIL)
2. Implement feature code (tests turn GREEN)
3. Refactor for quality (tests stay GREEN)

**Test Coverage Targets**:
- Contract tests: 100% (all providers must pass interface tests)
- Integration tests: Cover all user journey scenarios
- Unit tests: Critical algorithms (fuzzy matching, circuit breaker, cost calculation)

**Performance Benchmarks**:
- Failover: <2 seconds per provider switch
- Consensus: +10% accuracy improvement vs single-provider
- Health status command: Complete in <1 second

---

## Total Task Count: 110 tasks

**Breakdown by Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundation): 8 tasks
- Phase 3 (US1 - Failover): 42 tasks
- Phase 4 (US2 - Consensus): 14 tasks
- Phase 5 (US3 - Best-Match): 8 tasks
- Phase 6 (US4 - Monitoring): 21 tasks
- Phase 7 (Polish): 13 tasks

**Breakdown by User Story**:
- US1 (P1 - Failover): 42 tasks → MVP
- US2 (P2 - Consensus): 14 tasks
- US3 (P3 - Best-Match): 8 tasks
- US4 (P3 - Monitoring): 21 tasks
- Setup + Foundation: 12 tasks
- Polish: 13 tasks

**Parallel Opportunities**: ~40% of tasks within each phase can run in parallel

---

## Validation Checklist

All tasks follow the required format:
- ✅ Every task starts with `- [ ]` checkbox
- ✅ Every task has sequential Task ID (T001-T110)
- ✅ Parallelizable tasks marked with [P]
- ✅ User story tasks marked with [US1], [US2], [US3], or [US4]
- ✅ Every task includes specific file path
- ✅ Tasks organized by user story for independent implementation
- ✅ Clear acceptance criteria per user story
- ✅ Dependencies documented
- ✅ MVP scope clearly identified (Phase 3)
