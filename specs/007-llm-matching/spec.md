# Feature Specification: LLM-Based Company Matching

**Feature Branch**: `007-llm-matching`
**Created**: 2025-11-02
**Status**: Draft
**Input**: User description: "LLM-Based Company Matching - Phase 2b: Update GeminiAdapter to include company lists in prompt context, implement intelligent company matching with confidence scores, handle no-match scenarios"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Match Primary Startup Company (Priority: P1)

When an email mentions a portfolio startup by its exact name (e.g., "브레이크앤컴퍼니"), the system identifies it as the primary company, matches it to the corresponding entry in the Notion Companies database, and returns the company's unique identifier with high confidence.

**Why this priority**: Core functionality - every collaboration email mentions at least one portfolio startup. Without this, the feature cannot function. This is the minimum viable product that delivers immediate value by identifying which portfolio company is involved.

**Independent Test**: Use existing test email sample-001.txt containing "브레이크앤컴퍼니" and verify the system returns the correct Notion Companies database entry ID with confidence ≥0.90. No other user stories need to be implemented for this to work.

**Acceptance Scenarios**:

1. **Given** sample-001.txt "브레이크앤컴퍼니 x 신세계 PoC 킥오프" and Companies database contains entry {id: "abc123", name: "브레이크앤컴퍼니", classification: "Portfolio"}, **When** GeminiAdapter extracts entities, **Then** startup_name is "브레이크앤컴퍼니" AND matched_company_id is "abc123" AND startup_confidence is ≥0.90

2. **Given** korean_001.txt "본봄 파일럿 킥오프 미팅" and Companies database contains entry {id: "def456", name: "본봄", classification: "Portfolio"}, **When** GeminiAdapter extracts entities, **Then** startup_name is "본봄" AND matched_company_id is "def456" AND startup_confidence is ≥0.90

3. **Given** sample-002.txt "웨이크 x 신세계인터내셔널" and Companies database contains entry {id: "ghi789", name: "웨이크", classification: "Portfolio"}, **When** GeminiAdapter extracts entities, **Then** startup_name is "웨이크" AND matched_company_id is "ghi789" AND startup_confidence is ≥0.90

---

### User Story 2 - Match Beneficiary Company (SSG Affiliate or Portfolio) (Priority: P1)

When an email mentions a beneficiary company (either an SSG affiliate like "신세계푸드" or another portfolio company like "스마트푸드네트웍스"), the system identifies it from the Companies database and returns the company's unique identifier with high confidence, distinguishing whether it's an SSG affiliate or portfolio-to-portfolio collaboration.

**Why this priority**: Equally critical as US1 - identifying the beneficiary company is essential for collaboration tracking. Both the primary startup and beneficiary company must be matched for the feature to be useful. This determines collaboration type ([A] Portfolio×SSG vs [C] Portfolio×Portfolio).

**Independent Test**: Use existing test email sample-004.txt containing "NXN Labs × 신세계인터내셔널" and verify the system returns the correct Companies database entry ID with confidence ≥0.90 and classification "SSG Affiliate". Can be tested independently of fuzzy matching or no-match scenarios.

**Acceptance Scenarios**:

1. **Given** sample-004.txt "NXN Labs - SI GenAI 이미지생성 파일럿" and Companies database contains {id: "ghi789", name: "신세계인터내셔널", english_name: "Shinsegae International", classification: "SSG Affiliate"}, **When** GeminiAdapter extracts entities, **Then** startup_name is "NXN Labs" AND partner_org is "신세계인터내셔널" (or "Shinsegae International") AND matched_partner_id is "ghi789" AND partner_confidence is ≥0.90 AND partner_classification is "SSG Affiliate"

