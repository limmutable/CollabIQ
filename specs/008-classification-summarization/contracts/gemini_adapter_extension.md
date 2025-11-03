# API Contract: GeminiAdapter Extension for Classification & Summarization

**Feature**: 008-classification-summarization
**Date**: 2025-11-03
**Phase**: Phase 1 - Design Artifacts

## Overview

This document specifies the extended API contract for `GeminiAdapter` to support Phase 2c classification and summarization. The contract maintains backward compatibility with Phase 1b/2b while adding new classification and summarization capabilities.

---

## Method Signature

### New Method: `extract_entities_with_classification()`

```python
async def extract_entities_with_classification(
    self,
    email_content: str,
    matched_company_id: Optional[str] = None,
    matched_partner_id: Optional[str] = None,
    company_classification: Optional[str] = None,  # "Portfolio", "SSG Affiliate", "Other"
    partner_classification: Optional[str] = None,  # "Portfolio", "SSG Affiliate", "Other"
    collaboration_types: Optional[Dict[str, str]] = None,  # {"A": "[A]PortCoXSSG", "B": ...}
) -> ExtractedEntitiesWithClassification:
    """
    Extract entities with classification and summarization.

    Args:
        email_content: Cleaned email text (from Phase 1a)
        matched_company_id: Company ID from Phase 2b matching
        matched_partner_id: Partner ID from Phase 2b matching
        company_classification: Company type ("Portfolio", "SSG Affiliate", "Other")
        partner_classification: Partner type ("Portfolio", "SSG Affiliate", "Other")
        collaboration_types: Dict mapping codes to exact Notion field values
                            (fetched dynamically from Notion schema)

    Returns:
        ExtractedEntitiesWithClassification with all Phase 1b/2b/2c fields

    Raises:
        ValueError: If collaboration_types is None (required for type classification)
        GeminiAPIError: If Gemini API call fails
    """
```

**Backward Compatibility**:
- ✅ Existing `extract_entities()` method unchanged (Phase 1b/2b)
- ✅ New method name clearly indicates extended functionality
- ✅ All new parameters are optional (except where logic requires them)

---

## Request Format

### Gemini API Request (JSON)

**LLM Model**: `gemini-2.5-flash` (configurable via `GEMINI_MODEL` in `.env`)

