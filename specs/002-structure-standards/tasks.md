# Tasks: Project Structure Standards & File Naming Convention

**Input**: Design documents from `/specs/002-structure-standards/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not included - this feature focuses on documentation and manual file operations

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `docs/`, `.specify/memory/` at repository root
- This feature primarily works with documentation and configuration files

---

## Phase 1: Setup (Preparation)

**Purpose**: Ensure clean environment and prerequisites for standards documentation

- [ ] T001 Verify Git repository is clean with no uncommitted changes (run `git status`)
- [ ] T002 [P] Verify pytest is installed for final verification (run `uv run pytest --version` or `uv add --dev pytest`)
- [ ] T003 [P] Create backup of current constitution.md at `.specify/memory/constitution.md.backup`
- [ ] T004 [P] Create reports directory at `specs/002-structure-standards/reports/`

**Checkpoint**: Environment ready - user story implementation can now begin

---

## Phase 2: User Story 1 - Establish File Naming Standards (Priority: P1) 🎯 MVP

**Goal**: Document comprehensive file naming conventions in constitution.md so all developers have a reference guide

**Independent Test**: Review updated constitution.md and verify all naming rules are documented with pattern descriptions, format specifications, examples, and rationale

### Implementation for User Story 1

- [ ] T005 [US1] Read research.md to understand all naming convention decisions
- [ ] T006 [US1] Read data-model.md to understand Naming Convention Rule entity structure
- [ ] T007 [US1] Open .specify/memory/constitution.md for editing
- [ ] T008 [US1] Add "File Naming Standards" section after existing principles (before "Development Workflow" section)
- [ ] T009 [US1] Document Python naming standards (PEP 8 snake_case for modules) with examples in .specify/memory/constitution.md
- [ ] T010 [US1] Document major documentation naming (SCREAMING_SNAKE_CASE.md) with examples in .specify/memory/constitution.md
- [ ] T011 [US1] Document guide/tutorial naming (kebab-case.md) with boundary rules in .specify/memory/constitution.md
- [ ] T012 [US1] Document test file naming (test_*.py pytest convention) with examples in .specify/memory/constitution.md
- [ ] T013 [US1] Document test fixture naming (sequential numbering, descriptive names) with examples in .specify/memory/constitution.md
- [ ] T014 [US1] Document SpecKit framework conventions (###-feature-name/, spec.md, etc.) in .specify/memory/constitution.md
- [ ] T015 [US1] Document ecosystem standard files (README.md, pyproject.toml, Makefile - never rename) in .specify/memory/constitution.md
- [ ] T016 [US1] Document Git workflow for renames (use `git mv`, separate commits) in .specify/memory/constitution.md
- [ ] T017 [US1] Update constitution version from 1.0.0 to 1.1.0 (MINOR bump - new section added) in .specify/memory/constitution.md
- [ ] T018 [US1] Add amendment notes explaining v1.1.0 changes (File Naming Standards section added) in .specify/memory/constitution.md
- [ ] T019 [US1] Verify all file categories covered: specs, docs, Python modules, tests, fixtures, config files
- [ ] T020 [US1] Verify each naming rule includes: pattern description, format spec, valid examples, invalid examples, rationale
- [ ] T021 [US1] Commit constitution changes with message: "Add File Naming Standards section to constitution"

**Checkpoint**: Constitution.md now contains comprehensive naming standards (SC-001 complete) ✅

**Verification for US1**:
```bash
# Verify File Naming Standards section exists
grep -A 10 "File Naming Standards" .specify/memory/constitution.md

# Verify all categories documented
grep "Python Source Files" .specify/memory/constitution.md
grep "Documentation Files" .specify/memory/constitution.md
grep "Test Files" .specify/memory/constitution.md
grep "SpecKit Framework" .specify/memory/constitution.md

