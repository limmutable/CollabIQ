# Feature Specification: Production Readiness Fixes

**Feature Branch**: `017-production-readiness-fixes`
**Created**: 2025-11-19
**Status**: Draft
**Input**: User description: "Phase 017: Critical Production Fixes (Est: 5-7 days) - Goal: Make system fully production-ready with autonomous operation and validated quality. T001-T005: Person Matching Enhancement (2 days) - Query Notion workspace users API, Implement Korean name fuzzy matching, Map extracted names to user UUIDs, Add caching for user list (TTL: 24h), Write 담당자 field correctly. T006-T010: Collaboration Summary Quality (1 day) - Use multi-LLM orchestration (consensus/best-match) to improve "협업내용" field summaries, Generate clear 1-4 line summaries, Leverage existing Phase 012 multi-LLM infrastructure, Test with 20+ real emails for quality improvement. T011-T015: Gmail Token Management (1 day) - Implement automatic refresh_token usage, Add token encryption at rest, Handle refresh failures gracefully, Test token rotation workflow. T016-T020: LLM Prompt Engineering (1 day) - Fix UUID format enforcement in prompts, Add retry logic for format correction, Test with 20+ real emails. T021-T025: Autonomous Daemon Mode (1 day) - Implement `collabiq run --daemon` command, Add configurable check intervals (default 15min), Persist processing state for restart resilience, Handle graceful shutdown (SIGTERM/SIGINT), Test 24-hour continuous operation. T026-T030: Comprehensive E2E Testing (1 day) - Run full test suite (989+ tests), Generate Markdown test reports with coverage metrics, Validate all Phase 017 fixes with E2E tests, Ensure ≥86.5% pass rate maintained, Document quality improvements. Success Criteria: ✅ 담당자 field populated correctly in 95%+ of entries, ✅ Collaboration summaries clear and useful in 90%+ of entries, ✅ Gmail tokens auto-refresh for 30+ days, ✅ UUID validation errors <5%, ✅ Daemon runs 24+ hours without crashes, ✅ Test suite passes at ≥86.5% with comprehensive reports"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Person Assignment in Notion (Priority: P1)

As a collaboration manager, I need the system to automatically assign the correct person (담당자) to each collaboration entry in Notion so that I can immediately see who is responsible for each partnership without manual data entry.

**Why this priority**: This is the most critical gap blocking production use. Currently, the 담당자 (person-in-charge) field is left empty in all Notion entries, requiring manual lookup and assignment for every entry. This defeats the automation purpose and creates significant manual work overhead.

**Independent Test**: Can be fully tested by processing emails that mention Korean names in the person field and verifying that the correct Notion user is assigned to the 담당자 field. Delivers immediate value by eliminating manual person assignment work.

**Acceptance Scenarios**:

1. **Given** an email mentioning "김철수" as the 담당자, **When** the system processes the email, **Then** the Notion entry should have the correct workspace user assigned to the 담당자 field (matched by Korean name)
2. **Given** an email with a person name that has multiple possible matches in Notion workspace, **When** the system processes the email, **Then** the system should select the best match based on fuzzy matching confidence score (>85% threshold)
3. **Given** an email with a person name that doesn't exist in the Notion workspace, **When** the system processes the email, **Then** the 담당자 field should be left empty and a warning logged for manual review
4. **Given** the system has previously cached the Notion user list, **When** processing multiple emails within 24 hours, **Then** the system should use the cached user list without re-querying the Notion API

---

### User Story 2 - High-Quality Collaboration Summaries (Priority: P2)

As a collaboration manager, I need the system to generate clear, well-organized 1-4 line summaries of collaboration emails in the "협업내용" (collaboration content) field so that I can quickly understand what each partnership is about without reading the full email.

**Why this priority**: This significantly impacts user experience and decision-making efficiency. Currently, the LLM-generated summaries in the "협업내용" field are inconsistent in quality, sometimes too verbose, sometimes missing key details. Using multi-LLM orchestration (consensus or best-match strategies with Gemini, Claude, OpenAI) can dramatically improve summary quality and consistency. This is the second most important production blocker after 담당자 assignment.

