# Quickstart Guide: Test Suites Improvements

**Feature Branch**: `015-test-suite-improvements` | **Date**: 2025-11-11 | **Plan**: /Users/jlim/Projects/CollabIQ/specs/015-test-suite-improvements/plan.md

## Overview

This guide provides a quick overview of how to set up and run the enhanced test suites for the CollabIQ project. These improvements focus on achieving truly end-to-end automated testing, robust date extraction, optimized LLM performance, granular coverage, formal performance testing, and expanded negative/fuzz testing.

## Prerequisites

Ensure you have completed the standard CollabIQ project setup, including:
- Python 3.12+ installed.
- UV package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Project dependencies installed (`make install`).
- `.env` configured with necessary LLM API keys, Notion API token, and Gmail OAuth2 credentials.
- Gmail OAuth2 authentication completed (`uv run python scripts/authenticate_gmail.py`).

## 1. Setting up Test Accounts (for E2E with Real Integrations)

To run truly end-to-end automated tests with real Gmail fetching and Notion writes, you will need:

1.  **Dedicated Test Gmail Account**: Create a separate Gmail account for testing. This account should have minimal sensitive data.
2.  **Dedicated Test Notion Database**: Create a new Notion database specifically for test entries. This prevents test data from polluting your production Notion databases.

Update your `.env` file or a separate test configuration file with the credentials for these test accounts. Ensure the test Gmail account has OAuth2 authentication set up as per the standard project instructions.

## 2. Running Enhanced Test Suites

### 2.1. Running All Tests (including new suites)

To run all tests, including the newly introduced performance and fuzz tests, use the standard `make test` command:

```bash
make test
```

### 2.2. Running Specific Test Suites

To run specific test suites, you can use `pytest` directly:

*   **Unit Tests**:
    ```bash
    uv run pytest tests/unit/ -v
    ```
*   **Integration Tests**:
    ```bash
    uv run pytest tests/integration/ -v
    ```
*   **End-to-End (E2E) Tests (with real integrations)**:
    ```bash
    # Ensure your test Gmail and Notion credentials are configured
    uv run pytest tests/e2e/test_full_pipeline.py -v
    ```
*   **Performance Tests**:
    ```bash
    uv run pytest tests/performance/ -v
    ```
*   **Fuzz Tests**:
    ```bash
    uv run pytest tests/fuzz/ -v
    ```

### 2.3. Generating Granular Coverage Reports

To generate separate coverage reports for different test types, you will need to configure `pytest-cov` (details on specific configuration will be provided during implementation). Once configured, you might run commands similar to:

```bash
# Example: Unit test coverage
uv run pytest tests/unit/ --cov=src --cov-report=html:htmlcov/unit_coverage

# Example: Integration test coverage
uv run pytest tests/integration/ --cov=src --cov-report=html:htmlcov/integration_coverage

# Example: E2E test coverage
uv run pytest tests/e2e/ --cov=src --cov-report=html:htmlcov/e2e_coverage
```

### 2.4. Running LLM Benchmarking Suite

To run the dedicated LLM benchmarking suite for language performance (e.g., Korean text extraction):

```bash
uv run python scripts/benchmark_llm_performance.py --detailed
```

### 2.5. Running Fuzz Testing Scripts

To execute fuzz testing for input parsing and data validation:

```bash
uv run python scripts/fuzz_test_inputs.py --target-module src/content_normalizer/normalizer.py
```

## 3. Reviewing Test Results

*   **Standard Test Results**: View `pytest` output in the console.
*   **Coverage Reports**: Open the generated HTML files (e.g., `htmlcov/unit_coverage/index.html`) in your web browser.
*   **LLM Benchmarking Reports**: Results will be stored in `data/test_metrics/llm_benchmarking_report.json` (or similar).
*   **Performance Test Reports**: Results will be stored in `data/test_metrics/performance_report.json` (or similar).
*   **Fuzz Test Findings**: Findings (e.g., crashes, unexpected behavior) will be logged and potentially stored in `data/test_metrics/fuzz_findings.json`.

This quickstart guide will be further detailed during the implementation phase.