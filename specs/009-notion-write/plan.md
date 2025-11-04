# Implementation Plan: Notion Write Operations

**Branch**: `009-notion-write` | **Date**: 2025-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-notion-write/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Phase 2d implements Notion write operations to persist extracted and classified email data to the CollabIQ Notion database. The feature completes the end-to-end automation pipeline by:

1. **Creating Notion database entries** from Phase 2c output (entity extraction + company matching + classification + summarization)
2. **Linking company relations** using Phase 2b matched company IDs
3. **Detecting duplicates** before write using email_id query
4. **Handling errors gracefully** with file-based dead letter queue for failed writes
5. **Mapping field types dynamically** using Phase 2a schema discovery

**Technical Approach** (from research.md):
- Extend existing `NotionIntegrator` with `NotionWriter` class
- Reuse `NotionClient` infrastructure (rate limiting, error handling)
- Schema-aware field mapping with UTF-8 Korean text support
- Simple 3-attempt retry for transient errors (no exponential backoff)
- File-based DLQ in `data/dlq/` with Pydantic serialization

## Technical Context

**Language/Version**: Python 3.12+ (established in project)
**Primary Dependencies**:
- `notion-client` (official Notion Python SDK, already installed from Phase 2a)
- `pydantic` v2 (data validation, already used throughout project)
- `tenacity` (retry logic, already installed from Phase 2a)

**Storage**:
- Notion API (CollabIQ database writes)
- File-based DLQ: `data/dlq/notion_write_failures_{timestamp}.json`

**Testing**:
- `pytest` (established framework)
- `pytest-asyncio` (async test support, already installed)
- Contract tests for NotionWriter, FieldMapper, DLQManager interfaces
- Integration tests for E2E write workflows

**Target Platform**: Linux/macOS server (Python application)

**Project Type**: Single project (backend data processing pipeline)

**Performance Goals**:
- ≤2 seconds per write operation (including duplicate check, field mapping, API call)
- ~1.5 emails/sec sustained throughput (1 duplicate check + 1 write = 2 API calls @ 3 req/sec rate limit)
- <10ms field mapping time

**Constraints**:
- Notion API rate limit: 3 requests/second (averaged)
- Notion field character limits: 2000 chars for rich_text
- Duplicate check adds 1 extra API call per email
- Synchronous writes (no queue - deferred to Phase 3a)

**Scale/Scope**:
- Initial: ~10-50 emails/day
- Phase 2e: ~100-500 emails/day
- Single CollabIQ database (multiple databases out of scope)
- 11 Korean field names with English mappings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅ PASS

- **Status**: PASS
- **Evidence**: Complete specification exists at `spec.md` with:
  - 3 prioritized user stories (P1: Basic Write, P2: Duplicate Detection, P3: Field Mapping)
  - 13 functional requirements (FR-001 to FR-013)
  - 7 measurable success criteria (SC-001 to SC-007)
  - All requirements technology-agnostic at spec level
- **Verification**: Spec approved and clarified before planning began

### II. Incremental Delivery via Independent User Stories ✅ PASS

- **Status**: PASS
- **Evidence**:
  - **P1 (MVP)**: Write extracted email data to Notion - independently testable, deliverable value (data visible in Notion)
  - **P2**: Handle duplicate detection - independently testable, can be developed after P1
  - **P3**: Map field types correctly - independently testable, technical robustness layer
- **Verification**: Each user story has "Independent Test" description and acceptance scenarios
- **MVP Validation**: P1 alone constitutes viable delivery - basic write functionality with manual duplicate handling acceptable

### III. Test-Driven Development (TDD) ✅ PASS (MANDATORY)

- **Status**: PASS - TDD required and planned
- **Evidence**:
  - Spec section "User Scenarios & Testing" defines acceptance criteria for all user stories
  - Contract tests required for NotionWriter, FieldMapper, DLQManager interfaces
  - Integration tests required for E2E write workflows
  - Test strategy: Write tests first (red) → implement (green) → refactor