**Independent Test**: Can be fully tested by processing 20+ real emails and comparing summary quality across single-LLM vs multi-LLM orchestration strategies (consensus, best-match). Delivers immediate value by improving the clarity and usefulness of the "협업내용" field that users rely on daily.

**Acceptance Scenarios**:

1. **Given** an email describing a collaboration partnership, **When** the system uses multi-LLM consensus strategy, **Then** the "협업내용" field should contain a 1-4 line summary that clearly describes what the collaboration is about
2. **Given** an email with complex collaboration details, **When** the system orchestrates multiple LLMs (Gemini, Claude, OpenAI), **Then** the final summary should be more accurate and comprehensive than any single LLM's output
3. **Given** 20 test emails with known collaboration topics, **When** processed with multi-LLM orchestration, **Then** at least 90% of summaries should be rated as "clear and useful" (1-4 lines, captures key collaboration points)
4. **Given** an email mentioning multiple collaboration aspects, **When** the system generates the summary, **Then** the summary should prioritize the most important collaboration points and format them concisely

---

### User Story 3 - Unattended Gmail Access (Priority: P3)

As a system administrator, I need the system to automatically refresh Gmail API tokens without manual intervention so that automated daily email processing can run continuously for 30+ days without authentication failures.

**Why this priority**: This enables truly automated operation but is less critical than data completeness (담당자) and context visibility (page body). Current 7-day token expiration requires weekly manual re-authentication, which is acceptable for initial deployment but blocks unattended production operation.

**Independent Test**: Can be fully tested by simulating a token expiration scenario and verifying that the system automatically refreshes the token using the refresh_token. Delivers value by enabling hands-off operation.

**Acceptance Scenarios**:

1. **Given** a Gmail access token that is about to expire (within 1 hour), **When** the system attempts to fetch emails, **Then** the system should automatically refresh the token using the refresh_token before making the API call
2. **Given** a refresh_token that is still valid, **When** the token refresh process runs, **Then** the new access_token should be encrypted and stored securely at rest
3. **Given** a refresh_token that has been revoked or expired, **When** the token refresh process fails, **Then** the system should log a critical alert and gracefully degrade (skip email fetch) rather than crash
4. **Given** successful token refresh, **When** the system runs continuously for 30 days, **Then** tokens should be automatically refreshed without any manual intervention

---

### User Story 4 - Reliable UUID Extraction (Priority: P4)

As a system operator, I need the LLM to consistently extract Notion database UUIDs (not Korean company names) so that the system can link collaboration entries to the correct company records without validation errors.

**Why this priority**: This improves data quality but is less critical than the first three stories. The current workaround (manual correction of validation errors) is acceptable short-term. This optimization reduces manual cleanup work.

**Independent Test**: Can be fully tested by processing 20+ real emails with company mentions and verifying that UUID format validation errors occur in <5% of cases. Delivers value by reducing data correction work.

**Acceptance Scenarios**:

1. **Given** an email mentioning a company that exists in the Notion Companies database, **When** the LLM extracts company information, **Then** the extraction should contain the 32-character UUID (not the Korean company name) with ≥95% reliability
2. **Given** an extraction that returns a Korean company name instead of a UUID, **When** the validation fails, **Then** the system should automatically retry the extraction with corrected prompt instructions
3. **Given** 20 test emails with known company mentions, **When** processed through the system, **Then** UUID validation errors should occur in fewer than 1 out of 20 emails (<5% error rate)
4. **Given** the improved prompt engineering, **When** the LLM processes an email, **Then** the prompt should include clear examples of correct UUID format (32 hexadecimal characters) and explicit instructions to never return Korean text for UUID fields

---

### User Story 5 - Autonomous Background Operation (Priority: P5)

As a system administrator, I need to start the CollabIQ CLI with a single "run" or "start" command that monitors for new emails periodically so that the system can operate autonomously in the background without manual intervention for each email batch.

**Why this priority**: This enables true production deployment where the system runs continuously as a background service. Currently, the CLI requires manual execution for each email processing run. With autonomous operation, the system can check for new emails every N minutes, process them automatically, and handle errors gracefully. This is the final piece for production readiness but depends on other fixes (token auto-refresh, person assignment, summary quality) working reliably first.

