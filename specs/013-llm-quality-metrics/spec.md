# Feature Specification: LLM Quality Metrics & Tracking

**Feature Branch**: `013-llm-quality-metrics`
**Created**: 2025-11-09
**Status**: Draft
**Input**: User description: "Phase 3c - LLM Quality Metrics & Tracking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track Response Quality Metrics (Priority: P1)

System administrators need to monitor the quality of LLM responses when extracting structured data from emails and matching them to Notion database fields. The system tracks how accurately each LLM provider extracts the 5 key entities (person_in_charge, startup_name, partner_org, details, date) from email content and how well these extractions match to existing Notion database records. This enables data-driven decisions about provider selection and helps identify when model quality degrades.

**Why this priority**: This is the foundation for quality-based decision making. Without quality metrics on extraction accuracy and Notion field matching, we can only optimize for cost and speed, potentially sacrificing the accuracy of data written to Notion.

**Independent Test**: Can be fully tested by processing a set of emails through the system and verifying that quality metrics (per-field confidence scores for the 5 entities, field extraction completeness, Notion matching accuracy, validation failures) are correctly recorded and retrievable for each provider.

**Acceptance Scenarios**:

1. **Given** an LLM provider processes an email and extracts the 5 key entities (person, startup, partner, details, date), **When** the extraction completes, **Then** the system records per-field confidence scores (0.0-1.0), overall extraction confidence, field completeness percentage (extracted fields / total 5 fields), and extraction timestamp for that provider
2. **Given** multiple emails have been processed by a provider, **When** an administrator requests quality metrics, **Then** the system displays aggregate metrics including average per-field confidence, field completeness rate (% of extractions with all 5 fields populated), Notion matching success rate, and validation failure rate
3. **Given** a provider's extraction fails validation (e.g., missing required fields, invalid date format, low confidence scores), **When** the failure is recorded, **Then** the system increments the validation failure count, stores the failure reason (which field(s) failed and why), and associates it with the email being processed

---

### User Story 2 - Compare Provider Performance (Priority: P2)

System administrators need to compare quality metrics across multiple LLM providers to identify which provider performs best for specific extraction tasks. This enables informed provider selection and budget allocation.

**Why this priority**: Once we can track quality metrics, comparing them across providers enables optimization. This drives ROI by ensuring we use the most cost-effective provider that meets quality thresholds.

**Independent Test**: Can be tested by processing identical emails through multiple providers and verifying that comparative metrics (relative accuracy, consistency, quality-to-cost ratio) are accurately calculated and displayed.

**Acceptance Scenarios**:

1. **Given** the same email has been processed by multiple providers, **When** an administrator views comparative metrics, **Then** the system displays side-by-side quality scores, confidence levels, and field completeness for each provider
2. **Given** quality metrics and cost metrics exist for all providers, **When** an administrator requests a quality-to-cost analysis, **Then** the system calculates and displays the value score (quality per dollar) for each provider
3. **Given** one provider consistently has higher confidence scores, **When** the administrator views trending data, **Then** the system highlights the best-performing provider based on configurable quality criteria

---

### User Story 3 - Quality-Based Provider Selection (Priority: P3)

The system automatically routes extraction requests to providers based on quality metrics and business rules, ensuring high-accuracy extractions while managing costs. For example, use high-quality (expensive) providers only when confidence from cheaper providers falls below a threshold.

**Why this priority**: This automates the decision-making enabled by P1 and P2, maximizing operational efficiency. It's P3 because it requires the foundation of quality tracking and comparison.

**Independent Test**: Can be tested by configuring quality thresholds and verifying that the system correctly routes requests to appropriate providers based on historical quality metrics and current conditions.

**Acceptance Scenarios**:

1. **Given** quality thresholds are configured (e.g., minimum confidence 85%), **When** an extraction request arrives, **Then** the system selects a provider meeting the quality threshold with the lowest cost
2. **Given** the primary provider's recent quality metrics fall below threshold, **When** a new extraction request arrives, **Then** the system automatically routes to the next-best provider based on quality metrics
3. **Given** a provider shows consistently high quality for specific email types, **When** that email type is detected, **Then** the system preferentially routes to that provider regardless of cost

---

### Edge Cases

