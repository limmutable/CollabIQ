# Feature Specification: Multi-LLM Provider Support

**Feature Branch**: `012-multi-llm`
**Created**: 2025-11-08
**Status**: Draft
**Input**: User description: "Multi-LLM Provider Support with orchestrator strategies for failover, consensus, and best-match selection"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Failover on Provider Failure (Priority: P1)

When the primary LLM provider experiences an outage or error, the system automatically switches to a backup provider to continue processing emails without manual intervention or data loss.

**Why this priority**: System reliability is critical for production use. Without automatic failover, a single provider outage would halt all email processing, causing business disruption and potential data loss. This provides immediate business continuity value.

**Independent Test**: Can be fully tested by configuring two providers (e.g., Gemini and Claude), sending test emails, simulating Gemini API failure, and verifying that emails continue to be processed successfully using Claude within 2 seconds.

**Acceptance Scenarios**:

1. **Given** the system is configured with Gemini as primary and Claude as secondary provider, **When** Gemini API returns an error for an email extraction request, **Then** the system automatically retries the same email with Claude and successfully extracts entities
2. **Given** the primary provider is unavailable, **When** 10 emails arrive for processing, **Then** all 10 emails are processed using the secondary provider without data loss
3. **Given** a provider failure occurs, **When** the system switches to backup provider, **Then** the failover completes in under 2 seconds
4. **Given** multiple consecutive failures on primary provider, **When** the failure threshold is reached, **Then** the system marks the provider as unhealthy and routes all traffic to secondary provider

---

### User Story 2 - Improved Accuracy via Multi-Provider Consensus (Priority: P2)

For critical or ambiguous emails, the system queries multiple LLM providers and combines their responses to improve extraction accuracy through consensus or voting mechanisms.

**Why this priority**: While failover ensures availability, consensus improves accuracy for difficult extraction cases. This is valuable but not essential for basic system operation, making it a logical second priority after reliability is established.

**Independent Test**: Can be fully tested by enabling consensus mode, processing a test set of 100 emails with known entity values, querying both Gemini and Claude, merging their results, and measuring that accuracy improves by at least 10% compared to single-provider extraction.

**Acceptance Scenarios**:

1. **Given** consensus mode is enabled, **When** an email is processed, **Then** the system queries at least 2 configured providers and merges their extraction results
2. **Given** two providers return different confidence scores for the same entity, **When** merging results, **Then** the system selects the extraction with higher confidence
3. **Given** two providers return conflicting entity values, **When** using voting strategy, **Then** the system selects the value agreed upon by the majority of providers
4. **Given** a test set of 100 emails with known correct entities, **When** consensus mode is used versus single-provider mode, **Then** extraction accuracy improves by at least 10%

---

### User Story 3 - Best-Match Selection Across Providers (Priority: P3)

The system queries multiple providers simultaneously and selects the extraction result with the highest overall confidence score, optimizing for quality over consensus.

**Why this priority**: This is an optimization strategy that builds on the multi-provider capability. It's useful but less critical than failover (reliability) and consensus (accuracy improvement), as it primarily optimizes provider selection rather than enabling new capabilities.

**Independent Test**: Can be fully tested by configuring best-match mode, sending test emails to 3 providers (Gemini, Claude, OpenAI), receiving different confidence scores from each, and verifying the system selects and uses the result with the highest aggregate confidence.

**Acceptance Scenarios**:

1. **Given** best-match mode is enabled with 3 providers, **When** an email is processed, **Then** the system queries all 3 providers in parallel
2. **Given** Provider A returns confidence 0.85, Provider B returns 0.92, Provider C returns 0.78, **When** selecting best match, **Then** the system uses Provider B's extraction result
3. **Given** multiple providers return results, **When** calculating overall confidence, **Then** the system averages confidence scores across all extracted entities (person, startup, partner, details, date)
4. **Given** one provider times out, **When** best-match selection occurs, **Then** the system evaluates only the providers that returned results within the timeout window

---

### User Story 4 - Provider Health Monitoring and Visibility (Priority: P3)

Administrators can view real-time health status of all configured LLM providers, including uptime, error rates, response times, and cost metrics through a status command.

**Why this priority**: Monitoring is essential for operations but can be implemented after the core multi-provider functionality works. It provides visibility but doesn't directly affect email processing capability.

**Independent Test**: Can be fully tested by configuring multiple providers, processing emails over time, triggering various failure scenarios, and running `collabiq status --detailed` to verify it displays accurate health metrics, error counts, average response times, and cost data for each provider.

**Acceptance Scenarios**:

1. **Given** the system has processed emails using multiple providers, **When** admin runs `collabiq status --detailed`, **Then** the output shows health status (healthy/unhealthy) for each configured provider
2. **Given** providers have different error rates and response times, **When** viewing status, **Then** the display shows success rate percentage, average response time, and total API calls for each provider
3. **Given** providers have processed emails with different token counts, **When** viewing cost metrics, **Then** the display shows total tokens used and estimated cost per provider
4. **Given** a provider has been marked unhealthy due to consecutive failures, **When** viewing status, **Then** the display indicates the provider is in unhealthy state with failure count and last error time

---

### Edge Cases

