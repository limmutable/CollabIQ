# Quick Start: LLM-Based Company Matching

**Feature**: Phase 2b - LLM-Based Company Matching
**Branch**: `007-llm-matching`
**Prerequisites**: Phase 1b (Gemini extraction) + Phase 2a (Notion read) complete

## Overview

This feature adds intelligent company matching to email entity extraction. When processing emails, the system will automatically match extracted company names to entries in your Notion Companies database and return matched IDs with confidence scores.

**What you'll get**:
- Automatic company matching using Gemini 2.0 Flash semantic understanding
- Confidence scores (0.0-1.0) for each match
- Support for exact matches, abbreviations, typos, and Korean-English variations
- Graceful handling of no-match scenarios

---

## Prerequisites

Before using this feature, ensure you have:

1. ✅ **Phase 1b complete**: GeminiAdapter working with entity extraction
2. ✅ **Phase 2a complete**: NotionIntegrator fetching Companies database
3. ✅ **API Keys configured**: `GEMINI_API_KEY` and `NOTION_API_KEY` in `.env` or Infisical
4. ✅ **Test data**: Sample emails in `tests/fixtures/sample_emails/`

Check prerequisites:
```bash
# Verify Gemini API
uv run collabiq verify-infisical

# Verify Notion database access
uv run collabiq notion fetch

# Ensure on correct branch
git checkout 007-llm-matching
```

---

## Basic Usage

### Step 1: Fetch Company Context (Phase 2a)

```python
from src.notion_integrator.integrator import NotionIntegrator
from src.config.settings import get_settings

settings = get_settings()

# Initialize Notion integrator
integrator = NotionIntegrator(
    api_key=settings.get_secret_or_env("NOTION_API_KEY")
)

# Fetch and format company data
companies_db_id = settings.get_secret_or_env("NOTION_DATABASE_ID_COMPANIES")
data = integrator.get_data(companies_db_id=companies_db_id)

# Get markdown-formatted company list for LLM
company_context = data.summary_markdown  # ≤2000 tokens
```

### Step 2: Extract Entities with Matching

```python
from src.llm_adapters.gemini_adapter import GeminiAdapter

# Initialize Gemini adapter
adapter = GeminiAdapter(
    api_key=settings.get_secret_or_env("GEMINI_API_KEY"),
    model=settings.gemini_model
)

# Load test email
with open("tests/fixtures/sample_emails/sample-001.txt", "r") as f:
    email_text = f.read()

# Extract entities WITH company matching (Phase 2b)
entities = adapter.extract_entities(
    email_text=email_text,
    company_context=company_context  # NEW: Enable matching
)

# Access results
print(f"Startup: {entities.startup_name}")
print(f"Matched ID: {entities.matched_company_id}")
print(f"Confidence: {entities.startup_match_confidence:.2f}")

if entities.matched_company_id:
    print("✅ Match found - ready for Phase 2c classification")
else:
    print("⚠️ No match - requires manual review")
```

### Step 3: Save Results

```python
import json
from pathlib import Path

# Save to data/extractions/ (same as Phase 1b)
output_dir = Path("data/extractions")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "email_001_matched.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(entities.model_dump(), f, ensure_ascii=False, indent=2)

print(f"Saved to {output_file}")
```

---

## Example Outputs

### Example 1: Exact Match (High Confidence ≥0.90)

**Input**: sample-001.txt
```
제목: 브레이크앤컴퍼니 x 신세계 PoC 킥오프 결과
```

**Output**:
```json
{
  "person_in_charge": "이기선",
  "startup_name": "브레이크앤컴퍼니",
  "partner_org": "신세계",
  "details": "PoC 킥오프 미팅, AI 재고 최적화 솔루션 데모",
  "date": "2025-10-28",
  "matched_company_id": "abc123def456ghi789jkl012mno345",
  "matched_partner_id": "stu901vwx234yz056abc789def012",
  "startup_match_confidence": 0.98,
  "partner_match_confidence": 0.95
}
```

**Interpretation**: ✅ Auto-accept both matches (confidence ≥0.90)

---

### Example 2: Semantic Match (Moderate Confidence 0.70-0.89)

**Input**: Test email with abbreviation
```
SSG푸드와 협업 논의
```

**Output**:
```json
{
  "person_in_charge": null,
  "startup_name": "TableManager",
  "partner_org": "SSG푸드",
  "details": "협업 논의",
  "date": null,
  "matched_company_id": null,
  "matched_partner_id": "yz056abc123def456ghi789jkl012",
  "startup_match_confidence": null,
  "partner_match_confidence": 0.82
}
```

