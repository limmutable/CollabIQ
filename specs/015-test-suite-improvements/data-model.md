# Data Model: Test Suites Improvements

**Feature Branch**: `015-test-suite-improvements` | **Date**: 2025-11-11 | **Plan**: /Users/jlim/Projects/CollabIQ/specs/015-test-suite-improvements/plan.md

## Overview

This document outlines the key entities and their attributes involved in the 'Test Suites Improvements' feature. These entities primarily represent testing artifacts, configurations, and metrics necessary to achieve robust and comprehensive test coverage and performance validation.

## Key Entities

### 1. Test Email Data

**Description**: Represents emails fetched from a real Gmail account for automated end-to-end testing purposes.

**Attributes**:
- `content`: The raw and cleaned text content of the email.
- `sender`: The sender's email address.
- `recipient`: The recipient's email address.
- `subject`: The subject line of the email.
- `date`: The date and time the email was sent or received (raw string and normalized format).
- `attachments`: (Optional) Metadata or content of email attachments, if relevant for testing specific parsing scenarios.
- `email_id`: Unique identifier for the email.

**Relationships**:
- Can be linked to `Test Notion Entries` upon successful processing and extraction.

**Validation Rules**:
- Content must be non-empty after cleaning.
- Date must be parsable and normalizable.

### 2. Test Notion Entries

**Description**: Represents data created in a dedicated Notion database during automated end-to-end tests.

**Attributes**:
- `notion_page_id`: Unique identifier for the Notion page created.
- `extracted_entities`: A structured representation of entities extracted from the email (person, startup, partner, details, date, classification, summary, etc.).
- `status`: Status of the Notion entry creation (e.g., 'success', 'failed', 'duplicate').
- `creation_timestamp`: Timestamp when the Notion entry was created.

**Relationships**:
- Has a many-to-one relationship with `Test Email Data` (each Notion entry originates from an email).

**Validation Rules**:
- Essential fields within `extracted_entities` must be populated correctly.
- Must conform to the Notion database schema.

### 3. Date Formats

**Description**: Represents various representations of dates used in emails, including standard and edge cases, especially in Korean.

**Attributes**:
- `raw_date_string`: The original date string extracted from an email.
- `normalized_date`: The standardized and parsed `datetime` object.
- `locale`: The language locale of the date string (e.g., 'en', 'ko').
- `format_pattern`: The regex or format string used for parsing.

**Validation Rules**:
- `normalized_date` must accurately reflect the `raw_date_string`.
- Module accurately handles diverse date formats.

### 4. LLM Performance Metrics

**Description**: Data points tracking the confidence, completeness, and accuracy of LLM entity extraction for benchmarking and optimization.

**Attributes**:
- `llm_provider`: Identifier for the LLM service (e.g., 'Gemini', 'Claude', 'OpenAI').
- `metric_type`: Type of metric (e.g., 'confidence', 'completeness', 'accuracy').
- `field_name`: The specific entity field being measured (e.g., 'person', 'date', 'startup').
- `value`: The numerical value of the metric.
- `timestamp`: When the metric was recorded.
- `test_run_id`: Identifier for the specific benchmarking run.

**Relationships**:
- Associated with `Test Email Data` (input to LLM) and `Test Notion Entries` (extracted output).

**Validation Rules**:
- Metrics must be consistently collected and calculated.
- Benchmark results should be reproducible.

### 5. Code Coverage Reports

**Description**: Documents detailing the extent to which source code is executed by different test suites.

**Attributes**:
- `report_id`: Unique identifier for the coverage report.
- `test_suite_type`: Type of test suite (e.g., 'unit', 'integration', 'e2e').
- `coverage_percentage`: Overall percentage of code covered.
- `covered_files`: List of files included in the report.
- `lines_covered`: Number of lines executed.
- `lines_uncovered`: Number of lines not executed.
- `report_path`: File path to the generated HTML or XML report.

**Validation Rules**:
- Reports must accurately reflect code execution.
- Must be generated consistently for each test suite type.

### 6. Performance Metrics

**Description**: Measurements of system speed, responsiveness, and stability under various loads.

**Attributes**:
- `metric_name`: Name of the performance metric (e.g., 'avg_email_processing_time', 'llm_response_latency', 'notion_write_latency').
- `value`: Measured performance value.
- `unit`: Unit of measurement (e.g., 'seconds', 'milliseconds', 'req/s').
- `threshold`: The defined acceptable limit for the metric.
- `pass_fail_status`: Indicates if the metric met its threshold.
- `timestamp`: When the metric was recorded.
- `test_run_id`: Identifier for the specific performance test run.

**Relationships**:
- None directly, but reflects the performance of operations involving `Test Email Data` and `Test Notion Entries`.

**Validation Rules**:
- Measurements must be accurate and repeatable.
- Must trigger a failure if `value` exceeds `threshold`.

### 7. Negative Test Cases

**Description**: Scenarios designed to test the system's behavior with invalid, malformed, or unexpected inputs or external API errors.

**Attributes**:
- `case_id`: Unique identifier for the negative test case.
- `input_data`: The specific invalid or problematic input used.
- `expected_behavior`: How the system is expected to react (e.g., log error, return specific error code, graceful degradation).
- `actual_outcome`: The observed system behavior.
- `module_affected`: The system module or component being tested.

**Validation Rules**:
- System must not crash or produce unhandled exceptions.
- Error messages or fallback mechanisms must be user-friendly and informative.

### 8. Fuzz Test Configurations and Data

**Description**: Data and configurations used for fuzz testing input parsing and validation components.

**Attributes**:
- `fuzz_target`: The specific function or module being fuzzed.
- `input_generation_strategy`: Method used to generate varied inputs (e.g., random, mutated).
- `corpus_path`: Path to seed input data for fuzzing.
- `findings`: List of issues or crashes found during fuzzing.
- `fuzz_run_id`: Identifier for the specific fuzzing campaign.

**Validation Rules**:
- Fuzzing should effectively explore input space.
- Identified issues should be reproducible.