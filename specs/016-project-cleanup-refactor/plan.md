# Implementation Plan: Project Cleanup & Refactoring

**Branch**: `016-project-cleanup-refactor` | **Date**: 2025-11-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-project-cleanup-refactor/spec.md`

**Note**: This is a cleanup/refactoring phase, not a new feature implementation. This plan focuses on reorganization, consolidation, and polish rather than new functionality.

## Summary

Phase 016 performs comprehensive cleanup and reorganization of the CollabIQ codebase across three main areas:

1. **Documentation Consolidation (P1)**: Audit docs/ and specs/ directories to identify and consolidate duplicate documentation, remove outdated content, establish clear hierarchy, and create navigation index. Target: zero duplicates, <1 minute to find any doc.

2. **Test Suite Organization (P2)**: Reorganize tests/ directory with clear separation by type (unit/integration/e2e/performance/fuzz), remove redundant test cases, clean up test utilities in src/collabiq/test_utils/. Target: 20% test reduction while maintaining 98.9%+ pass rate.

3. **CLI Polish (P3)**: Implement minimal startup checks (<2 seconds), improve error messages, add interactive prompts for common admin tasks, enhance help text. Target: intuitive admin experience with clear feedback.

**Technical Approach**: Manual code review and reorganization guided by automated analysis (grep, find, test coverage tools). No new libraries or services. All changes are non-functional (maintaining existing behavior while improving organization).

## Technical Context

**Language/Version**: Python 3.12 (established in project)
**Primary Dependencies**: Existing dependencies only - no new dependencies required
**Storage**: File-based (documentation files, test files, CLI code)
**Testing**: pytest (existing test framework) - regression testing to ensure no functionality broken
**Target Platform**: macOS/Linux development environments (existing)
**Project Type**: Single project (established structure)
**Performance Goals**:
- Documentation: Find any doc in <1 minute
- Tests: 15% faster execution for unit/integration test suites
- CLI: <2 second cold start time
**Constraints**:
- No functional changes (regression testing enforces this)
- Maintain 98.9%+ test pass rate throughout cleanup
- No breaking changes to CLI command structure
**Scale/Scope**:
- ~100+ documentation files to audit
- ~735 tests to review and organize
- ~30+ CLI commands to polish

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Library-First ✅ **PASS** (N/A for cleanup phase)
**Evaluation**: This phase does not introduce new features or libraries. It reorganizes existing code and documentation. Library-first principle does not apply to refactoring/cleanup work.

### II. CLI Interface ✅ **PASS** (Preserved)
**Evaluation**: Existing CLI interfaces are being polished, not changed. CLI commands maintain their text I/O protocol and JSON support. No breaking changes to CLI interface.

### III. Test-First (NON-NEGOTIABLE) ✅ **PASS** (Regression focus)
**Evaluation**: This is a refactoring phase where tests already exist. The approach is:
1. Run baseline tests to establish current state (98.9% pass rate)
2. Perform cleanup/reorganization
3. Re-run all tests to verify no functionality broken
4. Regression testing serves as continuous validation
This follows TDD spirit: tests guide and validate refactoring.

### IV. Integration Testing ✅ **PASS** (Maintained)
**Evaluation**: Existing integration tests (E2E, API, Notion) are being reorganized, not removed. Integration test coverage is preserved while redundant tests are consolidated.

### V. Observability ✅ **PASS** (Enhanced)
**Evaluation**: CLI improvements include better error messages and status feedback, which enhances observability. Structured logging remains unchanged.

**Final Constitution Check**: ✅ **ALL GATES PASSED** - No violations, no complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/016-project-cleanup-refactor/
├── spec.md                      # Feature specification (completed)
├── plan.md                      # This file (/speckit.plan output)
├── research.md                  # Phase 0: Audit findings and consolidation strategy
├── data-model.md               # Phase 1: Documentation/test organization schema
├── quickstart.md               # Phase 1: Cleanup execution guide
├── contracts/                  # Phase 1: N/A (no API contracts for cleanup)
├── checklists/                 # Quality checklists
│   └── requirements.md         # Specification validation (completed)
└── tasks.md                    # Phase 2: Implementation tasks (/speckit.tasks - not yet created)
```

### Source Code (repository root)

**Current Structure** (no changes - cleanup only):

```text
docs/                           # Documentation to audit and consolidate
├── architecture/
├── testing/
├── validation/
└── setup/

specs/                          # Feature specifications (historical and current)
├── 001-feasibility-architecture/
├── 002-email-reception/
├── ...
└── 016-project-cleanup-refactor/  # This feature

tests/                          # Test suite to reorganize
├── unit/                       # Unit tests (to be organized)
├── integration/                # Integration tests (to be organized)
├── e2e/                        # End-to-end tests (validated)
├── performance/                # Performance tests (validated)
├── fuzz/                       # Fuzz tests (validated)
├── contract/                   # Contract tests
├── manual/                     # Manual test scripts
└── coverage_reports/           # Coverage report outputs

src/
├── collabiq/                   # Core application code
│   ├── cli/                    # CLI application (to be polished)
│   ├── test_utils/             # Test utilities (to be organized)
│   ├── date_parser/            # Date parsing library
│   ├── llm_benchmarking/       # LLM testing utilities
│   └── ...
├── llm_adapters/               # LLM provider adapters
├── notion_integrator/          # Notion API integration
├── content_normalizer/         # Email content cleaning
└── email_receiver/             # Gmail API integration

scripts/                        # Utility scripts
└── [various scripts for testing, benchmarking, admin tasks]
```

**Structure Decision**: This is a cleanup phase with no structural changes. The plan documents existing structure and identifies areas for consolidation within current directories. No new directories or services created.

## Complexity Tracking

**No violations** - Constitution check passed all gates. No complexity justification required.

This cleanup phase reduces complexity rather than adding it:
- Removes duplicate documentation (reduces cognitive load)
- Consolidates redundant tests (reduces maintenance burden)
- Improves CLI feedback (reduces debugging time)

---

**Next Steps**:
1. ✅ Specification complete and validated
2. ✅ Planning phase complete (this document)
3. 🔄 **Phase 0**: Research and audit (generate research.md)
4. ⏳ **Phase 1**: Design consolidation strategy (generate data-model.md, quickstart.md)
5. ⏳ **Phase 2**: Generate implementation tasks (run `/speckit.tasks`)

**Plan Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: Constitution check passed - Ready for Phase 0 research