2. **Given** sample-006.txt "플록스 × 스마트푸드네트워크 장바구니 리텐션 개선" and Companies database contains {id: "pqr678", name: "플록스", english_name: "Phlox", classification: "Portfolio"} and {id: "mno345", name: "스마트푸드네트워크", classification: "Portfolio"}, **When** GeminiAdapter extracts entities, **Then** identifies "플록스" as startup_name AND "스마트푸드네트워크" as partner_org AND both matched IDs returned AND both partner_classification is "Portfolio" (enabling [C] Portfolio×Portfolio classification)

3. **Given** english_002.txt "kickoff with Shinsegae International for BonBom" and Companies database contains {id: "jkl012", name: "신세계인터내셔널", english_name: "Shinsegae International", classification: "SSG Affiliate"}, **When** GeminiAdapter extracts entities, **Then** partner_org is "Shinsegae International" AND matched_partner_id is "jkl012" AND partner_confidence is ≥0.90

---

### User Story 3 - Handle Company Name Variations (Priority: P2)

When an email mentions a company using an abbreviation, nickname, or alternate spelling (e.g., "SSG푸드" for "신세계푸드", "Shinsegae Food" for "신세계푸드"), the system uses semantic understanding to match it to the correct database entry with moderate confidence.

**Why this priority**: Important for real-world usage but not blocking - emails often use informal names. Can be implemented after exact matching works (P1). Delivers value by reducing manual review queue size.

**Independent Test**: Create test email with "SSG푸드와 협업" and verify it matches "신세계푸드" with confidence between 0.75-0.89. This tests fuzzy matching independently without requiring exact match or no-match logic.

**Acceptance Scenarios**:

1. **Given** test email "SSG푸드와 협업 진행" and Companies database contains {name: "신세계푸드"}, **When** GeminiAdapter extracts entities, **Then** matched_partner_id is correct AND partner_confidence is between 0.75-0.89 (abbreviation match)

2. **Given** english_001.txt "pilot with Shinsegae Food" and Companies database contains {name: "신세계푸드", english_name: "Shinsegae Food"}, **When** GeminiAdapter extracts entities, **Then** matched_partner_id is correct AND partner_confidence is ≥0.85 (english_name exact match)

3. **Given** test email with typo "브레이크언컴퍼니" (typo: 언 instead of 앤) and Companies database contains "브레이크앤컴퍼니", **When** GeminiAdapter extracts entities, **Then** matched_company_id is correct AND startup_confidence is between 0.70-0.85 (typo tolerance)

4. **Given** test email with "스위트스팟 골프" (adding context word) and Companies database contains "스위트스팟", **When** GeminiAdapter extracts entities, **Then** matched_company_id is correct AND startup_confidence is between 0.80-0.89 (handles extra context)

---

### User Story 4 - Handle No-Match Scenarios (Priority: P2)

When an email mentions a company that does not exist in the Notion Companies database, the system returns null for the company ID and low confidence score, signaling that manual review is needed.

**Why this priority**: Important for handling new companies and preventing false positives, but not blocking - the system can still extract and process known companies without this. Reduces false positives and improves data quality.

**Independent Test**: Send an email mentioning "신생스타트업" (not in database) and verify the system returns null matched_company_id with confidence <0.70. Can be tested independently after exact matching works.

**Acceptance Scenarios**:

1. **Given** an email text "신생스타트업과 초기 미팅" and Companies database does NOT contain "신생스타트업", **When** GeminiAdapter extracts entities, **Then** startup_name is "신생스타트업" AND matched_company_id is null AND startup_confidence is <0.70

2. **Given** an email text "NewCo Inc. reached out for partnership" and Companies database does NOT contain "NewCo Inc.", **When** GeminiAdapter extracts entities, **Then** startup_name is "NewCo Inc." AND matched_company_id is null AND startup_confidence is <0.70

3. **Given** an email with ambiguous company name "ABC" (matches multiple entries partially), **When** GeminiAdapter extracts entities, **Then** matched_company_id is null AND startup_confidence is <0.70 (ambiguity = low confidence)

4. **Given** an email with generic organization "한국정부" (not a specific company), **When** GeminiAdapter extracts entities, **Then** partner_org is "한국정부" AND matched_partner_id is null AND partner_confidence is <0.70

