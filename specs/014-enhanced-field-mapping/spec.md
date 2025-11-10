# Feature Specification: Enhanced Notion Field Mapping

**Feature Branch**: `014-enhanced-field-mapping`
**Created**: 2025-11-10
**Status**: Draft
**Input**: User description: "Enhanced Notion Field Mapping - Add fuzzy company matching and person matching to populate relation fields (스타트업명, 협력기관) and people field (담당자) in Notion database"

## Problem Statement

Currently, the CollabIQ system successfully extracts three critical fields from collaboration emails using LLM:
- **담당자 (Person in Charge)**: Name of the person handling the collaboration
- **스타트업명 (Startup Name)**: Name of the startup company involved
- **협력기관 (Partner Organization)**: Name of the partner organization

However, these fields are **not being populated** in the Notion database because:

1. **Relation Field Constraint**: 스타트업명 and 협력기관 are relation fields that link to the Companies database. They require exact `page_id` values, not just text names. The Notion API rejects writes if the company name doesn't exactly match an existing entry.

2. **People Field Constraint**: 담당자 is a people (multi-select) field that requires Notion user UUIDs, not plain text names.

3. **Name Variation Issue**: LLM-extracted names often have spelling variations:
   - Parenthetical info: "웨이크(산스)" vs "웨이크"
   - Character alternatives: "스마트푸드네트워크" vs "스마트푸드네트웍스" (워크 vs 웍)
   - Abbreviations: "SSG" vs "에스에스지" or "신세계"
   - Spacing differences: "스타트업 A" vs "스타트업A"

Without proper field mapping, these three critical fields remain empty, severely limiting the database's utility for querying, filtering, and reporting.

## User Scenarios & Testing

### User Story 1 - Company Name Fuzzy Matching (Priority: P1)

When the LLM extracts a company name that doesn't exactly match an existing entry in the Companies database, the system should intelligently find the best match using fuzzy string matching algorithms.

**Why this priority**: This is the highest priority because company relations are the most critical fields for the database. Without populated company fields, users cannot:
- Query collaborations by company
- Generate company-specific reports
- Track collaboration history with specific companies
- Use Notion's relation field features

**Independent Test**: Can be fully tested by running fuzzy matching on a set of test company names (e.g., "웨이크(산스)" → "웨이크") and validating the match accuracy meets the 90% threshold. Delivers immediate value by enabling company field population.

**Acceptance Scenarios**:

1. **Given** a company name "웨이크(산스)" is extracted from an email, **When** the system searches the Companies database containing ["웨이크", "산스앤컴퍼니"], **Then** the system returns the page_id for "웨이크" with a similarity score ≥0.85

2. **Given** a company name "SSG" is extracted, **When** the system searches the Companies database containing ["에스에스지", "신세계그룹"], **Then** the system returns the best matching entry with confidence score

3. **Given** multiple potential matches exist with similar scores, **When** the highest similarity score is still ≥0.85, **Then** the system selects the highest scoring match

4. **Given** a company name is extracted, **When** no Companies database entry has a similarity score ≥0.85, **Then** the system creates a new entry in the Companies database with the extracted name

---

### User Story 2 - Auto-Create Missing Companies (Priority: P1)

When the LLM extracts a company name that has no fuzzy match in the Companies database (all similarity scores < 0.85), the system should automatically create a new company entry to enable the relation field to be populated.

**Why this priority**: Equal priority with fuzzy matching because both are essential for company field population. Auto-creation ensures the system handles genuinely new companies without manual intervention.

**Independent Test**: Can be tested by providing company names that definitely don't exist in the database (e.g., "완전히새로운회사123") and verifying: (1) new entry is created, (2) returned page_id is valid, (3) relation field is populated successfully. Delivers value by handling the full spectrum of company scenarios.

**Acceptance Scenarios**:

1. **Given** a company name "새로운스타트업" is extracted, **When** all Companies database entries have similarity scores < 0.85, **Then** the system creates a new entry titled "새로운스타트업" in the Companies database

2. **Given** a new company entry is created, **When** the system retrieves the page_id, **Then** the page_id is valid and can be used for the relation field

3. **Given** a new company is created for 스타트업명, **When** the system writes to the CollabIQ database, **Then** the relation field is successfully populated with the new company's page_id

4. **Given** the same new company appears in multiple emails, **When** the system processes subsequent emails, **Then** the system reuses the existing entry (now matches exactly) instead of creating duplicates

---

### User Story 3 - Person Name Matching (Priority: P2)

When the LLM extracts a person's name (담당자), the system should match it to a Notion workspace user and populate the people field with the user's UUID.

**Why this priority**: Lower priority than company matching because:
- Person field is less critical for querying/reporting (companies are the primary filter)
- Korean names have higher ambiguity (common family names)
- Acceptable to leave empty if no confident match found

However, still important for user accountability and collaboration tracking.

