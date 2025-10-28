# Implementation Plan: CollabIQ System - Feasibility Study & Architectural Foundation

**Branch**: `001-feasibility-architecture` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-feasibility-architecture/spec.md`

**Note**: This is FOUNDATION WORK ONLY - no feature implementation code will be written. Focus is on feasibility analysis, architecture design, implementation strategy, and project scaffolding to prepare for subsequent feature development in branches 002-xxx, 003-xxx, etc.

## Summary

This branch delivers the foundational analysis and setup for the CollabIQ system - an email-based collaboration tracking platform that will extract entities from Korean/English emails, create Notion database entries, classify collaborations, and generate reports. This foundation work validates technical feasibility (focusing on Gemini API for Korean NLP), designs system architecture with LLM abstraction layer for flexibility, defines a 5-phase implementation roadmap, and sets up project scaffolding with proper structure and documentation.

**Key Deliverables**:
1. Feasibility report validating Gemini API for Korean entity extraction (≥85% accuracy target)
2. Architecture design with LLMProvider abstraction layer enabling future LLM swapping
3. Implementation phasing plan (MVP → Phase 1-5) for subsequent feature branches
4. Project scaffold with folder structure, dependencies, configuration, and CI/CD skeleton
5. Comprehensive documentation (README.md, ARCHITECTURE.md, quickstart.md)

**NOT included**: No feature implementation code. Actual email processing, entity extraction, Notion integration, verification queue, and reporting will be implemented in future branches following the roadmap defined here.

## Technical Context

**Language/Version**: Python 3.12
- Rationale: Excellent ecosystem for LLM integration (Google Generative AI SDK), Notion SDK, NLP libraries, and async operations
- Alternative considered: Go (performance) - rejected due to weaker LLM/NLP library ecosystem

**Primary Dependencies**:
- **google-generativeai** (Gemini API SDK) - Korean/English entity extraction, classification, summarization, **AND fuzzy matching** (all-in-one)
- **notion-client** (official Notion SDK) - Database integration for "레이더 활동" entries
- **rapidfuzz** (optional fallback) - Only if Gemini-based matching fails to achieve ≥85% accuracy
- **pydantic** - Data validation and settings management
- **fastapi** (future) - Email webhook receiver or REST API
- **pytest** - Testing framework

**Storage**:
- Notion databases (레이더 활동, 스타트업, 계열사) - primary data store
- Local queue storage (pending) - For verification queue and retry logic (implementation decision in Phase 4)

**Testing**:
- **pytest** - Unit, integration, and contract testing
- **pytest-asyncio** - Async test support
- **pytest-mock** - Mocking LLM API calls for testing

**Target Platform**:
- Development: macOS (Apple Silicon ARM64) per CLAUDE.md
- Deployment: **Google Cloud Platform** (preferred for unified billing with Gemini API; decision between Cloud Run, Cloud Functions, or GCE pending architecture research)

**Project Type**: Single service (microservice architecture)
- Backend service handling email → extraction → Notion pipeline
- No frontend UI initially (verification queue UI in Phase 4)
- Focus on API-driven architecture with clean component boundaries

**Performance Goals**:
- Process 50 emails/day initially (baseline)
- Scale to 100+ emails/day without architecture changes
- Email-to-Notion latency: ≤5 minutes end-to-end (SC-001 from spec)
- LLM API response time: 1-3 seconds per email expected

**Constraints**:
- Gemini API cost budget: ~$15-50/month (50 emails/day with Flash/Pro models)
- Google Cloud deployment cost: ~$10-30/month (Cloud Run with auto-scaling)
- Combined GCP billing: Gemini API + Cloud Run + any storage on single invoice
- Notion API rate limits: 3 requests/second - must design queuing strategy
- Korean language requirement: Entity extraction must work equally well on Korean and English text
- Privacy policy: Store internal team member names/emails (담당자 field), external business identifiers (company names, collaboration details) only; no external personal data

**Scale/Scope**:
- Initial: 50 emails/day from investment team members
- Growth: 100+ emails/day within 6 months
- Users: ~5-10 investment team members sending collaboration updates
- Notion workspace: Existing databases (스타트업, 계열사, 레이더 활동) with stable schemas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS
- ✅ Feature specification (`spec.md`) exists and is approved
- ✅ User scenarios with acceptance criteria defined (4 user stories, 28 acceptance scenarios)
- ✅ Functional requirements documented (FR-001 through FR-022)
- ✅ Success criteria defined (SC-001 through SC-012)
- ✅ Requirements are technology-agnostic (focused on outcomes, not implementation)

### Principle II: Incremental Delivery via Independent User Stories ✅ PASS
- ✅ User stories prioritized (P1: Feasibility, P2: Architecture, P3: Phasing, P4: Setup)
- ✅ Each story independently testable:
  - P1 delivers feasibility report (go-no-go decision)
  - P2 delivers architecture diagrams (blueprint for implementation)
  - P3 delivers implementation roadmap (phasing plan)
  - P4 delivers working project scaffold (ready for Phase 1 implementation)
- ✅ P1 constitutes viable MVP (feasibility study alone provides decision-making value)
- ✅ Implementation proceeds in priority order (P1 → P2 → P3 → P4 sequential)

### Principle III: Test-Driven Development (TDD) ⚠️ N/A - Foundation Work
- ⚠️ TDD not applicable to foundation work (no feature implementation code)
- ✅ Test strategy will be defined in User Story 3 (implementation phasing plan)
- ✅ Future feature branches (002-xxx, 003-xxx) WILL follow TDD when tests are required

**Note**: Foundation work produces documentation artifacts (reports, diagrams, plans), not testable code. TDD will apply to subsequent feature implementation branches.

### Principle IV: Design Artifact Completeness ✅ PASS
- ✅ Planning phase (`/speckit.plan`) will produce:
  - `plan.md` (this file) - technical context, constitution check, project structure
  - `research.md` - Gemini API validation, Notion API testing, email infrastructure analysis, fuzzy matching evaluation
  - `data-model.md` - LLMProvider interface, entity schemas, component contracts
  - `quickstart.md` - Development environment setup guide
  - `contracts/` - LLMProvider interface spec, component API contracts
- ✅ Task generation (`/speckit.tasks`) will occur after planning artifacts complete
- ✅ Implementation (`/speckit.implement`) deferred to future branches

### Principle V: Simplicity & Justification ✅ PASS with Documented Complexity
- ✅ Abstraction layer (LLMProvider) complexity is justified:
  - **Why needed**: Enable future LLM provider swapping (Gemini → GPT/Claude) without rewriting entire system
  - **Why not simpler**: Direct Gemini integration would require full rewrite if accuracy insufficient or costs escalate
  - **Value**: 30 minutes to swap providers vs days/weeks to rewrite
- ✅ No other complexity introduced - foundation work remains focused on essential architecture decisions

**GATE RESULT**: ✅ **PASS** - All constitution principles satisfied for foundation work scope

## Project Structure

### Documentation (this feature)

```text
specs/001-feasibility-architecture/
├── spec.md                    # ✅ Complete (feature specification)
├── plan.md                    # 🔄 This file (implementation plan)
├── research.md                # 📝 Phase 0 output (feasibility findings)
├── data-model.md              # 📝 Phase 1 output (LLMProvider interface, entities)
├── architecture.md            # 📝 Phase 1 output (system architecture diagrams)
├── implementation-roadmap.md  # 📝 Phase 1 output (5-phase plan for future branches)
├── quickstart.md              # 📝 Phase 1 output (dev environment setup)
├── contracts/                 # 📝 Phase 1 output (API contracts)
│   ├── llm_provider.yaml      # LLMProvider interface specification
│   ├── email_receiver.yaml    # EmailReceiver component contract
│   └── notion_integrator.yaml # NotionIntegrator component contract
└── checklists/
    └── requirements.md        # ✅ Complete (quality validation checklist)
