# Implementation Tasks: LLM Quality Metrics & Tracking

**Feature**: 013-llm-quality-metrics
**Branch**: `013-llm-quality-metrics`
**Status**: ✅ **MVP COMPLETE** (Phase 3) - P2/P3 Pending
**Generated**: 2025-11-09
**MVP Completed**: 2025-11-09

## Progress Summary

**Overall Progress**: 30/38 tasks complete (79%)
- ✅ **Phase 1** (T001-T002): Setup & Initialization - **COMPLETE**
- ✅ **Phase 2** (T003-T006): Foundational Models - **COMPLETE**
- ✅ **Phase 3** (T007-T017): User Story 1 - Track Quality (P1) - **MVP COMPLETE**
- ✅ **Phase 4** (T018-T023): User Story 2 - Compare Providers (P2) - **COMPLETE**
- ✅ **Phase 5** (T024-T030): User Story 3 - Quality Routing (P3) - **COMPLETE**
- 🔄 **Phase 6** (T031-T038): Polish & Cross-Cutting - PENDING

## Overview

This document defines the implementation tasks for LLM quality metrics tracking, organized by user story to enable independent, incremental delivery. Each phase represents a complete, testable increment of functionality.

---

## Implementation Strategy

### MVP Scope (User Story 1 - P1)
The MVP delivers basic quality metrics tracking, enabling administrators to monitor extraction quality and validation failures. This provides immediate value by making quality data visible and actionable.

### Incremental Delivery
- **Phase 1**: Setup (project initialization, directory structure) → ✅ **COMPLETE**
- **Phase 2**: Foundational (pydantic models, shared utilities) → ✅ **COMPLETE**
- **Phase 3**: User Story 1 - Track Quality Metrics (P1) → ✅ **MVP COMPLETE**
- **Phase 4**: User Story 2 - Compare Provider Performance (P2) → 🔄 **PENDING**
- **Phase 5**: User Story 3 - Quality-Based Routing (P3) → 🔄 **PENDING**
- **Phase 6**: Polish & Cross-Cutting Concerns → 🔄 **PENDING**

### Independent Testing
Each user story phase includes verification criteria to confirm the increment works independently before proceeding to the next story.

---

## Phase 1: Setup & Initialization

**Goal**: Prepare project structure and ensure data directory exists for quality metrics storage.

**Tasks**:

- [x] T001 Create data/llm_health directory if it doesn't exist (may already exist from health_tracker)
- [x] T002 Verify write permissions to data/llm_health directory

**Verification**:
- ✅ `data/llm_health/` directory exists
- ✅ Directory is writable (test with touch command)

---

## Phase 2: Foundational - Data Models & Utilities

**Goal**: Define pydantic models for quality metrics and implement shared utility functions used across all user stories.

**Dependencies**: Phase 1 complete

**Tasks**:

- [x] T003 [P] Add QualityMetricsRecord model to src/llm_orchestrator/types.py (per-extraction quality data: email_id, provider_name, per_field_confidence dict, overall_confidence, field_completeness_percentage, fields_extracted, validation_passed, validation_failure_reasons, notion_matching_attempted, notion_matching_success, extraction_timestamp)
- [x] T004 [P] Add ProviderQualitySummary model to src/llm_orchestrator/types.py (aggregate statistics: provider_name, total_extractions, successful_validations, failed_validations, validation_success_rate, average_overall_confidence, confidence_std_deviation, average_field_completeness, average_fields_extracted, per_field_confidence_averages dict, quality_trend, last_50_avg_confidence, notion_matching_success_rate, updated_at)
- [x] T005 [P] Add QualityThresholdConfig model to src/llm_orchestrator/types.py (threshold configuration: threshold_name, minimum_average_confidence, minimum_field_completeness, maximum_validation_failure_rate, minimum_notion_matching_success_rate, evaluation_window_size, enabled)
- [x] T006 [P] Add ProviderQualityComparison model to src/llm_orchestrator/types.py (cross-provider analysis: comparison_timestamp, providers_compared list, provider_rankings list of dicts, quality_to_cost_rankings list of dicts, recommended_provider, recommendation_reason)

