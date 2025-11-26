# Implementation Plan: Deploy CollabIQ to Google Cloud

**Branch**: `018-deploy-google-cloud` | **Date**: November 25, 2025 | **Spec**: /specs/018-deploy-google-cloud/spec.md
**Input**: Feature specification from `/specs/018-deploy-google-cloud/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The primary requirement is to provide step-by-step instructions for deploying the CollabIQ Python CLI application to Google Cloud, targeting users with no prior server-side deployment experience. The technical approach will involve researching suitable Google Cloud services, outlining configuration steps for secrets and environment variables, and providing guidance on persistent storage and integrated billing.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: uv (package manager), Google Cloud SDK (CLI tools), potentially `google-cloud-storage`, `google-cloud-run` client libraries.
**Storage**: File-based JSON for extractions, caching, metrics (current project); will need persistent storage on Google Cloud (e.g., Cloud Storage, Persistent Disks for Compute Engine).
**Testing**: pytest (existing test suite, will need to define how to run tests in the deployed environment).
**Target Platform**: Google Cloud Platform (specific services like Cloud Run, Compute Engine, App Engine will be researched and recommended).
**Project Type**: Single project (Python CLI application).
**Performance Goals**: Reliable and responsive execution of the email processing pipeline, with successful end-to-end processing of test emails within 5 minutes of receipt.
**Constraints**: User's lack of server-side deployment experience; strong preference for Google Cloud platforms due to integrated billing and administration. Instructions must be highly detailed and user-friendly. Cost-effectiveness is a consideration for service recommendations.
**Scale/Scope**: Initial deployment of the CollabIQ application. The solution should be extensible to handle potential increases in email volume.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Library-First**: CollabIQ is structured as a CLI application with modular components, adhering to the library-first principle.
**II. CLI Interface**: The application has a comprehensive CLI interface.
**III. Test-First (NON-NEGOTIABLE)**: The project has an extensive test suite. Deployment instructions will include guidance on verifying functionality using existing tests.
**IV. Integration Testing**: Deployment inherently involves integration with Google Cloud services, which will require careful testing.
**V. Observability**: The application includes structured logging, which will be maintained and potentially integrated with Google Cloud's logging services (e.g., Cloud Logging).

**Additional Constraints**: The project adheres to Python 3.12+, uses uv, pytest, ruff, mypy, and integrates with specified LLM providers and Notion. The proposed deployment on Google Cloud is compatible with this existing tech stack.

## Project Structure

### Documentation (this feature)

```text
specs/018-deploy-google-cloud/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── collabiq/              # Main CLI application logic
├── config/                # Configuration & secrets management
├── llm_provider/          # LLM abstraction layer
├── llm_adapters/          # Specific LLM provider implementations (Gemini, Claude, OpenAI)
├── llm_orchestrator/      # Multi-LLM orchestration, health & cost tracking
├── email_receiver/        # Gmail API integration
├── content_normalizer/    # Email cleaning pipeline
├── notion_integrator/     # Notion API client (read + write)
├── error_handling/        # Unified retry system & circuit breakers
└── models/                # Pydantic data models

tests/
├── unit/
├── integration/
├── e2e/
└── validation/
```

**Structure Decision**: The existing single-project structure of CollabIQ is suitable for deployment to Google Cloud. We will leverage this structure and focus on documenting the necessary Google Cloud configurations and deployment steps. The application's modularity within `src/` is well-suited for containerization if a service like Cloud Run is chosen.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
|           |            |                                     |