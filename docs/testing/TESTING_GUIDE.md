# CollabIQ Testing Guide

**Last Updated**: November 26, 2025
**Test Suite Status**: ✅ 99%+ Pass Rate (993 tests, 933 passed, 57 skipped, 3 xfailed)
**Phase**: 017 Production Readiness Complete

## Quick Start

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test category
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/contract/ -v
uv run pytest tests/e2e/ -v
```

---

## Prerequisites

### 1. Python Environment
- **Python 3.12+** installed
- **UV package manager** installed:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 2. Install Dependencies
```bash
# Install all project dependencies
uv sync

# Or use make command
make install
```

### 3. Environment Configuration
Create a `.env` file in the project root with:
```bash
# LLM API Keys
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Notion Configuration
NOTION_API_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id

# Gmail Configuration (for E2E tests)
# Run: uv run python scripts/setup/authenticate_gmail.py
GMAIL_OAUTH_TOKEN_PATH=path/to/token.json
GMAIL_OAUTH_CREDENTIALS_PATH=path/to/credentials.json
```

---

## Test Suite Structure

### Test Categories

| Category | Files | Tests | Purpose | Speed |
|----------|-------|-------|---------|-------|
| **Unit Tests** | 31 | ~300 | Test individual functions/classes | Fast (< 0.1s) |
| **Integration Tests** | 33 | ~350 | Test component interactions | Medium (0.1-5s) |
| **Contract Tests** | 20 | ~150 | Verify API contracts | Fast (< 1s) |
| **E2E Tests** | 3 | ~10 | Full pipeline validation | Slow (5-30s) |
| **Performance Tests** | 2 | ~15 | Benchmark with thresholds | Variable |
| **Fuzz Tests** | 2 | ~25 | Randomized input testing | Variable |
| **Manual Tests** | 6 | ~10 | Require manual auth setup | N/A |
| **Total** | **97** | **993** | All automated tests | ~6 min |

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests (31 files)
│   ├── test_*.py
│   └── ...
├── integration/             # Component interaction tests (33 files)
│   ├── test_*.py
│   └── ...
├── contract/                # API contract tests (20 files)
│   ├── test_*.py
│   └── ...
├── e2e/                     # End-to-end tests (3 files)
│   ├── test_full_pipeline.py
│   ├── test_real_gmail_notion.py
│   └── test_cli_extraction.py
├── performance/             # Performance benchmarks (2 files)
│   └── test_performance.py
├── fuzz/                    # Fuzz tests (2 files)
│   └── test_fuzzing.py
├── manual/                  # Manual authentication tests (6 files)
│   └── test_infisical_connection.py
├── fixtures/                # Shared test fixtures
│   └── sample_emails/
└── conftest.py             # Global pytest configuration
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests (quiet mode)
uv run pytest -q

# Run all tests (verbose mode)
uv run pytest -v

# Run all tests (very verbose with test docstrings)
uv run pytest -vv

# Run with output capture disabled (see print statements)
uv run pytest -s
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Contract tests only
uv run pytest tests/contract/ -v

# E2E tests only (requires API credentials)
uv run pytest tests/e2e/ -v

# Run tests by marker
uv run pytest -m "not e2e" -v  # Skip E2E tests
```

### Run Specific Test Files

```bash
# Single test file
uv run pytest tests/unit/test_cost_tracker.py -v

# Multiple test files
uv run pytest tests/unit/test_cost_tracker.py tests/unit/test_health_tracker.py -v
```

### Run Specific Tests

```bash
# Single test function
uv run pytest tests/unit/test_cost_tracker.py::test_cost_tracker_initialization -v

# Single test class
uv run pytest tests/integration/test_duplicate_detection.py::TestDuplicateDetection -v

# Single test method in a class
uv run pytest tests/integration/test_duplicate_detection.py::TestDuplicateDetection::test_duplicate_detection_skip_behavior -v
```

### Filtering Tests by Name Pattern

```bash
# Run tests matching pattern
uv run pytest -k "duplicate" -v

# Run tests NOT matching pattern
uv run pytest -k "not duplicate" -v

# Run tests matching multiple patterns (OR)
uv run pytest -k "duplicate or cache" -v

# Run tests matching multiple patterns (AND)
uv run pytest -k "duplicate and skip" -v
```

---

## Test Output and Reporting

### Basic Output Options

```bash
# Quiet mode (dots only)
uv run pytest -q

# Verbose mode (test names)
uv run pytest -v

# Show test summary info
uv run pytest --tb=short

# Show only failures
uv run pytest --tb=line

# No traceback
uv run pytest --tb=no
```

### Coverage Reports

```bash
# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Performance and Timing

```bash
# Show slowest 10 tests
uv run pytest --durations=10

# Show slowest 20 tests
uv run pytest --durations=20

# Show all test durations
uv run pytest --durations=0
```

---

## Debugging Tests

### Stop on First Failure

```bash
# Stop at first failure
uv run pytest -x

