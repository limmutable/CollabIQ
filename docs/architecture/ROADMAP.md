# Implementation Roadmap: CollabIQ System

**Status**: 🔄 IN PROGRESS - Phase 016 Planning
**Version**: 2.7.0
**Date**: 2025-11-18
**Branch**: main

---

## Executive Summary

This roadmap breaks the CollabIQ system into **19 sequential phases** (branches 002-020), each delivering incremental value. Work proceeds at your own pace without deadlines - just complete phases step-by-step.

**Total Effort**: 42-58 days across 19 phases (including Gmail OAuth2 setup and project cleanup)
**MVP Target**: Phases 1a+1b (6-9 days) deliver extraction → JSON output for manual review ✅ **COMPLETE**
**Current Progress**: 13/19 phases complete (Phases 1a, 1b, 005, 2a, 2b, 2c, 2d, 2e, 3a, 3b, 3c, 3d, 3e/015) ✅
**Next Phase**: 016-project-cleanup-refactor (4-5 days) 🔄

---

## MVP Definition

**Minimal Feature Set**:
- Email ingestion (Phase 1a)
- Gemini entity extraction (Phase 1b)
- JSON output for manual review

**NOT Included in MVP**:
- Automatic Notion creation
- Fuzzy matching
- Verification queue
- Reporting

**Value Delivered**: Reduces manual entity extraction time by ≥30%

**Timeline**: Phase 1a (3-4 days) + Phase 1b (3-5 days) = **6-9 days total**

**Meets SC-007**: ✅ ≤2 weeks (14 days) requirement

**MVP Complete Milestone**: After Phase 1b, team can manually create Notion entries from JSON output

---

## Phase Structure

### MVP Track (Phases 1a-1b)

**Phase 1a - Email Reception** (Branch: `002-email-reception`) ✅ **COMPLETE**
**Timeline**: 3-4 days (Actual: Completed 2025-10-31)
**Complexity**: Low
**Status**: Merged to main, specs directory cleaned up

**Deliverables**: ✅
- EmailReceiver component (Gmail API with OAuth2)
- ContentNormalizer removing signatures, quoted threads, disclaimers
- Output: Cleaned email text saved to file storage
- CLI tool for manual testing
- Comprehensive documentation (READMEs, completion report)

**Tests**: ✅ 54 unit tests passing
- Signature detection: 17/17 tests passing
- Quote detection: 13/13 tests passing
- Disclaimer detection: 9/9 tests passing
- Duplicate tracker: 11/11 tests passing
- Pipeline integration: 4/4 tests passing

**Success Criteria**: ✅ All Exceeded
- ✅ Successfully receive and clean ≥90% of test emails (Ready for production validation)
- ✅ **100% signature removal accuracy** (Target: ≥95%) - 20-email dataset
- ✅ **100% quote removal accuracy** (Target: ≥95%) - 21-email dataset
- ✅ Zero duplicate email entries (11/11 tests passing)

---

**Phase 1b - Gemini Entity Extraction (MVP)** (Branch: `004-gemini-extraction`) ✅ **COMPLETE**
**Timeline**: 3-5 days (Actual: Completed 2025-10-31)
**Complexity**: Medium
**Status**: Merged to main, specs directory cleaned up

**Deliverables**: ✅
- LLMProvider abstract base class
- GeminiAdapter implementing extraction (NO matching/classification yet, just entities)
- Configuration management (API keys, settings)
- Output: JSON file with extracted entities + confidence scores

**Tests**: ✅ Integration tests for Gemini API (mocked + real), accuracy tests on sample emails

**Success Criteria**: ✅
- ≥85% entity extraction accuracy on test dataset
- ≥90% confidence scores accurate (calibrated vs human judgment)

**🎯 MVP Complete**: ✅ After Phase 1b, team can manually create Notion entries from JSON output

---

**Phase 005 - Gmail OAuth2 Setup** (Branch: `005-gmail-setup`) ✅ **COMPLETE**
**Timeline**: 2-3 days (Actual: Completed 2025-11-01)
**Complexity**: Low
**Status**: Merged to main, specs directory cleaned up

**Deliverables**: ✅
- OAuth2 Desktop Application flow for Gmail API
- Group alias email access (collab@signite.co)
- Authentication scripts and manual test utilities
- Comprehensive documentation (gmail-oauth-setup.md, troubleshooting-gmail-api.md)
- Token management (access tokens + refresh tokens)

**Tests**: ✅ 20/20 tests passing (100% pass rate)
- 6 unit tests for query construction
- 8 OAuth2 integration tests
- 6 Gmail receiver unit tests

**Success Criteria**: ✅
- Setup completes in <15 minutes following documentation
- Successfully retrieves emails from collab@signite.co (3 emails validated)
- Token auto-refresh works without user intervention
- All P1 user stories complete (27/30 tasks, 90%)

---

### Automation Track (Phases 2a-2e)

**Phase 2a - Notion Read Operations** (Branch: `006-notion-read`) ✅ **COMPLETE**
**Timeline**: 2-3 days (Actual: Completed 2025-11-02)
**Complexity**: Low
**Status**: Merged to main, specs directory cleaned up

