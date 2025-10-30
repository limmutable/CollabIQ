# CollabIQ

Email-based collaboration tracking system that automatically extracts collaboration activities from Korean/English emails and syncs them to Notion databases.

## Project Status

**Current Phase**: Foundation Work Complete ✅ (Branch 001-feasibility-architecture)
- ✅ Architecture Design Complete
- ✅ Implementation Roadmap Defined
- ✅ Project Scaffold Complete
- ✅ **Feasibility Testing Complete**
  - ✅ Gemini API Validation (T001-T004): 94% accuracy, exceeds 85% target
  - ✅ Notion API Validation (T005-T007): All CRUD operations confirmed

**Next Phase**: Phase 1a - Email Reception (Branch 002-email-reception)

## Overview

CollabIQ automates the tedious process of tracking collaboration activities by:
1. **Receiving** emails from `portfolioupdates@signite.co`
2. **Extracting** key information using Gemini API:
   - 담당자 (Person in charge)
   - 스타트업명 (Startup name)
   - 협업기관 (Partner organization)
   - 협업내용 (Collaboration details)
   - 날짜 (Date)
3. **Matching** companies against existing Notion databases using fuzzy matching
4. **Creating** entries in Notion's "CollabIQ" database
5. **Queuing** ambiguous cases for manual verification

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

Edit `.env` with your credentials:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
NOTION_API_KEY=your_notion_integration_token_here
NOTION_DATABASE_ID_COLLABIQ=your_collabiq_database_id_here
NOTION_DATABASE_ID_CORP=your_corp_database_id_here

# Optional - Email infrastructure (choose one approach)
GMAIL_CREDENTIALS_PATH=path/to/credentials.json  # Gmail API
IMAP_HOST=imap.gmail.com                         # IMAP
WEBHOOK_SECRET=your_webhook_secret_here          # Webhook

# Processing
FUZZY_MATCH_THRESHOLD=0.85
CONFIDENCE_THRESHOLD=0.85
```

See [docs/setup/quickstart.md](docs/setup/quickstart.md) for detailed setup instructions.

## Documentation

📚 **[Browse all documentation](docs/README.md)** - Complete documentation index

### Core Documentation
- [Architecture](docs/architecture/ARCHITECTURE.md) - System design and component diagrams
- [Implementation Roadmap](docs/architecture/IMPLEMENTATION_ROADMAP.md) - 12-phase development plan
- [API Contracts](docs/architecture/API_CONTRACTS.md) - Interface specifications
- [Quick Start Guide](docs/setup/quickstart.md) - Setup and configuration

### Validation Results
- [Notion API Validation](docs/validation/NOTION_API_VALIDATION.md) - ✅ Complete validation results (T005-T007)
- [Notion Schema Analysis](docs/validation/NOTION_SCHEMA_ANALYSIS.md) - Database structure documentation
- [Foundation Work Report](specs/001-feasibility-architecture/FOUNDATION_WORK_REPORT.md) - Phase 0 completion status

## Implementation Plan

**MVP Scope** (Phase 1a + 1b): 6-9 days
- Phase 0: Foundation (Current)
- Phase 1a: LLM Provider Core (2-3 days)
- Phase 1b: Notion Integrator Core (2-3 days)
- Phase 1c: Email Receiver Prototype (2-3 days)

**Full System**: 12 phases (~30-45 days)
- See [docs/architecture/IMPLEMENTATION_ROADMAP.md](docs/architecture/IMPLEMENTATION_ROADMAP.md) for complete timeline

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
│   ├── llm_provider/          # LLM abstraction layer
│   ├── llm_adapters/          # Gemini/GPT/Claude adapters
│   ├── email_receiver/        # Email ingestion (Gmail API/IMAP/Webhook)
│   ├── notion_integrator/     # Notion API client
│   ├── verification_queue/    # Manual verification workflow
│   └── reporting/             # Activity reports
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── contract/              # Contract tests for LLMProvider
├── config/
│   └── settings.py            # Pydantic settings
├── specs/
│   └── 001-feasibility-architecture/  # Foundation work specs
└── docs/                      # Documentation

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