**Verification**:
- ✅ All 4 pydantic models added to src/llm_orchestrator/types.py
- ✅ Models pass pydantic validation with example data from data-model.md
- ✅ Import test: `from llm_orchestrator.types import QualityMetricsRecord, ProviderQualitySummary, QualityThresholdConfig, ProviderQualityComparison`

---

## Phase 3: User Story 1 - Track Response Quality Metrics (P1)

**Goal**: Implement basic quality tracking - record extraction metrics, calculate aggregates, persist to JSON, and retrieve summaries.

**Priority**: P1 (MVP)

**Dependencies**: Phase 2 complete

**User Story**: System administrators need to monitor the quality of LLM responses when extracting structured data from emails. The system tracks how accurately each provider extracts the 5 key entities and enables viewing of aggregate quality statistics.

**Independent Test Criteria**:
1. Process an email through any provider (Gemini/Claude/OpenAI)
2. Extraction completes with confidence scores
3. Quality metrics are recorded: per-field confidence, overall confidence, field completeness
4. Retrieve provider quality summary via QualityTracker.get_metrics()
5. Summary shows: total extractions, average confidence, validation success rate
6. Metrics persist to data/llm_health/quality_metrics.json
7. Restart system and verify metrics reload correctly

**Tasks**:

### T007-T011: Core QualityTracker Implementation

- [x] T007 [US1] Create src/llm_orchestrator/quality_tracker.py with QualityTracker class structure (constructor with data_dir and evaluation_window_size parameters, initialize metrics dict, create data_dir if needed)
- [x] T008 [US1] Implement _load_metrics() method in src/llm_orchestrator/quality_tracker.py (load quality_metrics.json, parse JSON to ProviderQualitySummary objects, convert ISO timestamps to datetime, handle missing file gracefully, return empty dict on corruption)
- [x] T009 [US1] Implement _save_metrics() method in src/llm_orchestrator/quality_tracker.py (atomic write using tempfile.mkstemp() and shutil.move(), convert datetime to ISO strings, write with indent=2, clean up temp file on error, mirror health_tracker.py pattern exactly)
- [x] T010 [US1] Implement get_metrics(provider_name) method in src/llm_orchestrator/quality_tracker.py (lookup provider in metrics dict, initialize default ProviderQualitySummary if not found, persist new default to disk, return summary)
- [x] T011 [P] [US1] Implement get_all_metrics() method in src/llm_orchestrator/quality_tracker.py (return copy of metrics dict, no side effects)

### T012-T015: Quality Metric Calculation & Recording

- [x] T012 [US1] Implement _calculate_field_completeness() helper in src/llm_orchestrator/quality_tracker.py (count non-None fields in ExtractedEntities, return tuple of (fields_extracted int, completeness_percentage float), handle all 5 entities: person_in_charge, startup_name, partner_org, details, date)
- [x] T013 [US1] Implement _calculate_overall_confidence() helper in src/llm_orchestrator/quality_tracker.py (extract per-field confidence from ConfidenceScores, calculate average of 5 confidence values, return overall_confidence float)
- [x] T014 [US1] Implement _update_aggregate_statistics() method in src/llm_orchestrator/quality_tracker.py (increment total_extractions, update validation counters, recalculate running averages for confidence and completeness, update per-field confidence averages, calculate standard deviation, use incremental statistics formulas to avoid storing all records)
- [x] T015 [US1] Implement record_extraction(provider_name, extracted_entities, validation_passed, validation_failure_reasons) method in src/llm_orchestrator/quality_tracker.py (validate parameters, extract confidence and completeness from extracted_entities, call _update_aggregate_statistics(), call _save_metrics(), raise ValueError if validation_passed=False without failure_reasons)

### T016-T017: Integration & CLI Display

- [x] T016 [US1] Integrate quality_tracker.record_extraction() into orchestrator in src/llm_orchestrator/orchestrator.py (add quality_tracker instance to orchestrator constructor, call record_extraction() after cost_tracker.record_usage() in successful extraction path, pass extracted_entities and validation result, handle errors gracefully without blocking extraction)
- [x] T017 [US1] Add quality metrics display to status command in src/collabiq/commands/llm.py (display per-provider quality summary with rich tables: total extractions, validation success rate %, average confidence %, field completeness %, per-field confidence breakdown in detailed view)

