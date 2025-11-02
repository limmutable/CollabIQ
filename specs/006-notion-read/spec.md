# Feature Specification: Notion Read Operations

**Feature Branch**: `006-notion-read`
**Created**: 2025-11-02
**Status**: Draft
**Input**: User description: "Phase 2a - Notion Read Operations: NotionIntegrator component (read-only operations), discover and fetch data from 'Companies' and 'CollabIQ' Notion databases including their full schema (fields, types, relationships), cache data locally, format for LLM prompt context"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Database Schema Discovery (Priority: P1)

As a system administrator, I want the system to automatically discover the structure of our Notion databases (Companies and CollabIQ) so that it understands what fields exist, their types, and how they relate to each other.

**Why this priority**: This is the foundational capability that enables all data retrieval. Without understanding the schema, the system cannot know what data to fetch or how databases are connected.

**Independent Test**: Can be fully tested by triggering schema discovery and verifying that the system correctly identifies all database properties, field types, and relational fields. Delivers value by creating a complete data model for subsequent operations.

**Acceptance Scenarios**:

1. **Given** the system has valid Notion API credentials, **When** schema discovery is triggered, **Then** the system retrieves all field definitions from the Companies database
2. **Given** the system has valid Notion API credentials, **When** schema discovery is triggered, **Then** the system retrieves all field definitions from the CollabIQ database
3. **Given** databases contain relational fields, **When** schema is analyzed, **Then** the system identifies all relationships between Companies and CollabIQ databases
4. **Given** schema discovery completes, **When** the results are examined, **Then** each field includes its name, type, and any relationship targets

---

### User Story 2 - Complete Data Retrieval with Relationships (Priority: P1)

As a system administrator, I want the system to retrieve all records from both databases including related data so that the LLM has complete context about companies and their relationships.

**Why this priority**: Core data retrieval is essential for the LLM to understand the full context. Without related data, the system would have incomplete information about companies.

**Independent Test**: Can be tested by fetching data and verifying that related fields are properly resolved (e.g., if a CollabIQ record references a Company, the company data is included). Delivers value by providing complete, enriched data to the LLM.

**Acceptance Scenarios**:

1. **Given** the schema is known, **When** data retrieval is triggered, **Then** the system fetches all records from the Companies database with pagination
2. **Given** the schema is known, **When** data retrieval is triggered, **Then** the system fetches all records from the CollabIQ database with pagination
3. **Given** a record has relational fields, **When** the record is fetched, **Then** the system resolves the relationships and includes referenced data
4. **Given** multiple levels of relationships exist, **When** data is fetched, **Then** the system follows relationships to a configurable depth (default: 1 level)

---

### User Story 3 - Local Data Caching (Priority: P2)

As a cost-conscious system operator, I want the system to cache database schemas and data locally with automatic refresh so that we minimize Notion API calls while keeping data reasonably current.

**Why this priority**: While essential for production efficiency and cost control, caching is secondary to the core capabilities of schema discovery and data retrieval. The system can function without caching, albeit less efficiently.

**Independent Test**: Can be tested independently by verifying cache file creation, TTL expiration, and refresh behavior. Delivers value by reducing API costs and improving system performance.

**Acceptance Scenarios**:

1. **Given** schema and data have been fetched, **When** the data is stored, **Then** local cache files are created with timestamps
2. **Given** cached data exists and is recent (within TTL), **When** the system needs data, **Then** it uses the cached version without calling the Notion API
3. **Given** cached data exists but is stale (beyond TTL), **When** the system needs data, **Then** it automatically fetches fresh data from Notion and updates the cache
4. **Given** the cache file does not exist, **When** the system needs data, **Then** it fetches from Notion and creates a new cache file

---

### User Story 4 - API Rate Limit Compliance (Priority: P2)

As a responsible API consumer, I want the system to respect Notion's rate limits (3 requests/second) so that our integration remains stable and doesn't get throttled or blocked.

**Why this priority**: Critical for production stability, but only becomes relevant when implementing the fetch mechanism. Can be tested independently of business logic.

