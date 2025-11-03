# Research & Technical Decisions: LLM-Based Company Matching

**Feature**: Phase 2b - LLM-Based Company Matching
**Branch**: `007-llm-matching`
**Date**: 2025-11-02

## Overview

This document captures research findings and technical decisions made during Phase 0 planning for LLM-based company matching. The feature extends existing Phase 1b (GeminiAdapter) and Phase 2a (NotionIntegrator) infrastructure with minimal new complexity.

---

## Research Questions & Decisions

### RQ-001: How to inject company context into LLM prompts without exceeding token limits?

**Decision**: Use structured markdown format with ≤2000 tokens for full company list

**Rationale**:
- Gemini 2.0 Flash supports ≥32K tokens total context window
- Budget breakdown: 2000 tokens (company list) + 1000 tokens (email) + 1000 tokens (prompt template) = 4000 tokens total (well within limit)
- Phase 2a `format_for_llm()` already provides markdown formatting
- Markdown is human-readable and LLM-friendly (better than JSON for semantic tasks)

**Format example**:
```markdown
## Portfolio Companies
- 브레이크앤컴퍼니 (ID: abc123) - AI 재고 최적화
- 웨이크 (Wake, ID: def456) - Z세대 뷰티 플랫폼

## SSG Affiliates
- 신세계푸드 (Shinsegae Food, ID: ghi789) - 식자재 유통
```

**Alternatives considered**:
- JSON format → Rejected: Less semantic, harder for LLM to parse contextually
- Vector embeddings + RAG → Rejected: Overkill for ≤500 companies, adds complexity
- Chunking with multiple API calls → Rejected: Slower, requires orchestration logic

---

###RQ-002: Should we use RapidFuzz for fuzzy matching or rely purely on LLM semantic understanding?

**Decision**: Start with pure LLM semantic matching; add RapidFuzz fallback ONLY if accuracy <85%

**Rationale**:
- Gemini 2.0 Flash has strong multilingual semantic understanding (Korean-English)
- LLM can handle:
  - Abbreviations ("SSG푸드" → "신세계푸드")
  - Typos ("브레이크언컴퍼니" → "브레이크앤컴퍼니")
  - Cross-lingual matches ("Shinsegae Food" → "신세계푸드")
  - Context-aware disambiguation (multiple "신세계" variants)
- RapidFuzz requires custom Korean text normalization (Jamo decomposition, spacing rules)
- Simplicity principle (Constitution V): Try simpler solution first

**Fallback strategy** (if SC-001 fails):
```python
# Only add if LLM accuracy <85%
from rapidfuzz import fuzz, process

def fuzzy_match_fallback(extracted_name: str, companies: List[Dict]) -> Optional[Match]:
    # Normalize Korean text (remove spaces, Jamo normalization)
    normalized_name = normalize_korean(extracted_name)
    candidates = [normalize_korean(c["name"]) for c in companies]

    match, score, idx = process.extractOne(normalized_name, candidates, scorer=fuzz.ratio)
    if score >= 70:  # Threshold TBD
        return Match(id=companies[idx]["id"], confidence=score/100.0)
    return None
```

**Monitoring**: Track accuracy on 10-email test dataset; implement fallback if <85%

---

### RQ-003: How to extend ExtractedEntities model without breaking Phase 1b backward compatibility?

**Decision**: Add optional fields with `None` defaults to ExtractedEntities Pydantic model

**Rationale**:
- Pydantic supports backward-compatible schema extension via `Optional[T] = None`
- Phase 1b extractions without matching continue to work (fields auto-fill with None)
- Phase 2b extractions populate new fields when matching enabled

**Implementation**:
```python
# src/llm_provider/types.py
class ExtractedEntities(BaseModel):
    # Existing fields (Phase 1b) - unchanged
    person_in_charge: Optional[str] = None
    startup_name: Optional[str] = None
    partner_org: Optional[str] = None
    details: Optional[str] = None
    date: Optional[str] = None

    # New fields (Phase 2b) - optional, backward compatible
    matched_company_id: Optional[str] = None  # Notion page ID for startup
    matched_partner_id: Optional[str] = None  # Notion page ID for partner
    startup_match_confidence: Optional[float] = None  # 0.0-1.0
    partner_match_confidence: Optional[float] = None  # 0.0-1.0
```

**JSON output compatibility**:
```json
// Phase 1b output (still valid)
{
  "person_in_charge": "김철수",
  "startup_name": "본봄",
  "partner_org": "신세계",
  "details": "파일럿 킥오프",
  "date": "2025-11-01"
}

// Phase 2b output (extended)
{
  "person_in_charge": "김철수",
  "startup_name": "본봄",
  "partner_org": "신세계",
  "details": "파일럿 킥오프",
  "date": "2025-11-01",
  "matched_company_id": "abc123",
  "matched_partner_id": "def456",
  "startup_match_confidence": 0.95,
  "partner_match_confidence": 0.92
}
```

