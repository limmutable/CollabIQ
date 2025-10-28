<!--
============================================================================
SYNC IMPACT REPORT - Constitution Update
============================================================================
Version Change: Initial → 1.0.0
Modified Principles: None (initial creation)
Added Sections:
  - Core Principles (5 principles: Specification-First, Incremental Delivery, Test-Driven Development, Independent User Stories, Simplicity & Justification)
  - Development Workflow
  - Quality Standards
  - Governance
Removed Sections: None
Templates Status:
  ✅ plan-template.md - Aligned (Constitution Check section present)
  ✅ spec-template.md - Aligned (User stories with priorities, independent testing)
  ✅ tasks-template.md - Aligned (User story phases, parallel execution)
  ✅ Command files - Reviewed (no agent-specific conflicts found)
Follow-up TODOs: None
============================================================================
-->

# CollabIQ Constitution

## Core Principles

### I. Specification-First Development

Every feature MUST begin with a complete specification before any implementation work begins.

**Rules**:
- No code may be written until a feature specification (`spec.md`) exists and is approved
- Specifications MUST include user scenarios with acceptance criteria
- Specifications MUST include functional requirements (FR-XXX format)
- Specifications MUST define success criteria (SC-XXX format)
- All requirements MUST be technology-agnostic at the specification stage

**Rationale**: Clear specifications prevent scope creep, ensure stakeholder alignment, and enable accurate estimation. Writing specifications forces critical thinking about user needs before technical decisions constrain the solution space.

### II. Incremental Delivery via Independent User Stories

Features MUST be decomposed into independently deliverable user stories, each representing a complete slice of value.

**Rules**:
- User stories MUST be prioritized (P1, P2, P3, etc.)
- Each user story MUST be independently testable and demonstrable
- User story 1 (P1) MUST constitute a viable MVP (Minimum Viable Product)
- Implementation MUST proceed in priority order unless explicit parallel work is approved
- Each story completion MUST result in a deployable increment

**Rationale**: Independent user stories enable early feedback, reduce risk by delivering value incrementally, and allow for course correction without sunk costs. If only P1 is implemented, the project still delivers meaningful value.

### III. Test-Driven Development (TDD) - MANDATORY

All features requiring tests MUST follow strict test-first discipline.

**Rules**:
- Tests MUST be written before implementation code
- Tests MUST fail initially (red phase)
- Implementation proceeds only after failing tests exist (green phase)
- Refactoring occurs only after tests pass (refactor phase)
- Contract tests MUST verify API/interface boundaries
- Integration tests MUST verify user journey completeness
- Unit tests supplement where appropriate but are not mandatory

**Rationale**: Test-first ensures testability by design, serves as executable specifications, and prevents false confidence from tests written after the fact. Failing tests first proves they actually test something.

**Note**: Tests are OPTIONAL unless explicitly requested in feature specifications. When tests are required, TDD is NON-NEGOTIABLE.

### IV. Design Artifact Completeness

Implementation MUST NOT begin until all required design artifacts exist and are validated.

**Rules**:
- Planning phase (`/speckit.plan`) MUST produce:
  - `plan.md` with constitution check, technical context, and structure
  - `research.md` with technical investigation results
  - `data-model.md` with entity definitions and relationships
  - `quickstart.md` with step-by-step usage instructions
  - `contracts/` with API/interface specifications
- Task generation (`/speckit.tasks`) MUST occur after planning artifacts are complete
- Implementation (`/speckit.implement`) MUST NOT begin until `tasks.md` exists
- Constitution checks in `plan.md` MUST pass or have documented justifications

**Rationale**: Complete design artifacts prevent mid-implementation surprises, enable accurate task breakdown, and ensure all team members share a common understanding before costly coding begins.

### V. Simplicity & Justification

All complexity MUST be justified explicitly; simpler alternatives MUST be considered and rejected with documented reasoning.

**Rules**:
- Default to the simplest solution that meets requirements
- Patterns, abstractions, and frameworks MUST justify their existence
- Constitution violations MUST be documented in the "Complexity Tracking" section of `plan.md`
- Each violation MUST state: what is violated, why it's needed, and why simpler alternatives were rejected
- YAGNI principle applies: build only what is specified, not what might be needed

**Rationale**: Complexity is a liability. Every abstraction, pattern, or framework carries maintenance cost. Forcing explicit justification prevents cargo-cult engineering and premature optimization.

## Development Workflow

### Feature Lifecycle

1. **Specification** (`/speckit.specify`): Create `spec.md` with user stories, requirements, and success criteria
2. **Clarification** (`/speckit.clarify`): Identify and resolve underspecified areas (max 5 targeted questions)
3. **Planning** (`/speckit.plan`): Generate design artifacts (`plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)
4. **Task Generation** (`/speckit.tasks`): Create dependency-ordered `tasks.md` organized by user story
5. **Analysis** (`/speckit.analyze`): Cross-artifact consistency and quality validation (non-destructive)
6. **Implementation** (`/speckit.implement`): Execute tasks in priority order, verify with checklist (`/speckit.checklist`)

### Mandatory Gates

- **Gate 1**: Specification approved → Planning may begin
- **Gate 2**: Constitution check passes → Implementation may begin
- **Gate 3**: All P1 tasks complete → MVP deliverable
- **Gate 4**: All user story checkpoints pass → Feature complete

### Branch Strategy

- Feature branches named: `###-feature-name` (e.g., `001-user-authentication`)
- Branches created from main
- Merge to main only after all acceptance criteria pass

## Quality Standards

### Documentation Requirements

- Every feature MUST have `spec.md` and `plan.md`
- Every feature MUST have `quickstart.md` with step-by-step usage instructions
- API contracts MUST be documented in `contracts/` directory
- All design decisions MUST be traceable to requirements

### Code Quality

- Code MUST pass linting and formatting checks before commit
- Pre-commit hooks MUST enforce code quality standards
- All public APIs MUST have clear contracts
- Error messages MUST be actionable

### Testing Requirements (when tests are requested)

- Contract tests MUST exist for all API boundaries
- Integration tests MUST exist for all user journeys
- Tests MUST be written before implementation (TDD)
- All tests MUST pass before feature is considered complete

### Review Requirements

- All design artifacts MUST be reviewed before implementation begins
- Constitution checks MUST be validated by reviewer
- Complexity justifications MUST be challenged and validated
- User story independence MUST be verified

## Governance

### Constitution Authority

This constitution supersedes all other development practices, guidelines, and preferences. Any conflict between this constitution and other documents MUST be resolved in favor of the constitution.

### Amendment Process

1. **Proposal**: Document proposed change with rationale
2. **Impact Analysis**: Identify affected templates, processes, and in-flight features
3. **Approval**: Obtain stakeholder sign-off
4. **Migration**: Update all dependent templates and documentation
5. **Version Update**: Increment version per semantic versioning rules
6. **Communication**: Notify all team members

### Versioning Policy

Constitution version follows semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Backward-incompatible governance changes (principle removal, redefinition)
- **MINOR**: New principles, sections, or material expansions
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Verification

- All pull requests MUST include constitution compliance verification
- The `/speckit.analyze` command performs automated consistency checks
- Reviewers MUST validate constitution adherence
- Constitution violations MUST be documented in "Complexity Tracking" section with justification

### Enforcement

- Features not following this constitution MUST NOT be approved
- Unjustified complexity MUST be rejected
- Test-first discipline MUST be enforced when tests are required
- Specification-first workflow MUST be mandatory

**Version**: 1.0.0 | **Ratified**: 2025-10-28 | **Last Amended**: 2025-10-28
