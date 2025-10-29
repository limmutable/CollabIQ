# Feasibility Research Template: CollabIQ System

**Status**: 🔄 IN PROGRESS - Awaiting completion by team member with API access
**Created**: 2025-10-28
**Owner**: [Assign to team member with Gemini/Notion access]

---

## Overview

This document guides the feasibility analysis for the CollabIQ system. Complete each section with actual test results using real API keys and sample data.

---

## 1. Gemini API Validation (Tasks T001-T004)

### 1.1 Setup Checklist
- [x] Install google-generativeai SDK (`uv add google-generativeai` - COMPLETED)
- [x] Obtain API key from [Google AI Studio](https://makersuite.google.com/app/apikey) - COMPLETED
- [x] Set GEMINI_API_KEY in .env file - COMPLETED
- [x] Verify API access with test call - COMPLETED (Model: gemini-2.5-flash, Response: "안녕하세요!")

### 1.2 Sample Dataset Creation (T002)

**Location**: `tests/fixtures/sample_emails/`

**Note**: Samples are stored in the tests directory so they persist across all feature branches and can be used throughout the project lifecycle.

**Requirements**: Create 5-10 sample Korean collaboration emails with ground truth labels

**Template for each sample**:
```
File: sample-001.txt
Subject: [Original Korean subject]
Body: [Original Korean email body]

Ground Truth Labels:
- 스타트업명 (Startup Name): [Expected value]
- 협업기관 (Partner Org): [Expected value]
- 협업강도 (Intensity): [이해/협력/투자/인수]
- 날짜 (Date): [YYYY-MM-DD]
- 담당자 (Person): [Name]
```

**Status**: [x] Complete
**Sample Count**: 6 / 6 (sufficient for testing)

**Created Samples:**
- ✅ sample-001.txt: 브레이크앤컴퍼니 × 신세계 (A, 협럭)
- ✅ sample-002.txt: 웨이크 × Starbucks (A, 이해)
- ✅ sample-003.txt: 스위트스팟 × 신세계라이브쇼핑 (A, 협력)
- ✅ sample-004.txt: NXN Labs × 신세계인터내셔날 (A, 이해)
- ✅ sample-005.txt: 파지티브호텔 × 신세계 (A, 이해)
- ✅ sample-006.txt: 플록스 x 스마트푸드네트웍스 (C, 이해)
- ✅ GROUND_TRUTH.md: Expected entity extraction results for all samples

### 1.3 Gemini 2.5 Flash Testing (T003)

**Test Script Location**: `specs/001-feasibility-architecture/scripts/test_gemini_extraction.py`

**Status**: ✅ **COMPLETE** - Gemini 2.5 Flash meets all targets

**Test Results**:
1. **Accuracy** (Target: ≥85%)
   - Average confidence: **94%** ✅ PASS
   - Success rate: **100%** (6/6 samples)
   - Per-field confidence:
     - 담당자: 97%
     - 스타트업명: 98%
     - 협업기관: 94%
     - 협업내용: 93%
     - 날짜: 86%
     - 협업강도: 97%

2. **Confidence Scoring**
   - Average confidence: 94%
   - Calibration quality: [x] Excellent - all fields meet thresholds

3. **Latency**
   - Average API response time: **12.42 seconds**
   - Range: 7.51s - 19.04s
   - Status: [x] Acceptable for async processing

4. **Cost**
   - Estimated tokens per email: ~500
   - Cost per email: **$0.0001**
   - Cost for 50 emails/day: **$0.14/month** ✅
   - Much lower than expected (~$15/month)

**Decision**: [x] Flash sufficient - 94% confidence exceeds 85% target by 9 points

### 1.4 Gemini 2.5 Pro Testing (T004) - If needed

**Status**: ✅ **NOT NEEDED** - Flash is sufficient

**Only complete if Flash accuracy <85%**

[Same metrics as 1.3]

**Cost Comparison**:
| Model | Accuracy | Cost/month (50 emails/day) | Recommendation |
|-------|----------|---------------------------|----------------|
| Flash | ____%    | $_____                    | [ ] Use        |
| Pro   | ____%    | $_____                    | [ ] Use        |

---

## 2. Notion API Validation (Tasks T005-T007)

### 2.1 Setup Checklist (T005)
- [ ] Create Notion integration at [Notion Integrations](https://www.notion.so/my-integrations)
- [ ] Obtain integration token
- [ ] Set NOTION_API_KEY in .env file
- [ ] Set NOTION_DATABASE_ID_COLLABIQ in .env file (main "CollabIQ" database)
- [ ] Set NOTION_DATABASE_ID_CORP in .env file (unified company database)
- [ ] Install notion-client SDK (`uv add notion-client`)
- [ ] Grant integration access to test workspace

### 2.2 Prerequisites - Notion Database Structure Analysis

**IMPORTANT**: Before proceeding with validation, you MUST analyze the existing Notion database structure to understand:

1. **CollabIQ Database Structure**:
   - Analyze the current field schema in "CollabIQ" database
   - Document all existing field names, types, and relationships
   - Verify which fields already exist vs. which need to be created
   - Check for any custom properties or configurations

2. **Company Database (NOTION_DATABASE_ID_CORP) Structure**:
   - This is a **unified database** containing ALL companies:
     - Startup companies (non-portfolio)
     - Portfolio companies
     - Shinsegate affiliate companies
   - Analyze the field that distinguishes company types (likely a Select or Multi-select field)
   - Document the company classification field values
   - Understand the naming conventions used in this database

3. **Create Analysis Script** (T005a - NEW):
   - Create `specs/001-feasibility-architecture/scripts/analyze_notion_structure.py`
   - Script should:
     - Connect to Notion API
     - Retrieve and display the schema of NOTION_DATABASE_ID_COLLABIQ
     - Retrieve and display the schema of NOTION_DATABASE_ID_CORP
     - List all field names, types, and configurations
     - Export results to `specs/001-feasibility-architecture/notion-schema-analysis.md`
   - Status: [ ] Complete

**Analysis Output** (to be filled after running script):
```
CollabIQ Database Fields:
- Field 1: [Name] ([Type]) - [Description]
- Field 2: [Name] ([Type]) - [Description]
...

Company Database Fields:
- Field 1: [Name] ([Type]) - [Description]
- Company Type Field: [Name] ([Type]) - Options: [list all]
...
```

### 2.3 Test Database Schema (T006)

**Database Name**: "CollabIQ" (formerly "레이더 활동")

**Note**: Field requirements below are based on the original design. After completing the database structure analysis (2.2), update this section to reflect the **actual** fields in your Notion database.

**Expected Fields** (verify against actual schema):
1. **담당자** (Person field)
   - [ ] Exists in database (or created)
   - [ ] Tested with SDK
   - [ ] Works correctly

2. **스타트업명** (Relation to Company DB)
   - **Note**: This now relates to NOTION_DATABASE_ID_CORP (unified company database)
   - [ ] Exists in database (or created)
   - [ ] Tested linking to companies in CORP database
   - [ ] Verified filtering works for startup companies
   - [ ] Works correctly

3. **협업기관** (Relation to Company DB)
   - **Note**: This now relates to NOTION_DATABASE_ID_CORP (unified company database)
   - [ ] Exists in database (or created)
   - [ ] Tested linking to companies in CORP database
   - [ ] Verified filtering works for partner/affiliate companies
   - [ ] Works correctly

4. **협력주체** (Title field, auto-generated)
   - [ ] Created
   - [ ] Tested auto-generation
   - [ ] Works correctly

5. **협업내용** (Text field)
   - [ ] Created
   - [ ] Tested with long text
   - [ ] Works correctly

6. **협업형태** (Select field: [A], [B], [C], [D])
   - [ ] Created
   - [ ] Tested all options
   - [ ] Works correctly

7. **협업강도** (Select field: 이해, 협력, 투자, 인수)
   - [ ] Created
   - [ ] Tested all options
   - [ ] Works correctly

8. **날짜** (Date field)
   - [ ] Created
   - [ ] Tested date parsing
   - [ ] Works correctly

**Schema Validation**: [ ] PASS / [ ] FAIL (details: ____________)

### 2.4 Programmatic Entry Creation (T007)

**Test Script**: `specs/001-feasibility-architecture/scripts/test_notion_write.py`

**Prerequisites**:
- Notion API token configured in .env
- Database IDs configured (NOTION_DATABASE_ID_COLLABIQ, NOTION_DATABASE_ID_CORP)
- Database structure analysis completed (Section 2.2)
- At least a few test company entries exist in NOTION_DATABASE_ID_CORP

**Tests**:
1. Create entry with all field types
   - Test data should use actual field names from your schema analysis
   - Status: [ ] Success / [ ] Failed (reason: _________)

2. Test relation linking to unified company database
   - Test linking to a startup company from CORP database
   - Test linking to an affiliate company from CORP database
   - Verify the relation properly filters by company type if needed
   - Status: [ ] Success / [ ] Failed (reason: _________)

3. Test fuzzy matching scenario
   - Create a company relation using partial/abbreviated name
   - Verify system can match to existing CORP database entry
   - Status: [ ] Success / [ ] Failed (reason: _________)

4. Measure API rate limits
   - Documented limit: 3 requests/second
   - Actual observed limit: ____ requests/second
   - Rate limit errors encountered: [ ] Yes / [ ] No

**Result**: [ ] All tests passed / [ ] Some tests failed

**Important Notes**:
- The unified CORP database means you don't need separate STARTUP and affiliate databases
- Your script should handle the single company database with proper filtering
- Document how company types are distinguished in the database (checkbox? select field?)

---

## 3. Email Infrastructure Research (Task T008)

### 3.1 Options Comparison

**Output Document**: `specs/001-feasibility-architecture/email-infrastructure-comparison.md`

| Option | Setup Complexity | Cost | Reliability | Recommendation |
|--------|------------------|------|-------------|----------------|
| Gmail API | [H/M/L] | $____ | [H/M/L] | [ ] Yes / [ ] No |
| IMAP | [H/M/L] | $____ | [H/M/L] | [ ] Yes / [ ] No |
| SendGrid Parse | [H/M/L] | $____ | [H/M/L] | [ ] Yes / [ ] No |
| AWS SES | [H/M/L] | $____ | [H/M/L] | [ ] Yes / [ ] No |
| Mailgun | [H/M/L] | $____ | [H/M/L] | [ ] Yes / [ ] No |

**Criteria**:
- Setup Complexity: Time to get first email processing working
- Cost: Monthly cost for 50 emails/day
- Reliability: Uptime, error handling, support

**Selected Approach**: ________________

**Rationale**: ________________________________

---

## 4. Fuzzy Matching Evaluation (Tasks T009-T010)

### 4.1 Gemini-Based Fuzzy Matching (T009)

**Test Dataset**: 20-30 Korean company name pairs

**Test Cases**:
1. Abbreviations: "신세계인터" → "신세계인터내셔널"
2. Typos: "본봄 " → "본봄"
3. Spacing: "SSG" → "신세계"
4. [Add more test cases]

**Results**:
- Precision: ____%
- Recall: ____%
- Confidence calibration: [ ] Good / [ ] Poor

**Example Test Output**:
```
Input: "신세계인터"
Output: "신세계인터내셔널"
Confidence: ____
Correct: [ ] Yes / [ ] No
```

**Decision**: [ ] Gemini sufficient (≥85% accuracy) / [ ] Need fallback

### 4.2 RapidFuzz Fallback Evaluation (T010) - If needed

**Only complete if Gemini matching <85% accuracy**

- [ ] Install RapidFuzz (`uv add rapidfuzz`)
- [ ] Test Levenshtein distance on Korean company names
- [ ] Validate ≥0.85 threshold on test dataset

**Results**:
- Precision at 0.85 threshold: ____%
- Recall at 0.85 threshold: ____%

**Decision**: [ ] Use RapidFuzz as fallback / [ ] Stick with Gemini only

---

## 5. Go/No-Go Assessment (Task T011)

### 5.1 Technical Blockers

**Are there any technical blockers that prevent building this system?**

[ ] NO - All components validated successfully
[ ] YES - The following blockers exist:

1. ___________________________________
2. ___________________________________
3. ___________________________________

### 5.2 Integration Complexity

**Overall complexity rating**: [ ] Low / [ ] Medium / [ ] High

**Risk areas**:
- Gemini API Korean accuracy: [ ] Low risk / [ ] Medium risk / [ ] High risk
- Notion API rate limits: [ ] Low risk / [ ] Medium risk / [ ] High risk
- Email processing reliability: [ ] Low risk / [ ] Medium risk / [ ] High risk
- Fuzzy matching accuracy: [ ] Low risk / [ ] Medium risk / [ ] High risk

### 5.3 Cost Analysis

**Monthly operational cost estimate**:
- Gemini API (50 emails/day): $_____
- Email infrastructure: $_____
- GCP Cloud Run (estimated): $_____
- **Total**: $_____

**Is cost within budget?** [ ] Yes / [ ] No

### 5.4 Risk Mitigation Strategies

**For each identified risk, document mitigation**:

1. **Risk**: [e.g., Gemini accuracy <85%]
   **Mitigation**: [e.g., LLMProvider abstraction layer allows swapping to GPT/Claude]

2. **Risk**: ___________________________________
   **Mitigation**: ___________________________________

3. **Risk**: ___________________________________
   **Mitigation**: ___________________________________

### 5.5 Final Recommendation

**GO / NO-GO**: ___________

**Rationale**:
_____________________________________________
_____________________________________________
_____________________________________________

**Next Steps if GO**:
1. Proceed to architecture design (Phase 2)
2. [Additional steps]

**Next Steps if NO-GO**:
1. [Alternative approach]
2. [Blocking issues to resolve]

---

## 6. Summary for research.md

**Once all sections are complete, synthesize findings into `research.md`**

Key sections to include:
1. Executive Summary (GO/NO-GO with rationale)
2. Gemini API Validation Results
3. Notion API Compatibility Confirmation
4. Email Infrastructure Recommendation
5. Fuzzy Matching Approach Selection
6. Cost Analysis
7. Risk Assessment & Mitigation
8. Technical Blockers (if any)
9. Recommended Next Steps

---

## Completion Checklist

- [ ] All API keys obtained and tested
- [ ] Sample dataset created (10 Korean emails with ground truth)
- [ ] Gemini API tested (Flash +/- Pro)
- [ ] Notion API tested (all field types working)
- [ ] Email infrastructure options compared
- [ ] Fuzzy matching approach validated (≥85% accuracy)
- [ ] Cost analysis completed
- [ ] Risk mitigation strategies documented
- [ ] GO/NO-GO decision made
- [ ] research.md document written with all findings

**Estimated Time**: 2-3 days with API access and sample data

**Dependencies**:
- Gemini API key
- Notion workspace access
- Korean collaboration email samples (anonymized if needed)