- **Test Coverage**:
  - Contract tests: Validate API contracts (method signatures, error conditions)
  - Integration tests: E2E workflows (write entry, detect duplicate, handle errors)
  - Unit tests: Field mapping, DLQ serialization (optional, as needed)
- **Verification**: Tasks will specify "write tests first" for each component

### IV. Design Artifact Completeness ✅ PASS

- **Status**: PASS - All artifacts complete
- **Evidence**:
  - ✅ `spec.md` (complete, clarified, approved)
  - ✅ `plan.md` (this file, constitution check passed)
  - ✅ `research.md` (1,048 lines, 5 research areas complete)
  - ✅ `data-model.md` (429 lines, 4 entities documented)
  - ✅ `contracts/` (3 contracts, 2,129 lines total)
  - ✅ `quickstart.md` (738 lines, 10 sections)
- **Verification**: All Phase 0 and Phase 1 artifacts generated and validated
- **Next**: `/speckit.tasks` command will generate `tasks.md` from these artifacts

### V. Simplicity & Justification ✅ PASS

- **Status**: PASS - No violations, defaults to simplest solutions
- **Evidence**:
  - File-based DLQ (simplest persistent storage, no database)
  - 3-attempt immediate retry (no exponential backoff complexity)
  - Extend existing `NotionIntegrator` (reuse infrastructure, no new class hierarchy)
  - Schema-aware field mapping (dynamic but straightforward, no DSL)
  - Skip-by-default duplicate behavior (safest, simplest)
- **Complexity Tracking**: No violations to document
- **YAGNI Applied**:
  - No batch writes (not in spec)
  - No update operations (create-only, out of scope)
  - No webhook notifications (not in spec)
  - No rollback/transactions (partial writes acceptable per spec)

### Constitution Check Summary

**Overall Status**: ✅ **PASS** - Ready for implementation

All 5 constitution principles satisfied:
1. ✅ Specification-first complete
2. ✅ Independent user stories defined
3. ✅ TDD mandatory and planned
4. ✅ Design artifacts complete
5. ✅ Simplicity maintained, no unjustified complexity

**Gate Decision**: Proceed to Phase 2 (task generation via `/speckit.tasks`)

## Project Structure

### Documentation (this feature)

```text
specs/009-notion-write/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (Phase 0-1 complete)
├── research.md          # Technical research (1,048 lines, 5 areas)
├── data-model.md        # Entity definitions (429 lines, 4 entities)
├── quickstart.md        # Usage instructions (738 lines, 10 sections)
├── contracts/           # API/interface contracts
│   ├── notion_writer_contract.md    (623 lines)
│   ├── field_mapper_contract.md     (690 lines)
│   └── dlq_manager_contract.md      (816 lines)
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT YET CREATED)
```

### Source Code (repository root)

```text
src/
├── notion_integrator/
│   ├── __init__.py           # Package initialization (exists)
│   ├── integrator.py         # Main NotionIntegrator class (exists from Phase 2a)
│   ├── client.py             # NotionClient with rate limiting (exists from Phase 2a)
│   ├── fetcher.py            # Data fetching (exists from Phase 2a)
│   ├── formatter.py          # LLM formatting (exists from Phase 2a)
│   ├── cache.py              # Cache management (exists from Phase 2a)
│   ├── schema.py             # Schema discovery (exists from Phase 2a)
│   ├── exceptions.py         # Exception hierarchy (exists from Phase 2a)
│   ├── writer.py             # NEW: NotionWriter class for write operations
│   ├── field_mapper.py       # NEW: FieldMapper for Pydantic → Notion mapping
│   └── dlq_manager.py        # NEW: DLQManager for failed write handling
├── llm_provider/
│   └── types.py              # ExtractedEntitiesWithClassification model (exists from Phase 2c)
└── config/
    └── settings.py           # Environment variables (exists, may add DUPLICATE_BEHAVIOR)

tests/
├── contract/
│   ├── test_notion_writer.py        # NEW: NotionWriter contract tests
│   ├── test_field_mapper.py         # NEW: FieldMapper contract tests
│   └── test_dlq_manager.py          # NEW: DLQManager contract tests
├── integration/
│   ├── test_notion_write_e2e.py     # NEW: E2E write workflow tests
│   └── test_duplicate_detection.py  # NEW: Duplicate detection integration
├── unit/
│   └── test_field_mapping_logic.py  # NEW: Field mapping unit tests (optional)
└── manual/
    └── test_phase2d_notion_write.py # NEW: Manual demo script (Phase 2c pattern)

data/
└── dlq/                    # NEW: Dead letter queue directory
    └── notion_write_failures_{timestamp}.json  # Failed write records

scripts/
└── retry_dlq.py            # NEW: Manual DLQ retry script
```

