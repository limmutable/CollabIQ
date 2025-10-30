# Tasks: Email Reception and Normalization

**Input**: Design documents from `/specs/002-email-reception/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: TDD required - tests written before implementation per constitution Principle III

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Note**: This task list focuses on **Gmail API implementation** with placeholder tasks for IMAP and webhook methods (per user request).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `data/`, `config/` at repository root
- This feature works primarily with email ingestion and cleaning components

---

## Phase 1: Setup (Preparation)

**Purpose**: Initialize project structure and dependencies for email reception

- [X] T001 Verify Python 3.12 environment with UV package manager (run `uv python --version`)
- [X] T002 [P] Install Gmail API dependencies: `uv add google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2`
- [X] T003 [P] Install Cloud Pub/Sub dependencies: `uv add google-cloud-pubsub`
- [X] T004 [P] Install Pydantic for data models: `uv add pydantic pydantic-settings`
- [X] T005 [P] Install testing dependencies: `uv add --dev pytest pytest-mock pytest-asyncio pytest-cov`
- [X] T006 Create directory structure: `data/raw/`, `data/cleaned/`, `data/metadata/`
- [X] T007 Create directory structure: `src/email_receiver/`, `src/content_normalizer/`, `src/models/`
- [X] T008 Create directory structure: `tests/unit/`, `tests/integration/`, `tests/fixtures/sample_emails/`
- [X] T009 Create `.env.example` template with Gmail API credentials placeholders in repository root
- [X] T010 Create `.gitignore` entries for `data/`, `.env`, `credentials.json`, `token.json`

**Checkpoint**: Environment ready - all dependencies installed, directory structure in place

---

## Phase 2: Foundational (Data Models & Base Interfaces)

**Purpose**: Establish foundational data models and interfaces that all user stories depend on

- [X] T011 [P] Create EmailAttachment Pydantic model in `src/models/raw_email.py` per data-model.md
- [X] T012 [P] Create EmailMetadata Pydantic model in `src/models/raw_email.py` with validation per data-model.md
- [X] T013 Create RawEmail Pydantic model in `src/models/raw_email.py` with body validation per FR-003
- [X] T014 [P] Create CleaningStatus enum in `src/models/cleaned_email.py` per data-model.md
- [X] T015 [P] Create RemovedContent Pydantic model in `src/models/cleaned_email.py` with removal_percentage property
- [X] T016 Create CleanedEmail Pydantic model in `src/models/cleaned_email.py` per FR-007, FR-008
- [X] T017 Create EmailReceiver abstract base class interface in `src/email_receiver/base.py` per contracts/email_receiver.yaml
- [X] T018 Create ContentNormalizer interface skeleton in `src/content_normalizer/normalizer.py` (method signatures only)
- [X] T019 [P] Create `src/models/__init__.py` exposing RawEmail, CleanedEmail
- [X] T020 [P] Create `src/email_receiver/__init__.py` exposing EmailReceiver base class
- [X] T021 [P] Create `src/content_normalizer/__init__.py` exposing ContentNormalizer

**Checkpoint**: All foundational data models and interfaces created - ready for user story implementation

---

## Phase 3: User Story 1 - Receive and Store Raw Emails (Priority: P1) 🎯 MVP

**Goal**: Retrieve emails from portfolioupdates@signite.co and store as raw JSON files

**Independent Test**: Send test emails to inbox, verify retrieval within 5 minutes, check raw JSON files created in `data/raw/YYYY/MM/`

### Unit Tests for User Story 1 (TDD - Write First)

- [X] T022 [P] [US1] Create test fixtures: sample Gmail API message response JSON in `tests/fixtures/sample_emails/gmail_api_response.json`
- [X] T023 [P] [US1] Create test fixture: mock credentials in `tests/fixtures/mock_credentials.json`
- [X] T024 [US1] Write unit test `test_gmail_receiver_connect()` in `tests/unit/test_gmail_receiver.py` - verify OAuth2 connection
- [X] T025 [US1] Write unit test `test_gmail_receiver_fetch_new_messages()` in `tests/unit/test_gmail_receiver.py` - mock Gmail API list response
- [X] T026 [US1] Write unit test `test_gmail_receiver_parse_message()` in `tests/unit/test_gmail_receiver.py` - verify RawEmail creation from API response
- [X] T027 [US1] Write unit test `test_gmail_receiver_save_raw_email()` in `tests/unit/test_gmail_receiver.py` - verify JSON file creation with correct path
- [X] T028 [US1] Write unit test `test_gmail_receiver_exponential_backoff()` in `tests/unit/test_gmail_receiver.py` - verify retry logic per FR-010

### Implementation for User Story 1 (Gmail API Focus)

- [X] T029 [US1] Implement GmailReceiver class in `src/email_receiver/gmail_receiver.py` inheriting from EmailReceiver base
- [X] T030 [US1] Implement `connect()` method with Gmail API OAuth2 flow per contracts/email_receiver.yaml
- [X] T031 [US1] Implement `fetch_new_messages()` method calling Gmail API users().messages().list() per FR-002
- [X] T032 [US1] Implement `parse_message()` method converting Gmail API response to RawEmail model per data-model.md
- [X] T033 [US1] Implement `save_raw_email()` method saving to `data/raw/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json` per FR-003
- [X] T034 [US1] Implement exponential backoff retry decorator in `src/email_receiver/gmail_receiver.py` per FR-010 (max 3 retries)
- [X] T035 [US1] Implement connection error handling (CONNECTION_FAILED, AUTHENTICATION_FAILED) per contracts/email_receiver.yaml
- [X] T036 [US1] Add logging to `src/email_receiver/gmail_receiver.py` for all operations per FR-009

### Placeholder Tasks for Other Email Reception Methods

- [X] T037 [US1] **PLACEHOLDER**: Create IMAPReceiver class skeleton in `src/email_receiver/imap_receiver.py` (empty methods with docstrings)
- [X] T038 [US1] **PLACEHOLDER**: Create WebhookReceiver class skeleton in `src/email_receiver/webhook_receiver.py` (empty methods with docstrings)

### Integration Tests for User Story 1

- [X] T039 [US1] Write integration test `test_gmail_receiver_end_to_end()` in `tests/integration/test_email_receiver_gmail.py` - full fetch and save flow
- [X] T040 [US1] Write integration test `test_duplicate_detection()` in `tests/integration/test_email_receiver_gmail.py` - verify message ID tracking per FR-011
- [X] T041 [US1] Write integration test `test_empty_inbox()` in `tests/integration/test_email_receiver_gmail.py` - verify graceful handling of zero emails

### Duplicate Detection Implementation

- [ ] T042 [US1] Create DuplicateTracker Pydantic model in `src/models/duplicate_tracker.py` per data-model.md
- [ ] T043 [US1] Implement `is_duplicate()` method checking message ID in `data/metadata/processed_ids.json` per FR-011
- [ ] T044 [US1] Implement `mark_as_processed()` method adding message ID to tracker per FR-011
- [ ] T045 [US1] Integrate duplicate detection into GmailReceiver.fetch_new_messages() per FR-011

**Checkpoint**: Gmail API receiver fully functional - emails retrieved, saved as raw JSON, duplicates handled ✅

**Verification for US1**:
```bash
# Send test email to portfolioupdates@signite.co
# Run GmailReceiver
uv run python -m src.email_receiver.gmail_receiver

