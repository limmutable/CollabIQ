# Implementation Plan: Classification & Summarization

**Branch**: `008-classification-summarization` | **Date**: 2025-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-classification-summarization/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend Phase 2b's GeminiAdapter to classify collaboration types (dynamically fetched from Notion "협업형태" field) and intensity levels (이해/협력/투자/인수) using deterministic logic and Korean semantic analysis. Generate 3-5 sentence summaries (50-150 words) preserving key entities. Return confidence scores (0.0-1.0) for auto-acceptance (≥0.85) vs manual review (<0.85). Technical approach: (1) Fetch "협업형태" field values from Notion CollabIQ database at runtime using Phase 2a's NotionIntegrator.discover_database_schema(), (2) Apply deterministic type classification based on Phase 2b company classifications, (3) Use Gemini 2.0 Flash for Korean intensity classification and summarization, (4) Cache schema for session duration.

## Technical Context

**Language/Version**: Python 3.12 (established in project, using UV package manager)
**Primary Dependencies**:
- `google-generativeai` (Gemini 2.0 Flash for intensity classification + summarization)
- `notion-client` (Phase 2a - dynamic schema fetching)
- `pydantic` (data validation for extended ExtractedEntities model)
- Existing: GeminiAdapter (Phase 1b), NotionIntegrator (Phase 2a), Company matching (Phase 2b)

**Storage**: File-based JSON output (`data/extractions/{email_id}.json`) - no schema changes
**Testing**: pytest with existing test fixtures (tests/fixtures/sample_emails/sample-001.txt through sample-006.txt)
**Target Platform**: macOS/Linux server (established in project)
**Project Type**: Single project (extends existing `src/` structure)
**Performance Goals**: ≤4 seconds per email (Phase 1b extraction + Phase 2b matching + Phase 2c classification), single schema fetch per session
**Constraints**:
- Must maintain backward compatibility with Phase 1b/2b extraction
- Must use exact Notion field values (not hardcoded)
- Must support future "협업형태" value changes (A/B/C/D → 1/2/3/4, or adding types)
- ≥85% classification accuracy (type + intensity)

**Scale/Scope**:
- 4 collaboration types (dynamic, currently A/B/C/D)
- 4 intensity levels (이해/협력/투자/인수)
- 50-150 word summaries (3-5 sentences)
- Confidence threshold: 0.85 (auto-accept ≥0.85, manual review <0.85)
- Target: ≤25% manual review queue

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅ PASS

- ✅ Feature specification exists: [spec.md](spec.md)
- ✅ User scenarios with acceptance criteria: 4 user stories (P1: type + intensity, P2: summary + confidence)
- ✅ Functional requirements: FR-001 through FR-019 defined
- ✅ Success criteria: SC-001 through SC-007 defined (≥85% accuracy, performance targets)
- ✅ Technology-agnostic specification (no implementation details in spec)

### II. Incremental Delivery via Independent User Stories ✅ PASS

- ✅ User stories prioritized: P1 (type + intensity classification) delivers MVP, P2 (summary + confidence) adds value
- ✅ Each story independently testable:
  - P1 Story 1 (Type): Test with Phase 2b matched company IDs → verify exact Notion field values
  - P1 Story 2 (Intensity): Test with sample-001.txt through sample-006.txt → verify Korean keyword classification
  - P2 Story 3 (Summary): Test summary generation independently → verify 5 key entities preserved
  - P2 Story 4 (Confidence): Test confidence scoring independently → verify 0.85 threshold routing
- ✅ P1 constitutes viable MVP: Type + intensity classification enables complete collaboration tracking (core requirement)
- ✅ Implementation order: P1 first (classification), then P2 (summary/confidence)

### III. Test-Driven Development (TDD) ⚠️ CONDITIONAL

**Tests Required**: Yes (specification explicitly requires accuracy validation with test dataset)

**TDD Commitment**:
- ✅ Will write tests first for classification logic (type + intensity)
- ✅ Will write tests first for summary generation (entity preservation)
- ✅ Will use existing test fixtures (sample-001.txt through sample-006.txt) as ground truth
- ✅ Contract tests: GeminiAdapter response schema extension
- ✅ Integration tests: End-to-end email → classification → summary flow

