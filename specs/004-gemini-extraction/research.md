# Technical Research: Gemini Entity Extraction

**Feature**: 004-gemini-extraction
**Date**: 2025-11-01
**Research Phase**: Phase 0 - Technical Investigation

## Executive Summary

This document consolidates research findings for implementing LLM-based entity extraction from Korean/English collaboration emails using Gemini 2.5 Flash API.

**Key Decisions**:
1. ✅ Use `google-genai` SDK for Gemini API integration
2. ✅ Use `dateparser` library for multi-format date parsing
3. ✅ Implement few-shot prompting (not zero-shot) for better accuracy
4. ✅ Use structured JSON output with confidence scores via `response_schema`
5. ✅ Implement exponential backoff retry (3 retries) for API errors

---

## Decision 1: Gemini API Integration

### Choice: `google-genai` Python SDK

**Rationale**:
- Official Google SDK with automatic authentication
- Built-in structured output support (`response_schema`, `response_mime_type`)
- Auto-detection of `GEMINI_API_KEY` environment variable
- Integrates with existing Infisical secret management

**Installation**:
```bash
pip install -U google-genai
```

**Authentication**:
```python
from google import genai

# Auto-detect from GEMINI_API_KEY environment variable
client = genai.Client()
```

**Integration with Existing Config**:
- Add `GEMINI_API_KEY` to settings (via Infisical or .env)
- Add `GEMINI_MODEL` to settings (default: "gemini-2.5-flash")
- Leverage existing secret management from Phase 003 (Infisical integration)

### Rate Limits & Quotas (Free Tier)

| Metric | Limit | Implications |
|--------|-------|--------------|
| **Requests** | 10 req/min, 250-500 req/day | Sufficient for MVP (20-30 emails/day) |
| **Tokens** | 250,000 tokens/min | ~500-1000 tokens/email, well within limit |
| **Response Time** | ~1-3 seconds typical | Acceptable for non-real-time processing |
| **Rate Limit Error** | HTTP 429 (RESOURCE_EXHAUSTED) | Handle with exponential backoff retry |

**Note**: Free tier may auto-switch from Gemini 2.5 Pro to Flash after 10-15 prompts (quota exhaustion). This is acceptable for MVP as Flash is the target model.

### Alternatives Considered

- ❌ **Direct REST API**: Requires manual authentication, JSON schema validation, error handling (more complexity)
- ❌ **LangChain Gemini wrapper**: Additional dependency, overengineering for simple extraction use case
- ❌ **OpenAI GPT-4**: Higher cost ($0.01-0.03/request vs free), requires separate API key

---

## Decision 2: Date Parsing Library

### Choice: `dateparser`

**Rationale**:
- Handles all three requirements: English absolute dates, Korean dates, relative dates
- Automatic language detection (200+ locales including Korean)
- Superior relative date parsing ("yesterday", "next Monday" handled automatically)
- Single library solution (simpler than hybrid approach)

**Installation**:
```bash
pip install dateparser
```

**Usage**:
```python
import dateparser

# English absolute dates
dateparser.parse("2025-01-15")         # ✅ Works
dateparser.parse("January 15, 2025")   # ✅ Works

# Korean formats
dateparser.parse("2025년 1월 15일")     # ✅ Works (basic format)
dateparser.parse("10월 27일")          # ✅ Works (month + day)

# Relative dates
dateparser.parse("yesterday")          # ✅ Works
dateparser.parse("next week")          # ✅ Works
dateparser.parse("last Monday")        # ✅ Works
```

**Korean Edge Case - Week Notation**:
- Format `"11월 1주"` (November 1st week) requires custom regex handler
- Solution: Parse month with `dateparser`, compute week offset manually
- Implementation: See `src/llm_provider/date_utils.py` (to be created)

### Trade-offs

| Aspect | dateparser | python-dateutil |
|--------|-----------|-----------------|
| **Size** | ~2 MB | 229 KB |
| **Dependencies** | 4-5 | 1 |
| **Korean Support** | ✅ Partial (basic formats) | ❌ None |
| **Relative Dates** | ✅ Full (automatic) | ⚠️ Manual (via relativedelta) |
| **Performance** | Slower (negligible for email) | 10x faster (milliseconds) |

**Decision**: Trade slight size/performance penalty for Korean + relative date support.

### Alternatives Considered

