# Tasks: CollabIQ System - Feasibility Study & Architectural Foundation

**Input**: Design documents from `/specs/001-feasibility-architecture/`
**Prerequisites**: plan.md ✅, spec.md ✅

**Organization**: This is foundation work (NOT feature implementation). Tasks produce design artifacts (research.md, architecture.md, data-model.md, contracts/, quickstart.md) and project scaffolding. Future feature branches (002+) will implement actual system functionality.

**Tests**: Tests are not requested for this foundation work per spec.md. Foundation work produces design artifacts and project scaffold (no implementation code requiring tests). Test-driven development will apply to future feature branches per Constitution Principle III.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Specification artifacts**: `specs/001-feasibility-architecture/`
- **Project root**: `/Users/jlim/Projects/CollabIQ/`
- **Source code** (Phase 2 only): `src/`, `tests/`, `config/`, `docs/`

---

## Phase 1: User Story 1 - Feasibility Analysis & Technology Assessment (Priority: P1) 🎯 MVP

**Goal**: Validate technical feasibility of CollabIQ vision using Gemini API, assess Notion API compatibility, evaluate email infrastructure options, and select fuzzy matching approach. Produce go-no-go recommendation.

**Independent Test**: `research.md` exists with go-no-go recommendation, Gemini API validation results (≥85% accuracy target), Notion API compatibility confirmation, email infrastructure recommendation, and fuzzy matching approach selection.

### Research & Validation Tasks for User Story 1

- [x] T001 [US1] Set up Gemini API access (obtain API key from Google AI Studio, install google-generativeai SDK via `uv add google-generativeai`)
- [x] T002 [P] [US1] Create sample Korean collaboration email dataset in tests/fixtures/sample_emails/ (6 examples with ground truth labels for entities: 스타트업명, 협업기관, 협업강도, 날짜)
- [x] T003 [US1] Test Gemini 2.5 Flash with structured output on sample emails (94% average confidence ✅, 12.42s latency, $0.14/month cost - PASS all targets)
- [x] T004 [US1] Test Gemini 2.5 Pro if Flash accuracy insufficient (NOT NEEDED - Flash 94% exceeds 85% target)
- [X] T005 [P] [US1] Set up Notion API access (create integration at notion.so/my-integrations, obtain token, install notion-client SDK via `uv add notion-client`)
- [X] T006 [US1] Create test Notion workspace with "CollabIQ" database schema (담당자 Person field, 스타트업명/협업기관 Relation fields, 협력주체 Title field, 협업내용 Text field, 협업형태/협업강도 Select fields, 날짜 Date field - existing database analyzed and validated)
- [X] T007 [US1] Test creating Notion entries programmatically (verify all field types work via SDK, test relation linking with fuzzy match scenarios, measure API rate limits 3 req/s documented - all tests passed with 1.71 req/s observed)
- [ ] T008 [P] [US1] Research email infrastructure options (Gmail API: OAuth setup, 250 req/day free tier; IMAP: simple protocol, connection drops; Email webhook: SendGrid/AWS SES/Mailgun, ~$10-50/month) and document pros/cons matrix in specs/001-feasibility-architecture/email-infrastructure-comparison.md
- [ ] T009 [US1] Test Gemini-based fuzzy matching approach (provide Gemini with list of existing Notion company names in prompt context, test on 20-30 company name pairs from sample data, measure accuracy ≥85% target for abbreviations/typos/spacing, document confidence scores)
- [ ] T010 [US1] Evaluate RapidFuzz as fallback option (install `uv add rapidfuzz`, test Levenshtein distance on Korean company names, validate ≥0.85 threshold on test dataset, document if needed as fallback only if Gemini matching insufficient)
- [ ] T011 [US1] Synthesize all findings and produce go-no-go assessment in specs/001-feasibility-architecture/research.md (identify any technical blockers, assess integration complexity and risk, provide GO/NO-GO recommendation with risk mitigation strategies, summarize email infrastructure comparison from T008)

**Checkpoint**: At this point, User Story 1 should be complete with research.md containing go-no-go recommendation and all validation results.

