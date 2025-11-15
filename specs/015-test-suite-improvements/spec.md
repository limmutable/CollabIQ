# Feature Specification: Test Suites Improvements

**Feature Branch**: `015-test-suite-improvements`  
**Created**: 2025-11-11  
**Status**: Draft  
**Input**: User description: "Plan Phase 3e in roadmap.md. Read @testing_strategy_review_20251111_112917.md for more details when planning."

## User Scenarios & Testing

### User Story 1 - Achieve Truly End-to-End Automated Testing & Test Suite Refinement (Priority: P1)

As an administrator, I want the automated end-to-end test suite to fetch real emails and perform real Notion writes, and I also want to ensure all existing test suites and scripts are reviewed, refactored where necessary, and fully functional, so that the entire system pipeline is validated with actual external integrations, and the overall test infrastructure is robust, efficient, and reliable.

**Why this priority**: This directly addresses a critical gap in current automated testing by moving from mocked email bodies to real data, which is essential for validating the system's core functionality in a near-production environment. Additionally, a thorough review and refinement of existing test assets will improve maintainability and confidence in the entire testing framework.

**Independent Test**: This can be fully tested by:
1.  Running the automated E2E suite with configured test credentials for Gmail and Notion, observing successful email fetching, processing, Notion entry creation, and subsequent cleanup. This delivers value by providing a higher fidelity automated test of the full system.
2.  Independently executing all existing test scripts and suites, verifying their successful completion and logical correctness. This delivers value by ensuring the foundational testing infrastructure is sound.

**Acceptance Scenarios**:

1.  **Given** a configured test Gmail account and Notion database, **When** the automated E2E test suite is executed, **Then** real emails are fetched from Gmail.
2.  **Given** real emails are fetched and processed, **When** the automated E2E test suite proceeds, **Then** corresponding entries are created in the test Notion database.
3.  **Given** entries are created in the test Notion database, **When** the automated E2E test suite completes, **Then** a robust cleanup mechanism removes the test entries from Notion.
4.  **Given** all existing test suites and scripts, **When** they are executed, **Then** all tests run successfully without errors and their outputs are logically sound.
5.  **Given** the existing test codebase, **When** a refactoring analysis is performed, **Then** identified opportunities for improving test structure, readability, and efficiency are documented in `specs/015-test-suite-improvements/refactoring_analysis.md` and prioritized by impact on maintainability and test execution time.

---

### User Story 2 - Enhance Date Extraction Testing and Robustness (Priority: P1)

As a system maintainer, I want date extraction to be highly robust and thoroughly tested across various formats, especially Korean, so that the system accurately extracts and normalizes date information from emails, reducing manual correction efforts.

**Why this priority**: The current reports indicate struggles with date extraction across LLM providers. Improving this directly impacts data accuracy and reduces post-processing work.

**Independent Test**: This can be tested independently by providing a diverse dataset of emails with various date formats (including Korean) to a dedicated date parsing module and verifying the accuracy and consistency of the extracted and normalized dates. It delivers value by improving the reliability of a key data point.

**Acceptance Scenarios**:

1.  **Given** an email containing a date in a standard Korean format, **When** the system processes the email, **Then** the date is accurately extracted and normalized.
2.  **Given** an email containing an ambiguous or edge-case date format, **When** the system processes the email, **Then** the date is handled gracefully by logging a warning and either extracting a best-effort date or flagging the email for manual review in the Dead Letter Queue (DLQ).
3.  **Given** a dedicated date parsing module, **When** comprehensive unit and integration tests are run against it, **Then** the module demonstrates high accuracy across various date formats and edge cases.

---

### User Story 3 - Improve LLM Performance for Korean Text (Priority: P2)

As a system administrator, I want to systematically evaluate and optimize LLM performance for Korean text extraction, so that the system can leverage the best-performing LLM for Korean content, improving overall extraction quality and efficiency.

**Why this priority**: OpenAI's lower performance on Korean text suggests an opportunity for optimization, which can lead to better quality and potentially cost savings by routing Korean content to more efficient providers.

**Independent Test**: This can be tested by running a dedicated benchmarking suite with Korean text samples across different LLM providers and prompt variations, tracking metrics like confidence, completeness, and accuracy. It delivers value by enabling data-driven decisions for LLM routing and prompt engineering.

**Acceptance Scenarios**:

1.  **Given** a benchmarking suite for language performance, **When** it is executed with Korean text samples across multiple LLM providers, **Then** it systematically tracks and reports metrics such as confidence, completeness, and accuracy for entity extraction.
2.  **Given** various prompt engineering strategies for Korean text, **When** A/B tests are conducted using the benchmarking suite, **Then** the impact of different prompts on quality metrics is measurable.

---

### User Story 4 - Granular Test Coverage Reporting (Priority: P3)

As a developer, I want to generate separate code coverage reports for unit, integration, and end-to-end test suites, so that I can easily identify areas lacking specific types of test coverage and improve the quality of each test layer.

