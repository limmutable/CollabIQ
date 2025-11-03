# Research: Classification & Summarization

**Feature**: 008-classification-summarization
**Date**: 2025-11-03
**Phase**: Phase 0 - Technical Research

## Overview

This document resolves technical unknowns identified in the Technical Context section of [plan.md](plan.md). Research focuses on: (1) Dynamic Notion schema fetching patterns, (2) Gemini prompt engineering for Korean collaboration intensity classification, (3) Gemini summarization strategies for Korean-English mixed content.

---

## Decision 1: Dynamic Notion Schema Fetching Pattern

**Context**: FR-002 requires dynamically fetching "협업형태" field values from Notion CollabIQ database at runtime to support future changes (e.g., A/B/C/D → 1/2/3/4).

### Investigation

**Existing Phase 2a Implementation**:
- `NotionIntegrator.discover_database_schema(database_id)` already exists (Phase 2a)
- Returns `DatabaseSchema` with `properties: Dict[str, PropertySchema]`
- `PropertySchema` includes `type` and `options` (for Select fields)
- `SelectOption` model has `name` and `color` attributes

**Schema Fetch Pattern** (from Phase 2a source code):
```python
# src/notion_integrator/integrator.py
async def discover_database_schema(self, database_id: str) -> DatabaseSchema:
    """Discover database schema with caching"""
    return await discover_schema(
        client=self.client,
        database_id=database_id,
        cache=self.cache,
        ttl_hours=self.schema_cache_ttl
    )
```

**Cache Strategy** (from Phase 2a):
- File-based cache in `data/notion_cache/schema_{database_name}.json`
- TTL: 24 hours (configurable via `NOTION_SCHEMA_CACHE_TTL_HOURS`)
- Perfect for this use case: session-duration caching requirement (FR-006)

### Decision

**Chosen Approach**: Use existing `NotionIntegrator.discover_database_schema()` with default 24-hour cache TTL.

**Implementation Pattern**:
```python
class ClassificationService:
    def __init__(self, notion_integrator: NotionIntegrator, collabiq_db_id: str):
        self.notion = notion_integrator
        self.collabiq_db_id = collabiq_db_id
        self._type_values_cache: Optional[Dict[str, str]] = None

    async def get_collaboration_types(self) -> Dict[str, str]:
        """Fetch and parse collaboration type values once per session"""
        if self._type_values_cache is None:
            schema = await self.notion.discover_database_schema(self.collabiq_db_id)
            collab_type_prop = schema.properties.get("협업형태")

            if not collab_type_prop or collab_type_prop.type != "select":
                raise ValueError("협업형태 property not found or invalid type")

            # Parse options into {code: full_value} dict
            self._type_values_cache = {}
            for option in collab_type_prop.options:
                match = re.match(r'^\[([A-Z0-9])\]', option.name)
                if match:
                    code = match.group(1)
                    self._type_values_cache[code] = option.name

        return self._type_values_cache
```

**Rationale**:
- ✅ Reuses proven Phase 2a infrastructure (no new cache implementation)
- ✅ 24-hour TTL exceeds "session duration" requirement (acceptable lag for schema changes)
- ✅ Async-compatible (matches existing codebase patterns)
- ✅ Pattern matching `^\[([A-Z0-9])\]` handles both A/B/C/D and future 1/2/3/4 identifiers

**Alternatives Considered**:
- ❌ **In-memory cache only**: Lose cached values on process restart → unnecessary API calls
- ❌ **Custom cache TTL**: Adds complexity, 24 hours is sufficient for admin-level schema changes
- ❌ **Hardcode values**: Rejected (breaks when Notion admin changes values)

---

## Decision 2: Gemini Prompt Engineering for Korean Intensity Classification

**Context**: FR-007/FR-008 require classifying Korean collaboration intensity (이해/협력/투자/인수) with ≥85% accuracy using semantic understanding, not just keyword matching.

### Investigation

**Korean Business Terminology Analysis** (from spec.md FR-008):
- **이해** (Understanding): 초기 미팅, 탐색, 논의, 가능성 검토
- **협력** (Cooperation): PoC, 파일럿, 테스트, 프로토타입, 협업 진행
- **투자** (Investment): 투자 검토, DD, 밸류에이션, 계약 검토
- **인수** (Acquisition): 인수 협상, M&A, 통합 논의, 최종 계약

**Gemini 2.0 Flash Capabilities** (validated in Phase 2b):
- ✅ Strong Korean semantic understanding
- ✅ JSON schema adherence for structured output
- ✅ Confidence scoring support

