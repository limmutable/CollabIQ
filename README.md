# CollabIQ

Email-based collaboration tracking system that automatically extracts collaboration activities from Korean/English emails and syncs them to Notion databases.

## Project Status

**Current Phase**: Phase 2b Complete ✅ (Branch 007-llm-matching)

### Completed Phases
- ✅ **Phase 0**: Foundation Work (001-feasibility-architecture)
  - Architecture Design, Implementation Roadmap, Project Scaffold
  - Gemini API Validation: 94% accuracy, exceeds 85% target
  - Notion API Validation: All CRUD operations confirmed
- ✅ **Phase 1a**: Email Reception (002-email-reception)
  - Gmail API integration with OAuth 2.0
  - Email cleaning pipeline (signatures, disclaimers, quoted threads)
  - Duplicate detection and DLQ error handling
- ✅ **Phase 1b**: Gemini Entity Extraction (004-gemini-extraction)
  - GeminiAdapter with structured JSON output
  - CLI tool for manual entity extraction
  - **Accuracy**: 100% on test dataset (exceeds 85% target for SC-001, SC-002)
  - See [ACCURACY_REPORT.md](tests/fixtures/ground_truth/ACCURACY_REPORT.md)
- ✅ **Phase 005**: Gmail OAuth2 Setup (005-gmail-setup)
  - OAuth2 Desktop Application flow for Gmail API
  - Group alias email access (collab@signite.co)
  - Token management with auto-refresh
- ✅ **Phase 2a**: Notion Read Operations (006-notion-read)
  - NotionIntegrator module with schema discovery
  - Data fetching with pagination and relationship resolution
  - LLM-ready formatting (JSON + Markdown)
  - 63/63 tests passing
  - Infisical integration for secret management
- ✅ **Phase 2b**: LLM-Based Company Matching (007-llm-matching)
  - Extended GeminiAdapter with company_context parameter
  - Company matching with confidence scores (matched_company_id, matched_partner_id)
  - Enhanced prompt with detailed confidence scoring rules
  - **Accuracy**: 100% on test dataset (12/12 tests passing)
  - Handles abbreviations, typos, semantic matches, and no-match scenarios
  - See [VALIDATION_RESULTS.md](specs/007-llm-matching/VALIDATION_RESULTS.md)

**Next Phase**: Phase 2c - Classification & Summarization (008-classification-summarization)

## Overview

CollabIQ automates the tedious process of tracking collaboration activities by:
1. **Receiving** emails from `portfolioupdates@signite.co` via Gmail API (✅ Phase 1a + 005)
2. **Extracting** key information using Gemini API (✅ Phase 1b):
   - 담당자 (Person in charge)
   - 스타트업명 (Startup name)
   - 협업기관 (Partner organization)
   - 협업내용 (Collaboration details)
   - 날짜 (Date)
3. **Fetching** company data from Notion databases (✅ Phase 2a):
   - Schema discovery with caching
   - Pagination and relationship resolution
   - LLM-ready formatting
4. **Matching** companies against existing Notion databases using LLM (✅ Phase 2b)
5. **Creating** entries in Notion's "CollabIQ" database (🚧 Phase 2d)
6. **Queuing** ambiguous cases for manual verification (🚧 Phase 3a-3b)

## System Architecture

```
Email → EmailReceiver → ContentNormalizer → LLMProvider (Gemini)
                                                ↓
                    VerificationQueue ← NotionIntegrator → Notion
                            ↓
                    ReportGenerator
```

**Key Design Principles**:
- **LLM Abstraction Layer**: Swap between Gemini/GPT/Claude in ~30 minutes
- **Single-Service Monolith**: Simple deployment, easy debugging
- **GCP Cloud Run**: Serverless container deployment
- **Pydantic Validation**: Type-safe data handling throughout

See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for detailed component diagrams and data flow.

## Quick Start