**Why this priority**: This enhances developer productivity and code quality by providing more targeted insights into test coverage, allowing for more efficient test suite maintenance.

**Independent Test**: This can be tested by configuring the test runner to generate separate coverage reports for different test suites (e.g., unit, integration, E2E) and verifying that distinct reports are produced, accurately reflecting the coverage of each layer. It delivers value by improving the visibility of test coverage.

**Acceptance Scenarios**:

1.  **Given** the test environment is set up, **When** unit tests are run, **Then** a dedicated code coverage report for unit tests is generated.
2.  **Given** the test environment is set up, **When** integration tests are run, **Then** a dedicated code coverage report for integration tests is generated.
3.  **Given** the test environment is set up, **When** E2E tests are run, **Then** a dedicated code coverage report for E2E tests is generated.

---

### User Story 5 - Formalize Performance Testing (Priority: P2)

As a system operator, I want to have a formalized performance test suite with defined thresholds, so that I can continuously monitor the system's performance, identify regressions, and ensure it meets operational requirements.

**Why this priority**: Performance is critical for system reliability and user experience. Formalizing this ensures that performance is consistently tracked and validated.

**Independent Test**: This can be tested by running a dedicated performance test suite that measures key metrics (e.g., processing time, response times) under various conditions and asserts against predefined thresholds. It delivers value by ensuring the system consistently meets performance expectations.

**Acceptance Scenarios**:

1.  **Given** a dedicated performance test suite, **When** it is executed, **Then** it measures key performance metrics such as average processing time per email, LLM response times, and Notion write latency.
2.  **Given** defined performance thresholds, **When** the performance test suite runs, **Then** it includes assertions that fail if these thresholds are exceeded.

---

### User Story 6 - Expand Negative Testing and Edge Cases (Priority: P2)

As a quality assurance engineer, I want a comprehensive set of negative test cases and fuzz testing capabilities, so that the system is robust against invalid inputs, external API errors, and unexpected data scenarios, minimizing production bugs.

**Why this priority**: Proactive testing for negative scenarios and edge cases significantly improves system resilience and reduces the likelihood of unexpected failures in production.

**Independent Test**: This can be tested by systematically introducing invalid inputs, simulating API errors, and using fuzzing techniques against various modules, then verifying that the system handles these scenarios gracefully without crashing or producing incorrect output. It delivers value by enhancing the system's fault tolerance.

**Acceptance Scenarios**:

1.  **Given** a module that processes external input, **When** invalid input formats (e.g., malformed emails, incorrect API responses) are provided, **Then** the system handles them gracefully without crashing.
2.  **Given** an external API dependency, **When** errors (e.g., LLM API returning 500, Notion API rate limits) are simulated, **Then** the system's error handling mechanisms (e.g., retries, circuit breakers) function as expected.
3.  **Given** a data processing pipeline, **When** missing or incomplete data is introduced at various stages, **Then** the system processes it without critical errors or flags it appropriately.
4.  **Given** input parsing and data validation components, **When** fuzz testing is applied, **Then** unexpected vulnerabilities or bugs related to input handling are identified.
5.  **Given** input parsing and data validation components, **When** fuzz testing is applied with at least 1000 randomized inputs, **Then** unexpected vulnerabilities or bugs related to input handling are identified and logged to `data/test_metrics/fuzz_results.json`.
6.  **Given** fuzz testing results, **When** critical vulnerabilities are found, **Then** they are categorized by severity (critical/high/medium/low) and corresponding bug fix tasks are created.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST allow for automated E2E testing that integrates with real Gmail accounts for email fetching.
- **FR-002**: The system MUST support automated E2E testing that performs real Notion writes to a dedicated test database.
- **FR-003**: The system MUST include a robust cleanup mechanism for test entries created in the Notion database during automated E2E tests, with the following properties:
  - **Idempotency**: Can be run multiple times safely without side effects
  - **Retry Logic**: Automatically retries failed deletions with exponential backoff (max 3 attempts)
  - **Verification**: Confirms all test entries removed via post-cleanup query
  - **Error Handling**: Logs failures to stderr, continues cleanup for remaining entries, exits with non-zero code if any failures
  - **Selective Cleanup**: Only removes entries marked with test metadata (e.g., `test_run_id` property)
  - **Timeout Protection**: Fails gracefully if Notion API becomes unresponsive (30s timeout per operation)
