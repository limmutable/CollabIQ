# Quickstart: MVP End-to-End Testing

**Feature**: 008-mvp-e2e-test
**Purpose**: Step-by-step guide to run E2E tests and validate MVP pipeline

## Prerequisites

Before running E2E tests, ensure the following are complete:

- [ ] All MVP phases (1a, 1b, 2a, 2b, 2c, 2d) merged to main
- [ ] Gmail, Gemini, and Notion API credentials configured in `.env`
- [ ] Real emails available in collab@signite.co inbox (currently <10 emails)
- [ ] Production Notion "CollabIQ" database is accessible

**Note**: E2E tests will use ALL real emails from collab@signite.co inbox and write to the production Notion database. Test entries will be tagged with email_id and cleaned up manually after testing.

---

## Step 1: Select Test Emails

### 1.1 Automatic Email Selection (Recommended)

Run the email selection script to fetch ALL emails from collab@signite.co:
```bash
uv run python scripts/select_test_emails.py --all
```

This creates `data/e2e_test/test_email_ids.json` with all available emails from the inbox (currently <10 emails).

**Note**: Since there are currently fewer than 10 emails, we'll test with all available real production emails instead of requiring 50+ diverse emails.

### 1.2 Manual Email Selection (Optional)

If you want to test specific emails only:

1. Create `data/e2e_test/test_email_ids.json` manually:
```json
[
  {
    "email_id": "msg_abc123",
    "subject": "브레이크앤컴퍼니 x 신세계푸드",
    "received_date": "2025-10-28",
    "collaboration_type": "[A]",
    "has_korean_text": true,
    "selection_reason": "manual",
    "notes": "Known edge case"
  }
]
```

2. Add more email objects as needed

---

## Step 2: Run End-to-End Tests

### 2.1 Full Test Run (All Available Emails)

Run the complete pipeline with all emails from collab@signite.co:
```bash
uv run python scripts/run_e2e_tests.py --all
```

This processes all emails in `test_email_ids.json` (currently <10 emails).

Expected output:
```
Starting E2E test run: 2025-11-04T14:30:00
Processing 8 emails...

[1/8] msg_001 ✓ (18.5s)
[2/8] msg_002 ✓ (17.2s)
[3/8] msg_003 ✗ High severity error in extraction stage
...

Test run completed: 2025-11-04T14:30:00
Emails processed: 8
Success rate: 87.5% (7/8 successful)
Errors: critical=0, high=1, medium=0, low=0
Average time per email: 18.1s

Report saved to: data/e2e_test/reports/2025-11-04T14:30:00_summary.md
```

**⚠️ Note**: Test entries will be written to production CollabIQ database. Remember to run cleanup after testing (Step 6).

### 2.2 Test Single Email (Optional)

If you want to test a specific email only:
```bash
uv run python scripts/run_e2e_tests.py --email-id msg_001
```

### 2.3 Resume Interrupted Test Run (Optional)

If a test run is interrupted (system crash, user cancellation):
```bash
uv run python scripts/run_e2e_tests.py --resume 2025-11-04T14:30:00
```

The runner will skip already-processed emails and continue from the interruption point.

---

## Step 3: Review Test Results

### 3.1 View Test Summary

Open the generated report:
```bash
cat data/e2e_test/reports/{run_id}_summary.md
```

The report includes:
- Overall success rate by pipeline stage
- Error breakdown by severity
- Performance metrics (average/median/p95 times per stage)
- List of failed emails with error details

### 3.2 Inspect Individual Errors

Errors are organized by severity:
```bash
# View all high-severity errors
ls data/e2e_test/errors/high/

# Inspect specific error
cat data/e2e_test/errors/high/{run_id}_{email_id}_001.json
```

Each error file contains:
- Error message and stack trace
- Input data snapshot (for reproduction)
- Stage where error occurred
- Timestamp and severity

### 3.3 Analyze Performance Metrics

Export metrics to CSV for analysis:
```bash
uv run python scripts/export_metrics.py --run-id {run_id} --output metrics.csv
```

Open `metrics.csv` in Excel/Google Sheets to:
- Identify slow pipeline stages (>5 seconds)
- Analyze Gemini token usage per email
- Compare performance across different collaboration types

---

## Step 4: Fix Critical and High-Severity Errors

### 4.1 Prioritize Errors

Focus on critical and high-severity errors first (per FR-010, FR-011):

**Critical errors** (must fix immediately):
- API authentication failures
- Pipeline crashes
- Data corruption

**High-severity errors** (must fix before feature completion):
- Korean text encoding issues
- Incorrect Notion data
- Frequent failures (>10% of emails)

**Medium/Low errors** (document and defer):
- Edge case handling
- Minor performance issues
- Cosmetic problems

### 4.2 Fix and Verify

For each critical/high error:

1. Reproduce the error:
   ```bash
   # Use error's email_id
   uv run python scripts/run_e2e_tests.py --email-id msg_042
   ```

2. Apply fix to the code

