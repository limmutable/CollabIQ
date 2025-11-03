# Implementation Plan: LLM-Based Company Matching

**Branch**: `007-llm-matching` | **Date**: 2025-11-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-llm-matching/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Phase 2b extends the existing GeminiAdapter (from Phase 1b) to perform intelligent company matching by injecting Notion Companies database context (from Phase 2a) into extraction prompts. The system will return matched company IDs with confidence scores for both primary startup and beneficiary companies, enabling downstream classification (Phase 2c) and Notion write operations (Phase 2d). This is a read-only operation that enhances entity extraction with semantic matching capabilities using Gemini 2.0 Flash's multilingual understanding.

## Technical Context

**Language/Version**: Python 3.12+ (established in project, using UV package manager)
**Primary Dependencies**:
- `google-generativeai` (Gemini API client, already integrated in Phase 1b)
- `notion-client` (Notion API, integrated in Phase 2a)
- `pydantic` (data validation, already used for ExtractedEntities model)
- `tenacity` (retry logic, from Phase 2a)

**Storage**:
- File-based JSON output to `data/extractions/{email_id}.json` (established in Phase 1b)
- File-based JSON cache in `data/notion_cache/` for company lists (Phase 2a, TTL: 6h data, 24h schema)

**Testing**: pytest (established pattern)
- Contract tests for GeminiAdapter interface extension
- Integration tests for company matching with mocked Notion data
- Unit tests for confidence score logic and prompt formatting

**Target Platform**: Linux/macOS server (Python CLI application)

**Project Type**: Single Python project with modular architecture (src/ + tests/)