**Prompt Template**:
```python
CLASSIFICATION_PROMPT_TEMPLATE = """
Analyze this Korean business email and extract collaboration information.

Email Content:
{email_content}

Extract the following information:

1. **Basic Entities** (same as Phase 1b):
   - 담당자 (Person in charge)
   - 스타트업명 (Startup name)
   - 협업기관 (Partner organization)
   - 협업내용 (Collaboration details)
   - 날짜 (Date)

2. **Collaboration Intensity** (classify based on semantic understanding):
   Levels:
   - **이해** (Understanding): 초기 미팅, 탐색, 논의, 가능성 검토
   - **협력** (Cooperation): PoC, 파일럿, 테스트, 프로토타입, 협업 진행
   - **투자** (Investment): 투자 검토, DD, 밸류에이션, 계약 검토
   - **인수** (Acquisition): 인수 협상, M&A, 통합 논의, 최종 계약

   Choose the level that best matches the PRIMARY activity in the email.
   Consider verb tense (completed vs planned) when deciding.

3. **Collaboration Summary**:
   Create a 3-5 sentence summary (50-150 words) that:
   - Preserves these 5 key entities: startup name, partner, activity, date, person
   - Uses Korean for business terms, preserves English technical terms (PoC, DD, etc.)
   - Omits: email signatures, disclaimers, quoted emails, greetings

Return JSON (strict schema adherence required):
{{
  "담당자": "string or null",
  "스타트업명": "string or null",
  "협업기관": "string or null",
  "협업내용": "string or null",
  "날짜": "string (YYYY-MM-DD) or null",

  "collaboration_intensity": "이해" | "협력" | "투자" | "인수",
  "intensity_confidence": 0.0-1.0,
  "intensity_reasoning": "1-2 sentence explanation",

  "collaboration_summary": "3-5 sentence Korean summary",
  "summary_word_count": integer (actual word count),
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

**API Call**:
```python
response = await genai.GenerativeModel(
    model_name=self.model_name,  # "gemini-2.5-flash"
    generation_config={
        "temperature": 0.1,  # Low temperature for consistency
        "response_mime_type": "application/json",
        "response_schema": ExtractedEntitiesResponseSchema  # Pydantic → JSON Schema
    }
).generate_content_async(prompt)
```

---

## Response Format

### Gemini API Response (JSON)

```json
{
  "담당자": "김주영",
  "스타트업명": "브레이크앤컴퍼니",
  "협업기관": "신세계푸드",
  "협업내용": "AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅",
  "날짜": "2025-10-28",

  "collaboration_intensity": "협력",
  "intensity_confidence": 0.88,
  "intensity_reasoning": "이메일 내용에 'PoC 킥오프 미팅' 및 '파일럿 테스트 계획 수립'이 명확히 언급되어 협력 단계로 판단",

  "collaboration_summary": "브레이크앤컴퍼니와 신세계푸드가 AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅을 진행했습니다. 신세계백화점 강남점에서 11월 첫째 주부터 2개월간 파일럿 테스트 예정이며, 재고 회전율 15% 개선 및 폐기 손실 20% 감소 효과가 기대됩니다. 김주영 담당자가 프로젝트를 주도하며, 11월 3일 기술 통합 회의가 예정되어 있습니다.",
  "summary_word_count": 78,
  "key_entities_preserved": {
    "startup": true,
    "partner": true,
    "activity": true,
    "date": true,
    "person": true
  }
}
```

### Post-Processing (Python)

After receiving Gemini response, apply deterministic type classification:

```python
def classify_collaboration_type(
    company_classification: str,
    partner_classification: str,
    collaboration_types: Dict[str, str]
) -> tuple[str, float]:
    """
    Deterministic type classification based on company classifications.

    Returns:
        (collaboration_type, confidence)
        - collaboration_type: Exact Notion field value (e.g., "[A]PortCoXSSG")
        - confidence: Always 0.95 for deterministic logic (high confidence)
    """
    if company_classification == "Portfolio" and partner_classification == "SSG Affiliate":
        return (collaboration_types["A"], 0.95)
    elif company_classification == "Portfolio" and partner_classification == "Portfolio":
        return (collaboration_types["C"], 0.95)
    elif company_classification == "Portfolio":
        # External or Other
        return (collaboration_types["B"], 0.90)
    else:
        # Non-portfolio
        return (collaboration_types["D"], 0.80)
```

### Final Response Model

```python
ExtractedEntitiesWithClassification(
    # Phase 1b fields (from Gemini)
    담당자="김주영",
    스타트업명="브레이크앤컴퍼니",
    협업기관="신세계푸드",
    협업내용="AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅",
    날짜="2025-10-28",

    # Phase 2b fields (from input)
    matched_company_id="uuid-123",
    matched_partner_id="uuid-456",
    company_confidence=0.95,
    partner_confidence=0.98,

    # Phase 2c type classification (deterministic)
    collaboration_type="[A]PortCoXSSG",
    type_confidence=0.95,

    # Phase 2c intensity classification (from Gemini)
    collaboration_intensity="협력",
    intensity_confidence=0.88,

    # Phase 2c summary (from Gemini)
    collaboration_summary="브레이크앤컴퍼니와 신세계푸드가 AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅을 진행했습니다...",
    summary_word_count=78,
    key_entities_preserved={
        "startup": True,
        "partner": True,
        "activity": True,
        "date": True,
        "person": True
    },

    classification_timestamp="2025-11-03T10:30:00Z"
)
```

---

## Error Handling

### Error Scenarios

| Error | HTTP Status | Response | Mitigation |
|-------|-------------|----------|------------|
| Gemini API timeout | 503 | `GeminiAPIError: Timeout after 10s` | Retry with exponential backoff |
| Gemini rate limit | 429 | `GeminiAPIError: Rate limit exceeded` | Wait 60s, retry |
| Invalid JSON response | 500 | `GeminiAPIError: Invalid JSON` | Log error, return null classifications |
| Missing required fields | 500 | `ValidationError: Missing 담당자` | Return partial extraction, flag for manual review |
| Collaboration types not provided | 400 | `ValueError: collaboration_types required` | Caller must fetch from Notion first |

### Graceful Degradation

```python
try:
    entities_with_classification = await gemini_adapter.extract_entities_with_classification(...)