**Alternatives considered**:
- Separate MatchedEntities model → Rejected: Requires Phase 2c/2d to handle two schemas
- Nested matching object → Rejected: More complex, harder to query in Phase 2d

---

### RQ-004: How to calibrate confidence scores (0.0-1.0) for auto-acceptance threshold (0.85)?

**Decision**: Use Gemini's internal confidence + prompt-guided scoring; validate against ground truth

**Rationale**:
- Gemini 2.0 Flash can output confidence scores in structured JSON schema
- Prompt includes explicit confidence guidance:
  - ≥0.90: Exact match (Korean/English name match)
  - 0.70-0.89: Semantic match (abbreviation, typo, or context-based)
  - <0.70: Weak/ambiguous match or no match (return null)
- Threshold of 0.85 balances precision (SC-002: ≥95% precision @ ≥0.90) and recall

**Prompt guidance example**:
```text
CONFIDENCE SCORING RULES:
- 0.95-1.00: Exact character-for-character match of company name
- 0.90-0.94: Exact match after normalization (spacing, capitalization)
- 0.80-0.89: Clear semantic match (abbreviation, English/Korean equivalent)
- 0.70-0.79: Fuzzy match (typo, partial name, or contextual inference)
- 0.00-0.69: No confident match or ambiguous (multiple candidates)

If confidence <0.70, return null for matched_company_id.
```

**Validation approach**:
1. Run extraction on 10-email test dataset
2. Compare matched IDs to ground truth
3. Measure precision at different confidence thresholds:
   - P(correct | confidence ≥0.90) should be ≥95% (SC-002)
   - P(correct | confidence ≥0.85) should be ≥90%
   - P(correct | confidence ≥0.70) should be ≥80%
4. Adjust threshold if precision <80% at 0.85

**Monitoring**: Log all confidence scores + match outcomes for post-hoc calibration analysis

---

### RQ-005: Should company matching be a separate service or extend GeminiAdapter?

**Decision**: Extend GeminiAdapter with single API call for extraction + matching

**Rationale**:
- **Performance**: Single API call vs two sequential calls (2-3s vs 4-6s)
- **Consistency**: Extraction and matching use same email context (no context loss)
- **Simplicity**: No orchestration layer, no inter-service communication
- **Cost**: One Gemini API call vs two (50% cost reduction)
- **Atomic operation**: Extraction + matching succeed/fail together

**Extended method signature**:
```python
class GeminiAdapter(LLMProvider):
    def extract_entities(
        self,
        email_text: str,
        company_context: Optional[str] = None  # NEW: Formatted company list from Phase 2a
    ) -> ExtractedEntities:
        """Extract entities with optional company matching.

        Args:
            email_text: Cleaned email body
            company_context: Optional markdown-formatted company list
                           (from NotionIntegrator.format_for_llm())

        Returns:
            ExtractedEntities with matched_company_id/matched_partner_id
            populated if company_context provided, else None
        """
```

**Alternatives considered**:
- Separate `CompanyMatcher` service → Rejected: Extra API call, orchestration complexity
- Multi-LLM consensus (Gemini + GPT + Claude) → Rejected: Overkill for MVP, 3x cost
- Rule-based preprocessing + LLM fallback → Rejected: Harder to maintain two systems

---

## Technical Dependencies

### Existing Infrastructure (Reuse)

**Phase 1b - GeminiAdapter**:
- ✅ `google-generativeai` SDK already integrated
- ✅ Prompt template loading from `src/llm_adapters/prompts/`
- ✅ Retry logic with exponential backoff
- ✅ Structured JSON output with Pydantic validation
- **Action**: Extend `extract_entities()` method, update prompt template

**Phase 2a - NotionIntegrator**:
- ✅ `NotionIntegrator.get_data()` fetches Companies database
- ✅ `format_for_llm()` formats company data as markdown
- ✅ File-based JSON cache (6h data TTL, 24h schema TTL)
- **Action**: Call existing methods, no modifications needed

**Configuration**:
- ✅ `src/config/settings.py` manages Gemini + Notion API keys
- ✅ Infisical integration for secret management
- **Action**: No new configuration required

### New Dependencies

**None** - All required dependencies already in project:
- `google-generativeai` (Gemini API)
- `notion-client` (Notion API)
- `pydantic` (data validation)
- `tenacity` (retry logic)

**Optional (if fallback needed)**:
- `rapidfuzz` - Only add if LLM accuracy <85% (SC-001 failure)

---

## Performance Considerations

### Latency Budget

**Target**: ≤3 seconds per email (SC-003)

**Breakdown**:
1. Notion company fetch: ~200ms (cached, Phase 2a)
2. LLM context formatting: ~50ms (markdown generation)
3. Gemini API call: ~1500ms (extraction + matching in single call)
4. Response parsing: ~50ms (Pydantic validation)
5. JSON file write: ~100ms (to `data/extractions/`)
6. **Total**: ~1900ms (well below 3s target)

**Optimization opportunities**:
- Notion cache hit rate: ~95% (6h TTL, companies rarely change)
- Parallel processing: Not needed for MVP (single email at a time)
- Batch API calls: Future optimization (Phase 2e or later)

