# Quick Start: Gemini Entity Extraction

**Feature**: 004-gemini-extraction
**Target Users**: Developers testing entity extraction functionality
**Time to Complete**: 10 minutes

---

## Prerequisites

- Python 3.12+ installed
- UV package manager installed
- Gemini API key (from [Google AI Studio](https://aistudio.google.com/app/apikey))
- CollabIQ repository cloned and dependencies installed

---

## Step 1: Install Dependencies

```bash
cd CollabIQ

# Install all dependencies (includes google-genai, dateparser)
uv sync

# Verify installation
uv run python -c "from google import genai; print('✓ Gemini SDK installed')"
uv run python -c "import dateparser; print('✓ dateparser installed')"
```

---

## Step 2: Configure Gemini API Key

### Option A: Using Infisical (Recommended)

```bash
# Add GEMINI_API_KEY to Infisical dashboard
# (Project: CollabIQ, Environment: development)

# Verify Infisical connection
uv run python -c "from src.config.settings import get_settings; s = get_settings(); print(f'✓ Gemini model: {s.gemini_model}')"
```

### Option B: Using .env File (Local Development)

```bash
# Add to .env file
echo "GEMINI_API_KEY=AIza...your_actual_key_here" >> .env
echo "GEMINI_MODEL=gemini-2.5-flash" >> .env

# Verify configuration
uv run python -c "from src.config.settings import get_settings; s = get_settings(); print(f'✓ API key configured: {s.gemini_api_key[:10]}...')"
```

---

## Step 3: Test Single Email Extraction

Create a test email file:

```bash
# Create test email (Korean example)
cat > test_email.txt <<'EOF'
어제 신세계인터내셔널과 본봄 파일럿 킥오프 미팅을 진행했습니다.
11월 1주에 PoC 시작 예정이며, 테이블 예약 시스템 통합을 논의했습니다.

담당자: 김철수
EOF
```

Run extraction:

```bash
# Extract entities from single email
uv run python src/cli/extract_entities.py --email test_email.txt

# Expected output (JSON):
# {
#   "person_in_charge": "김철수",
#   "startup_name": "본봄",
#   "partner_org": "신세계인터내셔널",
#   "details": "파일럿 킥오프 미팅, 11월 1주 PoC 시작 예정, 테이블 예약 시스템 통합 논의",
#   "date": "2025-11-01",
#   "confidence": {
#     "person": 0.95,
#     "startup": 0.92,
#     "partner": 0.88,
#     "details": 0.90,
#     "date": 0.85
#   },
#   "email_id": "test_email_001",
#   "extracted_at": "2025-11-01T10:30:00Z"
# }
```

---

## Step 4: Test Batch Processing

```bash
# Create multiple test emails
mkdir -p test_emails
cat > test_emails/email_001.txt <<'EOF'
TableManager와 신세계푸드 협업 시작 - 2025년 1월 15일
EOF

cat > test_emails/email_002.txt <<'EOF'
Yesterday we kicked off the pilot with Shinsegae Food for our reservation system.
EOF

# Run batch extraction
uv run python src/cli/extract_entities.py --batch test_emails/*.txt --output batch_results.json

# View results
cat batch_results.json | python -m json.tool
```

**Expected Batch Output**:
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    { "email_id": "email_001", "startup_name": "TableManager", "..." },
    { "email_id": "email_002", "startup_name": "TableManager", "..." }
  ],
  "summary": {
    "total_count": 2,
    "success_count": 2,
    "failure_count": 0,
    "processing_time_seconds": 3.5
  }
}
```

---

## Step 5: Review Low-Confidence Extractions

```bash
# Extract from ambiguous email
cat > ambiguous_email.txt <<'EOF'
Met with some people about a collaboration next week.
EOF

uv run python src/cli/extract_entities.py --email ambiguous_email.txt --show-confidence

