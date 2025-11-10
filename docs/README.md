# CollabIQ Documentation

Welcome to the CollabIQ documentation. This guide will help you navigate all available resources.

## Getting Started

If you're new to CollabIQ, start here:

- [Quick Start Guide](setup/quickstart.md) - Set up your development environment in under 15 minutes
- [Infisical Secret Management](setup/infisical-setup.md) - Optional centralized secret management for teams

## Architecture & Design

Learn about the system design and implementation strategy:

- [System Architecture](architecture/ARCHITECTURE.md) - High-level component design, data flow, deployment architecture
- [Tech Stack](architecture/TECHSTACK.md) - Implementation details, dependencies, patterns, technical debt, and Infisical integration
- [API Contracts](architecture/API_CONTRACTS.md) - Interface specifications for all components
- [Implementation Roadmap](architecture/ROADMAP.md) - 12-phase development plan with progress tracking

## Testing & Validation

Review testing guides and API validation results:

- **[E2E Testing Guide](testing/E2E_TESTING.md)** - Comprehensive end-to-end testing workflow
- **[Validation Documentation Index](validation/README.md)** - Overview of all validation docs
- [E2E Data Model](validation/E2E_DATA_MODEL.md) - Test data structure reference
- [Gemini API Reference](validation/GEMINI_API_REFERENCE.md) - API capabilities, rate limits, pricing
- [Notion API Validation](validation/NOTION_API_VALIDATION.md) - Comprehensive Notion API test results
- [Notion Schema Analysis](validation/NOTION_SCHEMA_ANALYSIS.md) - Database field structures and types
- [Date Parsing Library Comparison](validation/date-parsing-library-comparison.md) - dateutil vs dateparser analysis

**Historical Docs**: Phase 0 documentation archived in [docs/archive/phase0/](archive/phase0/)

## Project Status

**Current Phase**: Phase 014 Complete ✅ (Enhanced Field Mapping with Fuzzy Matching)

### Completed Phases
- ✅ **Phase 0**: Foundation Work (Architecture, Roadmap, Project Scaffold)
- ✅ **Phase 1a**: Email Reception (Gmail API, OAuth2, Email Cleaning)
- ✅ **Phase 1b**: Gemini Entity Extraction (100% accuracy on test dataset)
- ✅ **Phase 005**: Gmail OAuth2 Setup (Group alias support, Token management)
- ✅ **Phase 2a**: Notion Read Operations (Schema discovery, Data fetching, LLM formatting)
- ✅ **Phase 2b**: LLM-Based Company Matching (100% accuracy, confidence scores)
- ✅ **Phase 2c**: Classification & Summarization (Type, Intensity, Summary generation)
- ✅ **Phase 2d**: Notion Write Operations (Duplicate detection, DLQ handling)
- ✅ **Phase 010**: Error Handling & Retry Logic (Unified retry system with circuit breakers)
- ✅ **Phase 011**: Admin CLI (Status, health checks, cost tracking, provider comparison)
- ✅ **Phase 012**: Multi-LLM Support (Claude, OpenAI adapters with unified interface)
- ✅ **Phase 013**: Quality Metrics & Intelligent Routing (Provider selection, metrics tracking)
- ✅ **Phase 014**: Enhanced Field Mapping (Company fuzzy matching, person matching, auto-creation)

**🎯 MVP Status**: PRODUCTION READY - Full pipeline with intelligent field population and relation management

**Next Steps**: Production monitoring and optimization

### Key Achievements
- ✅ **Gemini API Validation**: 94% accuracy (exceeds 85% target)
- ✅ **Notion API Validation**: All CRUD operations confirmed
- ✅ **MVP Complete**: Email ingestion + entity extraction + company matching + classification + Notion write
- ✅ **Notion Integration**: Schema discovery, pagination, relationship resolution, duplicate detection
- ✅ **Infisical Integration**: Centralized secret management for all services
- ✅ **Error Handling**: Unified retry system with circuit breakers, DLQ, and structured logging
- ✅ **Classification Pipeline**: Dynamic type classification, LLM-based intensity, summary generation
- ✅ **Field Mapping**: Fuzzy company matching (<1ms), person matching (100%), auto-creation of missing companies

## Quick Links

- [Main README](../README.md) - Project overview
- [Speckit Commands](../.claude/commands/) - Available development workflows
- [Test Fixtures](../tests/fixtures/) - Sample data for testing

## Need Help?

- Check the [Quick Start Guide](setup/quickstart.md) for setup issues
- Review [Architecture](architecture/ARCHITECTURE.md) for high-level system design
- See [Tech Stack](architecture/TECHSTACK.md) for implementation details and troubleshooting
- Check [API Contracts](architecture/API_CONTRACTS.md) for interface specifications