### Token Budget

**Target**: ≤2000 tokens for company list (Assumption #4)

**Test dataset** (10 companies):
- 6 portfolio companies × ~80 tokens each = 480 tokens
- 4 SSG affiliates × ~60 tokens each = 240 tokens
- Markdown structure + headings = ~50 tokens
- **Total**: ~770 tokens (well below 2000 limit)

**Full dataset** (500 companies estimate):
- 500 companies × ~70 tokens avg = 35,000 tokens → **EXCEEDS BUDGET**
- **Mitigation**: Prioritize active portfolio companies (≤200), truncate inactive/archived entries

---

## Risk Mitigations

### RM-001: LLM accuracy <85% (SC-001 failure)

**Risk**: Gemini semantic matching doesn't achieve 85% accuracy on test dataset

**Mitigation**:
1. **Primary**: Improve prompt engineering (add more few-shot examples)
2. **Secondary**: Implement RapidFuzz fuzzy matching fallback (see RQ-002)
3. **Tertiary**: Lower auto-acceptance threshold from 0.85 to 0.70 (more manual review)

**Detection**: Run validation after P1 user stories complete; measure accuracy against ground truth

---

### RM-002: Company list exceeds 2000 token budget

**Risk**: Companies database grows beyond MVP assumption (≤500 entries)

**Mitigation**:
1. **Primary**: Filter to active portfolio companies only (exclude archived/inactive)
2. **Secondary**: Truncate descriptions to 50 characters max
3. **Tertiary**: Implement pagination/chunking (send top N most relevant companies)

**Detection**: Monitor token count in `format_for_llm()` output; log warning if >1800 tokens

---

### RM-003: Notion API fails during extraction

**Risk**: Phase 2a NotionIntegrator.get_data() raises exception mid-extraction

**Mitigation (Assumption #12)**:
```python
try:
    company_context = notion_integrator.get_data(companies_db_id)
except NotionAPIError as e:
    logger.warning(f"Notion API failed: {e}. Continuing without matching.")
    company_context = None  # Graceful degradation

entities = gemini_adapter.extract_entities(email_text, company_context=company_context)
# entities.matched_company_id will be None if company_context is None
```

**Result**: System continues extraction without matching (matched IDs = null, confidence <0.50)

---

## Testing Strategy

### Contract Tests (TDD Phase - Red)

**Test**: Extended GeminiAdapter interface

```python
# tests/contract/test_gemini_adapter_matching_contract.py
def test_extract_entities_with_company_context():
    """Contract: extract_entities() accepts optional company_context parameter."""
    adapter = GeminiAdapter(api_key="test_key")

    # Test with company context
    entities = adapter.extract_entities(
        email_text="브레이크앤컴퍼니와 협업",
        company_context="## Portfolio Companies\n- 브레이크앤컴퍼니 (ID: abc123)"
    )
    assert entities.matched_company_id is not None
    assert entities.startup_match_confidence is not None

    # Test without company context (backward compatibility)
    entities = adapter.extract_entities(email_text="브레이크앤컴퍼니와 협업")
    assert entities.matched_company_id is None
    assert entities.startup_match_confidence is None
```

### Integration Tests (TDD Phase - Red)

**Test**: End-to-end company matching with mocked Notion data

```python
# tests/integration/test_company_matching_integration.py
def test_company_matching_end_to_end(mock_notion_data):
    """Integration: Extract entities + match companies from Notion database."""
    # Arrange
    email_text = load_fixture("sample_emails/sample-001.txt")
    adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))
    company_context = format_for_llm(mock_notion_data)  # 10 test companies

    # Act
    entities = adapter.extract_entities(email_text, company_context=company_context)

    # Assert
    assert entities.startup_name == "브레이크앤컴퍼니"
    assert entities.matched_company_id == "abc123"  # From mock_notion_data
    assert entities.startup_match_confidence >= 0.90
```

### Unit Tests

**Test**: Confidence score logic

```python
# tests/unit/test_confidence_scores.py
def test_confidence_threshold_logic():
    """Unit: Verify confidence >0.85 auto-accepts, <0.85 returns null."""
    # High confidence → return ID
    result = apply_confidence_threshold(matched_id="abc123", confidence=0.92)
    assert result == "abc123"

    # Low confidence → return null
    result = apply_confidence_threshold(matched_id="abc123", confidence=0.72)
    assert result is None
```

---

## Summary

**Research complete**: All technical decisions documented with rationale and alternatives considered.

**Key decisions**:
1. Single LLM call for extraction + matching (no separate service)
2. Markdown company list format (≤2000 tokens)
3. Pure LLM semantic matching (RapidFuzz fallback if accuracy <85%)
4. Backward-compatible ExtractedEntities extension (Optional fields)
5. Prompt-guided confidence scoring (0.85 threshold)

**Next phase**: Generate Phase 1 design artifacts (data-model.md, contracts/, quickstart.md)
