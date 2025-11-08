# Implementation Plan: Admin CLI Enhancement

**Branch**: `011-admin-cli` | **Date**: 2025-11-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-admin-cli/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements a unified `collabiq` CLI command to centralize all admin operations for the CollabIQ system. The CLI provides seven command groups (email, notion, test, errors, status, llm, config) with color-coded output, progress indicators, JSON mode, and graceful interrupt handling. This replaces fragmented script invocations with a single, intuitive entry point that improves admin productivity by 50% and enables safe automation through structured output.

## Technical Context

**Language/Version**: Python 3.12+ (established in project, using UV package manager)
**Primary Dependencies**: typer (CLI framework), rich (terminal formatting), click (command parsing support)
**Storage**: File-based (existing data/ directory structure for emails, extractions, test results, error records)
**Testing**: pytest (established in project), contract tests for CLI interface, integration tests for command workflows
**Target Platform**: Linux/macOS servers and containers (interactive terminal + non-interactive CI/CD)
**Project Type**: Single project (CLI extension to existing CollabIQ codebase)
**Performance Goals**: Status commands <5s, E2E test on 10 emails <3 minutes, non-processing commands <2s
**Constraints**: Must support both TTY and non-TTY environments, backward compatible with existing scripts during transition, no new external dependencies beyond typer/rich/click
**Scale/Scope**: 30+ CLI commands across 7 command groups, single admin user per environment, manual operation (not automated scheduling)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development ✅

- **spec.md exists**: ✅ Complete specification with 8 user stories, 78 functional requirements, 12 success criteria
- **User scenarios with acceptance criteria**: ✅ All 8 user stories have Given/When/Then scenarios
- **Technology-agnostic requirements**: ✅ All requirements focus on user capabilities, not implementation details
- **Status**: PASS

### II. Incremental Delivery via Independent User Stories ✅

- **User stories prioritized**: ✅ P1 (Single Entry Point, Email Pipeline), P2 (Notion, LLM, E2E Testing), P3 (Errors, Status, Config)
- **Independently testable**: ✅ Each story has "Independent Test" section with standalone verification
- **P1 constitutes viable MVP**: ✅ P1 delivers unified CLI with email management - core admin functionality
- **Priority order execution**: ✅ Tasks will be organized by user story priority
- **Status**: PASS

### III. Test-Driven Development (TDD) - MANDATORY ✅

- **Tests required**: ✅ Spec includes validation criteria for unit tests, integration tests, E2E tests, help text validation
- **Test-first discipline**: Will apply during implementation (contract tests → unit tests → integration tests before code)
- **Contract tests**: ✅ Required for CLI interface (command parsing, argument validation, help text)
- **Integration tests**: ✅ Required for multi-command workflows (fetch → clean → process)
- **Status**: PASS (will enforce during implementation)

### IV. Design Artifact Completeness ✅

- **Planning artifacts required**:
  - `plan.md`: ✅ Complete (this file)
  - `research.md`: ✅ Complete (Phase 0 - technology decisions, integration patterns, LLM graceful degradation)
  - `data-model.md`: ✅ Complete (Phase 1 - 12 entities, relationships, validation rules)
  - `quickstart.md`: ✅ Complete (Phase 1 - installation, workflows, troubleshooting)
  - `contracts/`: ✅ Complete (Phase 1 - cli-interface.md, command-groups.md with 30+ command specs)
- **Constitution check**: ✅ Complete (initial + post-design evaluation)
- **Agent context updated**: ✅ Complete (typer, rich dependencies added to CLAUDE.md)
- **Status**: COMPLETE - Ready for task generation (/speckit.tasks)

### V. Simplicity & Justification ✅

- **Default to simplest solution**: ✅ Using typer (standard Python CLI framework), rich (standard terminal formatting), existing file-based storage
- **Patterns justified**: No complex abstractions planned - straightforward command handlers calling existing components
- **No constitution violations expected**: CLI is a presentation layer over existing services
- **YAGNI applied**: Building only specified commands, no premature frameworks or plugin systems
- **Status**: PASS