**Prompt Engineering Strategy**:
```python
INTENSITY_CLASSIFICATION_PROMPT = """
Analyze this Korean business email and classify the collaboration intensity level.

Intensity Levels (in order of commitment):
1. **이해** (Understanding/Exploration): Initial meetings, possibility exploration, early discussions
   - Keywords: 초기 미팅, 탐색, 논의, 가능성 검토, 소개
   - Example: "협업 가능성 논의", "첫 미팅 예정"

2. **협력** (Cooperation/Pilot): Active collaboration, pilot projects, testing phase
   - Keywords: PoC, 파일럿, 테스트, 프로토타입, 협업 진행, 시범 운영
   - Example: "PoC 킥오프", "파일럿 시작"

3. **투자** (Investment): Investment review, due diligence, valuation, contract negotiation
   - Keywords: 투자 검토, DD, 밸류에이션, 계약 검토, 시리즈 A
   - Example: "투자 유치", "DD 진행"

4. **인수** (Acquisition): Acquisition negotiation, M&A, integration discussions
   - Keywords: 인수 협상, M&A, 통합 논의, 최종 계약
   - Example: "인수 협상 진행", "M&A 논의"

Email Content:
{email_content}

Determine the collaboration intensity based on:
1. Primary activity mentioned in the email (not just presence of keywords)
2. Verb tense (completed vs planned affects level)
3. Context and semantic meaning (not just keyword matching)

Return JSON:
{{
  "collaboration_intensity": "이해" | "협력" | "투자" | "인수",
  "intensity_confidence": 0.0-1.0,
  "intensity_reasoning": "1-2 sentence explanation of why this level was chosen"
}}
"""
```

### Decision

**Chosen Approach**: Structured LLM prompt with Korean keyword examples + semantic reasoning instructions.

**Rationale**:
- ✅ Provides keyword guidance without rigid keyword matching (supports edge cases via semantic understanding)
- ✅ Explicit instruction to prioritize primary activity (handles "초기 미팅 후 PoC 검토 예정" → 이해)
- ✅ Verb tense consideration (handles progression: "completed meeting, PoC planned")
- ✅ Confidence scoring built into response schema (enables 0.85 threshold routing)
- ✅ Reasoning field aids debugging and accuracy monitoring (FR-018)

**Validation Strategy**:
- Test on sample-001.txt through sample-006.txt (existing fixtures)
- Measure accuracy against manual ground truth labeling
- Iterate prompt if accuracy <85%

**Alternatives Considered**:
- ❌ **Pure keyword matching**: Fails on "파일럿 테스트 논의" (ambiguous: could be 이해 or 협력)
- ❌ **Separate NLP library (KoNLPy, etc.)**: Adds dependency, Gemini already handles Korean
- ❌ **Few-shot examples in prompt**: Increases token cost, not needed if prompt is clear

---

## Decision 3: Gemini Summarization Strategy for Korean-English Mixed Content

**Context**: FR-009/FR-010/FR-011 require generating 3-5 sentence summaries (50-150 words) preserving 5 key entities (startup, partner, activity, date, person) for Korean-English bilingual emails.

### Investigation

**Email Structure Analysis** (from test fixtures):
- Korean business terminology: 협업, 미팅, 파일럿, 투자
- English technical terms: PoC, DD, M&A, SaaS, API
- Mixed company names: "브레이크앤컴퍼니 × Google Cloud"

**Summary Requirements** (from spec.md):
- 3-5 sentences (hard constraint)
- 50-150 words (hard constraint)
- Must preserve: startup name, partner organization, activity/purpose, date, person in charge
- Must omit: email signatures, legal disclaimers, quoted previous emails

**Prompt Engineering Strategy**:
```python
SUMMARIZATION_PROMPT = """
Summarize this Korean business email in 3-5 sentences (50-150 words).

CRITICAL REQUIREMENTS:
1. Preserve these 5 key entities:
   - Startup name (스타트업명)
   - Partner organization (협업기관)
   - Activity/purpose (협업내용)
   - Date (날짜)
   - Person in charge (담당자)

2. Omit:
   - Email signatures
   - Legal disclaimers
   - Quoted previous emails
   - Generic greetings

3. Language:
   - Use Korean for company names and business terminology
   - Preserve English technical terms as-is (PoC, DD, M&A, API, etc.)
   - Keep bilingual clarity where appropriate

4. Length: 50-150 words, 3-5 sentences (STRICTLY ENFORCE)

Email Content:
{email_content}

Return JSON:
{{
  "collaboration_summary": "3-5 sentence summary in Korean",
  "word_count": integer (actual count),
  "key_entities_preserved": {{
    "startup": boolean,
    "partner": boolean,
    "activity": boolean,
    "date": boolean,
    "person": boolean
  }}
}}
"""
```

