# CollabIQ Quick Start Guide

This guide will walk you through setting up CollabIQ for the first time.

## Prerequisites

Before starting, ensure you have:

1. **Python 3.12 or higher** installed
2. **UV package manager** ([install here](https://github.com/astral-sh/uv))
3. **Gmail API credentials** (Phase 1a complete - email reception) - See [Gmail OAuth Setup Guide](gmail-oauth-setup.md)
4. **Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey) (Phase 1b complete - entity extraction)
5. **(Optional)** [Infisical](https://infisical.com) account for centralized secret management (recommended for teams) - See [Infisical Setup Guide](infisical-setup.md)
6. **(Future)** Notion integration token and database IDs (Phase 2 - not yet implemented)

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

**Current Status**:
- ✅ **Phase 1a Complete**: Email reception with Gmail API OAuth2
- ✅ **Phase 1b Complete**: Gemini entity extraction
- ✅ **Phase 005 Complete**: Gmail OAuth2 setup with group alias support
- 🚧 **Phase 2**: Notion integration (not yet implemented)

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

# Gemini API Configuration (✅ Implemented - Phase 1b)
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TIMEOUT_SECONDS=10
GEMINI_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO

# Future: Notion API (Phase 2 - Not Yet Implemented)
# NOTION_API_KEY=secret_...your_actual_token_here
# NOTION_DATABASE_ID_COLLABIQ=32_character_database_id_here
# NOTION_DATABASE_ID_CORP=32_character_database_id_here

# Future: Processing Configuration (Phase 2+ - Not Yet Implemented)
# FUZZY_MATCH_THRESHOLD=0.85
# CONFIDENCE_THRESHOLD=0.85
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
3. Run authentication flow: `uv run collabiq fetch`
4. Verify: `token.json` should be created after successful authentication

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

Test the complete email extraction pipeline:

```bash
# Fetch and extract entities from emails
uv run collabiq fetch

# Or use the old CLI (also available)
uv run python src/cli.py fetch --max-results 10
```

**What happens**:
1. Connects to Gmail API via OAuth2
2. Fetches emails from `collab@signite.co`
3. Cleans email content (removes signatures, quotes)
4. Extracts entities using Gemini API
5. Saves results to `data/extractions/*.json`

**Output Location**:
- Raw emails: `data/raw/YYYY/MM/*.json`
- Cleaned emails: `data/cleaned/YYYY/MM/*.json`
- Extracted entities: `data/extractions/*.json`

## Next Steps

### Current Status (Completed Phases)

✅ **Phase 1a Complete**: Email reception with Gmail API OAuth2
✅ **Phase 1b Complete**: Gemini entity extraction
✅ **Phase 005 Complete**: Gmail OAuth2 setup with group alias support
🎯 **MVP Complete**: Email ingestion + entity extraction + JSON output

### Next Implementation Phase

**Phase 2: Notion Integration** (Not Yet Started)

This phase will add automatic Notion database creation from extracted entities.

```bash
# When ready to start Phase 2
git checkout -b 006-notion-integration
/speckit.specify "Implement Notion integration for automatic entity creation"
```

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

```bash
# Verify Infisical integration
uv run collabiq verify-infisical

# Show CLI version
uv run collabiq version

# Fetch and process emails (not yet implemented in main CLI)
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
4. ✅ Be able to fetch and extract entities from emails
5. ✅ Understand the project structure

Now you're ready to:
- **Use the MVP**: Fetch emails and extract entities to JSON
- **Start Phase 2**: Implement Notion integration
- **Explore the codebase**: Review existing implementations
- **Add more features**: Follow the implementation roadmap

Welcome to CollabIQ! 🚀

---

**Quick Reference**:
- Setup Guides: [docs/setup/](.)
- Architecture Docs: [docs/architecture/](../architecture/)
- Data Output: `data/extractions/*.json`
- Test Suite: `make test`
