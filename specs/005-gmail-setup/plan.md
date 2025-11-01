# Implementation Plan: Gmail Setup for Production Email Access

**Branch**: `005-gmail-setup` | **Date**: 2025-11-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-gmail-setup/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Configure gmail_receiver.py to access emails from the **collab@signite.co Google Workspace group alias** using OAuth2 Desktop Application credentials. The system will authenticate as a group member (since group aliases have no standalone inbox) and use `deliveredto:"collab@signite.co"` Gmail API queries to filter group emails. OAuth2 credentials will be stored in Infisical (or .env fallback) while user-specific access/refresh tokens will be stored in local token.json with restricted permissions. Comprehensive step-by-step documentation will guide setup in under 15 minutes.

## Technical Context

**Language/Version**: Python 3.12 (established in project)
**Primary Dependencies**: google-auth-oauthlib, google-api-python-client, Infisical Python SDK (from Phase 003)
**Storage**: Infisical (OAuth2 credentials) + Local filesystem (token.json for user tokens)
**Testing**: pytest (existing test infrastructure)
**Target Platform**: macOS/Linux/Windows (cross-platform CLI application)
**Project Type**: Single (existing src/ structure)
**Performance Goals**: OAuth token refresh <2 seconds, email retrieval <5 seconds for typical queries
**Constraints**: Gmail API quota (1B units/day, 250 units/sec/user), token expiry (access: 1 hour, refresh: 6 months)
**Scale/Scope**: Single email account access, <100 emails/day typical usage, ~15 minute setup time target

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

- ✅ Feature specification ([spec.md](spec.md)) exists and is complete
- ✅ User scenarios include acceptance criteria
- ✅ Functional requirements documented (FR-001 through FR-012)
- ✅ Success criteria defined (SC-001 through SC-006)
- ✅ Requirements are technology-agnostic at specification stage

**Status**: PASS

---

### II. Incremental Delivery via Independent User Stories ✅

- ✅ User stories are prioritized (P1, P1, P2)
- ✅ Each user story is independently testable
- ✅ User Story 1 (Set Up Gmail API Credentials) constitutes viable MVP
- ✅ Implementation can proceed in priority order
- ✅ Each story completion results in deployable increment

**MVP Definition**: User Story 1 alone enables Gmail API access and email retrieval from collab@signite.co, providing immediate value even if User Story 2 and 3 are not implemented.

**Status**: PASS

---

### III. Test-Driven Development (TDD) ✅

**Applicability**: Tests are required for this feature (FR-010: Integration tests MUST run successfully)

- ✅ Tests will be written before implementation code
- ✅ Integration tests will verify Gmail API connection
- ✅ Contract tests will verify OAuth2 token handling
- ✅ Tests will validate group alias email retrieval

**TDD Discipline**: Mandatory for this feature. Tests must be written first and fail before implementation proceeds.

**Status**: PASS (TDD required and will be enforced)

---

### IV. Design Artifact Completeness ✅

Planning phase artifacts:
- ✅ [plan.md](plan.md) - This file (with constitution check, technical context, structure)
- ✅ [research.md](research.md) - 6 key technical decisions documented
- ✅ [data-model.md](data-model.md) - 4 entities defined (OAuth2Credentials, OAuth2Token, GmailServiceClient, GroupAlias)
- ✅ [quickstart.md](quickstart.md) - Step-by-step setup guide (15-minute target)
- ⚠️  contracts/ - No API contracts needed (configuration/documentation feature, not new API)

**Next Step**: Task generation (`/speckit.tasks`) may proceed after this plan is complete.

**Status**: PASS (all required artifacts complete)

---

### V. Simplicity & Justification ✅

- ✅ Desktop OAuth chosen over Service Account (simpler, no domain-wide delegation setup)
- ✅ Hybrid storage (Infisical + local) leverages existing infrastructure vs. creating new secret management
- ✅ Read-only scope (gmail.readonly) minimizes permissions
- ✅ No new patterns or frameworks introduced
- ✅ Focuses on documentation and configuration, not complex abstractions

**Status**: PASS (no complexity violations to justify)

---

### Constitution Check Summary

**Overall Status**: ✅ PASS

All five core principles are satisfied. Implementation may proceed after task generation.

## Project Structure

### Documentation (this feature)

```text
specs/005-gmail-setup/
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0: Technical research (6 key decisions)
├── data-model.md        # Phase 1: Entity definitions (4 entities)
├── quickstart.md        # Phase 1: Step-by-step setup guide
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Specification quality checklist
```

**Note**: No `contracts/` directory needed (configuration/documentation feature, no new APIs). No `tasks.md` yet (created by `/speckit.tasks` command in Phase 2).

### Source Code (repository root)

```text
src/
├── email_receiver/
│   ├── __init__.py
│   ├── gmail_receiver.py    # EXISTING - needs documentation updates
│   └── email_receiver.py    # EXISTING - base interface
├── config/
│   └── settings.py           # EXISTING - may need GOOGLE_CREDENTIALS_PATH config
└── cli/
    └── extract_entities.py   # EXISTING - uses gmail_receiver

tests/
├── integration/
│   ├── test_gmail_receiver.py          # EXISTING - needs updates for real API
│   └── test_gmail_oauth.py             # NEW - OAuth flow validation
├── fixtures/
│   └── sample_emails/                  # EXISTING - test email data
└── e2e/
    └── test_cli_extraction.py          # EXISTING - end-to-end validation

docs/
├── gmail-oauth-setup.md                # NEW - detailed OAuth setup guide
└── troubleshooting-gmail-api.md       # NEW - common error solutions

.gitignore                              # UPDATE - ensure credentials.json, token.json excluded
pyproject.toml                          # UPDATE - add google-auth-oauthlib, google-api-python-client
README.md                               # UPDATE - add Gmail setup instructions
```

**Structure Decision**: Single project structure (existing). This feature primarily adds **documentation and configuration**, not significant new code. Most changes are to existing `gmail_receiver.py` and test files. New files are primarily documentation in `docs/` directory.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations to track**: Constitution check passed all five principles without exceptions. No complexity justifications needed.
