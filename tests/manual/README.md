# Manual Test Scripts

**Purpose**: Manual test scripts that require real credentials and external API access.

These scripts are **not** run automatically by pytest. They are intended for:
- Manual testing during development
- Verifying API integrations with real services
- End-to-end testing with production credentials

---

## Available Scripts

### test_gmail_retrieval.py
**Purpose**: Test Gmail API connectivity and email retrieval

**Usage**:
```bash
# Test with default query (to:collab@signite.co)
uv run python tests/manual/test_gmail_retrieval.py --max-results 5

# Test with custom query
uv run python tests/manual/test_gmail_retrieval.py \
  --query 'to:collab@signite.co subject:"협업"' \
  --max-results 10
```

**Prerequisites**:
- Valid Gmail OAuth2 credentials (credentials.json)
- Authenticated token (token.json)
- Network access to Gmail API

---

### test_e2e_phase1b.py
**Purpose**: End-to-end test for Phase 1b (Entity Extraction)

**Usage**:
```bash
# Test Phase 1b pipeline with real emails
uv run python tests/manual/test_e2e_phase1b.py
```

**What it tests**:
1. Fetch emails from collab@signite.co using Gmail API
2. Clean and normalize email content
3. Extract entities using Gemini LLM (Phase 1b)
4. Save extraction results to JSON

**Prerequisites**:
- Gmail OAuth2 credentials and token
- Gemini API key (GEMINI_API_KEY in .env)
- Network access to Gmail API and Gemini API

---

### test_e2e_phase2b.py
**Purpose**: End-to-end test for Phase 2b (LLM-Based Company Matching)

**Usage**:
```bash
# Test Phase 2b with last 3 emails (default)
uv run python tests/manual/test_e2e_phase2b.py

# Test with more emails
uv run python tests/manual/test_e2e_phase2b.py --limit 10
```

**What it tests**:
1. Fetch emails from collab@signite.co using Gmail API
2. Fetch company data from Notion database
3. Clean and normalize email content
4. Extract entities with company matching using Gemini LLM (Phase 2b)
5. Compare Phase 1b vs Phase 2b results
6. Display match quality analysis with confidence scores
7. Save results to JSON file

**Prerequisites**:
- Gmail OAuth2 credentials and token
- Gemini API key (GEMINI_API_KEY in .env)
- Notion API token (NOTION_API_TOKEN in .env)
- Notion companies database ID (NOTION_DATABASE_ID_COMPANIES in .env)
- Network access to Gmail API, Gemini API, and Notion API

---

### test_infisical_connection.py
**Purpose**: Test Infisical secret management integration

**Usage**:
```bash
# Test Infisical connection
uv run python tests/manual/test_infisical_connection.py
```

**What it tests**:
1. Load Infisical configuration from .env
2. Authenticate with Infisical using machine identity
3. Retrieve test secrets from Infisical
4. Validate three-tier fallback (Infisical → SDK cache → .env)

**Prerequisites**:
- Infisical configuration in .env:
  - INFISICAL_ENABLED=true
  - INFISICAL_PROJECT_ID
  - INFISICAL_ENVIRONMENT
  - INFISICAL_CLIENT_ID
  - INFISICAL_CLIENT_SECRET
- Network access to Infisical API

---

## Running All Manual Tests

**Note**: Manual tests are NOT run by `pytest` automatically.

To run all manual tests at once:
```bash
# Run each test sequentially
for script in tests/manual/*.py; do
  echo "Running $script..."
  uv run python "$script"
  echo "---"
done
```

Or run individual tests as needed based on what you're testing.

---

## Adding New Manual Tests

When creating new manual test scripts:

1. **Naming convention**: `test_*.py`
2. **Place in**: `tests/manual/`
3. **Add shebang**: `#!/usr/bin/env python3`
4. **Add docstring**: Clear description of what the script tests
5. **Handle credentials**: Gracefully handle missing credentials
6. **Update this README**: Add entry to Available Scripts section

---

## Troubleshooting

### Error: "Credentials file not found"
**Solution**: Run `scripts/authenticate_gmail.py` to set up OAuth2 credentials

### Error: "GEMINI_API_KEY not set"
**Solution**: Add `GEMINI_API_KEY=your_key_here` to `.env` file

### Error: "NOTION_API_TOKEN not set"
**Solution**: Add `NOTION_API_TOKEN=your_token_here` to `.env` file

### Error: "Infisical authentication failed"
**Solution**: Verify Infisical configuration in `.env` file

---

## Related Documentation

- [Gmail OAuth Setup](../../docs/setup/gmail-oauth-setup.md)
- [Infisical Setup](../../docs/setup/infisical-setup.md)
- [Phase 1b Documentation](../../docs/features/004-gemini-extraction/)
- [Phase 2b Documentation](../../docs/features/007-llm-matching/)