# Verify raw email file created
ls -l data/raw/$(date +%Y)/$(date +%m)/

# Verify message ID in processed tracker
cat data/metadata/processed_ids.json

# Run unit tests
uv run pytest tests/unit/test_gmail_receiver.py -v

# Run integration tests (requires Gmail API credentials)
uv run pytest tests/integration/test_email_receiver_gmail.py -v
```

---

## Phase 4: User Story 2 - Remove Email Signatures (Priority: P2)

**Goal**: Detect and remove Korean and English email signatures from email body

**Independent Test**: Provide emails with various signature patterns, run ContentNormalizer, verify 95% signature removal accuracy per SC-002

### Unit Tests for User Story 2 (TDD - Write First)

- [ ] T046 [P] [US2] Create test fixtures: Korean signature samples in `tests/fixtures/sample_emails/korean_signature_*.txt` (5 variations)
- [ ] T047 [P] [US2] Create test fixtures: English signature samples in `tests/fixtures/sample_emails/english_signature_*.txt` (5 variations)
- [ ] T048 [US2] Write unit test `test_detect_korean_signature()` in `tests/unit/test_content_normalizer.py` - verify pattern matching
- [ ] T049 [US2] Write unit test `test_detect_english_signature()` in `tests/unit/test_content_normalizer.py` - verify pattern matching
- [ ] T050 [US2] Write unit test `test_remove_signature_preserves_content()` in `tests/unit/test_content_normalizer.py` - verify collaboration content intact
- [ ] T051 [US2] Write unit test `test_no_signature_no_change()` in `tests/unit/test_content_normalizer.py` - verify emails without signatures unchanged

### Signature Pattern Library Implementation

- [ ] T052 [US2] Create signature patterns module `src/content_normalizer/patterns.py` per contracts/content_normalizer.yaml
- [ ] T053 [US2] Define Korean signature regex patterns in `src/content_normalizer/patterns.py` (감사합니다, 드림, 올림) per research.md
- [ ] T054 [US2] Define English signature regex patterns in `src/content_normalizer/patterns.py` (Best regards, Sincerely, Thanks) per research.md
- [ ] T055 [US2] Implement heuristic signature detection (separator lines, contact info patterns) as fallback per edge cases

### ContentNormalizer Implementation (Signature Removal)

- [ ] T056 [US2] Implement `detect_signature()` method in `src/content_normalizer/normalizer.py` using patterns per FR-004
- [ ] T057 [US2] Implement `remove_signature()` method in `src/content_normalizer/normalizer.py` per FR-004
- [ ] T058 [US2] Implement signature removal accuracy tracking in RemovedContent model per SC-002
- [ ] T059 [US2] Add logging for signature detection and removal per FR-009

### Accuracy Tests for User Story 2

- [ ] T060 [US2] Write accuracy test `test_signature_removal_accuracy_95_percent()` in `tests/unit/test_content_normalizer.py` - verify SC-002 target
- [ ] T061 [US2] Create accuracy test dataset (20+ emails) in `tests/fixtures/sample_emails/accuracy_test_signatures/`

**Checkpoint**: Signature removal implemented with 95% accuracy target ✅

**Verification for US2**:
```bash
# Run signature removal tests
uv run pytest tests/unit/test_content_normalizer.py::test_detect_korean_signature -v
uv run pytest tests/unit/test_content_normalizer.py::test_detect_english_signature -v

