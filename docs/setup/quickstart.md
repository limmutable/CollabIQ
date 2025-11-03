# CollabIQ Quick Start Guide

This guide will walk you through setting up CollabIQ for the first time.

## Prerequisites

Before starting, ensure you have:

1. **Python 3.12 or higher** installed
2. **UV package manager** ([install here](https://github.com/astral-sh/uv))
3. **Gmail API credentials** (Phase 1a complete - email reception) - See [Gmail OAuth Setup Guide](gmail-oauth-setup.md)
4. **Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey) (Phase 1b complete - entity extraction)
5. **Notion API integration token and database IDs** (Phase 2a complete - Notion read operations)
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
- ✅ **Phase 2b Complete**: LLM-based company matching with confidence scores
- 🚧 **Phase 2c (Next)**: Classification & Summarization

See [docs/architecture/ROADMAP.md](../architecture/ROADMAP.md) for full implementation timeline.

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
uv run collabiq verify-infisical
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

# Gemini API Configuration (✅ Implemented - Phase 1b + 2b)
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash  # Updated model for Phase 2b
GEMINI_TIMEOUT_SECONDS=10
GEMINI_MAX_RETRIES=3

# Notion API Configuration (✅ Implemented - Phase 2a)
NOTION_API_KEY=secret_...your_actual_token_here
NOTION_DATABASE_ID_COMPANIES=32_character_database_id_here
NOTION_DATABASE_ID_COLLABIQ=32_character_database_id_here

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

## Next Steps

### Current Status (Completed Phases)

✅ **Phase 1a Complete**: Email reception with Gmail API OAuth2
✅ **Phase 1b Complete**: Gemini entity extraction (100% accuracy)
✅ **Phase 005 Complete**: Gmail OAuth2 setup with group alias support
✅ **Phase 2a Complete**: Notion Read Operations (schema discovery, data fetching, LLM formatting)
✅ **Phase 2b Complete**: LLM-based company matching with confidence scores (100% accuracy)
🎯 **MVP Complete**: Email ingestion + entity extraction + company matching + JSON output

### Next Implementation Phase

**Phase 2c: Classification & Summarization**

This phase will add automated email classification and collaborative content summarization.

See [docs/architecture/ROADMAP.md](../architecture/ROADMAP.md) for Phase 2c details.

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
uv run collabiq verify-infisical

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
- Rate limit exceeded (wait and retry)
- Model not available (check model name in .env)

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
uv run collabiq verify-infisical

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

## What's Next?

After completing this quick start, you should:
1. ✅ Have a working Python environment with UV
2. ✅ Have valid Gmail OAuth2 credentials configured
3. ✅ Have valid Gemini API key configured
4. ✅ Have valid Notion API credentials configured
5. ✅ Be able to fetch and extract entities from emails
6. ✅ Be able to fetch and format Notion data for LLM consumption
7. ✅ Understand the project structure

Now you're ready to:
- **Use the MVP**: Fetch emails and extract entities with company matching
- **Test real emails**: Run Phase 2b tests with actual collab@signite.co emails
- **Fetch Notion Data**: Retrieve company data with LLM-ready formatting
- **Explore Phase 2b**: Review company matching implementation
- **Start Phase 2c**: Implement classification and summarization
- **Add more features**: Follow the implementation roadmap

Welcome to CollabIQ! 🚀

---

**Quick Reference**:
- Setup Guides: [docs/setup/](.)
- Architecture Docs: [docs/architecture/](../architecture/)
- Data Output: `data/extractions/*.json`
- Test Suite: `make test`
