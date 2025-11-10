# Implementation Plan: Enhanced Notion Field Mapping

**Branch**: `014-enhanced-field-mapping` | **Date**: 2025-11-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-enhanced-field-mapping/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature adds fuzzy string matching and auto-creation capabilities to enable proper population of three critical Notion database fields: 담당자 (Person in Charge), 스타트업명 (Startup Name), and 협력기관 (Partner Organization). Currently, these fields remain empty despite LLM extraction because they require exact page_id matches (relation fields) or user UUIDs (people field). The solution implements Jaro-Winkler fuzzy matching with configurable thresholds, auto-creates missing company entries, and matches person names to Notion workspace users.

## Technical Context

**Language/Version**: Python 3.12+ (established in project)
**Primary Dependencies**: rapidfuzz (fuzzy matching library - already in pyproject.toml), notion-client (Notion API), pydantic (data validation)
**Storage**: File-based (JSON cache for Notion user list with TTL), Notion API (Companies database CRUD)
**Testing**: pytest, pytest-mock (established in project)
**Target Platform**: Linux/macOS server (CLI application)
**Project Type**: Single project (existing src/ structure)
**Performance Goals**: Fuzzy matching completes in <2 seconds per email with 1000+ companies, CLI commands respond in <1 second
**Constraints**: Notion API rate limits (3 requests/second), Korean text UTF-8 encoding, similarity thresholds (0.85 for companies, 0.70 for persons)
**Scale/Scope**: ~50-100 companies in database, ~10-20 Notion workspace users, 20+ test emails for validation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

- [x] Feature specification (`spec.md`) exists and is complete
- [x] User scenarios with acceptance criteria defined (4 prioritized user stories)
- [x] Functional requirements documented (FR-001 through FR-020)
- [x] Success criteria defined (SC-001 through SC-008)
- [x] Requirements are technology-agnostic at specification stage

**Status**: PASSED - Complete spec with 4 user stories, 20 functional requirements, 8 success criteria

### II. Incremental Delivery via Independent User Stories ✅

- [x] User stories prioritized (P1: Fuzzy Matching, P1: Auto-Create, P2: Person Matching, P3: CLI)
- [x] Each story independently testable and demonstrable
- [x] User Story 1 (Company Fuzzy Matching) constitutes viable MVP
- [x] Implementation can proceed in priority order
- [x] Each story delivers deployable increment

**Status**: PASSED - 4 prioritized stories, P1 stories (Fuzzy Matching + Auto-Create) are both essential for MVP and can be tested independently

### III. Test-Driven Development (TDD) ✅

- [x] Tests required per specification (unit tests for fuzzy matching, integration tests for Notion API, E2E tests for field population)
- [x] Test-first discipline will be followed
- [x] Contract tests planned for FuzzyCompanyMatcher and PersonMatcher interfaces
- [x] Integration tests planned for Notion API interactions
- [x] E2E tests planned for full field population flow

**Status**: PASSED - Comprehensive test strategy defined in spec.md and roadmap. TDD will be mandatory.

### IV. Design Artifact Completeness ✅

- [x] `plan.md` with constitution check, technical context (complete)
- [x] `research.md` with technical decisions (complete)
- [x] `data-model.md` with entity definitions (complete)
- [x] `quickstart.md` with usage instructions (complete)
- [x] `contracts/` with API specifications (complete: fuzzy_company_matcher.yaml, person_matcher.yaml)
- [ ] `tasks.md` generated after planning complete (Phase 2 - `/speckit.tasks`)

**Status**: COMPLETE - All planning artifacts generated, ready for task generation

### V. Simplicity & Justification ✅

- [x] Defaulting to simplest solution (deterministic fuzzy matching, no ML)
- [x] No unnecessary abstractions introduced
- [x] Reusing existing components (NotionClient, FieldMapper, retry logic)
- [x] No constitution violations requiring justification

**Status**: PASSED - Solution uses existing patterns, adds minimal new components, avoids ML complexity

**INITIAL GATE DECISION**: ✅ PROCEED TO PHASE 0 (Research)
- All constitution principles satisfied or in-progress as expected
- No violations requiring justification
- Test strategy appropriate for feature scope
- User stories properly prioritized and independent

**POST-DESIGN GATE DECISION**: ✅ PROCEED TO PHASE 2 (Task Generation)
- All design artifacts complete (research.md, data-model.md, contracts/, quickstart.md)
- Constitution principles re-validated:
  - ✅ Specification-First: Complete spec drives all design decisions
  - ✅ Incremental Delivery: 4 independent user stories with clear priorities
  - ✅ TDD: Comprehensive test strategy (contract, integration, unit, E2E)
  - ✅ Design Completeness: All required artifacts generated
  - ✅ Simplicity: Minimal new components, reuses existing patterns, no unnecessary complexity
- Technical decisions documented with rationale
- API contracts specify clear boundaries for TDD
- No new constitution violations introduced
- Ready for task generation via `/speckit.tasks`

## Project Structure

### Documentation (this feature)

```text
specs/014-enhanced-field-mapping/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output - technical decisions
├── data-model.md        # Phase 1 output - entity definitions
├── quickstart.md        # Phase 1 output - usage guide
├── contracts/           # Phase 1 output - API specifications
│   ├── fuzzy_company_matcher.yaml
│   └── person_matcher.yaml
├── checklists/
│   └── requirements.md  # Spec quality validation (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── notion_integrator/          # Existing - will be enhanced
│   ├── field_mapper.py         # MODIFY: Add fuzzy matching integration
│   ├── client.py               # USE: For Notion API calls
│   ├── fetcher.py              # USE: For Companies database queries
│   ├── writer.py               # USE: For company creation
│   ├── cache.py                # USE: For user list caching
│   ├── fuzzy_matcher.py        # NEW: FuzzyCompanyMatcher service
│   └── person_matcher.py       # NEW: PersonMatcher service
│
├── collabiq/commands/          # Existing CLI - will be enhanced
│   └── notion.py               # MODIFY: Add match-company, match-person, list-users
│
└── models/                     # Existing - may add types
    └── matching.py             # NEW: CompanyMatch, PersonMatch result types

tests/
├── contract/                   # API boundary tests
│   ├── test_fuzzy_company_matcher.py     # NEW: FuzzyCompanyMatcher contract
│   └── test_person_matcher.py            # NEW: PersonMatcher contract
│
├── integration/                # Multi-component tests
│   ├── test_field_mapping_with_fuzzy_match.py  # NEW: Full field mapping flow
│   ├── test_company_autocreate.py              # NEW: Auto-creation workflow
│   └── test_person_matching_integration.py     # NEW: Person matching with Notion API
│
└── unit/                       # Single-component tests
    ├── test_fuzzy_matching_algorithm.py  # NEW: Jaro-Winkler similarity tests
    └── test_korean_name_normalization.py # NEW: Korean text handling tests
```

**Structure Decision**: Single project structure (existing pattern maintained). New components added to `notion_integrator/` module to keep field mapping logic co-located. CLI commands added to existing `collabiq/commands/notion.py`. Test organization follows existing contract/integration/unit pattern.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations requiring justification** - All constitution principles satisfied.