# Run accuracy test
uv run pytest tests/unit/test_content_normalizer.py::test_signature_removal_accuracy_95_percent -v

# Verify 95% accuracy threshold met
```

---

## Phase 5: User Story 3 - Remove Quoted Thread Content (Priority: P2)

**Goal**: Detect and remove quoted email reply chains from email body

**Independent Test**: Provide emails with reply threads, run ContentNormalizer, verify 95% quoted thread removal accuracy per SC-003

### Unit Tests for User Story 3 (TDD - Write First)

- [ ] T062 [P] [US3] Create test fixtures: quoted thread samples in `tests/fixtures/sample_emails/quoted_thread_*.txt` (angle brackets, headers, nested)
- [ ] T063 [US3] Write unit test `test_detect_angle_bracket_quotes()` in `tests/unit/test_content_normalizer.py` - verify "> " prefix detection
- [ ] T064 [US3] Write unit test `test_detect_on_date_header()` in `tests/unit/test_content_normalizer.py` - verify "On [date] wrote:" detection
- [ ] T065 [US3] Write unit test `test_remove_nested_quotes()` in `tests/unit/test_content_normalizer.py` - verify multi-level quote removal
- [ ] T066 [US3] Write unit test `test_no_quotes_no_change()` in `tests/unit/test_content_normalizer.py` - verify fresh emails unchanged

### Quote Pattern Library Implementation

- [ ] T067 [US3] Define angle bracket quote regex patterns in `src/content_normalizer/patterns.py` per FR-005
- [ ] T068 [US3] Define "On [date] wrote:" header patterns in `src/content_normalizer/patterns.py` per FR-005
- [ ] T069 [US3] Implement nested quote detection algorithm in `src/content_normalizer/patterns.py` per acceptance scenarios

### ContentNormalizer Implementation (Quote Removal)

- [ ] T070 [US3] Implement `detect_quoted_thread()` method in `src/content_normalizer/normalizer.py` using patterns per FR-005
- [ ] T071 [US3] Implement `remove_quoted_thread()` method in `src/content_normalizer/normalizer.py` per FR-005
- [ ] T072 [US3] Implement quote removal accuracy tracking in RemovedContent model per SC-003
- [ ] T073 [US3] Add logging for quote detection and removal per FR-009

### Accuracy Tests for User Story 3

- [ ] T074 [US3] Write accuracy test `test_quote_removal_accuracy_95_percent()` in `tests/unit/test_content_normalizer.py` - verify SC-003 target
- [ ] T075 [US3] Create accuracy test dataset (20+ reply emails) in `tests/fixtures/sample_emails/accuracy_test_quotes/`

**Checkpoint**: Quoted thread removal implemented with 95% accuracy target ✅

**Verification for US3**:
```bash
# Run quote removal tests
uv run pytest tests/unit/test_content_normalizer.py::test_detect_angle_bracket_quotes -v
uv run pytest tests/unit/test_content_normalizer.py::test_detect_on_date_header -v
uv run pytest tests/unit/test_content_normalizer.py::test_remove_nested_quotes -v

