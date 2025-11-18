# Test Coverage Reports

This directory contains test coverage reports for the CollabIQ system, organized by test suite type.

## Overview

The CollabIQ test suite is divided into three layers, each with separate coverage tracking:

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Module interaction testing
3. **End-to-End Tests** - Full pipeline testing

## Quick Start

### Generate All Coverage Reports

```bash
# Run all tests with coverage
make test-coverage

# Or manually:
pytest --cov=src --cov-report=html --cov-report=term
```

### View Coverage Reports

```bash
# Open HTML report in browser
open tests/coverage_reports/htmlcov/index.html

# Or on Linux:
xdg-open tests/coverage_reports/htmlcov/index.html
```

## Granular Coverage Reports

### 1. Unit Test Coverage

Run only unit tests and generate coverage:

```bash
pytest tests/unit/ \
  --cov=src \
  --cov-report=html:tests/coverage_reports/unit_htmlcov \
  --cov-report=term \
  -m "not integration and not e2e"
```

**Expected Coverage**: 80%+ for core modules

### 2. Integration Test Coverage

Run only integration tests and generate coverage:

```bash
pytest tests/integration/ \
  --cov=src \
  --cov-report=html:tests/coverage_reports/integration_htmlcov \
  --cov-report=term \
  -m "integration and not e2e"
```

**Expected Coverage**: 60%+ (focuses on module interactions)

### 3. End-to-End Test Coverage

Run only E2E tests and generate coverage:

```bash
pytest tests/e2e/ \
  --cov=src \
  --cov-report=html:tests/coverage_reports/e2e_htmlcov \
  --cov-report=term \
  -m "e2e"
```

**Expected Coverage**: 40%+ (covers critical user flows)

### 4. Combined Coverage

Run all tests together:

```bash
pytest tests/ \
  --cov=src \
  --cov-report=html:tests/coverage_reports/htmlcov \
  --cov-report=term \
  --cov-report=json:tests/coverage_reports/coverage.json \
  --cov-report=xml:tests/coverage_reports/coverage.xml
```

**Target Coverage**: 85%+ overall

## Coverage Report Formats

### HTML Reports

Interactive HTML reports with line-by-line coverage highlighting:

- **All tests**: `tests/coverage_reports/htmlcov/index.html`
- **Unit only**: `tests/coverage_reports/unit_htmlcov/index.html`
- **Integration only**: `tests/coverage_reports/integration_htmlcov/index.html`
- **E2E only**: `tests/coverage_reports/e2e_htmlcov/index.html`

### Terminal Reports

Quick coverage summary in terminal:

```bash
pytest --cov=src --cov-report=term-missing
```

Shows:
- Coverage percentage per module
- Missing line numbers
- Branch coverage statistics

### JSON Reports

Machine-readable coverage data:

```bash
pytest --cov=src --cov-report=json:tests/coverage_reports/coverage.json
```

Use for:
- CI/CD integration
- Coverage trend analysis
- Custom report generation

### XML Reports

Standard XML format for tooling integration:

```bash
pytest --cov=src --cov-report=xml:tests/coverage_reports/coverage.xml
```

Compatible with:
- SonarQube
- Codecov
- Coveralls

## Advanced Usage

### Coverage for Specific Modules

```bash
# Date parser only
pytest tests/ --cov=src/collabiq/date_parser --cov-report=html

# LLM adapters only
pytest tests/ --cov=src/llm_adapters --cov-report=html

# Notion integrator only
pytest tests/ --cov=src/notion_integrator --cov-report=html
```

### Fail on Coverage Threshold

```bash
# Fail if coverage below 80%
pytest --cov=src --cov-fail-under=80

# Fail if coverage below 90% for specific module
pytest tests/ --cov=src/collabiq/date_parser --cov-fail-under=90
```

### Branch Coverage

View branch coverage (already enabled in pyproject.toml):

```bash
pytest --cov=src --cov-report=term --cov-branch
```

### Coverage Diff

Compare coverage between commits:

```bash
# Generate baseline
git checkout main
pytest --cov=src --cov-report=json:baseline_coverage.json

# Generate current
git checkout feature-branch
pytest --cov=src --cov-report=json:current_coverage.json

# Compare (requires coverage-diff tool)
coverage-diff baseline_coverage.json current_coverage.json
```

## Makefile Targets

Convenient shortcuts for coverage generation:

```makefile
# Add to Makefile
.PHONY: test-coverage test-coverage-unit test-coverage-integration test-coverage-e2e

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

test-coverage-unit:
	pytest tests/unit/ --cov=src --cov-report=html:tests/coverage_reports/unit_htmlcov -m "not integration and not e2e"

test-coverage-integration:
	pytest tests/integration/ --cov=src --cov-report=html:tests/coverage_reports/integration_htmlcov -m "integration and not e2e"

test-coverage-e2e:
	pytest tests/e2e/ --cov=src --cov-report=html:tests/coverage_reports/e2e_htmlcov -m "e2e"
```

## Coverage Goals

### Current Coverage (Phase 015)

| Test Suite | Coverage | Target |
|------------|----------|--------|
| Unit Tests | 75%+ | 80%+ |
| Integration Tests | 55%+ | 60%+ |
| E2E Tests | 35%+ | 40%+ |
| **Overall** | **80%+** | **85%+** |

### Per-Module Goals

| Module | Coverage | Priority |
|--------|----------|----------|
| date_parser | 95%+ | High |
| llm_adapters | 85%+ | High |
| notion_integrator | 80%+ | High |
| test_utils | 90%+ | High |
| content_normalizer | 75%+ | Medium |
| email_receiver | 70%+ | Medium |

## Ignoring Coverage

Use comments to exclude specific lines:

```python
def debug_only_function():  # pragma: no cover
    """This function is only for debugging."""
    print("Debug info")
```

Or exclude entire files in `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/scripts/*",
]
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=xml --cov-report=term

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./tests/coverage_reports/coverage.xml
    flags: unittests
    name: codecov-collabiq
```

### Coverage Badge

Add to README.md:

```markdown
![Coverage](https://img.shields.io/codecov/c/github/username/collabiq)
```

## Troubleshooting

### Coverage Not Detected

```bash
# Ensure pytest-cov is installed
uv pip list | grep pytest-cov

# Check coverage configuration
cat pyproject.toml | grep -A 10 "tool.coverage"

# Run with verbose coverage
pytest --cov=src --cov-report=term --cov-report=html -v
```

### Missing Lines

Check if lines are excluded:

```bash
# Show excluded lines in report
pytest --cov=src --cov-report=term-missing
```

### Low Coverage

Identify uncovered modules:

```bash
# Sort by coverage percentage
pytest --cov=src --cov-report=term | sort -k 4 -n
```

## Additional Resources

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](../../docs/testing/)

---

**Last Updated**: 2025-11-18
**Phase**: 015 - Test Suite Improvements
**Status**: Active