---

### User Story 5 - Provide LLM-Ready Company Context (Priority: P3)

The system formats Notion company data (fetched in Phase 2a) into a concise, structured format optimized for LLM prompt injection, including company names from the existing test dataset (브레이크앤컴퍼니, 웨이크, 스위트스팟, 블룸에이아이, 파지티브호텔, 스마트푸드네트웍스) and SSG affiliates (신세계, 신세계인터내셔널, 신세계푸드, 신세계라이브쇼핑).

**Why this priority**: Nice-to-have optimization - improves matching accuracy but Phase 2a already provides basic formatting. Can be enhanced after core matching works. Delivers value by improving semantic understanding.

**Independent Test**: Call formatting method with test dataset companies (6 startups + 4 SSG affiliates) and verify output contains company names in both Korean and English (where available), organized by classification, within 2000 tokens. Can be tested independently without entity extraction.

**Acceptance Scenarios**:

1. **Given** test dataset companies (6 portfolio + 4 SSG affiliates), **When** system prepares LLM context, **Then** formatted output is ≤500 tokens AND includes all 10 company names AND groups by classification (Portfolio vs SSG Affiliate)

2. **Given** company entry {name: "브레이크앤컴퍼니", description: "AI 재고 최적화"}, **When** system prepares LLM context, **Then** formatted output includes "브레이크앤컴퍼니 - Portfolio Company (AI 재고 최적화)"

3. **Given** company entry {name: "신세계푸드", english_name: "Shinsegae Food"}, **When** system prepares LLM context, **Then** formatted output includes "신세계푸드 (Shinsegae Food) - SSG Affiliate"

---

### Edge Cases

- **Multiple similar names**: How does system handle "신세계", "신세계인터내셔널", "신세계푸드" all present in same email? (Answer: Extract primary company based on context proximity to action verbs; others may appear in details field)

- **Company name changes**: How does system handle companies that changed names (e.g., old name in email but new name in database)? (Answer: Relies on Notion database maintaining aliases/old names in description or tags; otherwise returns null + low confidence for manual review)

- **Bilingual mixing**: How does system handle "Shinsegae푸드" (English+Korean mixed)? (Answer: LLM semantic understanding should handle; confidence may be slightly lower than pure Korean/English)

- **Company mentioned but not relevant**: How does system handle "신세계백화점에서 쇼핑" (casual mention, not business collaboration)? (Answer: Relies on context - if no collaboration action verbs present, may extract as partner_org but with lower confidence)

- **Partial matches**: How does system handle "Shinsegae" matching both "Shinsegae Food" and "Shinsegae International"? (Answer: Returns null + low confidence <0.70 due to ambiguity; requires manual review)

- **Token limit exceeded**: What happens if company list exceeds LLM context window? (Answer: Prioritize portfolio companies + SSG affiliates; truncate inactive/archived companies; include truncation warning in logs)

- **Notion API returns no companies**: What if Phase 2a fetching fails? (Answer: Fallback to extraction without matching - return null matched IDs + confidence <0.50; system should still extract names)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch company lists from Notion Companies database using NotionIntegrator (from Phase 2a) before entity extraction

- **FR-002**: System MUST include formatted company lists (Korean names, English names, classifications) in Gemini API prompt context

- **FR-003**: System MUST match extracted startup_name against portfolio companies in database and return matched company ID

- **FR-004**: System MUST match extracted partner_org against SSG affiliate companies in database and return matched partner ID

- **FR-005**: System MUST return null for matched_company_id when no suitable match found (confidence <0.70)

- **FR-006**: System MUST return confidence score (0.0-1.0) for each matched company ID reflecting match quality

- **FR-007**: System MUST handle exact name matches (Korean and English) with confidence ≥0.90

- **FR-008**: System MUST handle fuzzy matches (abbreviations, typos, alternate spellings) with confidence between 0.70-0.89