# Verify version updated to 1.1.0
grep "Version.*1.1.0" .specify/memory/constitution.md
```

---

## Phase 3: User Story 2 - Audit Current Project Structure (Priority: P2)

**Goal**: Identify all naming inconsistencies in current project with severity ratings to create actionable roadmap

**Independent Test**: Review audit report and verify all findings have file paths, severity ratings, recommendations, and migration complexity estimates

### Implementation for User Story 2

- [ ] T022 [US2] Create audit report file at `specs/002-structure-standards/reports/structure-audit.md`
- [ ] T023 [US2] Add audit report header with date, auditor name, summary placeholders in `reports/structure-audit.md`
- [ ] T024 [P] [US2] Audit Python modules: list all files with `find src/ config/ -name "*.py" -type f`
- [ ] T025 [P] [US2] Audit documentation files: list all files with `ls -1 docs/*.md`
- [ ] T026 [P] [US2] Audit test files: list all files with `find tests/ -name "*.py" -type f`
- [ ] T027 [P] [US2] Audit test fixtures: list all files with `find tests/fixtures/ -type f`
- [ ] T028 [US2] Check Python modules against snake_case standard, document any violations in `reports/structure-audit.md`
- [ ] T029 [US2] Check major docs against SCREAMING_SNAKE_CASE standard, document any violations in `reports/structure-audit.md`
- [ ] T030 [US2] Check guide docs against kebab-case standard, identify boundary cases (e.g., quickstart.md) in `reports/structure-audit.md`
- [ ] T031 [US2] Check test files against test_*.py convention, document any violations in `reports/structure-audit.md`
- [ ] T032 [US2] Check fixtures against naming guidelines, document any issues in `reports/structure-audit.md`
- [ ] T033 [US2] For each finding: assign severity (Critical, High, Medium, Low) based on impact on productivity
- [ ] T034 [US2] For each finding: estimate migration complexity (Simple, Moderate, Complex) based on references
- [ ] T035 [US2] For each finding: search for references with `grep -r "filename" . --exclude-dir=.git --exclude-dir=.venv`
- [ ] T036 [US2] For each finding: provide recommended name following documented standards
- [ ] T037 [US2] Create summary section with total findings count by severity in `reports/structure-audit.md`
- [ ] T038 [US2] Prioritize findings list: Critical first, then High, then Medium, then Low
- [ ] T039 [US2] Add re-audit section placeholder for post-cleanup verification in `reports/structure-audit.md`
- [ ] T040 [US2] Commit audit report with message: "Complete project structure audit with severity ratings"

**Checkpoint**: Audit report documents all inconsistencies with actionable recommendations (SC-006 complete) ✅

**Verification for US2**:
```bash
# Verify audit report exists and has content
cat specs/002-structure-standards/reports/structure-audit.md | head -30

# Check for severity ratings
grep -E "(Critical|High|Medium|Low)" specs/002-structure-standards/reports/structure-audit.md

# Verify summary section exists
grep "Summary" specs/002-structure-standards/reports/structure-audit.md
```

---

## Phase 4: User Story 3 - Apply Cleanup Recommendations (Priority: P3)

**Goal**: Resolve all Critical and High severity naming inconsistencies while preserving Git history and functionality

**Independent Test**: Verify all Critical/High findings resolved by re-running audit commands and confirming 0 remaining issues

**⚠️ NOTE**: Tasks below are TEMPLATE tasks. Actual cleanup tasks depend on audit findings from Phase 3.
Replace these tasks with specific file rename operations based on the audit report.

### Implementation for User Story 3

- [ ] T041 [US3] Review audit report and identify all Critical severity findings
- [ ] T042 [US3] Review audit report and identify all High severity findings
- [ ] T043 [US3] For each Critical/High finding: create migration task entry in `reports/structure-audit.md`
- [ ] T044 [US3] For each migration: identify dependencies (which tasks must complete first)
- [ ] T045 [US3] Order migrations by: (1) Critical before High, (2) no-dependency before with-dependency

**If findings exist, execute these cleanup steps per finding:**

#### Template: Rename Documentation File (Example)

- [ ] T046 [US3] Search for references to old filename: `grep -r "old_doc" . --exclude-dir=.git --exclude-dir=.venv`
- [ ] T047 [US3] Rename file using git mv: `git mv docs/old_doc.md docs/NEW_DOC.md`
- [ ] T048 [US3] Update all references found in step T046 in their respective files
- [ ] T049 [US3] Commit rename + reference updates: "Rename: old_doc.md → NEW_DOC.md (SCREAMING_SNAKE_CASE)"
- [ ] T050 [US3] Verify Git history preserved: `git log --follow docs/NEW_DOC.md`

#### Template: Rename Python Module with Imports (Example)

- [ ] T051 [US3] Search for import statements: `grep -r "from old_module" src/ tests/`
- [ ] T052 [US3] Rename module using git mv: `git mv src/old_module.py src/new_module.py`
- [ ] T053 [US3] Commit rename only: "Rename: old_module.py → new_module.py (snake_case)"
- [ ] T054 [US3] Update all import statements identified in T051
- [ ] T055 [US3] Commit import updates: "Update imports after old_module → new_module rename"
- [ ] T056 [US3] Verify tests pass: `uv run pytest`

**Repeat above template for each Critical/High finding**

#### Post-Cleanup Verification

- [ ] T057 [US3] Run pytest to verify no functionality broken: `uv run pytest`
- [ ] T058 [US3] Re-audit Python modules: `find src/ config/ -name "*.py" -type f`
- [ ] T059 [US3] Re-audit documentation: `ls -1 docs/*.md`
- [ ] T060 [US3] Re-audit tests: `find tests/ -name "*.py" -type f`
- [ ] T061 [US3] Verify 0 Critical severity findings remain
- [ ] T062 [US3] Verify 0 High severity findings remain
- [ ] T063 [US3] Update audit report with re-audit results in `reports/structure-audit.md`
- [ ] T064 [US3] Document deferred Medium/Low findings for future iteration in `reports/structure-audit.md`
- [ ] T065 [US3] Commit re-audit results: "Re-audit: Verify all Critical/High findings resolved"

**Checkpoint**: All Critical and High findings resolved, tests passing (SC-002, SC-005 complete) ✅

**Verification for US3**:
```bash
# Verify all tests pass
uv run pytest

# Check Git history preserved for renamed files
git log --follow docs/[renamed-file].md

# Verify audit report shows 0 Critical/High
grep "Critical Findings Remaining: 0" specs/002-structure-standards/reports/structure-audit.md
grep "High Findings Remaining: 0" specs/002-structure-standards/reports/structure-audit.md
```

---

## Phase 5: Polish & Documentation

**Purpose**: Final verification and feature completion

- [ ] T066 [P] Review quickstart.md and verify all steps match actual implementation
- [ ] T067 [P] Update completion-report.md template (if exists) with feature summary
- [ ] T068 [P] Verify all success criteria met: SC-001 through SC-006
- [ ] T069 Run final validation: verify developer can locate any file type using constitution.md (SC-004)
- [ ] T070 Create final commit summarizing feature completion

**Checkpoint**: Feature complete, all success criteria met ✅

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup completion
- **User Story 2 (Phase 3)**: Depends on User Story 1 completion (audit requires standards to exist)
- **User Story 3 (Phase 4)**: Depends on User Story 2 completion (cleanup requires audit findings)
- **Polish (Phase 5)**: Depends on User Story 3 completion

### User Story Dependencies

```text
US1 (Establish Standards) → US2 (Audit Structure) → US3 (Apply Cleanup)
```

**Sequential Execution Required**: Each user story builds on the previous one:
- US2 needs US1 because audit compares files against documented standards
- US3 needs US2 because cleanup follows audit recommendations

### Within Each User Story

**User Story 1** (P1):
- T005-T007: Sequential (must read docs before editing)
- T008-T018: Sequential (must add sections in logical order)
- T019-T021: Sequential (verification then commit)

**User Story 2** (P2):
- T024-T027: Parallel [P] (independent file listings)
- T028-T032: Sequential (check against standards)
- T033-T040: Sequential (analyze findings then commit)

**User Story 3** (P3):
- T041-T045: Sequential (must identify and plan before executing)
- T046-T056: Per-finding blocks (each rename is independent, but steps within a rename are sequential)
- T057-T065: Sequential (verify then document)

### Parallel Opportunities

**Limited parallelization** in this feature due to sequential nature:
- Phase 1 Setup: T002, T003, T004 can run in parallel
- Phase 3 US2 Audit: T024-T027 can run in parallel (file listings)
- Phase 4 US3 Cleanup: Different file renames can happen in parallel if no shared references

**Cannot parallelize**:
- User stories (US1 → US2 → US3 must be sequential)
- Documentation updates within US1 (logical order required)
- Rename + update references (must be atomic per file)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch setup tasks in parallel:
Task: "Verify pytest is installed for final verification"
Task: "Create backup of current constitution.md"
Task: "Create reports directory"
```

## Parallel Example: Phase 3 User Story 2 (Audit)

```bash
# Launch audit scans in parallel:
Task: "Audit Python modules: list all files"
Task: "Audit documentation files: list all files"
Task: "Audit test files: list all files"
Task: "Audit test fixtures: list all files"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~5 minutes)
2. Complete Phase 2: User Story 1 (~30 minutes)
3. **STOP and VALIDATE**: Constitution.md has all naming standards documented
4. **SUCCESS**: Developers can now reference constitution.md for all naming decisions (MVP delivered!)

**MVP Value**: Even without audit or cleanup, having documented standards prevents future inconsistency.

### Incremental Delivery

1. **Foundation** (Phase 1): Setup → Environment ready
2. **MVP** (Phase 2): User Story 1 → Standards documented (immediate value!)
3. **Analysis** (Phase 3): User Story 2 → Audit complete → Technical debt visibility
4. **Cleanup** (Phase 4): User Story 3 → Standards enforced → Consistent codebase
5. **Polish** (Phase 5): Final verification → Feature complete

### Stopping Points

You can stop after any user story and still have delivered value:

- **After US1**: Standards exist, future files will be consistent
- **After US2**: Standards exist + visibility into current issues
- **After US3**: Standards exist + current codebase is clean

---

## Notes

- **Tests not included**: This feature is documentation and manual operations, verified through review
- **Sequential user stories**: Unlike typical features, these stories cannot be parallelized (US2 needs US1, US3 needs US2)
- **[P] markers**: Used for independent file operations within a phase
- **[Story] labels**: [US1], [US2], [US3] map to user stories from spec.md
- **Git mv required**: All file renames must use `git mv` to preserve history (FR-008)
- **Commit strategy**: Separate commits for renames vs content changes (per research.md)
- **Template tasks in Phase 4**: Replace T046-T056 with actual file operations based on audit findings
- **No breaking changes**: All tests must pass after cleanup (FR-010, SC-005)

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (US1 - Establish Standards)**: 17 tasks
- **Phase 3 (US2 - Audit Structure)**: 19 tasks
- **Phase 4 (US3 - Apply Cleanup)**: 25 tasks (templates - adjust based on findings)
- **Phase 5 (Polish)**: 5 tasks

**Total**: 70 tasks (including templates)

**Estimated Time**:
- MVP (US1 only): 30-45 minutes
- MVP + Audit (US1 + US2): 1-1.5 hours
- Full feature (US1 + US2 + US3): 2-3 hours (depends on cleanup scope)

**Parallelizable Tasks**: 7 tasks marked [P]

**Independent Test Criteria**:
- US1: Review constitution.md completeness
- US2: Review audit report severity ratings
- US3: Verify 0 Critical/High findings + tests pass