# Run accuracy test
uv run pytest tests/unit/test_content_normalizer.py::test_quote_removal_accuracy_95_percent -v
```

---

## Phase 6: User Story 4 - Remove Disclaimers and Boilerplate (Priority: P3)

**Goal**: Detect and remove legal disclaimers and confidentiality notices from email body

**Independent Test**: Provide emails with disclaimer patterns, run ContentNormalizer, verify disclaimers removed while content preserved

### Unit Tests for User Story 4 (TDD - Write First)

- [ ] T076 [P] [US4] Create test fixtures: disclaimer samples in `tests/fixtures/sample_emails/disclaimer_*.txt` (confidentiality, legal, "intended only")
- [ ] T077 [US4] Write unit test `test_detect_confidentiality_disclaimer()` in `tests/unit/test_content_normalizer.py` - verify pattern matching
- [ ] T078 [US4] Write unit test `test_detect_intended_only_notice()` in `tests/unit/test_content_normalizer.py` - verify pattern matching
- [ ] T079 [US4] Write unit test `test_remove_disclaimer_preserves_content()` in `tests/unit/test_content_normalizer.py` - verify collaboration content intact

### Disclaimer Pattern Library Implementation

- [ ] T080 [US4] Define confidentiality disclaimer patterns in `src/content_normalizer/patterns.py` per FR-006
- [ ] T081 [US4] Define "intended only" notice patterns in `src/content_normalizer/patterns.py` per FR-006
- [ ] T082 [US4] Define common corporate boilerplate patterns in `src/content_normalizer/patterns.py`

### ContentNormalizer Implementation (Disclaimer Removal)

- [ ] T083 [US4] Implement `detect_disclaimer()` method in `src/content_normalizer/normalizer.py` using patterns per FR-006
- [ ] T084 [US4] Implement `remove_disclaimer()` method in `src/content_normalizer/normalizer.py` per FR-006
- [ ] T085 [US4] Implement disclaimer removal tracking in RemovedContent model
- [ ] T086 [US4] Add logging for disclaimer detection and removal per FR-009

**Checkpoint**: Disclaimer removal implemented ✅

**Verification for US4**:
```bash
# Run disclaimer removal tests
uv run pytest tests/unit/test_content_normalizer.py::test_detect_confidentiality_disclaimer -v
uv run pytest tests/unit/test_content_normalizer.py::test_detect_intended_only_notice -v
uv run pytest tests/unit/test_content_normalizer.py::test_remove_disclaimer_preserves_content -v
```

---

## Phase 7: ContentNormalizer Integration & End-to-End Testing

**Purpose**: Integrate all cleaning stages and validate complete pipeline

### ContentNormalizer Main Pipeline

- [ ] T087 Implement three-stage cleaning pipeline in `src/content_normalizer/normalizer.py` (disclaimers → quotes → signatures) per plan.md
- [ ] T088 Implement `normalize()` main method orchestrating all cleaning stages per contracts/content_normalizer.yaml
- [ ] T089 Implement empty content handling per FR-012 (flag emails with no content after cleaning)
- [ ] T090 Implement CleanedEmail model creation with RemovedContent summary per data-model.md
- [ ] T091 Implement `save_cleaned_email()` method saving to `data/cleaned/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json` per FR-008

### End-to-End Integration Tests

- [ ] T092 Write integration test `test_email_pipeline_end_to_end()` in `tests/integration/test_end_to_end_email.py` - full Gmail fetch → clean → save flow
- [ ] T093 Write integration test `test_mixed_language_content()` in `tests/integration/test_end_to_end_email.py` - verify Korean + English handling per edge cases
- [ ] T094 Write integration test `test_empty_email_after_cleaning()` in `tests/integration/test_end_to_end_email.py` - verify FR-012 flagging
- [ ] T095 Write integration test `test_performance_50_emails_10_minutes()` in `tests/integration/test_end_to_end_email.py` - verify SC-006 (12 sec/email average)

**Checkpoint**: Complete email reception and normalization pipeline functional ✅

**Verification**:
```bash
# Run end-to-end test with real Gmail API
uv run pytest tests/integration/test_end_to_end_email.py -v

