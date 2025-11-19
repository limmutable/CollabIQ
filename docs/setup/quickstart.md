# CollabIQ Quick Start Guide

This guide will walk you through setting up CollabIQ for the first time.

## Prerequisites

Before starting, ensure you have:

1. **Python 3.12 or higher** installed
2. **UV package manager** ([install here](https://github.com/astral-sh/uv))
3. **Gmail API credentials** (Phase 1a complete - email reception) - See [Gmail OAuth Setup Guide](gmail-oauth-setup.md)
4. **At least one LLM API key** (recommended: all three for failover):
   - **Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey) (free tier available)
   - **Anthropic API key** from [Anthropic Console](https://console.anthropic.com/) (optional for failover)
   - **OpenAI API key** from [OpenAI Platform](https://platform.openai.com/api-keys) (optional for failover)
5. **Notion API integration token and database IDs** (Phase 2a complete - Notion read operations + Phase 2c schema fetching)
6. **(Optional)** [Infisical](https://infisical.com) account for centralized secret management (recommended for teams) - See [Infisical Setup Guide](infisical-setup.md)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repo-url>
cd CollabIQ

# Install dependencies using UV
make install

# Or manually:
uv sync
```

This will:
- Create a virtual environment in `.venv/`
- Install all Python dependencies
- Set up development tools (pytest, ruff, mypy)

## Step 2: Verify Installation

Verify your Python and UV installation:

```bash
# Check Python version (should be 3.12+)
python --version

# Check UV installation
uv --version

# Verify virtual environment
ls .venv/

# Verify CLI is working
uv run collabiq --help
```

### Running Commands: Two Options

**Option 1: Use `uv run` (Recommended)**
```bash
# UV automatically activates the virtual environment
uv run python scripts/authenticate_gmail.py
uv run collabiq --help
uv run pytest
```

**Option 2: Activate Virtual Environment Manually**
```bash
# Activate the virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

# Now you can run commands directly
python scripts/authenticate_gmail.py
collabiq --help
pytest

# Deactivate when done
deactivate
```

**💡 Tip**: `uv run` is recommended because it:
- Automatically uses the correct Python version
- No need to manually activate/deactivate
- Works consistently across all platforms

**Current Status**:
- ✅ **Phase 1a Complete**: Email reception with Gmail API OAuth2
- ✅ **Phase 1b Complete**: Gemini entity extraction (100% accuracy on test dataset)
- ✅ **Phase 005 Complete**: Gmail OAuth2 setup with group alias support
- ✅ **Phase 2a Complete**: Notion Read Operations (schema discovery, data fetching, LLM formatting)
- ✅ **Phase 2b Complete**: LLM-based company matching with confidence scores (100% accuracy)
- ✅ **Phase 2c Complete**: Classification & Summarization (type, intensity, summary generation)
- ✅ **Phase 2d Complete**: Notion Write Operations (duplicate detection, DLQ handling)
- ✅ **Phase 2e Complete**: Error Handling & Retry Logic (unified retry system with circuit breakers)
- ✅ **Phase 3a Complete**: Admin CLI Enhancement (30+ commands across 7 groups)
- ✅ **Phase 3b Complete**: Multi-LLM Provider Support (Gemini/Claude/OpenAI with failover, consensus, best-match)
- ✅ **Phase 013 Complete**: Quality Metrics & Intelligent Routing (track quality, compare providers, quality-based routing)
- 🎯 **Production Status**: READY - Full automation with multi-LLM resilience, quality-based routing, and cost/performance tracking

**Error Handling**: CollabIQ includes comprehensive error handling with automatic retry logic:
- **Automatic Retries**: Transient failures (timeouts, rate limits) retry automatically with exponential backoff
- **Circuit Breakers**: Prevents cascading failures by failing fast when services are degraded
- **Dead Letter Queue (DLQ)**: Failed operations are preserved for later replay via `scripts/retry_dlq.py`
- **Structured Logging**: All errors logged with full context for debugging (JSON-formatted)
- **Service-Specific Configs**: Pre-configured retry settings for Gmail, Gemini, Notion, and Infisical

See [src/error_handling/README.md](../../src/error_handling/README.md) for usage guide and [docs/architecture/ROADMAP.md](../architecture/ROADMAP.md) for full implementation timeline.

## Step 3: Configure Environment

You have two options for managing secrets:

### Option A: Infisical (Recommended for Teams)

**Benefits:**
- ✅ No API keys in `.env` files (secure)
- ✅ Environment isolation (development/production)
- ✅ Centralized secret rotation
- ✅ Team onboarding without manual key sharing

**Setup** (10-15 minutes):

1. Get Infisical machine identity credentials from your team lead
2. Configure `.env` with Infisical settings:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and configure Infisical
INFISICAL_ENABLED=true
INFISICAL_PROJECT_ID=your-project-id
INFISICAL_ENVIRONMENT=development
INFISICAL_CLIENT_ID=machine-identity-abc123
INFISICAL_CLIENT_SECRET=secret-xyz789
```

3. Verify connection:
```bash
# Application will automatically fetch secrets from Infisical
uv run collabiq config test-secrets
```

**📖 Full Infisical Setup Guide:** [docs/setup/infisical-setup.md](infisical-setup.md)

### Option B: Local .env File

For local development or if you prefer managing secrets directly:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Fill in the required values:

```bash
# Disable Infisical (for local development)
INFISICAL_ENABLED=false

# Gmail API Configuration (✅ Implemented - Phase 1a + 005)
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_BATCH_SIZE=50

# Gemini API Configuration (✅ Implemented - Phase 1b + 2b + 2c)
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash  # Latest model (2025)
GEMINI_TIMEOUT_SECONDS=60
# Note: Retry logic is handled automatically by Phase 010 error handling system

# Notion API Configuration (✅ Implemented - Phase 2a + 2d)
NOTION_API_KEY=secret_...your_actual_token_here
NOTION_DATABASE_ID_COMPANIES=32_character_database_id_here
NOTION_DATABASE_ID_COLLABIQ=32_character_database_id_here
NOTION_DUPLICATE_STRATEGY=skip  # or 'update' to overwrite duplicates

# Logging
LOG_LEVEL=INFO

# Processing Configuration (✅ Implemented - Phase 2b)
CONFIDENCE_THRESHOLD=0.70  # Min confidence for company matching
```

## Step 4: Verify Configuration

Test that your configuration is valid:

```bash
uv run python -c "from src.config.settings import get_settings; settings = get_settings(); print(f'Gmail batch size: {settings.gmail_batch_size}'); print(f'Log level: {settings.log_level}'); print(f'Infisical enabled: {settings.infisical_enabled}')"
```

Expected output:
```
Gmail batch size: 50
Log level: INFO
Infisical enabled: False  # or True if you configured Infisical
```

## Step 5: Setup Gmail OAuth2 (Required)

Follow the Gmail OAuth2 setup guide to configure email access:

```bash
# See detailed setup instructions
cat docs/setup/gmail-oauth-setup.md
```

**Quick Steps**:
1. Create OAuth2 credentials in Google Cloud Console
2. Download `credentials.json` to project root
3. Run authentication flow: `uv run python scripts/authenticate_gmail.py`
4. Authenticate as a **group member** (e.g., jeffreylim@signite.co), NOT as collab@signite.co
5. Verify: `token.json` should be created after successful authentication

**⚠️ IMPORTANT**: collab@signite.co is a Google Group, not a mailbox. You must authenticate as a group member.

**Full Guide**: [docs/setup/gmail-oauth-setup.md](gmail-oauth-setup.md)

## Step 6: Setup Gemini API (Required)

Get your Gemini API key and add it to `.env`:

```bash
# Get API key from: https://makersuite.google.com/app/apikey
echo "GEMINI_API_KEY=AIzaSy...your_actual_key_here" >> .env
```

**Note**: If using Infisical, add the key to your Infisical project instead.

## Step 7: Run Tests

Ensure everything is working:

```bash
# Run all tests
make test

# Or with coverage
uv run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Expected Results**:
- ✅ All unit tests should pass (90+ tests)
- ✅ Integration tests for Gmail and Gemini APIs
- ✅ End-to-end extraction pipeline tests

## Step 8: Test the System

### Test Gmail Retrieval

Test Gmail API connection and email retrieval:

```bash
# Test Gmail retrieval from collab@signite.co
uv run python tests/manual/test_gmail_retrieval.py --max-results 5
```

### Test Phase 1b (Entity Extraction)

Test entity extraction without company matching:

```bash
# Run end-to-end Phase 1b test
uv run python tests/manual/test_e2e_phase1b.py --max-emails 2
```

**What happens**:
1. Connects to Gmail API via OAuth2
2. Fetches emails from `collab@signite.co` using `to:collab@signite.co` filter
3. Cleans email content (removes signatures, quotes)
4. Extracts entities using Gemini API
5. Displays results with extracted entities (담당자, 스타트업명, 협업기관, 날짜)

### Test Phase 2b (Company Matching)

Test entity extraction WITH company matching:

```bash
# Run end-to-end Phase 2b test with real emails
uv run python tests/manual/test_e2e_phase2b.py --limit 3
```

**What happens**:
1. Fetches recent emails from collab@signite.co
2. Fetches company data from Notion (portfolio + SSG affiliates)
3. Cleans and normalizes email content
4. Extracts entities WITH company matching using Gemini
5. Shows matched company IDs with confidence scores
6. Compares Phase 1b vs Phase 2b results
7. Saves results to `data/test_results/phase2b_real_emails_*.json`

### Test Phase 2c (Classification & Summarization)

Test the full classification workflow with type, intensity, and summary generation:

```bash
# Run Phase 2c classification demo
uv run python tests/manual/test_phase2c_classification.py
```

**What happens**:
1. Loads sample email (sample-001.txt from test fixtures)
2. Fetches collaboration types dynamically from Notion "협업형태" property
3. Extracts entities using Gemini API
4. Classifies collaboration type deterministically based on company relationships:
   - Portfolio + SSG Affiliate → [A]PortCoXSSG (95% confidence)
   - Portfolio + Portfolio → [C]PortCoXPortCo (95% confidence)
   - Portfolio + External → [B]Non-PortCoXSSG (90% confidence)
   - Non-Portfolio → [D]Other (80% confidence)
5. Classifies intensity using LLM Korean semantic analysis (이해/협력/투자/인수)
6. Generates 3-5 sentence summary preserving all 5 key entities
7. Displays confidence scores and manual review routing decision
8. Shows JSON serialization of complete result

**Example Output**:
```json
{
  "person_in_charge": "안동훈",
  "startup_name": "브레이크앤컴퍼니",
  "partner_org": "신세계푸드",
  "details": "PoC 킥오프",
  "date": "2025-10-28T00:00:00",
  "collaboration_type": "[A]PortCoXSSG",
  "type_confidence": 0.95,
  "collaboration_intensity": "협력",
  "intensity_confidence": 0.92,
  "intensity_reasoning": "PoC 킥오프 미팅과 파일럿 테스트 계획이 논의되어 협력 단계로 분류",
  "collaboration_summary": "브레이크앤컴퍼니(안동훈 팀장)와 신세계푸드가 2025년 10월 28일 PoC 킥오프 미팅 진행 완료...",
  "summary_word_count": 85,
  "key_entities_preserved": {
    "person_in_charge": true,
    "startup_name": true,
    "partner_org": true,
    "details": true,
    "date": true
  },
  "needs_manual_review": false
}
```

### Test Notion Integration (Phase 2a)

Test Notion data fetching and formatting:

```bash
# Fetch data from Notion databases
uv run collabiq notion fetch

# View database schema
uv run collabiq notion schema YOUR_COMPANIES_DB_ID

# Refresh cached data
uv run collabiq notion refresh YOUR_COMPANIES_DB_ID

# Export to JSON file
uv run collabiq notion export --output companies.json
```

**What happens**:
1. Connects to Notion API via integration token
2. Discovers database schema dynamically
3. Fetches all records with pagination
4. Resolves relationships (1-level depth)
5. Formats data for LLM consumption (JSON + Markdown)
6. Caches results (24h schema, 6h data)

**Output**:
- JSON format: Structured company records with all properties
- Markdown format: Human-readable summary with company classifications
- Cache location: `data/cache/*.json`

## Step 9: Quality Metrics & Intelligent Routing

### Test Quality Metrics (Phase 013)

Test quality tracking and provider comparison:

```bash
# Check current system status
collabiq llm status

# Compare provider performance
collabiq llm compare --detailed

# Export all metrics to JSON file
collabiq llm export-metrics

# Export only quality metrics
collabiq llm export-metrics -o quality_report.json --no-health --no-cost

# Test with specific email ID
uv run python test_specific_email.py --email-id "test_001" --show-metrics
```

**What happens**:
1. Tracks extraction quality automatically (confidence, completeness, validation)
2. Compares providers using composite scoring:
   - **Quality Score**: 40% confidence + 30% completeness + 30% validation
   - **Value Score**: quality-to-cost ratio (considers free tier vs paid)
3. Routes requests to optimal provider based on historical performance
4. Falls back to next provider if primary fails or is unhealthy

**Example Output**:
```
Quality Rankings:
1. Claude   - Quality: 0.85 (85% confidence, 90% completeness, 100% validation)
2. Gemini   - Quality: 0.82 (80% confidence, 85% completeness, 95% validation)
3. OpenAI   - Quality: 0.78 (75% confidence, 80% completeness, 90% validation)

Value Rankings (Quality-to-Cost):
1. Gemini   - Value: 1.23 (Free tier: 1.5x multiplier)
2. Claude   - Value: 8.10 (Quality 0.85 / Cost $0.105)
3. OpenAI   - Value: 346.67 (Quality 0.78 / Cost $0.00225)

Recommendation: Claude (highest quality, acceptable cost)
```

### Enable Quality-Based Routing

Turn on intelligent provider selection:

```bash
# Enable quality-based routing
collabiq llm set-quality-routing --enabled

# Test with quality routing
collabiq llm test "Your email text here" --quality-routing

# Switch orchestration strategy
collabiq llm set-strategy consensus  # or: failover, best_match
```

**Routing Logic**:
- **Enabled**: Selects provider with highest historical quality score
- **Disabled**: Uses fixed priority order (Gemini → Claude → OpenAI)
- **No metrics**: Falls back to priority order automatically

### View Quality Metrics

Check stored metrics and trends:

```bash
# View quality metrics file
cat data/llm_health/quality_metrics.json

# View cost tracking
cat data/llm_health/cost_metrics.json

# Show metrics in test script
uv run python test_specific_email.py --email-id "test_002" --show-metrics
```

**Metrics Tracked**:
- Per-provider extraction counts
- Confidence averages (overall + per-field)
- Field completeness percentages
- Validation success rates
- Total cost and cost-per-email
- Token usage (input/output/total)

**See Also**: [docs/cli/CLI_REFERENCE.md](../cli/CLI_REFERENCE.md) for complete CLI command reference

## Next Steps

### Current Status (Completed Phases)

✅ **Phase 1a Complete**: Email reception with Gmail API OAuth2
✅ **Phase 1b Complete**: Gemini entity extraction (100% accuracy)
✅ **Phase 005 Complete**: Gmail OAuth2 setup with group alias support
✅ **Phase 2a Complete**: Notion Read Operations (schema discovery, data fetching, LLM formatting)
✅ **Phase 2b Complete**: LLM-based company matching with confidence scores (100% accuracy)
✅ **Phase 2c Complete**: Classification & Summarization
  - Dynamic type classification (Portfolio+SSG → [A]PortCoXSSG)
  - LLM-based intensity classification (이해/협력/투자/인수)
  - Summary generation (3-5 sentences, preserves 5 key entities)
  - Confidence scoring with 0.85 threshold for manual review routing
✅ **Phase 2d Complete**: Notion Write Operations
  - Duplicate detection with configurable strategies (skip/update)
  - Schema-aware property mapping via FieldMapper
  - Dead Letter Queue (DLQ) for failed writes
  - Retry script for manual DLQ replay (`scripts/retry_dlq.py`)
✅ **Phase 010 Complete**: Error Handling & Retry Logic
  - Unified `@retry_with_backoff` decorator replacing ad-hoc retry logic
  - Circuit breaker pattern for Gmail, Gemini, Notion, and Infisical
  - Structured error logging with JSON formatting
  - Service-specific retry configurations (timeouts, attempts, jitter)
  - Rate limit handling with `Retry-After` header support
✅ **Phase 011 Complete**: Admin CLI (30+ commands for system management)
✅ **Phase 012 Complete**: Multi-LLM Support (Claude, OpenAI, Gemini with failover)
✅ **Phase 013 Complete**: Quality Metrics & Intelligent Routing
  - Automatic quality tracking (confidence, completeness, validation)
  - Provider comparison with composite scoring
  - Quality-based routing with cost optimization
  - Cost tracking with per-provider metrics

🎯 **Production Status**: READY - Full automation with multi-LLM resilience, quality-based routing, and cost/performance tracking

### Next Steps: Production & Monitoring

With the MVP complete, the focus shifts to:

1. **Production Deployment**
   - Deploy to Cloud Run or similar serverless platform
   - Configure production Infisical environment
   - Set up monitoring and alerting

2. **Monitoring & Observability**
   - DLQ monitoring dashboard
   - Circuit breaker state tracking
   - Error rate and retry metrics
   - Performance monitoring (latency, throughput)

3. **Operational Workflows**
   - Scheduled email processing (e.g., hourly cron job)
   - Manual DLQ replay workflow
   - Secret rotation procedures
   - Backup and disaster recovery

See [docs/architecture/ROADMAP.md](../architecture/ROADMAP.md) for the complete implementation timeline and future phases.

### Explore the System

```bash
# View system architecture
cat docs/architecture/ARCHITECTURE.md

# View implementation roadmap
cat docs/architecture/ROADMAP.md

# View test data and extraction results
ls data/extractions/

# View cleaned email data
ls data/cleaned/

# Explore source code structure
tree src/
```

### Validate Current Setup

```bash
# Verify Infisical integration (if enabled)
uv run collabiq config test-secrets

# Check CLI version
uv run collabiq version

# Run full test suite
make test
```

## Troubleshooting

### "Module not found" errors
```bash
# Ensure you're using UV's python
uv run python your_script.py

# Or activate the virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Virtual environment warnings
```bash
# If you see: warning: `VIRTUAL_ENV=venv` does not match...
# Either remove the old venv directory:
rm -rf venv
unset VIRTUAL_ENV

# Or ignore the warning (UV will use .venv correctly anyway)
```

### "Configuration errors"
```bash
# Check .env file exists
ls -la .env

# Check settings are loading correctly
uv run python -c "from src.config.settings import get_settings; settings = get_settings(); print(f'Log level: {settings.log_level}'); print(f'Infisical: {settings.infisical_enabled}')"
```

### Gmail API Authentication Errors

See the detailed troubleshooting guide: [docs/setup/troubleshooting-gmail-api.md](troubleshooting-gmail-api.md)

**Common Issues**:
- OAuth redirect URI mismatch
- Invalid or expired credentials
- Missing Gmail API scope permissions

### Gemini API Errors

```bash
# Test Gemini API connection
uv run python -c "from src.llm_provider.gemini_adapter import GeminiAdapter; adapter = GeminiAdapter(); print('✅ Gemini API configured')"
```

**Common Issues**:
- Invalid API key
- Rate limit exceeded (automatically retried with exponential backoff via Phase 010 error handling)
- Model not available (check model name in .env)

**Note**: Gemini API calls automatically retry on transient failures (timeouts, rate limits, server errors) using the unified retry system from Phase 010. See [src/error_handling/README.md](../../src/error_handling/README.md) for details.

### "Tests failing"
```bash
# Clean cache and reinstall
make clean
rm -rf .venv/
make install

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_gemini_adapter.py -v
```

### Dead Letter Queue (DLQ) Management

The DLQ stores failed write operations for later replay. Check and replay failed operations:

```bash
# Check DLQ directory for failed operations
ls -la data/dlq/

# View a specific DLQ entry (JSON format)
cat data/dlq/notion_write_YYYYMMDD_HHMMSS_*.json

# Replay ALL failed operations
uv run python scripts/retry_dlq.py

# Replay specific failed operation
uv run python scripts/retry_dlq.py --file data/dlq/notion_write_*.json

# Check DLQ replay logs
tail -f logs/email_processor.log | grep DLQ
```

**Common DLQ Scenarios**:
- **Notion API rate limits**: Automatic retry after rate limit window expires
- **Temporary network issues**: Retry after connectivity restored
- **Schema changes**: May require manual field mapping updates before retry
- **Duplicate detection**: Entries marked as duplicates are logged but not retried

**DLQ Best Practices**:
- Monitor `data/dlq/` directory regularly (set up file count alerts)
- Review failed entries before replaying (validate data quality)
- Schedule periodic DLQ replay (e.g., daily cron job)
- Clean up successfully replayed entries to avoid clutter

### Circuit Breaker Issues

If a service circuit breaker is stuck in OPEN state (failing fast):

```bash
# Check circuit breaker state in logs
tail -f logs/email_processor.log | grep "Circuit breaker"

# Wait for recovery timeout (60s for main services, 30s for Infisical)
# Or restart the application to reset all circuit breakers
```

**Circuit Breaker States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Too many failures, requests fail immediately (fail fast)
- **HALF_OPEN**: Testing if service recovered, limited requests allowed

## Getting Help

- **Gmail Setup Issues**: See [docs/setup/gmail-oauth-setup.md](gmail-oauth-setup.md) and [docs/setup/troubleshooting-gmail-api.md](troubleshooting-gmail-api.md)
- **Infisical Setup**: See [docs/setup/infisical-setup.md](infisical-setup.md)
- **Architecture Questions**: See [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- **Implementation Plan**: See [docs/architecture/ROADMAP.md](../architecture/ROADMAP.md)
- **SpecKit Commands**: Run `ls .claude/commands/` to see available workflows

## Development Workflow

```bash
# Daily workflow
make format    # Format code with ruff
make lint      # Check for issues
make test      # Run tests
git add .
git commit     # Pre-commit hooks will run automatically
```

## Available CLI Commands

### Main CLI (collabiq)

```bash
# Verify Infisical integration (checks Gmail, Gemini, Notion secrets)
uv run collabiq config test-secrets

# Show CLI version
uv run collabiq version

# Notion commands (Phase 2a)
uv run collabiq notion fetch              # Fetch data from Notion databases
uv run collabiq notion schema <DATABASE_ID>  # View database schema
uv run collabiq notion refresh <DATABASE_ID> # Refresh cached data
uv run collabiq notion export --output <file>     # Export to JSON file
```

### Legacy CLI (src/cli.py)

```bash
# Fetch and process emails
uv run python src/cli.py fetch --max-results 10

# Clean existing raw emails
uv run python src/cli.py clean-emails --input-dir data/raw

# Verify setup
uv run python src/cli.py verify
```

### Error Handling & DLQ Scripts

```bash
# Replay ALL failed operations from Dead Letter Queue
uv run python scripts/retry_dlq.py

# Replay specific DLQ entry
uv run python scripts/retry_dlq.py --file data/dlq/notion_write_*.json

# Diagnose Infisical connectivity
uv run python scripts/diagnose_infisical.py

# Check where secrets are loaded from (Infisical vs .env)
uv run python scripts/check_secret_source.py

# Clean up test entries from Notion (use with caution!)
uv run python scripts/cleanup_test_entries.py
```

## What's Next?

After completing this quick start, you should:
1. ✅ Have a working Python environment with UV
2. ✅ Have valid Gmail OAuth2 credentials configured
3. ✅ Have valid Gemini API key configured
4. ✅ Have valid Notion API credentials configured
5. ✅ Be able to fetch and extract entities from emails
6. ✅ Be able to fetch and format Notion data for LLM consumption
7. ✅ Be able to classify collaboration types and intensity
8. ✅ Be able to generate summaries preserving key entities
9. ✅ Be able to write results to Notion with duplicate detection
10. ✅ Understand error handling with automatic retries and circuit breakers
11. ✅ Understand the project structure

Now you're ready to:
- **Use the Full MVP Pipeline**: Fetch emails → extract entities → match companies → classify type/intensity → generate summaries → write to Notion
- **Test the Complete Flow**: Run end-to-end tests to see the full pipeline in action
- **Explore Error Handling**: Review retry logic, circuit breakers, and DLQ management
- **Monitor DLQ**: Check `data/dlq/` for failed operations and replay them with `scripts/retry_dlq.py`
- **Review Confidence Scores**: Understand auto-acceptance vs manual review routing
- **Production Planning**: Prepare for deployment with monitoring and operational workflows
- **Add more features**: Follow the implementation roadmap for future phases

Welcome to CollabIQ! 🚀

---

**Quick Reference**:
- Setup Guides: [docs/setup/](.)
- Architecture Docs: [docs/architecture/](../architecture/)
- Data Output: `data/extractions/*.json`
- Test Suite: `make test`
