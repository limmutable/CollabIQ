# Feature Specification: Admin CLI Enhancement

**Feature Branch**: `011-admin-cli`
**Created**: 2025-11-08
**Status**: Draft
**Input**: User description: "Admin CLI Enhancement - Unified collabiq command with organized subcommands for email (fetch, clean, list, verify, process), notion (verify, schema, test-write, cleanup-tests), test (e2e, select-emails, validate), errors (list, show, retry, clear for DLQ management), status (health check, component status, metrics with --watch mode), and config (show, validate, test-secrets, get) operations. Color-coded output, progress indicators, table formatting. JSON output mode (--json) for all commands. Graceful interrupt handling with resume capability. Help text with examples for all commands."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single Entry Point for All Operations (Priority: P1)

As an admin, I want to access all CollabIQ operations through a single `collabiq` command so that I don't need to remember multiple script paths or command variations, making system management efficient and intuitive.

**Why this priority**: This is the foundation - without a unified CLI entry point, admins must navigate fragmented scripts and commands. This delivers immediate value by centralizing all operations.

**Independent Test**: Run `collabiq --help` and verify all command groups (email, notion, test, errors, status, config) are listed with clear descriptions. Test basic commands like `collabiq status` work without errors.

**Acceptance Scenarios**:

1. **Given** the admin has CollabIQ installed, **When** they run `collabiq --help`, **Then** they see all command groups organized clearly with usage examples
2. **Given** the admin runs any `collabiq` subcommand, **When** the command completes, **Then** the output uses color coding (green for success, yellow for warnings, red for errors)
3. **Given** the admin types `collabiq` without arguments, **When** the command runs, **Then** they see friendly help text with common usage examples and next steps

---

### User Story 2 - Email Pipeline Management (Priority: P1)

As an admin, I want to manage email operations (fetch, clean, list, verify, process) through `collabiq email` commands so that I can control the email ingestion pipeline and troubleshoot email-related issues quickly.

**Why this priority**: Email reception is the entry point for all collaboration data. Admins must be able to fetch, inspect, and process emails reliably.

**Independent Test**: Run `collabiq email fetch --limit 5` to download 5 emails, then `collabiq email list` to view them, and verify both commands complete successfully with proper output formatting.

**Acceptance Scenarios**:

1. **Given** new emails exist in Gmail, **When** admin runs `collabiq email fetch`, **Then** emails are downloaded, deduplicated, and saved with a summary table showing count and status
2. **Given** raw emails exist in storage, **When** admin runs `collabiq email clean`, **Then** emails are normalized (signatures removed, content cleaned) and admin sees progress indicator during processing
3. **Given** admin needs to check email setup, **When** they run `collabiq email verify`, **Then** they see Gmail connection status, credential validity, recent email counts, and any configuration issues highlighted
4. **Given** admin wants to see recent emails, **When** they run `collabiq email list --limit 20`, **Then** they see a formatted table with sender, subject, date, and processing status
5. **Given** admin wants full pipeline execution, **When** they run `collabiq email process`, **Then** the system fetches, cleans, extracts entities, and writes to Notion with real-time progress updates

---

### User Story 3 - Notion Integration Management (Priority: P2)

As an admin, I want to manage Notion integration (verify, schema, test-write, cleanup) through `collabiq notion` commands so that I can ensure database connectivity, validate schema compatibility, and test write operations safely.

**Why this priority**: Notion is the output destination for extracted data. Admins need to verify connectivity and schema before processing emails.

**Independent Test**: Run `collabiq notion verify` and verify it checks connection, authentication, database access, and schema. Then run `collabiq notion test-write` to create and automatically cleanup a test entry.

**Acceptance Scenarios**:

1. **Given** Notion credentials are configured, **When** admin runs `collabiq notion verify`, **Then** they see connection status, authentication result, database accessibility, and schema compatibility check with detailed error messages for any failures
2. **Given** admin wants to inspect database schema, **When** they run `collabiq notion schema`, **Then** they see a formatted table of all properties with names, types, required status, and validation rules
3. **Given** admin wants to test write operations, **When** they run `collabiq notion test-write`, **Then** a test entry is created with sample data, verified to exist, automatically cleaned up, and confirmation is displayed
4. **Given** test entries exist from interrupted tests, **When** admin runs `collabiq notion cleanup-tests`, **Then** all test entries are identified, admin is prompted for confirmation, and entries are removed with summary

---

### User Story 4 - End-to-End Testing (Priority: P2)

As an admin, I want to run E2E tests on the complete pipeline through `collabiq test` commands so that I can validate system health, catch integration issues, and verify deployment readiness.

