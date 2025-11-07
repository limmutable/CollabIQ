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

## Validation Results

Review the feasibility testing and API validation results:

- [Notion API Validation](validation/NOTION_API_VALIDATION.md) - Comprehensive Notion API test results
- [Notion Schema Analysis](validation/NOTION_SCHEMA_ANALYSIS.md) - Database field structures and types
- [Foundation Work Report](validation/FOUNDATION_WORK_REPORT.md) - Phase 0 completion summary
- [Feasibility Testing](validation/FEASIBILITY_TESTING.md) - Gemini API and Notion API validation results
- [Email Infrastructure](validation/EMAIL_INFRASTRUCTURE.md) - Gmail API, IMAP, and webhook comparison

## Project Status

**Current Phase**: Phase 010 Complete ✅ (Error Handling & Retry Logic)

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

**🎯 MVP Status**: COMPLETE - Full extraction pipeline with Notion integration working end-to-end

**Next Steps**: Production deployment and monitoring

### Key Achievements
- ✅ **Gemini API Validation**: 94% accuracy (exceeds 85% target)
- ✅ **Notion API Validation**: All CRUD operations confirmed
- ✅ **MVP Complete**: Email ingestion + entity extraction + company matching + classification + Notion write
- ✅ **Notion Integration**: Schema discovery, pagination, relationship resolution, duplicate detection
- ✅ **Infisical Integration**: Centralized secret management for all services
- ✅ **Error Handling**: Unified retry system with circuit breakers, DLQ, and structured logging
- ✅ **Classification Pipeline**: Dynamic type classification, LLM-based intensity, summary generation

## Quick Links

- [Main README](../README.md) - Project overview
- [Speckit Commands](../.claude/commands/) - Available development workflows
- [Test Fixtures](../tests/fixtures/) - Sample data for testing

## Need Help?

- Check the [Quick Start Guide](setup/quickstart.md) for setup issues
- Review [Architecture](architecture/ARCHITECTURE.md) for high-level system design
- See [Tech Stack](architecture/TECHSTACK.md) for implementation details and troubleshooting
- Check [API Contracts](architecture/API_CONTRACTS.md) for interface specifications