**Test Strategy**:
1. Contract tests verify ExtractedEntities model extension (collaboration_type, collaboration_intensity, collaboration_summary, type_confidence, intensity_confidence)
2. Unit tests verify deterministic type classification logic (Portfolio+SSG=A, Portfolio+Portfolio=C, etc.)
3. Integration tests verify Korean intensity classification accuracy (≥85% on sample-001.txt through sample-006.txt)
4. Integration tests verify summary quality (5 key entities preserved in ≥90% of cases)

### IV. Design Artifact Completeness ⚠️ IN PROGRESS

**Required Artifacts** (this plan will generate):
- ✅ `plan.md`: This file (constitution check, technical context, structure) - IN PROGRESS
- ⏳ `research.md`: Phase 0 - Dynamic schema fetching pattern, Gemini prompt engineering for Korean classification
- ⏳ `data-model.md`: Phase 1 - Extended ExtractedEntities, CollaborationClassification, CollaborationSummary
- ⏳ `quickstart.md`: Phase 1 - Usage instructions for classification + summarization
- ⏳ `contracts/`: Phase 1 - GeminiAdapter response schema extension (JSON schema for new fields)

**Gate Status**: ⏳ Will complete in Phase 0-1 (this command)

### V. Simplicity & Justification ✅ PASS

**Complexity Introduced**: Minimal - extends existing patterns from Phase 1b + Phase 2b

**Justified Complexity**:
1. **Dynamic schema fetching**: Required by FR-002/FR-003 to support future "협업형태" value changes (not hardcoding A/B/C/D)
   - Simpler alternative rejected: Hardcode values → breaks when Notion admin changes field values
   - Chosen approach: Fetch once per session, cache for duration → future-proof + minimal performance impact

2. **Confidence scoring**: Required by P2 Story 4 and FR-012/FR-013 for manual review routing
   - Simpler alternative rejected: No confidence scores → all classifications require manual review (100% instead of target ≤25%)
   - Chosen approach: LLM returns confidence in JSON response → enables 0.85 threshold auto-acceptance

3. **Pattern matching for type codes**: Required by FR-004 to support future type identifier changes ([A]* → [1]*, etc.)
   - Simpler alternative rejected: Exact string matching → breaks if type names change but codes stay same
   - Chosen approach: Regex pattern `"[A]*"`, `"[B]*"` → flexible matching even if full names change

**Unnecessary Complexity Avoided**:
- ❌ No new LLM for type classification (deterministic logic based on Phase 2b company classifications)
- ❌ No complex NLP libraries for Korean (Gemini 2.0 Flash handles semantic understanding)
- ❌ No database schema changes (extends JSON output format)
- ❌ No new storage layer (reuses file-based extraction output)

### Constitution Compliance Summary

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Complete spec.md with all required sections |
| II. Independent User Stories | ✅ PASS | P1 (classification) is viable MVP, P2 adds value |
| III. Test-Driven Development | ⚠️ CONDITIONAL | Tests required, TDD committed, strategy defined |
| IV. Design Artifact Completeness | ⏳ IN PROGRESS | Will complete in Phase 0-1 of this command |
| V. Simplicity & Justification | ✅ PASS | Minimal complexity, all justified, no unnecessary abstractions |

**Gate Decision**: ✅ **PROCEED TO PHASE 0** - Constitution requirements satisfied, no violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
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
├── llm_adapters/
│   └── gemini_adapter.py         # EXTEND: Add classification + summarization logic
├── notion_integrator/
│   ├── integrator.py              # USE: discover_database_schema() for "협업형태" fetching
│   └── models.py                  # USE: DatabaseSchema, PropertySchema for schema parsing
├── models/                         # NEW: Classification service layer
│   └── classification_service.py  # Coordinates schema fetching + classification logic
├── config/
│   └── settings.py                # NO CHANGES: Reuses existing config
└── __init__.py

tests/
├── contract/
│   └── test_gemini_classification_contract.py  # NEW: ExtractedEntities schema extension
├── integration/
│   └── test_classification_e2e.py              # NEW: Email → classification → summary flow
├── unit/
│   ├── test_type_classification.py             # NEW: Deterministic type logic
│   ├── test_intensity_classification.py        # NEW: Korean keyword + LLM intensity
│   └── test_summary_generation.py              # NEW: Entity preservation + word count
└── fixtures/
    └── sample_emails/                           # EXISTING: Use sample-001.txt through sample-006.txt

data/
└── extractions/
    └── {email_id}.json           # EXTEND: Add collaboration_type, collaboration_intensity, collaboration_summary, *_confidence fields