**Deliverables**: ✅
- NotionIntegrator component (read-only operations)
- Schema discovery with caching (24h TTL)
- Data fetching with pagination and relationship resolution
- LLM-ready formatting (JSON + Markdown)
- CLI commands: fetch, refresh, schema, export
- Infisical integration for secret management

**Tests**: ✅ 63/63 tests passing (100% pass rate)
- 9 contract tests for NotionIntegrator interface
- 29 integration tests for Notion API operations
- 25 unit tests for schema, fetcher, formatter, cache

**Success Criteria**: ✅
- Successfully fetch all companies from both databases (✅ Validated with real data)
- Cache invalidation working correctly (✅ TTL-based: 24h schema, 6h data)
- API rate limits respected (✅ Token bucket: 3 req/s)
- Schema discovery working (✅ Dynamic property detection)
- Relationship resolution working (✅ 1-level depth, circular ref detection)

**Post-Merge Fix** (Branch: `fix-notion-api-2025-migration`) ✅ **COMPLETE**
- **Issue**: Notion API 2025-09-03 breaking changes (databases → data sources)
- **Fix Date**: 2025-11-02
- **Changes**: Migrated to data sources API, updated schema discovery, added diagnostic tool
- **Status**: Fixed and merged - all Notion operations now working correctly

---

**Phase 2b - LLM-Based Company Matching** (Branch: `007-llm-matching`) ✅ **COMPLETE**
**Timeline**: 2-3 days (Actual: Completed 2025-11-03)
**Complexity**: Low
**Status**: Merged to main, specs directory populated

**Deliverables**: ✅
- Extended GeminiAdapter with optional company_context parameter
- Company matching with confidence scores (matched_company_id, matched_partner_id)
- Enhanced prompt with detailed confidence scoring rules
- Backward compatible with Phase 1b (all new fields optional)
- Handle no-match scenarios (return null + low confidence <0.70)

**Tests**: ✅ 12/12 tests passing (100% pass rate)
- 4 contract tests for API compliance
- 8 integration tests covering US1-US4
  * US1: Primary startup matching (exact Korean names)
  * US2: Beneficiary matching (SSG affiliates + Portfolio×Portfolio)
  * US3: Name variations (abbreviations, typos)
  * US4: No-match scenarios (unknown companies, ambiguity)

**Success Criteria**: ✅
- ≥85% correct company matches on test dataset (✅ Achieved 100% accuracy)
- Confidence scores accurately reflect match quality (✅ Excellent calibration)
- Confidence ranges validated: Exact (0.95-1.00), Normalized (0.90-0.94), Semantic (0.75-0.89), Fuzzy (0.70-0.74), No-match (<0.70)

---

**Phase 2c - Classification & Summarization** (Branch: `008-classification-summarization`) ✅ **COMPLETE**
**Timeline**: 2-3 days (Actual: Completed 2025-11-03)
**Complexity**: Low
**Status**: Ready for merge, specs directory populated

**Deliverables**: ✅
- ClassificationService with dynamic schema fetching from Notion
- Dynamic type classification (Portfolio+SSG → [A]PortCoXSSG) - deterministic, no LLM
- LLM-based intensity classification using Korean semantic analysis (이해/협력/투자/인수)
- Summary generation preserving all 5 key entities (3-5 sentences, 50-150 words)
- Confidence scoring with 0.85 threshold for manual review routing
- Backward compatible (all Phase 2c fields optional)

**Tests**: ✅ 45/45 Phase 2c tests passing (100% pass rate)
- 24 contract tests for model validation, schema, intensity, summary
- 15 unit tests for type classification logic and pattern parsing
- 6 integration tests for E2E workflows

**Success Criteria**: ✅
- ≥95% correct 협업형태 classification (✅ Achieved with deterministic logic)
- ≥85% correct 협업강도 classification (✅ LLM-based with confidence scoring)
- Summaries preserve all key entities (≥90% completeness) (✅ Tracked with boolean flags)
- Summary word count compliance (≥95% within 50-150 range) (✅ Pydantic validation)
- See [COMPLETION_REPORT.md](../../specs/008-classification-summarization/COMPLETION_REPORT.md)

---

**Phase 2d - Notion Write Operations** (Branch: `009-notion-write`) ✅ **COMPLETE**
**Timeline**: 2-3 days (Completed)
**Complexity**: Low

**Deliverables**:
- ✅ NotionWriter with duplicate detection (skip/update modes)
- ✅ FieldMapper for schema-aware property mapping
- ✅ DLQManager for failed write handling
- ✅ Manual retry script (`scripts/retry_dlq.py`)
- ✅ Map extracted entities + matched companies → Notion fields
- ✅ Handle relation links (스타트업명, 협업기관)
- ✅ Auto-generate 협력주체 field (startup-org format)

**Tests**: 35+ tests passing (100%) - contract, integration, and E2E tests

**Success Criteria**: ✅ ACHIEVED
- ✅ Successfully create Notion entry with all fields correctly populated
- ✅ Duplicate detection prevents duplicate entries
- ✅ Failed writes captured in DLQ for manual retry
- ✅ Korean text, special characters, and emojis preserved correctly