# Output will flag low-confidence fields:
# ⚠️  person_in_charge: null (confidence: 0.0) - NEEDS REVIEW
# ⚠️  startup_name: null (confidence: 0.0) - NEEDS REVIEW
# ⚠️  partner_org: null (confidence: 0.0) - NEEDS REVIEW
# ✓ details: "collaboration" (confidence: 0.50) - NEEDS REVIEW
# ✓ date: "2025-11-08" (confidence: 0.75) - NEEDS REVIEW
```

---

## CLI Reference

### Single Email Extraction

```bash
uv run python src/cli/extract_entities.py --email <path/to/email.txt>

Options:
  --email PATH          Path to single email file (required)
  --output PATH         Output JSON file (default: stdout)
  --show-confidence     Show confidence scores in output
  --threshold FLOAT     Confidence threshold for flagging (default: 0.85)
```

### Batch Processing

```bash
uv run python src/cli/extract_entities.py --batch <pattern> --output <path.json>

Options:
  --batch PATTERN       Glob pattern for email files (e.g., "data/cleaned/*.txt")
  --output PATH         Output JSON file (required for batch)
  --parallel N          Number of parallel API calls (default: 1, max: 5)
```

---

## Output Format

### Single Extraction (stdout)

```json
{
  "person_in_charge": "김철수",
  "startup_name": "본봄",
  "partner_org": "신세계인터내셔널",
  "details": "파일럿 킥오프, 11월 1주 PoC 시작 예정",
  "date": "2025-11-01T00:00:00Z",
  "confidence": {
    "person": 0.95,
    "startup": 0.92,
    "partner": 0.88,
    "details": 0.90,
    "date": 0.85
  },
  "email_id": "msg_abc123",
  "extracted_at": "2025-11-01T10:30:00Z"
}
```

### Batch Output (file)

```json
{
  "batch_id": "uuid-here",
  "results": [
    { /* ExtractedEntities 1 */ },
    { /* ExtractedEntities 2 */ }
  ],
  "summary": {
    "total_count": 20,
    "success_count": 18,
    "failure_count": 2,
    "processing_time_seconds": 45.3
  }
}
```

---

## Troubleshooting

### Error: "Rate limit exceeded (429)"

```bash
# Wait 60 seconds and retry
# Free tier: 10 requests/minute

# Or use batch processing with delays:
uv run python src/cli/extract_entities.py --batch emails/*.txt --delay 6
# (6 seconds between requests = 10 req/min)
```

### Error: "API authentication failed (401)"

```bash
# Check API key configuration
uv run python -c "from src.config.settings import get_settings; s = get_settings(); print(s.get_secret_or_env('GEMINI_API_KEY')[:10])"

# Regenerate API key at https://aistudio.google.com/app/apikey
```

### Low Confidence Scores

- **Cause**: Email missing key information or ambiguous language
- **Solution**: Review flagged fields manually, update email source if possible
- **Threshold**: Adjust `--threshold` flag (default: 0.85)

### Korean Date Parsing Issues

```bash
# Test date parsing separately
uv run python -c "import dateparser; print(dateparser.parse('11월 1주'))"

# Known limitation: Week notation requires custom handler
# Supported: "11월 1일", "2025년 1월 15일", "yesterday"
```

---

## Next Steps

After testing extraction:

1. **Manual Notion Entry**: Copy JSON output to create Notion database entries manually (MVP workflow)
2. **Accuracy Validation**: Compare extraction results against ground truth (see tests/fixtures/ground_truth/GROUND_TRUTH.md)
3. **Production Testing**: Process real emails from `data/cleaned/` (Phase 1a output)

---

## Further Reading

- [Data Model](data-model.md) - Entity definitions and validation rules
- [API Contracts](contracts/llm_provider.yaml) - LLMProvider interface specification
- [Research](research.md) - Technical decisions and alternatives considered
- [Implementation Plan](plan.md) - Full feature implementation plan

---

**Quick Start Complete**: ✅
**MVP Workflow**: Extract entities → Manually create Notion entries (≤2 minutes per email)