**Structure Decision**: Single project structure maintained. Phase 2d extends existing `src/notion_integrator/` package with 3 new modules (writer.py, field_mapper.py, dlq_manager.py) and follows established testing patterns from Phase 2a/2b/2c.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: No violations - table intentionally left empty per constitution guidelines.

All design decisions use simplest solutions:
- File-based DLQ (no database)
- Immediate retry (no exponential backoff)
- Extend existing class (no new abstractions)
- Dynamic field mapping (no code generation)

## Phase 0: Research (Complete)

**Status**: ✅ Complete - See `research.md`

**Research Areas Completed**:
1. Notion API Write Operations Best Practices (185 lines)
2. Duplicate Detection Strategies (163 lines)
3. Dead Letter Queue (DLQ) Patterns (228 lines)
4. Field Mapping Best Practices (268 lines)
5. Retry Logic for Phase 2d (196 lines)

**Key Findings**:
- Use `POST /v1/pages` with schema-aware property formatting
- Pre-write query by email_id field (1 extra API call acceptable)
- File-based DLQ with Pydantic JSON serialization
- Dynamic FieldMapper using schema discovery from Phase 2a
- Simple 3-attempt retry with transient error classification

**Alternatives Evaluated**:
- Batch writes (rejected: not in spec, adds complexity)
- Database DLQ (rejected: overkill for Phase 2d volume)
- Exponential backoff (rejected: rate limiter already controls burst)
- Static field mapping (rejected: brittle to schema changes)

## Phase 1: Design & Contracts (Complete)

**Status**: ✅ Complete

### 1. Data Model (`data-model.md`) ✅

**Entities Defined**:
- **NotionCollabIQEntry**: Notion database record (11 Korean fields, 13 total properties)
- **WriteResult**: Write operation return value (success/duplicate/error states)
- **DLQEntry**: Dead letter queue record (email_id, extracted data, error context)
- **FieldMapping**: Internal Pydantic → Notion mapping representation

**Relationships**:
- WriteResult → NotionCollabIQEntry (created page)
- DLQEntry → ExtractedEntitiesWithClassification (failed data)
- FieldMapping → NotionCollabIQEntry (property types)

### 2. API Contracts (`contracts/`) ✅

**Contracts Created**:
- **notion_writer_contract.md**: NotionWriter interface (4 methods)
- **field_mapper_contract.md**: FieldMapper interface (6 formatters)
- **dlq_manager_contract.md**: DLQManager interface (4 methods)

**Key Contracts**:
- `NotionWriter.create_collabiq_entry(extracted_data, duplicate_behavior)` → WriteResult
- `FieldMapper.map_to_notion_properties(model)` → Dict[str, Any]
- `DLQManager.save_failed_write(email_id, data, error)` → Path

### 3. Quickstart Guide (`quickstart.md`) ✅

**Sections**:
1. Prerequisites (Phase 2a/2b/2c, Notion permissions)
2. Installation (no new dependencies)
3. Configuration (DUPLICATE_BEHAVIOR env var)
4. Basic Usage (write single email example)
5. Duplicate Handling (skip vs update)
6. Error Handling (DLQ explanation)
7. Retry Failed Writes (manual retry CLI)
8. Testing (integration tests + manual script)
9. Troubleshooting (6 common issues)
10. Production Deployment (pipeline integration)