- What happens when all configured providers are simultaneously unavailable or failing?
- How does the system handle providers that return valid responses but with very low confidence scores across all entities?
- What happens when consensus mode is enabled but providers return completely contradictory entity values with equal confidence?
- How does the system handle partial failures where a provider returns results for some entities but fails for others?
- What happens when a provider takes longer than the configured timeout but eventually returns a valid response?
- How does cost tracking handle providers with different pricing models (per-token vs per-request)?
- What happens when a provider returns unexpected response formats that don't match the expected schema?
- How does the system handle provider API version changes or deprecations?

## Requirements *(mandatory)*

### Functional Requirements

#### Provider Abstraction and Implementation

- **FR-001**: System MUST support multiple LLM provider implementations using a common interface that all providers implement
- **FR-002**: System MUST support at least three provider implementations: Gemini, Claude (Anthropic), and OpenAI
- **FR-003**: Each provider implementation MUST accept email text as input and return structured entity extraction results with confidence scores
- **FR-004**: Each provider implementation MUST handle authentication, rate limiting, and error responses specific to its API
- **FR-005**: System MUST allow administrators to configure which providers are enabled and their priority order

#### Orchestration Strategies

- **FR-006**: System MUST support a failover strategy that tries the primary provider first and falls back to secondary providers on error
- **FR-007**: System MUST support a consensus strategy that queries multiple providers and merges their results
- **FR-008**: System MUST support a best-match strategy that queries multiple providers and selects the result with highest confidence
- **FR-009**: System MUST allow configuration of which orchestration strategy to use (failover as default)
- **FR-010**: Failover strategy MUST complete provider switching in under 2 seconds when primary provider fails
- **FR-011**: Consensus strategy MUST merge results by selecting higher-confidence values for each entity when providers disagree
- **FR-012**: Best-match strategy MUST calculate overall confidence by averaging scores across all entities (person, startup, partner, details, date)

#### Health Monitoring and Circuit Breaking

- **FR-013**: System MUST track success/failure rates for each provider over time
- **FR-014**: System MUST mark a provider as unhealthy after a configurable threshold of consecutive failures (default: 5 failures)
- **FR-015**: System MUST automatically stop sending requests to unhealthy providers until they recover
- **FR-016**: System MUST periodically test unhealthy providers with low-priority requests to detect recovery
- **FR-017**: System MUST record response time for each provider request
- **FR-018**: System MUST track the timestamp of the last successful and last failed request per provider

#### Configuration

- **FR-019**: System MUST allow configuration of provider priority order for failover strategy
- **FR-020**: System MUST allow configuration of request timeout per provider (default: 30 seconds)
- **FR-021**: System MUST allow configuration of retry settings (max attempts, backoff strategy) per provider
- **FR-022**: System MUST allow configuration of the orchestration strategy to use (failover/consensus/best-match)
- **FR-023**: System MUST allow configuration of the unhealthy threshold (number of consecutive failures before marking provider unhealthy)

#### Cost Tracking

- **FR-024**: System MUST track token usage (input tokens and output tokens) for each provider request
- **FR-025**: System MUST track total API call count per provider
- **FR-026**: System MUST calculate and store cost per email based on provider-specific pricing
- **FR-027**: System MUST aggregate cost metrics across all emails processed

#### Admin Visibility

- **FR-028**: System MUST provide a `collabiq status --detailed` command that displays provider health information
- **FR-029**: Status output MUST show for each provider: name, health status, success rate, average response time, total API calls
- **FR-030**: Status output MUST show for each provider: total tokens used, estimated total cost, last success timestamp, last failure timestamp
- **FR-031**: Status output MUST indicate which orchestration strategy is currently active
- **FR-032**: Status output MUST show which provider is currently marked as primary

### Key Entities

- **LLM Provider**: Represents a specific LLM service (Gemini, Claude, OpenAI) with attributes including provider name, API endpoint, authentication credentials, current health status, priority level
- **Provider Health Metrics**: Contains health tracking data for a provider including success count, failure count, consecutive failures, average response time, last success timestamp, last failure timestamp, current health status (healthy/unhealthy)
- **Extraction Result**: The output from a provider containing extracted entities (person, startup, partner, details, date), confidence scores for each entity, provider name that generated the result, timestamp, token usage (input/output)
- **Orchestration Strategy**: Defines how multiple providers are coordinated including strategy type (failover/consensus/best-match), list of enabled providers, provider priority order, configuration parameters (timeouts, thresholds)
- **Cost Metrics**: Tracks financial cost per provider including total API calls, total input tokens, total output tokens, cost per token (provider-specific), total estimated cost, cost per email average

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System continues processing all incoming emails when the primary LLM provider is unavailable
- **SC-002**: Provider failover completes in under 2 seconds when switching from failed primary to secondary provider
- **SC-003**: Consensus mode improves entity extraction accuracy by at least 10% when measured against a test set of 100 emails with known correct entities
- **SC-004**: Administrators can view comprehensive provider health status by running a single status command
- **SC-005**: System tracks and reports cost per email processed, broken down by provider
- **SC-006**: All three provider implementations (Gemini, Claude, OpenAI) pass the same contract test suite, ensuring consistent behavior
- **SC-007**: When a provider is marked unhealthy after 5 consecutive failures, the system automatically routes all traffic to healthy providers
- **SC-008**: Best-match strategy selects the highest-confidence result across all queried providers within the configured timeout window