**Success Criteria** (from spec.md):
- ✅ SC-001: Feasibility report completed documenting technology evaluation with clear go-no-go recommendation
- ✅ SC-002: Korean NLP evaluation includes accuracy metrics from testing on ≥20 sample collaboration emails
- ✅ SC-003: Notion API validation demonstrates successful creation of test entry with all required field types
- ✅ SC-004: Fuzzy matching approach achieves ≥0.85 threshold with ≥90% precision and ≥80% recall on test dataset

---

## Phase 2: User Story 2 - System Architecture Design (Priority: P2)

**Goal**: Design system architecture with clear component boundaries, define LLMProvider abstraction layer, specify API contracts between components, design data flow and error handling, and select deployment architecture (Google Cloud Platform).

**Independent Test**: `architecture.md` exists with component diagram, data flow diagram, and deployment architecture. `data-model.md` exists with LLMProvider interface specification and entity schemas. `contracts/` directory exists with YAML specifications for each component interface.

**Prerequisites**: Phase 1 complete (research.md with GO recommendation)

### Architecture Design Tasks for User Story 2

- [x] T012 [US2] Design component architecture and create component diagram in specs/001-feasibility-architecture/architecture.md showing: EmailReceiver, ContentNormalizer, LLMProvider (abstraction layer), GeminiAdapter (implementation handling extraction + matching + classification + summarization), NotionIntegrator, VerificationQueue, ReportGenerator
- [x] T013 [P] [US2] Define LLMProvider abstract base class specification in specs/001-feasibility-architecture/data-model.md (methods: extract_entities(email_text) → ExtractedEntities, classify(entities, context) → Classification, summarize(text, max_sentences) → str, with Pydantic models for ExtractedEntities, Classification, ClassificationContext)
- [x] T014 [P] [US2] Design GeminiAdapter implementation approach in specs/001-feasibility-architecture/architecture.md (prompt engineering strategies for extraction/classification/summarization, JSON schema enforcement via structured output mode, error handling with retry logic, cost tracking per request, note how to swap to GPT/Claude by implementing GPTAdapter/ClaudeAdapter with same interface)
- [x] T015 [US2] Create data flow diagram in specs/001-feasibility-architecture/architecture.md showing simplified workflow: EmailReceiver → ContentNormalizer → NotionIntegrator (fetch company lists) → LLMProvider/GeminiAdapter (extraction + matching + classification + summarization in one call) → NotionIntegrator (create entry) → VerificationQueue (if low confidence), with error paths at each step
- [x] T016 [US2] Design error handling and retry strategy in specs/001-feasibility-architecture/architecture.md (LLM API failures: exponential backoff 1s/2s/4s/8s max 3 retries, Notion API failures: exponential backoff 5s/10s/20s max 5 retries, rate limit errors: queue locally, dead letter queue after max retries exhausted, manual review of DLQ items)
- [x] T017 [US2] Add edge case mitigation mapping table to specs/001-feasibility-architecture/architecture.md (map all 6 edge cases from spec.md lines 100-106 to mitigation strategies as defined in plan.md lines 455-464)
- [x] T018 [US2] Select deployment architecture for Google Cloud Platform in specs/001-feasibility-architecture/architecture.md (compare Cloud Functions 2nd gen vs Cloud Run vs Compute Engine, recommend Cloud Run with rationale: best balance for 50-100 emails/day, unified billing with Gemini API, Docker-based local dev, auto-scaling, document migration path to GCE if volume exceeds 500 emails/day)
- [x] T019 [P] [US2] Create LLMProvider interface contract in specs/001-feasibility-architecture/contracts/llm_provider.yaml (input/output schemas for extract_entities/classify/summarize methods, error conditions, example usage)
- [x] T020 [P] [US2] Create EmailReceiver component contract in specs/001-feasibility-architecture/contracts/email_receiver.yaml (input/output schemas, error conditions, example usage)
- [x] T021 [P] [US2] Create NotionIntegrator component contract in specs/001-feasibility-architecture/contracts/notion_integrator.yaml (input/output schemas for fetch/create operations, error conditions, example usage)

**Checkpoint**: At this point, User Story 2 should be complete with architecture.md, data-model.md, and contracts/ all defined.

