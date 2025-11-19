# Unit Tests

**Purpose**: Isolated component tests with mocked dependencies

## Characteristics

- **Speed**: Fast (<0.1s per test)
- **Dependencies**: None (all external calls mocked)
- **Execution**: Every commit
- **Total Files**: 31 test files

## Test Organization

Unit tests are organized by component:

### Core Components
- Email reception and cleaning
- LLM adapters (Gemini, Claude, OpenAI)
- Notion integration
- Content normalization
- Field mapping
- Error handling

### Running Unit Tests

```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific component
uv run pytest tests/unit/test_gemini_adapter.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=collabiq --cov-report=html
```

## Guidelines

- Mock all external dependencies (APIs, databases, file I/O)
- Each test should be independent and deterministic
- Use fixtures from `src/collabiq/test_utils/fixtures.py`
- Test edge cases and error conditions
- Keep tests fast (<0.1s each)