**Independent Test**: Can be tested by creating a test Notion workspace with known users, extracting test names (e.g., "김철수"), and validating: (1) correct user UUID is returned, (2) people field is populated, (3) no false positives occur. Delivers value by enabling person-based queries and accountability.

**Acceptance Scenarios**:

1. **Given** a person name "김철수" is extracted, **When** the Notion workspace contains a user named "김철수 (Cheolsu Kim)", **Then** the system returns that user's UUID with similarity score 1.00

2. **Given** a person name "이영희" is extracted, **When** multiple users have the same family name "이", **Then** the system uses the full name for matching and selects the best match

3. **Given** a person name is extracted, **When** no Notion user has a similarity score ≥0.70, **Then** the system logs a warning and leaves the 담당자 field empty

4. **Given** a person name matches multiple users with similar scores, **When** the top score is < 0.90, **Then** the system logs the ambiguity for manual review

---

### User Story 4 - CLI Testing Commands (Priority: P3)

Administrators need CLI commands to test company and person matching without running the full pipeline, enabling quick validation and troubleshooting.

**Why this priority**: Nice-to-have for development and debugging. The matching logic can be tested via automated tests. CLI commands provide convenience but aren't essential for MVP functionality.

**Independent Test**: Can be tested by running CLI commands with known test inputs and verifying output format, accuracy, and helpful error messages. Delivers value for admin troubleshooting and manual verification.

**Acceptance Scenarios**:

1. **Given** an administrator runs `collabiq notion match-company "웨이크(산스)"`, **When** the command executes, **Then** the system displays the best match, similarity score, and page_id

2. **Given** an administrator runs `collabiq notion match-person "김철수"`, **When** the command executes, **Then** the system displays matched Notion user(s), UUIDs, and similarity scores

3. **Given** an administrator runs `collabiq notion list-users`, **When** the command executes, **Then** the system displays all Notion workspace users with their UUIDs

4. **Given** an administrator adds `--dry-run` flag, **When** testing company creation, **Then** the system simulates the creation without actually writing to Notion

---

### Edge Cases

- **What happens when a company name has special characters or emojis?**
  System should preserve the exact extracted name, use normalized versions for similarity matching, and handle Unicode properly.

- **What happens when the Companies database is empty?**
  All extractions should trigger auto-creation (similarity < 0.85 by default), building the database from scratch.

- **What happens when a person's name is ambiguous (e.g., "김" only)?**
  System should require minimum threshold (0.70) and log low-confidence matches. May leave field empty if too ambiguous.

- **What happens when Notion API rate limits are hit during company creation?**
  System should use existing retry logic with exponential backoff, handle rate limits gracefully, and ensure no data loss.

- **What happens when a company name is extracted in English but database has Korean entries?**
  System should apply similarity matching across language boundaries (e.g., "Samsung" vs "삼성"). May need language-specific normalization.

- **What happens when the LLM extracts multiple company names in a single field?**
  System should handle multi-company scenarios (e.g., "A와 B의 협력") by splitting or selecting the primary company. Document behavior in requirements.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement fuzzy string matching using Jaro-Winkler or similar algorithm with configurable similarity threshold (default: 0.85)

- **FR-002**: System MUST search the entire Companies database for fuzzy matches when an extracted company name doesn't exactly match any entry

- **FR-003**: System MUST return the page_id of the best matching company when similarity score ≥0.85

- **FR-004**: System MUST create a new entry in the Companies database when no existing entry has a similarity score ≥0.85

- **FR-005**: System MUST populate 스타트업명 (Startup Name) relation field with the matched or newly created company's page_id

- **FR-006**: System MUST populate 협력기관 (Partner Org) relation field with the matched or newly created company's page_id

- **FR-007**: System MUST list all Notion workspace users via Notion API to enable person matching

- **FR-008**: System MUST implement fuzzy matching for person names with Korean name handling (family name + given name variations)

- **FR-009**: System MUST return the user UUID(s) for matched persons when similarity score ≥0.70

- **FR-010**: System MUST populate 담당자 (Person in Charge) people field with matched user UUID(s)

- **FR-011**: System MUST leave 담당자 field empty when no Notion user has a similarity score ≥0.70

- **FR-012**: System MUST log low-confidence matches (0.70-0.85) with match details for manual review

- **FR-013**: System MUST preserve backward compatibility with existing field mapping logic for other fields

- **FR-014**: System MUST handle duplicate company prevention by checking if extracted name now matches existing entries after previous auto-creation

- **FR-015**: System MUST provide CLI command `collabiq notion match-company <name>` to test company matching

- **FR-016**: System MUST provide CLI command `collabiq notion match-person <name>` to test person matching

- **FR-017**: System MUST provide CLI command `collabiq notion list-users` to list all workspace users

- **FR-018**: CLI commands MUST support `--dry-run` flag to test matching without creating Notion entries