### Overall Gate Status: ✅ PASS

**Post-Design Re-evaluation** (2025-11-08):
All design artifacts completed. Constitution compliance verified:
- ✅ Specification complete with prioritized user stories
- ✅ Test-driven development approach documented (contract → unit → integration tests)
- ✅ All planning artifacts generated (research, data-model, contracts, quickstart)
- ✅ Simplicity maintained (standard frameworks, no complex abstractions)
- ✅ No constitution violations requiring justification

**Gate cleared for implementation**. Ready to proceed to `/speckit.tasks` for task generation.

## Project Structure

### Documentation (this feature)

```text
specs/011-admin-cli/
├── spec.md              # Feature specification (created)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli-interface.md # CLI command contracts and argument specifications
│   └── command-groups.md # Command group organization and routing
├── checklists/
│   └── requirements.md  # Specification quality checklist (created)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── collabiq/              # NEW: Unified CLI entry point module
│   ├── __init__.py        # Main CLI app with typer setup
│   ├── commands/          # NEW: Command group implementations
│   │   ├── __init__.py
│   │   ├── email.py       # Email pipeline commands (fetch, clean, list, verify, process)
│   │   ├── notion.py      # Notion integration commands (verify, schema, test-write, cleanup)
│   │   ├── test.py        # Testing commands (e2e, select-emails, validate)
│   │   ├── errors.py      # Error management commands (list, show, retry, clear)
│   │   ├── status.py      # System status commands (health, detailed, watch)
│   │   ├── llm.py         # LLM provider commands (status, test, policy, usage, enable/disable)
│   │   └── config.py      # Configuration commands (show, validate, test-secrets, get)
│   ├── formatters/        # NEW: Output formatting utilities
│   │   ├── __init__.py
│   │   ├── tables.py      # Table formatting with rich
│   │   ├── progress.py    # Progress indicators (spinners, bars, ETA)
│   │   ├── colors.py      # Color-coded output handling
│   │   └── json_output.py # JSON mode formatting
│   └── utils/             # NEW: CLI utilities
│       ├── __init__.py
│       ├── interrupt.py   # Graceful interrupt handling
│       ├── validation.py  # Input validation helpers
│       └── logging.py     # CLI operation logging
├── email_receiver/        # EXISTING: Email reception logic
├── content_normalizer/    # EXISTING: Email cleaning logic
├── llm_adapters/          # EXISTING: LLM extraction logic
├── llm_provider/          # EXISTING: Multi-LLM infrastructure (Phase 3b)
├── notion_integrator/     # EXISTING: Notion write operations
├── e2e_test/              # EXISTING: E2E test infrastructure
├── error_handling/        # EXISTING: Error tracking and DLQ
└── config/                # EXISTING: Configuration management

tests/
├── contract/
│   └── test_cli_interface.py    # NEW: CLI command contracts (argument parsing, help text)
├── integration/
│   ├── test_cli_email_workflow.py    # NEW: Email command workflows
│   ├── test_cli_notion_workflow.py   # NEW: Notion command workflows
│   └── test_cli_e2e_workflow.py      # NEW: E2E test command workflows
└── unit/
    ├── test_cli_formatters.py        # NEW: Output formatting tests
    └── test_cli_utils.py              # NEW: CLI utilities tests

pyproject.toml             # MODIFY: Add typer, rich dependencies and collabiq entry point
```

**Structure Decision**: Single project structure (Option 1) with new `src/collabiq/` module containing CLI implementation. The CLI is a presentation layer that orchestrates existing components (email_receiver, llm_adapters, notion_integrator, e2e_test, error_handling). No changes to existing modules except adding CLI command handlers. Package entry point will be configured in pyproject.toml to install `collabiq` command globally.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified. This feature follows the simplicity principle by:
- Using standard Python CLI framework (typer) without custom abstractions
- Presenting existing components through CLI interface (no new business logic)
- File-based storage aligned with existing architecture
- No premature optimization or plugin systems