```

### Source Code (repository root)

**Note**: This foundation work will create PROJECT STRUCTURE ONLY (folders, README, .gitignore, config files) - NO implementation code yet. Structure designed to match architecture decisions from Phase 1.

```text
CollabIQ/
├── .github/
│   └── workflows/
│       └── ci.yml                  # 📝 CI/CD pipeline (linting, type checking, tests)
│
├── .specify/                        # ✅ Exists (SpecKit framework files)
│   ├── memory/
│   │   └── constitution.md         # ✅ Exists (project governance)
│   ├── templates/                  # ✅ Exists (spec/plan/task templates)
│   └── scripts/                    # ✅ Exists (automation scripts)
│
├── specs/                           # ✅ Exists
│   └── 001-feasibility-architecture/ # ✅ Current feature
│
├── src/                             # 📝 To be created (Phase 1)
│   ├── llm_provider/                # LLM abstraction layer (handles extraction + matching)
│   │   ├── __init__.py              # Exports LLMProvider base class
│   │   ├── base.py                  # LLMProvider abstract base class (ABC)
│   │   └── types.py                 # Entity, Classification, MatchedCompany types
│   │
│   ├── llm_adapters/                # LLM provider implementations
│   │   ├── __init__.py              # Exports GeminiAdapter
│   │   └── gemini.py                # GeminiAdapter (extraction + fuzzy matching in one prompt)
│   │
│   ├── email_receiver/              # Email ingestion component (Phase 1 implementation)
│   │   └── __init__.py              # Placeholder
│   │
│   ├── notion_integrator/           # Notion API integration (Phase 2 implementation)
│   │   └── __init__.py              # Fetches company lists, creates entries
│   │
│   ├── verification_queue/          # Manual review queue (Phase 3 implementation)
│   │   └── __init__.py              # Placeholder
│   │
│   └── reporting/                   # Analytics and summary reports (Phase 4 implementation)
│       └── __init__.py              # Placeholder
│
├── tests/                           # 📝 To be created (Phase 1)
│   ├── unit/                        # Unit tests (mock LLM/Notion APIs)
│   ├── integration/                 # Integration tests (real API calls with test data)
│   └── contract/                    # Contract tests (verify component interfaces)
│
├── config/                          # 📝 To be created (Phase 1)
│   ├── settings.py                  # Pydantic settings management
│   └── logging.py                   # Logging configuration
│
├── docs/                            # 📝 To be created (Phase 1)
│   ├── ARCHITECTURE.md              # System architecture diagrams and explanations
│   ├── IMPLEMENTATION_ROADMAP.md    # 5-phase implementation plan
│   └── API_CONTRACTS.md             # Component interface specifications
│
├── .env.example                     # 📝 To be created (Phase 1)
├── .gitignore                       # 📝 To be created (Phase 1)
├── .python-version                  # 📝 To be created (3.12)
├── pyproject.toml                   # 📝 To be created (UV package config)
├── uv.lock                          # 📝 To be created (dependency lockfile)
├── README.md                        # 📝 To be created (Phase 1)
└── Makefile                         # 📝 To be created (common tasks: test, lint, run)
```

**Structure Decision**: Single-project Python service architecture chosen for CollabIQ. This structure supports:
1. **Clear component separation**: Each component (email_receiver, llm_provider, notion_integrator, etc.) has its own directory following single-responsibility principle
2. **LLM abstraction layer**: `llm_provider/` defines interface, `llm_adapters/` contains implementations (Gemini first, GPT/Claude later)
3. **Testability**: Separate `tests/` hierarchy matching `src/` structure enables comprehensive testing at unit, integration, and contract levels
4. **Scalability**: Structure allows future extraction of components into separate services if needed (e.g., verification queue UI as separate frontend service)

**Rationale for single project vs alternatives**:
- **Not web app structure** (frontend/backend split): No UI initially; verification queue UI (Phase 4) can be added as `frontend/` directory when needed
- **Not mobile + API**: This is a backend service processing emails, not a mobile app
- **Single project fits** because all components are tightly coupled in the email → extraction → Notion pipeline; microservices split would add unnecessary network latency and complexity

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| LLM abstraction layer adds interface complexity | Enable swapping Gemini → GPT/Claude/multi-LLM without rewriting system; future-proof against API changes, cost increases, or accuracy improvements from new models | Direct Gemini integration rejected: Would require rewriting entire extraction pipeline if Gemini fails accuracy target or costs escalate. Abstraction layer = 30 min provider swap vs weeks of rewrite. Cost: One extra module (`llm_provider/base.py` ~100 lines). Benefit: Operational flexibility worth maintenance cost. |

**No other violations**: Foundation work introduces minimal complexity - only the abstraction layer which is explicitly justified above.

---

## Phase 0: Research & Feasibility Analysis

**Objective**: Validate technical feasibility of CollabIQ vision using Gemini API, assess Notion API compatibility, evaluate email infrastructure options, and select fuzzy matching approach. Produce go-no-go recommendation.

**Prerequisites**: None (this is the starting phase)

**Deliverables**:
1. `research.md` - Comprehensive feasibility report with all technical validations
2. Gemini API test results on Korean collaboration emails (accuracy, cost, latency)
3. Notion API validation (field type support, rate limits)
4. Email infrastructure comparison (Gmail API vs IMAP vs webhook)
5. Fuzzy matching algorithm evaluation (RapidFuzz vs alternatives)
6. Go-no-go recommendation with risk assessment

**Research Tasks**:

1. **Gemini API Validation for Korean Entity Extraction**
   - Set up Gemini API access (obtain API key, install `google-generativeai` SDK)
   - Create sample Korean collaboration emails (5-10 examples with ground truth labels):
     - Example: "어제 신세계인터와 본봄 파일럿 킥오프, 11월 1주 PoC 시작 예정"
     - Expected entities: 스타트업명=본봄, 협업기관=신세계인터내셔널, 협업강도=협력, 날짜=received date
   - Test Gemini 2.5 Flash with structured output (JSON mode):
     - Prompt engineering: Design extraction prompt with entity schema
     - Measure accuracy: Compare extracted entities vs ground truth (target ≥85%)
     - Measure confidence scoring: Verify Gemini can return per-field confidence scores
     - Measure latency: Time API calls (expected 1-3 seconds)
     - Calculate cost: Count tokens, estimate monthly cost at 50 emails/day
   - Test Gemini 2.5 Pro if Flash accuracy insufficient (higher cost, likely better accuracy)
   - Document findings in `research.md` with example prompts, accuracy metrics, cost breakdown

2. **Notion API Compatibility Validation**
   - Set up Notion API access (create integration, obtain token, install `notion-client` SDK)
   - Create test workspace with "레이더 활동" database schema:
     - 담당자 (Person field)
     - 스타트업명 (Relation to 스타트업 DB)
     - 협업기관 (Relation to 계열사 DB)
     - 협력주체 (Title field, auto-generated)
     - 협업내용 (Text field)
     - 협업형태 (Select field: [A], [B], [C], [D])
     - 협업강도 (Select field: 이해, 협력, 투자, 인수)
     - 날짜 (Date field)
   - Test creating entries programmatically:
     - Verify all field types work via SDK
     - Test relation linking (fuzzy match scenarios)
     - Measure API rate limits (3 req/s documented, validate in practice)
     - Document payload format for future implementation
   - Document findings in `research.md` with example code snippets

3. **Email Infrastructure Options Analysis**
   - Research email processing approaches:
     - **Gmail API**: Programmatic access to radar@signite.co inbox
       - Pros: Official API, rich filtering, attachment handling
       - Cons: OAuth setup complexity, quota limits (250 req/day free tier)
       - Cost: Free for reasonable volume, scales with usage
     - **IMAP**: Direct mailbox access via standard protocol
       - Pros: Simple, no API quotas, works with any email provider
       - Cons: Less reliable (connection drops), requires credential management
       - Cost: Free (self-hosted)
     - **Email Webhook** (SendGrid Inbound Parse, AWS SES, Mailgun):
       - Pros: Push-based (no polling), scales easily, reliable delivery
       - Cons: Requires domain/subdomain setup, external service dependency
       - Cost: ~$10-50/month depending on volume
   - Recommend approach based on CollabIQ constraints:
     - 50 emails/day baseline (low volume)
     - radar@signite.co email address (existing Gmail/Google Workspace?)
     - Reliability requirements (email loss tolerance)
   - Document findings in `research.md` with pros/cons matrix

4. **Fuzzy Matching Strategy Evaluation**
   - **Primary approach**: Use Gemini for fuzzy matching (simpler, leverages LLM's semantic understanding)
     - Provide Gemini with list of existing Notion company names in prompt context
     - Ask Gemini to match extracted company name to closest existing entry
     - Gemini can handle:
       - Abbreviations: "신세계인터" → "신세계인터내셔널"
       - Typos and spacing: "본봄 " → "본봄"
       - Different representations: "SSG" → "신세계" (semantic understanding)
       - Return matched name + confidence score
     - Test on sample dataset (20-30 company name pairs from Notion)
     - Measure accuracy: Does Gemini match correctly ≥85% of the time?
   - **Fallback approach** (only if Gemini matching insufficient):
     - **RapidFuzz** (modern, fast, multiple algorithms)
       - Levenshtein distance for Korean text
       - ≥0.85 similarity threshold
       - Use only if Gemini fails to achieve ≥85% matching accuracy
   - **Recommendation**: Start with Gemini-based matching (simpler architecture, one less component)
     - Pros: No separate FuzzyMatcher component needed, semantic understanding (handles abbreviations better), works in same LLM call as extraction
     - Cons: Slightly higher LLM cost (longer prompt with company list), depends on Gemini accuracy
   - Document findings in `research.md` with example prompts and accuracy comparison

5. **Go-No-Go Assessment**
   - Synthesize findings from tasks 1-4
   - Identify technical blockers (if any):
     - Gemini accuracy <85% → Recommend GPT/Claude alternative or multi-LLM
     - Notion API missing field type → Redesign data model or find workaround
     - Email infrastructure prohibitively expensive → Recommend IMAP fallback
     - Fuzzy matching can't achieve ≥0.85 threshold → Recommend manual review queue
   - Assess integration complexity and risk
   - Provide go-no-go recommendation:
     - **GO**: All technical components validated, proceed to architecture phase
     - **NO-GO**: Critical blocker identified, abort or pivot approach
   - Document in `research.md` with risk mitigation strategies

**Output**: `research.md` file in `/specs/001-feasibility-architecture/` directory

---

## Phase 1: Architecture Design & Component Contracts

**Objective**: Design system architecture with clear component boundaries, define LLMProvider abstraction layer, specify API contracts between components, design data flow and error handling, and select deployment architecture.

**Prerequisites**: Phase 0 complete (`research.md` with go-no-go recommendation: GO)

**Deliverables**:
1. `architecture.md` - Component diagram, data flow diagram, deployment architecture
2. `data-model.md` - LLMProvider interface spec, entity schemas, component contracts
3. `contracts/` directory - YAML specifications for each component interface
4. `implementation-roadmap.md` - 5-phase plan for subsequent feature branches
5. `quickstart.md` - Development environment setup guide

**Design Tasks**:

1. **Component Architecture Design**
   - Define system components with single responsibilities:
     - **EmailReceiver**: Ingest emails from radar@signite.co (Phase 1 implementation)
     - **ContentNormalizer**: Strip signatures, quoted threads, disclaimers (Phase 1)
     - **LLMProvider** (abstraction layer): Interface for entity extraction, classification, summarization, **AND company name matching** (all-in-one)
     - **GeminiAdapter** (implementation): Gemini API integration implementing LLMProvider
       - Handles extraction, classification, summarization, AND fuzzy matching in single prompt
       - Receives Notion company list as context, returns matched company names with confidence
     - **NotionIntegrator**: Create/update Notion database entries, fetch company lists for LLM context (Phase 2 implementation)
     - **VerificationQueue**: Manual review for low-confidence extractions (Phase 4 implementation)
     - **ReportGenerator**: Periodic summary analytics (Phase 5 implementation)
   - **Removed component**: FuzzyMatcher (functionality absorbed into LLMProvider/GeminiAdapter)
   - Create component diagram showing relationships and data flow
   - Document in `architecture.md`

2. **LLMProvider Abstraction Layer Specification**
   - Define `LLMProvider` abstract base class (ABC):
     ```python
     class LLMProvider(ABC):
         @abstractmethod
         def extract_entities(self, email_text: str) -> ExtractedEntities:
             """Extract key entities from email text.

             Args:
                 email_text: Normalized email body (Korean/English)

             Returns:
                 ExtractedEntities with fields:
                   - 담당자 (person_in_charge): str | None
                   - 스타트업명 (startup_name): str | None
                   - 협업기관 (partner_org): str | None
                   - 협업내용 (details): str
                   - 날짜 (date): datetime | None
                   - confidence: dict[str, float]  # Per-field confidence scores
             """
             pass

         @abstractmethod
         def classify(self, entities: ExtractedEntities, context: ClassificationContext) -> Classification:
             """Classify collaboration type and intensity.

             Args:
                 entities: Extracted entities from extract_entities()
                 context: Portfolio status, SSG affiliation lookup results

             Returns:
                 Classification with fields:
                   - 협업형태 (collab_type): Literal["[A]", "[B]", "[C]", "[D]"]
                   - 협업강도 (intensity): Literal["이해", "협력", "투자", "인수"]
                   - confidence: dict[str, float]  # Per-classification confidence
             """
             pass

         @abstractmethod
         def summarize(self, text: str, max_sentences: int = 5) -> str:
             """Generate 3-5 sentence summary preserving key details.

             Args:
                 text: Full collaboration details text
                 max_sentences: Maximum sentences in summary (3-5)

             Returns:
                 Summary string (Korean or English matching input)
             """
             pass
     ```
   - Define Pydantic models for `ExtractedEntities`, `Classification`, `ClassificationContext`
   - Document in `data-model.md` with type definitions
   - Create YAML contract in `contracts/llm_provider.yaml`

3. **GeminiAdapter Implementation Design**
   - Design concrete implementation of LLMProvider for Gemini:
     - Prompt engineering: Extraction prompt, classification prompt, summarization prompt
     - JSON schema enforcement: Use Gemini's structured output mode
     - Error handling: Retry logic for API failures, fallback for rate limits
     - Cost tracking: Log token usage per request
   - Document implementation approach in `architecture.md` (NOT actual code yet)
   - Specify how to swap to GPT/Claude later (implement GPTAdapter, ClaudeAdapter with same interface)

4. **Data Flow Diagram**
   - Map email-to-Notion workflow (simplified - no separate fuzzy matcher):
     1. EmailReceiver → raw email
     2. ContentNormalizer → cleaned text
     3. NotionIntegrator → fetch existing company lists (스타트업, 협업기관) for LLM context
     4. LLMProvider (via GeminiAdapter) → ExtractedEntities + Classification + **MatchedCompanies** (all in one call)
        - Receives: cleaned email text + company lists from Notion
        - Returns: entities + matched company IDs + confidence scores
     5. NotionIntegrator → create new "레이더 활동" entry with matched relations
     6. (If low confidence) → VerificationQueue
   - Show error paths at each step:
     - Email parsing fails → log error, notify admin
     - LLM API fails → retry with exponential backoff, queue for later
     - Notion API fails (fetch or create) → retry, queue locally, dead letter queue if unrecoverable
     - Company match confidence low (<0.85) → flag for verification, store unmatched name
   - Document in `architecture.md` with sequence diagram

5. **Error Handling & Retry Strategy**
   - Specify retry logic:
     - **LLM API failures**: Exponential backoff (1s, 2s, 4s, 8s), max 3 retries
     - **Notion API failures**: Exponential backoff (5s, 10s, 20s), max 5 retries
     - **Rate limit errors**: Queue locally, process when rate limit resets
   - Specify dead letter queue for unrecoverable errors:
     - After max retries exhausted → save to DLQ (file, database, or separate Notion database)
     - Manual review of DLQ items
   - Document in `architecture.md`

   **Edge Case Mitigation Mapping** (from spec.md lines 100-106):

   | Edge Case | Mitigation Strategy |
   |-----------|---------------------|
   | Gemini API fails to achieve ≥85% confidence on Korean text | LLMProvider abstraction layer allows easy swapping to GPT-4 or Claude without rewriting system; OR implement multi-LLM voting/consensus for higher accuracy at higher cost |
   | Notion API rate limits (3 req/s) insufficient for 50 emails/day | Calculate actual throughput requirements and design queuing/batching strategy to stay within limits (Phase 2e: error handling includes rate limit handling) |
   | Selected technology stack has licensing issues | Evaluate alternative libraries or negotiate licensing before proceeding; LLM APIs (Gemini, GPT, Claude) have commercial-friendly terms |
   | Email infrastructure (Gmail API) has prohibitive cost at scale | Compare with alternatives (IMAP self-hosted, SendGrid Inbound Parse, AWS SES) and switch if needed; abstraction in EmailReceiver component enables swapping |
   | Architecture design reveals conflicting requirements | LLM API calls (1-3 second latency) fit well with serverless constraints compared to loading large NLP models (10-30 second cold start); revise architecture accordingly if conflicts found |
   | LLM API costs become prohibitive at scale | Calculate break-even point (e.g., at 500+ emails/day, self-hosted NLP may be cheaper); LLMProvider abstraction allows swapping NLP backend without rewriting entire system |

6. **Deployment Architecture Selection (Google Cloud Platform)**
   - Compare deployment options based on research findings (all on GCP for unified billing with Gemini API):
     - **Cloud Functions (2nd gen)** (serverless):
       - Pros: Auto-scaling, pay-per-use, low maintenance, native Python 3.12 support
       - Cons: Cold starts (~1-2s), execution time limits (60 min max for 2nd gen)
       - Fit: Good for 50-100 emails/day with <3s LLM latency
       - Cost: Free tier 2M invocations/month, then ~$0.40/million invocations
     - **Cloud Run** (containerized serverless):
       - Pros: No cold starts with min instances, custom containers, scales to zero, easy local development with Docker
       - Cons: Slightly higher cost than Functions, requires Dockerfile
       - Fit: Best for 50-100 emails/day, flexible resource allocation, production-grade
       - Cost: Free tier 2M requests/month, ~$0.40/million requests + CPU/memory costs
     - **Compute Engine (GCE)** (VM-based):
       - Pros: Full control, no cold starts, persistent state, cheapest for constant load
       - Cons: Manual scaling, always-on costs, more maintenance
       - Fit: Only if processing >1000 emails/day constantly
       - Cost: ~$25-50/month for small VM (e2-micro/e2-small)
   - Recommend approach for CollabIQ: **Cloud Run** (containerized serverless)
     - Rationale: Best balance of simplicity, cost, and flexibility for 50-100 emails/day
     - Unified billing with Gemini API in GCP console
     - Easy local dev with Docker, production-grade with auto-scaling
     - Can set min instances=1 to eliminate cold starts if needed (~$10/month)
   - Document in `architecture.md` with migration path to GCE if volume exceeds 500 emails/day

7. **Component API Contracts**
   - For each component, specify:
     - Input schema (Pydantic models)
     - Output schema (Pydantic models)
     - Error conditions (exception types)
     - Example usage
   - Create YAML files in `contracts/`:
     - `llm_provider.yaml` - LLMProvider interface
     - `email_receiver.yaml` - EmailReceiver component
     - `notion_integrator.yaml` - NotionIntegrator component
   - Reference from `data-model.md`

**Output**: `architecture.md`, `data-model.md`, `contracts/*.yaml` files in `/specs/001-feasibility-architecture/` directory

---

## Phase 2: Implementation Roadmap & Project Scaffold

**Objective**: Define 5-phase implementation plan for subsequent feature branches, set up project structure with folders/files, create README and development docs, configure CI/CD, and prepare for Phase 1 feature implementation.

**Prerequisites**: Phase 1 complete (architecture design validated)

**Deliverables**:
1. `implementation-roadmap.md` - 5-phase plan with deliverables, dependencies, test strategy
2. `quickstart.md` - Development environment setup instructions
3. Project structure created (folders, README, .gitignore, Makefile, pyproject.toml)
4. `.env.example` - Configuration template
5. CI/CD pipeline skeleton (`.github/workflows/ci.yml`)
6. README.md - Project overview and getting started guide

**Implementation Planning Tasks**:

1. **Define Implementation Roadmap (Fragmented into Sprint-Sized Increments)**

   **MVP Definition**: Minimal feature set delivering value
   - Email ingestion → Gemini extraction → JSON output for manual review
   - **NOT** included in MVP: Automatic Notion creation, fuzzy matching, verification queue, reporting
   - Value delivered: Reduces manual entity extraction time by ≥30%
   - Completable in: Phase 1a (3-4 days) + Phase 1b (3-5 days) = **6-9 days total**
   - **Meets spec SC-007**: ≤2 weeks (14 days) requirement ✅

   ---

   ### **Phase 1a - Basic Email Reception** (Branch: `002-email-reception`)
   **Goal**: Receive emails and normalize content

   **Deliverables**:
   - EmailReceiver component (Gmail API or IMAP based on research)
   - ContentNormalizer removing signatures, quoted threads, disclaimers
   - Output: Cleaned email text saved to file

   **Tests**: Unit tests for normalizer (signature removal, quote stripping)

   **Success criteria**:
   - Successfully receive and clean ≥90% of test emails
   - Signature/quote removal accuracy ≥95%

   **Timeline**: 3-4 days
   **Complexity**: Low (no LLM, just text processing)

   ---

   ### **Phase 1b - Gemini Entity Extraction (MVP)** (Branch: `003-gemini-extraction`)
   **Goal**: Extract entities from cleaned emails using Gemini

   **Deliverables**:
   - LLMProvider abstract base class
   - GeminiAdapter implementing extraction (NO matching/classification yet, just entities)
   - Configuration management (API keys, settings)
   - Output: JSON file with extracted entities + confidence scores

   **Tests**: Integration tests for Gemini API (mocked + real), accuracy tests on sample emails

   **Success criteria**:
   - ≥85% entity extraction accuracy on test dataset
   - ≥90% confidence scores accurate (calibrated vs human judgment)

   **Timeline**: 3-5 days
   **Complexity**: Medium (Gemini API integration, prompt engineering)

   **MVP Complete**: After Phase 1b, team can manually create Notion entries from JSON output

   **Note**: Phase 1b implements only `extract_entities()` method. `classify()` and `summarize()` methods added in Phase 2c to complete LLMProvider interface (spec FR-008).

   ---

   ### **Phase 2a - Notion Read Operations** (Branch: `004-notion-read`)
   **Goal**: Fetch existing company lists from Notion for LLM context

   **Deliverables**:
   - NotionIntegrator component (read-only operations)
   - Fetch company lists from 스타트업 and 계열사 databases
   - Cache company lists locally (refresh every N hours)
   - Format company lists for LLM prompt context

   **Tests**: Integration tests for Notion API (list databases, query pages, handle pagination)

   **Success criteria**:
   - Successfully fetch all companies from both databases
   - Cache invalidation working correctly
   - API rate limits respected (3 req/s)

   **Timeline**: 2-3 days
   **Complexity**: Low (standard API integration)

   ---

   ### **Phase 2b - LLM-Based Company Matching** (Branch: `005-llm-matching`)
   **Goal**: Add fuzzy matching to Gemini extraction using company lists

   **Deliverables**:
   - Update GeminiAdapter to include company lists in prompt
   - Return matched company IDs with confidence scores
   - Handle no-match scenarios (return null + low confidence)

   **Tests**: Accuracy tests for matching (abbreviations, typos, semantic matches)

   **Success criteria**:
   - ≥85% correct company matches on test dataset
   - Confidence scores accurately reflect match quality

   **Timeline**: 2-3 days
   **Complexity**: Low (prompt engineering only)

   ---

   ### **Phase 2c - Classification & Summarization** (Branch: `006-classification-summarization`)
   **Goal**: Add collaboration type and intensity classification plus summarization to Gemini

   **Deliverables**:
   - Update GeminiAdapter prompt with classification rules
   - 협업형태: [A]/[B]/[C]/[D] based on portfolio/SSG status
   - 협업강도: 이해/협력/투자/인수 based on activity keywords
   - Add summarization method (3-5 sentence summaries preserving key details)
   - Return classifications + summaries with confidence scores

   **Tests**: Accuracy tests for classification against human-labeled dataset, summarization quality evaluation

   **Success criteria**:
   - ≥85% correct 협업형태 classification
   - ≥85% correct 협업강도 classification
   - Summaries preserve all key entities and activities (≥90% completeness)

   **Timeline**: 2-3 days
   **Complexity**: Low (prompt engineering, rule specification)

   ---

   ### **Phase 2d - Notion Write Operations** (Branch: `007-notion-write`)
   **Goal**: Create "레이더 활동" entries in Notion

   **Deliverables**:
   - NotionIntegrator create entry method
   - Map extracted entities + matched companies → Notion fields
   - Handle relation links (스타트업명, 협업기관)
   - Auto-generate 협력주체 field (startup-org format)

   **Tests**: Integration tests (create entry, verify fields, handle duplicates)

   **Success criteria**:
   - Successfully create Notion entry for ≥95% of valid extractions
   - All fields correctly populated

   **Timeline**: 2-3 days
   **Complexity**: Low (standard API integration)

   ---

   ### **Phase 2e - Error Handling & Retry Logic** (Branch: `008-error-handling`)
   **Goal**: Add robust error handling for LLM and Notion API failures

   **Deliverables**:
   - Exponential backoff retry logic (LLM: 3 retries, Notion: 5 retries)
   - Dead letter queue for unrecoverable errors (save to file)
   - Logging and monitoring (track success/failure rates)

   **Tests**: Failure scenario tests (API down, rate limits, timeouts)

   **Success criteria**:
   - Graceful degradation when APIs fail
   - No data loss (DLQ captures all failures)

   **Timeline**: 2-3 days
   **Complexity**: Medium (error scenarios, retry logic)

   ---

   ### **Phase 3a - Verification Queue Storage** (Branch: `009-queue-storage`)
   **Goal**: Store low-confidence extractions for manual review

   **Deliverables**:
   - VerificationQueue component
   - Store records with confidence <0.85
   - Flag specific fields needing review (e.g., ambiguous company match)
   - Simple file-based storage (JSON or SQLite)

   **Tests**: Unit tests for queue operations (add, list, update, remove)

   **Success criteria**:
   - All low-confidence records captured
   - Queue queryable by confidence threshold

   **Timeline**: 2-3 days
   **Complexity**: Low (CRUD operations)

   ---

   ### **Phase 3b - Review UI (Simple)** (Branch: `010-review-ui`)
   **Goal**: Web interface for manual review of queued records

   **Deliverables**:
   - Simple FastAPI web app (HTML templates)
   - List queued records with flagged fields highlighted
   - Edit form to correct extractions
   - Approve button → create Notion entry

   **Tests**: UI tests (Selenium or Playwright)

   **Success criteria**:
   - ≤2 minutes average review time per record
   - UI works on mobile (responsive design)

   **Timeline**: 3-4 days
   **Complexity**: Medium (UI development)

   ---

   ### **Phase 4a - Basic Reporting** (Branch: `011-basic-reporting`)
   **Goal**: Generate simple summary statistics

   **Deliverables**:
   - ReportGenerator component
   - Query Notion for all collaboration records
   - Calculate basic stats (count by type, count by intensity, top companies)
   - Output: Markdown report

   **Tests**: Data accuracy tests (compare to manual calculation)

   **Success criteria**:
   - Stats match manual calculation (≤1% variance)
   - Report generation completes in <5 minutes

   **Timeline**: 2-3 days
   **Complexity**: Low (aggregation queries)

   ---

   ### **Phase 4b - Advanced Analytics** (Branch: `012-advanced-analytics`)
   **Goal**: Add trends, insights, and Notion publishing

   **Deliverables**:
   - Time-series trends (collaborations over time)
   - Highlight detection (top 5 most significant collaborations)
   - Insight generation (LLM-based observations)
   - Publish report as Notion page with proper formatting

   **Tests**: Data quality tests, Notion integration tests

   **Success criteria**:
   - Insights are actionable and accurate
   - Notion page properly formatted with links

   **Timeline**: 3-4 days
   **Complexity**: Medium (LLM for insights, Notion page creation)

   ---

   ### **Dependency Graph**:
   ```
   Phase 1a (email reception)
       ↓
   Phase 1b (extraction) → MVP ✅
       ↓
   Phase 2a (Notion read)
       ↓
   Phase 2b (LLM matching) ← depends on 2a
       ↓
   Phase 2c (classification) ← depends on 2b
       ↓
   Phase 2d (Notion write) ← depends on 2a, 2c
       ↓
   Phase 2e (error handling) ← depends on 2d
       ↓
   Phase 3a (queue storage) ← depends on 2e
       ↓
   Phase 3b (review UI) ← depends on 3a
       ↓
   Phase 4a (basic reporting) ← depends on 2d (needs data)
       ↓
   Phase 4b (advanced analytics) ← depends on 4a
   ```

   **Total**: 12 phases, each 2-5 days of focused work

   - Document test strategy per phase in `implementation-roadmap.md`

2. **Create Project Scaffold**
   - Create folder structure (as defined in Project Structure section above)
   - Initialize Python project with UV:
     - `uv init --package`
     - `uv python pin 3.12`
     - Create `pyproject.toml` with project metadata
   - Create placeholder `__init__.py` files in each `src/` subdirectory
   - Create README.md with:
     - Project overview
     - Architecture summary (link to `specs/001-feasibility-architecture/architecture.md`)
     - Getting started guide (link to `quickstart.md`)
     - Development workflow
     - Contributing guidelines
   - Create `.gitignore` for Python projects (venv, __pycache__, .env, etc.)
   - Create Makefile with common tasks:
     ```makefile
     .PHONY: install test lint format run clean

     install:
         uv sync

     test:
         uv run pytest

     lint:
         uv run ruff check .
         uv run mypy src/

     format:
         uv run ruff format .
         uv run ruff check --fix .

     clean:
         find . -type d -name __pycache__ -exec rm -rf {} +
         find . -type f -name "*.pyc" -delete
     ```

3. **Create Configuration Management**
   - Create `.env.example` with required variables:
     ```
     # Gemini API
     GEMINI_API_KEY=your_gemini_api_key_here
     GEMINI_MODEL=gemini-2.5-flash  # or gemini-2.5-pro

     # Notion API
     NOTION_API_KEY=your_notion_integration_token_here
     NOTION_DATABASE_ID_RADAR=your_radar_database_id_here
     NOTION_DATABASE_ID_STARTUP=your_startup_database_id_here
     NOTION_DATABASE_ID_CORP=your_corp_database_id_here

     # Email (choose one based on research findings)
     # Option 1: Gmail API
     GMAIL_CREDENTIALS_PATH=path/to/credentials.json
     # Option 2: IMAP
     IMAP_HOST=imap.gmail.com
     IMAP_PORT=993
     IMAP_USERNAME=radar@signite.co
     IMAP_PASSWORD=your_password_here
     # Option 3: Webhook
     WEBHOOK_SECRET=your_webhook_secret_here

     # Fuzzy Matching
     FUZZY_MATCH_THRESHOLD=0.85

     # Processing
     CONFIDENCE_THRESHOLD=0.85
     MAX_RETRIES=3
     RETRY_DELAY_SECONDS=5
     ```
   - Create `config/settings.py` using Pydantic:
     ```python
     from pydantic_settings import BaseSettings

     class Settings(BaseSettings):
         gemini_api_key: str
         gemini_model: str = "gemini-2.5-flash"

         notion_api_key: str
         notion_database_id_radar: str
         notion_database_id_startup: str
         notion_database_id_corp: str

         fuzzy_match_threshold: float = 0.85
         confidence_threshold: float = 0.85

         class Config:
             env_file = ".env"
     ```

4. **Create quickstart.md**
   - Document step-by-step development environment setup:
     1. Prerequisites (Python 3.12, UV, Git)
     2. Clone repository
     3. Install dependencies (`uv sync`)
     4. Configure environment variables (copy `.env.example` to `.env`, fill in keys)
     5. Validate setup (run `make test`, `make lint`)
     6. Next steps (implement Phase 1 in branch `002-email-entity-extraction`)
   - Target: New developer can run project locally within 30 minutes (SC-010)

5. **Set Up CI/CD Pipeline**
   - Create `.github/workflows/ci.yml`:
     ```yaml
     name: CI

     on: [push, pull_request]

     jobs:
       test:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v3
           - name: Set up Python
             uses: actions/setup-python@v4
             with:
               python-version: '3.12'
           - name: Install UV
             run: curl -LsSf https://astral.sh/uv/install.sh | sh
           - name: Install dependencies
             run: uv sync
           - name: Run linting
             run: |
               uv run ruff check .
               uv run mypy src/
           - name: Run tests
             run: uv run pytest
     ```
   - Validate pipeline runs successfully (even with no tests yet)

6. **Install Initial Dependencies**
   - Add core dependencies to `pyproject.toml` via UV:
     - `uv add google-generativeai`  # Gemini API SDK
     - `uv add notion-client`  # Notion SDK
     - `uv add rapidfuzz`  # Fuzzy matching
     - `uv add pydantic pydantic-settings`  # Data validation + config
     - `uv add --dev pytest pytest-asyncio pytest-mock`  # Testing
     - `uv add --dev ruff mypy`  # Code quality
   - Validate all imports work (create simple test scripts)

**Output**: Project structure created, `implementation-roadmap.md`, `quickstart.md`, README.md, all configuration files

---

## Phase 3: Update Agent Context & Documentation

**Objective**: Update agent-specific context files with new technology decisions, create comprehensive project documentation linking all foundation artifacts, and prepare repository for feature implementation branches.

**Prerequisites**: Phase 2 complete (project scaffold exists)

**Deliverables**:
1. Updated agent context file (`.claude/` or equivalent)
2. docs/ARCHITECTURE.md - Copy of architecture design with diagrams
3. docs/IMPLEMENTATION_ROADMAP.md - Copy of phasing plan for easy reference
4. docs/API_CONTRACTS.md - Consolidated component interface docs
5. Updated README.md with links to all documentation

**Tasks**:

1. **Update Agent Context**
   - Run `.specify/scripts/bash/update-agent-context.sh claude` (or appropriate agent)
   - Script will detect which AI agent is in use and update the appropriate context file
   - Add technology decisions from this foundation work:
     - Language: Python 3.12
     - NLP: Gemini API (google-generativeai SDK)
     - Architecture: LLMProvider abstraction layer with GeminiAdapter
     - Storage: Notion databases
     - Deployment: Monolithic service (initially)
   - Preserve any manual additions between markers

2. **Create Comprehensive Documentation**
   - Copy `specs/001-feasibility-architecture/architecture.md` → `docs/ARCHITECTURE.md`
   - Copy `specs/001-feasibility-architecture/implementation-roadmap.md` → `docs/IMPLEMENTATION_ROADMAP.md`
   - Create `docs/API_CONTRACTS.md` consolidating all contract YAML files with explanations
   - Update README.md with navigation:
     - Project overview
     - [Architecture](docs/ARCHITECTURE.md)
     - [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)
     - [API Contracts](docs/API_CONTRACTS.md)
     - [Quickstart Guide](specs/001-feasibility-architecture/quickstart.md)
     - [Foundation Work Spec](specs/001-feasibility-architecture/spec.md)

3. **Validate Foundation Work Complete**
   - Review checklist from spec.md:
     - ✅ Feasibility report exists (`research.md`)
     - ✅ Architecture design exists (`architecture.md`, component diagrams)
     - ✅ Implementation roadmap exists (`implementation-roadmap.md`, 5 phases defined)
     - ✅ Project scaffold exists (folders, README, config, CI/CD)
     - ✅ Quickstart guide exists (`quickstart.md`)
     - ✅ All dependencies installed and working
   - Run `make test` to validate CI/CD pipeline works
   - Run `make lint` to validate code quality checks work
   - Verify new developer can follow `quickstart.md` and set up environment within 30 minutes

**Output**: Updated agent context, comprehensive documentation in `docs/`, validated project setup

---

## Summary & Next Steps

### Foundation Work Completion Checklist

- ⏸️ **User Story 1 (P1) - Feasibility Analysis** (AWAITING USER - API KEYS REQUIRED)
  - [ ] `research.md` with Gemini API validation results
  - [ ] Notion API compatibility verified
  - [ ] Email infrastructure recommendation
  - [ ] Fuzzy matching algorithm selected
  - [ ] Go-no-go recommendation documented
  - **Note**: Templates created (`research-template.md`, `email-infrastructure-comparison.md`) to guide user through testing with their API keys

- ✅ **User Story 2 (P2) - Architecture Design** (COMPLETE)
  - [x] `architecture.md` with component diagram and data flow
  - [x] `data-model.md` with LLMProvider interface specification
  - [x] `contracts/*.yaml` with component API contracts
  - [x] Error handling strategy documented
  - [x] Deployment architecture selected (Google Cloud Run)

- ✅ **User Story 3 (P3) - Implementation Strategy** (COMPLETE)
  - [x] `implementation-roadmap.md` with 12-phase plan (updated from 5-phase)
  - [x] MVP defined (Phase 1a + 1b = 6-9 days)
  - [x] Phase dependencies mapped (dependency graph included)
  - [x] Test strategy per phase documented

- ✅ **User Story 4 (P4) - Project Setup** (COMPLETE)
  - [x] Project structure created (src/, tests/, config/, docs/)
  - [x] `pyproject.toml` with dependencies (google-generativeai, notion-client, pydantic-settings, pytest, ruff, mypy, pytest-cov)
  - [x] `.env.example` with configuration template
  - [x] `.env` with placeholders for user to fill in API keys
  - [x] `quickstart.md` with setup instructions
  - [x] `README.md` with project overview
  - [x] CI/CD pipeline working (`.github/workflows/ci.yml` validated locally)
  - [x] All dependencies installed and validated (uv.lock generated)
  - [x] Makefile with common tasks (install, test, lint, format, clean)
  - [x] docs/ARCHITECTURE.md, docs/IMPLEMENTATION_ROADMAP.md, docs/API_CONTRACTS.md created

### Artifacts Generated

**Specification Directory** (`specs/001-feasibility-architecture/`):
- ✅ spec.md (already exists)
- ✅ plan.md (this file - updated with completion status)
- ⏸️ research.md (Phase 0 output - awaiting user API testing)
- ✅ research-template.md (Phase 0 guide - created to help user complete feasibility)
- ✅ email-infrastructure-comparison.md (Phase 0 template - created)
- ✅ architecture.md (Phase 1 output)
- ✅ data-model.md (Phase 1 output)
- ✅ implementation-roadmap.md (Phase 2 output - 12 phases)
- ✅ quickstart.md (Phase 2 output)
- ✅ contracts/ (Phase 1 output)
  - ✅ llm_provider.yaml
  - ✅ email_receiver.yaml
  - ✅ notion_integrator.yaml

**Repository Root**:
- ✅ README.md (Phase 2 output)
- ✅ docs/ARCHITECTURE.md (Phase 3 output - copied from specs/)
- ✅ docs/IMPLEMENTATION_ROADMAP.md (Phase 3 output - copied from specs/)
- ✅ docs/API_CONTRACTS.md (Phase 3 output - consolidated from contracts/)
- ✅ docs/quickstart.md (Phase 3 output)
- ✅ src/ folder structure (Phase 2 output)
  - ✅ src/llm_provider/, src/llm_adapters/, src/email_receiver/, src/notion_integrator/, src/verification_queue/, src/reporting/
- ✅ tests/ folder structure (Phase 2 output)
  - ✅ tests/unit/, tests/integration/, tests/contract/
- ✅ config/ folder (Phase 2 output)
  - ✅ config/settings.py (Pydantic settings)
  - ✅ config/__init__.py
- ✅ .github/workflows/ci.yml (Phase 2 output - validated locally)
- ✅ pyproject.toml (Phase 2 output - with all dependencies)
- ✅ .env.example (Phase 2 output)
- ✅ .env (created with placeholders for user)
- ✅ Makefile (Phase 2 output)
- ✅ .gitignore (Phase 2 output)

### Next Feature Branches

**After 001-feasibility-architecture completes**, proceed with feature implementation (12 sequential phases):

### **MVP Track** (Phases 1a-1b):
1. **002-email-reception** (Phase 1a) - Email ingestion + normalization [3-4 days]
2. **003-gemini-extraction** (Phase 1b) - Entity extraction via Gemini [3-5 days]
   → **MVP Complete**: Team can manually create Notion entries from JSON

### **Automation Track** (Phases 2a-2e):
3. **004-notion-read** (Phase 2a) - Fetch company lists [2-3 days]
4. **005-llm-matching** (Phase 2b) - LLM-based fuzzy matching [2-3 days]
5. **006-classification-summarization** (Phase 2c) - Add classification + summarization [2-3 days]
6. **007-notion-write** (Phase 2d) - Auto-create Notion entries [2-3 days]
7. **008-error-handling** (Phase 2e) - Retry logic, DLQ [2-3 days]
   → **Full Automation Complete**: Email → Notion without manual intervention

### **Quality Track** (Phases 3a-3b):
8. **009-queue-storage** (Phase 3a) - Store low-confidence records [2-3 days]
9. **010-review-ui** (Phase 3b) - Manual review interface [3-4 days]
   → **Production-Ready**: Edge cases handled gracefully

### **Analytics Track** (Phases 4a-4b):
10. **011-basic-reporting** (Phase 4a) - Simple stats [2-3 days]
11. **012-advanced-analytics** (Phase 4b) - Trends, insights, Notion publishing [3-4 days]
    → **Complete System**: Full end-to-end including reporting

**Total**: 12 phases, work at your own pace step-by-step

### Constitution Compliance

This foundation work **complies with all CollabIQ Constitution principles**:
- ✅ Principle I: Specification exists before planning
- ✅ Principle II: Independent user stories with P1 as MVP
- ✅ Principle III: TDD deferred to feature implementation (N/A for foundation docs)
- ✅ Principle IV: All required design artifacts will be produced
- ✅ Principle V: Complexity (abstraction layer) explicitly justified

**Gate 2 Status**: ✅ **READY FOR IMPLEMENTATION** (after foundation work completes)

---

**Implementation will NOT begin until**:
1. All Phase 0-2 tasks complete
2. All deliverables exist and are validated
3. Constitution check re-validated after design complete
4. Technical lead approves architecture and roadmap

**This plan document** serves as the blueprint for executing foundation work. No feature implementation code will be written in this branch - only analysis, design, planning, and project structure setup.
