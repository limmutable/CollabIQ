# Feature Specification: Classification & Summarization

**Feature Branch**: `008-classification-summarization`
**Created**: 2025-11-03
**Status**: Draft
**Input**: User description: "Phase 2c - Classification & Summarization: Classify collaboration types ([A]/[B]/[C]/[D]) and intensity levels (이해/협력/투자/인수), and generate structured summaries of collaboration content for Notion database entries"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify Collaboration Type (Priority: P1)

When an email describes a collaboration involving a portfolio startup and an SSG affiliate (e.g., "브레이크앤컴퍼니 × 신세계푸드 PoC"), the system automatically determines the collaboration type as "[A]PortCoXSSG" (exact Notion database field value), enabling proper categorization in the Notion CollabIQ database.

**Why this priority**: Core functionality - every collaboration must be classified to be useful. Classification type determines reporting, tracking, and business insights. Without this, the system cannot organize collaborations meaningfully. This is the minimum viable feature that delivers immediate value by automatically categorizing collaborations.

**Independent Test**: Use Phase 2b test results (matched company IDs with classifications) and verify the system correctly determines exact Notion field values: "[A]PortCoXSSG" for portfolio×SSG, "[C]PortCoXPortCo" for portfolio×portfolio, "[B]Non-PortCoXSSG" for portfolio×external, and "[D]Other" for non-portfolio collaborations. Can be tested with existing ground truth emails without implementing intensity classification or summarization.

**Acceptance Scenarios**:

1. **Given** email "브레이크앤컴퍼니 x 신세계푸드 PoC 킥오프" with matched_company_id (classification: Portfolio) and matched_partner_id (classification: SSG Affiliate), **When** GeminiAdapter classifies collaboration type, **Then** collaboration_type is "[A]PortCoXSSG" (exact Notion field value) with confidence ≥0.90

2. **Given** email "플록스 × 스마트푸드네트워크 장바구니 개선" with both IDs classified as Portfolio, **When** system classifies, **Then** collaboration_type is "[C]PortCoXPortCo" (exact Notion field value) with confidence ≥0.90

3. **Given** email "웨이크 × Microsoft Teams 통합" with matched_company_id (Portfolio) and partner not in database (external), **When** system classifies, **Then** collaboration_type is "[B]Non-PortCoXSSG" (exact Notion field value) with confidence ≥0.85

4. **Given** email "삼성전자 x LG협력" with neither company being portfolio companies, **When** system classifies, **Then** collaboration_type is "[D]Other" (exact Notion field value) with confidence ≥0.70

---

### User Story 2 - Classify Collaboration Intensity (Priority: P1)

When an email describes collaboration activities (e.g., "투자 검토", "PoC 킥오프", "인수 논의"), the system identifies the collaboration intensity level (이해/협력/투자/인수) based on semantic understanding of Korean business terminology, ensuring accurate tracking of collaboration depth.

**Why this priority**: Equally critical as type classification - intensity determines urgency, resource allocation, and strategic importance. Both type and intensity are required for complete collaboration tracking. This enables filtering high-priority collaborations (투자/인수) from exploratory ones (이해).

**Independent Test**: Use existing test email fixtures (tests/fixtures/sample_emails/sample-001.txt through sample-006.txt) to verify correct intensity classification with confidence ≥0.85. Can be tested independently of type classification by using emails with known intensity indicators.

**Acceptance Scenarios**:

1. **Given** sample-005.txt "파지티브호텔 첫 미팅 결과" (contains "협업 가능성 논의"), **When** system classifies intensity, **Then** collaboration_intensity is "이해" (Understanding/Exploration) with confidence ≥0.85

2. **Given** sample-001.txt "브레이크앤컴퍼니 x 신세계 PoC 킥오프 결과" (contains "PoC 킥오프 미팅", "파일럿 테스트"), **When** system classifies intensity, **Then** collaboration_intensity is "협력" (Cooperation/Pilot) with confidence ≥0.90