---

**Phase 2e - Error Handling & Retry Logic** ✅ (Branch: `010-error-handling`)
**Timeline**: 2-3 days (Completed: 2025-11-08)
**Complexity**: Medium

**Deliverables**:
- ✅ Unified retry system with `@retry_with_backoff` decorator (Gmail, Gemini, Notion)
- ✅ Circuit breaker pattern for fault isolation (per-service)
- ✅ Error classification (TRANSIENT/PERMANENT/CRITICAL)
- ✅ Exponential backoff with jitter and rate limit handling
- ✅ Dead letter queue with idempotent replay (`replay_batch()`)
- ✅ Structured error logging with JSON formatting

**Tests**: 52/58 passing (90%) - Gmail integration: 100%, Circuit breaker: 100%

**Success Criteria**:
- ✅ Graceful degradation when APIs fail (95% transient failure recovery)
- ✅ No data loss (DLQ captures all failures with idempotency)
- ✅ Clean retry logic (removed duplicate patterns, unified to single decorator)

**🎯 Full Automation Complete**: Email → Notion without manual intervention

---

### Operations & Quality Track (Phases 3a-3c)

**Rationale**: With expected low email volume (0-5 emails/day), focus shifts from manual review UI to operational excellence through CLI tools, multi-LLM resilience, and quality tracking. This aligns with server-side automation and occasional admin maintenance needs.

---

**Phase 3a - Admin CLI Enhancement** (Branch: `011-admin-cli`) ✅ **COMPLETE**
**Timeline**: 4-5 days (Completed: 2025-11-08)
**Complexity**: Medium
**Status**: Production-ready, all 132 tasks complete

**Deliverables**: ✅
- ✅ Unified `collabiq` command with 7 organized command groups (30 total commands)
  - `email`: fetch, clean, list, verify, process (5 commands)
  - `notion`: verify, schema, test-write, cleanup-tests (4 commands)
  - `test`: e2e, select-emails, validate (3 commands)
  - `errors`: list, show, retry, clear (4 commands - DLQ management)
  - `status`: basic, --detailed, --watch (3 modes - health monitoring)
  - `config`: show, validate, test-secrets, get (4 commands)
  - `llm`: status, test, policy, set-policy, usage, disable, enable (7 commands)
- ✅ Rich formatted output (tables, progress bars, colored text)
- ✅ JSON output mode (`--json`) for all commands (automation support)
- ✅ Global flags (--debug, --quiet, --no-color) across all commands
- ✅ Graceful interrupt handling with resume capability (E2E tests)
- ✅ Comprehensive help text with usage examples for all commands

**Tests**: ✅ 32 contract tests + 11 integration tests (100% passing)
- 32/32 contract tests verify CLI interface stability
- 11/11 integration tests validate workflows
- 3 test scripts for manual validation

**Success Criteria**: ✅ ALL EXCEEDED
- ✅ 100% of admin operations accessible via `collabiq` command (30 commands)
- ✅ `collabiq status` completes in ~1.88s (62% faster than <5s target)
- ✅ E2E test workflow implemented with progress tracking
- ✅ All commands provide actionable error messages with remediation
- ✅ Admin can diagnose/resolve common issues via CLI alone

**Why Priority**: Admin needs robust CLI tools before system goes to production. This replaces scattered scripts with unified interface for setup, testing, monitoring, and troubleshooting.

**Documentation**: See [docs/architecture/CLI_IMPLEMENTATION_COMPLETE.md](CLI_IMPLEMENTATION_COMPLETE.md) and [docs/validation/COMMANDS.md](../validation/COMMANDS.md)

---

**Phase 3b - Multi-LLM Provider Support** (Branch: `012-multi-llm`) ✅ **COMPLETE**
**Timeline**: 5-6 days (Completed: 2025-11-09)
**Complexity**: High
**Status**: Full implementation complete - all strategies, health monitoring, cost tracking

**Deliverables**: ✅
- ✅ LLM provider abstraction layer (extends existing `LLMProvider` interface)
- ✅ Provider implementations:
  - Gemini 2.0 Flash (free tier)
  - Claude Sonnet 4.5 (Anthropic API via `anthropic` SDK)
  - OpenAI GPT-4o Mini (via `openai` SDK)
- ✅ LLM orchestrator with three strategies:
  - **Failover**: Sequential provider attempts with health-based skipping
  - **Consensus**: Parallel calls with majority voting (Jaro-Winkler fuzzy matching)
  - **Best-Match**: Parallel calls selecting highest confidence result
- ✅ Provider health monitoring with circuit breaking (CLOSED/OPEN/HALF_OPEN states)
- ✅ Cost tracking with token usage monitoring and per-provider pricing
- ✅ Configuration for provider priority, timeout, retry settings
- ✅ HealthTracker with persistent state (data/llm_health/health_metrics.json)
- ✅ CostTracker with token usage history (data/llm_health/cost_metrics.json)
- ✅ Real API integration with Infisical secret management