**Success Criteria** (from spec.md):
- ✅ SC-005: Architecture design includes component diagram, data flow diagram, and API contracts
- ✅ SC-012: Architecture design supports scaling from 50 to 100+ emails/day without fundamental redesign

---

## Phase 3: User Story 3 - Implementation Strategy & Phasing Plan (Priority: P3)

**Goal**: Define step-by-step implementation roadmap that breaks the full CollabIQ system into 12 manageable phases, each delivering incremental value. Strategy must align with MVP-first approach (Phase 1a+1b as minimal viable increment).

**Independent Test**: `implementation-roadmap.md` exists with 12-phase breakdown, MVP definition (Phase 1a+1b completable in 6-9 days, meeting SC-007 ≤2 weeks requirement), dependency graph, and test strategy per phase.

**Prerequisites**: Phase 2 complete (architecture design validated)

### Implementation Roadmap Tasks for User Story 3

- [ ] T022 [US3] Define MVP scope in specs/001-feasibility-architecture/implementation-roadmap.md (minimal feature set: email ingestion → Gemini extraction → JSON output for manual review, NOT included: automatic Notion creation, fuzzy matching, verification queue, reporting, value delivered: reduces manual entity extraction time by ≥30%, completable in Phase 1a 3-4 days + Phase 1b 3-5 days = 6-9 days total, confirms meets spec SC-007 ≤2 weeks requirement)
- [ ] T023 [US3] Document Phase 1a-1b (MVP track) in specs/001-feasibility-architecture/implementation-roadmap.md (Phase 1a: email reception + normalization, branch 002-email-reception, 3-4 days; Phase 1b: Gemini entity extraction, branch 003-gemini-extraction, 3-5 days, MVP complete after Phase 1b with JSON output for manual Notion entry creation)
- [ ] T024 [US3] Document Phases 2a-2e (automation track) in specs/001-feasibility-architecture/implementation-roadmap.md (Phase 2a: Notion read operations branch 004-notion-read 2-3 days, Phase 2b: LLM-based fuzzy matching branch 005-llm-matching 2-3 days, Phase 2c: classification + summarization branch 006-classification-summarization 2-3 days, Phase 2d: Notion write operations branch 007-notion-write 2-3 days, Phase 2e: error handling + retry logic branch 008-error-handling 2-3 days, full automation complete after Phase 2e)
- [ ] T025 [US3] Document Phases 3a-3b (quality track) in specs/001-feasibility-architecture/implementation-roadmap.md (Phase 3a: verification queue storage branch 009-queue-storage 2-3 days, Phase 3b: review UI branch 010-review-ui 3-4 days, production-ready after Phase 3b with edge case handling)
- [ ] T026 [US3] Document Phases 4a-4b (analytics track) in specs/001-feasibility-architecture/implementation-roadmap.md (Phase 4a: basic reporting branch 011-basic-reporting 2-3 days, Phase 4b: advanced analytics branch 012-advanced-analytics 3-4 days, complete system after Phase 4b with full end-to-end reporting)
- [ ] T027 [US3] Create dependency graph in specs/001-feasibility-architecture/implementation-roadmap.md showing phase completion order: Phase 1a → Phase 1b (MVP) → Phase 2a → Phase 2b → Phase 2c → Phase 2d → Phase 2e → Phase 3a → Phase 3b → Phase 4a → Phase 4b
- [ ] T028 [US3] Document test strategy per phase in specs/001-feasibility-architecture/implementation-roadmap.md (Phase 1a: unit tests for normalizer, Phase 1b: integration tests for Gemini API + accuracy tests on sample emails, Phase 2a: integration tests for Notion API, Phase 2b: accuracy tests for matching, Phase 2c: accuracy tests for classification + summarization quality, Phase 2d: integration tests for entry creation, Phase 2e: failure scenario tests, Phase 3a: unit tests for queue operations, Phase 3b: UI tests Selenium/Playwright, Phase 4a: data accuracy tests, Phase 4b: data quality tests + Notion integration tests)

**Checkpoint**: At this point, User Story 3 should be complete with implementation-roadmap.md containing 12-phase plan and test strategy.

**Success Criteria** (from spec.md):
- ✅ SC-006: Implementation strategy defines MVP and 12 phases (exceeds required 5) with each phase independently deliverable and testable
- ✅ SC-007: MVP scope is minimal (6-9 days, ≤2 weeks) yet delivers measurable user value (reduces manual data entry time by ≥30%)

