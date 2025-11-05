# Feature Specification: MVP End-to-End Testing & Error Resolution

**Feature Branch**: `008-mvp-e2e-test`
**Created**: 2025-11-04
**Status**: Draft
**Input**: User description: "create a branch MVP-end-to-end test to test and fix errors for end-to-end MVP test before we proceed to Phase 2e and forward."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Pipeline Validation (Priority: P1)

As a developer preparing for Phase 2e, I need to verify that the entire MVP pipeline (email reception → entity extraction → company matching → classification → Notion write) works end-to-end with real data, so that I can identify and fix any integration issues before building additional features.

**Why this priority**: This is the foundation for all future work. If the core pipeline has bugs or integration issues, any features built on top (Phase 2e+) will inherit those problems. Catching errors now prevents compounding technical debt.

**Independent Test**: Can be fully tested by running the complete pipeline with a sample of real emails from collab@signite.co and verifying that correctly formatted entries appear in the Notion CollabIQ database. Delivers immediate value by confirming MVP readiness.

**Acceptance Scenarios**:

1. **Given** the system has valid credentials for Gmail, Gemini, and Notion APIs, **When** an end-to-end test is executed with 10 real emails from collab@signite.co, **Then** all 10 emails are successfully processed through all pipeline stages without errors.

2. **Given** a test email contains typical collaboration data (Korean names, dates, company names), **When** the email is processed end-to-end, **Then** a Notion entry is created with all required fields populated correctly (담당자, 스타트업명, 협업기관, 날짜, 협업형태, 협업강도, 요약).

3. **Given** the pipeline encounters an error at any stage, **When** the error occurs, **Then** the error is logged with full context (email_id, stage, error details) and the email is added to the appropriate DLQ for later retry.

4. **Given** duplicate emails are processed, **When** the duplicate detection runs, **Then** duplicates are correctly identified and handled according to the configured duplicate behavior (skip or update).

---

### User Story 2 - Error Identification & Prioritization (Priority: P1)

As a developer, I need to identify all errors, edge cases, and data quality issues in the current MVP implementation, categorized by severity and impact, so that I can prioritize fixes before moving to Phase 2e.

**Why this priority**: Equal priority to P1 because error identification is the prerequisite for fixing. We need a comprehensive catalog of issues before we can address them effectively.

**Independent Test**: Can be tested by running the pipeline with diverse real-world emails (various formats, edge cases, Korean/English mix) and collecting all errors, warnings, and unexpected behaviors. Delivers value by creating a clear action plan for fixes.

**Acceptance Scenarios**:

1. **Given** the pipeline is run with 50+ diverse real emails, **When** all emails are processed, **Then** all errors are captured in a categorized error report with severity levels (critical, high, medium, low).

2. **Given** an error occurs during processing, **When** the error is logged, **Then** the log includes enough context to reproduce the issue (email_id, input data, stack trace, affected component).

3. **Given** multiple errors are identified, **When** errors are categorized, **Then** each error is assigned a severity level based on: frequency (how often it occurs), impact (does it block processing?), and data quality (does it corrupt results?).

4. **Given** edge cases are discovered (unusual date formats, missing fields, ambiguous company names), **When** these cases are documented, **Then** each edge case includes the email_id, input data, expected behavior, and actual behavior.

---

### User Story 3 - Critical Error Resolution (Priority: P2)

As a developer, I need to fix all critical and high-severity errors identified in User Story 2, so that the MVP pipeline can reliably process typical collaboration emails without failures.

**Why this priority**: Secondary to identification because we need to know what's broken before we can fix it. However, this must be completed before Phase 2e to ensure a stable foundation.

**Independent Test**: Can be tested by re-running the end-to-end pipeline with the same test dataset after fixes are applied, and verifying that critical/high-severity errors no longer occur. Delivers value by achieving stable MVP operation.

**Acceptance Scenarios**:

1. **Given** a critical error was identified (e.g., API authentication failure, schema mismatch), **When** the fix is applied, **Then** the error no longer occurs when processing the same input data.

2. **Given** a high-severity error was identified (e.g., Korean text encoding issue, date parsing failure), **When** the fix is applied, **Then** the affected component correctly handles the previously problematic input.

3. **Given** all critical/high-severity errors have been fixed, **When** the full test dataset is re-processed, **Then** the success rate improves to ≥95% (only medium/low-severity issues remain).

4. **Given** a fix is applied to one component, **When** the fix is tested, **Then** the fix does not introduce new errors in other components (regression testing).

---

### User Story 4 - Performance & Resource Validation (Priority: P3)

As a developer, I need to measure the pipeline's performance characteristics (processing time, API call volume, token usage, memory consumption) to establish baselines and identify bottlenecks before scaling to Phase 2e.

**Why this priority**: Lower priority because functional correctness (P1-P2) is more important than optimization. However, understanding performance now helps prevent costly refactoring later if we discover major bottlenecks.