- What happens when a provider returns an extraction but with very low confidence scores (e.g., 0.2)? Should this be treated as a quality failure?
- How does the system handle extractions where some fields are high confidence and others are very low confidence? Should field-level quality metrics be tracked separately?
- What happens when quality metrics for all providers fall below acceptable thresholds simultaneously? Should the system alert administrators or fall back to best-effort extraction?
- How long should quality metrics be retained? Should older data be archived or aggregated to prevent unbounded storage growth?
- What happens if quality metrics diverge significantly between different types of content (e.g., a provider excels at meeting invites but struggles with contract extractions)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture quality metrics for each LLM extraction, including: per-field confidence scores for the 5 key entities (person_in_charge, startup_name, partner_org, details, date), overall extraction confidence (average of per-field scores), field completeness percentage (number of non-null fields / 5 total fields), Notion matching accuracy (if applicable), and validation failure indicators with specific failure reasons
- **FR-002**: System MUST store quality metrics with timestamps, provider identifier, and associated email/extraction identifier for traceability
- **FR-003**: System MUST calculate aggregate quality statistics per provider, including: average confidence score, field completeness rate (percentage of extractions with all required fields), validation failure rate, and quality trend over time (improving/degrading/stable)
- **FR-004**: System MUST enable comparison of quality metrics across providers, displaying relative performance rankings and statistical significance of differences
- **FR-005**: System MUST calculate quality-to-cost ratio (value score) by combining quality metrics with existing cost tracking data
- **FR-006**: System MUST support configurable quality thresholds for automated provider selection (e.g., minimum confidence 80%, maximum validation failure rate 5%)
- **FR-007**: System MUST record quality degradation events when provider metrics fall below threshold over a sliding time window
- **FR-008**: System MUST provide administrative interface to view quality metrics, trends, and comparative analysis
- **FR-009**: System MUST persist quality metrics to disk with atomic writes to ensure data integrity across application restarts
- **FR-010**: System MUST support reset/archival of quality metrics for testing and long-term data management

### Key Entities

- **Quality Metrics Record**: Represents quality measurements for a single email extraction attempt, including per-field confidence scores for the 5 key entities (person: 0.0-1.0, startup: 0.0-1.0, partner: 0.0-1.0, details: 0.0-1.0, date: 0.0-1.0), overall extraction confidence (average of the 5 scores), field completeness percentage (count of non-null fields / 5), Notion matching accuracy (if entity matching occurred), validation status (pass/fail), validation failure reasons with specific field-level details (e.g., "date field: invalid format"), extraction timestamp, provider identifier (gemini/claude/openai), and email/extraction reference ID
- **Provider Quality Summary**: Aggregate quality statistics for a provider, including average confidence score, standard deviation of confidence, field completeness rate, total extractions processed, validation success rate, quality trend indicator (improving/stable/degrading), and time period covered
- **Quality Threshold**: Configuration defining acceptable quality levels, including minimum average confidence, maximum validation failure rate, minimum field completeness percentage, evaluation time window (e.g., last 100 extractions), and affected email types (if type-specific)
- **Quality Comparison**: Cross-provider analysis, including provider rankings by quality metric, statistical significance of differences, quality-to-cost ratios, and recommendation for optimal provider selection

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can view quality metrics for any provider within 2 seconds of requesting them, with metrics accurate to the last completed extraction
- **SC-002**: System correctly identifies and records quality degradation when a provider's average confidence drops by more than 10 percentage points over 50 consecutive extractions
- **SC-003**: Quality-based provider selection improves overall extraction accuracy by at least 15% compared to cost-only selection, measured by validation failure rate reduction
- **SC-004**: Administrators can identify the best-performing provider for their use case within 5 minutes of reviewing comparative quality metrics
- **SC-005**: System maintains quality metric history for at least 10,000 extractions per provider without performance degradation (query response time remains under 2 seconds)
- **SC-006**: Quality metrics dashboard provides actionable insights that lead to measurable cost savings (e.g., identifying that a cheaper provider meets quality thresholds) or quality improvements (e.g., detecting provider degradation before it impacts business operations)

## Assumptions

- **A-001**: LLM providers return per-field confidence scores for the 5 key entities (person_in_charge, startup_name, partner_org, details, date) in the ConfidenceScores model (this is currently true for all existing adapters: gemini_adapter, claude_adapter, openai_adapter)
- **A-002**: Validation logic exists or will be implemented to determine if extractions meet quality standards (can leverage existing email content structure validation)
- **A-003**: Quality metrics will be stored using the existing file-based JSON persistence pattern (consistent with health_tracker.py and cost_tracker.py)
- **A-004**: Quality thresholds will be configured via existing configuration mechanisms (environment variables, config files, or CLI commands)
- **A-005**: Initial implementation will track quality at the extraction level; field-level quality tracking can be added in future iterations if needed
- **A-006**: Quality metrics retention period will default to unlimited (no automatic archival) unless storage becomes a concern, at which point aggregation/archival can be implemented
- **A-007**: Quality-based routing will integrate with the existing LLM orchestrator failover logic rather than replacing it entirely
