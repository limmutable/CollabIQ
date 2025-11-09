# CollabIQ

**Automated collaboration tracking system** that extracts collaboration activities from Korean/English emails and syncs them to Notion databases.

CollabIQ eliminates manual data entry by automatically processing collaboration emails, extracting key information using AI, matching companies in your database, and creating structured Notion entries—all with intelligent error handling and duplicate detection.

---

## What Does CollabIQ Do?

CollabIQ automates the tedious process of tracking collaboration activities:

1. **Receives** emails from your collaboration inbox via Gmail API
2. **Cleans** email content (removes signatures, disclaimers, quoted threads)
3. **Extracts** key entities using Multi-LLM orchestration (Gemini/Claude/OpenAI):
   - 담당자 (Person in charge)
   - 스타트업명 (Startup name)
   - 협업기관 (Partner organization)
   - 협업내용 (Collaboration details)
   - 날짜 (Date)
4. **Matches** companies against your Notion database using semantic AI matching
5. **Classifies** collaboration type and intensity:
   - Type: Portfolio+SSG, Non-Portfolio+SSG, Portfolio+Portfolio, Other
   - Intensity: 이해 (Understanding), 협력 (Collaboration), 투자 (Investment), 인수 (Acquisition)
6. **Generates** concise summaries preserving all key information
7. **Writes** structured entries to your Notion "CollabIQ" database
8. **Handles** errors gracefully with automatic retries, circuit breakers, and dead letter queue

**Result**: Collaboration data flows automatically from email → Notion with 100% accuracy on entity extraction and company matching.

---

## Key Features

### ✅ Intelligent Entity Extraction
- **Multi-LLM support** with failover across Gemini, Claude, and OpenAI
- **Quality-based routing** automatically selects best provider based on historical performance
- **100% accuracy** on test dataset with automatic provider failover
- **Provider health monitoring** with circuit breakers (CLOSED/OPEN/HALF_OPEN states)
- **Quality metrics tracking** monitors confidence, completeness, and validation success
- **Cost tracking** monitors token usage and pricing across all providers
- **Provider comparison** with composite scoring (quality vs cost optimization)
- Handles both Korean and English emails
- Extracts 5 key entities: person, startup, partner, details, date
- Confidence scoring for each field

### ✅ Smart Company Matching
- **Semantic matching** handles abbreviations, typos, and variations
- Matches against existing Notion company database
- **100% accuracy** on test dataset
- Confidence threshold (0.70) ensures quality

### ✅ Automated Classification
- **Dynamic type classification** based on company relationships
- **LLM-based intensity analysis** with Korean semantic understanding
- **Auto-generated summaries** (3-5 sentences) preserving key details
- Manual review routing for low-confidence cases (< 0.85)

### ✅ Robust Error Handling
- **Automatic retries** with exponential backoff for transient failures
- **Circuit breakers** prevent cascading failures across services
- **Dead Letter Queue (DLQ)** preserves failed operations for replay
- **Structured logging** with full context for debugging
- **Rate limit handling** with `Retry-After` header support

### ✅ Notion Integration
- **Duplicate detection** with configurable strategies (skip/update)
- **Schema-aware field mapping** adapts to your Notion database structure
- **Relationship resolution** automatically links companies
- **Cached data** reduces API calls (24h schema cache, 6h data cache)

### ✅ Secure Secrets Management
- **Infisical integration** for centralized secret management (optional)
- Environment isolation (dev/staging/production)
- Automatic secret rotation without restart
- Fallback to local `.env` file

---

## Quick Start