**Why this priority**: E2E testing is critical for production confidence, but requires emails to exist first (depends on email pipeline).

**Independent Test**: Run `collabiq test e2e --limit 3` on three test emails and verify a detailed report is generated showing pass/fail for each pipeline stage (reception, extraction, matching, classification, validation, write).

**Acceptance Scenarios**:

1. **Given** test emails are configured, **When** admin runs `collabiq test e2e --all`, **Then** all test emails are processed through the complete pipeline with a detailed report showing stage-by-stage results
2. **Given** a test run was interrupted, **When** admin runs `collabiq test e2e --resume <run-id>`, **Then** testing resumes from the last successful email without reprocessing completed emails
3. **Given** admin needs to test a specific email, **When** they run `collabiq test e2e --email-id <id>`, **Then** only that email is processed with verbose output showing each pipeline stage
4. **Given** admin needs to set up test emails, **When** they run `collabiq test select-emails`, **Then** recent emails are analyzed for suitability and test candidates are saved to configuration
5. **Given** admin wants quick validation, **When** they run `collabiq test validate`, **Then** basic health checks run (Gmail auth, Notion access, Gemini API) with pass/fail results in under 10 seconds

---

### User Story 5 - Error Management and DLQ Operations (Priority: P3)

As an admin, I want to view, inspect, retry, and clear failed operations through `collabiq errors` commands so that I can recover from transient errors and maintain data integrity.

**Why this priority**: Error management is important for data recovery but not needed until the system is processing emails and encountering failures.

**Independent Test**: Simulate a failure (disconnect network during email processing), verify it appears in `collabiq errors list`, inspect details with `collabiq errors show <id>`, then retry with `collabiq errors retry <id>` and confirm success.

**Acceptance Scenarios**:

1. **Given** errors have occurred during processing, **When** admin runs `collabiq errors list`, **Then** they see a table of failed operations with error type, timestamp, severity (critical/high/medium/low), and retry count
2. **Given** admin needs error details, **When** they run `collabiq errors show <error-id>`, **Then** they see full error message, stack trace (if available), affected email/data, and suggested remediation
3. **Given** admin wants to retry failures, **When** they run `collabiq errors retry --all`, **Then** all retriable (transient) errors are reprocessed with progress indicator and success/fail summary
4. **Given** errors are resolved, **When** admin runs `collabiq errors clear --resolved`, **Then** resolved errors are archived with confirmation and remaining active errors are displayed

---

### User Story 6 - System Health Monitoring (Priority: P3)

As an admin, I want to check overall system health, component status, and metrics through `collabiq status` commands so that I can quickly diagnose issues and monitor system performance.

**Why this priority**: Health monitoring provides visibility but is most valuable after the system is processing data regularly.

**Independent Test**: Run `collabiq status` and verify it shows overall health (healthy/degraded/critical) and status for all components (Gmail, Notion, Gemini) in under 5 seconds.

**Acceptance Scenarios**:

1. **Given** the system is operational, **When** admin runs `collabiq status`, **Then** they see overall health indicator, component status (Gmail, Notion, Gemini), and recent activity summary (emails processed today, success rate, error count)
2. **Given** admin needs detailed metrics, **When** they run `collabiq status --detailed`, **Then** they see processing rates, error breakdown by severity, API quota usage, and performance metrics (avg processing time)
3. **Given** admin wants continuous monitoring, **When** they run `collabiq status --watch`, **Then** the status display refreshes every 30 seconds with updated metrics and highlighted changes
4. **Given** a component is degraded, **When** admin checks status, **Then** degraded components are highlighted in yellow/red, with specific error messages and suggested remediation actions

---

### User Story 7 - Configuration Management (Priority: P3)

As an admin, I want to view, validate, and test configuration through `collabiq config` commands so that I can troubleshoot setup issues, verify environment variables, and ensure secrets are accessible.

**Why this priority**: Configuration management is valuable for troubleshooting but most setup is one-time or infrequent.

**Independent Test**: Run `collabiq config show` and verify all configuration values are displayed with secrets masked (e.g., `GEMINI_API_KEY=AIza...***`) and source indicators (Infisical/env/default).

**Acceptance Scenarios**:

1. **Given** configuration is loaded, **When** admin runs `collabiq config show`, **Then** they see all settings with secrets masked, source attribution (Infisical/env/default), and categories (Gmail, Notion, Gemini, System)
2. **Given** admin needs to validate setup, **When** they run `collabiq config validate`, **Then** all required settings are checked, missing/invalid values are reported, and suggestions are provided
3. **Given** admin wants to test secret access, **When** they run `collabiq config test-secrets`, **Then** Infisical connectivity is verified, all secrets are fetched (with masked display), and any access issues are reported
4. **Given** admin needs a specific value, **When** they run `collabiq config get GEMINI_API_KEY`, **Then** the value is displayed (masked for secrets) with its source and any related settings