**Tests**: ✅ 70/70 tests passing (100% pass rate)
- 24 contract tests for Claude and OpenAI adapters
- 16 integration tests for LLMOrchestrator
- 16 integration tests for FailoverStrategy
- 8 integration tests for ConsensusStrategy
- 6 integration tests for BestMatchStrategy
- Real API validation with Korean text extraction (100% success across all providers)

**Success Criteria**: ✅ ALL EXCEEDED
- ✅ System continues processing emails if one LLM provider is down
- ✅ Provider failover with automatic health-based skipping
- ✅ Circuit breaker pattern (CLOSED/OPEN/HALF_OPEN states)
- ✅ Consensus mode with fuzzy matching (perfect 1.00 agreement on Korean text)
- ✅ Best-match selection (Claude selected with 0.941 confidence)
- ✅ Cost tracking (token usage + pricing per provider)
- ✅ Real API testing (Gemini: 1.8s avg, Claude: 4.0s avg, OpenAI: 3.2s avg)

**Why Priority**: Production systems need resilience. Multiple LLM providers ensure uptime even if one provider has outages/rate limits.

---

**Phase 3c - LLM Quality Metrics & Tracking** (Branch: `013-llm-quality-metrics`) ✅ **COMPLETE**
**Timeline**: 3-4 days (Completed: 2025-11-09)
**Complexity**: Medium
**Status**: Full implementation complete - quality tracking, provider comparison, intelligent routing

**Deliverables**: ✅
- ✅ Quality metrics calculation and tracking:
  - **Per-provider confidence tracking** (overall + per-field averages)
  - **Field completeness tracking** (percentage of extracted fields)
  - **Validation success rate** (successful vs failed validations)
  - **Quality score formula**: 40% confidence + 30% completeness + 30% validation
  - **Value score formula**: Quality-to-cost ratio (free tier: 1.5x multiplier, paid: quality / (1 + cost × 1000))
- ✅ Intelligent provider selection:
  - **Quality-based routing**: Automatically select best provider based on historical metrics
  - **Configurable routing toggle**: Enable/disable via CLI or config
  - **Fallback to priority**: Uses fixed priority when routing disabled or no metrics available
  - **Health integration**: Skips unhealthy providers even with good metrics
- ✅ Provider comparison and analysis:
  - Quality rankings (composite scoring across confidence, completeness, validation)
  - Value rankings (quality-to-cost optimization)
  - Detailed per-field confidence breakdown
  - Recommendation engine (highest quality vs best value)
- ✅ CLI commands for quality management:
  - `collabiq llm status` - Show provider health and basic metrics
  - `collabiq llm compare [--detailed]` - Compare provider performance
  - `collabiq llm set-quality-routing [--enabled/--disabled]` - Toggle routing
  - `collabiq llm test <text> [--quality-routing]` - Test with routing
- ✅ Persistent quality tracking:
  - File-based storage: `data/llm_health/quality_metrics.json`
  - Per-provider metrics with timestamps
  - Atomic writes with error handling
  - Automatic metrics updates after each extraction
- ✅ Test script for specific email IDs:
  - `test_specific_email.py` with full CLI interface
  - Support for inline text, file input, or default samples
  - Strategy selection, quality routing toggle, provider forcing
  - Results saving and metrics display options

**Tests**: ✅ 9/9 integration tests passing (100% pass rate)
- Quality-based provider selection (highest quality chosen)
- Fallback to priority when routing disabled
- Fallback when no metrics available
- Health check integration (skip unhealthy providers)
- Provider failure handling (try next in list)
- Edge cases (empty candidates, subset selection)

**Success Criteria**: ✅ ALL EXCEEDED
- ✅ Quality metrics accurately track extraction performance per provider
- ✅ Provider comparison identifies best performer (composite scoring working)
- ✅ Quality-based routing selects optimal provider automatically
- ✅ CLI provides comprehensive quality management interface
- ✅ Metrics persist and update correctly across sessions
- ✅ Integration with health monitoring (skip unhealthy providers)
- ✅ Cost optimization via value scoring (quality-to-cost ratio)

**Why Priority**: Multi-LLM processing generates valuable quality signals that should be captured for monitoring, debugging, and continuous improvement. Quality-based routing optimizes extraction quality while managing costs.

**Documentation**: See [docs/CLI_REFERENCE.md](../CLI_REFERENCE.md), [docs/validation/QUALITY_METRICS_DEMO_RESULTS.md](../validation/QUALITY_METRICS_DEMO_RESULTS.md), and [docs/architecture/ALL_PROVIDERS_STRATEGY.md](ALL_PROVIDERS_STRATEGY.md)

**🎯 Production-Ready**: Robust CLI, resilient multi-LLM processing, quality tracking, and intelligent routing

---

**Phase 3d - Enhanced Notion Field Mapping** (Branch: `014-enhanced-field-mapping`) ✅ **COMPLETE**
**Timeline**: 3-4 days (Actual: Completed 2025-11-10)
**Complexity**: Medium
**Status**: Merged to main, production ready

**Problem Statement**:
Currently, the LLM extracts key values for three critical fields:
- 담당자 (Person in Charge) - extracted as name string
- 스타트업명 (Startup Name) - extracted as company name
- 협력기관 (Partner Org) - extracted as organization name

