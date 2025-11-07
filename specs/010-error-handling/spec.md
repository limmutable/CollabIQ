# Feature Specification: Error Handling & Retry Logic

**Feature Branch**: `010-error-handling`
**Created**: 2025-11-06
**Status**: Draft
**Input**: User description: "Phase 2e - Error Handling & Retry Logic"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transient API Failures Handled Automatically (Priority: P1)

When external API calls (Gmail, Gemini, Notion, Infisical) temporarily fail due to network issues, rate limits, or service hiccups, the system automatically retries the operation without losing data or requiring manual intervention. Users don't experience interruptions for temporary failures.

**Why this priority**: External API failures are the most common source of errors in the current pipeline. Without automatic retry, every transient network issue or rate limit results in lost emails or incomplete processing. This is the foundation for system reliability.

**Independent Test**: Can be fully tested by simulating API timeouts and rate limits, and verifying that operations complete successfully after retries. Delivers immediate value by making the system resilient to the most common failure mode.

**Acceptance Scenarios**:

1. **Given** Gmail API returns a timeout error, **When** the system attempts to fetch emails, **Then** it retries up to 3 times with exponential backoff before failing
2. **Given** Notion API returns a 429 rate limit error, **When** writing a collaboration entry, **Then** the system waits and retries according to rate limit headers
3. **Given** Gemini API returns a 503 service unavailable error, **When** extracting entities from email, **Then** the system retries with exponential backoff and eventually succeeds
4. **Given** Infisical API has a connection timeout, **When** fetching secrets, **Then** the system falls back to .env file and logs the failure for monitoring

---

### User Story 2 - Invalid Data Handled Gracefully (Priority: P2)

When email content or LLM responses contain invalid, malformed, or unexpected data, the system logs detailed error information, skips the problematic item, and continues processing other emails. Users can review error logs to understand what went wrong and take corrective action if needed.

**Why this priority**: Data validation errors are preventable failures that should not crash the system or block processing of other valid emails. This ensures one bad email doesn't stop the entire pipeline.

**Independent Test**: Can be tested by feeding emails with missing required fields, malformed dates, or LLM responses with invalid company IDs. System should log errors and continue processing subsequent emails.

**Acceptance Scenarios**:

1. **Given** an email with no discernible date, **When** processing the email, **Then** the system logs a data validation error and moves to the next email
2. **Given** Gemini returns company names instead of UUIDs, **When** validating extracted entities, **Then** the system logs the mismatch, marks the entry as "needs_review", and continues
3. **Given** an email with Korean text encoding issues, **When** parsing content, **Then** the system attempts to decode using fallback encodings and logs the issue if it fails
4. **Given** Notion database schema changes, **When** mapping fields, **Then** the system detects missing fields and logs schema mismatch errors

---

### User Story 3 - Critical Failures Preserved for Recovery (Priority: P3)

When the system encounters unrecoverable errors (authentication failures, database unavailable, file system errors), it preserves the state of failed operations in a dead letter queue (DLQ) so they can be retried later or investigated. Users receive notifications about critical failures that require attention.

**Why this priority**: Some failures cannot be automatically resolved and require human intervention. The system should preserve all information needed for debugging and recovery rather than losing data permanently.

**Independent Test**: Can be tested by simulating authentication failures or database unavailability, and verifying that failed operations are persisted to DLQ with full context. Recovery can be tested by fixing the issue and reprocessing DLQ entries.

**Acceptance Scenarios**:

1. **Given** Infisical authentication fails, **When** attempting to fetch secrets, **Then** the system logs the failure, preserves the email ID in DLQ, and continues with .env fallback
2. **Given** Notion database is deleted or permissions revoked, **When** attempting to write entries, **Then** the system preserves all extracted data in DLQ with full email context
3. **Given** file system is full when saving extraction results, **When** writing to disk, **Then** the system logs the error and queues the operation for retry
4. **Given** DLQ entries exist from previous failures, **When** the underlying issue is fixed, **Then** users can replay DLQ entries successfully

---

### Edge Cases

- What happens when retry attempts exceed maximum count? (System moves item to DLQ and alerts)
- How does the system handle partial failures? (e.g., email fetched but extraction failed)
- What happens if DLQ storage fills up? (System alerts and stops processing new items until space is freed)
- How does the system handle cascading failures? (Circuit breaker pattern to prevent overwhelming downstream services)
- What happens when errors occur during error handling? (Fail-safe logging to stderr/console)
- How does the system differentiate between retryable and non-retryable errors?
- What happens when rate limit headers are missing or malformed?
- How does the system handle timeouts during retry backoff periods?

## Requirements *(mandatory)*

### Functional Requirements

#### Retry Logic

- **FR-001**: System MUST implement exponential backoff with jitter for all external API calls (Gmail, Gemini, Notion, Infisical)
- **FR-002**: System MUST retry transient failures (timeouts, 5xx errors, rate limits) up to 3 times before marking as failed
- **FR-003**: System MUST NOT retry permanent failures (authentication errors, 4xx client errors except 429)
- **FR-004**: System MUST respect rate limit headers from APIs (Retry-After, X-RateLimit-Reset) when retrying
- **FR-005**: System MUST log each retry attempt with error details, attempt number, and backoff duration

