# CollabIQ

**Automated collaboration tracking system** that extracts collaboration activities from Korean/English emails and syncs them to Notion databases.

CollabIQ eliminates manual data entry by automatically processing collaboration emails, extracting key information using AI, matching companies in your database, and creating structured Notion entries—all with intelligent error handling and duplicate detection.

---

## Key Features

### ✅ Intelligent Entity Extraction
- **Multi-LLM support** (Gemini, Claude, OpenAI) with automatic failover
- **Quality-based routing** selects the best provider based on historical performance
- **100% accuracy** on test dataset
- Extracts 5 key entities: person, startup, partner, details, date

### ✅ Smart Company Matching & Classification
- **Semantic matching** for company names against Notion database
- **Dynamic classification** of collaboration type and intensity
- **Auto-generated summaries** preserving key context

### ✅ Robust Operations
- **Cloud-Native**: Deployed on Google Cloud Run with state persistence
- **Resilient**: Circuit breakers, automatic retries, and Dead Letter Queue (DLQ)
- **Secure**: Integrated with Infisical and Google Secret Manager
- **Daemon Mode**: Continuous background processing

---

## Quick Start

### Prerequisites
- Python 3.12+ and [UV package manager](https://github.com/astral-sh/uv)
- LLM API Key (Gemini, Anthropic, or OpenAI)
- Notion API Token & Database IDs
- Gmail OAuth2 Credentials

### Installation

```bash
# Clone and install
git clone <repo-url>
cd CollabIQ
make install

# Configure environment
cp .env.example .env
# Edit .env with your keys
```

### Setup Guides
- **[Quick Start Guide](docs/setup/quickstart.md)**: Full setup instructions
- **[Google Cloud Deployment](docs/deployment/google-cloud-guide.md)**: Deploy to production
- **[Gmail Setup](docs/setup/gmail-oauth-setup.md)**: Configure email access

---

## Usage (CLI)

CollabIQ provides a comprehensive CLI for all operations.

```bash
# System Status
uv run collabiq status --detailed

# Run Pipeline (Fetch -> Extract -> Write)
uv run collabiq email process --limit 10

# Run in Daemon Mode (Continuous)
uv run collabiq run --daemon --interval 15

# LLM Management
uv run collabiq llm status
uv run collabiq llm compare --detailed

# Notion Utilities
uv run collabiq notion verify
```

For complete documentation, see [CLI Reference](docs/cli/CLI_REFERENCE.md).

---

## Project Status

**Current Phase**: Phase 018 Complete (Cloud Deployment) ✅
**Production Ready**: Yes

- **Email & Parsing**: ✅ Gmail API, Content Normalization
- **Intelligence**: ✅ Multi-LLM (Gemini/Claude/OpenAI), Semantic Matching
- **Data**: ✅ Notion Integration (Read/Write), Schema-aware Mapping
- **Operations**: ✅ CLI, Error Handling, Daemon Mode, GCS State
- **Deployment**: ✅ Docker, Cloud Run, Secret Manager

---

## Documentation Structure

- **[docs/setup/](docs/setup/)**: Installation and configuration
- **[docs/architecture/](docs/architecture/)**: System design and roadmap
- **[docs/deployment/](docs/deployment/)**: Cloud deployment guides
- **[docs/cli/](docs/cli/)**: Command reference
- **[docs/testing/](docs/testing/)**: Testing strategies and reports

---

**Built with**: Python 3.12 | Multi-LLM | Notion API | Google Cloud Run