**Interpretation**: ✅ Auto-accept partner match (0.82 ≥ threshold 0.85 if adjusted)
⚠️ If threshold remains 0.85, this goes to manual review queue

---

### Example 3: No Match (Low Confidence <0.70)

**Input**: Unknown company
```
CryptoStartup과 협업 제안
```

**Output**:
```json
{
  "person_in_charge": null,
  "startup_name": "CryptoStartup",
  "partner_org": null,
  "details": "협업 제안",
  "date": null,
  "matched_company_id": null,
  "matched_partner_id": null,
  "startup_match_confidence": 0.38,
  "partner_match_confidence": null
}
```

**Interpretation**: ⚠️ No match found - company not in database (requires manual entry, see TD-001)

---

## Confidence Score Interpretation

| Confidence | Match Type | Auto-Accept? | Action |
|-----------|-----------|--------------|--------|
| ≥0.90 | Exact match | ✅ Yes | Proceed to Phase 2c |
| 0.70-0.89 | Semantic match | ⚠️ Depends | Check threshold (default 0.85) |
| 0.50-0.69 | Weak match | ❌ No | Manual review (Phase 3a) |
| <0.50 | No match | ❌ No | Create new company (TD-001) |

---

## Backward Compatibility (Phase 1b Mode)

If you don't provide `company_context`, the system works exactly like Phase 1b:

```python
# Phase 1b mode (extraction only, no matching)
entities = adapter.extract_entities(email_text)  # No company_context parameter

# All matching fields will be None
assert entities.matched_company_id is None
assert entities.matched_partner_id is None
assert entities.startup_match_confidence is None
assert entities.partner_match_confidence is None
```

**Use case**: If Notion API is unavailable, system gracefully degrades to extraction-only mode.

---

## Testing the Feature

### Run Contract Tests
```bash
# Test interface compliance
uv run pytest tests/contract/test_gemini_adapter_matching_contract.py -v
```

### Run Integration Tests
```bash
# Test end-to-end matching with real Gemini API
uv run pytest tests/integration/test_company_matching_integration.py -v
```

### Run Full Test Suite
```bash
# All tests including unit tests for confidence logic
uv run pytest tests/ -k matching -v
```

---

## Troubleshooting

### Issue: `matched_company_id` is always None

**Possible causes**:
1. No `company_context` provided → Solution: Pass `company_context` parameter
2. Notion cache expired → Solution: Run `uv run collabiq notion refresh <DB_ID>`
3. Company not in database → Solution: Add company to Notion Companies database
4. Low confidence (<0.70) → Solution: Check `startup_match_confidence` value

**Debug**:
```python
print(f"Company context length: {len(company_context)} chars")
print(f"Confidence score: {entities.startup_match_confidence}")
```

---

### Issue: Wrong company matched

**Possible causes**:
1. Multiple similar names in database → Solution: Add more context to company descriptions
2. Ambiguous email text → Solution: Improve email cleaning (Phase 1a)
3. LLM hallucination → Solution: File issue, may need RapidFuzz fallback (see research.md RM-001)

**Debug**:
```python
# Check what companies are in context
print(company_context)  # Should show all 10 test companies
```

---

### Issue: Performance >3 seconds (SC-003 failure)

**Possible causes**:
1. Notion cache miss → Solution: Warm up cache with `notion fetch`
2. Large company list (>500 entries) → Solution: Implement RM-002 mitigation (filter inactive)
3. Gemini API slow → Solution: Check API status, retry with backoff

**Measure**:
```python
import time

start = time.time()
entities = adapter.extract_entities(email_text, company_context)
elapsed = time.time() - start

print(f"Extraction + matching took {elapsed:.2f}s")
assert elapsed < 3.0, f"Performance target missed: {elapsed:.2f}s"
```

---

## Next Steps

After verifying company matching works:

1. **Phase 2c**: Use `matched_company_id` and `matched_partner_id` for collaboration classification ([A]/[B]/[C]/[D])
2. **Phase 2d**: Write to Notion CollabIQ database using matched IDs as relation links
3. **Phase 3a**: Implement manual review queue for low-confidence matches (<0.85)

---

## API Reference

See [contracts/gemini_adapter_extension.md](contracts/gemini_adapter_extension.md) for detailed API contract.

**Key methods**:
- `GeminiAdapter.extract_entities(email_text, company_context=None)` - Main extraction + matching
- `NotionIntegrator.get_data(companies_db_id)` - Fetch company list from Phase 2a
- `NotionIntegrator.format_for_llm()` - Get markdown-formatted company context

**Data models**:
- `ExtractedEntities` - See [data-model.md](data-model.md) for schema

---

**Quick Start Complete** | Ready to implement Phase 2b with confidence scoring and company matching!