3. **Given** sample-003.txt "스위트스팟 골프 거리측정계 제품 소개" (contains "시리즈 A 투자 유치"), **When** system classifies intensity, **Then** collaboration_intensity is "투자" (Investment) with confidence ≥0.95

4. **Given** sample-006.txt "플록스 × 스마트푸드네트워크" (contains "장바구니 개선 프로젝트"), **When** system classifies intensity, **Then** collaboration_intensity is "협력" (Cooperation/Pilot) with confidence ≥0.90

5. **Given** sample-004.txt "NXN Labs - SI GenAI 이미지생성 파일럿" (contains "파일럿 시작", "적용 가능성 탐색"), **When** system classifies, **Then** intensity is "협력" with confidence ≥0.85

---

### User Story 3 - Generate Collaboration Summary (Priority: P2)

When an email contains collaboration details (entities, activities, timeline, outcomes), the system generates a concise 3-5 sentence summary preserving all key information (who, what, when, why, how), enabling quick review in the Notion database without reading the full email.

**Why this priority**: Important for usability but not blocking - users can read full emails if summaries aren't available. Summaries significantly improve efficiency by providing at-a-glance insights. Delivers value by reducing time spent reviewing each collaboration entry from minutes to seconds.

**Independent Test**: Generate summary from test email "브레이크앤컴퍼니 x 신세계푸드 PoC 킥오프" and verify it includes: startup name (브레이크앤컴퍼니), partner (신세계푸드), activity (PoC 킥오프), date, and person in charge. Measure completeness by checking all 5 key entities are present (≥90% completeness). Can be tested independently without classification.

**Acceptance Scenarios**:

1. **Given** email "브레이크앤컴퍼니 x 신세계푸드 PoC 킥오프 (2025-11-15, 담당: Jeffrey Lim)", **When** system generates summary, **Then** summary is 3-5 sentences AND includes all 5 key entities (startup, partner, activity, date, person) AND word count is between 50-150 words

2. **Given** lengthy email (500+ words) with multiple topics, **When** system summarizes, **Then** summary focuses on primary collaboration topic AND preserves critical dates/milestones AND omits secondary details (email signatures, disclaimers)

3. **Given** email with Korean-English mixed content, **When** system summarizes, **Then** summary uses Korean for company names and maintains bilingual clarity where appropriate

4. **Given** email with sensitive information (financial terms, confidential data), **When** system summarizes, **Then** summary preserves business-critical details while maintaining appropriate confidentiality level

---

### User Story 4 - Return Confidence Scores for Manual Review (Priority: P2)

When the system classifies collaboration type or intensity with low confidence (<0.85), it returns confidence scores along with classifications, enabling automated routing to manual verification queue (Phase 3a) for ambiguous cases.

**Why this priority**: Important for data quality and preventing false classifications, but not blocking - system can still classify all collaborations without confidence scoring. Reduces manual review burden by auto-accepting high-confidence classifications (≥0.85) while flagging uncertain ones. Improves over time as patterns emerge.

**Independent Test**: Process test emails with clear classifications (confidence ≥0.90) and ambiguous ones (confidence <0.70) and verify confidence scores accurately reflect classification difficulty. High-confidence cases should match human classification ≥95% of time. Can be tested by comparing LLM confidence to human inter-rater agreement.

**Acceptance Scenarios**:

1. **Given** clear email "브레이크앤컴퍼니 x 신세계푸드 PoC 킥오프" (obvious "[A]PortCoXSSG" + 협력), **When** system classifies, **Then** type_confidence ≥0.90 AND intensity_confidence ≥0.90

2. **Given** ambiguous email "A사와 B사 간 논의" (companies not specified, activity vague), **When** system classifies, **Then** type_confidence <0.70 AND intensity_confidence <0.70

3. **Given** email with external partner "웨이크 × Google Cloud 협업" (Google not in database), **When** system classifies type as "[B]Non-PortCoXSSG", **Then** type_confidence is between 0.75-0.89 (lower than portfolio×SSG cases)