---

### Edge Cases

- What happens when multiple admins run operations concurrently? → System uses file locking for critical operations (e.g., email fetch) and displays friendly message if another admin is running the same command
- How does the CLI handle partial failures (e.g., 8 out of 10 emails processed)? → Shows summary with successful count and failed count, saves progress, provides command to retry failures
- What happens when an operation is interrupted (Ctrl+C during E2E test)? → Gracefully saves progress, cleans up temporary state, displays resume command, allows continuation with `--resume`
- How does the system handle rate limits from APIs? → Displays rate limit status in error message, suggests wait time, provides `--retry-after` flag for automatic retry
- What happens when configuration is invalid for specific operations? → Operations that don't depend on invalid config proceed with warnings, operations that need that config fail with clear error and fix suggestions
- How does the CLI handle very large outputs (e.g., 1000 error records)? → Implements pagination (default 20 items), provides `--limit` flag, supports `--all` for complete output, offers `--json` mode for scripting
- What happens when disk space is low? → `status` command shows disk usage warning, cleanup suggestions are provided, processing operations check available space before starting
- How does JSON output mode work? → All commands support `--json` flag, outputs valid JSON with consistent structure (status, data, errors), suitable for parsing by scripts or CI/CD
- What happens when required credentials are missing? → Command fails immediately with clear error message, displays setup instructions, provides link to credential configuration docs

## Requirements *(mandatory)*

### Functional Requirements

#### Core CLI Infrastructure

- **FR-001**: System MUST provide a single entry point command `collabiq` installed in the system PATH
- **FR-002**: System MUST organize commands into six logical groups: email, notion, test, errors, status, config
- **FR-003**: System MUST provide contextual help via `--help` flag for main command and all subcommands
- **FR-004**: System MUST use consistent option naming across all commands (`--limit`, `--debug`, `--json`, `--yes`, `--quiet`)
- **FR-005**: System MUST display operation progress for long-running tasks using progress bars or status messages
- **FR-006**: System MUST provide JSON output mode via `--json` flag for all commands (structured, parseable output)
- **FR-007**: System MUST handle graceful shutdown on interrupt signals (SIGINT, SIGTERM) with progress saving
- **FR-008**: System MUST log all CLI operations to system log file with timestamp, user, command, and result
- **FR-009**: System MUST support `--debug` flag globally to enable verbose logging for troubleshooting
- **FR-010**: System MUST support `--quiet` flag to suppress non-error output for automation scenarios

#### Email Pipeline Commands

- **FR-011**: System MUST provide `collabiq email fetch` command to download emails from Gmail with `--limit` option
- **FR-012**: System MUST provide `collabiq email clean` command to normalize raw emails with batch processing
- **FR-013**: System MUST provide `collabiq email list` command to display recent emails with filtering (`--limit`, `--since`, `--status`)
- **FR-014**: System MUST provide `collabiq email verify` command to check Gmail connectivity and display diagnostic info
- **FR-015**: System MUST provide `collabiq email process` command to run complete pipeline (fetch, clean, extract, validate, write)
- **FR-016**: Email commands MUST display summary statistics (count processed, duration, success/failure breakdown)
- **FR-017**: Email commands MUST handle duplicate detection automatically and report skipped duplicates
- **FR-018**: Email fetch MUST show progress indicator with count fetched and estimated remaining
- **FR-019**: Email list MUST display emails in formatted table with sender, subject, date, and processing status columns

#### Notion Integration Commands

- **FR-020**: System MUST provide `collabiq notion verify` command to check connection, auth, database access, and schema
- **FR-021**: System MUST provide `collabiq notion schema` command to display database properties in formatted table
- **FR-022**: System MUST provide `collabiq notion test-write` command to create and cleanup a test entry with verification
- **FR-023**: System MUST provide `collabiq notion cleanup-tests` command to remove all test entries with confirmation
- **FR-024**: Notion verify MUST check connection, authentication, database access, and schema compatibility separately
- **FR-025**: Notion schema MUST display property names, types, required status, and validation rules
- **FR-026**: Notion commands MUST display API quota usage and rate limit status if available

#### Testing Commands