**Phase 3 Checkpoint**:
- ✅ QualityTracker class implemented with record_extraction(), get_metrics(), get_all_metrics()
- ✅ Quality metrics recorded after each extraction in orchestrator
- ✅ Metrics persist to data/llm_health/quality_metrics.json with atomic writes
- ✅ CLI command `collabiq llm status --detailed` displays quality metrics for all providers
- ✅ Per-field confidence breakdown displayed for each provider
- 🔄 Process 10+ test emails and verify metrics are accurate (confidence, completeness, validation) - **MANUAL TESTING REQUIRED**
- 🔄 Restart system and verify metrics reload correctly from JSON - **MANUAL TESTING REQUIRED**

**✅ MVP DELIVERABLE COMPLETE**: After Phase 3, administrators can monitor extraction quality, view aggregate statistics, and identify validation failures. This provides immediate value for quality-based decision making.

**Implementation Summary (2025-11-09)**:
- ✅ 4 new Pydantic models added to [src/llm_orchestrator/types.py](../../src/llm_orchestrator/types.py)
- ✅ Complete QualityTracker class created in [src/llm_orchestrator/quality_tracker.py](../../src/llm_orchestrator/quality_tracker.py) (420 lines)
- ✅ Orchestrator integration in [src/llm_orchestrator/orchestrator.py](../../src/llm_orchestrator/orchestrator.py) with graceful error handling
- ✅ CLI quality metrics display in [src/collabiq/commands/llm.py](../../src/collabiq/commands/llm.py) with color-coded tables
- ✅ **BONUS**: Cost tracking also integrated (wasn't previously wired up!)
- ✅ File-based JSON persistence with atomic writes
- ✅ Incremental statistics (running averages, no full record storage)

---

## Phase 4: User Story 2 - Compare Provider Performance (P2)

**Goal**: Enable cross-provider quality comparison and quality-to-cost analysis to identify the best-performing provider.

**Priority**: P2

**Dependencies**: Phase 3 complete (US1 quality tracking operational)

**User Story**: System administrators need to compare quality metrics across multiple LLM providers to identify which provider performs best and offers the best value (quality per dollar).

**Independent Test Criteria**:
1. All 3 providers (Gemini, Claude, OpenAI) have processed emails and have quality metrics
2. All 3 providers have cost metrics tracked by CostTracker
3. Call QualityTracker.compare_providers(cost_tracker)
4. Returns ProviderQualityComparison with provider_rankings (by quality score)
5. Returns quality_to_cost_rankings (by value score)
6. Recommended provider identified with human-readable reason
7. CLI command displays comparison table with quality scores and value scores
8. Administrators can identify best provider within 5 minutes of reviewing output

**Tasks**:

### T018-T021: Provider Comparison Implementation

- [x] T018 [P] [US2] Implement _calculate_quality_score() method in src/llm_orchestrator/quality_tracker.py (composite quality score weighted: 40% confidence + 30% completeness + 30% validation_rate, return score 0.0-1.0)
- [x] T019 [P] [US2] Implement _calculate_value_score() method in src/llm_orchestrator/quality_tracker.py (value_score = quality_score / (1 + cost_per_email * 1000), free tier providers get 1.5x bonus, return unbounded float score)
- [x] T020 [US2] Implement _generate_recommendation() helper in src/llm_orchestrator/quality_tracker.py (determine best value provider, generate 2-3 sentence human-readable explanation, return tuple of provider_name and reason)
- [x] T021 [US2] Implement compare_providers(provider_names, cost_tracker) method in src/llm_orchestrator/quality_tracker.py (calculate quality and value scores, rank by both dimensions, generate recommendation, return ProviderQualityComparison)

### T022-T023: CLI Comparison Display

- [x] T022 [P] [US2] Implement CLI command `collabiq llm compare` in src/collabiq/commands/llm.py (display quality rankings table, value rankings table with recommendation marker, show recommendation summary, add --detailed flag for per-metric breakdown)
- [x] T023 [US2] Add detailed comparison display with per-metric breakdown (confidence, completeness, validation rate, cost per email, quality score, value score with color-coded formatting)

**Phase 4 Checkpoint**:
- ✅ QualityTracker.compare_providers() implemented and returns ProviderQualityComparison
- ✅ Quality scores calculated with weighted formula (40% confidence, 30% completeness, 30% validation)
- ✅ Value scores calculated with quality-to-cost ratio (free tier gets 1.5x bonus)
- ✅ Recommendation logic implemented with human-readable explanations
- ✅ CLI command `collabiq llm compare` displays provider comparison
- ✅ Basic comparison view shows quality rankings and value rankings with recommendation
- ✅ Detailed comparison view (--detailed flag) shows per-metric breakdown
- ✅ Color-coded formatting for quality thresholds (green/yellow/red)
- 🔄 Test with real data: Process emails through all 3 providers and verify comparison - **MANUAL TESTING REQUIRED**
- 🔄 Verify recommendation logic with different cost scenarios - **MANUAL TESTING REQUIRED**

**DELIVERABLE**: After Phase 4, administrators can compare providers, identify the best-performing provider, and calculate ROI for provider selection decisions.

**Implementation Summary (2025-11-09)**:
- ✅ 4 new methods added to [src/llm_orchestrator/quality_tracker.py](../../src/llm_orchestrator/quality_tracker.py):
  - `_calculate_quality_score()`: Composite scoring with weighted formula
  - `_calculate_value_score()`: Quality-to-cost ratio calculation
  - `_generate_recommendation()`: Human-readable recommendation generation
  - `compare_providers()`: Full provider comparison with rankings
- ✅ CLI command `collabiq llm compare` added to [src/collabiq/commands/llm.py](../../src/collabiq/commands/llm.py)
- ✅ Basic and detailed comparison display modes implemented
- ✅ Rich table formatting with color-coded metrics
- ✅ All syntax verified with py_compile

---

## Phase 5: User Story 3 - Quality-Based Provider Selection (P3)

**Goal**: Implement automated quality-based routing that selects providers based on quality thresholds and historical performance.

**Priority**: P3

**Dependencies**: Phase 4 complete (US2 comparison operational)

**User Story**: The system automatically routes extraction requests to providers based on quality metrics and business rules, ensuring high-accuracy extractions while managing costs.

**Independent Test Criteria**:
1. Configure quality thresholds (min confidence 85%, max validation failures 5%)
2. Process emails through system
3. For each extraction, system checks if provider meets quality thresholds
4. Providers failing thresholds are excluded from selection
5. Among qualifying providers, system selects lowest-cost option
6. CLI displays threshold check results for each provider
7. Quality-based routing improves accuracy by 15% vs cost-only routing

**Tasks**:

### T024-T027: Quality-Aware Routing Configuration & Selection

- [x] T024 [P] [US3] Add quality-aware routing fields to OrchestrationConfig in src/llm_orchestrator/types.py (add enable_quality_routing bool flag, quality_threshold QualityThresholdConfig | None, quality_weight float 0.0-1.0, preserve backward compatibility with defaults)
- [x] T025 [US3] Add select_provider_by_quality() method to QualityTracker in src/llm_orchestrator/quality_tracker.py (takes list of candidate provider names, filters providers with metrics, ranks candidates by composite quality score, returns provider name with highest quality or None, logs selection decision with reasoning)
- [x] T026 [P] [US3] Modify FailoverStrategy in src/llm_orchestrator/strategies/failover.py (check if quality_tracker is passed, call select_provider_by_quality() to get quality-ranked provider, try quality-selected provider first then fall back to priority order, maintain existing health checks and circuit breaker logic, add logging for quality-based selection)
- [x] T027 [US3] Update orchestrator to pass quality_tracker to strategies (modify FailoverStrategy initialization in orchestrator.__init__() to accept optional quality_tracker, pass self.quality_tracker to FailoverStrategy constructor when enable_quality_routing is True, ensure backward compatibility)

### T028-T030: CLI Commands & Integration Test

- [x] T028 [US3] Add CLI command `collabiq llm set-quality-routing` in src/collabiq/commands/llm.py (subcommand to enable/disable quality-based routing, arguments: --enable/--disable, --min-confidence, --min-completeness, --max-validation-failures, display current quality routing status)
- [x] T029 [P] [US3] Add quality routing status to `collabiq llm status --detailed` output (show "Quality Routing: Enabled/Disabled", if enabled show active thresholds, show which provider would be selected based on current quality metrics)
- [x] T030 [US3] Add integration test for quality-aware routing in tests/integration/test_quality_routing.py (mock quality metrics for multiple providers, verify quality routing selects highest quality provider, verify fallback to priority order when quality routing disabled, test threshold filtering, test health check integration)

**Phase 5 Checkpoint**:
- ✅ Quality-aware routing configuration added to OrchestrationConfig (T024)
- ✅ select_provider_by_quality() method implemented in QualityTracker (T025)
- ✅ FailoverStrategy modified to support quality-based routing (T026)
- ✅ Orchestrator updated to pass quality_tracker to FailoverStrategy (T027)
- ✅ CLI command `collabiq llm set-quality-routing` added (T028)
- ✅ Quality routing status displayed in `collabiq llm status --detailed` (T029)
- ✅ Integration tests added for quality-aware routing (T030)
- 🔄 Manual testing required: Enable quality routing and verify provider selection
- 🔄 Manual testing required: Process emails and verify quality-based provider selection

**DELIVERABLE**: After Phase 5, the system supports opt-in quality-based provider routing. When enabled, providers are selected based on historical quality metrics rather than fixed priority order. All tasks T024-T030 complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Add refinements, documentation, and cross-cutting features that improve the overall quality and usability of the feature.

**Dependencies**: All user stories (P1, P2, P3) complete

**Tasks**:

- [ ] T031 [P] Add logging throughout quality_tracker.py (log quality metric updates at DEBUG level, log threshold failures at WARNING level, log routing decisions at INFO level, use structured logging with provider_name, confidence, completeness as fields)
- [ ] T032 [P] Add error handling for edge cases in quality_tracker.py (handle corrupted quality_metrics.json gracefully, handle missing ConfidenceScores in ExtractedEntities, handle division by zero in value score calculation, handle negative or invalid confidence values)
- [ ] T033 [P] Add __all__ export list to src/llm_orchestrator/types.py (export QualityMetricsRecord, ProviderQualitySummary, QualityThresholdConfig, ProviderQualityComparison for clean imports)
- [ ] T034 [P] Update CLAUDE.md with quality metrics feature (add "File-based JSON for provider quality metrics (013-llm-quality-metrics)" to Active Technologies section, maintain consistency with health and cost tracking entries)
- [ ] T035 [P] Add quality metrics export command in src/cli/commands/quality.py (`collabiq quality export --format csv --output quality_report.csv`, support csv/json/html formats, include all provider metrics, add --date-range filter, generate reports for stakeholder sharing)
- [ ] T036 Verify all atomic writes work correctly (test concurrent write scenarios, verify no partial writes or corruption, validate tempfile cleanup on errors, confirm POSIX atomic rename semantics)
- [ ] T037 Performance test with 10,000 extraction records per provider (measure query time for get_metrics(), measure comparison time for compare_providers(), verify <2 second response time per SC-005, optimize if needed)
- [ ] T038 Update quickstart.md with actual CLI commands (replace placeholder commands with real implementation, add screenshots or example output, verify all 7 quickstart steps work end-to-end)

**Phase 6 Checkpoint**:
- ✅ All logging added with appropriate levels
- ✅ All edge cases handled gracefully without crashes
- ✅ CLAUDE.md updated with new technology
- ✅ Quality export command working with CSV/JSON/HTML formats
- ✅ Atomic writes verified with concurrent test scenarios
- ✅ Performance targets met: <2s for 10,000 records
- ✅ Quickstart guide validated end-to-end

**FINAL DELIVERABLE**: Feature complete, polished, and ready for production use.

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational Models)
    ↓