4. **Given** email with multiple activities "초기 미팅 후 PoC 검토 예정" (mixed 이해+협력), **When** system classifies intensity, **Then** intensity is primary activity (이해) with confidence between 0.70-0.85

---

### Edge Cases

- **Multiple collaboration types in one email**: How does system handle "브레이크앤컴퍼니 x 신세계푸드 PoC + 스위트스팟 x 신세계인터내셔널 미팅"? (Answer: Extract primary collaboration based on context prominence; secondary collaborations may be lost - acceptable for MVP, future enhancement to extract multiple)

- **Intensity progression**: How does system handle "초기 미팅 완료, PoC 진행 예정"? (Answer: Classify based on current status - if PoC active, use 협력; if only planning, use 이해; LLM determines from verb tense)

- **Unclassifiable collaborations**: What if email mentions collaboration but provides no details about type or intensity? (Answer: Return null classifications with confidence <0.50, route to manual review queue)

- **Classification disagreement**: What if type suggests "[A]PortCoXSSG" (Portfolio×SSG) but email explicitly states "외부 협력"? (Answer: LLM uses semantic understanding of email content over pattern matching; explicit user statements override inferred classifications)

- **Bilingual terminology mixing**: How does system handle "스타트업 investment 검토"? (Answer: LLM semantic understanding handles mixed Korean/English; "investment" → 투자 regardless of language)

- **Summary length violations**: What if critical details exceed 5 sentences? (Answer: Prioritize most important entities; acceptable to truncate secondary details; enforce 150-word hard limit)

- **Company name changes mid-email**: How does system handle "본봄(구 베이비빌리) x 신세계"? (Answer: Summary includes both names for clarity; classification uses current name from Phase 2b matching)

- **Confidential data in summaries**: How to prevent leaking sensitive financial terms? (Answer: LLM prompt instructs to preserve business context without specific numbers; "투자 검토 진행" vs "100억 투자 검토" - acceptable for MVP, future enhancement for PII redaction)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST classify collaboration type based on matched company classifications from Phase 2b (matched_company_id and matched_partner_id)

- **FR-002**: System MUST dynamically fetch collaboration type field values from Notion CollabIQ database "협업형태" property at runtime (not hardcoded) to support future changes to available types

- **FR-003**: System MUST extract available collaboration type options from Notion "협업형태" Select property and parse them to identify the four type categories (currently: "[A]PortCoXSSG", "[B]Non-PortCoXSSG", "[C]PortCoXPortCo", "[D]Other" but may change)

- **FR-004**: System MUST determine collaboration type using this logic and return exact Notion field values fetched from schema:
  - Type matching "[A]*" pattern if startup is Portfolio AND partner is SSG Affiliate
  - Type matching "[C]*" pattern if startup is Portfolio AND partner is Portfolio
  - Type matching "[B]*" pattern if startup is Portfolio AND partner is External (not in database or Other classification)
  - Type matching "[D]*" pattern if startup is not Portfolio

- **FR-005**: System MUST fail gracefully if "협업형태" property is missing or has unexpected structure, logging error and continuing with null collaboration_type

- **FR-006**: System MUST cache fetched "협업형태" field values for the duration of the extraction session (avoid repeated Notion API calls per email)

- **FR-007**: System MUST classify collaboration intensity into four levels: 이해 (Understanding/Exploration), 협력 (Cooperation/Pilot), 투자 (Investment), 인수 (Acquisition)

- **FR-008**: System MUST identify intensity based on semantic analysis of Korean business terminology and activity keywords:
  - 이해: 초기 미팅, 탐색, 논의, 가능성 검토
  - 협력: PoC, 파일럿, 테스트, 프로토타입, 협업 진행
  - 투자: 투자 검토, DD, 밸류에이션, 계약 검토
  - 인수: 인수 협상, M&A, 통합 논의, 최종 계약

