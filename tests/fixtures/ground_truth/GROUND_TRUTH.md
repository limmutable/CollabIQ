# Ground Truth for Entity Extraction Test Dataset

This file contains expected extraction results for the test email dataset.
Used for accuracy validation (SC-001, SC-002).

## Format

Each entry contains:
- File: Test email filename
- Expected Entities: person_in_charge, startup_name, partner_org, details, date
- Notes: Any special considerations

---

## Korean Emails

### korean_001.txt

**Input**: "어제 신세계인터내셔널과 본봄 파일럿 킥오프 미팅을 진행했습니다..."

**Expected**:
- person_in_charge: "김철수"
- startup_name: "본봄"
- partner_org: "신세계인터내셔널"
- details: "파일럿 킥오프 미팅, 테이블 예약 시스템 통합 논의, 11월 1주에 PoC 시작 예정"
- date: 2025-11-01 (November 1st week)

**Confidence Threshold**: All ≥0.85

---

### korean_002.txt

**Input**: "신세계푸드와 TableManager 레스토랑 예약 시스템 도입 협의..."

**Expected**:
- person_in_charge: "이영희"
- startup_name: "TableManager"
- partner_org: "신세계푸드"
- details: "레스토랑 예약 시스템 도입 협의, 10월 27일 미팅에서 시범 운영 논의, 11월부터 3개월간 파일럿 테스트 진행 예정"
- date: 2025-10-27

**Confidence Threshold**: All ≥0.85

---

## English Emails

### english_001.txt

**Input**: "TableManager kicked off the pilot program with Shinsegae Food yesterday..."

**Expected**:
- person_in_charge: "John Kim"
- startup_name: "TableManager"
- partner_org: "Shinsegae Food"
- details: "pilot program kickoff, restaurant reservation system integration, 3-month trial period beginning next Monday"
- date: 2025-10-31 (yesterday, relative to 2025-11-01)

**Confidence Threshold**: All ≥0.85

---

### english_002.txt

**Input**: "Yesterday we had a kickoff meeting with Shinsegae International for the BonBom pilot..."

**Expected**:
- person_in_charge: null (missing)
- startup_name: "BonBom"
- partner_org: "Shinsegae International"
- details: "kickoff meeting, PoC scheduled to start in the first week of November, table reservation system integration"
- date: 2025-11-01 (first week of November)

**Confidence Threshold**: All ≥0.85 except person_in_charge (0.0)

---

## Validation Criteria

**SC-001**: ≥85% extraction accuracy on 20 Korean emails
**SC-002**: ≥85% extraction accuracy on 10 English emails

**Accuracy Calculation**:
```
accuracy = (correct_extractions / total_fields) * 100%

where:
- total_fields = 5 entities × number_of_emails
- correct_extractions = count of fields matching ground truth
```

**Matching Rules**:
- Exact match for person_in_charge, startup_name, partner_org
- Semantic match for details (contains key information)
- Date match within ±1 day tolerance for relative dates