**Independent Test**: Can be tested by simulating high-volume fetch scenarios and verifying that request timing never exceeds rate limits. Delivers value by ensuring reliable, uninterrupted service.

**Acceptance Scenarios**:

1. **Given** multiple API requests are queued, **When** the system makes requests to Notion, **Then** no more than 3 requests are made per second
2. **Given** the system encounters a rate limit error from Notion, **When** the error is detected, **Then** the system implements exponential backoff and retries
3. **Given** pagination requires multiple API calls, **When** fetching a large company list, **Then** requests are automatically throttled to stay within rate limits

---

### User Story 5 - LLM-Ready Data Formatting (Priority: P2)

As an LLM integration developer, I want the retrieved data formatted in a structure optimized for LLM consumption so that the LLM can easily reference company information when processing emails, identify company types, and determine collaboration classifications.

**Why this priority**: Essential for the downstream LLM workflow, but can be implemented after basic data retrieval works. The format can evolve based on LLM performance.

**Independent Test**: Can be tested by verifying the output format matches expected structure and contains all necessary fields in a readable format. Delivers value by making data immediately usable for LLM prompts.

**Acceptance Scenarios**:

1. **Given** data has been retrieved from both databases, **When** formatting is applied, **Then** the output includes all companies with their key attributes in a structured format
2. **Given** relational data exists, **When** formatting is applied, **Then** related records are nested or referenced clearly
3. **Given** the LLM needs to search for a company, **When** reviewing the formatted data, **Then** company names are easily scannable (e.g., as a list or key-value structure)
4. **Given** multiple data points exist per company, **When** formatted, **Then** the most relevant fields for email identification are prioritized
5. **Given** a company has the "Shinsegae affiliates?" checkbox checked, **When** formatted for LLM, **Then** the company is clearly marked as a Shinsegae affiliate
6. **Given** a company has the "Is Portfolio?" checkbox checked, **When** formatted for LLM, **Then** the company is clearly marked as a portfolio company
7. **Given** a company record is formatted, **When** examined by LLM, **Then** both classification fields (Shinsegae affiliate status and portfolio status) are immediately visible to support collaboration type determination (A: PortCo×SSG, B: Non-PortCo×SSG, C: PortCo×PortCo, D: Other)

---

### User Story 6 - Error Recovery and Resilience (Priority: P3)

As a system operator, I want the system to gracefully handle API failures and network issues so that temporary problems don't break the entire workflow.

**Why this priority**: Important for production reliability, but the system can function in ideal conditions without sophisticated error handling. Can be added incrementally.

**Independent Test**: Can be tested by simulating various failure scenarios (network timeout, invalid credentials, API errors) and verifying appropriate fallback behavior.

**Acceptance Scenarios**:

1. **Given** a Notion API call fails due to network timeout, **When** the error is detected, **Then** the system retries up to 3 times with exponential backoff
2. **Given** Notion API credentials are invalid, **When** authentication fails, **Then** the system logs a clear error message and uses the last successful cached data if available
3. **Given** a cache file exists but Notion API is unreachable, **When** the system needs data, **Then** it uses the cached data even if stale and logs a warning
4. **Given** both Notion API and cache are unavailable, **When** the system needs data, **Then** it returns an empty/minimal dataset and logs a critical error for operator attention

---

### Edge Cases

