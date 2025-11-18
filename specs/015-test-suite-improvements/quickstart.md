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

Coverage reporting is fully configured with `pytest-cov`. Generate separate coverage reports for different test types:

```bash
# All tests with combined coverage
uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

# Unit test coverage only
uv run pytest tests/unit/ --cov=src \
  --cov-report=html:tests/coverage_reports/unit_htmlcov \
  --cov-report=term \
  -m "not integration and not e2e"

# Integration test coverage only
uv run pytest tests/integration/ --cov=src \
  --cov-report=html:tests/coverage_reports/integration_htmlcov \
  --cov-report=term \
  -m "integration and not e2e"

# E2E test coverage only
uv run pytest tests/e2e/ --cov=src \
  --cov-report=html:tests/coverage_reports/e2e_htmlcov \
  --cov-report=term \
  -m "e2e"

# View HTML coverage report
open tests/coverage_reports/htmlcov/index.html
```

For detailed coverage documentation, see [tests/coverage_reports/README.md](../../tests/coverage_reports/README.md).

### 2.4. Running LLM Benchmarking Suite

Run the LLM benchmarking suite to test prompt variations and performance:

```bash
# Run benchmark with default samples
uv run python scripts/benchmark_llm_performance.py --provider gemini

# Run with Korean samples (20 emails)
uv run python scripts/benchmark_llm_performance.py \
  --provider gemini \
  --test-data data/test_metrics/korean_benchmark_samples.json \
  --output-dir data/test_metrics/prompt_benchmarks

# Compare two prompts
uv run python scripts/benchmark_llm_performance.py \
  --compare \
  --baseline baseline \
  --test structured_output
```

Results are stored in `data/test_metrics/prompt_benchmarks/` with detailed metrics.

### 2.5. Running Fuzz Testing Campaigns

Execute comprehensive fuzz testing campaigns against system components:

```bash
# Run all fuzz campaigns (date parser, extraction validation)
uv run python scripts/fuzz_test_inputs.py --target all --count 20

# Test date parser only
uv run python scripts/fuzz_test_inputs.py --target date_parser --count 100

# Test extraction validation only
uv run python scripts/fuzz_test_inputs.py --target extraction_validation --count 50

# Custom output directory
uv run python scripts/fuzz_test_inputs.py \
  --target all \
  --count 50 \
  --output-dir data/test_metrics/fuzz_results
```

### 2.6. Running Performance Tests

Execute performance tests with defined thresholds:

```bash
# Run all performance tests (non-integration)
uv run pytest tests/performance/ -v -m "not integration and not e2e"

# Run integration performance tests (requires API keys)
uv run pytest tests/performance/ -v -m "integration"

# Run specific performance test class
uv run pytest tests/performance/test_performance.py::TestPerformanceMonitorUtility -v
```

## 3. Reviewing Test Results

### Test Output
*   **Standard Test Results**: View `pytest` output in the console with `-v` for verbose mode
*   **Test Markers**: Use `-m` to filter tests: `"not integration"`, `"e2e"`, `"integration"`

### Coverage Reports
*   **HTML Reports**:
    - All tests: `tests/coverage_reports/htmlcov/index.html`
    - Unit only: `tests/coverage_reports/unit_htmlcov/index.html`
    - Integration only: `tests/coverage_reports/integration_htmlcov/index.html`
    - E2E only: `tests/coverage_reports/e2e_htmlcov/index.html`
*   **Terminal Reports**: Shown automatically with `--cov-report=term`
*   **JSON/XML Reports**: Generated in `tests/coverage_reports/` for CI/CD

### LLM Benchmarking Reports
*   **Individual Results**: `data/test_metrics/prompt_benchmarks/*.json`
*   **Summary Report**: `data/test_metrics/prompt_optimization_results.md`
*   **Winning Prompt**: See `src/collabiq/llm_benchmarking/prompt_optimizer.py`

### Performance Test Reports
*   **Metrics JSON**: `data/test_metrics/performance/*.json`
*   **Test Output**: Console shows performance metrics and threshold violations
*   **Thresholds**: Defined in `src/collabiq/test_utils/performance_thresholds.py`

### Fuzz Test Reports
*   **Campaign Results**: `data/test_metrics/fuzz_results/fuzz_results_*.json`
*   **Markdown Reports**: `data/test_metrics/fuzz_results/fuzz_report_*.md`
*   **Test Output**: Console shows success rates and error types

## 4. Test Suite Summary

### Implemented Features
- ✅ **User Story 1**: Real E2E testing with Gmail/Notion (6 tests, all passing)
- ✅ **User Story 2**: Date parser library with 98% accuracy target
- ✅ **User Story 3**: LLM benchmarking with 5 prompt variations
- ✅ **User Story 4**: Granular coverage reporting (HTML, XML, JSON)
- ✅ **User Story 5**: Performance testing framework (13 tests)
- ✅ **User Story 6**: Negative testing & fuzzing (35+ tests)

### Test Statistics (as of 2025-11-18)
- **Total Tests**: 100+ tests across all suites
- **E2E Tests**: 6 tests (71s runtime)
- **Performance Tests**: 13 tests (8 unit + 5 integration)
- **Fuzz Tests**: 23 tests (non-integration)
- **Error Handling**: 12 tests
- **API Error Tests**: 18 integration tests
- **Coverage Target**: 85%+ overall

### Key Improvements
1. **Production Impact**: Structured output prompt (100% success rate, 95% startup/90% person extraction)
2. **Date Accuracy**: Enhanced date_parser with 98% target accuracy
3. **Robustness**: Comprehensive fuzz testing with 8 categories
4. **Performance**: Formalized thresholds and monitoring
5. **Quality**: Granular coverage tracking by test suite