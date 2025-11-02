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

**Current Phase**: Phase 2a Complete ✅ (Notion Read Operations)

### Completed Phases
- ✅ **Phase 0**: Foundation Work (Architecture, Roadmap, Project Scaffold)
- ✅ **Phase 1a**: Email Reception (Gmail API, OAuth2, Email Cleaning)
- ✅ **Phase 1b**: Gemini Entity Extraction (100% accuracy on test dataset)
- ✅ **Phase 005**: Gmail OAuth2 Setup (Group alias support, Token management)
- ✅ **Phase 2a**: Notion Read Operations (Schema discovery, Data fetching, LLM formatting)

**Next Phase**: Phase 2b - LLM-Based Company Matching

### Key Achievements
- ✅ **Gemini API Validation**: 94% accuracy (exceeds 85% target)
- ✅ **Notion API Validation**: All CRUD operations confirmed
- ✅ **MVP Complete**: Email ingestion + entity extraction + JSON output
- ✅ **Notion Integration**: Schema discovery, pagination, relationship resolution (63/63 tests passing)
- ✅ **Infisical Integration**: Centralized secret management for all services

## Quick Links

- [Main README](../README.md) - Project overview
- [Speckit Commands](../.claude/commands/) - Available development workflows
- [Test Fixtures](../tests/fixtures/) - Sample data for testing

## Need Help?

- Check the [Quick Start Guide](setup/quickstart.md) for setup issues
- Review [Architecture](architecture/ARCHITECTURE.md) for high-level system design
- See [Tech Stack](architecture/TECHSTACK.md) for implementation details and troubleshooting
- Check [API Contracts](architecture/API_CONTRACTS.md) for interface specifications