- **FR-009**: System MUST generate summary of collaboration content in 3-5 sentences (50-150 words)

- **FR-010**: Summary MUST preserve these key entities: startup name, partner organization, activity/purpose, date, person in charge

- **FR-011**: Summary MUST omit non-essential content: email signatures, legal disclaimers, quoted previous emails, generic greetings

- **FR-012**: System MUST return confidence scores (0.0-1.0) for both type classification and intensity classification

- **FR-013**: System MUST use confidence threshold of 0.85 for auto-acceptance (≥0.85 = high confidence, <0.85 = manual review needed)

- **FR-014**: System MUST handle Korean-English bilingual content in classification and summarization

- **FR-015**: System MUST prioritize explicit user statements over inferred classifications when conflicts occur

- **FR-016**: System MUST extend GeminiAdapter.extract_entities() response schema to include: collaboration_type (exact Notion field value dynamically fetched), collaboration_intensity, collaboration_summary, type_confidence, intensity_confidence

- **FR-017**: System MUST maintain backward compatibility - Phase 1b entity extraction must continue to work if classification/summarization unavailable

- **FR-018**: System MUST log all classification decisions (type, intensity, confidence, reasoning) for debugging and accuracy monitoring

- **FR-019**: System MUST handle emails mentioning multiple collaborations by extracting the primary (most prominent) collaboration

### Key Entities

- **Collaboration Classification**: Represents the categorization result for a collaboration
  - Attributes: collaboration_type (exact Notion field value: "[A]PortCoXSSG"|"[B]Non-PortCoXSSG"|"[C]PortCoXPortCo"|"[D]Other"), collaboration_intensity (이해/협력/투자/인수), type_confidence (0.0-1.0), intensity_confidence (0.0-1.0), classification_reason (explanation for debugging)
  - Relationships: Derived from matched company classifications (Phase 2b output)

- **Collaboration Summary**: Structured summary of collaboration content
  - Attributes: summary_text (3-5 sentences), word_count (50-150), key_entities_preserved (boolean flags for startup/partner/activity/date/person), summary_language (Korean/English/Mixed)
  - Relationships: Generated from cleaned email content (Phase 1a output) and extracted entities (Phase 1b output)

- **Extended Extracted Entities**: Enhanced entity extraction result with classifications and summary
  - Extends existing ExtractedEntities model (from Phase 1b + Phase 2b)
  - New attributes: collaboration_type, collaboration_intensity, collaboration_summary, type_confidence, intensity_confidence

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System achieves ≥85% correct collaboration type classification on test dataset with known ground truth (20-30 emails covering all four types)

- **SC-002**: System achieves ≥85% correct collaboration intensity classification on test dataset with known ground truth (20-30 emails covering all four intensity levels)

- **SC-003**: Generated summaries preserve all five key entities (startup, partner, activity, date, person) in ≥90% of cases when entities are present in original email

- **SC-004**: Summary word count stays within 50-150 word range for ≥95% of emails

- **SC-005**: Confidence scores accurately predict classification correctness - classifications with confidence ≥0.90 have ≥95% accuracy, classifications with confidence 0.70-0.89 have ≥80% accuracy

- **SC-006**: System completes classification and summarization for single email in ≤4 seconds (including Phase 1b extraction + Phase 2b matching + Phase 2c classification)

- **SC-007**: Manual review queue (confidence <0.85) contains ≤25% of total classifications (down from 100% without automated classification)

## Assumptions *(mandatory)*

1. **Phase 2b complete**: Matched company IDs with classification metadata (Portfolio/SSG Affiliate/Other) are available from GeminiAdapter output

2. **Collaboration type deterministic**: Type classification follows strict logic rules based on company classifications (no LLM ambiguity, only manual review needed when matched IDs are null)