# Verify performance target
uv run pytest tests/integration/test_end_to_end_email.py::test_performance_50_emails_10_minutes -v

# Check cleaned email files
ls -l data/cleaned/$(date +%Y)/$(date +%m)/
cat data/cleaned/$(date +%Y)/$(date +%m)/<latest_file>.json | jq '.cleaned_body'
```

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Finalize configuration, logging, error handling, and documentation

- [ ] T096 [P] Create comprehensive logging configuration in `src/config/logging_config.py` per FR-009
- [ ] T097 [P] Create Pydantic Settings model for environment variables in `src/config/settings.py` (Gmail credentials, Pub/Sub topic)
- [ ] T098 [P] Write README for email reception component in `src/email_receiver/README.md`
- [ ] T099 [P] Write README for content normalizer component in `src/content_normalizer/README.md`
- [ ] T100 Create CLI entry point `src/cli.py` for manual testing of email reception pipeline
- [ ] T101 Implement rate limit handling (RATE_LIMIT_EXCEEDED error) per edge cases
- [ ] T102 Add configuration validation on startup (verify credentials, directory permissions)
- [ ] T103 Create quickstart verification script `scripts/verify_setup.sh` checking all prerequisites per quickstart.md
- [ ] T104 Run final test suite and verify all tests pass: `uv run pytest tests/ -v --cov=src --cov-report=html`
- [ ] T105 Verify success criteria SC-001 through SC-007 documented in completion-report.md

**Checkpoint**: Feature complete, all tests passing, ready for deployment ✅

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (Phase 1)
- **User Story 1 (Phase 3)**: Depends on Foundational completion (Phase 2)
- **User Story 2 (Phase 4)**: Depends on Foundational completion (Phase 2) - **Can run in parallel with US1**
- **User Story 3 (Phase 5)**: Depends on Foundational completion (Phase 2) - **Can run in parallel with US1, US2**
- **User Story 4 (Phase 6)**: Depends on Foundational completion (Phase 2) - **Can run in parallel with US1, US2, US3**
- **Integration (Phase 7)**: Depends on US1-US4 completion (Phases 3-6)
- **Polish (Phase 8)**: Depends on Integration completion (Phase 7)

### User Story Dependencies

```text
Foundational (Phase 2)
      │
      ├──────> US1 (Phase 3) ────┐
      ├──────> US2 (Phase 4) ────┤
      ├──────> US3 (Phase 5) ────┼──> Integration (Phase 7) ──> Polish (Phase 8)
      └──────> US4 (Phase 6) ────┘