- What happens when a Notion database is empty (no records)?
- How does the system handle Unicode characters in field names and data values (Korean, Japanese, emoji)?
- What happens when Notion API returns partial data due to permission issues?
- How does the system handle very large databases (1000+ records) with many pages of results?
- What happens if the cache file is corrupted or unreadable?
- How does the system handle circular relationships (A references B, B references A)?
- What happens when Notion API is temporarily down during a scheduled refresh?
- How does the system handle records that are archived or deleted in Notion?
- What happens when a relational field references a page that no longer exists?
- How does the system handle databases with deeply nested relationships (3+ levels)?
- What happens when field types change in Notion (e.g., text becomes select)?
- How does the system handle databases with hundreds of fields?
- What happens when the "Shinsegae affiliates?" checkbox is unchecked, checked, or missing for a company record?
- What happens when the "Is Portfolio?" checkbox is unchecked, checked, or missing for a company record?
- How does the system handle companies that transition from startup to Shinsegae affiliate status (checkbox state changes)?
- How does the system handle companies that transition to/from portfolio status (checkbox state changes)?
- What happens when a company has both "Shinsegae affiliates?" and "Is Portfolio?" checked (valid scenario for Type A collaborations)?
- How does the system handle companies with neither checkbox checked (Type D: Other)?

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Access:**
- **FR-001**: System MUST connect to Notion API using credentials stored in Infisical or .env file
- **FR-002**: System MUST access both the "Companies" and "CollabIQ" Notion databases using the integration token

**Schema Discovery:**
- **FR-003**: System MUST retrieve the complete schema (all properties/fields) from the Companies database
- **FR-004**: System MUST retrieve the complete schema (all properties/fields) from the CollabIQ database
- **FR-005**: System MUST identify field types for each property (text, number, select, multi-select, relation, date, etc.)
- **FR-006**: System MUST detect and document relational fields including their target database
- **FR-007**: System MUST handle schema changes gracefully (detect when cached schema is outdated)

**Data Retrieval:**
- **FR-008**: System MUST fetch all records from the Companies database with full field data
- **FR-009**: System MUST fetch all records from the CollabIQ database with full field data
- **FR-010**: System MUST handle paginated API responses and fetch all pages automatically
- **FR-011**: System MUST resolve relational fields by fetching referenced records
- **FR-012**: System MUST support configurable relationship depth (default: 1 level to avoid infinite loops)
- **FR-013**: System MUST detect and prevent infinite loops from circular relationships

**Rate Limiting & Performance:**
- **FR-014**: System MUST respect Notion API rate limits of 3 requests per second maximum
- **FR-015**: System MUST implement request queuing to stay within rate limits
- **FR-016**: System MUST handle rate limit errors with exponential backoff

**Caching:**
- **FR-017**: System MUST cache database schemas locally in a structured format
- **FR-018**: System MUST cache fetched data locally in a structured format
- **FR-019**: System MUST store cache timestamps to track data freshness
- **FR-020**: System MUST refresh cached data automatically when cache age exceeds configurable TTL (default: 6 hours)
- **FR-021**: System MUST support separate TTLs for schema cache (longer) vs data cache (shorter)

**Data Formatting:**
- **FR-022**: System MUST format retrieved data into a structure suitable for LLM prompt context
- **FR-023**: System MUST preserve all relevant metadata (database source, field names, values)
- **FR-024**: System MUST handle Unicode text (Korean, Japanese, emoji) correctly in all operations
- **FR-025**: System MUST provide data in a format that makes company identification straightforward

**Error Handling & Resilience:**
- **FR-026**: System MUST implement retry logic with exponential backoff for transient API failures
- **FR-027**: System MUST log all Notion API operations (success, failure, retry attempts) with appropriate detail
- **FR-028**: System MUST fall back to cached data when Notion API is unreachable
- **FR-029**: System MUST handle missing or deleted referenced records gracefully
- **FR-030**: System MUST validate cache integrity and rebuild if corrupted

**Operations & Debugging:**
- **FR-031**: System MUST provide a manual cache refresh mechanism for testing and troubleshooting
- **FR-032**: System MUST provide visibility into schema structure (e.g., via logging or CLI command)
- **FR-033**: System MUST report clear error messages when Notion permissions are insufficient