# Stop after N failures
uv run pytest --maxfail=3
```

### Interactive Debugging

```bash
# Drop into debugger on failure
uv run pytest --pdb

# Drop into debugger on failure, show locals
uv run pytest --pdb --showlocals
```

### Verbose Error Output

```bash
# Show full diff on assertion errors
uv run pytest -vv

# Show captured stdout/stderr
uv run pytest -s

# Show full tracebacks
uv run pytest --tb=long

# Show local variables in tracebacks
uv run pytest --showlocals
```

---

## Advanced Usage

### Parallel Execution (Faster)

```bash
# Install pytest-xdist
uv add --dev pytest-xdist

# Run tests in parallel (auto-detect CPU count)
uv run pytest -n auto

# Run tests in parallel (specific worker count)
uv run pytest -n 4
```

### Re-run Failed Tests

```bash
# Run last failed tests only
uv run pytest --lf

# Run failed tests first, then others
uv run pytest --ff
```

### Test Markers

```bash
# List available markers
uv run pytest --markers

# Run tests with specific marker
uv run pytest -m "integration" -v
uv run pytest -m "not e2e" -v

# Combine markers
uv run pytest -m "integration and not slow" -v
```

---

## Common Test Scenarios

### 1. Quick Smoke Test (Unit Tests Only)
```bash
uv run pytest tests/unit/ -q
# ~30 seconds, fast feedback
```

### 2. Pre-Commit Validation
```bash
# Run all tests except E2E
uv run pytest -m "not e2e" -v
# ~2 minutes, good for pre-commit
```

### 3. Full Test Suite
```bash
# Run everything
uv run pytest -v
# ~3-4 minutes, complete validation
```

### 4. Integration Tests Only
```bash
# Test component interactions
uv run pytest tests/integration/ -v
# ~1-2 minutes
```

### 5. Contract Tests Only
```bash
# Verify API contracts
uv run pytest tests/contract/ -v
# ~30 seconds
```

### 6. E2E Tests (Requires API Credentials)
```bash
# Full pipeline validation
uv run pytest tests/e2e/ -v
# ~30 seconds, requires configured APIs
```

---

## Test Configuration

### pytest.ini / pyproject.toml

The project uses `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--strict-config",
]
markers = [
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "notion: Tests requiring Notion API",
]
```

---

## Troubleshooting

### Issue: Import Errors
```bash
# Ensure dependencies are installed
uv sync

# Verify Python version
python --version  # Should be 3.12+
```

### Issue: API Credential Errors
```bash
# Check .env file exists and has required keys
cat .env

# Re-run Gmail OAuth authentication
uv run python scripts/setup/authenticate_gmail.py
```

### Issue: Slow Tests
```bash
# Identify slow tests
uv run pytest --durations=20

# Run without E2E tests
uv run pytest -m "not e2e" -v

# Use parallel execution
uv run pytest -n auto
```

### Issue: Flaky Tests
```bash
# Run specific test multiple times
uv run pytest tests/path/to/test.py::test_name --count=10

# Show test output for debugging
uv run pytest tests/path/to/test.py::test_name -s -vv
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Writing Guidelines

### Best Practices

1. **Use descriptive test names**: `test_duplicate_detection_skip_behavior` not `test_1`
2. **One assertion per test**: Focus on testing one thing
3. **Use fixtures**: Share test setup across tests
4. **Mock external dependencies**: Don't call real APIs in unit tests
5. **Test edge cases**: Empty inputs, None values, boundary conditions
6. **Use AsyncMock for async code**: Properly mock coroutines
7. **Keep tests fast**: Unit tests should be < 1 second
8. **Document test purpose**: Use docstrings to explain what's being tested

### Example Test Structure

```python
@pytest.mark.asyncio
async def test_duplicate_detection_skip_behavior(
    notion_writer_skip, mock_notion_integrator
):
    """
    Test that duplicate entries are skipped when duplicate_behavior='skip'.

    Verifies:
    - First write creates entry
    - Second write with same email_id is skipped
    - No duplicate entries in database
    """
    # Arrange
    sample_data = create_valid_extracted_data(email_id="test-001")

    # Act - First write
    result1 = await notion_writer_skip.create_collabiq_entry(sample_data)

    # Act - Second write (duplicate)
    result2 = await notion_writer_skip.create_collabiq_entry(sample_data)

    # Assert
    assert result1["status"] == "created"
    assert result2["status"] == "skipped"
```

---

## Additional Resources

- **Test Improvement Summary**: [specs/015-test-suite-improvements/test_improvement_summary.md](../../specs/015-test-suite-improvements/test_improvement_summary.md)
- **CLI Architecture**: [docs/architecture/CLI_ARCHITECTURE.md](../architecture/CLI_ARCHITECTURE.md)
- **E2E Testing Guide**: [docs/testing/E2E_TESTING.md](./E2E_TESTING.md)
- **pytest Documentation**: https://docs.pytest.org/

---

**Questions or Issues?**
See project README.md or open an issue on the repository.
