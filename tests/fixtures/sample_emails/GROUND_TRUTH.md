# Ground Truth Labels for Test Emails

This file contains the expected entity extraction results for each sample email. Use these labels to measure extraction accuracy.

---

## Sample 001: 브레이크앤컴퍼니 x 신세계

**Expected Entities:**
- 담당자: 김주영 <gloriakim@signite.co>
- 스타트업명: 브레이크앤컴퍼니
- 협업기관: 신세계 (신세계백화점)
- 협업내용: AI 기반 재고 최적화 솔루션 PoC, 강남점 파일럿 테스트, 11월 첫째 주부터 2개월간 시범 운영
- 날짜: 2025-10-28
- 협업형태: [A] PortCo X SSG
- 협업강도: 협력

**Confidence Scores (Expected):**
- person: 0.95+
- startup: 0.90+
- partner: 0.85+
- details: 0.90+
- date: 0.80+

---

## Sample 002: WAKE - Starbucks

**Expected Entities:**
- 담당자: 김주영 <gloriakim@signite.co>
- 스타트업명: 웨이크 (WAKE)
- 협업기관: Starbucks
- 협업내용: Sans Coffee 소개
- 날짜: 2025-07-15
- 협업형태: [A] PortCo X SSG
- 협업강도: 이해

**Confidence Scores (Expected):**
- person: 0.95+
- startup: 0.90+
- partner: 0.90+
- details: 0.85+
- date: 0.75+

---

## Sample 003: 스위트스팟 투자 및 협업

**Expected Entities:**
- 담당자: 임정민 <jeffreylim@signite.co>
- 스타트업명: 스위트스팟
- 협업기관: 신세계라이브쇼핑
- 협업내용: 시리즈 A 투자 50억원 유치, 골프 거리측정계 제품 소개, 라이브 커머스 협업, 골프용품 라이브 방송, 2026년 Q1 본격 협업
- 날짜: 2025-11-18
- 협업형태: [A] PortCo X SSG
- 협업강도: 협력

**Confidence Scores (Expected):**
- person: 0.90+
- startup: 0.95+
- partner: 0.85+ (multiple partners)
- details: 0.90+
- date: 0.70+

---

## Sample 004: NXN Labs - 신세계인터내셔날

**Expected Entities:**
- 담당자: 임정민 <jeffreylim@signite.co>
- 스타트업명: NXN Labs
- 협업기관: 신세계인터내셔날
- 협업내용: NXN Labs 소개 및 Shinsegae V 앱내에 NXN이 AI로 자동생성한 이미지 적용 PoC 문의
- 날짜: 2025-10-12
- 협업형태: [A] PortCo X SSG
- 협업강도: 이해

**Confidence Scores (Expected):**
- person: 0.85+ (abbreviated name)
- startup: 0.90+
- partner: 0.90+
- details: 0.85+
- date: 0.85+

---

## Sample 005: 파지티브호텔 초기 미팅

**Expected Entities:**
- 담당자: 김주영 <gloriakim@signite.co>
- 스타트업명: 파지티브호텔
- 협업기관: 신세계
- 협업내용: 호텔 재고 최적화 SaaS, VIP 고객 호텔 제휴, SSG PAY 연동, 상품권 결제 지원, 초기 미팅 완료
- 날짜: 2025-10-25
- 협업형태: [A] PortCo X SSG
- 협업강도: 이해

**Confidence Scores (Expected):**
- person: 0.95+
- startup: 0.90+
- partner: 0.85+
- details: 0.80+
- date: 0.75+

---

## Sample 006: 플록스 <> 스마트푸드네트웍스 협업을 위한 소개

**Expected Entities:**
- 담당자: 임정민 <jeffreylim@signite.co>
- 스타트업명: 플록스
- 협업기관: 스마트푸드네트웍스
- 협업내용: 차별화상회 앱의 구매전환율 개선 프로젝트 상담을 위한 소개
- 날짜: 2025-11-02
- 협업형태: [C] PortCo X PortCo
- 협업강도: 이해

**Confidence Scores (Expected):**
- person: 0.90+
- startup: 0.95+
- partner: 0.90+
- details: 0.90+
- date: 0.80+

---

## Summary Statistics

**Total Samples:** 6

**Company Distribution:**
- Startups: 6 unique (브레이크앤컴퍼니, 웨이크, 스위트스팟, NXN Labs, 파지티브호텔, 플록스)
- Partners: 4 unique SSG affiliates (신세계, Starbucks, 신세계라이브쇼핑, 신세계인터내셔날) and 1 Portfolio Company (스마트푸드네트웍스)
- Senders: 2 unique (jeffreylim@signite.co, gloriakim@signite.co)

**Collaboration Type:**
- [A] 5 sampels
- [C] 1 sample

**Collaboration Intensity:**
- 이해: 4 samples (웨이크, NXN Labs, 파지티브호텔, 플록스)
- 협력: 2 samples (브레이크앤컴퍼sl, 스위트스팟)

**Accuracy Target:** ≥85% across all fields

**Test Coverage:**
- ✅ Korean language extraction
- ✅ Multiple SSG affiliates
- ✅ At least 2 collaboration intensities among (이해/협력/투자/인수)
- ✅ Various date formats
- ✅ Abbreviated names (Jeffrey vs Jeffrey Lim)
- ✅ Multiple partners in one email
- ✅ Complex business scenarios (PoC, pilot, investment, M&A)