```

**Key Insight**: User Stories 2, 3, 4 can all be developed in parallel after Foundational phase, as they are independent cleaning operations. Only US1 (email reception) is a hard dependency for integration testing.

### Within Each User Story

**User Story 1** (P1 - Email Reception):
- T022-T028: Tests can be written in parallel
- T029-T036: Implementation must be sequential (Gmail API integration)
- T037-T038: Placeholder tasks (no dependencies)
- T039-T041: Integration tests run after implementation
- T042-T045: Duplicate detection can be parallel with Gmail tests

**User Story 2** (P2 - Signature Removal):
- T046-T051: Tests can be written in parallel
- T052-T055: Pattern library sequential
- T056-T059: Implementation sequential
- T060-T061: Accuracy tests sequential

**User Story 3** (P2 - Quote Removal):
- T062-T066: Tests can be written in parallel
- T067-T069: Pattern library sequential
- T070-T073: Implementation sequential
- T074-T075: Accuracy tests sequential

**User Story 4** (P3 - Disclaimer Removal):
- T076-T079: Tests can be written in parallel
- T080-T082: Pattern library sequential
- T083-T086: Implementation sequential

### Parallel Opportunities

**High Parallelization Potential**:
- Phase 1 Setup: T002-T005 (dependency installation), T007-T008 (directory creation)
- Phase 2 Foundational: T011-T012, T014-T015, T019-T021 (independent models)
- Phase 4-6: US2, US3, US4 can be fully developed in parallel (different pattern categories)
- Phase 8 Polish: T096-T099 (documentation and config)

**Cannot Parallelize**:
- User Story 1 Gmail implementation (T029-T036) - sequential API integration
- Integration tests (Phase 7) - require all user stories complete
- Three-stage cleaning pipeline (T087) - requires US2-US4 complete

---

## Parallel Execution Examples

### Example 1: Phase 1 Setup (Parallel Dependency Installation)

```bash
# Launch installation tasks in parallel:
Task T002: Install Gmail API dependencies
Task T003: Install Cloud Pub/Sub dependencies
Task T004: Install Pydantic dependencies
Task T005: Install testing dependencies

# All can run simultaneously
```

### Example 2: Phase 2 Foundational (Parallel Model Creation)

```bash
# Launch model creation tasks in parallel:
Task T011: Create EmailAttachment model
Task T012: Create EmailMetadata model
Task T014: Create CleaningStatus enum
Task T015: Create RemovedContent model

# All independent Pydantic models
```

### Example 3: Phases 4-6 (Parallel User Stories)

```bash
# After Foundational phase complete, launch all cleaning user stories in parallel:
Team Member A: Implements User Story 2 (Signature Removal) - T046-T061
Team Member B: Implements User Story 3 (Quote Removal) - T062-T075
Team Member C: Implements User Story 4 (Disclaimer Removal) - T076-T086