- **FR-004**: The system MUST incorporate a dedicated module for date parsing and normalization, capable of handling diverse date formats, including Korean.
- **FR-005**: The system MUST implement comprehensive unit and integration tests for the dedicated date parsing module.
- **FR-006**: The system MUST provide a benchmarking suite to systematically evaluate LLM performance on Korean and English text for entity extraction.
- **FR-007**: The system MUST enable testing of different prompt engineering strategies for LLMs, particularly for Korean text, and track their impact on quality metrics.
- **FR-008**: The system MUST be configurable to generate separate code coverage reports for unit, integration, and E2E test suites.
- **FR-009**: The system MUST include a dedicated performance test suite to measure key metrics at different pipeline stages:
  - **Internal Processing Time**: Email parsing, content normalization, entity extraction (excludes external API calls)
  - **LLM API Response Time**: Time from request to response (measured at p50, p95, p99 percentiles)
  - **Notion API Write Latency**: Time to write single entry, including retry attempts
  - **End-to-End Pipeline Time**: Total time from email fetch to Notion write completion (includes all external API calls)
  - **Resource Utilization**: Memory usage, CPU usage during processing
- **FR-010**: The system MUST allow for the definition of performance thresholds and integrate assertions into performance tests to fail if these thresholds are exceeded.
- **FR-011**: The system MUST include a comprehensive set of negative test cases for each module and the overall pipeline.
- **FR-012**: The system MUST incorporate fuzz testing capabilities for input parsing and data validation.

### Key Entities

- **Test Email Data**: Represents emails fetched from a real Gmail account for testing purposes.
- **Test Notion Entries**: Represents data created in a dedicated Notion database during automated E2E tests.
- **Date Formats**: Various representations of dates, including standard and edge cases, especially in Korean.
- **LLM Performance Metrics**: Data points tracking confidence, completeness, and accuracy of LLM entity extraction.
- **Code Coverage Reports**: Documents detailing the extent to which source code is executed by test suites.
- **Performance Metrics**: Measurements of system speed, responsiveness, and stability under various loads.
- **Negative Test Cases**: Scenarios designed to test the system's behavior with invalid or unexpected inputs.

### CLI Interface Requirements (Constitution Compliance)

Per constitution principle II, all new libraries must expose CLI interfaces with text I/O protocol.

#### Date Parser CLI

**Command**: `python -m src.collabiq.date_parser.cli <input>`

- **Input**: Raw text via stdin or args (e.g., "2024년 11월 13일", "Nov 13, 2024")
- **Output**: JSON to stdout: `{"parsed_date": "2024-11-13", "format_detected": "korean_ymd", "confidence": 0.95}`
- **Output (Human)**: `--format=text` flag: "Parsed: 2024-11-13 (Korean YMD format, 95% confidence)"
- **Errors**: stderr with exit code 1

#### LLM Benchmarking CLI

**Command**: `python -m src.collabiq.llm_benchmarking.cli --provider=<name> --dataset=<path>`

- **Input**: Args for provider selection, dataset path (JSON file with test cases)
- **Output**: JSON to stdout with metrics: `{"provider": "gemini", "accuracy": 0.92, "avg_time": 2.1, "confidence": 0.88}`
- **Output (Human)**: `--format=text` flag: Table format with results
- **Errors**: stderr with exit code 1

#### Test Utils CLI

**Command**: `python -m src.collabiq.test_utils.cli cleanup --database-id=<id>`

- **Input**: Args for operation (cleanup/monitor), database ID
- **Output**: JSON to stdout: `{"cleaned": 15, "errors": 0, "duration": 3.2}`
- **Output (Human)**: `--format=text` flag: "Cleaned 15 entries in 3.2s"
- **Errors**: stderr with exit code 1

## Success Criteria

### Measurable Outcomes

- **SC-001**: Automated E2E tests successfully fetch real emails and write to a test Notion database with cleanup, achieving a success rate of at least 95% (baseline: manual testing only, no automated real-API tests).
- **SC-002**: Date extraction robustness is significantly improved, with the dedicated date parsing module achieving at least 98% accuracy across diverse date formats in unit and integration tests (baseline: ~85% accuracy based on testing_strategy_review report).
- **SC-003**: LLM performance on Korean text is systematically benchmarked, and prompt optimization tests demonstrate at least a 10% improvement in accuracy or confidence for the selected LLM on Korean content (baseline: current OpenAI performance ~70% on Korean per testing report).
- **SC-004**: Granular test coverage reports are available for unit, integration, and E2E tests, providing clear visibility into coverage percentages for each layer (baseline: single combined coverage report only).
- **SC-005**: A performance test suite with defined thresholds is integrated into the CI/CD pipeline, and the system consistently meets all defined performance thresholds:
  - **Email processing (internal)**: < 2 seconds (baseline: ~1.5s measured, excludes external API calls)
  - **LLM API response times**: < 5 seconds at p95 (baseline: 2-8s variable, per testing report)
  - **Notion write operations**: < 3 seconds (baseline: ~2s measured)
  - **End-to-end pipeline**: < 15 seconds total (baseline: 10-20s variable)
- **SC-006**: Comprehensive negative test cases and fuzz testing are implemented, leading to the identification and resolution of at least 5 critical or high-severity bugs related to robustness and error handling (baseline: no systematic negative testing, bugs found reactively).