3. **Dynamic schema fetching**: System MUST fetch "협업형태" field values from Notion CollabIQ database at runtime using NotionIntegrator.discover_database_schema() to support future changes (e.g., field values changing from A/B/C/D to 1/2/3/4, or adding new types)

4. **Field value pattern matching**: Collaboration type field values follow "[X]*" pattern where X is the type identifier (currently A/B/C/D), allowing flexible matching even if full names change

5. **Intensity keyword coverage**: The four Korean keyword sets (이해/협력/투자/인수) cover ≥90% of collaboration activities in real emails; edge cases use semantic similarity

6. **Single primary collaboration**: Each email describes one primary collaboration; multiple collaborations are edge cases handled by extracting most prominent one

7. **Summary quality threshold**: 3-5 sentence summaries provide sufficient context for Notion database quick review; full email access available if needed

8. **Gemini API semantic understanding**: Gemini 2.0 Flash can classify Korean collaboration intensity with ≥85% accuracy without additional NLP libraries; fallback to keyword matching only if LLM accuracy insufficient

9. **Confidence calibration**: Fixed threshold of 0.85 balances automation (≥85% auto-accept) and data quality (<85% manual review); threshold may be adjusted based on production accuracy monitoring

10. **Bilingual handling**: System prioritizes Korean for company names and business terminology; English technical terms preserved as-is in summaries

11. **Summary length adequate**: 50-150 words (3-5 sentences) captures essential information for ≥90% of emails; longer emails may lose secondary details (acceptable for MVP)

12. **Privacy preservation**: Summaries do not require PII redaction for MVP; financial details and sensitive data preserved in business context without specific numbers (acceptable risk for internal use)

13. **Classification immutability**: Classifications are final once created; re-classification of historical entries not supported (manual correction via Notion UI if needed)

14. **Error handling**: If classification or summarization fails, system degrades gracefully - returns extracted entities without classifications/summary (preserves Phase 1b+2b functionality)

15. **Schema caching**: "협업형태" field values are cached for the session duration to avoid repeated API calls; cache invalidates on next system restart (acceptable delay for schema changes)

## Dependencies

- **Phase 2b (007-llm-matching)**: MUST be complete - requires matched_company_id and matched_partner_id with classification metadata (Portfolio/SSG Affiliate/Other)

- **Phase 2a (006-notion-read)**: MUST be complete - requires NotionIntegrator.discover_database_schema() to dynamically fetch "협업형태" field values from CollabIQ database at runtime

- **Phase 1b (004-gemini-extraction)**: MUST be complete - builds upon GeminiAdapter entity extraction with extended response schema

- **Phase 1a (002-email-reception)**: MUST be complete - requires cleaned email content for summarization

- **Notion CollabIQ Database**: MUST have "협업형태" Select property with values following "[X]*" pattern (e.g., "[A]PortCoXSSG") for type classification

- **Gemini API**: MUST support structured JSON output with flexible schema (already validated in Phase 1b + Phase 2b)

- **Korean language model**: Gemini 2.0 Flash MUST have strong Korean semantic understanding for intensity classification (validated in Phase 2b)

## Out of Scope

1. **Multi-collaboration extraction**: Handling emails describing 3+ distinct collaborations; MVP extracts only primary collaboration

2. **Historical re-classification**: Applying new classification logic to previously extracted emails; applies only to new extractions after Phase 2c deployment

3. **Custom classification rules**: User-defined classification logic or intensity levels; uses fixed [A]/[B]/[C]/[D] types and 이해/협력/투자/인수 levels

4. **PII redaction**: Automatic removal of personally identifiable information or financial details from summaries; acceptable for internal MVP use

5. **Summary formatting**: Markdown, bullet points, or structured formatting in summaries; plain text only for MVP

6. **Multi-language summaries**: Generating summaries in languages beyond Korean/English; bilingual handling limited to preserving mixed content

7. **Classification explanations**: Detailed reasoning for why specific type/intensity was chosen; confidence scores only (future enhancement: human-readable explanations)