- **FR-019**: System MUST handle Korean text encoding properly (UTF-8) throughout matching and creation process

- **FR-020**: System MUST add confidence scores to match results and include them in logs for audit trails

### Key Entities

- **FuzzyCompanyMatcher**: Service responsible for searching Companies database, computing similarity scores, and returning page_id or triggering creation. Key attributes: similarity threshold (0.85), normalization rules, matching algorithm.

- **PersonMatcher**: Service responsible for listing Notion users, computing similarity scores for person names, and returning user UUIDs. Key attributes: person threshold (0.70), Korean name handling, ambiguity detection.

- **CompanyMatch**: Result object containing matched company page_id, similarity score, match confidence level, and whether a new entry was created.

- **PersonMatch**: Result object containing matched user UUID(s), similarity score, match confidence level, and ambiguity indicators.

- **FieldMapper Enhancement**: Integration point that uses FuzzyCompanyMatcher and PersonMatcher to populate relation and people fields before Notion write operation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least 90% of extracted company names are successfully matched to Companies database entries (exact matches + fuzzy matches with score ≥0.85) across test dataset of 20+ emails

- **SC-002**: At least 85% of extracted person names are successfully matched to Notion users (similarity ≥0.70) across test dataset of 20+ emails

- **SC-003**: All auto-created companies are properly formatted with correct title property and are linkable as relation field values

- **SC-004**: All low-confidence matches (0.70-0.85 for persons, 0.85-0.90 for companies) are logged with sufficient detail for manual review (match pair, similarity score, context)

- **SC-005**: Zero false positives in company matching (no incorrect company linked) validated through manual review of 20+ test cases

- **SC-006**: All three fields (담당자, 스타트업명, 협력기관) are populated in at least 90% of test emails (where values were extracted by LLM)

- **SC-007**: Fuzzy matching completes within 2 seconds per email even when Companies database contains 1000+ entries

- **SC-008**: CLI commands return results within 1 second and provide helpful error messages for invalid inputs

## Assumptions

- **Assumption 1**: The Companies database already contains a representative set of common companies that the organization collaborates with. If starting from scratch, the auto-creation feature will build the database over time.

- **Assumption 2**: Notion workspace users are properly configured with their full names (Korean and/or English). Users without proper names may not match successfully.

- **Assumption 3**: LLM extraction quality for company and person names is sufficient (≥85% accuracy) as established in previous phases. This feature focuses on mapping, not extraction improvement.

- **Assumption 4**: Similarity threshold of 0.85 for companies is appropriate for Korean company names. This may need tuning based on real-world testing.

- **Assumption 5**: Person name matching threshold of 0.70 is sufficiently conservative to avoid false positives given the higher ambiguity of Korean names.

- **Assumption 6**: The Notion API supports listing workspace users and provides sufficient name information for matching. (Verified in Notion API documentation)

- **Assumption 7**: Auto-creating company entries in the Companies database is acceptable business logic. Organizations may prefer manual review for new companies, which can be added as a configuration option later.

## Dependencies

- **Phase 2a (Notion Read)**: Required for querying Companies database and listing Notion users
- **Phase 2d (Notion Write)**: Required for creating new company entries and populating relation/people fields
- **Phase 3a (Admin CLI)**: Required for implementing CLI testing commands
- **Existing FieldMapper**: Will be enhanced to integrate fuzzy matching logic

## Constraints

- **Notion API Rate Limits**: Must respect Notion API rate limits when searching Companies database and creating new entries. Use existing retry logic from Phase 010.

- **Notion API 2025-09-03**: Must use `data_sources.query()` method for database queries as established in previous phases.

- **Unicode Handling**: Must properly handle Korean text (UTF-8) throughout matching, logging, and creation operations.

- **Performance**: Fuzzy matching should complete within 2 seconds even for large Companies databases (1000+ entries). May need optimization if performance degrades.

- **Backward Compatibility**: Must not break existing field mapping for other fields. All changes should be additive.

## Out of Scope

- **Multi-language Company Matching**: Matching across languages (e.g., "Samsung" vs "삼성") is NOT included in this phase. Future enhancement if needed.

- **Machine Learning-Based Matching**: This phase uses deterministic fuzzy string matching algorithms (Jaro-Winkler). ML-based approaches are out of scope.

- **Manual Review Queue**: Low-confidence matches are logged but not presented in a UI for manual review. Future enhancement for Phase 4+ if needed.

- **Company Merge/Deduplication**: If multiple company entries exist for the same company, this feature won't detect or merge them. Out of scope.

- **Historical Data Backfill**: This feature only applies to newly processed emails. Re-processing historical emails with empty company fields is out of scope.

- **Person Role/Title Extraction**: Only person names are matched. Extracting roles or titles (e.g., "김철수 대표님") is out of scope for this phase.