**Performance Goals**:
- ≤3 seconds per email for complete extraction + matching (SC-003)
- ≤2000 tokens for company list prompt context (Assumption #4)
- ≥85% matching accuracy on test dataset (SC-001)

**Constraints**:
- Read-only Notion operations (no database writes until Phase 2d)
- Single Gemini API call for extraction + matching (no multi-LLM orchestration)
- Company list ≤500 entries for MVP (Assumption #3)
- Must work with existing Phase 1b ExtractedEntities schema (backward compatible extension)

**Scale/Scope**:
- 10 test companies (6 portfolio + 4 SSG affiliates) for validation
- 10 test emails (6 sample + 4 ground truth) for accuracy measurement
- 5 user stories (2 P1, 2 P2, 1 P3)
- 18 functional requirements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

- ✅ Feature specification (`spec.md`) exists and is complete
- ✅ User scenarios with acceptance criteria defined (5 user stories with Given-When-Then scenarios)
- ✅ Functional requirements documented (FR-001 through FR-018)
- ✅ Success criteria defined (SC-001 through SC-007, all measurable)
- ✅ Requirements are technology-agnostic at specification stage

**Status**: PASS - Complete specification with requirements checklist validation

### II. Incremental Delivery via Independent User Stories ✅

- ✅ User stories prioritized (P1: US1+US2, P2: US3+US4, P3: US5)
- ✅ Each user story independently testable:
  - US1 (P1): Match primary startup - testable with sample-001.txt alone
  - US2 (P1): Match beneficiary company - testable with sample-004.txt alone
  - US3 (P2): Handle variations - testable with synthetic fuzzy examples
  - US4 (P2): Handle no-match - testable with unknown company names
  - US5 (P3): LLM context formatting - testable without extraction logic
- ✅ US1+US2 together constitute viable MVP (matching both companies enables Phase 2c classification)
- ✅ Implementation proceeds in priority order (P1 → P2 → P3)

**Status**: PASS - MVP (US1+US2) delivers complete value; remaining stories are enhancements

### III. Test-Driven Development (TDD) ⚠️ OPTIONAL

**Tests explicitly required**: ✅ YES (spec includes Success Criteria with measurable accuracy targets)

**Test strategy** (when implementation begins):
- Contract tests MUST be written first for extended ExtractedEntities model
- Integration tests MUST be written first for company matching with mocked Notion data
- Unit tests for confidence score calibration and prompt formatting

**Status**: PASS (conditional) - Tests are required by spec; TDD will be enforced during implementation

### IV. Design Artifact Completeness 🔄 IN PROGRESS

Required artifacts from `/speckit.plan`:
- ✅ `plan.md` - This file (in progress)
- 🔄 `research.md` - Phase 0 (pending)
- 🔄 `data-model.md` - Phase 1 (pending)
- 🔄 `quickstart.md` - Phase 1 (pending)
- 🔄 `contracts/` - Phase 1 (pending)

**Status**: IN PROGRESS - Plan underway, research and design artifacts pending

### V. Simplicity & Justification ✅

**Complexity assessment**:
- ✅ Extends existing GeminiAdapter (no new LLM adapter)
- ✅ Reuses Phase 2a NotionIntegrator (no custom Notion client)
- ✅ Single API call for extraction + matching (no orchestration layer)
- ✅ No new data stores (uses existing file-based JSON cache)
- ✅ No new frameworks or abstractions

**Complexity violations**: NONE

**Status**: PASS - Feature adds minimal complexity by extending existing components

---

**Overall Gate Status**: ✅ PASS (with Phase 0/1 artifacts pending completion)

**Proceed to**: Phase 0 Research (resolve any NEEDS CLARIFICATION markers, document technical decisions)

## Project Structure

### Documentation (this feature)

```text
specs/007-llm-matching/
├── spec.md              # Feature specification (✅ complete)
├── plan.md              # This file (🔄 in progress)
├── research.md          # Phase 0 output (pending)
├── data-model.md        # Phase 1 output (pending)
├── quickstart.md        # Phase 1 output (pending)
├── contracts/           # Phase 1 output (pending)
│   └── gemini_adapter_extension.md  # Extended interface contract
├── checklists/
│   └── requirements.md  # Specification quality validation (✅ complete)
└── tasks.md             # Phase 2 output from /speckit.tasks (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── llm_adapters/
│   ├── gemini_adapter.py          # [MODIFY] Extend extract_entities() method
│   └── prompts/
│       └── extraction_prompt.txt  # [MODIFY] Add company list context section
├── llm_provider/
│   └── types.py                   # [MODIFY] Extend ExtractedEntities model
├── notion_integrator/
│   ├── integrator.py              # [USE] Existing NotionIntegrator.get_data()
│   ├── formatter.py               # [USE] Existing format_for_llm() function
│   └── cache.py                   # [USE] Existing cache (6h TTL for companies)
├── config/
│   └── settings.py                # [USE] Existing settings management
└── cli.py                         # [NO CHANGE] CLI remains unchanged

tests/
├── contract/
│   └── test_gemini_adapter_matching_contract.py  # [NEW] Extended interface tests
├── integration/
│   └── test_company_matching_integration.py      # [NEW] End-to-end matching tests
├── unit/
│   └── test_confidence_scores.py                 # [NEW] Confidence logic tests
└── fixtures/
    ├── sample_emails/              # [USE] Existing 6 test emails
    ├── ground_truth/               # [USE] Existing 4 validation emails
    └── mock_notion_data.json       # [NEW] Mocked Companies database (10 entries)

data/
├── extractions/                    # [USE] Existing JSON output directory
└── notion_cache/                   # [USE] Existing Phase 2a cache (6h/24h TTL)
```

**Structure Decision**: Single Python project (Option 1). This feature extends existing modules (`src/llm_adapters/gemini_adapter.py`, `src/llm_provider/types.py`) and reuses Phase 2a infrastructure (`src/notion_integrator/`). No new top-level directories or services required. Tests follow established `contract/`, `integration/`, `unit/` organization.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - This feature adheres to all constitution principles:
- ✅ Specification-first workflow followed
- ✅ Independent user stories (P1 MVP viable)
- ✅ TDD required and will be enforced
- ✅ Design artifacts in progress
- ✅ Minimal complexity (extends existing components only)

---

**Planning Phase Status**: Constitution gates passed. Proceeding to Phase 0 (Research) and Phase 1 (Design).