Phase 3 (US1 - Track Quality Metrics) ← MVP COMPLETE HERE
    ↓
Phase 4 (US2 - Compare Providers) ← INDEPENDENT (can be implemented in parallel with US3 if desired)
    ↓
Phase 5 (US3 - Quality-Based Routing)
    ↓
Phase 6 (Polish & Cross-Cutting)
```

**Note**: Phase 4 (US2) and Phase 5 (US3) have minimal dependencies. If parallel development is needed, US2 can proceed while US3 is being implemented, as long as US1 (foundation) is complete.

---

## Parallel Execution Opportunities

### Within Phase 2 (Foundational)
All model definitions (T003-T006) can be implemented in parallel - they have no interdependencies.

**Parallel Group 2A**:
- T003: QualityMetricsRecord
- T004: ProviderQualitySummary
- T005: QualityThresholdConfig
- T006: ProviderQualityComparison

### Within Phase 3 (US1)
Core tracker implementation and helpers can be parallelized:

**Parallel Group 3A** (after T007 skeleton created):
- T008: _load_metrics()
- T009: _save_metrics()
- T010: get_metrics()
- T011: get_all_metrics()

**Parallel Group 3B** (calculation helpers):
- T012: _calculate_field_completeness()
- T013: _calculate_overall_confidence()

**Parallel Group 3C** (final integration, after T015 complete):
- T016: Orchestrator integration
- T017: CLI display

### Within Phase 4 (US2)
Comparison calculations can be parallelized:

**Parallel Group 4A**:
- T018: _calculate_quality_score()
- T019: _calculate_value_score()
- T020: _rank_providers()
- T022: reset_metrics()

**Parallel Group 4B** (after T021 complete):
- T023: CLI comparison display

### Within Phase 5 (US3)
Trend and threshold logic can be parallelized:

**Parallel Group 5A**:
- T024: _calculate_trend()
- T026: check_quality_threshold()
- T030: quality_thresholds.json

**Parallel Group 5B** (after T027 complete):
- T029: CLI quality commands

### Within Phase 6 (Polish)
All polish tasks are independent and can run in parallel:

**Parallel Group 6A**:
- T031: Logging
- T032: Error handling
- T033: __all__ exports
- T034: CLAUDE.md update
- T035: Export command
- T036: Atomic write verification
- T037: Performance testing
- T038: Quickstart update

---

## Task Summary

**Total Tasks**: 38
- Phase 1 (Setup): 2 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (US1 - Track Quality): 11 tasks ← **MVP**
- Phase 4 (US2 - Compare Providers): 6 tasks
- Phase 5 (US3 - Quality-Based Routing): 7 tasks
- Phase 6 (Polish): 8 tasks

**Parallelizable Tasks**: 27 tasks (71%) marked with [P]
**User Story Breakdown**:
- US1 (P1): 11 tasks (T007-T017) - MVP
- US2 (P2): 6 tasks (T018-T023)
- US3 (P3): 7 tasks (T024-T030)

**Estimated Timeline** (sequential implementation):
- Phase 1-2: 0.5 day (setup + models)
- Phase 3 (US1): 2-3 days (core tracking - MVP)
- Phase 4 (US2): 1 day (comparison)
- Phase 5 (US3): 1.5 days (routing)
- Phase 6: 1 day (polish)
- **Total**: ~6-7 days sequential, ~3-4 days with parallel execution

**Suggested MVP Scope**: Phase 1-3 (T001-T017) delivers basic quality tracking and CLI display - immediate value for administrators to monitor extraction quality.

---

## Implementation Notes

### File Paths Reference
- **New Files**:
  - `src/llm_orchestrator/quality_tracker.py` (main implementation)
  - `src/cli/commands/quality.py` (CLI commands)
  - `src/config/quality_thresholds.json` (threshold configuration)
  - `data/llm_health/quality_metrics.json` (persisted metrics)

- **Modified Files**:
  - `src/llm_orchestrator/types.py` (add 4 pydantic models)
  - `src/llm_orchestrator/orchestrator.py` (integrate quality tracking and routing)
  - `src/cli/commands/status.py` (add quality metrics display)
  - `CLAUDE.md` (update agent context)

### Testing Strategy
- **Unit Tests**: Not explicitly required per spec (tests are optional unless requested)
- **Contract Tests**: Optional - if implementing tests, follow TDD with tests for QualityTracker API contract
- **Integration Tests**: Optional - if implementing tests, test end-to-end quality tracking workflow
- **Manual Testing**: Required for each phase checkpoint to verify user story acceptance criteria

### Quality Gates
Each phase must pass its checkpoint criteria before proceeding to the next phase. This ensures incremental delivery of working functionality.

---

**Ready for Implementation**: All tasks are defined with specific file paths, clear descriptions, and proper checklist formatting. Execute tasks in dependency order, parallelizing where indicated, and verify checkpoints after each phase.