**Business Rules:**
- **FR-034**: System MUST preserve the "Shinsegae affiliates?" checkbox field from the Companies database to distinguish Shinsegae affiliated companies from other companies
- **FR-035**: System MUST preserve the "Is Portfolio?" checkbox field from the Companies database to distinguish portfolio companies from other companies
- **FR-036**: System MUST ensure each company record clearly indicates both affiliation status (Shinsegae affiliate: yes/no) and portfolio status (Portfolio company: yes/no)
- **FR-037**: System MUST format company data to support the four collaboration type classifications:
  - Type A: Portfolio Company × Shinsegae Affiliate
  - Type B: Non-Portfolio Company × Shinsegae Affiliate
  - Type C: Portfolio Company × Portfolio Company
  - Type D: Other (any combination not covered by A, B, or C)
- **FR-038**: System MUST make both classification fields (Shinsegae affiliates?, Is Portfolio?) easily accessible in the formatted output for LLM consumption

### Collaboration Classification Logic

The system supports downstream LLM-based classification of email collaborations into four types based on company characteristics:

**Company Classification Fields** (from Companies database):
- **"Shinsegae affiliates?"** (checkbox): Indicates if company is a Shinsegae affiliated company
- **"Is Portfolio?"** (checkbox): Indicates if company is a portfolio company

**Collaboration Types** (determined by LLM in later phase based on company pairs identified in emails):
- **Type A - PortCo × SSG**: One company is a Portfolio Company (Is Portfolio? = checked), the other is a Shinsegae Affiliate (Shinsegae affiliates? = checked)
- **Type B - Non-PortCo × SSG**: One company is NOT a Portfolio Company (Is Portfolio? = unchecked), the other is a Shinsegae Affiliate (Shinsegae affiliates? = checked)
- **Type C - PortCo × PortCo**: Both companies are Portfolio Companies (both have Is Portfolio? = checked)
- **Type D - Other**: Any collaboration not fitting Types A, B, or C

**Note**: This phase (Notion Read Operations) is responsible only for **retrieving and formatting** the classification fields. The actual collaboration type determination (A/B/C/D) will be performed by the LLM in a subsequent phase when analyzing email content.

### Key Entities

- **NotionDatabase**: Represents a Notion database (Companies or CollabIQ), including database ID, name, and complete schema definition with all property types
- **NotionProperty**: Represents a field/property in a Notion database, including property name, type (text, select, relation, etc.), and relationship target if applicable
- **NotionRecord**: Represents a single record/page from a Notion database, including all field values, resolved relationships, and company classification fields (Shinsegae affiliates?, Is Portfolio?)
- **DatabaseSchema**: Represents the complete structure of a database, including all properties, their types, and inter-database relationships
- **RelationshipGraph**: Represents the connections between databases, tracking which fields link to which databases to support relationship resolution
- **DataCache**: Represents cached schema and data, including content, timestamp, TTL, and validity status
- **NotionIntegrator**: Component that manages all read-only Notion operations, including API authentication, schema discovery, data retrieval, pagination, rate limiting, relationship resolution, and caching logic

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully discovers complete schema from both databases (all fields with types) within 10 seconds
- **SC-002**: System retrieves all records from both databases within 60 seconds for databases containing up to 500 records
- **SC-003**: System correctly resolves at least 95% of relational fields (verified by spot-checking referenced data)
- **SC-004**: System maintains Notion API rate limits with zero violations (measured over a 24-hour period)
- **SC-005**: Cache hit rate exceeds 80% during normal operations (meaning 80% of data requests are served from cache rather than API calls)
- **SC-006**: System recovers from transient Notion API failures within 3 retry attempts in 95% of cases
- **SC-007**: Data provided to LLM includes 100% of active records from both databases (verified against Notion UI)
- **SC-008**: Cache refresh operations complete successfully on schedule without manual intervention for 7 consecutive days
- **SC-009**: System handles databases with up to 1000 records and 50 fields each without performance degradation or timeout errors
- **SC-010**: System correctly handles Unicode text (Korean, Japanese, emoji) in 100% of field names and values
- **SC-011**: System correctly preserves both "Shinsegae affiliates?" and "Is Portfolio?" checkbox states for 100% of company records
- **SC-012**: Formatted output enables LLM to determine collaboration type (A/B/C/D) for any pair of companies with 100% of required data present
