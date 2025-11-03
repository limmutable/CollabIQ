# Quickstart: Classification & Summarization

**Feature**: 008-classification-summarization
**Date**: 2025-11-03
**Prerequisites**: Phase 1a (email reception), Phase 1b (entity extraction), Phase 2a (Notion read), Phase 2b (company matching)

## Overview

This guide shows how to use Phase 2c's classification and summarization features to automatically classify collaboration types (dynamically fetched from Notion "협업형태" field) and intensity levels (이해/협력/투자/인수), and generate 3-5 sentence summaries preserving 5 key entities.

---

## Quick Example

```python
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.notion_integrator.integrator import NotionIntegrator
from src.models.classification_service import ClassificationService
from src.config.settings import get_settings

# Initialize components
settings = get_settings()
gemini_adapter = GeminiAdapter(settings)
notion_integrator = NotionIntegrator(settings)

# Create classification service
classification_service = ClassificationService(
    notion_integrator=notion_integrator,
    gemini_adapter=gemini_adapter,
    collabiq_db_id=settings.notion_database_id_collabiq
)

# Process email with classification + summarization
email_content = """
보낸사람: Giseon Teddy.Lee <ks.lee@break.co.kr>
받는사람: 안동훈 <cogito9@shinsegae.com>
제목: 브레이크앤컴퍼니 x 신세계 PoC 킥오프 결과

어제 신세계 유통 디지털 혁신팀과의 PoC 킥오프 미팅 요약 전달드립니다.
11월 첫째 주부터 2개월간 파일럿 테스트 예정입니다.
"""

# Extract with classification
result = await classification_service.extract_with_classification(
    email_content=email_content
)

# View results
print(f"Type: {result.collaboration_type}")  # "[A]PortCoXSSG"
print(f"Intensity: {result.collaboration_intensity}")  # "협력"
print(f"Summary: {result.collaboration_summary}")
print(f"Confidence: Type={result.type_confidence}, Intensity={result.intensity_confidence}")
```

**Output**:
```
Type: [A]PortCoXSSG
Intensity: 협력
Type Confidence: 0.95
Intensity Confidence: 0.88
Summary: 브레이크앤컴퍼니와 신세계 유통 디지털 혁신팀이 PoC 킥오프 미팅을 진행했습니다. 11월 첫째 주부터 2개월간 파일럿 테스트가 예정되어 있습니다. 담당자는 안동훈입니다.
Word Count: 42
Key Entities Preserved: startup=True, partner=True, activity=True, date=True, person=True
```

---

## Step-by-Step Usage

### Step 1: Setup Dependencies

Ensure all Phase 1b, 2a, and 2b components are initialized:

```python
from src.config.settings import get_settings
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.notion_integrator.integrator import NotionIntegrator

settings = get_settings()

# Phase 1b: Entity extraction
gemini_adapter = GeminiAdapter(settings)

# Phase 2a: Notion schema fetching
notion_integrator = NotionIntegrator(settings)
```

### Step 2: Fetch Collaboration Types from Notion

Dynamic schema fetching (runs once per session, cached for 24 hours):

```python
# Get collaboration types from Notion "협업형태" property
schema = await notion_integrator.discover_database_schema(
    settings.notion_database_id_collabiq
)

collab_type_prop = schema.properties.get("협업형태")
if not collab_type_prop:
    raise ValueError("협업형태 property not found in CollabIQ database")

# Parse into {code: full_value} dict
collaboration_types = {}
import re
for option in collab_type_prop.options:
    match = re.match(r'^\[([A-Z0-9])\]', option.name)
    if match:
        code = match.group(1)
        collaboration_types[code] = option.name

print(collaboration_types)
# {'A': '[A]PortCoXSSG', 'B': '[B]Non-PortCoXSSG', 'C': '[C]PortCoXPortCo', 'D': '[D]Other'}
```

### Step 3: Classify Collaboration Type (Deterministic)

Based on Phase 2b company classifications:

```python
def classify_type(company_class: str, partner_class: str, types: dict) -> tuple:
    """Deterministic type classification"""
    if company_class == "Portfolio" and partner_class == "SSG Affiliate":
        return (types["A"], 0.95)  # "[A]PortCoXSSG", high confidence
    elif company_class == "Portfolio" and partner_class == "Portfolio":
        return (types["C"], 0.95)  # "[C]PortCoXPortCo"
    elif company_class == "Portfolio":
        return (types["B"], 0.90)  # "[B]Non-PortCoXSSG" (external)
    else:
        return (types["D"], 0.80)  # "[D]Other" (non-portfolio)

# Example
collaboration_type, type_confidence = classify_type(
    company_class="Portfolio",
    partner_class="SSG Affiliate",
    types=collaboration_types
)
print(f"Type: {collaboration_type}, Confidence: {type_confidence}")
# Type: [A]PortCoXSSG, Confidence: 0.95
```