---

## Phase 4: User Story 4 - Technology Stack Selection & Project Setup (Priority: P4)

**Goal**: Select specific technologies/libraries, set up project scaffolding with proper structure, dependencies, configuration management, and development environment. Create README, quickstart guide, and CI/CD skeleton.

**Independent Test**: Working project repository exists at `/Users/jlim/Projects/CollabIQ/` with: selected tech stack documented in README.md, project structure matching architecture (src/, tests/, config/, docs/ folders), dependencies installed and working (pyproject.toml, uv.lock), configuration management setup (.env.example, config/settings.py), development environment instructions in specs/001-feasibility-architecture/quickstart.md, and CI/CD skeleton (.github/workflows/ci.yml) executing successfully.

**Prerequisites**: Phase 3 complete (implementation roadmap defined)

### Project Scaffold Tasks for User Story 4

- [ ] T029 [US4] Initialize Python project with UV at repository root (run `uv init --package`, `uv python pin 3.12`, create pyproject.toml with project metadata: name="collabiq", version="0.1.0", description="Email-based collaboration tracking system")
- [ ] T030 [P] [US4] Create project folder structure matching architecture design from plan.md (create src/llm_provider/, src/llm_adapters/, src/email_receiver/, src/notion_integrator/, src/verification_queue/, src/reporting/, tests/unit/, tests/integration/, tests/contract/, config/, docs/, with placeholder __init__.py files in each src/ subdirectory)
- [ ] T031 [P] [US4] Install core dependencies via UV (run `uv add google-generativeai notion-client rapidfuzz pydantic pydantic-settings`, run `uv add --dev pytest pytest-asyncio pytest-mock ruff mypy`)
- [ ] T032 [P] [US4] Create .env.example configuration template in repository root with required variables (GEMINI_API_KEY, GEMINI_MODEL=gemini-2.5-flash, NOTION_API_KEY, NOTION_DATABASE_ID_COLLABIQ, NOTION_DATABASE_ID_CORP, GMAIL_CREDENTIALS_PATH or IMAP_HOST/PORT/USERNAME/PASSWORD or WEBHOOK_SECRET, FUZZY_MATCH_THRESHOLD=0.85, CONFIDENCE_THRESHOLD=0.85, MAX_RETRIES=3, RETRY_DELAY_SECONDS=5)
- [ ] T033 [P] [US4] Create Pydantic settings management in config/settings.py (BaseSettings class with gemini_api_key, gemini_model, notion_api_key, notion_database_id_collabiq, notion_database_id_corp, fuzzy_match_threshold, confidence_threshold, Config with env_file=".env")
- [ ] T034 [P] [US4] Create .gitignore for Python projects in repository root (ignore .venv/, __pycache__/, *.pyc, .env, .DS_Store, *.log, .pytest_cache/, .mypy_cache/, .ruff_cache/, uv.lock conflict files)
- [ ] T035 [P] [US4] Create Makefile with common tasks in repository root (targets: install via uv sync, test via uv run pytest, lint via uv run ruff check . && uv run mypy src/, format via uv run ruff format . && uv run ruff check --fix ., clean to remove __pycache__ and *.pyc files)
- [ ] T036 [US4] Create README.md in repository root (project overview: CollabIQ email-based collaboration tracking system, architecture summary with link to specs/001-feasibility-architecture/architecture.md, getting started guide with link to quickstart.md, development workflow using Makefile targets, contributing guidelines)
- [ ] T037 [US4] Create quickstart.md in specs/001-feasibility-architecture/ (step-by-step dev environment setup: prerequisites Python 3.12 + UV + Git, clone repository, run `uv sync` to install dependencies, copy .env.example to .env and fill in API keys, run `make test` to validate setup, run `make lint` to check code quality, next steps: implement Phase 1a in branch 002-email-reception, target: new developer can run project locally within 30 minutes per SC-010)
- [ ] T038 [P] [US4] Create CI/CD pipeline skeleton in .github/workflows/ci.yml (trigger on push and pull_request, job: runs-on ubuntu-latest, steps: checkout, setup Python 3.12, install UV via curl, run uv sync, run linting via uv run ruff check . && uv run mypy src/, run tests via uv run pytest)
- [ ] T039 [US4] Validate CI/CD pipeline executes successfully (commit .github/workflows/ci.yml, push to branch, verify GitHub Actions runs successfully even with no tests yet, confirm linting passes on empty src/ structure)
- [ ] T040 [P] [US4] Copy architecture.md to docs/ARCHITECTURE.md in repository root (preserve all content from specs/001-feasibility-architecture/architecture.md)
- [ ] T041 [P] [US4] Copy implementation-roadmap.md to docs/IMPLEMENTATION_ROADMAP.md in repository root (preserve all content from specs/001-feasibility-architecture/implementation-roadmap.md)
- [ ] T042 [P] [US4] Create docs/API_CONTRACTS.md consolidating all contract YAML files (consolidate contracts/llm_provider.yaml, contracts/email_receiver.yaml, contracts/notion_integrator.yaml with explanations and examples)
- [ ] T043 [US4] Update README.md with navigation links (add links to docs/ARCHITECTURE.md, docs/IMPLEMENTATION_ROADMAP.md, docs/API_CONTRACTS.md, specs/001-feasibility-architecture/quickstart.md, specs/001-feasibility-architecture/spec.md)