**Independent Test**: Can be fully tested by starting the daemon mode, letting it run for 24 hours, and verifying that it processes emails at configured intervals, handles errors gracefully, and respects rate limits. Delivers value by enabling true hands-off operation.

**Acceptance Scenarios**:

1. **Given** the CollabIQ CLI with autonomous mode implemented, **When** the user runs `collabiq run --daemon --interval 15m`, **Then** the system should start monitoring for new emails every 15 minutes continuously
2. **Given** the daemon is running, **When** new emails arrive in Gmail, **Then** the system should detect them on the next check interval, process them automatically, and write results to Notion
3. **Given** the daemon encounters an error (e.g., API rate limit, network timeout), **When** the error occurs, **Then** the system should log the error, wait for the next interval, and continue running without crashing
4. **Given** the daemon has been running for 24 hours, **When** checking system logs, **Then** the logs should show all processing runs, success/failure counts, and any errors encountered

---

### User Story 6 - Comprehensive E2E Testing & Reporting (Priority: P6)

As a developer, I need to run comprehensive end-to-end tests with all production fixes and generate detailed test reports so that I can verify the system works correctly before deployment and track test coverage, pass rates, and quality metrics.

**Why this priority**: This validates that all five production fixes work together correctly in a real production environment. Phases 015-016 improved the test suite to 989 tests with 86.5% pass rate, but we need to verify that the new fixes (person assignment, summary quality, token management, UUID extraction, daemon mode) don't break existing functionality and actually improve quality metrics. This is essential for deployment confidence but lower priority than implementing the fixes themselves.

**Independent Test**: Can be fully tested by running the full test suite (unit, integration, E2E, contract, performance tests) and verifying that pass rates improve or remain stable (≥86.5%), coverage increases, and comprehensive Markdown reports are generated. Delivers value by providing deployment confidence and tracking quality improvements.

**Acceptance Scenarios**:

1. **Given** all Phase 017 fixes are implemented, **When** the developer runs the full test suite, **Then** the overall pass rate should be ≥86.5% (baseline from Phase 015) or higher
2. **Given** the test suite executes, **When** tests complete, **Then** a Markdown test report should be generated showing pass/fail counts, test duration, and coverage metrics
3. **Given** the E2E tests run with real Gmail/Notion credentials, **When** processing test emails, **Then** at least 95% of E2E tests should pass with the new production fixes
4. **Given** the test report is generated, **When** reviewing quality metrics, **Then** the report should show improvements in person assignment success rate, summary quality scores, and reduced UUID validation errors compared to pre-Phase 017 baselines

---

### Edge Cases

- What happens when a person's Korean name has multiple valid spellings or romanizations (e.g., "김철수" vs "Kim Chulsu")?
- How does the system handle emails where multiple people are mentioned in the 담당자 field?
- What happens when the Notion workspace user list changes (new users added, users removed) during the 24-hour cache TTL?
- What happens when multiple LLMs produce vastly different collaboration summaries (no consensus)?
- How does the system handle emails with minimal collaboration content (e.g., just a greeting or meeting request)?
- What happens when all LLMs in the orchestration pool fail or timeout?
- What happens when the Gmail refresh_token expires or is revoked (e.g., user revoked access in Google Account settings)?
- What happens when the LLM returns a malformed UUID (e.g., 31 characters, non-hexadecimal characters)?
- What happens when the daemon process receives a shutdown signal (SIGTERM, SIGINT) while processing emails?
- How does the daemon handle system restarts or crashes (resume from last processed email)?
- What happens when the daemon encounters repeated failures (e.g., 5 consecutive errors) - should it stop or continue?
- How does the system prevent duplicate email processing if the daemon is restarted mid-cycle?

## Requirements *(mandatory)*

### Functional Requirements

**Person Matching Enhancement (User Story 1)**:

- **FR-001**: System MUST query the Notion workspace users API to retrieve the complete list of workspace members
- **FR-002**: System MUST cache the Notion user list for 24 hours to minimize API calls
- **FR-003**: System MUST implement fuzzy string matching for Korean names using a similarity threshold of ≥85%
- **FR-004**: System MUST map extracted person names (Korean text) to Notion workspace user UUIDs
- **FR-005**: System MUST write the matched user UUID to the 담당자 (person-in-charge) field in Notion entries
- **FR-006**: System MUST log a warning when person name matching confidence is below 85% threshold
- **FR-007**: System MUST leave the 담당자 field empty when no suitable match is found (confidence <85%)

**Collaboration Summary Quality Enhancement (User Story 2)**:

- **FR-008**: System MUST use multi-LLM orchestration (minimum 2 LLMs) to generate collaboration summaries for the "협업내용" field
- **FR-009**: System MUST support at least two orchestration strategies: consensus (majority vote) and best-match (quality scoring)
- **FR-010**: Generated summaries MUST be 1-4 lines in length (maximum 400 characters)
- **FR-011**: System MUST prioritize the most important collaboration details when generating summaries
- **FR-012**: System MUST evaluate summary quality based on clarity, completeness, and conciseness
- **FR-013**: System MUST fall back to single best-performing LLM if multi-LLM orchestration fails

**Gmail Token Management (User Story 3)**:

- **FR-014**: System MUST automatically detect when Gmail access token is within 1 hour of expiration
- **FR-015**: System MUST use the refresh_token to obtain a new access_token before expiration
- **FR-016**: System MUST encrypt access tokens and refresh tokens at rest
- **FR-017**: System MUST handle refresh_token failures gracefully without crashing
- **FR-018**: System MUST log critical alerts when refresh_token is revoked or expired
- **FR-019**: System MUST support unattended operation for 30+ days with automatic token refresh

**LLM Prompt Engineering (User Story 4)**:

- **FR-020**: LLM prompts MUST include explicit instructions to return 32-character hexadecimal UUIDs for company fields
- **FR-021**: LLM prompts MUST include examples of correct UUID format
- **FR-022**: System MUST implement retry logic when UUID validation fails (malformed format)
- **FR-023**: System MUST limit UUID extraction retries to a maximum of 2 attempts per email
- **FR-024**: System MUST track UUID validation error rate and log metrics for monitoring
- **FR-025**: System MUST achieve UUID validation error rate below 5% across 20+ test emails

**Autonomous Background Operation (User Story 5)**:

- **FR-026**: System MUST provide a daemon mode CLI command (e.g., `collabiq run --daemon --interval <duration>`) that runs continuously
- **FR-027**: System MUST support configurable check intervals (minimum 5 minutes, default 15 minutes) for email monitoring
- **FR-028**: System MUST track last processed email timestamp to avoid duplicate processing across daemon restarts
- **FR-029**: System MUST handle graceful shutdown on SIGTERM/SIGINT signals, completing current email processing before exit
- **FR-030**: System MUST log each processing cycle with timestamp, emails processed count, success/failure status, and errors
- **FR-031**: System MUST continue running after individual processing errors (retry on next interval)
- **FR-032**: System MUST implement health check endpoint or status command to verify daemon is running
- **FR-033**: System MUST respect API rate limits with exponential backoff when limits are hit during daemon operation

**Comprehensive E2E Testing & Reporting (User Story 6)**:

- **FR-034**: System MUST provide a test execution command that runs the full test suite (unit, integration, E2E, contract, performance, fuzz)
- **FR-035**: Test suite MUST maintain or exceed 86.5% pass rate baseline established in Phase 015
- **FR-036**: System MUST generate Markdown test reports with pass/fail counts, test duration, coverage percentage, and detailed failure logs
- **FR-037**: E2E tests MUST validate all Phase 017 fixes (person assignment, summary quality, token refresh, UUID extraction, daemon mode)
- **FR-038**: Test reports MUST include quality metrics comparison showing before/after Phase 017 improvements
- **FR-039**: System MUST provide separate test commands for quick checks (unit only) and comprehensive validation (all test types)
- **FR-040**: Test execution MUST fail fast on critical errors while collecting results for non-critical failures