**Independent Test**: Can be tested by instrumenting the pipeline with timing and resource tracking, processing a representative batch of emails, and collecting performance metrics. Delivers value by identifying optimization opportunities.

**Acceptance Scenarios**:

1. **Given** the pipeline is instrumented with performance tracking, **When** 50 emails are processed, **Then** performance metrics are collected for each stage (email reception, extraction, matching, classification, write).

2. **Given** performance data is collected, **When** metrics are analyzed, **Then** a performance baseline is established showing: average processing time per email, API calls per email, Gemini token usage per email, and memory consumption.

3. **Given** performance bottlenecks are identified (stages taking >5 seconds), **When** bottlenecks are documented, **Then** each bottleneck is analyzed to determine if it's due to API latency, inefficient code, or data volume.

4. **Given** the current MVP architecture, **When** performance metrics are reviewed, **Then** potential scaling issues are identified (e.g., sequential processing limiting throughput, cache miss rates, API rate limits).

---

### Edge Cases

- **What happens when the Gmail API returns partial email data** (e.g., missing body, incomplete headers)?
  - System should handle gracefully, log the issue, and add to DLQ with enough context for manual review

- **What happens when Gemini extraction returns low-confidence results** across all fields?
  - System should route to manual review queue if average confidence is below threshold (e.g., <0.50)

- **What happens when company matching finds multiple high-confidence matches** (tie scenarios)?
  - System should use configured tie-breaking logic (highest confidence, most recent match, or route to manual review)

- **What happens when the Notion API schema changes** during processing (field renamed, new required field added)?
  - System should detect schema mismatch, add to DLQ with schema error details, and notify via logs/alerts

- **What happens when processing large batches of emails** (50+ emails in one run)?
  - System should track progress, handle partial failures gracefully, and allow resuming from last successful email

- **What happens when Korean text contains special characters** (emojis, traditional Chinese characters, unusual punctuation)?
  - System should preserve all Unicode characters through the entire pipeline without corruption

- **What happens when dates are ambiguous or missing** in the email content?
  - System should fall back to email received date with a flag indicating date source uncertainty

- **What happens when the pipeline is interrupted mid-processing** (system crash, user cancellation)?
  - System should track processing state, avoid duplicate processing on restart, and cleanly resume from interruption point

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute the complete MVP pipeline (email reception → entity extraction → company matching → classification/summarization → Notion write) with a configurable set of test emails from collab@signite.co.

- **FR-002**: System MUST provide an end-to-end test script or command that processes real emails through all pipeline stages and reports success/failure for each email.

- **FR-003**: System MUST collect and categorize all errors, warnings, and unexpected behaviors encountered during end-to-end testing, with severity levels (critical, high, medium, low).

- **FR-004**: System MUST log sufficient context for each error to enable reproduction and debugging (email_id, input data, stage where error occurred, stack trace, error message).

- **FR-005**: System MUST verify data integrity at each pipeline stage by comparing output against expected schema and data quality rules (e.g., non-empty required fields, valid date formats, Korean text not corrupted).

- **FR-006**: System MUST validate that Notion entries created during testing contain correctly formatted data in all required fields (담당자, 스타트업명, 협업기관, 날짜, 협업형태, 협업강도, 요약).

- **FR-007**: System MUST test duplicate detection by processing the same email multiple times and verifying that only one Notion entry is created (or existing entry is updated per configuration).

- **FR-008**: System MUST measure and report performance metrics for each pipeline stage (processing time, API call count, token usage, success rate).

- **FR-009**: System MUST identify and document all critical and high-severity errors that block successful processing or cause data corruption.

- **FR-010**: System MUST fix all identified critical errors (those that prevent pipeline from completing or cause data loss) before completing this feature.

- **FR-011**: System MUST fix all identified high-severity errors (those that cause incorrect data in Notion or frequent failures) before completing this feature.

- **FR-012**: System MUST provide a test summary report showing: total emails processed, success rate by stage, error breakdown by severity, performance metrics, and list of remaining known issues (medium/low severity).

- **FR-013**: System MUST validate that all existing unit, integration, and contract tests continue to pass after any fixes are applied (regression protection).

- **FR-014**: System MUST handle edge cases gracefully (partial email data, low-confidence extractions, schema mismatches, special characters) without crashing the pipeline.

- **FR-015**: System MUST provide a clean way to run end-to-end tests without polluting production Notion databases (test database configuration or data cleanup mechanism).

### Key Entities

- **End-to-End Test Run**: Represents a single execution of the complete pipeline with a set of test emails. Key attributes:
  - Test run ID (timestamp-based)
  - Number of emails processed
  - Success/failure count per stage
  - Performance metrics (total time, average time per email)
  - List of errors encountered
  - Configuration used (test/production APIs, database IDs)