## Phase 2: Implementation Tasks (Next Step)

**Status**: Pending - Run `/speckit.tasks` to generate `tasks.md`

**Expected Task Structure** (preview based on user stories):

### User Story 1 (P1): Write Extracted Email Data to Notion
- Setup: Create writer.py, field_mapper.py, dlq_manager.py stubs
- Tests: Write contract tests (red phase)
- Implementation: NotionWriter.create_collabiq_entry() (green phase)
- Integration: E2E test write workflow
- Verification: Manual test script

### User Story 2 (P2): Handle Duplicate Detection
- Tests: Write duplicate detection contract tests
- Implementation: NotionWriter.check_duplicate() query
- Integration: Test skip vs update behavior
- Configuration: Add DUPLICATE_BEHAVIOR env var

### User Story 3 (P3): Map Field Types Correctly
- Tests: Write field mapper contract tests
- Implementation: FieldMapper with 6 formatters
- Integration: Test all Notion property types
- Edge Cases: Korean text, null fields, relation validation

**Estimated Effort**: 2-3 days (per ROADMAP.md)

## Agent Context Update

**Status**: Pending - Run after Phase 1 complete

**Command**: `.specify/scripts/bash/update-agent-context.sh claude`

**Technologies to Add**:
- Notion API write operations (`POST /v1/pages`)
- File-based DLQ pattern
- Field mapping strategies

**Existing Technologies** (already in context from Phase 2a/2b/2c):
- notion-client SDK
- Pydantic v2
- Async/await patterns
- Phase 2c ExtractedEntitiesWithClassification model

## Dependencies

**Phase Dependencies**:
- ✅ Phase 2a: Notion Read Operations (schema discovery, NotionClient infrastructure)
- ✅ Phase 2b: Company Matching (matched company IDs for relations)
- ✅ Phase 2c: Classification & Summarization (data to write to Notion)

**External Dependencies**:
- ✅ `notion-client` (already installed)
- ✅ `pydantic` v2 (already installed)
- ✅ `tenacity` (already installed)
- ✅ Python 3.12+ (project standard)

**Environment Dependencies**:
- `NOTION_API_KEY` (already configured from Phase 2a)
- `NOTION_DATABASE_ID_COLLABIQ` (already configured from Phase 2a)
- `DUPLICATE_BEHAVIOR` (new, optional, default="skip")

## Success Criteria Mapping

| Success Criterion | Implementation Approach | Verification Method |
|-------------------|------------------------|---------------------|
| **SC-001**: ≥95% write success rate | 3-attempt retry + DLQ for permanent failures | Integration tests, monitoring |
| **SC-002**: 100% relation linking | Phase 2b company IDs + validation | Contract tests, E2E tests |
| **SC-003**: 100% correct "협력주체" format | FieldMapper with "{startup}-{partner}" template | Contract tests |
| **SC-004**: >99% duplicate prevention | Pre-write email_id query | Integration tests, duplicate test cases |
| **SC-005**: ≤2 seconds per write | Async/await + rate-limited API calls | Performance tests, timing assertions |
| **SC-006**: 100% DLQ capture | DLQManager.save_failed_write() + error context | Contract tests, manual retry verification |
| **SC-007**: 100% Korean text preservation | UTF-8 encoding + Notion rich_text format | Integration tests with Korean samples |

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Notion API rate limit exceeded | Medium | High | NotionClient already has rate limiting from Phase 2a |
| Duplicate detection false positives | Low | Medium | email_id is unique identifier from Gmail (Phase 1a) |
| Korean text encoding errors | Low | High | UTF-8 throughout stack + explicit testing |
| Relation ID validation failure | Medium | Medium | Graceful degradation (omit relation, log warning) |
| DLQ file conflicts | Low | Low | Timestamp in filename prevents collisions |
| Schema changes breaking mapping | Low | High | Dynamic schema discovery from Phase 2a |