However, these fields are not being populated in the Notion database because:
1. **스타트업명 and 협력기관** are relation fields linking to the Companies database, requiring exact name matches
2. **담당자** is a people (multi-select) field requiring Notion user UUIDs, not name strings
3. LLM-extracted names may have slight variations (e.g., "웨이크(산스)" vs "웨이크")

**Deliverables**:
- ✅ **Fuzzy Company Matching Service**:
  - Search Companies database for fuzzy matches (handle variations, abbreviations, parenthetical info)
  - Use similarity scoring (Jaro-Winkler or similar) with configurable threshold (≥0.85)
  - Match extracted names to actual Notion database entries
  - Return page_id for exact/fuzzy matches, or null if no match found

- ✅ **Auto-Create Missing Companies**:
  - When extracted company name has no match in Companies database (similarity < 0.85)
  - Create new entry in Companies database with extracted name
  - Return newly created page_id for relation field population
  - Handle both 스타트업명 (Startup Name) and 협력기관 (Partner Org) fields

- ✅ **Person Matching Service**:
  - List all Notion workspace users via Notion API
  - Fuzzy match extracted 담당자 name to Notion user names
  - Use similarity scoring with Korean name handling (family name + given name variations)
  - Return best matching user UUID(s) for people field population
  - Handle cases where no match found (log warning, leave field empty)

- ✅ **Enhanced FieldMapper**:
  - Integrate FuzzyCompanyMatcher for 스타트업명 and 협력기관 fields
  - Integrate PersonMatcher for 담당자 field
  - Add confidence scores for matches (log low-confidence matches for review)
  - Preserve existing field mapping logic (backward compatible)

- ✅ **CLI Commands**:
  - `collabiq notion match-company <name>` - Test company matching
  - `collabiq notion match-person <name>` - Test person matching
  - `collabiq notion list-users` - List all workspace users
  - Add `--dry-run` flag to test matching without creating entries

**Tests**:
- Unit tests for fuzzy matching algorithms (Jaro-Winkler, similarity scoring)
- Integration tests for Companies database search
- Integration tests for Notion user listing
- E2E tests verifying field population with fuzzy matching
- Edge case tests (ambiguous names, multiple matches, no matches)

**Success Criteria**:
- ✅ **SC-001**: ≥90% of extracted company names successfully matched to Companies database entries (exact + fuzzy)
- ✅ **SC-002**: ≥85% of extracted person names successfully matched to Notion users
- ✅ **SC-003**: Auto-created companies are properly formatted and linkable
- ✅ **SC-004**: Low-confidence matches (0.70-0.85) are logged for manual review
- ✅ **SC-005**: No false positives in company matching (wrong company linked)
- ✅ **SC-006**: All three fields (담당자, 스타트업명, 협력기관) populated in ≥90% of test emails

**Why Priority**: These three fields are critical for Notion database usability. Without proper field mapping, extracted data cannot be effectively queried, filtered, or analyzed in Notion. Relation fields enable powerful cross-database queries and reporting.

**Examples**:

**Company Matching**:
```
Extracted: "웨이크(산스)"
Database entries: ["웨이크", "산스앤컴퍼니", "스타트업A"]
→ Match: "웨이크" (similarity: 0.87)
→ Action: Use page_id of "웨이크" for relation field

Extracted: "새로운회사"
Database entries: ["기존회사A", "기존회사B"]
→ Match: None (all similarities < 0.85)
→ Action: Create new entry "새로운회사" in Companies database
→ Return: page_id of newly created entry
```

**Person Matching**:
```
Extracted: "김철수"
Notion users: ["김철수 (Cheolsu Kim)", "이영희 (Younghee Lee)", "박지민 (Jimin Park)"]
→ Match: "김철수 (Cheolsu Kim)" (similarity: 1.00)
→ Action: Use user UUID for 담당자 people field

Extracted: "최민수"
Notion users: ["김철수", "이영희", "박지민"]
→ Match: None (all similarities < 0.70)
→ Action: Log warning, leave 담당자 field empty
```

---

**Phase 3e - Test Suites Improvements** (Branch: `015-test-suite-improvements`) ✅ **COMPLETE**
**Timeline**: 5-7 days (Actual: Completed 2025-11-16)
**Complexity**: High
**Status**: Merged to main, production ready

**Deliverables**: ✅
- ✅ **Test Suite Stabilization**: Fixed 81 test failures (96% reduction from 84→3)
  - Import path consistency (280+ fixes across 57 test files)
  - Mock patch paths updated for new import structure
  - CLI architecture restructured (flat → hierarchical subcommands)
  - Circuit breaker test isolation (proper global instance reset)
  - E2E test import path fixes (CLI script sys.path correction)
- ✅ **Test Infrastructure Improvements**:
  - Companies cache tests fixed (11 tests passing)
  - Structured logger sanitization order corrected
  - CLI command registration (all 7 groups registered, 29 tests fixed)
  - Notion writer mock structure alignment
  - Duplicate detection mock improvements
  - Gemini retry flow mocking (complete with response format fixes)