- ❌ **python-dateutil only**: No Korean support, manual relative date parsing
- ❌ **Hybrid approach** (dateutil + dateparser): More complexity, two libraries to maintain
- ❌ **Custom regex parser**: Error-prone, lower reliability than battle-tested library

---

## Decision 3: Prompt Engineering Strategy

### Choice: Few-Shot Prompting with Structured Output

**Rationale**:
- Few-shot improves accuracy by 30-50% vs zero-shot (per Gemini documentation)
- Structured output (`response_schema`) ensures consistent JSON format
- Confidence scores included as 0.0-1.0 float fields in schema

**System Prompt Template**:
```text
You are an entity extraction assistant for collaboration tracking emails.

Extract exactly 5 entities from Korean/English emails:
1. person_in_charge (담당자): Person responsible for collaboration
2. startup_name (스타트업명): Name of startup company
3. partner_org (협업기관): Partner organization
4. details (협업내용): Collaboration description (preserve original text)
5. date (날짜): Collaboration date (convert to YYYY-MM-DD)

For each entity, provide:
- value: extracted text (or null if missing)
- confidence: 0.0-1.0 score (0.0 if missing, lower if ambiguous)

Return JSON matching the schema exactly.
```

**Few-Shot Examples** (2-3 examples):
```json
// Example 1: Korean email
{
  "input": "어제 신세계인터와 본봄 파일럿 킥오프, 11월 1주 PoC 시작 예정 - 김철수",
  "output": {
    "person_in_charge": {"value": "김철수", "confidence": 0.95},
    "startup_name": {"value": "본봄", "confidence": 0.92},
    "partner_org": {"value": "신세계인터내셔널", "confidence": 0.88},
    "details": {"value": "파일럿 킥오프, 11월 1주 PoC 시작 예정", "confidence": 0.90},
    "date": {"value": "2025-11-01", "confidence": 0.85}
  }
}

// Example 2: English email (partial info)
{
  "input": "TableManager kicked off pilot with Shinsegae yesterday",
  "output": {
    "person_in_charge": {"value": null, "confidence": 0.0},
    "startup_name": {"value": "TableManager", "confidence": 0.95},
    "partner_org": {"value": "Shinsegae", "confidence": 0.90},
    "details": {"value": "kicked off pilot", "confidence": 0.85},
    "date": {"value": "2025-10-31", "confidence": 0.80}
  }
}
```

**Response Schema** (Pydantic-compatible):
```python
{
  "type": "object",
  "properties": {
    "person_in_charge": {
      "type": "object",
      "properties": {
        "value": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
      },
      "required": ["value", "confidence"]
    },
    # ... repeat for all 5 entities
  },
  "required": ["person_in_charge", "startup_name", "partner_org", "details", "date"]
}
```

### Alternatives Considered

- ❌ **Zero-shot**: Lower accuracy (60-70% vs 85-90% for few-shot)
- ❌ **Unstructured text output**: Requires additional parsing, error-prone
- ❌ **Separate API calls per entity**: 5x cost, slower, higher failure rate

---

## Decision 4: Error Handling & Retry Strategy

### Choice: Exponential Backoff with 3 Retries

**Error Types & Handling**:

| Error Code | Meaning | Retry Strategy |
|-----------|---------|----------------|
| **429** | Rate limit (RESOURCE_EXHAUSTED) | ✅ Retry with backoff (1s → 2s → 4s) |
| **500** | Internal server error | ✅ Retry (may be transient) |
| **503** | Service unavailable | ✅ Retry (temporary outage) |
| **400/401/403** | Auth/validation error | ❌ No retry (fix required) |
| **408** | Timeout | ✅ Retry once (increase timeout) |

**Retry Logic**:
```python
import time
import random

def exponential_backoff_retry(func, max_retries=3):
    """Retry with exponential backoff and jitter"""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            delay = min(60, (2 ** attempt) + random.uniform(0, 1))
            logging.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt+1}/{max_retries})")
            time.sleep(delay)
        except (InternalServerError, ServiceUnavailable) as e:
            if attempt == max_retries - 1:
                raise
            delay = min(60, (2 ** attempt))
            logging.warning(f"API error {type(e).__name__}, retrying in {delay}s")
            time.sleep(delay)
```

**Timeout Handling**:
- Default timeout: 10 seconds
- Configurable via `GEMINI_TIMEOUT_SECONDS` environment variable
- Raise `LLMTimeoutError` on timeout (retryable)

### Alternatives Considered

