# Quickstart Guide: Enhanced Notion Field Mapping

**Feature**: 014-enhanced-field-mapping
**Audience**: Users, administrators, testers
**Prerequisites**: CollabIQ system installed and configured (Phases 1-3c complete)

## Overview

This feature automatically populates three critical Notion database fields that were previously left empty:
- **담당자 (Person in Charge)**: Matches person names to Notion workspace users
- **스타트업명 (Startup Name)**: Matches company names to the Companies database
- **협력기관 (Partner Organization)**: Matches organization names to the Companies database

The system uses fuzzy string matching to handle spelling variations and auto-creates missing companies.

## Quick Start (5 minutes)

### 1. Test Company Matching

Test fuzzy matching with a known company name:

```bash
# Basic usage - test exact match
collabiq notion match-company "웨이크"

# Test fuzzy match with variation
collabiq notion match-company "웨이크(산스)"

# Test with dry-run (no actual creation)
collabiq notion match-company "새로운회사" --dry-run
```

**Expected Output**:
```
Company Match Result
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Match Type:        fuzzy
  Company Name:      웨이크
  Page ID:           abc123def456
  Similarity:        87%
  Confidence:        medium
  Was Created:       No
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Test Person Matching

Test person name matching against Notion workspace users:

```bash
# Test with Korean name
collabiq notion match-person "김철수"

# Test with ambiguous name
collabiq notion match-person "김"
```

**Expected Output**:
```
Person Match Result
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Match Type:        exact
  User Name:         김철수 (Cheolsu Kim)
  User ID:           user-uuid-123
  Similarity:        100%
  Confidence:        high
  Ambiguous:         No
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. List Notion Users

View all workspace users available for matching:

```bash
# List all users
collabiq notion list-users

# Force refresh from Notion API (bypass cache)
collabiq notion list-users --refresh
```

**Expected Output**:
```
Notion Workspace Users (3 users)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Name                        | Type   | Email
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  김철수 (Cheolsu Kim)        | person | cheolsu@example.com
  이영희 (Younghee Lee)       | person | younghee@example.com
  박지민 (Jimin Park)         | person | jimin@example.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cache Status: fresh (updated 2 hours ago)
```

### 4. Run Full Pipeline

Process an email end-to-end with enhanced field mapping:

```bash
# Process test email
collabiq test e2e --mode production --email-id test-email-001

# Verify fields populated in report
cat data/e2e_test/reports/20251110_143000-e2e_test.md
```

**Expected**: All three fields (담당자, 스타트업명, 협력기관) should be populated in the Notion entry.

## Use Cases

### Use Case 1: Company Name with Variations

**Scenario**: LLM extracts "웨이크(산스)" but Companies database has "웨이크"

**Steps**:
1. System searches for exact match "웨이크(산스)" → Not found
2. System computes fuzzy similarity for all companies
3. "웨이크" scores 0.87 (above 0.85 threshold)
4. System returns page_id for "웨이크"
5. FieldMapper populates 스타트업명 relation field with page_id

**Result**: ✅ Field successfully populated despite spelling variation

### Use Case 2: New Company

**Scenario**: LLM extracts "새로운스타트업" which doesn't exist in database

**Steps**:
1. System searches for exact match → Not found
2. System computes fuzzy similarity → All < 0.85
3. System auto-creates "새로운스타트업" in Companies database
4. System returns new page_id
5. FieldMapper populates 스타트업명 relation field

**Result**: ✅ New company created, field populated

### Use Case 3: Person Name Matching

**Scenario**: LLM extracts "김철수", Notion has "김철수 (Cheolsu Kim)"

**Steps**:
1. System loads cached user list (or fetches if stale)
2. System searches for exact match "김철수" → Not found
3. System computes fuzzy similarity for all users
4. "김철수 (Cheolsu Kim)" scores 0.95 (above 0.70 threshold)
5. System returns user_id
6. FieldMapper populates 담당자 people field

**Result**: ✅ Person field successfully populated

### Use Case 4: Ambiguous Person Name

**Scenario**: LLM extracts "김" (family name only), multiple users match

**Steps**:
1. System computes similarity for all users
2. Multiple "김" names score ≥ 0.70
3. Top 2 scores differ by < 0.10 → Mark ambiguous
4. System logs warning with alternative matches
5. System returns best match but logs for manual review

**Result**: ⚠️ Field populated with best guess, admin notified for review

## CLI Commands Reference

### Company Matching

```bash
# Basic company matching
collabiq notion match-company "<company_name>"

# With dry-run (no creation)
collabiq notion match-company "<company_name>" --dry-run

# Custom similarity threshold
collabiq notion match-company "<company_name>" --threshold 0.90
```

**Options**:
- `--dry-run`: Test matching without creating new companies
- `--threshold <float>`: Override default similarity threshold (default: 0.85)