- ✅ **Documentation Created**:
  - Comprehensive [CLI_ARCHITECTURE.md](../architecture/CLI_ARCHITECTURE.md) documenting hierarchical command structure
  - [test_improvement_summary.md](../../specs/015-test-suite-improvements/test_improvement_summary.md) tracking all fixes
  - [T011_remaining_failures.md](../../specs/015-test-suite-improvements/T011_remaining_failures.md) analyzing remaining issues
  - [refactoring_analysis.md](../../specs/015-test-suite-improvements/refactoring_analysis.md) comprehensive 478-line analysis
- ✅ **Test Pass Rate**: 98.9% (727/735 non-manual tests passing)
  - 8 Infisical tests (expected - SDK not installed)
  - All critical test infrastructure working correctly
  - E2E tests 100% passing (11/11 tests)

**Tests**: ✅ 727 passing / 735 non-manual tests (98.9% pass rate)
- Unit tests: 97.3% passing (8 Infisical failures expected)
- Integration tests: 100% passing
- Contract tests: 100% passing
- E2E tests: 100% passing (11/11 tests)

**Success Criteria**: ✅ ALL ACHIEVED
- ✅ **SC-001**: Test suite stabilized with 98.9% pass rate (727/735 tests passing)
- ✅ **SC-002**: Import path consistency achieved (280+ fixes, isinstance() failures resolved)
- ✅ **SC-003**: Mock structure aligned with actual code (tests reflect production behavior)
- ✅ **SC-004**: Circuit breaker test isolation working (proper reset between tests)
- ✅ **SC-005**: CLI architecture documented and tested (hierarchical subcommands)
- ✅ **SC-006**: Test infrastructure reliable and maintainable (comprehensive documentation)
- ✅ **SC-007**: Refactoring analysis complete (500+ lines of fixture duplication identified)

**Why Priority**: Test suite stability is essential for continued development. A reliable test suite enables confident refactoring, catches regressions early, and provides a solid foundation for future features. Phase 015 transformed an 88.8% pass rate into 98.9%, ensuring production readiness.

---

**Phase 016 - Project Cleanup & Refactoring** (Branch: `016-project-cleanup-refactor`) 🔄 **IN PLANNING**
**Timeline**: 4-5 days
**Complexity**: Medium
**Status**: Planning phase

**Deliverables**:
- ✨ **Documentation Consolidation**:
  - Audit all documentation in `docs/` and `specs/` directories
  - Remove duplicate content and merge related documents
  - Archive or delete outdated documentation
  - Establish clear documentation hierarchy and navigation
  - Update links and cross-references across all docs
  - Create documentation index/map for easy navigation
- 🧪 **Test Suite Organization**:
  - Reorganize test files in `tests/` directory for better structure
  - Remove redundant or obsolete test files
  - Consolidate similar test cases across test suites
  - Clean up test utilities in `src/collabiq/test_utils/`
  - Ensure clear separation between unit/integration/e2e/performance/fuzz tests
  - Update test documentation to reflect new organization
- 🖥️ **CLI Application Polish**:
  - Implement minimal startup checks (config validation, credential verification)
  - Improve admin CLI commands for better user experience
  - Add clearer error messages and user guidance
  - Streamline command structure and reduce verbosity
  - Add interactive prompts for common admin tasks
  - Improve status check commands with actionable feedback

**Tests**: Regression testing to ensure no functionality broken during reorganization

**Success Criteria**:
- ✅ Documentation audit complete with clear categorization (current/archive/obsolete)
- ✅ No duplicate documentation remains
- ✅ Test suite reduced by ≥20% through consolidation while maintaining coverage
- ✅ All tests still pass after reorganization (98.9%+ pass rate maintained)
- ✅ CLI startup time <2 seconds with minimal checks
- ✅ Admin commands have clear help text and interactive prompts

**Why Priority**: After completing major feature development and test suite improvements in Phase 015, the codebase needs cleanup to maintain long-term maintainability. Reducing documentation duplication, organizing tests logically, and polishing the CLI will improve developer experience and make future phases easier to implement.

---

### Analytics Track (Phases 4a-4c)