- **FR-009**: System MUST handle case-insensitive matching for English company names

- **FR-010**: System MUST preserve original extracted company names (startup_name, partner_org) even when no match found

- **FR-011**: System MUST format company context to fit within 2000 tokens for LLM prompt injection

- **FR-012**: System MUST prioritize portfolio companies and SSG affiliates over archived/inactive companies when formatting context

- **FR-013**: System MUST include both Korean name and english_name (if available) for each company in LLM context

- **FR-014**: System MUST log all company matching decisions (matched ID, confidence, reason) for debugging

- **FR-015**: System MUST handle semantic matching (e.g., "Shinsegae Food" → "신세계푸드") using LLM understanding

- **FR-016**: System MUST return null matched ID (not error) when multiple ambiguous matches found (confidence <0.70)

- **FR-017**: System MUST update GeminiAdapter.extract_entities() response schema to include matched_company_id and matched_partner_id fields

- **FR-018**: System MUST maintain backward compatibility - existing entity extraction must continue to work if company list unavailable

### Key Entities *(include if feature involves data)*

- **Company Match Result**: Represents the outcome of matching an extracted company name to the database
  - Attributes: matched_company_id (Notion page ID or null), original_name (extracted text), confidence_score (0.0-1.0), match_reason (exact/fuzzy/semantic/no-match)
  - Relationships: Links to Notion Companies database entry via page ID

- **Company Context**: Formatted company data for LLM prompt injection
  - Attributes: company_list_text (formatted string), total_companies (count), token_count (for prompt budget), last_updated (cache timestamp)
  - Relationships: Derived from NotionIntegrator company records (Phase 2a)

- **Extended Extracted Entities**: Enhanced entity extraction result with matched IDs
  - Extends existing ExtractedEntities model (from Phase 1b)
  - New attributes: matched_company_id (Notion page ID), matched_partner_id (Notion page ID), startup_match_confidence (0.0-1.0), partner_match_confidence (0.0-1.0)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System achieves ≥85% correct company matches on existing test dataset (6 sample emails + 4 korean/english test emails from ground truth) with known company mappings

- **SC-002**: Confidence scores accurately reflect match quality - matches with confidence ≥0.90 have ≥95% precision, matches with confidence 0.70-0.89 have ≥80% precision

- **SC-003**: System completes company matching for single email in ≤3 seconds (including Notion company list fetch with caching)

- **SC-004**: System correctly returns null matched_company_id for ≥90% of companies not present in database (no false positives)

- **SC-005**: Fuzzy matching handles ≥80% of common variations (abbreviations like "SSG푸드" → "신세계푸드", English-Korean like "Shinsegae Food" → "신세계푸드")

- **SC-006**: Token budget for company context stays within 2000 tokens for databases with ≤200 companies

- **SC-007**: Manual review queue (confidence <0.85) contains ≤20% of total extractions after company matching enabled (down from 100% without matching)

## Assumptions *(mandatory)*

1. **Phase 2a complete**: NotionIntegrator module is fully functional and can fetch company lists with schema {id, name, english_name, classification}

2. **Notion database structure**: Companies database includes fields: Name (title), English Name (text), Classification (select: Portfolio/SSG Affiliate/Other), Status (select: Active/Inactive/Archived)

3. **Company list size**: Total companies in database will not exceed 500 entries for MVP; pagination and caching from Phase 2a handle larger datasets

4. **Gemini API context window**: Gemini 2.0 Flash supports ≥32K tokens; company list context (≤2000 tokens) + email text (≤1000 tokens) + prompt template (≤1000 tokens) = 4000 tokens total well within limit

5. **Existing infrastructure**: GeminiAdapter from Phase 1b supports prompt customization and structured JSON output schema extension

6. **No multi-LLM orchestration**: Single Gemini API call performs both extraction and matching (no separate matching LLM); future phase may split if accuracy insufficient