# All three can proceed independently
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~30 minutes)
2. Complete Phase 2: Foundational (~1 hour)
3. Complete Phase 3: User Story 1 (~8 hours)
4. **STOP and VALIDATE**: Gmail API receiver works, emails stored as raw JSON
5. **SUCCESS**: Email ingestion pipeline established (MVP delivered!)

**MVP Value**: Even without cleaning, having emails ingested and stored provides immediate value for manual review and establishes the foundation for all downstream processing.

### Incremental Delivery

1. **Foundation** (Phase 1-2): Setup + Models → Data structures ready
2. **MVP** (Phase 3): User Story 1 → Email reception working (immediate value!)
3. **Enhanced Cleaning** (Phase 4-6): User Stories 2-4 → Signature, quote, disclaimer removal (parallel development)
4. **Integration** (Phase 7): End-to-end pipeline → Full workflow validated
5. **Production Ready** (Phase 8): Polish → Deployment ready

### Stopping Points

You can stop after any user story and still have delivered value:

- **After US1**: Email ingestion works, raw emails stored (MVP)
- **After US2**: Email ingestion + signature removal (most impactful cleaning)
- **After US3**: Email ingestion + signature + quote removal (high accuracy)
- **After US4**: Complete cleaning pipeline (full feature)

---

## Notes

- **TDD Required**: Tests are mandatory per constitution Principle III - all tests written before implementation
- **Gmail API Focus**: This task list prioritizes Gmail API implementation (T029-T036) with placeholders for IMAP (T037) and webhooks (T038)
- **[P] Markers**: Used for independent tasks within a phase (different files, no dependencies)
- **[Story] Labels**: [US1], [US2], [US3], [US4] map to user stories from spec.md
- **Test-First**: All unit tests (T022-T028, T046-T051, T062-T066, T076-T079) written before implementation
- **Accuracy Tests**: SC-002 and SC-003 require 95% accuracy - validated in T060, T074
- **Performance Target**: SC-006 requires 12 sec/email average - validated in T095
- **Duplicate Detection**: FR-011 handled in T042-T045 (message ID tracking)
- **Error Handling**: FR-010 exponential backoff implemented in T034
- **Three-Stage Cleaning**: Plan.md specifies disclaimers → quotes → signatures order (T087)

---

## Task Count Summary

- **Phase 1 (Setup)**: 10 tasks
- **Phase 2 (Foundational)**: 11 tasks
- **Phase 3 (US1 - Email Reception)**: 24 tasks (includes 7 test tasks, 2 placeholder tasks)
- **Phase 4 (US2 - Signature Removal)**: 16 tasks (includes 6 test tasks)
- **Phase 5 (US3 - Quote Removal)**: 14 tasks (includes 5 test tasks)
- **Phase 6 (US4 - Disclaimer Removal)**: 11 tasks (includes 4 test tasks)
- **Phase 7 (Integration)**: 9 tasks (includes 4 integration test tasks)
- **Phase 8 (Polish)**: 10 tasks

**Total**: 105 tasks

**Test Tasks**: 26 tasks (25% of total - TDD approach)
**Implementation Tasks**: 79 tasks

**Estimated Time**:
- MVP (US1 only): 1-1.5 days (Setup + Foundational + US1)
- MVP + Signature Removal (US1 + US2): 2 days
- Full Feature (US1-US4 + Integration): 3-4 days (per implementation-roadmap.md)

**Parallelizable Tasks**: 35 tasks marked [P] (33% can run in parallel)

**Independent Test Criteria**:
- US1: Send emails, verify raw JSON files created, check duplicate detection
- US2: Run normalizer on signature test set, verify 95% removal accuracy
- US3: Run normalizer on quote test set, verify 95% removal accuracy
- US4: Run normalizer on disclaimer test set, verify removal while preserving content
