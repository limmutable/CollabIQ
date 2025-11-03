# Feature Specification: Notion Write Operations

**Feature Branch**: `009-notion-write`
**Created**: 2025-11-03
**Status**: Draft
**Input**: User description: "Phase 2d - Notion Write Operations (Branch: `009-notion-write`)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Write Extracted Email Data to Notion Database (Priority: P1)

After an email has been processed through the full pipeline (entity extraction → company matching → classification → summarization), the system automatically creates a new entry in the CollabIQ Notion database with all extracted and classified information.

**Why this priority**: This is the core deliverable of Phase 2d and completes the end-to-end automation pipeline. Without this capability, all extracted data remains isolated in JSON files with no centralized visibility or management.

**Independent Test**: Can be fully tested by processing a single email through the pipeline and verifying that a corresponding Notion database entry is created with all fields correctly populated. Delivers immediate value by making collaboration data visible in Notion.

**Acceptance Scenarios**:

1. **Given** an email has been successfully processed with entity extraction, company matching, and classification complete, **When** the write operation is triggered, **Then** a new entry is created in the CollabIQ Notion database with all fields populated from the extracted data.

2. **Given** extracted data includes matched company IDs for startup and partner organization, **When** the entry is created, **Then** the "스타트업명" and "협업기관" relation fields are correctly linked to the corresponding company records in the Companies database.

3. **Given** the startup name is "브레이크앤컴퍼니" and partner org is "신세계푸드", **When** the entry is created, **Then** the "협력주체" field is auto-generated as "브레이크앤컴퍼니-신세계푸드".

4. **Given** classification data includes type ([A]PortCoXSSG), intensity (협력), and summary, **When** the entry is created, **Then** all Phase 2c classification fields ("협업형태", "협업강도", "요약") are correctly populated.

5. **Given** the extracted date is "2025-10-28T00:00:00", **When** the entry is created, **Then** the Notion date field is correctly formatted and stored.

---

### User Story 2 - Handle Duplicate Detection (Priority: P2)

When processing an email that has already been written to Notion (based on email_id or collaboration identifier), the system detects the duplicate and either skips the write operation or updates the existing entry based on configuration.

**Why this priority**: Prevents duplicate entries in the database when emails are reprocessed (e.g., during testing, after errors, or when re-running the pipeline). Essential for data integrity but secondary to the basic write functionality.

**Independent Test**: Can be tested by processing the same email twice and verifying that only one Notion entry exists, or that the second processing updates the first entry. Delivers value by maintaining clean data without manual deduplication.

**Acceptance Scenarios**:

1. **Given** an entry for email_id "msg_001" already exists in Notion, **When** the same email is processed again, **Then** the system detects the duplicate and skips the write operation (or updates the existing entry based on configuration).

2. **Given** an entry with the same "협력주체" (startup-partner combination) and date already exists, **When** a new email with matching criteria is processed, **Then** the system flags this as a potential duplicate for manual review.

3. **Given** duplicate detection is configured to "skip", **When** a duplicate is detected, **Then** the system logs the skip action and continues processing without creating a new entry.

4. **Given** duplicate detection is configured to "update", **When** a duplicate is detected, **Then** the system updates the existing entry with new classification data or confidence scores if they differ.

---

### User Story 3 - Map Field Types Correctly (Priority: P2)

Different Notion field types (text, select, multi-select, relation, date, number) require specific formatting. The system correctly maps extracted data to the appropriate Notion field format based on the database schema.

**Why this priority**: Notion API has strict type requirements - sending incorrectly formatted data results in API errors. This ensures robustness but is secondary to basic write functionality since it's a technical requirement rather than a user-facing feature.

**Independent Test**: Can be tested by creating test entries with all field types and verifying that each field is correctly formatted and accepted by the Notion API. Delivers value by preventing write failures due to type mismatches.

**Acceptance Scenarios**:

1. **Given** the "협업형태" field is a Notion select property, **When** the collaboration type is "[A]PortCoXSSG", **Then** the system sends the value in the correct select format `{"select": {"name": "[A]PortCoXSSG"}}`.

2. **Given** the "협업강도" field is a Notion select property, **When** the intensity is "협력", **Then** the system sends the value in the correct select format.

3. **Given** the "스타트업명" field is a Notion relation property, **When** the matched company ID is "abc123-def456", **Then** the system sends the relation in the correct format `{"relation": [{"id": "abc123-def456"}]}`.

4. **Given** the "날짜" field is a Notion date property, **When** the extracted date is "2025-10-28T00:00:00", **Then** the system sends the date in ISO 8601 format `{"date": {"start": "2025-10-28"}}`.