### Decision

**Chosen Approach**: Structured prompt with explicit entity preservation checklist + length enforcement.

**Rationale**:
- ✅ JSON response schema enables validation (FR-010 entity preservation verification)
- ✅ Explicit length constraints in prompt (50-150 words, 3-5 sentences)
- ✅ Bilingual handling strategy (Korean primary, preserve English technical terms)
- ✅ Omission list prevents signature/disclaimer leakage
- ✅ Word count in response enables SC-004 validation (≥95% within 50-150 range)

**Post-Processing** (if needed):
```python
def validate_summary(summary: str, word_count: int) -> str:
    """Enforce hard length limits if LLM violates constraints"""
    if word_count > 150:
        # Truncate to 150 words, preserve sentence boundaries
        sentences = summary.split('. ')
        truncated = []
        current_words = 0
        for sentence in sentences:
            sentence_words = len(sentence.split())
            if current_words + sentence_words <= 150:
                truncated.append(sentence)
                current_words += sentence_words
            else:
                break
        return '. '.join(truncated) + '.'
    return summary
```

**Alternatives Considered**:
- ❌ **Abstractive summarization without entity checklist**: Risk losing key entities (fails SC-003)
- ❌ **Template-based extraction**: Rigid, fails on varied email structures
- ❌ **Separate Korean/English summaries**: Increases complexity, not required

---

## Decision 4: Confidence Score Calibration

**Context**: FR-012/FR-013 require confidence threshold of 0.85 for auto-acceptance. Need to verify Gemini's confidence scores are well-calibrated.

### Investigation

**Gemini Confidence Scoring** (from Phase 2b validation):
- Gemini returns confidence scores in JSON responses
- Phase 2b company matching used confidence ≥0.70 threshold (100% accuracy on test dataset)
- Higher threshold (0.85) is more conservative → lower false positive rate

**Calibration Validation Plan**:
1. Test on sample-001.txt through sample-006.txt
2. Manual ground truth labeling for type + intensity
3. Calculate precision@0.85: P(correct | confidence ≥0.85)
4. Target: ≥95% precision (from SC-005)

**Fallback Strategy** (if calibration poor):
```python
def adjust_confidence(raw_confidence: float, classification_type: str) -> float:
    """Apply calibration factor if needed"""
    # Type classification (deterministic) should have higher confidence
    if classification_type == "type":
        return min(1.0, raw_confidence * 1.1)  # Boost by 10%
    # Intensity (LLM-based) uses raw confidence
    return raw_confidence
```

### Decision

**Chosen Approach**: Use Gemini's raw confidence scores initially, validate with test dataset, add calibration if needed.

**Rationale**:
- ✅ Phase 2b validation shows Gemini confidence is reliable (100% accuracy at 0.70 threshold)
- ✅ Conservative 0.85 threshold reduces false positives (better to route to manual review than accept wrong classification)
- ✅ Validation built into test strategy (SC-005)
- ✅ Calibration layer available if needed (doesn't add complexity unless required)

**Alternatives Considered**:
- ❌ **Fixed confidence for deterministic logic**: Type classification is deterministic but LLM still returns confidence → use it
- ❌ **Complex calibration model**: Premature optimization, test with raw scores first

---

## Research Summary

| Decision | Approach | Complexity Added | Justification |
|----------|----------|------------------|---------------|
| 1. Schema Fetching | Reuse Phase 2a `NotionIntegrator` | None (existing) | Proven infrastructure, 24h TTL exceeds needs |
| 2. Intensity Classification | Structured LLM prompt with Korean keywords | Low (prompt engineering) | Semantic understanding > pure keyword matching |
| 3. Summarization | Entity-preserving prompt with length enforcement | Low (prompt + validation) | Checklist ensures 5 key entities preserved |
| 4. Confidence Calibration | Use raw scores, validate, calibrate if needed | Minimal (optional fallback) | Phase 2b shows scores are reliable |

**Total Complexity**: **Low** - Primarily prompt engineering and extending existing patterns. No new dependencies, no complex algorithms.

**Risks Identified**:
- ⚠️ LLM accuracy <85% for intensity classification → Mitigation: Iterate prompt, add few-shot examples
- ⚠️ Summary length violations frequent → Mitigation: Post-processing truncation (already designed)
- ⚠️ Confidence scores poorly calibrated → Mitigation: Calibration factor (already designed)

**Next Steps**: Proceed to Phase 1 (data-model.md, contracts/, quickstart.md)