3. Re-run the same email to verify fix:
   ```bash
   uv run python scripts/run_e2e_tests.py --email-id msg_042
   ```

4. Update error status:
   ```bash
   uv run python scripts/update_error_status.py \
     --error-id {error_id} \
     --status fixed \
     --commit {git_commit_hash}
   ```

### 4.3 Re-Run Full Test Suite

After fixing all critical/high errors, re-run the full test suite:
```bash
uv run python scripts/run_e2e_tests.py --all
```

Verify success rate ≥95% (SC-001).

---

## Step 5: Validate Success Criteria

Before completing this feature, verify all success criteria:

- [ ] **SC-001**: Pipeline processes ≥95% of test emails without critical/high errors
- [ ] **SC-002**: All Notion entries have correctly formatted data (100% accuracy)
- [ ] **SC-003**: All critical errors identified, fixed, and verified
- [ ] **SC-004**: All high-severity errors identified, fixed, and verified
- [ ] **SC-005**: Error logs include full context (email_id, stack trace, input data)
- [ ] **SC-006**: Duplicate detection works correctly (100% of duplicate test cases)
- [ ] **SC-007**: Korean text preserved without corruption (100% of entries)
- [ ] **SC-008**: Pipeline processes emails in ≤10 seconds on average
- [ ] **SC-009**: All existing tests still pass (no regressions)
- [ ] **SC-010**: Performance baselines established for all stages

Run the success criteria validation script:
```bash
uv run python scripts/validate_success_criteria.py --run-id {run_id}
```

---

## Step 6: Clean Up Test Data (Required)

After testing is complete, clean up test entries from production database:

```bash
# Delete test entries from production CollabIQ database
uv run python scripts/cleanup_test_entries.py
```

This script will:
1. Load test email_ids from `data/e2e_test/test_email_ids.json`
2. Find all Notion entries where Email ID field matches test email_ids
3. Show you what will be deleted (dry-run preview)
4. Ask for explicit confirmation before deletion
5. Delete confirmed entries and log all deletions to audit trail

**Options**:
```bash
# Dry-run mode (preview only, no deletion)
uv run python scripts/cleanup_test_entries.py --dry-run

# Skip confirmation prompt (use with caution)
uv run python scripts/cleanup_test_entries.py --yes

# Specify custom test email IDs file
uv run python scripts/cleanup_test_entries.py --email-ids-file path/to/custom_ids.json
```

**Safety Notes**:
- Script only deletes entries where Email ID field matches test email_ids
- Requires explicit "yes" confirmation before any deletion
- All deletions logged to `data/e2e_test/cleanup_audit_{timestamp}.log`
- Can be safely re-run if interrupted (idempotent operation)

---

## Troubleshooting

### Issue: Cleanup script accidentally deleting wrong entries

**Solution**:
1. Always use `--dry-run` first to preview what will be deleted
2. Verify `test_email_ids.json` contains only test emails (not production email IDs)
3. Check cleanup audit log in `data/e2e_test/cleanup_audit_{timestamp}.log` for records of what was deleted

### Issue: "Rate limit exceeded" errors

**Solution**:
1. Add delay between emails: `--delay 2` (2 seconds between emails)
2. Run tests in smaller batches: `--limit 10`
3. Check Gemini/Notion API quotas in their respective dashboards

### Issue: Korean text corruption in Notion entries

**Solution**:
1. Check all JSON writes use `encoding='utf-8'`
2. Verify environment locale: `locale` (should show UTF-8)
3. Check Notion API requests include `Content-Type: application/json; charset=utf-8` header

### Issue: Test run crashes mid-execution

**Solution**:
1. Resume from interruption point: `--resume {run_id}`
2. Check error logs in `data/e2e_test/errors/critical/`
3. If consistent crash, run single email to debug: `--email-id msg_XXX`

---

## Next Steps

Once all success criteria pass:
1. Commit and push all fixes to feature branch
2. Run full test suite one final time
3. Merge feature branch to main
4. Proceed to Phase 2e (next feature in roadmap)

---

## Command Reference

```bash
# Email selection
uv run python scripts/select_test_emails.py --all           # Fetch all emails from inbox

# Run tests
uv run python scripts/run_e2e_tests.py --all                # Test all selected emails (<10 currently)
uv run python scripts/run_e2e_tests.py --email-id msg_001   # Test single email
uv run python scripts/run_e2e_tests.py --resume {run_id}    # Resume interrupted run

# Error management
uv run python scripts/update_error_status.py --error-id {id} --status fixed --commit {hash}

# Performance analysis
uv run python scripts/export_metrics.py --run-id {run_id} --output metrics.csv

# Success criteria validation
uv run python scripts/validate_success_criteria.py --run-id {run_id}

# Cleanup (Required after testing)
uv run python scripts/cleanup_test_entries.py                 # Interactive cleanup
uv run python scripts/cleanup_test_entries.py --dry-run      # Preview only
uv run python scripts/cleanup_test_entries.py --yes          # Skip confirmation
```