### Prerequisites
- Python 3.12 or higher
- UV package manager ([install here](https://github.com/astral-sh/uv))
- **At least one LLM API key** (recommended: all three for failover):
  - Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey) (free tier available)
  - Anthropic API key from [Anthropic Console](https://console.anthropic.com/) (optional)
  - OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys) (optional)
- Notion API integration token and database IDs
- Gmail OAuth2 credentials (for email access)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd CollabIQ

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Setup

**For detailed setup instructions**, see [docs/setup/quickstart.md](docs/setup/quickstart.md)

**Quick configuration steps**:
1. Configure `.env` with API keys (or use Infisical for team deployments)
2. Setup Gmail OAuth2: `uv run python scripts/authenticate_gmail.py`
3. Verify configuration: `uv run collabiq verify-infisical`
4. Run tests: `make test`

---

## Usage

### Admin CLI

CollabIQ provides a comprehensive CLI for all operations:

```bash
# System health check
uv run collabiq status
uv run collabiq status --detailed

# Email pipeline
uv run collabiq email fetch --limit 10
uv run collabiq email list
uv run collabiq email verify

# Notion integration
uv run collabiq notion verify
uv run collabiq notion schema
uv run collabiq notion test-write

# Error management
uv run collabiq errors list
uv run collabiq errors retry --all

# Configuration
uv run collabiq config show
uv run collabiq config validate

# E2E testing
uv run collabiq test validate
uv run collabiq test e2e --limit 5

# LLM provider management (Multi-provider support)
uv run collabiq llm status --detailed
uv run collabiq llm compare --detailed
uv run collabiq llm test gemini
uv run collabiq llm test claude
uv run collabiq llm set-strategy failover
uv run collabiq llm set-quality-routing --enabled

# Export metrics to JSON
uv run collabiq llm export-metrics
uv run collabiq llm export-metrics -o quality_report.json --no-health --no-cost

# Test with specific email ID
uv run python scripts/test_specific_email.py --email-id "test_001" --show-metrics
```

For complete CLI documentation, see [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)

### Legacy Scripts (Deprecated)

```bash
# Legacy: Fetch recent emails and extract entities
uv run python tests/manual/test_gmail_retrieval.py --max-results 5

# Legacy: Run full pipeline (extract + match + classify + write to Notion)
uv run python tests/manual/test_e2e_phase2b.py --limit 3
```

---

## Testing

```bash
# Run all tests
make test

# Run with coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run specific test suite
uv run pytest tests/unit/test_gemini_adapter.py -v

# Lint and format code
make lint
make format
```

**Test Coverage**: 90+ unit tests, full integration test coverage for Gmail, Gemini, and Notion APIs.

---

## System Architecture

```
Email (Gmail) → EmailReceiver → ContentNormalizer → Gemini AI
                                                        ↓
                                    Extracts entities + Matches companies
                                    + Classifies type/intensity + Summarizes
                                                        ↓
                Dead Letter Queue ← NotionIntegrator → Notion Database
                        ↓
                Manual Retry Script
```

**Key Design Principles**:
- **Multi-LLM Orchestration**: Automatic failover across Gemini/Claude/OpenAI with health monitoring
- **LLM Abstraction Layer**: Pluggable provider architecture with unified interface
- **Single-Service Monolith**: Simple deployment, easy debugging
- **Error Resilience**: Automatic retries, circuit breakers, DLQ for fault tolerance
- **Pydantic Validation**: Type-safe data handling throughout

For detailed architecture, see [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

---

## Project Status

**Current Phase**: Phase 013 Complete - Quality Metrics & Intelligent Routing
**Production Ready**: ✅ Yes - Full automation with multi-LLM resilience
**Overall Progress**: 12/14 phases complete (86%)

### Completed Features

✅ **Phase 1a**: Email Reception (Gmail API OAuth2)
✅ **Phase 1b**: Gemini Entity Extraction (100% accuracy)
✅ **Phase 005**: Gmail OAuth2 Setup (group alias support)
✅ **Phase 2a**: Notion Read Operations (schema discovery, data fetching)
✅ **Phase 2b**: LLM-Based Company Matching (100% accuracy)
✅ **Phase 2c**: Classification & Summarization (type/intensity/summary)
✅ **Phase 2d**: Notion Write Operations (duplicate detection, DLQ)
✅ **Phase 2e**: Error Handling (circuit breakers, unified retry logic)
✅ **Phase 3a**: Admin CLI (30+ commands for system management)
✅ **Phase 3b**: Multi-LLM Support (Gemini, Claude, OpenAI with failover)
✅ **Phase 3c**: Quality Metrics & Intelligent Routing (quality tracking, provider comparison)

### Current Capabilities

- Full end-to-end automation: Email → Notion without manual intervention
- Multi-LLM resilience with automatic failover
- Quality-based provider selection with cost optimization
- Comprehensive CLI for all operations
- Circuit breakers and automatic retry for fault tolerance
- Cost and quality tracking per provider
- Dead Letter Queue for failed operations

### Next Steps

🎯 **Phase 4a**: Basic Reporting - Generate analytics from Notion data
⏳ **Phase 4b**: Advanced Analytics - Trend analysis and insights
⏳ **Phase 4c**: Dashboards - Visual reporting interface

For detailed roadmap, see [docs/architecture/ROADMAP.md](docs/architecture/ROADMAP.md)

---

## Project Structure

```
CollabIQ/
├── src/
│   ├── collabiq/              # CLI application
│   ├── config/                # Configuration & secrets management
│   ├── llm_provider/          # LLM abstraction layer
│   ├── llm_adapters/          # Provider implementations (Gemini, Claude, OpenAI)
│   ├── llm_orchestrator/      # Multi-LLM orchestration with health & cost tracking
│   ├── email_receiver/        # Gmail API integration
│   ├── content_normalizer/    # Email cleaning pipeline
│   ├── notion_integrator/     # Notion API client (read + write)
│   ├── error_handling/        # Unified retry system & circuit breakers
│   └── models/                # Pydantic data models
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── e2e/                   # End-to-end tests
│   ├── manual/                # Manual tests (real APIs)
│   └── fixtures/              # Test data & ground truth
├── docs/
│   ├── setup/                 # Setup & configuration guides
│   ├── architecture/          # System design documents
│   └── validation/            # API validation reports
├── scripts/                   # Utility scripts
├── data/                      # Runtime data (emails, extractions, cache, DLQ)
└── .env.example              # Environment template
```

---

## Documentation

### Getting Started
- [Quick Start Guide](docs/setup/quickstart.md) - Complete setup in 15 minutes
- [Gmail OAuth Setup](docs/setup/gmail-oauth-setup.md) - Gmail API authentication
- [Infisical Setup](docs/setup/infisical-setup.md) - Centralized secret management (optional)
- [Troubleshooting](docs/setup/troubleshooting-gmail-api.md) - Common issues and solutions

### Architecture & Design
- [System Architecture](docs/architecture/ARCHITECTURE.md) - Component design and data flow
- [Tech Stack](docs/architecture/TECHSTACK.md) - Technologies, dependencies, patterns
- [API Contracts](docs/architecture/API_CONTRACTS.md) - Interface specifications
- [Implementation Roadmap](docs/architecture/ROADMAP.md) - Development timeline

### Validation & Testing
- [Notion API Validation](docs/validation/NOTION_API_VALIDATION.md) - API test results
- [Feasibility Testing](docs/validation/FEASIBILITY_TESTING.md) - Gemini & Notion validation
- [E2E Testing Guide](docs/validation/E2E_QUICKSTART.md) - End-to-end testing

### All Documentation
Browse the complete documentation at [docs/README.md](docs/README.md)

---

## Configuration

CollabIQ supports two configuration methods:

### Option 1: Infisical (Recommended for Teams)
Centralized secret management with environment isolation and automatic rotation.

```bash
# .env configuration
INFISICAL_ENABLED=true
INFISICAL_PROJECT_ID=your-project-id
INFISICAL_ENVIRONMENT=development
INFISICAL_CLIENT_ID=machine-identity-abc123
INFISICAL_CLIENT_SECRET=secret-xyz789
```

See [docs/setup/infisical-setup.md](docs/setup/infisical-setup.md) for complete setup.

### Option 2: Local .env File
Direct configuration for solo developers or local development.

```bash
# .env configuration
INFISICAL_ENABLED=false

# LLM API Keys (at least one required)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional for failover
OPENAI_API_KEY=your_openai_api_key_here        # Optional for failover

# Notion & Gmail
NOTION_API_KEY=your_notion_token_here
GMAIL_CREDENTIALS_PATH=credentials.json
CONFIDENCE_THRESHOLD=0.70
```

See [docs/setup/quickstart.md](docs/setup/quickstart.md) for all configuration options.

---

## Known Issues & Limitations

### Current Limitations
- **Gmail Group Authentication**: Must authenticate as group member, not the group email itself
- **Notion API Rate Limits**: 3 requests/second (system handles this with rate limiting)
- **Korean Language Focus**: Optimized for Korean emails, but works with English
- **Manual Review**: Low-confidence entries (< 0.85) may need manual review

### Technical Debt
- **Notion API Migration**: Updated to v2025-09-03 (completed)
- **Retry Logic**: Unified to `@retry_with_backoff` decorator (completed)
- **Token Management**: Gmail token auto-refresh implemented

See [docs/architecture/TECHSTACK.md](docs/architecture/TECHSTACK.md) for detailed technical debt tracking.

---

## Development

### Daily Workflow

```bash
# Install dependencies
make install

# Format code
make format

# Run linting
make lint

# Run tests
make test

# Clean cache
make clean
```

### Pre-commit Hooks
Pre-commit hooks automatically run on `git commit` to ensure code quality (ruff, mypy).

---

## Deployment

### Local Development
```bash
uv run collabiq --help
```

### Production (GCP Cloud Run)
See [docs/architecture/ARCHITECTURE.md#deployment-architecture](docs/architecture/ARCHITECTURE.md#deployment-architecture) for Cloud Run deployment guide.

**Estimated Cost**: $25-65/month for 50 emails/day on GCP Cloud Run with Gemini API.

---

## Support & Contributing

### Getting Help
- Check [docs/setup/quickstart.md](docs/setup/quickstart.md) for setup issues
- Review [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for design questions
- See [docs/architecture/TECHSTACK.md](docs/architecture/TECHSTACK.md) for troubleshooting

### Contributing
This project follows a specification-first development approach:
1. Features start with specification documents
2. Implementation follows plan → tasks → code workflow
3. All changes require tests and documentation updates

---

## License

[Add license information]

---

## Links

- [Notion Workspace](https://www.notion.so/signite) (requires access)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [UV Package Manager](https://github.com/astral-sh/uv)

---

**Built with**: Python 3.12 | Multi-LLM (Gemini/Claude/OpenAI) | Notion API | Pydantic | pytest | ruff | mypy
