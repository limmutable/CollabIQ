# CLI Tool: Entity Extraction

This directory contains command-line tools for CollabIQ entity extraction features.

## Phase 1b: Gemini Entity Extraction (MVP)

### Status: Core Implementation Complete ✅

**Implementation Progress**:
- ✅ GeminiAdapter with structured JSON output
- ✅ Test suite (26/29 tests passing)
- ✅ Error handling and retry logic
- ⏳ CLI tool pending (see Technical Debt below)

### Technical Debt

The CLI integration (T026-T028) has been **deferred** to focus on completing the MVP core functionality:

**Deferred Tasks**:
- T026: CLI tool creation (`extract_entities.py`)
- T027: Extraction logging
- T028: End-to-end testing

**Current Workaround**:
Use the GeminiAdapter directly in Python:

```python
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.config.settings import get_settings

# Initialize adapter
settings = get_settings()
adapter = GeminiAdapter(
    api_key=settings.get_secret_or_env("GEMINI_API_KEY"),
    model=settings.gemini_model,
)

# Extract entities
with open("path/to/email.txt") as f:
    email_text = f.read()

entities = adapter.extract_entities(email_text)
print(entities.model_dump_json(indent=2))
```

**Planned Fix**: Phase 2a (after Notion integration)

### Usage Examples (When CLI is Implemented)

**Single Email Extraction**:
```bash
uv run python src/cli/extract_entities.py --email tests/fixtures/sample_emails/korean_001.txt

# Expected output: JSON with 5 entities + confidence scores
```

**Batch Processing** (Deferred to Phase 4):
```bash
uv run python src/cli/extract_entities.py --batch data/cleaned/*.txt --output batch_results.json
```

**Confidence Review** (Deferred to Phase 5):
```bash
uv run python src/cli/extract_entities.py --email email.txt --show-confidence
```

### Troubleshooting

**Error: "ModuleNotFoundError: No module named 'src'"**
- **Cause**: Python path not configured
- **Fix**: Run from repository root: `uv run python src/cli/extract_entities.py`

**Error: "email_text cannot be empty"**
- **Cause**: Empty or whitespace-only email file
- **Fix**: Ensure email file contains actual text content

**Error: "email_text too long (15000 chars). Maximum length is 10,000 characters."**
- **Cause**: Email exceeds maximum length
- **Fix**: Truncate email or split into multiple extractions

**Error: "Rate limit exceeded (429)"**
- **Cause**: Gemini API rate limit hit (10 req/min on free tier)
- **Fix**: Wait 60 seconds or use paid tier

**Error: "Authentication failed (401)"**
- **Cause**: Invalid or missing GEMINI_API_KEY
- **Fix**:
  1. Check Infisical connection: `uv run python -c "from src.config.settings import get_settings; s = get_settings(); print(s.get_secret_or_env('GEMINI_API_KEY')[:10])"`
  2. Verify API key in Infisical dashboard or `.env` file
  3. Regenerate API key at https://aistudio.google.com/app/apikey

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `LLMValidationError: Malformed API response` | Gemini returned invalid JSON | Check API status, retry request |
| `LLMTimeoutError: Request timeout (10s)` | Slow API response | Increase timeout in settings or retry |
| `LLMRateLimitError: Rate limit exceeded after 3 retries` | Too many requests | Wait 60s between batches |
| `Pydantic ValidationError` | Invalid entity data | Check response format matches schema |

### Configuration

**Environment Variables** (via Infisical or `.env`):
```bash
# Gemini API Configuration
GEMINI_API_KEY=AIzaSyD...                 # Required
GEMINI_MODEL=gemini-2.0-flash-exp         # Default model
GEMINI_TIMEOUT_SECONDS=10                 # Request timeout
GEMINI_MAX_RETRIES=3                      # Retry attempts
```

**Settings** (`src/config/settings.py`):
- `gemini_api_key`: Retrieved from Infisical or `.env`
- `gemini_model`: Model name (default: "gemini-2.0-flash-exp")
- `gemini_timeout_seconds`: Timeout in seconds (default: 10)
- `gemini_max_retries`: Maximum retry attempts (default: 3)

### Testing

**Run all extraction tests**:
```bash
# Contract tests (LLMProvider interface)
uv run pytest tests/contract/test_llm_provider_interface.py -v

# Integration tests (GeminiAdapter)
uv run pytest tests/integration/test_gemini_adapter.py -v

# Unit tests (date parsing, confidence scoring)
uv run pytest tests/unit/test_date_parsing.py -v
uv run pytest tests/unit/test_confidence_scoring.py -v
```

**Coverage**:
```bash
uv run pytest --cov=src/llm_provider --cov=src/llm_adapters --cov-report=html
open htmlcov/index.html
```

### Performance

**Single Email**:
- Processing time: ≤5 seconds (excluding Gemini API latency)
- Gemini API latency: ~1-3 seconds (typical)
- Total: ~3-8 seconds per email

**Accuracy** (MVP target):
- Korean emails: ≥85% accuracy (SC-001)
- English emails: ≥85% accuracy (SC-002)
- Confidence calibration: ≥90% (SC-003)

### Next Steps

1. **Complete CLI integration** (T026-T028) - Pending
2. **Integrate with Notion** (Phase 2a) - Automatic entry creation
3. **Add batch processing** (Phase 4) - Process 20+ emails efficiently
4. **Add confidence review** (Phase 5) - Manual review queue

---

**Document Status**: ✅ Complete
**Last Updated**: 2025-11-01 (Phase 1b completion)