7. **LLM semantic understanding**: Gemini 2.0 Flash can perform semantic matching (abbreviations, typos, Korean-English) without additional NLP libraries like RapidFuzz; fallback to rule-based matching only if LLM accuracy <85%

8. **Cache validity**: Company list cached for 6 hours (from Phase 2a) is acceptable freshness; new companies added to Notion will appear in matching after cache refresh

9. **Confidence threshold**: Fixed threshold of 0.85 for auto-acceptance (confidence ≥0.85 = auto-create Notion entry); values <0.85 go to verification queue (Phase 3a)

10. **Primary company focus**: Emails mention one primary startup and one primary partner; multiple company mentions are rare edge cases handled by extracting most contextually relevant

11. **No duplicate detection**: Duplicate company entries in Notion database (e.g., two "본봄" entries) are database quality issues resolved outside this feature; matching returns first found

12. **Error handling**: If Notion API fails (Phase 2a), system degrades gracefully - extracts company names without matching (matched_id = null, confidence <0.50)

## Dependencies

- **Phase 2a (006-notion-read)**: MUST be complete - requires NotionIntegrator to fetch company lists with schema discovery and caching

- **Phase 1b (004-gemini-extraction)**: MUST be complete - builds upon GeminiAdapter entity extraction with extended response schema

- **Notion Companies Database**: MUST exist with fields: Name, English Name (optional), Classification, Status

- **Gemini API**: MUST support structured JSON output with flexible schema (already validated in Phase 1b)

- **Infisical or .env**: MUST provide NOTION_API_KEY and NOTION_DATABASE_ID_COMPANIES (configured in Phase 2a)

## Out of Scope

1. **Creating new Notion entries**: Automatic Notion database writes are Phase 2d; this phase only returns matched IDs

2. **Auto-creating missing companies**: When no match is found, system returns null (no-match) rather than automatically creating a new Companies database entry. This is deferred to future phase (see Technical Debt below).

3. **Classification and summarization**: Collaboration type (A/B/C/D) and intensity (이해/협력/투자/인수) are Phase 2c; this phase focuses on company matching only

3. **Verification queue UI**: Manual review interface for low-confidence matches is Phase 3b; this phase returns confidence scores for future queueing

4. **Multi-company matching**: Handling emails with 3+ companies (e.g., three-way partnerships) is out of scope; extracts primary startup + primary partner only

5. **Company alias management**: Maintaining alternate names/nicknames in Notion database is manual admin task, not automated by this feature

6. **Historical matching**: Re-matching previously extracted emails after database updates is out of scope; applies only to new extractions

7. **Custom matching rules**: User-defined matching logic (e.g., "always match '벤처캐피탈' to specific ID") is out of scope; relies on LLM semantic understanding only

8. **Performance optimization**: Batch processing multiple emails, parallel API calls, advanced caching strategies are future optimizations; MVP processes one email at a time

9. **Multi-language support beyond Korean/English**: Japanese, Chinese, or other languages are out of scope for MVP

10. **Company disambiguation UI**: Interactive prompts asking users to choose between ambiguous matches are Phase 3b; MVP returns null + low confidence for ambiguous cases

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Gemini API accuracy <85% for fuzzy matches** | High - core success criteria failure | Medium | Monitor accuracy on test dataset; if <85%, implement fallback rule-based matching with RapidFuzz library for Korean text similarity |
| **Notion company list too large (>500 companies)** | Medium - LLM context overflow | Low | Prioritize active companies; implement pagination or chunking; truncate inactive/archived entries beyond token budget |
| **Company name ambiguity (multiple "ABC Company" entries)** | Medium - false positive matches | Medium | Return null + low confidence when multiple strong matches found; log ambiguity for manual database cleanup |
| **Confidence score calibration inaccurate** | High - incorrect auto-acceptance decisions | Medium | Validate confidence scores against 30-email test dataset; adjust threshold (0.85) if precision drops below 80% |
| **Phase 2a fetching fails during extraction** | Medium - extraction continues but without matching | Low | Implement graceful degradation - extract names, return null IDs, log warning; system remains operational |
| **Token budget exceeded with large companies** | Low - prompt truncation | Low | Monitor token count; truncate company list at 2000 tokens; prioritize portfolio companies over archived |