## Performance Expectations

**Throughput**:
- Target: 1.5 emails/sec sustained (with duplicate check)
- API calls per email: 2 (1 query + 1 write)
- Rate limit: 3 req/sec (Notion API averaged)
- Bottleneck: Notion API (not CPU, not I/O)

**Latency Breakdown** (per email):
- Duplicate check query: ~300-500ms
- Field mapping: <10ms
- Write API call: ~500-800ms
- DLQ save (on error): ~5-10ms
- **Total**: ~1-1.5 seconds (within SC-005: ≤2 seconds)

**Resource Usage**:
- Memory: Minimal (Pydantic models ~1-5KB each)
- Disk: DLQ files ~10-50KB per failed write
- Network: Notion API (HTTPS)

## Testing Strategy

**Test Pyramid**:
1. **Contract Tests** (mandatory, TDD):
   - NotionWriter interface (4 methods)
   - FieldMapper interface (6 formatters)
   - DLQManager interface (4 methods)
   - Total: ~15-20 contract tests

2. **Integration Tests** (mandatory, TDD):
   - E2E write workflow (extract → classify → write)
   - Duplicate detection (skip vs update)
   - Error handling (transient vs permanent)
   - Korean text preservation
   - Total: ~8-12 integration tests

3. **Unit Tests** (optional, as needed):
   - Field mapping logic (type conversion)
   - DLQ serialization
   - Total: ~5-10 unit tests

**Test Data**:
- Reuse Phase 2c sample emails (sample-001.txt through sample-006.txt)
- Mock Notion API responses (success, duplicate, error)
- Korean text samples (브레이크앤컴퍼니, 신세계푸드, etc.)

**Manual Testing**:
- `tests/manual/test_phase2d_notion_write.py` (follows Phase 2c pattern)
- Demonstrates: basic write, duplicate detection, error handling, DLQ retry

## Rollout Plan

**Phase 2d (Current)**:
1. Implement write operations with basic retry (3 attempts)
2. File-based DLQ for failed writes
3. Manual retry script for DLQ processing
4. Target: 10-50 emails/day

**Phase 2e (Next)**:
1. Comprehensive retry logic with exponential backoff
2. Automated DLQ processing with scheduled retries
3. Enhanced rate limit handling
4. Target: 100-500 emails/day

**Production Readiness**:
- Phase 2d provides MVP write capability
- Phase 2e enhances reliability and scale
- Phase 3a adds async queue for high volume

## Documentation Updates Required

**After Phase 2d Implementation**:
1. Update `README.md` to mark Phase 2d complete
2. Update `ROADMAP.md` with Phase 2d completion status
3. Update `TECHSTACK.md` with write operation patterns
4. Update `docs/setup/quickstart.md` with Phase 2d testing instructions
5. Create `specs/009-notion-write/COMPLETION_REPORT.md` after feature complete

## Next Steps

**Immediate** (after plan approval):
1. Run `.specify/scripts/bash/update-agent-context.sh claude` to update AI context
2. Run `/speckit.tasks` to generate dependency-ordered task breakdown
3. Review `tasks.md` for task completeness and ordering
4. Begin implementation via `/speckit.implement`

**During Implementation**:
1. Follow TDD discipline (tests first, implementation second)
2. Verify each user story independently before proceeding
3. Update documentation as features complete
4. Monitor test pass rate and success criteria achievement

**After Implementation**:
1. Run full test suite (`uv run pytest`)
2. Execute manual test script (`tests/manual/test_phase2d_notion_write.py`)
3. Create completion report
4. Update project documentation
5. Merge to main after all acceptance criteria pass

---

**Plan Status**: ✅ Complete - Ready for Phase 2 (/speckit.tasks)
**Next Command**: `/speckit.tasks`
**Estimated Timeline**: 2-3 days (per ROADMAP.md complexity assessment)
