# End-to-End Tests

**Purpose**: Complete user scenarios with real APIs

## Characteristics

- **Speed**: Slow (5-30s per test)
- **Dependencies**: Real Gmail/Notion APIs, credentials required
- **Execution**: Pre-merge, nightly
- **Total Files**: 3 test files

## Test Coverage

E2E tests validate complete workflows:

### Full Pipeline Tests
- `test_full_pipeline.py`: Complete email processing pipeline
- `test_real_gmail_notion.py`: Real Gmail → Notion integration
- Other end-to-end scenarios

### Prerequisites

E2E tests require real API credentials:

```bash
# Required environment variables
export GOOGLE_CREDENTIALS_PATH=credentials.json
export GMAIL_TOKEN_PATH=token.json
export GEMINI_API_KEY=your_gemini_api_key
export NOTION_API_KEY=your_notion_api_key
export NOTION_DATABASE_ID_COLLABIQ=your_collabiq_db_id
export NOTION_DATABASE_ID_COMPANIES=your_companies_db_id
```

### Running E2E Tests

```bash
# Run all E2E tests (requires credentials)
uv run pytest tests/e2e/ -v

# Run specific E2E test
uv run pytest tests/e2e/test_full_pipeline.py -v

# Skip E2E tests (for CI without credentials)
uv run pytest -m "not e2e" -v
```

### Safety Features

- Uses production Gmail (read-only, safe)
- Uses production Notion credentials (writes to real database)
- Automatically cleans up test entries after validation
- Safe to run multiple times (duplicate detection prevents multiple entries)

## Guidelines

- Test complete user journeys
- Use real external APIs
- Clean up test data after execution
- Handle API rate limits gracefully
- Document required credentials
