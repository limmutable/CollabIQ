# Implementation Plan: Infisical Secret Management Integration

**Branch**: `003-infisical-secrets` | **Date**: 2025-11-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-infisical-secrets/spec.md`

## Summary

Replace local .env file credential storage with Infisical centralized secret management platform. Integrate Infisical Python SDK to securely retrieve API keys (Gmail, Gemini, Notion) with caching, environment isolation, and fallback mechanisms. This eliminates hardcoded credentials in version control and streamlines developer onboarding by enabling machine identity-based authentication.

## Technical Context

**Language/Version**: Python 3.12 (established in project)
**Primary Dependencies**:
- Existing: pydantic>=2.12.3, pydantic-settings>=2.11.0
- New: infisicalsdk (Python SDK for Infisical)

**Storage**: Local in-memory cache for secrets (TTL-based), existing file-based .env fallback
**Testing**: pytest (existing test infrastructure), pytest-mock for Infisical SDK mocking
**Target Platform**: Local development (macOS/Linux), Google Cloud Run (production)
**Project Type**: Single project (existing src/ structure)
**Performance Goals**: <500ms secret retrieval latency on application startup
**Constraints**:
- Must not break existing .env file fallback for offline development
- Must integrate with existing Pydantic settings (src/config/settings.py)
- Cache TTL default 60 seconds, configurable 0-3600 seconds

**Scale/Scope**: 3 API credentials initially (Gmail, Gemini, Notion), 3 environments (dev, staging, prod)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Specification-First Development ✅
- **Status**: PASS
- **Evidence**: Complete spec.md exists with user stories, functional requirements (FR-001 through FR-013), and success criteria (SC-001 through SC-007)
- **Validation**: All requirements are technology-agnostic at specification stage

### Incremental Delivery via Independent User Stories ✅
- **Status**: PASS
- **Evidence**: 4 prioritized user stories (P1: Secure API Key Storage, P2: Developer Onboarding, P3: Automated Secret Rotation, P2: Environment-Specific Management)
- **MVP Definition**: P1 (Secure API Key Storage) constitutes viable MVP - application can retrieve secrets from Infisical and start without .env files
- **Independence**: Each story is independently testable and demonstrable
- **Validation**: P1 alone delivers value (eliminates hardcoded credentials); P2-P3 enhance but are not required for basic functionality

### Test-Driven Development (TDD) - MANDATORY (when tests requested) ✅
- **Status**: PASS (tests required)
- **Evidence**: Existing pytest infrastructure (45% coverage from Phase 1a)
- **Plan**: Contract tests for Infisical SDK integration, integration tests for settings loading
- **Commitment**: Tests will be written before implementation (red-green-refactor cycle)

### Design Artifact Completeness ⏳
- **Status**: IN PROGRESS
- **Required Artifacts**:
  - plan.md ✅ (this file)
  - research.md ⏳ (Phase 0)
  - data-model.md ⏳ (Phase 1)
  - contracts/ ⏳ (Phase 1)
  - quickstart.md ⏳ (Phase 1)
  - tasks.md ⏳ (/speckit.tasks command after planning)
- **Validation**: Will be completed before implementation begins

### Simplicity & Justification ✅
- **Status**: PASS
- **Default Simplicity**: Using existing Pydantic settings pattern, adding Infisical as optional layer
- **Justified Complexity**: None identified yet (will be documented in Complexity Tracking if violations found during design)
- **YAGNI Compliance**: Building only what is specified (P1-P3 user stories), not adding folder organization, approval workflows, or multi-platform support yet

## Project Structure

### Documentation (this feature)

```text
specs/003-infisical-secrets/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technical research)
├── data-model.md        # Phase 1 output (entity definitions)
├── quickstart.md        # Phase 1 output (usage instructions)
├── contracts/           # Phase 1 output (Infisical SDK integration contracts)
│   └── infisical_client.yaml  # InfisicalClient interface specification
├── checklists/          # Quality validation
│   └── requirements.md  # Specification quality checklist (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── config/
│   ├── __init__.py
│   ├── settings.py           # MODIFIED: Integrate Infisical secret loading
│   ├── infisical_client.py   # NEW: Infisical SDK wrapper
│   ├── logging_config.py     # Existing
│   └── validation.py         # MODIFIED: Add Infisical connectivity check
├── models/                   # Existing
├── email_receiver/           # Existing
├── content_normalizer/       # Existing
├── llm_provider/             # Existing (Phase 1b)
├── llm_adapters/             # Existing (Phase 1b)
├── notion_integrator/        # Existing (Phase 2a)
├── verification_queue/       # Existing (Phase 3a)
├── reporting/                # Existing (Phase 4a)
└── cli.py                    # MODIFIED: Add --verify-infisical command

tests/
├── unit/
│   ├── test_infisical_client.py    # NEW: Infisical SDK wrapper tests
│   └── test_settings_infisical.py  # NEW: Settings integration tests
├── integration/
│   └── test_infisical_integration.py  # NEW: End-to-end secret retrieval tests
└── fixtures/
    └── infisical/
        ├── mock_secrets.json         # NEW: Mock Infisical responses
        └── mock_auth_responses.json  # NEW: Mock authentication responses

