# Test Email Samples for CollabIQ

**Location**: `tests/fixtures/sample_emails/`

This directory contains mock Korean collaboration emails used for testing the Gemini API entity extraction accuracy throughout the project development lifecycle. These samples persist across all feature branches and serve as the canonical test dataset.

## Purpose

These samples are used to:
1. **Validate Gemini API** entity extraction accuracy (Task T003)
2. **Benchmark performance** across different model versions
3. **Test end-to-end pipeline** from email ingestion to Notion creation
4. **Regression testing** when making changes to extraction logic

## Files

### Sample Emails (6 files)

- **sample-001.txt**: 브레이크앤컴퍼니 × 신세계 백화점 (협력 - PoC 파일럿)
- **sample-002.txt**: 웨이크 × 신세계인터내셔날 (이해 - 제안서 검토)
- **sample-003.txt**: 스위트스팟 × 신세계라이브쇼핑 (투자 + 협력)
- **sample-004.txt**: 블룸에이아이 × 신세계푸드 (협력 - 파일럿 운영)
- **sample-005.txt**: 파지티브호텔 × 신세계 (이해 - 초기 논의)
- **sample-006.txt**: 스마트푸드네트웍스 × 신세계푸드 (인수 - 실사 진행)

### Ground Truth Labels

- **../ground_truth/GROUND_TRUTH.md**: Expected extraction results for all test emails with confidence thresholds
- **../ground_truth/ACCURACY_REPORT.md**: Actual extraction accuracy results from Phase 1b testing

## Test Coverage

### Companies

**Startups (6 unique):**
1. 브레이크앤컴퍼니 - AI 재고 최적화
2. 웨이크 - Z세대 뷰티 플랫폼
3. 스위트스팟 - 골프 예약 플랫폼
4. 블룸에이아이 - 음성 AI
5. 파지티브호텔 - 호텔 예약 SaaS
6. 스마트푸드네트웍스 - B2B 식자재 유통

**SSG Affiliates (4 unique):**
1. 신세계 (백화점)
2. 신세계인터내셔날 (패션/뷰티)
3. 신세계푸드 (식품/외식)
4. 신세계라이브쇼핑 (홈쇼핑)

### Collaboration Intensities

- **이해** (Understand): 2 samples - Initial meetings, proposal review
- **협력** (Cooperate): 3 samples - Pilots, PoCs, active collaboration
- **투자** (Invest): 1 sample - Series A funding
- **인수** (Acquire): 1 sample - M&A due diligence

### Email Senders

- jeffreylim@signite.co (2 emails)
- gloriakim@signite.co (2 emails)
- sblee@signite.co (2 emails)

## Accuracy Target

**Overall Target**: ≥85% accuracy across all entity fields

**Per-Field Targets:**
- 담당자 (Person): ≥85%
- 스타트업명 (Startup): ≥85%
- 협업기관 (Partner): ≥85%
- 협업내용 (Details): ≥80%
- 날짜 (Date): ≥75%
- 협업강도 (Intensity): ≥85%

## Usage

### Manual Testing

```bash
# Read a sample email
cat tests/fixtures/sample_emails/sample-001.txt

# Check expected results
cat tests/fixtures/ground_truth/GROUND_TRUTH.md
```

### Automated Testing (Future)

```bash
# Run entity extraction test script (to be created in Phase 1b)
uv run pytest tests/integration/test_gemini_extraction.py

# Expected output:
# ✓ Sample 001: 92% accuracy (5/5 fields correct)
# ✓ Sample 002: 88% accuracy (5/5 fields correct)
# ...
# Overall: 89% accuracy (PASS ≥85%)
```

## Notes

- **Fictional Data**: All emails are mock data created for testing purposes
- **Korean Language**: All emails are in Korean to test language-specific extraction
- **Realistic Scenarios**: Based on actual SSG affiliate collaboration patterns
- **Recipient Emails**: Placeholder `[recipient@ssg.com]` - fill in actual addresses as needed
- **Dates**: Use relative dates (e.g., "어제", "11월 첫째 주") to test date parsing

## Maintenance

When updating samples:
1. Update the sample .txt file
2. Update corresponding ground truth labels in ../ground_truth/GROUND_TRUTH.md
3. Re-run extraction tests to verify accuracy
4. Update ACCURACY_REPORT.md with new results
5. Update this README if adding new samples or test scenarios

---

**Created**: 2025-10-28
**Last Updated**: 2025-10-28
**Sample Count**: 6 emails
**Test Coverage**: All 4 collaboration intensities, 4 SSG affiliates, 6 startups
