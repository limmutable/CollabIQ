# Research: MVP End-to-End Testing & Error Resolution

**Feature**: 008-mvp-e2e-test
**Date**: 2025-11-04
**Status**: Complete

## Overview

This document consolidates research findings for implementing end-to-end testing of the MVP pipeline. The primary unknown was test database setup strategy to avoid polluting production Notion data.

## Research Tasks

### 1. Test Database Setup Strategy

**Question**: How should we handle Notion database writes during E2E testing to avoid polluting production data?

**Decision**: Use production database with manual cleanup after tests (Option A)

**Rationale**:
- Simpler approach - no need to maintain separate test database or keep schemas in sync
- Tests run against real production schema, catching any schema drift issues immediately
- Manual cleanup is acceptable for development/testing workflow
- Cleanup script with confirmation prompts mitigates risk of accidental data deletion

**Implementation Approach**:
1. Use production "CollabIQ" database for all E2E testing (no separate test database)
2. Tag all test entries with email_id from test email set
3. After test runs complete, use cleanup script `scripts/cleanup_test_entries.py` to delete test entries
4. Cleanup script filters by email_id list (only deletes entries matching test emails)
5. Cleanup script requires explicit user confirmation before deletion
6. All deletions logged to audit trail file

**Safety Measures**:
- Cleanup script only deletes entries where email_id matches test email list
- Explicit confirmation prompt before any deletion
- Dry-run mode available to preview what would be deleted
- Idempotent operation (can be safely re-run if interrupted)
- Logs all deleted entry IDs for audit trail

**Alternatives Considered**:
- **Option B (originally chosen): Separate test database**: Rejected due to maintenance overhead (keeping two databases in sync, schema changes must be replicated), and doesn't test against actual production schema
- **Option C: Mock Notion API entirely**: Rejected because this defeats the purpose of end-to-end validation - we need to test real API interactions including rate limits, schema changes, and network errors
- **Option D: Create/delete temporary database for each test run**: Rejected because Notion API doesn't support programmatic database creation, and database schema setup is manual/tedious

**Trade-offs Accepted**:
- Risk: Failed tests may leave orphaned entries (mitigated by cleanup script can be re-run)
- Risk: Manual cleanup step required (mitigated by automated script with confirmation)
- Risk: Potential for accidental deletion (mitigated by email_id filtering and confirmation prompts)
- Benefit: No schema synchronization overhead
- Benefit: Tests validate against actual production schema

---

### 2. Error Categorization Best Practices

**Question**: What severity levels and categorization scheme should we use for error reporting?

**Decision**: Four-tier severity system (Critical, High, Medium, Low) with explicit definitions

**Rationale**:
- Industry-standard approach used in bug tracking systems (JIRA, Linear, GitHub Issues)
- Clear priority for fixing: Critical + High must be fixed, Medium + Low can be deferred
- Aligns with spec requirements (FR-010, FR-011: fix critical/high only)

**Severity Definitions**:

| Severity | Definition | Examples | Action Required |
|----------|------------|----------|-----------------|
| **Critical** | Blocks pipeline from completing or causes data loss | API authentication failure, unhandled exception crashing process, data corruption in Notion | Fix immediately (blocking) |
| **High** | Causes incorrect data in Notion or frequent failures (>10% of emails) | Korean text encoding errors, date parsing failures, company matching returning wrong IDs | Fix before feature completion |
| **Medium** | Causes occasional failures (<10% of emails) or degrades user experience | Edge case date formats not handled, ambiguous company names not resolved, slow performance (>10s) | Document and defer to future work |
| **Low** | Minor issues that don't affect correctness | Verbose logging, suboptimal error messages, missing progress indicators | Document and defer indefinitely |

**Frequency Thresholds**:
- If an error occurs in >25% of test emails → Escalate severity by one level (Medium → High, High → Critical)
- If an error occurs in <5% of test emails → Severity capped at Medium (even if impact is high)

**Alternatives Considered**:
- **Option A: Five-tier system (Blocker, Critical, Major, Minor, Trivial)**: Rejected as over-complex for MVP scope - four tiers sufficient
- **Option B: Two-tier system (Blocking, Non-blocking)**: Rejected as too coarse - doesn't help prioritize non-blocking issues

---

### 3. Performance Metrics Collection

**Question**: What performance metrics should we collect, and how should we instrument the pipeline?

**Decision**: Per-stage timing with Python's time.perf_counter(), aggregate statistics, and percentile reporting

**Rationale**:
- Python's `time.perf_counter()` is the recommended way to measure elapsed time (monotonic clock, high resolution)
- Per-stage timing identifies bottlenecks (which stage is slow?)
- Aggregate statistics (mean, median, p95, p99) reveal patterns across multiple emails
- Simple decorator-based instrumentation minimizes code changes

**Metrics to Collect**:

Per Email:
- Total pipeline time (start to finish)
- Per-stage time (reception, extraction, matching, classification, write)
- API call count (Gemini calls, Notion calls)
- Gemini token usage (input tokens, output tokens)
- Success/failure status per stage

Aggregate (across all test emails):
- Success rate per stage (% of emails successfully processed)
- Average/median/p95/p99 times per stage
- Total API costs (Gemini tokens * pricing)
- Error frequency by type

**Implementation Approach**:
```python
# Decorator for timing
@track_performance(stage="extraction")
def extract_entities(email):
    # existing code
    pass

# Context manager for API tracking
with api_tracker.track_call("gemini"):
    response = gemini_client.generate(...)
```

**Alternatives Considered**:
- **Option A: Use external profiling tool (cProfile, py-spy)**: Rejected as overkill - we need pipeline-level metrics, not line-by-line profiling
- **Option B: Manual timing with print statements**: Rejected as not reusable and hard to aggregate
- **Option C: Full observability stack (Prometheus, Grafana)**: Rejected as out of scope for Phase 008 - defer to production monitoring (Phase 3+)

