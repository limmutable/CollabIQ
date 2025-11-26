# CollabIQ Test Suite

**Purpose**: Comprehensive test suite for CollabIQ components

**Test Statistics**:
- Total Tests: 993 tests
- Pass Rate: 99%+ (932 passed, ~56 skipped for credential-dependent tests)
- Execution Time: ~4 minutes

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific category
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests
uv run pytest tests/e2e/            # E2E tests
uv run pytest tests/performance/   # Performance benchmarks
uv run pytest tests/fuzz/           # Fuzz testing

# Run with markers
uv run pytest -m "not e2e"         # Skip E2E tests (no credentials needed)
uv run pytest -m integration       # Only integration tests

# Run with coverage (requires pytest-cov)
uv run pytest --cov=collabiq --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_gemini_adapter.py -v
```

## Test Organization

### [unit/](unit/) - Unit Tests (31 files)
**Purpose**: Isolated component tests with mocked dependencies
- **Speed**: Fast (<0.1s per test)
- **Dependencies**: None (all external calls mocked)
- **Execution**: Every commit
- **Files**: 31 test files covering core components

### [integration/](integration/) - Integration Tests (33 files)
**Purpose**: Multi-component interaction tests
- **Speed**: Moderate (0.1-5s per test)
- **Dependencies**: May use test databases, mock APIs
- **Execution**: Pre-push, CI/CD
- **Files**: 33 test files for component interactions

### [e2e/](e2e/) - End-to-End Tests (3 files)
**Purpose**: Complete user scenarios with real APIs
- **Speed**: Slow (5-30s per test)
- **Dependencies**: Real Gmail/Notion APIs, credentials required
- **Execution**: Pre-merge, nightly
- **Files**: 3 test files for full pipeline validation

### [performance/](performance/) - Performance Tests (2 files)
**Purpose**: Load, stress, and latency benchmarks
- **Speed**: Variable (10-60s)
- **Dependencies**: Real or mock APIs
- **Execution**: Weekly, on-demand
- **Files**: 2 test files with performance thresholds

### [fuzz/](fuzz/) - Fuzz Tests (2 files)
**Purpose**: Randomized input testing for edge cases
- **Speed**: Variable (5-30s)
- **Dependencies**: None (generates random inputs)
- **Execution**: Weekly, on-demand
- **Files**: 2 test files for input validation

### [contract/](contract/) - Contract Tests (20 files)
**Purpose**: External API contract validation
- **Speed**: Moderate (1-5s per test)
- **Dependencies**: Real API calls (Notion, Gmail)
- **Execution**: Weekly, API version changes
- **Files**: 20 test files validating external APIs

### [manual/](manual/) - Manual Test Scripts (6 files)
**Purpose**: Human-executed validation and exploratory testing
- **Speed**: Not automated
- **Dependencies**: Varies
- **Execution**: As needed
- **Files**: 6 scripts for manual verification

### [validation/](validation/) - Validation Tests (1 file)
**Purpose**: Historical validation and acceptance tests
- **Speed**: Variable
- **Dependencies**: May require real APIs
- **Execution**: As needed
- **Files**: 1 validation script

## Test Utilities

Shared test utilities are in `src/collabiq/test_utils/`:
- `fixtures.py`: Pytest fixtures for test data and objects
- `mocks.py`: Mock implementations of external services
- `assertions.py`: Custom assertion helpers
- `helpers.py`: Test helper functions

## Test Fixtures

Sample data and test fixtures are in `tests/fixtures/`:
- `sample_emails/`: Email test data
- `mocks/`: Mock API responses
- `ground_truth/`: Expected outputs for validation
- `evaluation/`: Evaluation datasets
- `infisical/`: Infisical test data

## Test Markers

Available pytest markers:
- `@pytest.mark.e2e`: End-to-end tests (requires credentials)
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance benchmarks
- `@pytest.mark.fuzz`: Fuzz tests
- `@pytest.mark.notion`: Requires Notion API
- `@pytest.mark.gmail`: Requires Gmail API

Skip markers:
```bash
pytest -m "not e2e"           # Skip E2E tests
pytest -m "not integration"   # Skip integration tests
pytest -m "not performance"   # Skip performance tests
```

## Coverage Reports

Coverage reports are generated in `tests/coverage_reports/`:
- `htmlcov/`: HTML coverage report (open `index.html`)
- `coverage.xml`: XML coverage report (for CI/CD)
- `coverage.json`: JSON coverage report

## Continuous Integration

For CI/CD environments:
```yaml
# GitHub Actions example
- name: Run tests
  run: |
    # Fast tests (unit + integration without real APIs)
    uv run pytest tests/unit tests/integration -m "not e2e" -v

    # E2E tests (if credentials available)
    if [ -n "$NOTION_API_KEY" ]; then
      uv run pytest tests/e2e/ -v
    fi
  env:
    NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

## Related Documentation

- [Testing Guide](../docs/testing/TESTING_GUIDE.md): Comprehensive testing strategies
- [E2E Testing](../docs/testing/E2E_TESTING.md): End-to-end test setup and execution
- [Test Results](../docs/testing/E2E_TEST_RESULTS_FINAL_20251109.md): Latest test execution results

---

**Test Suite Version**: 2.1 (Phase 017 test fixes)
**Last Updated**: 2025-11-26
**Status**: 993 tests, 99%+ pass rate (credential-dependent tests properly skipped)
