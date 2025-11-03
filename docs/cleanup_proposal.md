# Cleanup Proposal: Documentation & Scripts

**Date**: 2025-11-03
**Status**: PROPOSED - Awaiting approval

---

## Issue 1: Documentation Consolidation

### Current State
- **gmail-oauth-setup.md** (443 lines): Complete setup guide with step-by-step GCP configuration
- **GMAIL_GROUP_AUTHENTICATION.md** (220 lines): Quick reference with troubleshooting

### Analysis
**Overlap**:
- Both explain collab@signite.co is a Google Group
- Both emphasize `to:collab@signite.co` query requirement
- Both have authentication instructions

**Unique Content in gmail-oauth-setup.md**:
- ✅ Google Cloud Console setup (Steps 1.1-1.4)
- ✅ OAuth consent screen configuration
- ✅ Credentials download
- ✅ Local .env configuration
- ✅ Integration test instructions

**Unique Content in GMAIL_GROUP_AUTHENTICATION.md**:
- ✅ Common mistakes with wrong/correct code examples
- ✅ Quick reference card table
- ✅ Detailed troubleshooting scenarios
- ✅ Test script usage examples

### Recommendation: **MERGE** into single document

**Proposed Structure**: `docs/setup/gmail-oauth-setup.md` (enhanced)
```markdown
# Gmail API Setup for CollabIQ

## Overview
⚠️ CRITICAL: Google Group Authentication (consolidated warning)

## Part 1: Google Cloud Console Setup (5-8 min)
[Keep existing content]

## Part 2: Local Configuration (3-5 min)
[Keep existing content]

## Part 3: First-Time Authentication (2-3 min)
[Keep existing content]

## Part 4: Validation (2-3 min)
[Keep existing content]

## Part 5: Common Mistakes & Troubleshooting (NEW - from GMAIL_GROUP_AUTHENTICATION.md)
### Common Mistakes to Avoid
- ❌ Mistake 1: Trying to authenticate as collab@signite.co
- ❌ Mistake 2: Retrieving emails without filtering
- ❌ Mistake 3: Using deliveredto: operator

### Troubleshooting
[Merge both docs' troubleshooting sections]

## Quick Reference Card (NEW - from GMAIL_GROUP_AUTHENTICATION.md)
[Add table for instant lookup]
```

**Action**:
- Merge GMAIL_GROUP_AUTHENTICATION.md → gmail-oauth-setup.md (Part 5)
- Delete GMAIL_GROUP_AUTHENTICATION.md
- Update any references to deleted file

---

## Issue 2: Scripts Directory Cleanup

### Current State (10 scripts)

| Script | Purpose | Issue | Proposed Action |
|--------|---------|-------|-----------------|
| `authenticate_gmail.py` | OAuth2 authentication | ✅ Correctly placed | **KEEP** - Utility script |
| `check_secret_source.py` | Debug Infisical vs .env | ✅ Correctly placed | **KEEP** - Utility script |
| `diagnose_notion_access.py` | Debug Notion API issues | ✅ Correctly placed | **KEEP** - Utility script |
| `verify_setup.sh` | Verify prerequisites | ✅ Correctly placed | **KEEP** - Utility script |
| `validate_infisical.py` | Test Infisical connection | ❓ Naming confusion with `verify_setup.sh` | **RENAME** → `test_infisical_connection.py` |
| `test_gmail_retrieval.py` | Test Gmail API retrieval | ❓ Generic test, overlaps with e2e | **KEEP** but clarify purpose |
| `test_e2e_extraction.py` | End-to-end Phase 1b test | ❓ Not in /tests directory | **MOVE** → `tests/manual/test_e2e_phase1b.py` |
| `test_phase2b_real_emails.py` | End-to-end Phase 2b test | ❓ Not in /tests directory | **MOVE** → `tests/manual/test_e2e_phase2b.py` |
| `validate_extraction_accuracy.py` | Validate against ground truth | ❓ "validate" vs "test" confusion | **MOVE** → `tests/validation/validate_accuracy.py` |

### Issues Identified

