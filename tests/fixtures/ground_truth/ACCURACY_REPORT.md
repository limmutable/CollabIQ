# Entity Extraction Accuracy Validation Report

**Generated**: 2025-11-01 20:15:37
**Test Dataset**: 4 emails (2 Korean, 2 English)

## Summary

- **Overall Accuracy**: 100.0% (20/20 fields correct)
- **Korean Accuracy (SC-001)**: 100.0% (10/10 fields) - Target: ≥85%
- **English Accuracy (SC-002)**: 100.0% (10/10 fields) - Target: ≥85%

### Success Criteria

- ✅ **SC-001**: Korean email accuracy ≥85% (100.0%)
- ✅ **SC-002**: English email accuracy ≥85% (100.0%)

## Detailed Results

### ✅ english_001.txt - 100.0%

**Score**: 5/5 fields correct (100.0%)

- ✅ **person_in_charge**: Exact match
- ✅ **startup_name**: Exact match
- ✅ **partner_org**: Exact match
- ✅ **details**: Matched 4/5 keywords (80%)
- ✅ **date**: Date diff: 0 days (tolerance: ±1 days)

### ✅ english_002.txt - 100.0%

**Score**: 5/5 fields correct (100.0%)

- ✅ **person_in_charge**: Both null (correct)
- ✅ **startup_name**: Exact match
- ✅ **partner_org**: Exact match
- ✅ **details**: Matched 4/4 keywords (100%)
- ✅ **date**: Date diff: 0 days (tolerance: ±7 days)

⚠️  **Low Confidence**: person

### ✅ korean_001.txt - 100.0%

**Score**: 5/5 fields correct (100.0%)

- ✅ **person_in_charge**: Exact match
- ✅ **startup_name**: Exact match
- ✅ **partner_org**: Exact match
- ✅ **details**: Matched 5/5 keywords (100%)
- ✅ **date**: Date diff: 0 days (tolerance: ±7 days)

### ✅ korean_002.txt - 100.0%

**Score**: 5/5 fields correct (100.0%)

- ✅ **person_in_charge**: Exact match
- ✅ **startup_name**: Exact match
- ✅ **partner_org**: Exact match
- ✅ **details**: Matched 5/5 keywords (100%)
- ✅ **date**: Date diff: 0 days (tolerance: ±1 days)

## Recommendations

- ✅ Overall accuracy meets target. System is ready for MVP.
- 📝 Only 4 test emails available. Target is 30 emails (20 Korean + 10 English) for comprehensive validation.