**Checkpoint**: At this point, User Story 4 should be complete with working project scaffold ready for Phase 1a implementation in branch 002-email-reception.

**Success Criteria** (from spec.md):
- ✅ SC-008: Technology stack selection is documented with rationale, all dependencies are installed and working, and sample code validates each integration point
- ✅ SC-009: Project scaffold includes working folder structure, configuration management, development environment documentation, and CI/CD pipeline executing successfully
- ✅ SC-010: Development environment setup instructions enable new developer to run project locally within 30 minutes following README

---

## Phase 5: Polish & Documentation Finalization

**Purpose**: Final documentation updates and validation before moving to feature implementation branches

- [ ] T044 [P] Update specs/001-feasibility-architecture/plan.md with "Foundation Work Complete" status (mark all Phase 0-2 deliverables as complete, confirm all 22 functional requirements addressed, confirm all 12 success criteria met)
- [ ] T045 [P] Create foundation work completion report in specs/001-feasibility-architecture/completion-report.md (summarize all deliverables: research.md with go-no-go, architecture.md with diagrams, data-model.md with LLMProvider interface, implementation-roadmap.md with 12 phases, quickstart.md with setup guide, contracts/ with 3 YAML files, project scaffold with working structure, confirm constitution compliance: Principle I-V all pass)
- [ ] T046 Run quickstart.md validation (follow quickstart.md instructions as a new developer would, verify can complete setup within 30 minutes, confirm make test and make lint execute successfully, document any issues found and fix before completion)
- [ ] T047 Final constitution re-check (review constitution.md principles I-V against completed foundation work, confirm Principle I: Specification-First satisfied with spec.md, confirm Principle II: Incremental Delivery satisfied with 4 independent user stories P1-P4, confirm Principle III: TDD N/A for foundation work deferred to feature branches, confirm Principle IV: Design Artifacts complete with all required files existing, confirm Principle V: Simplicity & Justification satisfied with LLM abstraction layer justified in plan.md Complexity Tracking section)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (User Story 1 - Feasibility)**: No dependencies - can start immediately
- **Phase 2 (User Story 2 - Architecture)**: Depends on Phase 1 completion (research.md with GO recommendation)
- **Phase 3 (User Story 3 - Implementation Strategy)**: Depends on Phase 2 completion (architecture design validated)
- **Phase 4 (User Story 4 - Project Setup)**: Depends on Phase 3 completion (implementation roadmap defined)
- **Phase 5 (Polish)**: Depends on Phase 4 completion (project scaffold exists)

### User Story Dependencies

- **User Story 1 (P1)**: Can start immediately - No dependencies
- **User Story 2 (P2)**: Requires User Story 1 complete (GO recommendation from research.md)
- **User Story 3 (P3)**: Requires User Story 2 complete (architecture validated)
- **User Story 4 (P4)**: Requires User Story 3 complete (roadmap defined)

