# Ground Truth Labels for Test Emails

This file contains the expected entity extraction results for each sample email. Use these labels to measure extraction accuracy.

---

## Sample 001: 브레이크앤컴퍼니 x 신세계

**Expected Entities:**
- 담당자: Jeffrey Lim (jeffreylim@signite.co)
- 스타트업명: 브레이크앤컴퍼니
- 협업기관: 신세계 (신세계백화점)
- 협업내용: AI 기반 재고 최적화 솔루션 PoC, 강남점 파일럿 테스트, 11월 첫째 주부터 2개월간 시범 운영
- 날짜: 2024-10-28 (이메일 작성일 기준)
- 협업형태: [A] PortCo × SSG
- 협업강도: 협력

**Confidence Scores (Expected):**
- person: 0.95+
- startup: 0.90+
- partner: 0.85+
- details: 0.90+
- date: 0.80+

---

## Sample 002: 웨이크 - 신세계인터내셔날

**Expected Entities:**
- 담당자: Gloria Kim (gloriakim@signite.co)
- 스타트업명: 웨이크
- 협업기관: 신세계인터내셔날
- 협업내용: Z세대 뷰티 큐레이션 플랫폼, 신세계인터 온라인몰 입점 전용관 오픈, 공동 마케팅 캠페인, 12월 파일럿 론칭 목표
- 날짜: 2024-10-25 (미팅 날짜 기준)
- 협업형태: [A] PortCo × SSG
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
- 담당자: 이성범 (sblee@signite.co)
- 스타트업명: 스위트스팟
- 협업기관: 신세계라이브쇼핑, 신세계 그룹 (벤처캐피탈)
- 협업내용: 시리즈 A 투자 50억원 유치, 골프 예약 플랫폼, 라이브 커머스 협업, 골프용품 라이브 방송, 2024년 Q1 본격 협업
- 날짜: 2024-11월 (예정)
- 협업형태: [A] PortCo × SSG
- 협업강도: 투자 + 협력

**Confidence Scores (Expected):**
- person: 0.90+
- startup: 0.95+
- partner: 0.85+ (multiple partners)
- details: 0.90+
- date: 0.70+

---

## Sample 004: 블룸에이아이 - 신세계푸드

**Expected Entities:**
- 담당자: Jeffrey (jeffreylim@signite.co)
- 스타트업명: 블룸에이아이
- 협업기관: 신세계푸드
- 협업내용: 음성 AI 주문 시스템, 콜센터 자동화, B2B 전화 주문 처리, 파일럿 10/15 시작, 일 평균 200건 처리
- 날짜: 2024-10-15 (파일럿 시작일)
- 협업형태: [A] PortCo × SSG
- 협업강도: 협력

**Confidence Scores (Expected):**
- person: 0.85+ (abbreviated name)
- startup: 0.90+
- partner: 0.90+
- details: 0.85+
- date: 0.85+

---

## Sample 005: 파지티브호텔 초기 미팅

**Expected Entities:**
- 담당자: Gloria Kim (gloriakim@signite.co)
- 스타트업명: 파지티브호텔
- 협업기관: 신세계백화점, 신세계 (유통 전략팀)
- 협업내용: 호텔 재고 최적화 SaaS, VIP 고객 호텔 제휴, SSG PAY 연동, 상품권 결제 지원, 초기 미팅 완료
- 날짜: 2024-10-28 (미팅 날짜 기준)
- 협업형태: [A] PortCo × SSG
- 협업강도: 이해

**Confidence Scores (Expected):**
- person: 0.95+
- startup: 0.90+
- partner: 0.85+
- details: 0.80+
- date: 0.75+

---

## Sample 006: 스마트푸드네트웍스 인수 협상

**Expected Entities:**
- 담당자: 이성범 (sblee@signite.co)
- 스타트업명: 스마트푸드네트웍스
- 협업기관: 신세계푸드
- 협업내용: B2B 식자재 유통 플랫폼 인수, LOI 체결 완료, 실사 진행 중, 인수 금액 약 200억원, 11월 말 최종 계약 목표
- 날짜: 2024-10-20 (LOI 체결일)
- 협업형태: [A] PortCo × SSG
- 협업강도: 인수

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
- Startups: 6 unique (브레이크앤컴퍼니, 웨이크, 스위트스팟, 블룸에이아이, 파지티브호텔, 스마트푸드네트웍스)
- Partners: 4 unique SSG affiliates (신세계, 신세계인터내셔날, 신세계푸드, 신세계라이브쇼핑)
- Senders: 3 unique (jeffreylim@signite.co, gloriakim@signite.co, sblee@signite.co)

**Collaboration Type:**
- All samples: [A] PortCo × SSG affiliate

**Collaboration Intensity:**
- 이해: 2 samples (웨이크, 파지티브호텔)
- 협력: 3 samples (브레이크앤컴퍼니, 블룸에이아이, 스위트스팟)
- 투자: 1 sample (스위트스팟)
- 인수: 1 sample (스마트푸드네트웍스)

**Accuracy Target:** ≥85% across all fields

**Test Coverage:**
- ✅ Korean language extraction
- ✅ Multiple SSG affiliates
- ✅ All collaboration intensities (이해/협력/투자/인수)
- ✅ Various date formats
- ✅ Abbreviated names (Jeffrey vs Jeffrey Lim)
- ✅ Multiple partners in one email
- ✅ Complex business scenarios (PoC, pilot, investment, M&A)