### Person Matching

```bash
# Basic person matching
collabiq notion match-person "<person_name>"

# Show alternative matches
collabiq notion match-person "<person_name>" --show-alternatives
```

**Options**:
- `--show-alternatives`: Display other potential matches (useful for debugging ambiguity)

### User Management

```bash
# List all users
collabiq notion list-users

# Force cache refresh
collabiq notion list-users --refresh

# Export to JSON
collabiq notion list-users --format json > users.json
```

**Options**:
- `--refresh`: Bypass cache and fetch fresh data from Notion API
- `--format <table|json>`: Output format (default: table)

## Configuration

### Similarity Thresholds

Default thresholds are set in configuration:

```python
# config/settings.py
FUZZY_MATCHING_CONFIG = {
    "company_threshold": 0.85,  # Strict threshold for companies
    "person_threshold": 0.70,   # Lenient threshold for persons
    "ambiguity_threshold": 0.10  # Mark ambiguous if top 2 differ by <0.10
}
```

To override:
```bash
# Set via environment variable
export COLLABIQ_COMPANY_THRESHOLD=0.90
export COLLABIQ_PERSON_THRESHOLD=0.75
```

### Cache Settings

User list cache configuration:

```python
# config/settings.py
CACHE_CONFIG = {
    "user_list_ttl": 86400,  # 24 hours in seconds
    "cache_dir": "data/notion_cache/"
}
```

To force cache refresh:
```bash
# Delete cache file
rm data/notion_cache/users_list.json

# Or use --refresh flag
collabiq notion list-users --refresh
```

## Troubleshooting

### Issue 1: Company Not Matching Despite Exact Name

**Symptoms**: match-company returns "none" even though company exists

**Causes**:
- Company name has extra whitespace
- Company name has special characters
- Cache is stale

**Solutions**:
```bash
# Check exact company name in Notion database
collabiq notion list-companies | grep "웨이크"

# Try trimming whitespace
collabiq notion match-company "$(echo '웨이크 ' | xargs)"

# Clear cache and retry
rm -rf data/notion_cache/
collabiq notion match-company "웨이크"
```

### Issue 2: Person Field Always Empty

**Symptoms**: Person matching returns "none" for all names

**Causes**:
- User list cache is stale or corrupt
- Notion API permissions insufficient
- Person names in Notion are formatted differently

**Solutions**:
```bash
# Verify user list is populated
collabiq notion list-users --refresh

# Check if user exists
collabiq notion list-users | grep "김철수"

# Test with exact Notion name format
collabiq notion match-person "김철수 (Cheolsu Kim)"
```

### Issue 3: Auto-Creation Creating Duplicates

**Symptoms**: Multiple similar companies created (e.g., "웨이크", "웨이크", "웨이크 ")

**Causes**:
- Whitespace differences not normalized
- Concurrent email processing creating race conditions

**Solutions**:
```bash
# Manually merge duplicates in Notion
# Update CollabIQ entries to point to canonical company

# Verify exact matching works
collabiq notion match-company "웨이크"  # Should return existing

# Enable stricter threshold temporarily
export COLLABIQ_COMPANY_THRESHOLD=0.95
```

### Issue 4: Performance Degradation

**Symptoms**: match-company takes >2 seconds

**Causes**:
- Companies database has >1000 entries
- Notion API rate limits being hit

**Solutions**:
```bash
# Check database size
collabiq notion list-companies | wc -l

# Monitor API rate limits
collabiq status --component notion

# If >1000 companies, consider optimization (future enhancement)
```

## Validation

### Success Criteria Verification

After implementation, verify these success criteria:

**SC-001**: At least 90% of extracted company names successfully matched
```bash
# Run E2E test on 20+ emails
collabiq test e2e --mode production --count 20

# Check success rate in report
grep "Company match rate" data/e2e_test/reports/latest.md
```

**SC-002**: At least 85% of extracted person names successfully matched
```bash
# Check person match rate
grep "Person match rate" data/e2e_test/reports/latest.md
```

**SC-006**: All three fields populated in ≥90% of test emails
```bash
# Check field population rate
grep "Field population rate" data/e2e_test/reports/latest.md
```

## Next Steps

- **Production Deployment**: Run E2E tests with 20+ real emails to validate 90% match rates
- **Monitor Logs**: Check logs for low-confidence matches requiring manual review
- **Tune Thresholds**: Adjust similarity thresholds based on false positive/negative rates
- **Optimize Performance**: If >1000 companies, consider adding BK-tree indexing

## Support

For issues or questions:
- Check logs: `data/logs/collabiq.log`
- Review error details: `data/e2e_test/errors/`
- Contact: jlim@prorata.vc

---

**Document Status**: ✅ COMPLETE
**Last Updated**: 2025-11-10
**Next Review**: After Phase 3d implementation complete