### Key Entities

- **Notion Workspace User**: Represents a person in the Notion workspace with attributes including Korean name, English name (if available), user UUID, and workspace role. Related to Notion entries via the 담당자 (person-in-charge) field.

- **Collaboration Summary**: Represents a concise 1-4 line summary of collaboration content extracted from an email, stored in the "협업내용" field. Attributes include summary text (max 400 characters), orchestration strategy used (consensus/best-match), contributing LLM models, quality score, and generation timestamp. Related to multi-LLM orchestration results.

- **Gmail Token Pair**: Represents the OAuth2 access token and refresh token for Gmail API access, including access token value, refresh token value, token expiration timestamp, and encryption status. Related to email fetching operations.

- **UUID Extraction Result**: Represents the outcome of LLM company UUID extraction, including extracted UUID value, validation status (valid/invalid format), retry count, and confidence score. Related to Notion company linkage.

- **Daemon Process State**: Represents the autonomous background operation state, including daemon start timestamp, last check timestamp, check interval duration, total processing cycles, emails processed count, error count, current status (running/stopped/error), and last processed email ID. Persisted to enable graceful restarts and duplicate prevention.

- **Test Execution Report**: Represents comprehensive test results, including total tests executed, pass count, fail count, skip count, test duration, coverage percentage, test categories breakdown (unit/integration/E2E/contract/performance/fuzz), detailed failure logs, and quality metrics comparison (before/after Phase 017). Generated as Markdown for easy viewing and analysis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of collaboration entries have the 담당자 field correctly populated with matched Notion workspace users (measured across 20+ test emails)
- **SC-002**: 90% of "협업내용" summaries are rated as "clear and useful" (1-4 lines, captures key collaboration points) across 20+ test emails
- **SC-003**: System operates continuously for 30+ days without manual Gmail authentication intervention
- **SC-004**: UUID validation error rate is below 5% (fewer than 1 error per 20 processed emails)
- **SC-005**: Person name matching completes within 2 seconds per email (including Notion user list query or cache retrieval)
- **SC-006**: Multi-LLM collaboration summary generation completes within 8 seconds per email (including orchestration overhead)
- **SC-007**: Token refresh process completes within 5 seconds when needed
- **SC-008**: System processes 50 emails with all six enhancements in under 12 minutes total (manual mode)
- **SC-009**: Daemon mode runs continuously for 24 hours without crashes, processing emails at configured intervals (15 minutes default)
- **SC-010**: Daemon handles graceful shutdown within 10 seconds of receiving SIGTERM/SIGINT signal
- **SC-011**: Full test suite (989+ tests) maintains ≥86.5% pass rate with Phase 017 fixes implemented
- **SC-012**: Markdown test report is generated with coverage metrics, pass/fail breakdown, and quality improvements visible

## Assumptions *(optional)*

- Notion workspace has a relatively stable user list (changes less than once per day)
- Korean names in emails are written in Hangul (not romanized)
- Gmail refresh tokens have a default expiration of several months (unless explicitly revoked)
- Multi-LLM orchestration infrastructure already exists (Phase 012 implemented Gemini, Claude, OpenAI adapters with failover/consensus)
- LLM providers (Gemini, Claude, OpenAI) maintain current response format and JSON structure
- Multi-LLM orchestration overhead (2-3 LLM calls) is acceptable for improved summary quality
- System has network access to Gmail API, Notion API, and all LLM provider APIs at all times
- Fuzzy matching library (rapidfuzz) supports Korean Unicode characters correctly
- Daemon mode will be deployed on a stable server/container environment (not a laptop that sleeps)
- Email volume is manageable with 15-minute check intervals (not receiving thousands of emails per hour)

## Dependencies *(optional)*