- **Error Record**: Represents a single error or unexpected behavior discovered during testing. Key attributes:
  - Severity level (critical, high, medium, low)
  - Component/stage where error occurred
  - Email ID (reference to input data)
  - Error message and stack trace
  - Input data snapshot
  - Timestamp
  - Resolution status (open, fixed, deferred)

- **Performance Metric**: Represents timing and resource usage data for a pipeline stage. Key attributes:
  - Stage name (reception, extraction, matching, classification, write)
  - Email ID
  - Processing time (seconds)
  - API call count
  - Token usage (for Gemini calls)
  - Memory consumption
  - Success/failure status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The end-to-end pipeline successfully processes ≥95% of a diverse test dataset (50+ real emails) without critical or high-severity errors.

- **SC-002**: All Notion entries created during testing contain correctly formatted data in all required fields, with 100% accuracy for successfully processed emails.

- **SC-003**: All critical errors (those preventing pipeline completion or causing data loss) are identified, fixed, and verified within this feature branch.

- **SC-004**: All high-severity errors (those causing incorrect data or frequent failures) are identified, fixed, and verified within this feature branch.

- **SC-005**: Error logs provide enough context to reproduce 100% of identified issues (email_id, input data, stack trace available).

- **SC-006**: Duplicate detection correctly identifies and handles 100% of duplicate test cases (same email processed multiple times).

- **SC-007**: Korean text (담당자, 스타트업명, 협업기관, 요약) is preserved without encoding errors or corruption in 100% of Notion entries.

- **SC-008**: The pipeline processes a typical collaboration email (entity extraction through Notion write) in ≤10 seconds on average (excluding network latency).

- **SC-009**: All existing tests (unit, integration, contract) continue to pass after fixes are applied, ensuring no regressions are introduced.

- **SC-010**: Performance metrics establish clear baselines for each pipeline stage (reception: X seconds, extraction: Y seconds, etc.) to guide future optimization.

## Assumptions

1. **Test Data Availability**: There are sufficient real emails in collab@signite.co inbox to create a diverse test dataset (50+ emails with various formats, edge cases, and collaboration types).

2. **API Stability**: Gmail, Gemini, and Notion APIs are generally stable during testing. Transient API errors (rate limits, timeouts) will be retried but are not considered bugs in the MVP pipeline.

3. **Test Environment**: A test Notion database (separate from production) is available for end-to-end testing, or there is a mechanism to clean up test data from the production database.

4. **Scope Boundary**: This feature focuses on the current MVP pipeline (Phases 1a, 1b, 2a, 2b, 2c, 2d). Issues in components not yet implemented (Phase 2e+) are out of scope.

5. **Medium/Low Severity Errors**: Not all errors need to be fixed in this feature. Medium and low-severity errors can be documented and deferred to future work if they don't significantly impact MVP functionality.

6. **Performance Targets**: Current performance targets (≤10 seconds per email) are based on single-user usage. Performance optimization for concurrent processing and high volume is deferred to Phase 3+.

7. **Manual Review Queue**: If ambiguous or low-confidence cases are discovered, they can be handled via existing DLQ mechanism. A formal manual review UI (Phase 3) is not required for this feature.

8. **Existing Test Coverage**: Unit and integration tests already cover individual components. This feature focuses on discovering integration issues and edge cases not covered by existing tests.

## Dependencies

- **All MVP Phases Complete**: Phases 1a (email reception), 1b (entity extraction), 005 (Gmail setup), 2a (Notion read), 2b (company matching), 2c (classification), and 2d (Notion write) must be implemented and merged.
- **Real Email Access**: Gmail API access to collab@signite.co with a sample of real collaboration emails.
- **Test Notion Database**: A Notion database (test or production) where test entries can be created and inspected.
- **API Credentials**: Valid credentials for Gmail, Gemini, and Notion APIs (via Infisical or .env).
- **Existing Test Framework**: pytest and existing test infrastructure for regression testing.

## Out of Scope

- **Performance Optimization**: Identifying bottlenecks is in scope, but implementing optimizations (e.g., async processing, caching improvements, batch operations) is deferred to future phases unless critical for MVP functionality.
- **New Features**: This feature is about testing and fixing existing MVP functionality, not adding new capabilities. Feature requests discovered during testing should be logged for future phases.
- **Manual Review UI**: Building a user interface for manual review of ambiguous cases is deferred to Phase 3. The DLQ mechanism is sufficient for now.
- **Comprehensive Load Testing**: Testing with hundreds or thousands of emails, or testing concurrent processing, is out of scope. Focus is on correctness with typical usage volumes (10-50 emails).
- **Production Monitoring**: Setting up alerting, dashboards, or production monitoring tools is out of scope. This feature focuses on dev/test environment validation.
- **Medium/Low Severity Fixes**: Not all errors must be fixed. Only critical and high-severity errors are required to be resolved within this feature. Medium/low issues can be documented and deferred.