5. **Given** the "요약" field is a Notion rich text property, **When** the summary contains Korean text, **Then** the system sends the text in the correct rich text format `{"rich_text": [{"text": {"content": "..."}}]}`.

---

### Edge Cases

- **What happens when a required Notion field is missing from the extracted data?**
  - System should use reasonable defaults or mark the entry for manual review
  - Log the missing field for monitoring and debugging

- **What happens when the Notion API returns an error (rate limit, schema change, invalid field)?**
  - System should capture the error with full context (email_id, extracted data, API response)
  - Save failed writes to a dead letter queue (file-based for Phase 2d, to be enhanced in Phase 2e)
  - Continue processing other emails without crashing

- **What happens when a relation field references a non-existent company ID?**
  - System should omit the relation field rather than failing the entire write
  - Log a warning with the missing company ID
  - Mark the entry for manual review

- **What happens when the "협력주체" auto-generated field exceeds Notion's character limit?**
  - Truncate intelligently (preserve key information, add ellipsis)
  - Log the truncation for monitoring

- **What happens when extracted data contains special characters or emojis?**
  - Notion's rich text format supports Unicode, so preserve all characters
  - Test with Korean text, emojis, and special punctuation

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a method to create a new entry in the CollabIQ Notion database with all extracted and classified data fields.

- **FR-002**: System MUST map `ExtractedEntitiesWithClassification` Pydantic model fields to corresponding Notion database properties based on dynamic schema discovery (from Phase 2a).

- **FR-003**: System MUST correctly format field values according to Notion field types:
  - Text fields: `{"rich_text": [{"text": {"content": "value"}}]}`
  - Select fields: `{"select": {"name": "value"}}`
  - Date fields: `{"date": {"start": "YYYY-MM-DD"}}`
  - Relation fields: `{"relation": [{"id": "page_id"}]}`
  - Number fields: `{"number": value}`

- **FR-004**: System MUST link matched company IDs to Notion relation fields:
  - "스타트업명" relation field linked to startup company ID (from Phase 2b matching)
  - "협업기관" relation field linked to partner company ID (from Phase 2b matching)

- **FR-005**: System MUST auto-generate the "협력주체" field by concatenating startup name and partner organization name with a hyphen separator (e.g., "브레이크앤컴퍼니-신세계푸드").

- **FR-006**: System MUST populate all Phase 2c classification fields:
  - "협업형태" (collaboration_type, e.g., "[A]PortCoXSSG")
  - "협업강도" (collaboration_intensity, e.g., "협력")
  - "요약" (collaboration_summary, 3-5 sentences)
  - Confidence scores (stored in appropriate fields)

- **FR-007**: System MUST detect duplicate entries before creating new records:
  - Primary duplicate key: email_id (unique identifier from Gmail)
  - Secondary duplicate key: combination of startup name + partner org + date (fuzzy match within 7 days)

- **FR-008**: System MUST handle duplicate detection with configurable behavior:
  - "skip": Log duplicate and skip write operation
  - "update": Update existing entry with new classification data
  - Default behavior: "skip" (configurable via environment variable `DUPLICATE_BEHAVIOR`)
  - Rationale: Default to "skip" for production safety (prevents overwriting manual edits), but allow "update" via configuration for development or specific use cases where progressive enrichment is desired

- **FR-009**: System MUST capture and log write failures with full context:
  - Email ID
  - Extracted data (sanitized if contains sensitive info)
  - Notion API error response
  - Timestamp of failure

- **FR-010**: System MUST save failed writes to a dead letter queue for retry or manual review:
  - File-based DLQ: `data/dlq/notion_write_failures_{timestamp}.json`
  - Include all context needed to retry the write operation
  - Format: one JSON object per failed write

- **FR-011**: System MUST validate Notion API response and confirm successful entry creation:
  - Check response status code (200 or 201 for success)
  - Extract and return the created page ID
  - Verify that all fields were accepted (no partial writes)

- **FR-012**: System MUST handle missing or null fields gracefully:
  - Omit fields with null values rather than sending empty strings
  - Use reasonable defaults for required fields (e.g., empty summary if generation failed)
  - Mark entries with missing critical fields for manual review

- **FR-013**: System MUST preserve Korean text encoding throughout the write process:
  - UTF-8 encoding for all text fields
  - No character corruption or mojibake
  - Support for Korean punctuation and spacing

### Key Entities