8. **Summary quality scoring**: Measuring summary quality beyond entity completeness; no readability or coherence metrics for MVP

9. **Learning from corrections**: Using manual classification corrections (Phase 3b) to improve future classifications; static classification logic for MVP

10. **Classification versioning**: Tracking changes to classification logic or re-running classifications with updated rules; classifications are immutable once created

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Gemini API accuracy <85% for intensity classification | High - core success criteria failure | Medium | Monitor accuracy on test dataset; implement fallback keyword-based classification using predefined Korean keyword lists; adjust confidence threshold if needed |
| Summary length inconsistency (too short or too long) | Medium - usability impact | Medium | Enforce strict 50-150 word limit in LLM prompt; truncate at 150 words if exceeded; validate summary completeness (5 key entities) before acceptance |
| Confidence score calibration inaccurate | High - incorrect auto-acceptance/rejection | Medium | Validate confidence scores against 30-email test dataset; adjust threshold (0.85) if precision drops below 80%; implement confidence monitoring in production |
| Type classification logic errors (edge cases) | Medium - incorrect categorization | Low | Logic is deterministic based on Phase 2b company classifications; errors only occur if Phase 2b matching incorrect; validation tests catch logic bugs early |
| Bilingual terminology confusion | Low - minor classification errors | Low | Gemini 2.0 Flash handles Korean-English mixing well (validated in Phase 2b); monitor edge cases in production; acceptable <5% error rate for bilingual content |
| Multiple collaborations causing extraction failures | Low - edge case impact | Low | Extract most prominent collaboration using contextual salience; acceptable to lose secondary collaborations for MVP; future enhancement for multi-extraction |

## Related Features

- **Phase 2b (007-llm-matching)**: Provides matched company IDs with classifications (Portfolio/SSG Affiliate) needed for type determination
- **Phase 1b (004-gemini-extraction)**: Provides entity extraction foundation that this phase extends with classifications and summaries
- **Phase 2d (009-notion-write)**: Will use collaboration_type and collaboration_intensity fields to populate Notion database entries
- **Phase 3a (011-queue-storage)**: Will store low-confidence classifications (<0.85) for manual review using confidence scores from this phase
- **Phase 4a (013-basic-reporting)**: Will use collaboration type and intensity for filtering and grouping in reports

## Future Enhancements (Post-MVP)

1. **Multi-collaboration extraction**: Handle emails mentioning 3+ distinct collaborations by extracting multiple classifications and summaries

2. **Classification explanations**: Provide human-readable reasoning for each classification decision (e.g., "Classified as [A] because startup is Portfolio (브레이크앤컴퍼니) and partner is SSG Affiliate (신세계푸드)")

3. **Custom intensity levels**: Allow admins to define custom intensity categories beyond the default four (e.g., "전략적 제휴", "독점 계약")

4. **Summary quality scoring**: Measure summary readability, coherence, and informativeness using automated metrics (ROUGE, BERTScore)

5. **Learning from corrections**: Use manual classification corrections (Phase 3b) to fine-tune LLM prompts or adjust keyword lists

6. **Classification versioning**: Track changes to classification logic over time and allow re-running historical classifications with updated rules

7. **PII redaction**: Automatically detect and redact sensitive information (financial terms, personal data) from summaries while preserving business context

8. **Multi-language support**: Generate summaries in user-preferred language (Korean, English, Japanese) regardless of email language

9. **Structured summary format**: Use markdown, bullet points, or JSON for machine-readable summaries

10. **Confidence threshold tuning**: Dynamically adjust confidence threshold (0.85) based on production accuracy and manual review capacity

## Technical Debt

None identified - Phase 2c is a straightforward extension of Phase 2b's LLM-based extraction pattern. Classification logic is deterministic (type) or keyword-based (intensity), minimizing technical complexity. Future enhancements listed above are optional improvements, not deferred critical features.

---

**Specification Complete**
**Next Step**: Run `/speckit.plan` to create implementation plan.