```

**Structure Decision**: Single project structure (Option 1) - extends existing `src/` modules with minimal new files. **No new packages required** - only extending GeminiAdapter and adding a lightweight ClassificationService coordinator. Follows established CollabIQ pattern: adapter pattern (GeminiAdapter) + service layer (ClassificationService) + data models (Pydantic).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No constitution violations** - all complexity justified in Constitution Check section V. Simplicity & Justification.
---

## Constitution Check (Post-Design Re-evaluation)

*GATE: Re-check after Phase 1 design artifacts complete*

### IV. Design Artifact Completeness ✅ COMPLETE

**Required Artifacts** (generated in Phase 0-1):
- ✅ `plan.md`: This file - constitution check, technical context, structure COMPLETE
- ✅ `research.md`: Phase 0 complete - 4 technical decisions documented
- ✅ `data-model.md`: Phase 1 complete - 3 entity models defined with validation
- ✅ `quickstart.md`: Phase 1 complete - step-by-step usage guide with examples
- ✅ `contracts/gemini_adapter_extension.md`: Phase 1 complete - API contract with test cases

**Gate Status**: ✅ **PASS** - All required artifacts generated

### Post-Design Review

| Artifact | Quality Check | Status |
|----------|---------------|--------|
| research.md | 4 decisions with rationale + alternatives | ✅ PASS |
| data-model.md | 3 entity models + validation rules + migration strategy | ✅ PASS |
| contracts/gemini_adapter_extension.md | API signature + request/response format + error handling + 7 test cases | ✅ PASS |
| quickstart.md | Quick example + 6-step guide + 3 use cases + troubleshooting | ✅ PASS |

**Design Quality**:
- ✅ All unknowns from Technical Context resolved (no NEEDS CLARIFICATION remaining)
- ✅ Backward compatibility maintained (Phase 1b/2b extraction still works)
- ✅ Test strategy defined (contract + unit + integration tests)
- ✅ Performance requirements documented (≤4 seconds per email)
- ✅ Error handling and graceful degradation specified

### Final Constitution Compliance

| Principle | Initial | Post-Design | Notes |
|-----------|---------|-------------|-------|
| I. Specification-First | ✅ PASS | ✅ PASS | spec.md unchanged |
| II. Independent User Stories | ✅ PASS | ✅ PASS | MVP viability confirmed |
| III. Test-Driven Development | ⚠️ CONDITIONAL | ✅ COMMITTED | Test strategy defined in contracts + quickstart |
| IV. Design Artifact Completeness | ⏳ IN PROGRESS | ✅ COMPLETE | All artifacts generated |
| V. Simplicity & Justification | ✅ PASS | ✅ PASS | No new complexity introduced |

**Final Gate Decision**: ✅ **APPROVED FOR TASK GENERATION** (`/speckit.tasks`)

---

## Summary

**Implementation Plan Complete**: ✅

**Branch**: `008-classification-summarization`

**Generated Artifacts**:
1. [plan.md](plan.md) - This file (implementation plan with constitution check)
2. [research.md](research.md) - 4 technical decisions (dynamic schema, intensity prompt, summarization, confidence calibration)
3. [data-model.md](data-model.md) - 3 entity models (CollaborationClassification, CollaborationSummary, ExtractedEntitiesWithClassification)
4. [contracts/gemini_adapter_extension.md](contracts/gemini_adapter_extension.md) - API contract with 7 test cases
5. [quickstart.md](quickstart.md) - Usage guide with 3 use cases and troubleshooting

**Ready for Next Phase**: ✅ Run `/speckit.tasks` to generate implementation tasks

**Estimated Complexity**: **Low** (2-3 days)
- Extends existing GeminiAdapter with minimal new code
- Reuses Phase 2a NotionIntegrator for dynamic schema fetching
- Deterministic type classification (no LLM needed)
- Single Gemini API call for intensity + summary
- No database schema changes (extends JSON output)

**Key Technologies**:
- Python 3.12 (established)
- Gemini 2.5 Flash (configured in .env)
- Pydantic (data validation)
- NotionIntegrator (Phase 2a - schema fetching)
- GeminiAdapter (Phase 1b/2b - entity extraction + matching)

---

**Implementation Plan Status**: ✅ **COMPLETE**
**Next Command**: `/speckit.tasks` to generate dependency-ordered tasks organized by user story