#### Issue 2.1: Naming Inconsistency
**Problem**: `validate_*` vs `verify_*` vs `test_*` used inconsistently

**Current Usage**:
- `validate_extraction_accuracy.py` - Checks against ground truth
- `validate_infisical.py` - Tests Infisical connection
- `verify_setup.sh` - Checks prerequisites

**Proposed Naming Convention**:
```
/scripts/
  - Utility scripts only (authenticate, diagnose, check)
  - No "test_*" or "validate_*" scripts here

/tests/manual/
  - test_e2e_phase1b.py (moved from scripts/test_e2e_extraction.py)
  - test_e2e_phase2b.py (moved from scripts/test_phase2b_real_emails.py)
  - test_gmail_retrieval.py (moved from scripts/)
  - test_infisical_connection.py (moved from scripts/validate_infisical.py)

/tests/validation/
  - validate_accuracy.py (moved from scripts/validate_extraction_accuracy.py)
```

#### Issue 2.2: Test Scripts in Wrong Directory
**Problem**: `test_*.py` scripts are in `/scripts` instead of `/tests`

**Why this matters**:
- pytest discovers tests in /tests directory
- Developers expect tests to be in /tests
- /scripts should be for utility/operational scripts

**Affected Scripts**:
- `test_gmail_retrieval.py` - Should be in /tests/manual/
- `test_e2e_extraction.py` - Should be in /tests/manual/
- `test_phase2b_real_emails.py` - Should be in /tests/manual/
- `validate_extraction_accuracy.py` - Should be in /tests/validation/

#### Issue 2.3: Overlapping Functionality
**Problem**: Multiple Gmail retrieval scripts

**Current Scripts**:
- `test_gmail_retrieval.py` - Generic Gmail API test
- `test_e2e_extraction.py` - Fetches emails + runs extraction (Phase 1b)
- `test_phase2b_real_emails.py` - Fetches emails + runs matching (Phase 2b)

**Analysis**:
- `test_gmail_retrieval.py` - Low-level API test (useful for debugging)
- `test_e2e_extraction.py` - Full Phase 1b pipeline test
- `test_phase2b_real_emails.py` - Full Phase 2b pipeline test

**Recommendation**: Keep all three, but clarify purposes:
- `test_gmail_retrieval.py` → For testing Gmail API connectivity only
- `test_e2e_phase1b.py` → For testing Phase 1b extraction pipeline
- `test_e2e_phase2b.py` → For testing Phase 2b matching pipeline

---

## Proposed File Structure

### Before
```
/scripts/
  authenticate_gmail.py
  check_secret_source.py
  diagnose_notion_access.py
  test_e2e_extraction.py               ❌ Test in /scripts
  test_gmail_retrieval.py              ❌ Test in /scripts
  test_phase2b_real_emails.py          ❌ Test in /scripts
  validate_extraction_accuracy.py      ❌ Validation in /scripts
  validate_infisical.py                ❌ Test in /scripts
  verify_setup.sh

/docs/setup/
  gmail-oauth-setup.md
  GMAIL_GROUP_AUTHENTICATION.md        ❌ Duplicate content
```

### After
```
/scripts/
  authenticate_gmail.py                ✅ Utility: OAuth2 flow
  check_secret_source.py               ✅ Utility: Debug secrets
  diagnose_notion_access.py            ✅ Utility: Debug Notion
  verify_setup.sh                      ✅ Utility: Check prerequisites

/tests/manual/                         ✅ Manual test scripts
  test_gmail_retrieval.py              ✅ Test: Gmail API only
  test_e2e_phase1b.py                  ✅ Test: Full Phase 1b pipeline
  test_e2e_phase2b.py                  ✅ Test: Full Phase 2b pipeline
  test_infisical_connection.py         ✅ Test: Infisical integration

/tests/validation/                     ✅ Validation scripts
  validate_accuracy.py                 ✅ Validate: Ground truth comparison

/docs/setup/
  gmail-oauth-setup.md                 ✅ Single comprehensive guide
```

---

## Implementation Plan

### Step 1: Documentation Consolidation

