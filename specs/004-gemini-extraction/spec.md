# Feature Specification: Gemini Entity Extraction (MVP)

**Feature Branch**: `004-gemini-extraction`
**Created**: 2025-11-01
**Status**: Draft
**Input**: User description: "Phase 1b - Gemini Entity Extraction (MVP): Implement LLM-based entity extraction from Korean/English emails to extract key collaboration information (담당자, 스타트업명, 협업기관, 협업내용, 날짜)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Entities from Single Email (Priority: P1)

A team member receives a Korean email about a collaboration update and wants to extract structured information without manually parsing the text.

**Why this priority**: Core MVP functionality - delivers immediate value by automating the most time-consuming manual task (reading emails and extracting 5 key fields). This alone saves 3-5 minutes per email.

**Independent Test**: Can be fully tested by feeding a single cleaned email text to the extraction component and verifying all 5 entities are correctly identified with confidence scores above 85%.

**Acceptance Scenarios**:

1. **Given** a cleaned Korean email about a collaboration event, **When** the system extracts entities, **Then** it correctly identifies 담당자 (person in charge), 스타트업명 (startup name), 협업기관 (partner organization), 협업내용 (collaboration details), and 날짜 (date) with confidence scores
2. **Given** a cleaned English email about a collaboration event, **When** the system extracts entities, **Then** it correctly identifies all 5 entities in English with confidence scores
3. **Given** a mixed Korean-English email, **When** the system extracts entities, **Then** it correctly handles both languages and outputs entities in the appropriate language with confidence scores
4. **Given** an email with missing date information, **When** the system extracts entities, **Then** it returns null for the date field and lower confidence score for that field while successfully extracting other entities

---

### User Story 2 - Batch Process Multiple Emails (Priority: P2)

A team member wants to process a backlog of 20 collaboration emails from the past week and extract entities from all of them efficiently.

**Why this priority**: Enables processing historical emails and handling multiple updates at once. Adds significant value for catching up on backlogs but depends on Story 1 working correctly first.

**Independent Test**: Can be tested by providing 20 cleaned email texts and verifying the system processes all of them sequentially, returning a JSON file containing extracted entities for each email with processing metadata (success/failure, processing time).

**Acceptance Scenarios**:

1. **Given** 20 cleaned emails in a directory, **When** the batch processor runs, **Then** it processes all emails and outputs a single JSON file with an array of extracted entities, one per email
2. **Given** a batch containing 3 emails with extraction errors, **When** the batch processor runs, **Then** it continues processing remaining emails and marks failed ones with error details in the output
3. **Given** a batch of 20 emails, **When** processing completes, **Then** the system reports total processing time, success count, and failure count

---

### User Story 3 - Review Confidence Scores (Priority: P2)

A team member wants to review low-confidence extractions to verify accuracy before manually creating Notion entries.

**Why this priority**: Builds trust in the system and helps identify patterns in extraction errors. Critical for MVP adoption but doesn't block basic extraction functionality.

**Independent Test**: Can be tested by processing emails with deliberately ambiguous content (e.g., multiple dates, unclear partner names) and verifying the system correctly flags low-confidence fields (< 85%) in the JSON output.

**Acceptance Scenarios**:

1. **Given** an email with ambiguous partner organization name, **When** entities are extracted, **Then** the partner_org field has a confidence score below 85% and is flagged for manual review in the JSON output
2. **Given** an email with no clear date mentioned, **When** entities are extracted, **Then** the date field is null and confidence score is 0% or marked as "not found"
3. **Given** a batch of 20 emails, **When** processing completes, **Then** the JSON output includes a summary showing which emails need manual review (any field with confidence < 85%)

---

### Edge Cases

- What happens when an email contains multiple collaboration events (e.g., two different startups mentioned)?
- How does the system handle emails with forwarded content containing outdated information?
- What if the email is entirely in English but uses Korean names for companies/people?
- How does the system handle emails with only partial information (e.g., missing person in charge)?
- What happens when the date is mentioned in relative terms ("next Tuesday", "last week") instead of absolute dates?
- How does the system handle emails with HTML formatting, special characters, or emoji?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept cleaned email text (Korean, English, or mixed) as input and extract exactly 5 entities: 담당자 (person_in_charge), 스타트업명 (startup_name), 협업기관 (partner_org), 협업내용 (details), 날짜 (date)
- **FR-002**: System MUST return a confidence score (0.0-1.0) for each extracted entity indicating extraction certainty
- **FR-003**: System MUST output extracted entities in JSON format with fields: person_in_charge, startup_name, partner_org, details, date, confidence (object with per-field scores), email_id (for tracking)
- **FR-004**: System MUST handle emails where one or more entities are missing by returning null for missing fields and confidence score of 0.0
- **FR-005**: System MUST support batch processing of multiple emails and output a JSON array containing extraction results for each email
- **FR-006**: System MUST include error handling for Gemini API failures (rate limits, network errors, invalid responses) and mark failed extractions with error status in JSON output
- **FR-007**: System MUST preserve original text of the 협업내용 (details) field without summarization or modification (extraction only, not transformation)
- **FR-008**: System MUST handle date extraction in multiple formats: absolute dates (YYYY-MM-DD, MM/DD), relative dates ("next week", "yesterday"), and Korean date formats ("11월 1주")
- **FR-009**: System MUST provide a command-line interface for manual testing with a single email file as input
- **FR-010**: System MUST log all Gemini API requests and responses (without exposing API keys) for debugging and accuracy analysis
- **FR-011**: System MUST use an abstract LLMProvider interface to enable future swapping of Gemini with GPT-4 or Claude without changing business logic
- **FR-012**: System MUST implement Gemini-specific adapter (GeminiAdapter) that conforms to the LLMProvider interface

