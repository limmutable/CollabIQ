# Integration Tests

**Purpose**: Multi-component interaction tests

## Characteristics

- **Speed**: Moderate (0.1-5s per test)
- **Dependencies**: May use test databases, mock APIs
- **Execution**: Pre-push, CI/CD
- **Total Files**: 33 test files

## Test Coverage

Integration tests validate component interactions:

### Component Integration
- LLM Orchestrator with multiple providers
- Notion read/write operations
- Company matching with Notion database
- Classification and summarization pipelines
- Field mapping and person matching
- Error handling and retry logic

### Running Integration Tests

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific integration
uv run pytest tests/integration/test_notion_integrator.py -v

# Skip tests requiring real APIs
uv run pytest tests/integration/ -m "not notion" -v
```

## Guidelines

- Test real component interactions (not mocked)
- May use test databases or mock external APIs
- Verify data flow between components
- Test error handling at integration boundaries
- Keep tests reasonably fast (<5s each)