- ❌ **No retry**: Fails on transient errors (poor user experience)
- ❌ **Fixed delay retry**: Ignores exponential nature of rate limits
- ❌ **Unlimited retries**: Risk of infinite loops, delayed error feedback

---

## Decision 5: Architecture & Caching

### Choice: TTL-Based In-Memory Cache (Optional)

**Rationale**:
- Leverage existing in-memory cache pattern from Phase 003 (Infisical integration)
- Cache extracted entities for duplicate email detection
- TTL: 3600 seconds (1 hour) for recent extractions
- Cache key: `email_id` (from Phase 1a duplicate tracker)

**Implementation**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

class GeminiAdapter:
    def __init__(self):
        self._extraction_cache = {}  # {email_id: (entities, timestamp)}

    def extract_entities(self, email_text: str, email_id: str) -> ExtractedEntities:
        # Check cache
        if email_id in self._extraction_cache:
            entities, timestamp = self._extraction_cache[email_id]
            if datetime.now() - timestamp < timedelta(hours=1):
                logging.info(f"Cache hit for email {email_id}")
                return entities

        # Extract (cache miss or expired)
        entities = self._call_gemini_api(email_text)
        self._extraction_cache[email_id] = (entities, datetime.now())
        return entities
```

**Trade-off**: Memory usage (~1-2 KB per cached email) vs API cost savings.

### Alternatives Considered

- ❌ **No caching**: Wastes API calls on duplicate emails
- ❌ **Persistent cache** (Redis/SQLite): Overengineering for MVP (20-30 emails/day)
- ❌ **File-based cache**: Slower than in-memory, adds I/O complexity

---

## Implementation Checklist

Based on research findings, the implementation will require:

### Dependencies to Add
- [ ] `google-genai` - Gemini Python SDK
- [ ] `dateparser` - Multi-format date parsing

### Configuration Updates
- [ ] Add `GEMINI_API_KEY` to `src/config/settings.py` (via Infisical or .env)
- [ ] Add `GEMINI_MODEL` to settings (default: "gemini-2.5-flash")
- [ ] Add `GEMINI_TIMEOUT_SECONDS` to settings (default: 10)
- [ ] Add `GEMINI_MAX_RETRIES` to settings (default: 3)

### Code Components
- [ ] `src/llm_provider/base.py` - Abstract LLMProvider interface
- [ ] `src/llm_adapters/gemini_adapter.py` - GeminiAdapter implementation
- [ ] `src/llm_adapters/prompts/extraction_prompt.txt` - System prompt + few-shot examples
- [ ] `src/llm_provider/date_utils.py` - Korean week notation parser
- [ ] `src/llm_provider/exceptions.py` - LLM-specific exceptions (LLMAPIError, LLMRateLimitError, LLMTimeoutError)

### Testing Requirements
- [ ] Mock Gemini API responses for unit tests
- [ ] Create 30-email test dataset (20 Korean + 10 English)
- [ ] Define ground truth for accuracy validation (GROUND_TRUTH.md)
- [ ] Test rate limit handling (mock 429 responses)
- [ ] Test timeout handling (mock slow API)
- [ ] Test Korean week notation parsing ("11월 1주")

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Rate limit exceeded** | Medium | High | Implement exponential backoff retry, batch processing with delays |
| **API downtime** | Low | High | Retry logic, error logging, dead letter queue (Phase 2e) |
| **Inaccurate extractions** | Medium | Medium | Few-shot prompting, confidence thresholds, manual review queue (P3) |
| **Korean date parsing fails** | Medium | Low | Fallback to null + confidence 0.0, document edge cases |
| **API cost increases** | Low | Low | MVP uses free tier (10 req/min sufficient for 20-30 emails/day) |

---

## Validation Plan

After implementation, validate against success criteria:

1. **SC-001**: ≥85% accuracy on 20 Korean emails
2. **SC-002**: ≥85% accuracy on 10 English emails
3. **SC-003**: ≥90% confidence calibration (high-confidence = correct)
4. **SC-004**: ≤5 seconds processing time per email

**Validation Method**:
- Run extraction on test dataset (30 emails)
- Compare results against GROUND_TRUTH.md
- Calculate accuracy per entity type (person, startup, partner, details, date)
- Calculate confidence calibration (% of high-confidence extractions that are correct)

---

**Research Complete**: ✅
**Next Step**: Phase 1 - Design artifacts (data-model.md, contracts/, quickstart.md)