### Key Entities *(include if feature involves data)*

- **ExtractedEntities**: Represents the 5 key pieces of information extracted from a collaboration email
  - person_in_charge (담당자): The person responsible for the collaboration (string, nullable)
  - startup_name (스타트업명): Name of the startup involved (string, nullable)
  - partner_org (협업기관): Partner organization collaborating with the startup (string, nullable)
  - details (협업내용): Full description of the collaboration activity (string, nullable)
  - date (날짜): Date of the collaboration event (ISO 8601 date, nullable)
  - confidence: Object containing per-field confidence scores (float 0.0-1.0)
  - email_id: Unique identifier linking to the source email (string, required)
  - extracted_at: Timestamp when extraction occurred (ISO 8601 datetime, required)

- **LLMProvider**: Abstract interface defining the contract for any LLM service
  - extract_entities(email_text: str) -> ExtractedEntities: Core extraction method
  - Implementations: GeminiAdapter (Phase 1b), GPT4Adapter (future), ClaudeAdapter (future)

- **ExtractionBatch**: Represents a batch processing job
  - batch_id: Unique identifier for the batch (string, required)
  - emails: List of email texts to process (array of strings, required)
  - results: Array of ExtractedEntities for each email (array, populated after processing)
  - summary: Processing metadata (total_count, success_count, failure_count, processing_time_seconds)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System achieves ≥85% entity extraction accuracy on a test dataset of 20 Korean collaboration emails (manually verified ground truth)
- **SC-002**: System achieves ≥85% entity extraction accuracy on a test dataset of 10 English collaboration emails
- **SC-003**: Confidence scores are calibrated such that ≥90% of extractions with confidence ≥0.85 are verified as correct by manual review
- **SC-004**: System processes a single email and returns extracted entities within 5 seconds (excluding network latency for Gemini API)
- **SC-005**: System successfully handles batch processing of 20 emails without crashing or losing data
- **SC-006**: Team members can manually create Notion entries from JSON output in ≤2 minutes per entry (compared to 5-7 minutes reading raw emails) - 30-40% time reduction
- **SC-007**: System completes MVP implementation within 2 weeks from Phase 1b start date

## Assumptions

1. **Email Format**: Emails have already been cleaned (Phase 1a) - signatures, disclaimers, and quoted text removed
2. **Language Support**: Only Korean and English are required; other languages are out of scope for MVP
3. **Gemini API Access**: Valid Gemini API key is available and rate limits (60 requests/minute) are sufficient for MVP usage
4. **Date Parsing**: System will use industry-standard date parsing libraries for common formats; extremely ambiguous dates (e.g., "sometime soon") may return null
5. **Single Event per Email**: For MVP, each email describes one primary collaboration event (multiple events in one email are edge cases, handled in later phases)
6. **Manual Notion Entry**: MVP does not automate Notion database creation (Phase 2a-2e) - team manually copies JSON data
7. **No Fuzzy Matching**: MVP does not match extracted company names against existing Notion databases (Phase 2c) - exact text extraction only
8. **Error Recovery**: Gemini API failures are logged but not automatically retried (manual retry via CLI tool)

## Dependencies

- **Phase 1a (Email Reception)**: MUST be complete - provides cleaned email text as input
- **Gemini API**: Requires active Gemini 2.5 Flash API key and network connectivity
- **Python Environment**: Python 3.12+, UV package manager for dependency management
- **Configuration**: Gemini API key stored securely (via Infisical or .env file)

## Out of Scope (for MVP)

- Automatic Notion database creation (deferred to Phase 2a)
- Fuzzy matching of company names against Notion databases (deferred to Phase 2c)
- Company classification (startup vs partner org) (deferred to Phase 2b)
- Verification queue for ambiguous extractions (deferred to Phase 3)
- Activity reporting and dashboards (deferred to Phase 4)
- Multi-event extraction from single email (future enhancement)
- Support for languages beyond Korean/English (future enhancement)