except GeminiAPIError as e:
    logger.error(f"Classification failed: {e}")
    # Return Phase 1b/2b extraction only
    entities = ExtractedEntitiesWithClassification(
        담당자=...,  # Phase 1b fields
        matched_company_id=...,  # Phase 2b fields
        collaboration_type=None,  # Phase 2c fields null
        collaboration_intensity=None,
        collaboration_summary=None
    )
    # Flag for manual review
    entities.needs_manual_review = True
```

---

## Performance Requirements

| Operation | Target | Measured | Notes |
|-----------|--------|----------|-------|
| Gemini API call | ≤3 seconds | TBD | Same as Phase 1b/2b |
| Type classification (deterministic) | <10ms | N/A | Pure Python logic |
| Total processing time | ≤4 seconds | TBD | Phase 1b + 2b + 2c combined |

**Optimization**:
- ✅ Single Gemini API call for intensity + summary (not separate calls)
- ✅ Deterministic type classification (no LLM call needed)
- ✅ Parallel processing possible (type classification doesn't depend on Gemini response)

---

## Contract Tests

### Test Cases

```python
import pytest
from tests.contract.test_gemini_classification_contract import *

class TestGeminiAdapterClassificationContract:
    """Contract tests for GeminiAdapter extension"""

    async def test_response_schema_valid(self):
        """Verify Gemini returns all required fields"""
        response = await gemini_adapter.extract_entities_with_classification(
            email_content=sample_email,
            company_classification="Portfolio",
            partner_classification="SSG Affiliate",
            collaboration_types={"A": "[A]PortCoXSSG", "B": "[B]Non-PortCoXSSG", ...}
        )

        # Phase 1b fields
        assert response.담당자 is not None
        assert response.스타트업명 is not None

        # Phase 2c fields
        assert response.collaboration_type == "[A]PortCoXSSG"
        assert response.collaboration_intensity in ["이해", "협력", "투자", "인수"]
        assert 0.0 <= response.type_confidence <= 1.0
        assert 0.0 <= response.intensity_confidence <= 1.0
        assert response.collaboration_summary is not None
        assert 50 <= response.summary_word_count <= 150

    async def test_deterministic_type_classification(self):
        """Verify type classification logic"""
        test_cases = [
            ("Portfolio", "SSG Affiliate", "[A]PortCoXSSG"),
            ("Portfolio", "Portfolio", "[C]PortCoXPortCo"),
            ("Portfolio", "Other", "[B]Non-PortCoXSSG"),
            ("Other", "SSG Affiliate", "[D]Other"),
        ]

        for company_class, partner_class, expected_type in test_cases:
            response = await gemini_adapter.extract_entities_with_classification(
                email_content="...",
                company_classification=company_class,
                partner_classification=partner_class,
                collaboration_types=NOTION_TYPES
            )
            assert response.collaboration_type == expected_type
            assert response.type_confidence >= 0.80

    async def test_backward_compatibility(self):
        """Verify Phase 1b/2b extraction still works"""
        # Old method unchanged
        entities = await gemini_adapter.extract_entities(email_content)
        assert hasattr(entities, '담당자')
        assert not hasattr(entities, 'collaboration_type')  # Phase 2c field absent

    async def test_graceful_degradation(self):
        """Verify null classifications don't break extraction"""
        response = await gemini_adapter.extract_entities_with_classification(
            email_content="Empty email",
            company_classification=None,
            partner_classification=None,
            collaboration_types=NOTION_TYPES
        )

        # Phase 1b extraction should still work
        assert response.담당자 is None or isinstance(response.담당자, str)

        # Phase 2c classifications should be null
        assert response.collaboration_type is None
        assert response.collaboration_intensity is None
```

---

## Summary

**Contract Guarantees**:
1. ✅ Response schema matches `ExtractedEntitiesWithClassification` model
2. ✅ All Phase 1b/2b fields preserved (backward compatible)
3. ✅ Intensity classification returns one of 4 valid Korean values
4. ✅ Summary length within 50-150 words (≥95% compliance)
5. ✅ Confidence scores in range [0.0, 1.0]
6. ✅ Type classification deterministic (0.95 confidence for Portfolio+SSG)
7. ✅ Graceful degradation on errors (null classifications, preserve Phase 1b/2b data)

**Next Steps**: Generate quickstart.md with usage examples