#### Error Classification

- **FR-006**: System MUST classify errors into three categories: transient (retryable), permanent (not retryable), and critical (requires human intervention)
- **FR-007**: System MUST identify rate limit errors (429 status codes) and handle them separately with longer backoff
- **FR-008**: System MUST detect authentication/authorization failures (401, 403) and escalate immediately without retry
- **FR-009**: System MUST detect data validation errors (Pydantic validation failures) and log detailed field-level errors

#### Error Logging and Monitoring

- **FR-010**: System MUST log all errors with severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **FR-011**: System MUST include contextual information in error logs: email ID, operation type, timestamp, full stack trace
- **FR-012**: System MUST write error logs to structured format (JSON) for easy parsing and monitoring
- **FR-013**: System MUST preserve original error messages and stack traces for debugging
- **FR-014**: System MUST track error counts per operation type for monitoring dashboards

#### Dead Letter Queue (DLQ)

- **FR-015**: System MUST persist failed operations to DLQ after exhausting all retry attempts
- **FR-016**: DLQ entries MUST include: email ID, original email content, extraction data (if available), error details, timestamp, retry count
- **FR-017**: System MUST provide mechanism to replay DLQ entries after underlying issues are fixed
- **FR-018**: DLQ MUST be stored in file system with one JSON file per failed operation
- **FR-019**: System MUST prevent duplicate processing of DLQ entries using unique operation IDs

#### Graceful Degradation

- **FR-020**: When Infisical is unavailable, system MUST fall back to .env file and continue processing
- **FR-021**: When Notion write fails, system MUST preserve extracted data locally and continue processing next email
- **FR-022**: When Gemini API fails, system MUST log the error and mark email for manual review
- **FR-023**: System MUST continue processing remaining emails even if one email fails completely

#### Circuit Breaker

- **FR-024**: System MUST implement circuit breaker pattern for external API calls to prevent cascading failures
- **FR-025**: Circuit breaker MUST open (stop requests) after 5 consecutive failures to the same service
- **FR-026**: Circuit breaker MUST attempt to close (resume requests) after 60 seconds of cool-down
- **FR-027**: Circuit breaker state MUST be logged for monitoring and debugging

### Key Entities

- **ErrorRecord**: Represents a logged error with severity, message, stack trace, context (email ID, operation), timestamp, and retry count
- **DLQEntry**: Represents a failed operation in dead letter queue with original data, error details, creation timestamp, and retry metadata
- **RetryConfig**: Configuration for retry behavior including max attempts, backoff multiplier, jitter range, and timeout values
- **CircuitBreakerState**: State of circuit breaker for each external service (closed/open/half-open, failure count, last failure time)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of transient API failures recover automatically without manual intervention
- **SC-002**: System processes at least 90% of emails successfully even when individual operations fail
- **SC-003**: All critical failures are captured in DLQ with sufficient context for debugging (100% data preservation)
- **SC-004**: Mean time to recovery (MTTR) for transient failures is under 10 seconds with exponential backoff
- **SC-005**: Error logs contain actionable information (stack traces, context) in 100% of cases
- **SC-006**: Circuit breakers prevent system overload by stopping requests after 5 consecutive failures
- **SC-007**: DLQ entries can be replayed successfully after fixing underlying issues (100% recovery rate)
- **SC-008**: System continues processing other emails within 1 second of encountering a non-critical error

## Assumptions

- External APIs (Gmail, Gemini, Notion, Infisical) follow standard HTTP status code conventions
- Rate limit headers follow common formats (Retry-After, X-RateLimit-Reset)
- File system has sufficient space for DLQ storage (monitoring will alert if space is low)
- Exponential backoff with jitter is sufficient to avoid thundering herd problem
- Email processing is idempotent (replaying operations produces same result)
- Current error handling in codebase is minimal and needs comprehensive upgrade
- Most failures are transient (network issues, rate limits) rather than permanent

## Out of Scope

- Real-time alerting/notifications for critical errors (future phase)
- Metrics dashboard for error rates and trends (future phase)
- Automated root cause analysis (future phase)
- Integration with external monitoring services (Datadog, Sentry)
- Recovery automation for common error patterns (future phase)
- Distributed tracing across service boundaries (future phase)

## Dependencies

- Python `tenacity` library for retry logic (already in use for Notion writes)
- Python logging module (standard library)
- Python `json` module for structured logging (standard library)
- Existing DLQ implementation from Feature 006 (Dead Letter Queue)
- Circuit breaker implementation (new dependency or custom implementation needed)

## Risks

- **Risk**: Aggressive retry logic could exacerbate rate limiting issues
  - **Mitigation**: Implement exponential backoff with jitter and respect rate limit headers

- **Risk**: DLQ storage could fill up disk space over time
  - **Mitigation**: Implement DLQ rotation/archival policy, monitor disk usage

- **Risk**: Circuit breakers could prevent legitimate requests if threshold is too sensitive
  - **Mitigation**: Start with conservative threshold (5 failures), tune based on monitoring data

- **Risk**: Error logging could contain sensitive information (API keys, email content)
  - **Mitigation**: Implement log sanitization to redact sensitive data before writing
