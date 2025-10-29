# Implementation Plan: Project Structure Standards & File Naming Convention

**Branch**: `002-structure-standards` | **Date**: 2025-10-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-structure-standards/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature establishes comprehensive file naming conventions in the constitution and performs structural cleanup of the CollabIQ project. The work progresses through three phases: (1) documenting naming standards for all file categories with format specifications and examples, (2) auditing the current project structure to identify deviations with severity ratings, and (3) applying cleanup recommendations to resolve Critical and High severity issues while preserving Git history and functionality.

## Technical Context

**Language/Version**: Python 3.12 (established in project)
**Primary Dependencies**: Git (for file operations and history preservation), markdown (for documentation)
**Storage**: File system (constitution.md, audit reports, project files)
**Testing**: pytest (existing project standard, used to verify no functionality breaks)
**Target Platform**: macOS (developer machines), cross-platform compatibility for file naming
**Project Type**: Single project (Python package with SpecKit framework)
**Performance Goals**: Developer can locate any file type in under 30 seconds using documented structure
**Constraints**: Must not break existing functionality, must preserve Git history using `git mv`, must not modify other Git branches
**Scale/Scope**: Small project (7 source modules, ~10 documentation files, 6 test fixtures, 1 completed feature branch)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

- **Status**: PASS
- **Evidence**: Complete specification exists at [spec.md](spec.md) with user scenarios, functional requirements, and success criteria
- **Validation**: All requirements are technology-agnostic, no code has been written yet

### II. Incremental Delivery via Independent User Stories ✅

- **Status**: PASS
- **Evidence**:
  - P1 (Establish File Naming Standards): Independently testable by reviewing constitution.md, delivers immediate reference guide value
  - P2 (Audit Current Project Structure): Independently testable by reviewing audit document, delivers visibility into technical debt
  - P3 (Apply Cleanup Recommendations): Independently testable by verifying conformance, delivers consistent codebase
- **MVP**: P1 alone constitutes viable MVP - documentation of naming standards provides immediate value without requiring audit or cleanup
- **Validation**: Each user story can be developed, tested, and deployed independently

### III. Test-Driven Development (TDD) ⚠️

- **Status**: N/A (Tests Optional for This Feature)
- **Rationale**: This feature is primarily documentation and manual file operations (updating constitution.md, performing audit, renaming files)
- **Validation Approach**: Manual verification via:
  - P1: Review constitution.md completeness and clarity
  - P2: Review audit report for severity ratings and recommendations
  - P3: Verify existing pytest tests still pass after renames (FR-010, SC-005)
- **Note**: While TDD is not applicable for documentation work, the feature does include verification that existing tests continue to pass after cleanup operations

### IV. Design Artifact Completeness ✅

- **Status**: COMPLETE (Planning Phase)
- **Required Artifacts**:
  - ✅ `spec.md` - Complete
  - ✅ `plan.md` - This file (complete)
  - ✅ `research.md` - Complete (Phase 0)
  - ✅ `data-model.md` - Complete (Phase 1)
  - ✅ `quickstart.md` - Complete (Phase 1)
  - ✅ `contracts/` - N/A (no API endpoints for this feature)
  - ⏳ `tasks.md` - Ready for generation via `/speckit.tasks` command
- **Gate Status**: ✅ PASS - All planning artifacts complete

### V. Simplicity & Justification ✅

- **Status**: PASS
- **Validation**: This feature follows the simplest approach:
  - Manual documentation in constitution.md (no automation framework)
  - Manual audit using existing file system tools (no custom tooling)
  - Manual cleanup using `git mv` (standard Git command, no scripts)
  - No new dependencies or frameworks introduced
- **Complexity**: None added - feature uses existing project tools and processes

### Constitution Compliance Summary

**Overall Status**: ✅ PASS - May proceed to Phase 0 Research

All applicable principles are satisfied:
- Specification-first workflow followed ✅
- User stories are independent and prioritized ✅
- TDD N/A for documentation work (manual verification sufficient) ⚠️
- Design artifacts in progress (will complete in planning phase) 🔄
- No complexity added (simplest possible approach) ✅

**No violations requiring justification in Complexity Tracking section.**

## Project Structure

### Documentation (this feature)

```text
specs/002-structure-standards/
├── spec.md              # Feature specification (created by /speckit.specify)
├── plan.md              # This file (created by /speckit.plan)
├── research.md          # Phase 0 research findings (created by /speckit.plan)
├── data-model.md        # Phase 1 entity definitions (created by /speckit.plan)
├── quickstart.md        # Phase 1 step-by-step guide (created by /speckit.plan)
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Spec quality validation (created by /speckit.specify)
└── tasks.md             # Phase 2 implementation tasks (NOT YET CREATED - use /speckit.tasks)

Note: contracts/ directory NOT needed for this feature (no API endpoints or interfaces)
```

### Source Code (repository root)

**Current Structure**:

```text
/Users/jlim/Projects/CollabIQ/
├── .specify/                      # SpecKit framework (not modified by this feature)
│   ├── memory/
│   │   └── constitution.md        # PRIMARY TARGET: Add "File Naming Standards" section
│   ├── scripts/
│   └── templates/
├── config/                        # Configuration modules
│   ├── __init__.py
│   └── settings.py
├── docs/                          # Documentation files
│   ├── ARCHITECTURE.md            # AUDIT: Check naming consistency
│   ├── API_CONTRACTS.md
│   ├── EMAIL_INFRASTRUCTURE.md
│   ├── FEASIBILITY_TESTING.md
│   ├── FOUNDATION_WORK_REPORT.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── NOTION_API_VALIDATION.md
│   ├── NOTION_SCHEMA_ANALYSIS.md
│   └── quickstart.md              # AUDIT: Check against major doc naming
├── specs/                         # Feature specifications (SpecKit standard)
│   ├── 001-feasibility-architecture/  # Not modified (different branch)
│   └── 002-structure-standards/       # This feature
├── src/                           # Source code modules
│   ├── collabiq/                  # AUDIT: Check module naming
│   ├── email_receiver/
│   ├── llm_adapters/
│   ├── llm_provider/
│   ├── notion_integrator/
│   ├── reporting/
│   └── verification_queue/
├── tests/                         # Test files
│   ├── contract/                  # AUDIT: Check test organization
│   ├── integration/
│   ├── unit/
│   └── fixtures/
│       └── sample_emails/         # AUDIT: Check fixture naming
├── Makefile                       # Ecosystem standard (not renamed)
├── pyproject.toml                 # Ecosystem standard (not renamed)
├── README.md                      # Ecosystem standard (not renamed)
└── uv.lock                        # Ecosystem standard (not renamed)
```

**Structure Decision**: Single project structure (Python package). This feature:
- Adds "File Naming Standards" section to `.specify/memory/constitution.md`
- Creates audit report documenting current structure deviations
- Performs cleanup on files within `002-structure-standards` branch only
- Does NOT modify SpecKit framework structure or ecosystem configuration files
- Focuses on establishing standards for: specs/, docs/, src/, tests/, config/ directories

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - Constitution Check passed all applicable principles. No complexity tracking required.
