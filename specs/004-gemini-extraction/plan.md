# Implementation Plan: Gemini Entity Extraction (MVP)

**Branch**: `004-gemini-extraction` | **Date**: 2025-11-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-gemini-extraction/spec.md`

## Summary

Implement LLM-based entity extraction from Korean/English emails using Gemini 2.5 Flash API. The system extracts 5 key entities (담당자, 스타트업명, 협업기관, 협업내용, 날짜) from cleaned email text and outputs structured JSON with confidence scores. This enables the MVP milestone: team members can manually create Notion entries from JSON output, reducing manual processing time from 5-7 minutes to ≤2 minutes per email (30-40% time reduction).

**Technical Approach**: Abstract LLMProvider interface with GeminiAdapter implementation for future LLM swappability. No fuzzy matching, no Notion integration, no classification—pure entity extraction only.

## Technical Context

**Language/Version**: Python 3.12+ (established in project)
**Primary Dependencies**:
- `google-generativeai` (Gemini Python SDK) for LLM API
- `pydantic` (existing) for data models and validation
- `python-dateutil` or `dateparser` for multi-format date parsing

**Storage**: File-based JSON output (`data/extractions/{email_id}.json`)
**Testing**:
- `pytest` (existing) for unit/integration tests
- `pytest-mock` (existing) for mocking Gemini API calls
- Test dataset: 20 Korean + 10 English collaboration emails (from Phase 0 validation)

**Target Platform**: Linux server (development: macOS/Linux)
**Project Type**: Single project (monolithic service architecture)
**Performance Goals**:
- Single email extraction: ≤5 seconds (excluding Gemini API latency)
- Batch processing: 20 emails without memory issues
- Gemini API rate limit: 60 requests/minute (sufficient for MVP)

**Constraints**:
- Gemini API latency: typically 1-3 seconds per request (external dependency)
- API key security: MUST NOT log API keys
- Confidence threshold: ≥0.85 for high-confidence extractions
- Date parsing: handle Korean formats ("11월 1주"), relative dates ("yesterday"), absolute dates (YYYY-MM-DD)

**Scale/Scope**:
- MVP target: 20-30 emails/day (manual testing phase)
- Test coverage: ≥85% entity extraction accuracy on 30-email test dataset
- 3 user stories (P1: single email, P2: batch, P3: confidence review)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅

- ✅ Complete specification exists ([spec.md](spec.md))
- ✅ User scenarios with acceptance criteria defined (3 stories, 10 scenarios)
- ✅ Functional requirements documented (FR-001 through FR-012)
- ✅ Success criteria defined (SC-001 through SC-007)
- ✅ Requirements are technology-agnostic (focus on extracted entities, not implementation)

### Principle II: Incremental Delivery via Independent User Stories ✅

- ✅ User stories prioritized (P1, P2, P2)
- ✅ Each story independently testable:
  - P1: Single email → verify 5 entities extracted
  - P2: Batch → verify 20 emails processed
  - P3: Confidence review → verify low-confidence flagging
- ✅ P1 constitutes viable MVP (single email extraction delivers immediate value)
- ✅ Sequential implementation planned (P1 → P2 → P3)
- ✅ Each story completion = deployable increment

### Principle III: Test-Driven Development (TDD) - MANDATORY ✅

**Tests Required**: Yes (explicitly stated in spec: "Integration tests for Gemini API, accuracy tests on sample emails")

TDD Commitment:
- ✅ Contract tests for LLMProvider interface (write interface test first)
- ✅ Integration tests for GeminiAdapter (mock API first, then implement)
- ✅ Accuracy tests for extraction (define ground truth first, then extract)
- ✅ Unit tests for date parsing (test cases first, then parser)
- ✅ All tests written BEFORE implementation code

### Principle IV: Design Artifact Completeness ⏳

**Status**: In Progress (this planning phase)

Required artifacts:
- ✅ `plan.md` - This file
- ⏳ `research.md` - Phase 0 output (next step)
- ⏳ `data-model.md` - Phase 1 output
- ⏳ `quickstart.md` - Phase 1 output
- ⏳ `contracts/` - Phase 1 output

**Gate**: Implementation MUST NOT begin until all artifacts complete.

### Principle V: Simplicity & Justification ✅

**Complexity Audit**:
- Abstract LLMProvider interface: **JUSTIFIED** (enables future Gemini→GPT/Claude swap without rewriting business logic, per FR-011)
- Pydantic models: **ALREADY ESTABLISHED** (project standard, no new complexity)
- File-based storage: **SIMPLEST OPTION** (no database needed for MVP)
- Date parsing library: **NECESSARY** (handling "11월 1주", "yesterday", "2025-01-15" without custom parser would be error-prone)

**Rejected Alternatives**:
- ❌ Direct Gemini API calls without abstraction: Would lock into Gemini, violating FR-011 (swappability requirement)
- ❌ Database storage: Overengineering for MVP (20-30 emails/day)
- ❌ Custom date parser: Reinventing wheel, lower reliability than battle-tested libraries

**No Constitution Violations**: All complexity justified by explicit requirements.

## Project Structure

### Documentation (this feature)

```text
specs/004-gemini-extraction/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0: Gemini API investigation, date parsing library comparison
├── data-model.md        # Phase 1: ExtractedEntities, LLMProvider, ExtractionBatch models
├── quickstart.md        # Phase 1: Usage guide for CLI tool
├── contracts/           # Phase 1: LLMProvider interface specification (OpenAPI/Pydantic)
│   └── llm_provider.yaml
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2: Implementation tasks (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── llm_provider/              # NEW - LLM abstraction layer
│   ├── __init__.py
│   ├── base.py                # Abstract LLMProvider base class
│   ├── types.py               # Pydantic models (ExtractedEntities, ConfidenceScores)
│   └── exceptions.py          # LLM-specific exceptions
├── llm_adapters/              # NEW - LLM implementations
│   ├── __init__.py
│   ├── gemini_adapter.py      # GeminiAdapter(LLMProvider) implementation
│   └── prompts/               # Prompt templates
│       └── extraction_prompt.txt
├── models/                    # EXISTING - shared data models
│   └── (add extraction models if needed)
├── cli/                       # EXISTING - command-line tools
│   └── extract_entities.py   # NEW - CLI tool for manual testing
└── config/                    # EXISTING (via src/config/)
    └── settings.py            # UPDATE - add Gemini API key field

tests/
├── contract/                  # NEW - interface tests
│   └── test_llm_provider_interface.py
├── integration/               # NEW - Gemini API tests
│   └── test_gemini_adapter.py
├── unit/                      # NEW - component tests
│   ├── test_date_parsing.py
│   └── test_confidence_scoring.py
└── fixtures/                  # NEW - test data
    ├── sample_emails/         # 30 cleaned email samples (20 Korean + 10 English)
    │   ├── korean_001.txt
    │   └── english_001.txt
    ├── ground_truth/          # Expected extraction results
    │   └── GROUND_TRUTH.md
    └── mocks/
        └── gemini_responses.json
```

**Structure Decision**: Single project structure (Option 1) selected because:
- Monolithic service architecture (per ARCHITECTURE.md)
- No frontend/backend split
- All components in single deployment unit
- Follows existing CollabIQ project structure (`src/`, `tests/`)

**New Directories**:
- `src/llm_provider/` - Abstract LLM interface (future-proofs for GPT/Claude)
- `src/llm_adapters/` - Concrete LLM implementations (Gemini now, others later)
- `tests/fixtures/sample_emails/` - Test dataset for accuracy validation

## Complexity Tracking

> **No Constitution Violations** - This section intentionally empty.

All complexity justified under Principle V (Simplicity & Justification):
- LLMProvider abstraction: Required by FR-011 (swappability)
- Date parsing library: Necessary for multi-format date handling (FR-008)
- File-based storage: Simplest option for MVP (vs database)

## Next Steps

This planning command will now proceed with Phase 0 (Research) and Phase 1 (Design) to generate the required artifacts before implementation can begin.
