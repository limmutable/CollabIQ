# Running E2E Tests with Real Components

## Overview

The E2E test infrastructure has two modes:

1. **Mock Mode** (Default) - Tests infrastructure without writing to Notion
2. **Real Component Mode** - Actual end-to-end testing with Notion writes

## Why Mock Mode Was Used

The initial tests ran in **mock mode** because:
- ✅ Safe default - no accidental Notion writes during development
- ✅ Tests E2E infrastructure (runner, error collector, validators, reports)
- ✅ Fast execution (no API calls)
- ✅ No API quotas consumed

The mock mode confirmed that:
- Email selection works (8 emails fetched)
- Test orchestration works (100% success rate)
- Report generation works (summary + error reports)
- Error tracking infrastructure is functional

## Running with Real Components

### Prerequisites

Ensure all environment variables are set:
```bash
# Gmail API
GOOGLE_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Gemini API
GEMINI_API_KEY=your_api_key

# Notion API
NOTION_API_KEY=your_api_key
COLLABIQ_DB_ID=your_database_id
```

### Option 1: Dry-Run (Recommended First)

Test with real components but **without writing to Notion**:

```bash
uv run python scripts/run_e2e_with_real_components.py --all --dry-run
```

This will:
- ✅ Initialize all real components (Gmail, Gemini, Notion)
- ✅ Fetch real emails from Gmail
- ✅ Extract entities with Gemini API
- ✅ Classify collaborations
- ❌ **NOT write to Notion** (dry-run mode)
- ✅ Generate full reports

### Option 2: Full E2E with Notion Writes

**⚠️ WARNING: This writes to production Notion database!**

```bash
# Process all emails (REQUIRES --confirm)
uv run python scripts/run_e2e_with_real_components.py --all --confirm

# Process single email for testing
uv run python scripts/run_e2e_with_real_components.py --email-id <msg_id> --confirm
```

This will:
- ✅ Initialize all real components
- ✅ Fetch real emails from Gmail
- ✅ Extract entities with Gemini API
- ✅ Classify collaborations
- ✅ **Write entries to Notion database**
- ✅ Validate created entries
- ✅ Generate reports

### Option 3: Single Email Test

Test with a single email first:

```bash
# Get email ID from test_email_ids.json
cat data/e2e_test/test_email_ids.json | jq '.[0].email_id'

# Run with that specific email
uv run python scripts/run_e2e_with_real_components.py \
  --email-id "<email_id>" \
  --confirm
```

## Safety Features

The real component script has multiple safety checks:

1. **Explicit Confirmation Required**
   - Must use `--confirm` flag
   - Additional "YES" confirmation prompt
   - Clear warnings about production writes

2. **Dry-Run Mode**
   - Use `--dry-run` to test without writes
   - All components initialized but writes skipped

3. **Duplicate Detection**
   - NotionWriter configured with `duplicate_behavior="skip"`
   - Won't create duplicate entries for same email_id

4. **Cleanup Script Ready**
   - Cleanup script available for removing test entries
   - Supports dry-run preview before deletion

## After Running Tests

### 1. Check Notion Database

Manually verify created entries:
- Go to your Notion CollabIQ database
- Check for entries with email_ids from `test_email_ids.json`
- Verify:
  - ✅ All required fields populated
  - ✅ Korean text preserved (no mojibake)
  - ✅ Date formats correct (YYYY-MM-DD)
  - ✅ Collaboration types correct ([A/B/C/D])
  - ✅ Company IDs valid

### 2. Review Reports

```bash
# View summary report
cat data/e2e_test/reports/<run_id>_summary.md

# View error report (if any errors occurred)
cat data/e2e_test/reports/<run_id>_errors.md
```

### 3. Clean Up Test Entries

**IMPORTANT**: Remove test entries from Notion after verification:

```bash
# Preview what will be deleted (safe)
uv run python scripts/cleanup_test_entries.py --dry-run

# Actually delete test entries (after verification)
uv run python scripts/cleanup_test_entries.py
```

## Expected Results

### Success Criteria

- **SC-001**: ≥95% pipeline success rate
- **SC-002**: 100% data accuracy in Notion
- **SC-003**: No critical errors
- **SC-007**: 100% Korean text preservation

### Typical First Run

**Dry-Run**:
- All 8 emails should process successfully
- 100% success rate
- 0 errors (mocked data)

**Real Run**:
- Success rate depends on actual email content
- May have extraction/matching issues on first run
- Errors will be categorized by severity
- Korean text preservation should be validated

### Common Issues

1. **Authentication Errors**
   - Gmail: Check GOOGLE_CREDENTIALS_PATH and token.json
   - Gemini: Verify GEMINI_API_KEY
   - Notion: Verify NOTION_API_KEY and database permissions

2. **Extraction Failures**
   - May occur with complex/ambiguous email content
   - Check error report for details
   - Gemini API may need prompt tuning

3. **Matching Failures**
   - Company names not in Notion database
   - Check error logs for unmatched companies
   - May need to add companies to database first

4. **Korean Text Issues**
   - Check for mojibake patterns in Notion
   - Verify UTF-8 encoding throughout pipeline
   - Review validator error messages

## Comparison: Mock vs Real

| Feature | Mock Mode | Real Component Mode |
|---------|-----------|---------------------|
| Notion Writes | ❌ No | ✅ Yes |
| Gmail Fetch | ❌ No | ✅ Yes |
| Gemini Extraction | ❌ No | ✅ Yes |
| Classification | ❌ No | ✅ Yes |
| Validation | ✅ Yes | ✅ Yes |
| Error Tracking | ✅ Yes | ✅ Yes |
| Reports | ✅ Yes | ✅ Yes |
| API Costs | Free | Uses quota |
| Safety | 100% safe | Requires cleanup |
| Use Case | Infrastructure testing | Full MVP validation |

## Scripts Summary

| Script | Purpose | Safety |
|--------|---------|--------|
| `select_test_emails.py` | Fetch emails from Gmail | Safe (read-only) |
| `run_e2e_tests.py` | Run in mock mode | Safe (no writes) |
| `run_e2e_with_real_components.py` | Run with real Notion writes | ⚠️ Requires --confirm |
| `tests/manual/run_e2e_validation.py` | Interactive mock testing | Safe (no writes) |
| `cleanup_test_entries.py` | Remove test entries | ⚠️ Deletes from Notion |

## Next Steps

1. **First Run**: Start with dry-run mode
   ```bash
   uv run python scripts/run_e2e_with_real_components.py --all --dry-run
   ```

2. **Single Email Test**: Test one email with real writes
   ```bash
   uv run python scripts/run_e2e_with_real_components.py \
     --email-id "<first_email_id>" \
     --confirm
   ```

3. **Full Test**: Run all emails if single email succeeds
   ```bash
   uv run python scripts/run_e2e_with_real_components.py --all --confirm
   ```

4. **Verify & Clean**: Check Notion manually, then cleanup
   ```bash
   uv run python scripts/cleanup_test_entries.py
   ```

---

**Last Updated**: 2025-11-05
**Status**: Ready for real component testing
