# E2E Testing Documentation

**Last Updated**: 2025-11-06
**Feature**: MVP End-to-End Testing (008-mvp-e2e-test)
**Status**: Phase 3 Complete ✅

---

## Documentation Index

### Main Guides

1. **[E2E_TESTING.md](E2E_TESTING.md)** (40K) - Comprehensive E2E testing guide
   - Setup and configuration
   - Running tests (mock and real component modes)
   - Success criteria and validation
   - Troubleshooting
   - Implementation status and bug fixes
   - Phase completion history

2. **[E2E_QUICKSTART.md](E2E_QUICKSTART.md)** (9.6K) - Quick start guide
   - Step-by-step testing workflow
   - Email selection
   - Running tests
   - Validation and cleanup

3. **[E2E_DATA_MODEL.md](E2E_DATA_MODEL.md)** (14K) - Data structure reference
   - TestRun entity
   - ErrorRecord entity
   - PerformanceMetric entity
   - TestEmailMetadata entity
   - JSON schema definitions

---

## Test Scripts & Tools

### Production Scripts

Located in `/scripts/`:

- **`select_test_emails.py`** - Select emails from Gmail for testing
  - Fetches all emails from collab@signite.co
  - Detects Korean text (Unicode \uac00-\ud7a3)
  - Creates `data/e2e_test/test_email_ids.json`
  - Usage: `uv run python scripts/select_test_emails.py --all`

- **`run_e2e_tests.py`** - Run E2E tests in mock mode (safe, no API calls)
  - Tests infrastructure without writing to Notion
  - Fast execution for development
  - Usage: `uv run python scripts/run_e2e_tests.py --all`

- **`run_e2e_with_real_components.py`** - Run E2E tests with real components
  - ⚠️ **Writes to production Notion database**
  - Requires `--confirm` flag for safety
  - Usage: `uv run python scripts/run_e2e_with_real_components.py --email-id <ID> --confirm --yes`

- **`cleanup_test_entries.py`** - Remove test entries from Notion
  - Dry-run mode with `--dry-run`
  - Email ID filtering
  - Audit logging
  - Usage: `uv run python scripts/cleanup_test_entries.py --dry-run`

- **`diagnose_notion_access.py`** - Verify Notion database access and schema
  - Read-only diagnostic tool
  - Usage: `uv run python scripts/diagnose_notion_access.py`

### Test Suites

Located in `/tests/`:

- **`tests/e2e/test_full_pipeline.py`** - Automated E2E tests (pytest)
  - Full pipeline testing
  - Mock mode tests
  - Run with: `pytest tests/e2e/`

- **`tests/manual/run_e2e_validation.py`** - Interactive E2E validation
  - Manual test execution
  - Step-by-step validation
  - Configurable test modes

---

## Data Directories

All test data stored in `data/e2e_test/`:

```
data/e2e_test/
├── test_email_ids.json     # Selected test emails
├── runs/                   # Test run metadata
│   └── YYYYMMDD_HHMMSS.json
├── errors/                 # Error records by severity
│   ├── critical/
│   ├── high/
│   ├── medium/
│   └── low/
├── reports/                # Test summaries and reports
│   ├── YYYYMMDD_HHMMSS_summary.md
│   └── YYYYMMDD_HHMMSS_errors.md
└── metrics/                # Performance timing data
```

---

## Related Documentation

### Architecture & Planning

Located in `/specs/008-mvp-e2e-test/`:

- `spec.md` - Feature specification
- `plan.md` - Implementation plan
- `tasks.md` - Task breakdown
- `research.md` - Research and decisions
- `bugfixes/` - Historical bug fixes and resolutions

### Technical Documentation

Located in `/docs/architecture/`:

- [TECHSTACK.md](../architecture/TECHSTACK.md) - Technical debt tracking
  - Phase 2d known limitations
  - Future improvements

---

## Quick Reference

### Common Commands

```bash
# 1. Select test emails (read-only)
uv run python scripts/select_test_emails.py --all

# 2. Run mock tests (safe, no writes)
uv run python scripts/run_e2e_tests.py --all

# 3. Run with real components (production writes)
uv run python scripts/run_e2e_with_real_components.py --email-id <ID> --confirm --yes

# 4. View latest test results
cat data/e2e_test/reports/*_summary.md | tail -50

# 5. Clean up test entries (preview first)
uv run python scripts/cleanup_test_entries.py --dry-run
uv run python scripts/cleanup_test_entries.py
```

### Success Criteria

- ✅ SC-001: ≥95% success rate
- ✅ SC-002: 100% data accuracy
- ✅ SC-003: Zero critical errors
- ✅ SC-007: 100% Korean text preservation

---

## Bug Fixes & Known Issues

### Recent Fixes (November 2025)

1. **"None-None" Entry Bug** (2025-11-06) ✅ Fixed
   - Real email fetching implemented
   - Email IDs preserved correctly
   - Verified with 3 real emails

2. **Notion "People" Field Error** (2025-11-06) ✅ Fixed
   - 담당자 field skipped (requires user ID mapping)
   - Documented as technical debt

See [bugfixes directory](../../specs/008-mvp-e2e-test/bugfixes/) for detailed reports.

### Known Limitations

- 담당자 (person_in_charge) field empty - requires user name→UUID mapping
- Company matching limited to existing database entries
- Page body content not written - only properties populated

See [TECHSTACK.md](../architecture/TECHSTACK.md#phase-2d-technical-debt-notion-write-operations) for planned improvements.

---

**For questions or issues**, see the main [E2E_TESTING.md](E2E_TESTING.md) guide or create an issue in the repository.
