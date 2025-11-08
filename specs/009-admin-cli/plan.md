# Implementation Plan: Admin CLI Enhancement

**Branch**: `009-admin-cli` | **Date**: 2025-11-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-admin-cli/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a unified `collabiq` CLI command that provides organized subcommands for managing all CollabIQ operations including email pipeline, Notion integration, testing, error management, system health monitoring, LLM provider management, and configuration. The CLI will use Typer for command structure, Rich for formatted output, and integrate with existing components (email receiver, content normalizer, LLM adapters, Notion integrator, error handling system).

## Technical Context

**Language/Version**: Python 3.12+ (established in project, using UV package manager)
**Primary Dependencies**: typer (CLI framework), rich (terminal formatting), click (low-level CLI support), existing CollabIQ components (email_receiver, content_normalizer, llm_adapters, notion_integrator, error_handling)
**Storage**: File-based (existing JSON data in `data/` directory, no new storage requirements)
**Testing**: pytest (established in project)
**Target Platform**: Linux/macOS server environments with shell access
**Project Type**: Single project (CLI extension to existing codebase)
**Performance Goals**: Status commands < 5 seconds, E2E test (10 emails) < 3 minutes, non-processing commands < 2 seconds
**Constraints**: Must maintain backward compatibility with existing `uv run python src/cli.py` scripts during transition, no new external dependencies beyond typer/rich/click, must work in containerized environments without interactive TTY
**Scale/Scope**: Single admin user per environment, 7 command groups, ~30 total commands, integration with 6 existing pipeline components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