- **FR-027**: System MUST provide `collabiq test e2e` command to run end-to-end tests with `--all`, `--limit`, or `--email-id` options
- **FR-028**: System MUST support E2E test resumption via `collabiq test e2e --resume <run-id>` after interruption
- **FR-029**: System MUST provide `collabiq test select-emails` command to analyze and configure test email candidates
- **FR-030**: System MUST provide `collabiq test validate` command for quick health checks (under 10 seconds)
- **FR-031**: E2E tests MUST generate detailed reports with pass/fail status for each pipeline stage
- **FR-032**: E2E tests MUST show real-time progress with current email, stage, and estimated completion time
- **FR-033**: Test reports MUST be saved to `data/e2e_test/reports/` with timestamped filenames
- **FR-034**: Test validate MUST check Gmail auth, Notion access, Gemini API, and configuration validity

#### Error Management Commands

- **FR-035**: System MUST provide `collabiq errors list` command with filtering by `--severity`, `--since`, `--limit`
- **FR-036**: System MUST provide `collabiq errors show <error-id>` command to display full error details
- **FR-037**: System MUST provide `collabiq errors retry` command with options `--all`, `--id <id>`, or `--since <date>`
- **FR-038**: System MUST provide `collabiq errors clear` command with options `--resolved` or `--before <date>`
- **FR-039**: Errors list MUST display errors in table format with ID, timestamp, severity, type, and retry count
- **FR-040**: Errors show MUST display error message, stack trace, affected data, and suggested remediation
- **FR-041**: Errors retry MUST only retry transient errors and skip permanent errors with explanation
- **FR-042**: Error commands MUST categorize errors by severity (critical/high/medium/low) using existing error classification

#### System Status Commands

- **FR-043**: System MUST provide `collabiq status` command showing overall health and component status
- **FR-044**: System MUST display component health for Gmail, Notion, and Gemini with pass/fail/degraded indicators
- **FR-045**: System MUST show recent activity metrics (emails processed today, success rate, error count, last run time)
- **FR-046**: System MUST support `collabiq status --detailed` for extended metrics (processing rates, API usage, performance)
- **FR-047**: System MUST support `collabiq status --watch` for continuous monitoring with 30-second refresh
- **FR-048**: Status display MUST highlight degraded/failed components and provide suggested remediation actions
- **FR-049**: Status command MUST complete in under 5 seconds for basic health check
- **FR-050**: Status detailed MUST show disk usage, memory usage, and log file sizes

#### Configuration Commands

- **FR-051**: System MUST provide `collabiq config show` command to display all configuration with secrets masked
- **FR-052**: System MUST indicate configuration source (Infisical/env/default) for each setting
- **FR-053**: System MUST provide `collabiq config validate` command to check for missing/invalid required settings
- **FR-054**: System MUST provide `collabiq config test-secrets` command to verify Infisical connectivity
- **FR-055**: System MUST provide `collabiq config get <key>` command to display specific configuration value
- **FR-056**: Config show MUST group settings by category (Gmail, Notion, Gemini, System) for readability
- **FR-057**: Config show MUST mask sensitive values (API keys, tokens) showing only first 4 and last 3 characters
- **FR-058**: Config validate MUST check all required settings and report missing/invalid values with fix suggestions

#### User Experience

- **FR-059**: System MUST use color-coded output (green for success, yellow for warnings, red for errors, blue for info)
- **FR-060**: System MUST display tables with proper column alignment using rich text formatting library
- **FR-061**: System MUST provide usage examples in help text for complex commands
- **FR-062**: System MUST support `--yes` flag to skip confirmation prompts for automation
- **FR-063**: System MUST display helpful error messages with context and suggested next steps (not just stack traces)
- **FR-064**: System MUST show command execution time for operations taking longer than 2 seconds
- **FR-065**: System MUST provide clear progress indicators (spinner, progress bar, percentage) for long operations
- **FR-066**: System MUST support color disabling via `--no-color` flag or `NO_COLOR` environment variable

### Key Entities