**Output Format**: JSON files with structured metrics for easy analysis and visualization

---

### 4. Test Data Selection Strategy

**Question**: How should we select test emails for validation?

**Decision**: Use ALL available real emails from collab@signite.co inbox

**Rationale**:
- Currently fewer than 10 emails available in the inbox
- Testing with all real production emails provides authentic validation
- No need for sampling strategy with small dataset
- Real emails contain actual production data patterns and edge cases

**Selection Strategy**:

Use All Available Emails (<10 currently):
- Fetch ALL emails from collab@signite.co inbox
- No filtering or sampling needed with small dataset
- Each email represents actual production use case
- Sufficient for MVP validation before Phase 2e

**Alternatives Considered**:
- **Option A: Stratified sampling (40) + manual selection (10)**: Rejected because we don't have 50+ emails currently. Over-engineering for small dataset.
- **Option B: Synthetic test data**: Rejected because we need to validate with real-world data complexity
- **Option C: Wait until more emails accumulate**: Rejected because we can proceed with MVP validation using available emails

**Implementation**: Email selection script fetches all emails from inbox and saves metadata to `data/e2e_test/test_email_ids.json`

**Future Consideration**: When more emails accumulate (50+), can implement stratified sampling for more comprehensive testing

---

### 5. Korean Text Encoding Validation

**Question**: How do we verify Korean text is preserved correctly throughout the pipeline?

**Decision**: Character-level comparison between input email and final Notion entry with explicit UTF-8 validation

**Rationale**:
- Korean text corruption (mojibake) is a common issue in multi-stage pipelines
- UTF-8 is the standard encoding, but mishandling at any stage causes corruption
- Character-level comparison detects subtle issues (e.g., normalization forms, whitespace changes)

**Validation Approach**:

For each test email:
1. Extract Korean text from original email (담당자, 스타트업명, 협업기관, 요약)
2. Retrieve corresponding Notion entry after pipeline completes
3. Compare character-by-character (exact match required)
4. Check for common mojibake patterns (e.g., "한글" → "í•œê¸€")
5. Verify UTF-8 encoding at each stage (email → JSON → Gemini API → Notion API)

**Test Cases**:
- Standard Korean Hangul characters (가-힣)
- Korean punctuation (、。！？)
- Mixed Korean + English text
- Korean with emojis (브레이크앤컴퍼니 🚀)
- Traditional Chinese characters sometimes used in Korean text (漢字)

**Alternatives Considered**:
- **Option A: Visual inspection only**: Rejected as not scalable and error-prone
- **Option B: Fuzzy matching (allow minor differences)**: Rejected because even minor differences indicate encoding bugs
- **Option C: Check only that text "looks Korean"**: Rejected as too coarse - corruption can be subtle

**Success Criteria**: 100% of Korean text fields match exactly between input and output (SC-007)

---

## Summary of Decisions

| Topic | Decision | Impact on Implementation |
|-------|----------|--------------------------|
| Test Database | Production database with manual cleanup (Option A) | Use existing `NOTION_DATABASE_ID_COLLABIQ`, cleanup script deletes test entries by email_id after tests |
| Error Severity | Four-tier system (Critical/High/Medium/Low) | Error collector categorizes all errors, report generator groups by severity |
| Performance Metrics | Per-stage timing with decorator/context manager | Instrument pipeline with `@track_performance` and `api_tracker.track_call()` |
| Test Data Selection | Use all available emails from inbox (<10 currently) | Email selection script creates `test_email_ids.json` with all emails from collab@signite.co |
| Korean Text Validation | Character-level comparison with UTF-8 checks | Validator compares input Korean text vs Notion entry character-by-character |

---

## Dependencies Identified

**External Services**:
- Gmail API (existing): Retrieve test emails
- Gemini API (existing): Entity extraction, company matching, classification
- Notion API (existing): Write test entries, retrieve for validation

**Python Packages** (all existing in project):
- pytest: Test framework
- pydantic: Data validation
- time: Performance timing (built-in)
- json: Metric/error output (built-in)

**Configuration**:
- New data directory: `data/e2e_test/` with subdirectories (runs/, errors/, metrics/, reports/)

**Manual Setup**:
- Run email selection script to populate `data/e2e_test/test_email_ids.json`
- After E2E tests complete, run cleanup script to remove test entries from production database

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Failed tests leave orphaned entries in production database | Medium | Medium | Cleanup script can be re-run idempotently; logs all deletions for audit trail |
| Accidental deletion of real production data | Low | Critical | Cleanup script filters by email_id from test set only; requires explicit confirmation before deletion; dry-run mode available |
| Test emails deleted from Gmail inbox | Low | Medium | Cache test email content locally after first retrieval |
| Rate limits hit during batch testing | Medium | Medium | Add configurable delay between emails (default 1 second), respect API rate limit headers |
| Korean text corruption during JSON serialization | Low | High | Force UTF-8 encoding on all JSON writes, verify with unit tests |
| Long-running tests time out | Low | Low | Add configurable timeout per email (default 30 seconds), skip slow emails and flag for investigation |

---

## Next Steps (Phase 1)

With research complete, proceed to:
1. **data-model.md**: Define Error Record, Performance Metric, Test Run entities
2. **contracts/**: Define test harness interfaces (ErrorCollector, PerformanceTracker, ReportGenerator, Validator)
3. **quickstart.md**: Step-by-step instructions for running E2E tests

**Blockers Resolved**: Test database strategy is now clear, no remaining NEEDS CLARIFICATION items.