- **Existing Phase 011**: Daemon mode builds on the existing CLI infrastructure (Typer framework) implemented in Phase 011 (admin-cli)
- **Existing Phase 012**: Multi-LLM orchestration builds on the LLM adapter infrastructure (Gemini, Claude, OpenAI) and orchestration strategies (failover, consensus, best-match) implemented in Phase 012 (multi-llm)
- **Existing Phase 014**: Person matching builds on the company matching fuzzy logic implemented in Phase 014 (enhanced-field-mapping)
- **Existing Phase 015-016**: Testing infrastructure builds on the comprehensive test suite (989 tests, 86.5% baseline) established in Phases 015-016 (test-suite-improvements, project-cleanup)
- **Notion API**: Requires Notion workspace users API endpoint
- **Gmail OAuth2**: Depends on existing OAuth2 implementation with refresh_token support
- **LLM Adapters**: Requires existing Gemini, Claude, and OpenAI adapters with prompt management infrastructure
- **Caching Layer**: Requires existing caching mechanism (used for Notion schema and data cache)
- **Signal Handling**: Requires proper SIGTERM/SIGINT signal handling for graceful shutdown
- **Testing Framework**: Requires pytest, pytest-cov for test execution and Markdown report generation

## Out of Scope *(optional)*

- Creating new Notion workspace users when person names don't match existing users
- Implementing manual summary editing UI or workflow for low-quality summaries
- Supporting multiple language names beyond Korean (e.g., English, Chinese)
- Implementing manual person assignment UI or workflow for low-confidence matches
- Migrating existing Notion entries to add missing 담당자 fields or regenerate summaries
- Implementing token refresh for Notion API or LLM providers (only Gmail tokens)
- Supporting multiple 담당자 assignments per entry (only single person assignment)
- Implementing email attachment analysis in collaboration summaries
- Creating bidirectional sync (Notion edits back to email)
- Displaying full email content in Notion page body (focus is on summary quality, not full content display)
- Implementing systemd service files or Docker containerization for daemon deployment (users deploy as needed)
- Building a web UI or dashboard for daemon monitoring (CLI status command and logs are sufficient)
- Implementing distributed processing or horizontal scaling (single daemon instance only)
- Writing new tests for Phase 017 fixes (leveraging existing test infrastructure to validate new functionality)
- Implementing CI/CD integration for automated test execution (manual test execution is sufficient)

## Notes *(optional)*

- The 담당자 (person-in-charge) field is currently always left empty in production, requiring significant manual data entry work. This is the #1 user complaint.
- The "협업내용" summaries generated by single-LLM extraction are inconsistent in quality—sometimes too verbose, sometimes missing key details. This is the #2 user complaint.
- Multi-LLM orchestration infrastructure already exists from Phase 012 (failover, consensus, best-match strategies), so this phase leverages existing capabilities for summary quality improvement.
- Gmail refresh tokens can be revoked by users at any time through Google Account settings. The system must handle this gracefully.
- Korean name matching is complex due to the large number of surnames and given names. Fuzzy matching helps but may still produce false positives.
- The LLM occasionally returns Korean company names ("웨이크", "신세계푸드") instead of UUIDs, causing Pydantic validation errors. This has been observed in real production emails.
- Token encryption at rest is a security best practice but adds complexity. The encryption key itself must be managed securely (likely via Infisical or environment variable).
- Multi-LLM orchestration adds latency (2-3 LLM API calls instead of 1), but the improved summary quality justifies the overhead based on user feedback.
- Daemon mode is the final piece for production readiness. It enables true hands-off operation but depends on other fixes (token auto-refresh, person assignment, summary quality) working reliably.
- The daemon must persist state (last processed email ID) to prevent duplicate processing across restarts. File-based state persistence is sufficient for single-instance deployment.
- Graceful shutdown is critical—the daemon must complete current email processing before exit to avoid data loss or partial writes to Notion.
- Phase 015-016 established a solid test foundation (989 tests across 9 categories, 86.5% pass rate baseline). This phase validates that new fixes don't break existing functionality and actually improve quality metrics.
- Test execution should run at key milestones: after each user story implementation, before merging to main, and as part of final deployment validation.
- Markdown test reports make it easy to track progress, identify regressions, and demonstrate quality improvements to stakeholders without requiring HTML tooling.
- The estimated 5-7 day timeline assumes no major blockers and includes time for testing with real production emails, 24-hour daemon stability testing, and comprehensive test execution with report generation.