- **CLI Command**: An executable operation with name, description, arguments, options, help text, and handler function
- **Command Group**: Logical grouping of related commands (email, notion, test, errors, status, config) with shared context
- **Operation Result**: Execution outcome with status (success/failure/partial), message, data, and execution time
- **Progress Indicator**: Visual feedback showing operation progress (spinner, bar, percentage, ETA) for user awareness
- **Error Record**: Failed operation details including error ID, timestamp, severity, type, message, stack trace, and retry count
- **Health Status**: Component health snapshot with status (healthy/degraded/critical), last check time, and metrics
- **Configuration Item**: Setting with key, value, source (Infisical/env/default), category, and validation rules
- **Test Report**: E2E test execution summary with run ID, timestamp, email count, stage results, and error details

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can execute any system operation using `collabiq` command without knowing script paths (100% of operations accessible via CLI)
- **SC-002**: Admin can check overall system health in under 5 seconds using `collabiq status`
- **SC-003**: Admin can run complete E2E test on 10 emails and receive detailed report in under 3 minutes
- **SC-004**: All commands provide actionable error messages that suggest remediation steps (100% of error cases include next steps)
- **SC-005**: Admin can discover and learn any command using `--help` without external documentation (measured by help text completeness covering all options and examples)
- **SC-006**: CLI operations produce consistent structured output enabling scripting (all commands support `--json` flag)
- **SC-007**: Interrupted operations can be resumed without data loss (100% of long-running operations support resume or save progress)
- **SC-008**: Admin can diagnose and resolve common issues using CLI tools alone, reducing need for code inspection (reduces support requests by 60%)
- **SC-009**: Non-processing commands (verify, status, list, show) complete in under 2 seconds
- **SC-010**: Admin task completion time improves by 50% compared to using individual scripts (measured by average time for common workflows)
- **SC-011**: System provides real-time feedback for operations longer than 2 seconds (progress indicators show status updates at least every 5 seconds)
- **SC-012**: Error messages include context and remediation suggestions for 100% of error types

## Dependencies & Assumptions

### Dependencies

- Existing email receiver, content normalizer, LLM adapters, and Notion integrator components (Phase 2e complete)
- Gmail API, Gemini API, and Notion API connectivity
- Python 3.12+ with typer, rich, click libraries
- File-based data storage in `data/` directory structure
- Error handling system with DLQ support (Phase 2e)
- E2E testing infrastructure (Phase 2e)

### Assumptions

- Single admin user per environment (no multi-user coordination or access control needed)
- Admin has shell access to server/container where CollabIQ runs
- Admin is comfortable with command-line tools and terminal operations
- All API credentials are configured via Infisical or .env files before CLI use
- System logs are writable and accessible for CLI audit trail
- Python virtual environment is activated when running `collabiq` command
- Test email selection can use existing heuristics (Korean text detection, collaboration patterns)
- Admin will run CLI commands manually (not automated via cron or scheduler)

### Out of Scope

- Web-based admin UI or dashboard (CLI only for this feature)
- Multi-user access control, permissions, or audit trails (single admin assumed)
- Real-time push notifications or alerting (admin must run commands to check status)
- Automated scheduling or cron integration (admin triggers operations manually)
- Performance profiling or detailed optimization tools (basic metrics only)
- Database schema migrations or Notion schema management
- Backup and restore operations (separate operational concern)
- Log rotation or log file management (relies on system log management)
- Auto-completion for shell (bash/zsh completion files)
- Interactive prompts or wizards for complex workflows

## Technical Constraints

- Must maintain backward compatibility with existing `uv run python src/cli.py` scripts during transition period
- Must not introduce new external dependencies beyond Python standard library, typer, rich, and click
- Must work in containerized environments without interactive TTY features
- Must respect existing data directory structure (`data/raw/`, `data/cleaned/`, `data/e2e_test/`)
- Must integrate with existing error handling and retry mechanisms without modification
- Command execution must not hold locks or resources longer than necessary
- Must support both interactive terminal use and non-interactive automation (CI/CD)
- Must handle missing dependencies gracefully (e.g., if Infisical is unavailable, fall back to .env)

## Security Considerations

- Configuration display must mask sensitive values (API keys, tokens, passwords) showing only partial data
- Error messages and logs must not expose sensitive data (email content, API keys) in stack traces
- Test data cleanup must completely remove test entries from Notion to prevent data leakage
- CLI operations must validate and sanitize user input to prevent command injection
- Log files containing CLI operations must be protected with appropriate file permissions (600 or 640)
- JSON output mode must not expose secrets even when requested (always mask sensitive fields)
- Temporary files created during operations must be cleaned up and not contain sensitive data

## Validation Criteria

- All commands must have unit tests verifying argument parsing, validation, and help text
- Integration tests must cover complete command execution for happy paths and error scenarios
- E2E tests must validate multi-command workflows (e.g., `fetch → clean → process`, `verify → test-write → cleanup`)
- Help text must be validated for accuracy, completeness, and example correctness
- Error handling must be tested for all known failure modes (network errors, API limits, missing config, invalid input)
- Performance benchmarks must verify status command completes in <5s, E2E test on 10 emails in <3m
- JSON output must be validated for correct structure and parseability
- Color output must be tested with and without TTY (no ANSI codes in non-interactive mode)