### Prerequisites
- Python 3.12+
- UV package manager ([installation](https://github.com/astral-sh/uv))
- Gemini API key
- Notion API token and database IDs
- (Optional) Infisical account for centralized secret management

### Installation

```bash
# Clone and navigate
git clone <repo-url>
cd CollabIQ

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

#### Option 1: Infisical (Recommended for Teams)

CollabIQ supports [Infisical](https://infisical.com) for centralized secret management, eliminating the need to share API keys via email/Slack.

**Benefits**:
- ✅ No credentials in .env files (secure)
- ✅ Environment isolation (development/production)
- ✅ Centralized secret rotation
- ✅ Team member onboarding without manual secret sharing

**Setup** (10 minutes):
```bash
# 1. Get machine identity credentials from team lead
# 2. Add to .env file
cp .env.example .env
# Edit .env with Infisical credentials:
#   INFISICAL_ENABLED=true
#   INFISICAL_PROJECT_ID=your-project-id
#   INFISICAL_ENVIRONMENT=development
#   INFISICAL_CLIENT_ID=machine-identity-abc123
#   INFISICAL_CLIENT_SECRET=secret-xyz789

# 3. Verify connection (checks Gmail, Gemini, and Notion secrets)
uv run collabiq verify-infisical

# 4. Start application (secrets auto-loaded)
uv run collabiq notion fetch
```

**📖 Full Infisical Setup Guide**: [docs/setup/infisical-setup.md](docs/setup/infisical-setup.md)

#### Option 2: Local .env File

Edit `.env` with your credentials directly:

```bash
# Infisical (optional - set to false to use local .env)
INFISICAL_ENABLED=false

# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
NOTION_API_KEY=your_notion_integration_token_here
NOTION_DATABASE_ID_COMPANIES=your_companies_database_id_here
NOTION_DATABASE_ID_COLLABIQ=your_collabiq_database_id_here

# Gmail API
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Processing (future phases)
FUZZY_MATCH_THRESHOLD=0.85
CONFIDENCE_THRESHOLD=0.85
```

See [docs/setup/quickstart.md](docs/setup/quickstart.md) for detailed setup instructions.

### Gmail API Setup

To retrieve emails from Gmail, you need to configure OAuth2 credentials:

**Quick Setup** (10-15 minutes):
1. **Create OAuth2 credentials** in Google Cloud Console:
   - Follow the step-by-step guide: [docs/setup/gmail-oauth-setup.md](docs/setup/gmail-oauth-setup.md)
   - Download `credentials.json` to your project root

2. **Authenticate with Gmail**:
   ```bash
   uv run python scripts/authenticate_gmail.py
   ```
   - A browser window will open for you to sign in
   - Grant read-only access to your Gmail
   - Token is automatically saved and refreshed

3. **Start retrieving emails**:
   ```bash
   uv run python src/cli/extract_entities.py
   ```

**For Group Aliases** (e.g., collab@signite.co):
- Authenticate with any Google Workspace account that is a **member** of the group
- The system automatically filters emails using `to:collab@signite.co`
- See [docs/setup/gmail-oauth-setup.md](docs/setup/gmail-oauth-setup.md) for detailed instructions

**Troubleshooting**:
- If authentication fails, see [docs/setup/troubleshooting-gmail-api.md](docs/setup/troubleshooting-gmail-api.md)
- Common issues: redirect URI mismatch, invalid credentials, expired tokens

## Documentation

📚 **[Browse all documentation](docs/README.md)** - Complete documentation index

### Core Documentation
- [Architecture](docs/architecture/ARCHITECTURE.md) - High-level system design and component diagrams
- [Tech Stack](docs/architecture/TECHSTACK.md) - Implementation details, dependencies, and technical debt
- [Implementation Roadmap](docs/architecture/ROADMAP.md) - 12-phase development plan with progress tracking
- [API Contracts](docs/architecture/API_CONTRACTS.md) - Interface specifications
- [Quick Start Guide](docs/setup/quickstart.md) - Setup and configuration

### Validation Results
- [Notion API Validation](docs/validation/NOTION_API_VALIDATION.md) - ✅ Complete validation results (T005-T007)
- [Notion Schema Analysis](docs/validation/NOTION_SCHEMA_ANALYSIS.md) - Database structure documentation
- [Foundation Work Report](docs/validation/FOUNDATION_WORK_REPORT.md) - Phase 0 completion status
- [Feasibility Testing](docs/validation/FEASIBILITY_TESTING.md) - Gemini API and Notion API validation results
- [Email Infrastructure](docs/validation/EMAIL_INFRASTRUCTURE.md) - Gmail API, IMAP, and webhook comparison

## Implementation Plan

**MVP Scope** (Phase 1a + 1b): 6-9 days
- Phase 0: Foundation (Current)
- Phase 1a: LLM Provider Core (2-3 days)
- Phase 1b: Notion Integrator Core (2-3 days)
- Phase 1c: Email Receiver Prototype (2-3 days)

**Full System**: 12 phases (~30-45 days)
- See [docs/architecture/ROADMAP.md](docs/architecture/ROADMAP.md) for complete timeline

## Testing

```bash
# Run all tests
make test

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Linting and type checking
make lint

# Format code
make format
```

## Development

```bash
# Install dependencies
make install

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Clean cache files
make clean
```

## Project Structure

```
CollabIQ/
├── src/
│   ├── collabiq/              # CLI application
│   ├── config/                # Configuration management (Infisical integration)
│   ├── llm_provider/          # LLM abstraction layer
│   ├── llm_adapters/          # Gemini adapter implementation
│   ├── email_receiver/        # Email ingestion (Gmail API)
│   ├── content_normalizer/    # Email cleaning pipeline
│   ├── notion_integrator/     # Notion API client (✅ Phase 2a complete)
│   │   ├── integrator.py      # High-level API
│   │   ├── client.py          # Rate-limited Notion API wrapper
│   │   ├── schema.py          # Schema discovery
│   │   ├── fetcher.py         # Data fetching with pagination
│   │   ├── formatter.py       # LLM-ready formatting
│   │   ├── cache.py           # File-based caching with TTL
│   │   └── models.py          # Pydantic data models
│   ├── verification_queue/    # Manual verification workflow (future)
│   └── reporting/             # Activity reports (future)
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── contract/              # Contract tests for LLMProvider
│   └── fixtures/              # Test data and ground truth
├── docs/
│   ├── setup/                 # Setup guides
│   ├── architecture/          # System design documents
│   └── validation/            # API validation reports
├── data/
│   ├── raw/                   # Raw email data
│   ├── cleaned/               # Cleaned email data
│   ├── extractions/           # Extracted entities (JSON)
│   └── cache/                 # Notion schema and data cache
└── .claude/                   # SpecKit commands

```

## Contributing

This project follows a specification-first development approach using SpecKit:

1. All features start with `/speckit.specify`
2. Implementation follows `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
3. See `.claude/commands/` for available SpecKit commands

## License

[Add license information]

## Links

- [Notion Workspace](https://www.notion.so/signite) (requires access)
- [Gemini API Docs](https://ai.google.dev/docs)
- [SpecKit Framework](https://github.com/joshmu/speckit) (if applicable)

---

**Built with**: Python 3.12 | Gemini API | Notion API | Pydantic | pytest | ruff | mypy