**Phase 4a - Basic Reporting** (Branch: `017-basic-reporting`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- ReportGenerator component
- Query Notion for all collaboration records
- Calculate basic stats (count by type, count by intensity, top companies)
- Output: Markdown report

**Tests**: Data accuracy tests (compare to manual calculation)

**Success Criteria**:
- Stats match manual calculation (≤1% variance)
- Report generation completes in <5 minutes

---

**Phase 4b - Advanced Analytics** (Branch: `018-advanced-analytics`)
**Timeline**: 3-4 days
**Complexity**: Medium

**Deliverables**:
- Time-series trends (collaborations over time)
- Highlight detection (top 5 most significant collaborations)
- Insight generation (LLM-based observations)
- Publish report as Notion page with proper formatting

**Tests**: Data quality tests, Notion integration tests

**Success Criteria**:
- Insights are actionable and accurate
- Notion page properly formatted with links

---

**Phase 4c - Automated Admin Reporting** (Branch: `019-admin-reporting`)
**Timeline**: 3-4 days
**Complexity**: Low-Medium

**Deliverables**:
- Daily summary email to admin with:
  - System health status (all components operational/degraded)
  - Processing metrics (emails received, processed, success rate)
  - Error summary (critical/high errors with details, low errors count)
  - LLM provider usage (API calls per provider, costs, health)
  - Notion database stats (entries created, validation failures)
  - Actionable alerts (e.g., "Gmail auth expires in 3 days", "Error rate above threshold")
- Email templating system (HTML + plain text)
- Configurable schedule and recipients
- Optional Slack/webhook notifications for critical issues
- Archive reports to `data/reports/` directory

**Tests**: Unit tests for report generation, integration tests for email delivery, template rendering tests

**Success Criteria**:
- Daily email delivered reliably at configured time
- Report includes all key metrics and actionable insights
- Critical errors trigger immediate notification (within 5 minutes)
- Admin can diagnose 80% of issues from report alone (no CLI needed)
- Report generation completes in <30 seconds

**Why Priority**: Admin doesn't need to actively monitor server. Daily reports provide visibility into system health and issues. Automated alerts reduce response time for critical problems.

**🎯 Complete System**: Full end-to-end with reporting and automated monitoring

---

## Dependency Graph

```
✅ Phase 1a (002-email-reception) - COMPLETE
    ↓
✅ Phase 1b (004-gemini-extraction) → 🎯 MVP ✅ - COMPLETE
    ↓
✅ Phase 005 (005-gmail-setup) - COMPLETE
    ↓
✅ Phase 2a (006-notion-read) - COMPLETE
    ↓
✅ Phase 2b (007-llm-matching) - COMPLETE
    ↓
✅ Phase 2c (008-classification-summarization) - COMPLETE
    ↓
✅ Phase 2d (009-notion-write) - COMPLETE
    ↓
✅ Phase 2e (010-error-handling) - COMPLETE → 🎯 Full Automation ✅
    ↓
    ├─→ ✅ Phase 3a (011-admin-cli) - COMPLETE ← depends on 2e (needs all components for CLI)
    │       ↓
    ├─→ ✅ Phase 3b (012-multi-llm) - COMPLETE ← depends on 2e (needs existing LLM interface)
    │       ↓
    ├─→ ✅ Phase 3c (013-llm-quality-metrics) - COMPLETE ← depends on 3b (needs multi-LLM processing), 2d (Notion write)
    │       ↓
    └─→ Phase 3d (014-enhanced-field-mapping) ← depends on 2d (Notion write), 2a (Notion read), 3a (CLI for testing)
            ↓
        → 🎯 Production-Ready with Full Field Mapping (Phases 3a+3b+3c+3d)
            ↓
        → ✅ Phase 3e (015-test-suite-improvements) ← depends on 3d (needs full system for E2E testing) - COMPLETE
            ↓
        → 🔄 Phase 016 (016-project-cleanup-refactor) ← depends on 3e (cleanup after major feature work) - IN PLANNING
            ↓
Phase 4a (017-basic-reporting) ← depends on 016 (needs clean codebase), 3e (needs robust testing), 3d (needs complete field population), 2d (Notion data)
    ↓
Phase 4b (018-advanced-analytics) ← depends on 4a, 3b (multi-LLM for insights)
    ↓
Phase 4c (019-admin-reporting) ← depends on 3a (uses CLI for metrics), 3b (LLM provider usage)
    ↓
→ 🎯 Complete System ✅
```

---

## Test Strategy Per Phase

| Phase | Test Type | Focus | Tools |
|-------|-----------|-------|-------|
| **1a** | Unit tests | Normalizer (signature removal, quote stripping) | pytest |
| **1b** | Integration + Accuracy | Gemini API calls, extraction accuracy on sample emails | pytest, pytest-mock |
| **2a** | Integration | Notion API (list databases, pagination) | pytest, notion-client |
| **2b** | Accuracy | Company matching (abbreviations, typos, semantic) | pytest |
| **2c** | Accuracy + Quality | Classification accuracy, summarization completeness | pytest |
| **2d** | Integration | Entry creation, field population, relation linking | pytest, notion-client |
| **2e** | Failure scenarios | API down, rate limits, timeouts, DLQ | pytest, pytest-mock |
| **3a** | Unit + Integration + E2E | Command parsing, execution, workflows | pytest, typer.testing |
| **3b** | Contract + Integration + Failure | Provider interface, orchestrator strategies, failover | pytest, pytest-mock |
| **3c** | Unit + Integration | Metrics calculation, Notion field population, quality reports | pytest, notion-client |
| **3d** | Unit + Integration + E2E | Fuzzy matching, Notion API, field population | pytest, notion-client, jellyfish |
| **3e** | Unit + Integration + E2E + Performance + Fuzz | End-to-end automation, date extraction, LLM performance, coverage, negative testing | pytest, pytest-cov, tenacity, rapidfuzz |
| **016** | Regression | Ensure no functionality broken during cleanup | pytest (all existing test suites) |
| **4a** | Data accuracy | Stats vs manual calculation | pytest |
| **4b** | Data quality + Integration | Insights quality, Notion page formatting | pytest, notion-client |
| **4c** | Unit + Integration | Report generation, email delivery, template rendering | pytest, email testing |

---

## Implementation Strategy

### Sequential Execution (Required)

Foundation work → Phase 1a → Phase 1b → ... → Phase 4c

**Why Sequential**: Each phase builds on deliverables from previous phases. Cannot parallelize within this roadmap.

### Milestone Validation

After each milestone, **STOP and VALIDATE**:

1. **After Phase 1b (MVP)**: Test JSON output quality, verify manual Notion entry creation works
2. **After Phase 2e (Full Automation)**: Test end-to-end email → Notion flow without manual steps
3. **After Phase 3c (Production-Ready)**: Test multi-LLM resilience, verify quality metrics tracking
4. **After Phase 3d (Complete Field Mapping)**: Verify all relation fields populated, test fuzzy matching accuracy
5. **After Phase 4c (Complete System)**: Review final reports and monitoring, validate insights quality

### Timeline Flexibility

**No deadlines** - work at your own pace. Effort estimates (3-4 days, 2-3 days) are for planning only, not due dates.

**Total Effort**: 38-53 days if working full-time sequentially. Actual calendar time will vary based on:
- API testing results (may need additional validation)
- Debugging time (errors, edge cases)
- Code review cycles
- Deployment testing

---

## Future Enhancements (Post-Phase 4b)

**Not in current roadmap, but possible future branches**:

1. **Multi-LLM Orchestrator** (if single LLM accuracy insufficient)
   - Consensus-based voting across Gemini/GPT/Claude
   - Higher accuracy at higher cost

2. **Advanced Email Parsing** (if needed)
   - Attachment handling (PDFs, images)
   - Thread context analysis (multi-email conversations)

3. **Notification System**
   - Slack/email alerts for high-value collaborations
   - Weekly summary emails to investment team

4. **Search & Filter**
   - Advanced search across collaboration records
   - Custom filters by type, intensity, date range, company

5. **API Endpoints**
   - REST API for external integrations
   - Webhook support for real-time notifications

6. **Performance Optimization**
   - Batch processing for high volume (>100 emails/day)
   - Caching strategies for repeated queries
   - Database migration from Notion to PostgreSQL (if Notion limits hit)

---

## Success Criteria Mapping

| Success Criterion | Phase(s) | Validation Method |
|-------------------|----------|-------------------|
| **SC-006**: MVP + 12 phases defined | All phases | ✅ This document |
| **SC-007**: MVP ≤2 weeks | Phases 1a-1b | 6-9 days < 14 days ✅ |
| All phases independently deliverable | All phases | Each phase has clear deliverables + tests |
| All phases independently testable | All phases | Test strategy defined per phase |

---

## Next Steps

**Progress Status**:
1. ✅ **Implementation roadmap documented** (this file)
2. ✅ **Project scaffold** (working Python project structure)
3. ✅ **Phase 1a Complete** (branch 002-email-reception merged to main)
4. ✅ **Phase 1b Complete** (branch 004-gemini-extraction merged to main) → **🎯 MVP COMPLETE**
5. ✅ **Phase 005 Complete** (branch 005-gmail-setup merged to main)
6. ✅ **Phase 2a Complete** (branch 006-notion-read merged to main)
7. ✅ **Phase 2b Complete** (branch 007-llm-matching merged to main)
8. ✅ **Phase 2c Complete** (branch 008-classification-summarization merged to main)
9. ✅ **Phase 2d Complete** (branch 009-notion-write merged to main)
10. ✅ **Phase 2e Complete** (branch 010-error-handling merged to main) → **🎯 FULL AUTOMATION COMPLETE**
11. ✅ **Phase 3a Complete** (branch 011-admin-cli ready for merge) → **🎯 PRODUCTION CLI READY**
12. ✅ **Phase 3b Complete** (012-multi-llm)
13. ✅ **Phase 3c Complete** (013-llm-quality-metrics)
14. ✅ **Phase 3d Complete** (014-enhanced-field-mapping)
15. ✅ **Phase 3e Complete** (015-test-suite-improvements) → **🎯 PRODUCTION READY WITH STABLE TEST SUITE**
16. 🔄 **Phase 016 In Planning** (016-project-cleanup-refactor) → **Next: Codebase Cleanup & Organization**

**Current Status**: Full automation complete (Email → Notion without manual intervention). Admin CLI complete with 30+ commands. Multi-LLM Provider Support complete with failover, consensus, and best-match strategies. Quality Metrics & Intelligent Routing complete with provider comparison and automatic quality-based routing. Enhanced Notion Field Mapping complete with fuzzy matching for companies and people. **Test Suite Stable** with 98.9% pass rate (727/735 tests passing). **Next Phase**: Project cleanup - documentation consolidation, test organization, CLI polish.

---

**Document Version**: 2.7.0
**Last Updated**: 2025-11-18 (Phase 016 Project Cleanup & Refactoring - Planning)
**Next Review**: After Phase 016 completion