1. **Merge GMAIL_GROUP_AUTHENTICATION.md into gmail-oauth-setup.md**
   ```bash
   # Add Part 5: Common Mistakes & Troubleshooting (from GMAIL_GROUP_AUTHENTICATION.md)
   # Add Quick Reference Card section
   ```

2. **Delete GMAIL_GROUP_AUTHENTICATION.md**
   ```bash
   git rm docs/setup/GMAIL_GROUP_AUTHENTICATION.md
   ```

3. **Update references**
   - Check for any links to GMAIL_GROUP_AUTHENTICATION.md
   - Update to point to gmail-oauth-setup.md#troubleshooting

### Step 2: Scripts Reorganization

1. **Create new test directories**
   ```bash
   mkdir -p tests/manual
   mkdir -p tests/validation
   ```

2. **Move test scripts**
   ```bash
   # Manual tests
   git mv scripts/test_gmail_retrieval.py tests/manual/
   git mv scripts/test_e2e_extraction.py tests/manual/test_e2e_phase1b.py
   git mv scripts/test_phase2b_real_emails.py tests/manual/test_e2e_phase2b.py
   git mv scripts/validate_infisical.py tests/manual/test_infisical_connection.py

   # Validation scripts
   git mv scripts/validate_extraction_accuracy.py tests/validation/validate_accuracy.py
   ```

3. **Update script headers**
   - Update docstrings to reflect new purposes
   - Add "Manual Test" or "Validation Script" labels

4. **Update references**
   - README.md
   - quickstart.md
   - gmail-oauth-setup.md
   - Any other documentation referencing these scripts

5. **Create tests/manual/README.md**
   ```markdown
   # Manual Test Scripts

   These scripts require real credentials and external API access.
   They are not run by pytest automatically.

   ## Available Tests
   - test_gmail_retrieval.py - Test Gmail API connectivity
   - test_e2e_phase1b.py - Test Phase 1b extraction pipeline
   - test_e2e_phase2b.py - Test Phase 2b matching pipeline
   - test_infisical_connection.py - Test Infisical integration
   ```

### Step 3: Update Documentation References

**Files to update**:
- [ ] README.md
- [ ] docs/setup/quickstart.md
- [ ] docs/setup/gmail-oauth-setup.md (after merge)
- [ ] docs/architecture/TECHSTACK.md
- [ ] Any CLAUDE.md references

---

## Breaking Changes

### For Users
- Scripts moved from `/scripts` to `/tests/manual/` - update any automation

**Before**:
```bash
uv run python scripts/test_gmail_retrieval.py
uv run python scripts/test_e2e_extraction.py
uv run python scripts/validate_extraction_accuracy.py
```

**After**:
```bash
uv run python tests/manual/test_gmail_retrieval.py
uv run python tests/manual/test_e2e_phase1b.py
uv run python tests/validation/validate_accuracy.py
```

### For Documentation
- GMAIL_GROUP_AUTHENTICATION.md deleted - use gmail-oauth-setup.md

**Before**:
```markdown
See [Gmail Group Authentication](GMAIL_GROUP_AUTHENTICATION.md)
```

**After**:
```markdown
See [Gmail OAuth Setup - Troubleshooting](gmail-oauth-setup.md#part-5-common-mistakes--troubleshooting)
```

---

## Benefits

### Documentation
✅ Single source of truth for Gmail setup
✅ Easier to maintain (no duplicate content)
✅ Better organized with clear sections
✅ Quick reference card included at end

### Scripts
✅ Clear separation: utilities in /scripts, tests in /tests
✅ Consistent naming conventions
✅ Easier for developers to find test scripts
✅ pytest can discover manual tests if needed
✅ Reduces confusion about where to add new scripts

---

## Timeline

**Estimated Effort**: 1-2 hours
- Documentation merge: 30 min
- Scripts reorganization: 30 min
- Update references: 30 min
- Testing: 30 min

---

## Approval Required

- [ ] User approves documentation merge
- [ ] User approves scripts reorganization
- [ ] User approves breaking changes

**Next Steps**: Awaiting user confirmation to proceed with implementation.