## Related Features

- **Phase 2a (006-notion-read)**: Provides company data fetching and LLM-ready formatting foundation
- **Phase 1b (004-gemini-extraction)**: Provides entity extraction foundation that this phase extends
- **Phase 2c (008-classification-summarization)**: Will build on matched company IDs to determine collaboration type ([A]/[B]/[C]/[D])
- **Phase 2d (009-notion-write)**: Will use matched company IDs to create relation links in Notion entries
- **Phase 3a (011-queue-storage)**: Will store low-confidence matches (<0.85) for manual review using confidence scores from this phase

## Future Enhancements (Post-MVP)

1. **Multi-company extraction**: Handle emails mentioning 3+ companies (e.g., "A, B, C 협업") by extracting multiple startup IDs or partner IDs

2. **Company relationship mapping**: Detect parent-subsidiary relationships (e.g., "Shinsegae Group" includes "Shinsegae Food") and map to database hierarchy

3. **Temporal company tracking**: Handle company name changes over time by checking extraction date against database change history

4. **Learning from corrections**: Use manual review corrections (Phase 3b) to fine-tune matching prompts or thresholds

5. **Multi-LLM consensus**: Use multiple LLMs (Gemini + GPT + Claude) for ambiguous matches and combine confidence scores

6. **Custom matching dictionaries**: Allow admins to define custom abbreviations (e.g., "SSG" always maps to "신세계") via configuration

7. **Match explanation**: Provide human-readable reason for each match decision (e.g., "Matched via exact Korean name" vs "Matched via English semantic similarity")

8. **Performance monitoring dashboard**: Track matching accuracy, confidence distribution, no-match rate over time

9. **Active learning pipeline**: Automatically flag low-confidence matches for human review and use corrections to retrain prompt examples

10. **Cross-lingual matching**: Handle Japanese/Chinese company names for international collaborations

## Technical Debt

**TD-001: Auto-create missing companies with notification**

**Description**: When company matching returns null (no match found in Companies database), the system should automatically create a new Companies database entry and notify the person in charge (identified by @signite.co email domain from the email thread).

**Current Behavior**: System returns `matched_company_id = null` and `confidence < 0.70` for no-match scenarios (US4). This requires manual intervention to create the company entry in Notion.

**Desired Behavior**:
1. When `matched_company_id = null` and extracted company name has reasonable confidence (e.g., ≥0.70)
2. Automatically create new entry in Companies database with:
   - Name: extracted startup_name or partner_org
   - Classification: "Pending Review" (to be classified later)
   - Created By: System (auto-generated)
   - Status: "Active"
3. Send notification email to person in charge (identified by @signite.co domain from email participants)
   - **Do NOT notify external parties** (non-@signite.co emails)
   - Include: company name, email source, link to Notion entry
4. Return newly created company ID as `matched_company_id` with flag `auto_created = true`

**Why deferred**:
- Requires Notion write operations (Phase 2d: 009-notion-write)
- Requires email notification system (not yet implemented)
- Adds complexity to Phase 2b which should focus on read-only matching
- Need to define approval workflow for auto-created entries

**Target Phase**: Phase 2d-ext or Phase 3 (after Notion write operations are stable)

**Related Requirements**:
- FR-005: Currently returns null for no-match → will return auto-created ID
- US4: No-match scenarios → will become auto-create scenarios
- Dependencies: Phase 2d (Notion write), Email notification service

**Estimated Effort**: 2-3 days
- Notion write operations: 1 day
- Email notification logic: 1 day
- Testing and validation: 0.5 day

---

**Specification Complete**
**Next Step**: Run `/speckit.clarify` if clarifications needed, or `/speckit.plan` to create implementation plan.