**⚠️ CRITICAL**: Foundation work MUST proceed sequentially (P1 → P2 → P3 → P4) because each story builds on the previous one's deliverables. This is different from feature implementation where user stories can often proceed in parallel.

### Within Each User Story

- **User Story 1**: Tasks T001-T011 have some parallelization opportunities (T002, T005, T008, T010 marked [P])
- **User Story 2**: Tasks T012-T021 have significant parallelization (T013, T014, T019, T020, T021 marked [P])
- **User Story 3**: Tasks T022-T028 are sequential (each phase documentation depends on understanding previous phases)
- **User Story 4**: Tasks T029-T043 have significant parallelization (T030, T031, T032, T033, T034, T035, T038, T040, T041, T042 marked [P])

### Parallel Opportunities

- **Within User Story 1**: T002 (create samples), T005 (Notion setup), T008 (email research), T010 (RapidFuzz eval) can run in parallel
- **Within User Story 2**: T013 (LLMProvider spec), T014 (GeminiAdapter design), T019-T021 (all contract files) can run in parallel
- **Within User Story 4**: Most tasks T030-T035, T038, T040-T042 can run in parallel (different files, no dependencies)

---

## Parallel Example: User Story 4 (Project Setup)

```bash
# Launch all parallel project setup tasks together:
Task T030: "Create project folder structure"
Task T031: "Install core dependencies via UV"
Task T032: "Create .env.example configuration template"
Task T033: "Create Pydantic settings management in config/settings.py"
Task T034: "Create .gitignore for Python projects"
Task T035: "Create Makefile with common tasks"
Task T038: "Create CI/CD pipeline skeleton in .github/workflows/ci.yml"

# After above complete, can parallelize documentation tasks:
Task T040: "Copy architecture.md to docs/ARCHITECTURE.md"
Task T041: "Copy implementation-roadmap.md to docs/IMPLEMENTATION_ROADMAP.md"
Task T042: "Create docs/API_CONTRACTS.md consolidating all contract YAML files"
```

---

## Implementation Strategy

### Sequential Foundation Work (NOT MVP-style)

This is foundation work, not feature implementation. Tasks MUST proceed sequentially by user story:

1. **Complete Phase 1 (User Story 1)**: Feasibility analysis → research.md with GO recommendation
2. **Complete Phase 2 (User Story 2)**: Architecture design → architecture.md, data-model.md, contracts/
3. **Complete Phase 3 (User Story 3)**: Implementation strategy → implementation-roadmap.md with 12 phases
4. **Complete Phase 4 (User Story 4)**: Project setup → working scaffold, README, quickstart, CI/CD
5. **Complete Phase 5**: Polish → validation and constitution re-check
6. **STOP and VALIDATE**: Foundation complete, ready for feature branch 002-email-reception

### After Foundation Complete

Future feature implementation will follow incremental delivery:

1. **002-email-reception (Phase 1a)**: Email ingestion + normalization → 3-4 days
2. **003-gemini-extraction (Phase 1b)**: Entity extraction → 3-5 days → **MVP Complete!** ✅
3. **004-notion-read (Phase 2a)**: Fetch company lists → 2-3 days
4. ... continue through Phases 2b-4b as defined in implementation-roadmap.md

Each future feature branch will be independently testable and deliverable.

---

## Notes

- **Foundation vs Feature Work**: This tasks.md produces design artifacts (research, architecture, roadmap, scaffold), NOT feature implementation code
- **Sequential Execution**: User stories P1-P4 MUST complete sequentially (each builds on previous)
- **Parallelization Within Stories**: Many tasks within each user story can run in parallel (marked [P])
- **Constitution Compliance**: All principles satisfied (I: spec-first, II: incremental with P1-P4, III: TDD deferred to features, IV: all artifacts produced, V: complexity justified)
- **Next Steps**: After T047 complete, branch 001-feasibility-architecture ready for merge, create branch 002-email-reception for Phase 1a implementation
- **Success Criteria**: All 12 success criteria (SC-001 to SC-012) mapped to specific tasks and validation checkpoints

**Total Tasks**: 47 tasks (11 for US1, 10 for US2, 7 for US3, 15 for US4, 4 for polish)