### Step 4: Classify Intensity (LLM-based)

Using Gemini 2.5 Flash for Korean semantic understanding:

```python
# Gemini prompt for intensity classification
intensity_prompt = f"""
Analyze this Korean business email and classify the collaboration intensity level.

Intensity Levels:
1. **이해** (Understanding): 초기 미팅, 탐색, 논의, 가능성 검토
2. **협력** (Cooperation): PoC, 파일럿, 테스트, 프로토타입, 협업 진행
3. **투자** (Investment): 투자 검토, DD, 밸류에이션, 계약 검토
4. **인수** (Acquisition): 인수 협상, M&A, 통합 논의, 최종 계약

Email Content:
{email_content}

Return JSON:
{{
  "collaboration_intensity": "이해" | "협력" | "투자" | "인수",
  "intensity_confidence": 0.0-1.0,
  "intensity_reasoning": "explanation"
}}
"""

response = await gemini_adapter.generate_json(intensity_prompt)
print(f"Intensity: {response['collaboration_intensity']}")
print(f"Confidence: {response['intensity_confidence']}")
print(f"Reasoning: {response['intensity_reasoning']}")
```

**Example Output**:
```
Intensity: 협력
Confidence: 0.88
Reasoning: 이메일 내용에 'PoC 킥오프 미팅' 및 '파일럿 테스트'가 명확히 언급되어 협력 단계로 판단
```

### Step 5: Generate Summary

Preserve 5 key entities (startup, partner, activity, date, person):

```python
summary_prompt = f"""
Summarize this Korean business email in 3-5 sentences (50-150 words).

CRITICAL: Preserve these 5 key entities:
1. Startup name (스타트업명)
2. Partner organization (협업기관)
3. Activity/purpose (협업내용)
4. Date (날짜)
5. Person in charge (담당자)

Email Content:
{email_content}

Return JSON:
{{
  "collaboration_summary": "3-5 sentence Korean summary",
  "summary_word_count": integer,
  "key_entities_preserved": {{
    "startup": boolean,
    "partner": boolean,
    "activity": boolean,
    "date": boolean,
    "person": boolean
  }}
}}
"""

response = await gemini_adapter.generate_json(summary_prompt)
print(f"Summary: {response['collaboration_summary']}")
print(f"Word Count: {response['summary_word_count']}")
print(f"Entities Preserved: {response['key_entities_preserved']}")
```

### Step 6: Save Results

Store extended extraction with classifications:

```python
from src.models.classification_service import ExtractedEntitiesWithClassification
import json
from datetime import datetime

# Create full result object
result = ExtractedEntitiesWithClassification(
    # Phase 1b fields
    담당자=entities.담당자,
    스타트업명=entities.스타트업명,
    협업기관=entities.협업기관,
    협업내용=entities.협업내용,
    날짜=entities.날짜,

    # Phase 2b fields
    matched_company_id=matched_company_id,
    matched_partner_id=matched_partner_id,
    company_confidence=company_confidence,
    partner_confidence=partner_confidence,

    # Phase 2c fields
    collaboration_type=collaboration_type,
    collaboration_intensity=intensity_response['collaboration_intensity'],
    type_confidence=type_confidence,
    intensity_confidence=intensity_response['intensity_confidence'],
    collaboration_summary=summary_response['collaboration_summary'],
    summary_word_count=summary_response['summary_word_count'],
    key_entities_preserved=summary_response['key_entities_preserved'],
    classification_timestamp=datetime.utcnow().isoformat() + 'Z'
)

# Save to file
output_path = f"data/extractions/{email_id}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result.dict(), f, ensure_ascii=False, indent=2)

print(f"Saved to: {output_path}")
```

---

## Testing

### Run Unit Tests

```bash
# Test deterministic type classification logic
uv run pytest tests/unit/test_type_classification.py -v

# Test intensity classification with sample emails
uv run pytest tests/unit/test_intensity_classification.py -v

# Test summary generation
uv run pytest tests/unit/test_summary_generation.py -v
```

### Run Integration Tests

```bash
# End-to-end test with real email fixtures
uv run pytest tests/integration/test_classification_e2e.py -v

# Test with sample-001.txt through sample-006.txt
uv run pytest tests/integration/test_classification_e2e.py::test_sample_emails -v
```

### Run Contract Tests

```bash
# Verify Gemini response schema
uv run pytest tests/contract/test_gemini_classification_contract.py -v
```

---

## Common Use Cases

### Use Case 1: Batch Process Emails

Process multiple emails with classification:

```python
async def batch_process_with_classification(email_ids: list[str]):
    """Process multiple emails with classification"""
    classification_service = ClassificationService(...)

    results = []
    for email_id in email_ids:
        # Load email
        email_content = load_email(email_id)

        # Process with classification
        result = await classification_service.extract_with_classification(email_content)

        # Route based on confidence
        if result.needs_manual_review():
            print(f"Email {email_id} → Manual Review Queue")
            # Add to manual review queue (Phase 3a)
        else:
            print(f"Email {email_id} → Auto-accepted")
            # Write to Notion (Phase 2d)

        results.append(result)

    return results
```

### Use Case 2: Re-classify Existing Extractions

Add classifications to existing Phase 1b/2b extractions:

```python
async def upgrade_existing_extraction(extraction_file: str):
    """Add Phase 2c classifications to existing extraction"""
    # Load existing extraction
    with open(extraction_file) as f:
        data = json.load(f)

    # Parse as Phase 1b/2b model
    entities = ExtractedEntities(**data)

    # Add Phase 2c classifications
    classification_service = ClassificationService(...)
    result = await classification_service.add_classification(entities)

    # Save upgraded version
    with open(extraction_file, 'w') as f:
        json.dump(result.dict(), f, ensure_ascii=False, indent=2)

    print(f"Upgraded: {extraction_file}")
```

### Use Case 3: Validate Classification Accuracy

Test against ground truth:

```python
async def validate_accuracy(test_emails: list[dict]):
    """Validate classification accuracy against ground truth"""
    classification_service = ClassificationService(...)

    correct_types = 0
    correct_intensities = 0
    total = len(test_emails)

    for test in test_emails:
        result = await classification_service.extract_with_classification(
            test['email_content']
        )

        if result.collaboration_type == test['ground_truth_type']:
            correct_types += 1

        if result.collaboration_intensity == test['ground_truth_intensity']:
            correct_intensities += 1

    type_accuracy = correct_types / total
    intensity_accuracy = correct_intensities / total

    print(f"Type Accuracy: {type_accuracy:.1%}")
    print(f"Intensity Accuracy: {intensity_accuracy:.1%}")

    # Success Criteria: ≥85% accuracy (SC-001, SC-002)
    assert type_accuracy >= 0.85, f"Type accuracy too low: {type_accuracy:.1%}"
    assert intensity_accuracy >= 0.85, f"Intensity accuracy too low: {intensity_accuracy:.1%}"
```

---

## Troubleshooting

### Issue 1: "협업형태 property not found"

**Cause**: Notion CollabIQ database doesn't have "협업형태" Select property.

**Solution**:
```python
# Verify database ID is correct
print(f"CollabIQ DB ID: {settings.notion_database_id_collabiq}")

# List all properties
schema = await notion_integrator.discover_database_schema(settings.notion_database_id_collabiq)
print("Available properties:")
for name, prop in schema.properties.items():
    print(f"  - {name} ({prop.type})")
```

### Issue 2: Low classification confidence (<0.85)

**Cause**: Ambiguous email content or unclear intensity indicators.

**Solution**:
```python
# Check confidence scores
if result.type_confidence < 0.85 or result.intensity_confidence < 0.85:
    print(f"Low confidence detected:")
    print(f"  Type: {result.type_confidence}")
    print(f"  Intensity: {result.intensity_confidence}")
    print(f"  Reasoning: {result.classification_reason}")

    # Route to manual review
    add_to_manual_review_queue(result)
```

### Issue 3: Summary too long (>150 words)

**Cause**: Gemini occasionally violates length constraints.

**Solution**:
```python
def enforce_summary_length(summary: str, max_words: int = 150) -> str:
    """Truncate summary to max words"""
    words = summary.split()
    if len(words) <= max_words:
        return summary

    # Truncate at sentence boundaries
    sentences = summary.split('. ')
    truncated = []
    current_words = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())
        if current_words + sentence_words <= max_words:
            truncated.append(sentence)
            current_words += sentence_words
        else:
            break

    return '. '.join(truncated) + '.'
```

---

## Next Steps

1. **Run tests**: Validate classification accuracy on sample-001.txt through sample-006.txt
2. **Integrate with Phase 2d**: Use classifications to populate Notion CollabIQ database
3. **Setup manual review queue**: Route low-confidence classifications (Phase 3a)
4. **Monitor accuracy**: Track classification accuracy over time (FR-018 logging)

---

## Reference

- **Specification**: [spec.md](spec.md)
- **Implementation Plan**: [plan.md](plan.md)
- **Data Model**: [data-model.md](data-model.md)
- **API Contract**: [contracts/gemini_adapter_extension.md](contracts/gemini_adapter_extension.md)
- **Research Decisions**: [research.md](research.md)
