# CollabIQ Quick Start Guide

This guide will walk you through setting up CollabIQ for the first time.

## Prerequisites

Before starting, ensure you have:

1. **Python 3.12 or higher** installed
2. **UV package manager** ([install here](https://github.com/astral-sh/uv))
3. **Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
4. **Notion integration token** and database IDs
5. **(Optional)** [Infisical](https://infisical.com) account for centralized secret management (recommended for teams)

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

## Step 2: Get Your API Keys

### Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### Notion API Token

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Give it a name (e.g., "CollabIQ")
4. Select the workspace
5. Copy the "Internal Integration Token" (starts with `secret_...`)

### Notion Database IDs

You need the IDs for two databases:
- **CollabIQ** - Main collaboration tracking database
- **Company Database** - Unified database containing all companies: startups, portfolio companies, and Shinsegate affiliates (this consolidates what were previously separate startup and affiliate databases)

To get a database ID:
1. Open the database in Notion
2. Click "..." → "Copy link"
3. Extract the ID from the URL:
   ```
   https://www.notion.so/workspace/<DATABASE_ID>?v=...
                                   ^^^ This 32-character string
   ```

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
# Disable Infisical
INFISICAL_ENABLED=false

# Required: Gemini API
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash

# Required: Notion API
NOTION_API_KEY=secret_...your_actual_token_here
NOTION_DATABASE_ID_COLLABIQ=32_character_database_id_here
NOTION_DATABASE_ID_CORP=32_character_database_id_here

# Optional: Email Infrastructure (set up later)
# For now, you can leave these as placeholder values

# Processing Configuration (defaults are fine)
FUZZY_MATCH_THRESHOLD=0.85
CONFIDENCE_THRESHOLD=0.85
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5

# Logging
LOG_LEVEL=INFO
```

## Step 4: Verify Configuration

Test that your configuration is valid:

```bash
uv run python -c "from config.settings import settings; print(f'Gemini: {settings.gemini_model}'); print(f'Notion: {settings.notion_api_key[:20]}...')"
```

Expected output:
```
Gemini: gemini-2.5-flash
Notion: secret_abc123...
```

## Step 5: Run Tests

Ensure everything is working:

```bash
# Run all tests
make test

# Or with coverage
uv run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Step 6: Validate Notion Connection (Phase 1 Feasibility)

Before proceeding with implementation, validate your Notion setup:

```bash
# TODO: This script will be created in Phase 1b
uv run python scripts/validate_notion.py
```

This script should:
- ✅ Connect to Notion API
- ✅ Find all three databases
- ✅ Read sample entries from each database
- ✅ Verify database schema matches expectations

## Step 7: Validate Gemini API (Phase 1 Feasibility)

Test the Gemini API with a sample email:

```bash
# TODO: This script will be created in Phase 1a
uv run python scripts/validate_gemini.py
```

This script should:
- ✅ Connect to Gemini API
- ✅ Extract entities from a sample Korean email
- ✅ Return confidence scores above threshold
- ✅ Handle edge cases (English, mixed language, forwarded emails)

## Step 8: Choose Email Infrastructure (Phase 1c)

You'll need to choose one of three approaches:

### Option 1: Gmail API (Recommended for Development)
- **Pros**: Official API, rich metadata, easy local testing
- **Cons**: OAuth2 setup required
- **Setup**: See `specs/001-feasibility-architecture/email-infrastructure-comparison.md`

### Option 2: IMAP
- **Pros**: Simple, works with any email provider
- **Cons**: Polling-based, may miss emails
- **Setup**: Use app-specific password for `portfolioupdates@signite.co`

### Option 3: Webhook (Recommended for Production)
- **Pros**: Real-time, scalable, no polling
- **Cons**: Requires public endpoint, provider-specific setup
- **Setup**: Configure in Gmail/Google Workspace admin

For now, you can skip this step - it's needed for Phase 1c.

## Next Steps

### If You're Following the Implementation Roadmap:

1. **Complete Phase 0 Feasibility** (Manual):
   - Follow `specs/001-feasibility-architecture/research-template.md`
   - Test Gemini API with real Korean emails
   - Validate Notion database structure
   - Choose email infrastructure approach
   - Document findings

2. **Start Phase 1a: LLM Provider Core** (Branch 002-llm-provider):
   ```bash
   git checkout -b 002-llm-provider
   /speckit.specify "Implement LLMProvider abstraction layer and GeminiAdapter"
   ```

3. **Continue with Phase 1b: Notion Integrator** (Branch 003-notion-integrator)

4. **Build Phase 1c: Email Receiver Prototype** (Branch 004-email-receiver)

### If You're Exploring the Codebase:

```bash
# View system architecture
cat docs/architecture/ARCHITECTURE.md

# View implementation roadmap
cat docs/architecture/ROADMAP.md

# View API contracts
cat docs/architecture/API_CONTRACTS.md

# Explore project structure
tree src/
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

### "API key not found" errors
```bash
# Check .env file exists
ls -la .env

# Check settings are loading
uv run python -c "from config.settings import settings; print(settings.gemini_api_key[:10])"
```

### "Notion API errors"
- Ensure your integration has access to the databases
- In Notion, click "..." on each database → "Connections" → Add your integration
- Verify database IDs are correct (32 characters, no spaces)

### "Tests failing"
```bash
# Clean cache and reinstall
make clean
rm -rf .venv/
make install

# Run tests with verbose output
uv run pytest -v
```

## Getting Help

- **Architecture Questions**: See [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- **Implementation Plan**: See [docs/architecture/ROADMAP.md](../architecture/ROADMAP.md)
- **API Contracts**: See [docs/architecture/API_CONTRACTS.md](../architecture/API_CONTRACTS.md)
- **SpecKit Commands**: Run `ls .claude/commands/` to see available workflows

## Development Workflow

```bash
# Daily workflow
make format    # Format code
make lint      # Check for issues
make test      # Run tests
git add .
git commit     # Pre-commit hooks will run automatically
```

## What's Next?

After completing this quick start, you should:
1. ✅ Have a working Python environment with UV
2. ✅ Have valid Gemini and Notion API keys configured
3. ✅ Understand the project structure
4. ✅ Be able to run tests

Now you're ready to either:
- **Complete Phase 0 Feasibility Testing** using the research template
- **Start implementing Phase 1a** (LLM Provider Core)
- **Explore the codebase** and documentation

Welcome to CollabIQ! 🚀