- **Notion CollabIQ Database Entry**: Represents a single collaboration record in Notion with the following conceptual fields (actual field names in Korean):
  - Startup name (relation to Companies database)
  - Partner organization (relation to Companies database)
  - Collaboration subject (auto-generated: "startup-partner")
  - Person in charge (text)
  - Collaboration details (text)
  - Date of collaboration (date)
  - Collaboration type (select: [A], [B], [C], [D])
  - Collaboration intensity (select: 이해, 협력, 투자, 인수)
  - Summary (rich text, 3-5 sentences)
  - Type confidence score (number, 0.0-1.0)
  - Intensity confidence score (number, 0.0-1.0)
  - Manual review flag (checkbox, based on confidence threshold)
  - Email ID (text, unique identifier)
  - Classification timestamp (date)

- **Extracted Entities with Classification**: The input data model containing all fields from Phase 1b (entity extraction), Phase 2b (company matching), and Phase 2c (classification and summarization):
  - Basic entities: person_in_charge, startup_name, partner_org, details, date
  - Company matching: matched_startup_id, matched_partner_id, classification fields
  - Classification: collaboration_type, type_confidence, collaboration_intensity, intensity_confidence, intensity_reasoning
  - Summarization: collaboration_summary, summary_word_count, key_entities_preserved
  - Metadata: email_id, confidence scores, classification_timestamp

- **Dead Letter Queue Record**: A failed write operation stored for retry or manual intervention:
  - Email ID (reference to original email)
  - Extracted data (full ExtractedEntitiesWithClassification object)
  - Error details (API response, error message, stack trace)
  - Failure timestamp
  - Retry count (for Phase 2e)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully creates Notion entries for ≥95% of valid extractions on first write attempt (no API errors, no schema mismatches).

- **SC-002**: All relation fields (스타트업명, 협업기관) are correctly linked to Companies database for 100% of entries where matched company IDs are available.

- **SC-003**: Auto-generated "협력주체" field matches the format "startup-partner" for 100% of entries.

- **SC-004**: Duplicate detection prevents >99% of duplicate entries when the same email is processed multiple times (based on email_id matching).

- **SC-005**: System completes write operation (including duplicate check, field mapping, API call, and response validation) in ≤2 seconds per email.

- **SC-006**: Failed writes are captured in the dead letter queue with 100% of required context (email_id, extracted data, error details) for retry or manual review.

- **SC-007**: Korean text (담당자, 스타트업명, 협업기관, 요약) is preserved without encoding errors for 100% of entries.

## Assumptions

1. **Notion Database Schema**: The CollabIQ Notion database schema has been finalized and includes all required fields for Phase 2c classification data. Schema changes will be rare after Phase 2d launch.

2. **Company IDs Availability**: Phase 2b company matching provides company IDs for both startup and partner organization in >85% of cases. When IDs are missing, the entry can still be created with text names only.

3. **Notion API Stability**: Notion API is generally reliable with >99% uptime. Basic retry logic (3 attempts with exponential backoff) will be implemented in Phase 2d, with comprehensive error handling deferred to Phase 2e.

4. **Single CollabIQ Database**: There is one primary CollabIQ database for all collaboration entries. Multi-database writes are not required in Phase 2d.

5. **Synchronous Writes**: Write operations are synchronous (block until complete) rather than queued. Async queue-based writes will be introduced in Phase 3a.

6. **File-Based DLQ**: Dead letter queue is file-based (JSON files) for Phase 2d. More robust DLQ with retry scheduling will be implemented in Phase 2e.

7. **Duplicate Detection Strategy**: Primary duplicate detection is based on email_id (exact match). Secondary fuzzy matching based on startup+partner+date is optional and may have false positives.

8. **UTF-8 Encoding**: All systems (Python, Notion API, JSON serialization) use UTF-8 encoding by default, ensuring Korean text is preserved.

## Dependencies

- **Phase 2a**: Notion Read Operations - provides schema discovery and database access capabilities
- **Phase 2b**: Company Matching - provides matched company IDs for relation field linking
- **Phase 2c**: Classification & Summarization - provides classification data and summaries to be written
- **notion-client**: Official Notion Python SDK for API interactions
- **Environment Configuration**: Notion API token and CollabIQ database ID must be configured

## Out of Scope

- **Comprehensive Retry Logic**: Basic retry (3 attempts) is included, but exponential backoff, rate limit handling, and DLQ processing are deferred to Phase 2e.
- **Update Existing Entries**: Phase 2d focuses on creating new entries. Updating existing entries (e.g., when classification improves) may be added later if needed.
- **Bulk Write Operations**: Writing multiple emails in a single batch operation is out of scope. Each email is written individually.
- **Write Permissions Management**: Assumes the configured Notion integration has write permissions to the CollabIQ database. Permission troubleshooting is out of scope.
- **Rollback on Partial Failure**: If some fields are written but others fail, the entry remains in a partial state. Atomic writes or rollback are not implemented in Phase 2d.
- **Webhook Notifications**: Notion does not provide webhooks for write confirmations. Polling or external notification systems are out of scope.