docs/
└── architecture/
    └── TECHSTACK.md          # MODIFIED: Add Infisical to tech stack

pyproject.toml                # MODIFIED: Add infisicalsdk dependency
.env.example                  # MODIFIED: Add Infisical configuration examples
README.md                     # MODIFIED: Add Infisical setup instructions
```

**Structure Decision**: Extending existing single project structure (src/) by adding Infisical client wrapper in src/config/ module. This keeps secret management logic co-located with existing settings management (Pydantic), maintaining architectural consistency. No new top-level directories required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No Constitution violations identified at planning stage.**

If complexity emerges during implementation (Phase 1-2), document here with justification.

---

## Phase 0: Research & Technical Investigation

**Goal**: Resolve all technical unknowns and validate technology choices for Infisical integration

### Research Tasks

#### R1: Infisical Python SDK Integration Patterns
- **Question**: How does infisicalsdk integrate with existing Pydantic settings?
- **Investigation**:
  - Review infisicalsdk documentation for custom settings sources
  - Examine Pydantic v2 settings_customise_sources pattern
  - Test infisical SDK initialization patterns (client creation, authentication flow)
- **Decision Criteria**: Must integrate without breaking existing .env file fallback
- **Output**: Integration pattern recommendation (wrapper vs. custom settings source)

#### R2: Caching Strategy & Performance
- **Question**: How should secret caching be implemented to meet <500ms startup latency?
- **Investigation**:
  - Test infisicalsdk built-in caching behavior (cache_ttl parameter)
  - Measure cache hit/miss latency (mocked Infisical API)
  - Evaluate fallback behavior when Infisical unavailable
- **Decision Criteria**: Startup latency <500ms (SC-003), 99.9% reliability with cache fallback (SC-004)
- **Output**: Caching architecture (in-memory only vs. disk persistence)

#### R3: Authentication Flow & Machine Identities
- **Question**: How should Universal Auth machine identities be stored and managed?
- **Investigation**:
  - Review Universal Auth client_id/client_secret requirements
  - Determine storage location for machine identity credentials (env vars, config file, CLI input)
  - Test authentication error handling (invalid credentials, expired tokens)
- **Decision Criteria**: Secure storage, easy rotation, clear error messages
- **Output**: Authentication pattern recommendation

#### R4: Environment Isolation Implementation
- **Question**: How should environment-specific secrets be organized in Infisical?
- **Investigation**:
  - Compare single project with environment slugs vs. multiple projects
  - Test environment slug parameter usage in SDK
  - Validate access control separation (dev cannot access prod)
- **Decision Criteria**: Clear separation, easy to understand, minimal configuration
- **Output**: Environment organization pattern

#### R5: Testing Strategy for Infisical Integration
- **Question**: How should Infisical SDK be mocked for unit/integration tests?
- **Investigation**:
  - Review pytest-mock patterns for SDK mocking
  - Create sample mock responses for get_secret_by_name, list_secrets
  - Test error scenarios (network failure, auth failure, missing secrets)
- **Decision Criteria**: Tests run offline, comprehensive error coverage
- **Output**: Mocking patterns and test fixtures structure

#### R6: Error Handling & Fallback Mechanisms
- **Question**: What error conditions must be handled and how?
- **Investigation**:
  - List all Infisical SDK exception types
  - Define fallback behavior for each error type (cache, .env, fail)
  - Test partial failure scenarios (some secrets available, others missing)
- **Decision Criteria**: Clear error messages, graceful degradation, no silent failures
- **Output**: Error handling decision matrix

### Research Output Location

All findings will be consolidated in [research.md](research.md) with sections:
- Decision: [technology/pattern chosen]
- Rationale: [why this choice]
- Alternatives Considered: [other options evaluated]
- Implementation Notes: [key details for Phase 1]

---

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete with all R1-R6 decisions made

### Phase 1.1: Data Model (data-model.md)

**Entities**:

1. **InfisicalConfig**
   - Attributes: enabled (bool), host (str), project_id (str), environment_slug (str), client_id (str), client_secret (str), cache_ttl (int)
   - Purpose: Configuration for Infisical client initialization
   - Relationships: Used by InfisicalClient
   - Validation: client_id/client_secret required if enabled=True

2. **SecretCache**
   - Attributes: secrets (dict[str, str]), last_updated (datetime), ttl_seconds (int)
   - Purpose: In-memory cache for retrieved secrets
   - Behavior: Expire secrets after TTL, refresh on cache miss
   - Relationships: Managed by InfisicalClient

3. **SecretValue**
   - Attributes: key (str), value (str), environment (str), confidence (bool = cached or fresh)
   - Purpose: Individual secret with metadata
   - Relationships: Retrieved by InfisicalClient, consumed by Settings

**State Transitions**:
- SecretCache: Empty → Populated (first fetch) → Stale (TTL expired) → Refreshed (refetch)
- InfisicalClient: Uninitialized → Authenticated → Ready → Disconnected (on error)

### Phase 1.2: API Contracts (contracts/)

**Contract 1: InfisicalClient Interface** (infisical_client.yaml)

```yaml
InfisicalClient:
  description: Wrapper around Infisical Python SDK for secret retrieval
  initialization:
    parameters:
      - host: string (default: https://app.infisical.com)
      - project_id: string (required)
      - environment_slug: string (required, e.g., "dev", "staging", "prod")
      - client_id: string (required for Universal Auth)
      - client_secret: string (required for Universal Auth)
      - cache_ttl: integer (default: 60, range: 0-3600)
    raises:
      - InfisicalAuthError: Invalid client_id/client_secret
      - InfisicalConnectionError: Cannot reach Infisical host

  methods:
    get_secret:
      parameters:
        - secret_name: string (required)
      returns:
        - secret_value: string
      raises:
        - SecretNotFoundError: Secret does not exist in Infisical
        - InfisicalCacheMissError: Cache expired and API unreachable (with fallback to .env)
      behavior:
        - Check cache first (if not expired)
        - Fetch from Infisical API if cache miss
        - Update cache with fetched value
        - Log retrieval operation (without logging secret value)

    get_all_secrets:
      parameters: none
      returns:
        - secrets: dict[str, str] (key-value pairs)
      raises:
        - InfisicalConnectionError: Cannot fetch secrets
      behavior:
        - Fetch all secrets for configured project_id + environment_slug
        - Cache all retrieved secrets
        - Return as dictionary

    refresh_cache:
      parameters: none
      returns: none
      raises:
        - InfisicalConnectionError: Cannot refresh cache
      behavior:
        - Force cache refresh regardless of TTL
        - Fetch all secrets from Infisical API
        - Update internal cache

    is_connected:
      parameters: none
      returns:
        - connected: boolean
      raises: none
      behavior:
        - Test connectivity to Infisical API
        - Return True if reachable, False otherwise
```

**Contract 2: Settings Integration** (not a separate file, documented here)

Modified `Settings` class behavior:
- If `INFISICAL_ENABLED=true`, initialize InfisicalClient during `__init__`
- Override field defaults with values from InfisicalClient.get_secret()
- Fall back to .env file values if Infisical unavailable
- Log which source provided each secret (Infisical, cache, .env, default)

### Phase 1.3: Quickstart Guide (quickstart.md)

**Sections**:
1. Prerequisites (Infisical account, project created, machine identity provisioned)
2. Installation (uv add infisicalsdk)
3. Configuration (.env variables: INFISICAL_ENABLED, INFISICAL_PROJECT_ID, etc.)
4. First Secret Retrieval (step-by-step example)
5. Environment Setup (dev vs prod configuration)
6. Troubleshooting (common errors and solutions)
7. Verification (collabiq verify-infisical command)

### Phase 1.4: Agent Context Update

Run: `.specify/scripts/bash/update-agent-context.sh claude`

This will:
- Detect Claude AI agent usage
- Update CLAUDE.md with Infisical SDK dependency
- Preserve manual additions between markers
- Add only new technology (infisicalsdk)

---

## Re-evaluated Constitution Check (Post-Design)

### Specification-First Development ✅
- **Status**: PASS
- **Evidence**: Design artifacts (data-model.md, contracts/, quickstart.md) all derived from spec.md
- **Validation**: No implementation details added that weren't specified in requirements

### Incremental Delivery via Independent User Stories ✅
- **Status**: PASS
- **Evidence**: Phase 1 design supports P1 MVP (basic secret retrieval), with P2-P3 features as optional enhancements
- **Validation**: InfisicalClient can be deployed with minimal feature set (get_secret only), then enhanced

### Test-Driven Development ✅
- **Status**: PASS
- **Evidence**: Contract tests planned for InfisicalClient interface, integration tests for Settings
- **Commitment**: Tests will be written before implementation code

### Design Artifact Completeness ✅
- **Status**: PASS (all required artifacts exist)
- **Evidence**:
  - plan.md ✅
  - research.md ✅ (Phase 0 complete)
  - data-model.md ✅ (Phase 1.1 complete)
  - contracts/ ✅ (Phase 1.2 complete)
  - quickstart.md ✅ (Phase 1.3 complete)
- **Next Step**: Generate tasks.md via /speckit.tasks

### Simplicity & Justification ✅
- **Status**: PASS
- **Evidence**: No unnecessary abstractions introduced
- **Rationale for chosen patterns**:
  - Wrapper class (InfisicalClient) justified by need for caching + error handling logic
  - In-memory cache justified by performance requirement (<500ms startup)
  - Optional flag (INFISICAL_ENABLED) justified by need for gradual rollout

**No Constitution violations. Ready for task generation (/speckit.tasks) and implementation (/speckit.implement).**

---

## Next Steps

1. **Review & Approve**: Validate this plan against specification
2. **Run `/speckit.tasks`**: Generate dependency-ordered tasks.md organized by user story
3. **Run `/speckit.implement`**: Execute tasks in priority order with TDD discipline

**Planning Phase Complete** ✅
