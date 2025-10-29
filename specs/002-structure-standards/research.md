# Research: Project Structure Standards & File Naming Convention

**Feature**: 002-structure-standards
**Date**: 2025-10-29
**Purpose**: Investigate best practices for file naming conventions and project structure organization

## Research Questions

1. What are the established Python community standards for file and module naming?
2. What naming conventions are appropriate for documentation files in software projects?
3. What are the best practices for preserving Git history when renaming files?
4. How should test files be organized and named in Python projects?
5. What naming patterns does the SpecKit framework already establish?

## Research Findings

### R1: Python Community Standards (PEP 8)

**Decision**: Adopt PEP 8 naming conventions as the foundation for all Python code

**Rationale**:
- PEP 8 is the official Python style guide, widely adopted across the Python ecosystem
- Provides clear, tested conventions that Python developers universally recognize
- Ensures compatibility with Python tooling (linters, formatters, IDEs)

**Key PEP 8 Conventions**:

1. **Module and Package Names**:
   - Format: `lowercase_with_underscores` (snake_case)
   - Keep names short and descriptive
   - Avoid dashes/hyphens (not importable in Python)
   - Examples: `email_receiver`, `llm_adapters`, `notion_integrator` ✅

2. **Python Special Files**:
   - `__init__.py` - Package initialization (required for Python packages)
   - `__main__.py` - Entry point when package run as module
   - `__version__.py` - Version information (conventional but not required)
   - These follow Python conventions and should NEVER be renamed

3. **Test Files**:
   - Prefix: `test_` for pytest discovery
   - Format: `test_<module_name>.py` or `<module_name>_test.py`
   - Examples: `test_email_receiver.py`, `test_gemini_extraction.py`

**Alternatives Considered**:
- camelCase (rejected - not Python convention, reduces readability)
- kebab-case (rejected - not importable as Python modules)
- SCREAMING_SNAKE_CASE (rejected - reserved for constants)

**Source**: [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)

---

### R2: Documentation File Naming Conventions

**Decision**: Use two-tier documentation naming system based on importance and permanence

**Rationale**:
- High-visibility documentation (README, CHANGELOG) uses ecosystem-standard naming
- Major architectural/technical documents use SCREAMING_SNAKE_CASE for prominence
- User guides and tutorials use descriptive kebab-case for readability

**Documentation Naming Rules**:

1. **Ecosystem Standards** (NEVER change these):
   - `README.md` - Project overview and quick start
   - `CHANGELOG.md` - Version history
   - `LICENSE` - Legal information
   - `CONTRIBUTING.md` - Contribution guidelines
   - These are universally recognized and expected at repository root

2. **Major Technical Documents**:
   - Format: `SCREAMING_SNAKE_CASE.md`
   - Purpose: High-importance reference documents
   - Examples:
     - `ARCHITECTURE.md` ✅
     - `API_CONTRACTS.md` ✅
     - `IMPLEMENTATION_ROADMAP.md` ✅
     - `FEASIBILITY_TESTING.md` ✅
   - Rationale: Visual prominence in file listings, clearly distinct from code files

3. **Guides and Tutorials**:
   - Format: `descriptive-kebab-case.md`
   - Purpose: Step-by-step instructions, explanatory content
   - Examples:
     - `quickstart.md` ✅ (SpecKit standard)
     - `email-infrastructure-comparison.md` ✅
     - `getting-started.md`
   - Rationale: Readable, URL-friendly, lower visual weight than major docs

**Current CollabIQ Compliance**:
- ✅ Ecosystem standards: `README.md`, `Makefile`
- ✅ Major docs: All use SCREAMING_SNAKE_CASE
- ✅ Guides: `quickstart.md` follows kebab-case
- Issue: Inconsistency between `quickstart.md` (kebab) and major docs (SCREAMING) - need to define boundary

**Alternatives Considered**:
- All lowercase (rejected - poor visual hierarchy)
- camelCase (rejected - not markdown convention)
- All SCREAMING_SNAKE_CASE (rejected - loses importance signaling)

**Industry References**:
- Rust: Uses SCREAMING_SNAKE_CASE for major docs (ARCHITECTURE.md, CONTRIBUTING.md)
- Python: Mix of README.md (standard) and descriptive lowercase
- Go: Primarily README.md with supplementary lowercase docs
- Consensus: README.md is universal, other conventions vary by project

---

### R3: Git File Rename Best Practices

**Decision**: Use `git mv` for all tracked file renames and separate rename commits from content changes

**Rationale**:
- Git's rename detection preserves file history across renames
- Separate commits make history easier to review and understand
- Proper attribution maintained for all contributors

**Git Rename Workflow**:

1. **Use `git mv` Command**:
   ```bash
   git mv old_name.py new_name.py
   ```
   - Git automatically tracks the rename (shown as "renamed: old -> new")
   - File history (`git log --follow`) remains intact
   - `git blame` traces back through the rename

2. **Commit Strategy**:
   - **Separate commit per category of renames**:
     ```bash
     git mv docs/old_doc.md docs/NEW_DOC.md
     git commit -m "Rename: old_doc.md → NEW_DOC.md (conform to SCREAMING_SNAKE_CASE)"
     ```
   - **Never mix renames with content changes** in same commit
   - Include before/after paths in commit message
   - Use "Rename:" prefix for clarity in git log

3. **Update References After Rename**:
   - Search codebase for all import statements: `grep -r "old_name" .`
   - Update all imports in separate commit after rename:
     ```bash
     git commit -m "Update imports after email_receiver → email_processor rename"
     ```

4. **Verify History Preservation**:
   ```bash
   git log --follow new_name.py  # Should show full history including pre-rename
   ```

**Complexity Considerations**:
- **Simple renames** (no imports): Single `git mv` + commit
- **Module renames** (imported elsewhere):
  1. Commit: Rename file with `git mv`
  2. Commit: Update all imports
  3. Commit: Run tests to verify
- **Mass renames**: Group by category (all docs, all modules) in separate commits

**Alternatives Considered**:
- Manual `mv` + `git add` (rejected - Git may not detect rename)
- Squashing rename commits (rejected - loses granular history)
- Mixing renames with content changes (rejected - makes review impossible)

**Source**: [Git Documentation - git-mv](https://git-scm.com/docs/git-mv)

---

### R4: Test Organization and Naming in Python Projects

**Decision**: Adopt three-tier test organization (unit, integration, contract) with pytest naming conventions

**Rationale**:
- Clear separation of test types aids in selective test execution
- pytest's test discovery works automatically with `test_` prefix
- Contract tests validate API boundaries (critical for CollabIQ's LLM/Notion integrations)

**Test Organization Structure**:

```text
tests/
├── contract/          # API/interface boundary tests
│   ├── test_gemini_api.py
│   ├── test_notion_api.py
│   └── test_email_parser.py
├── integration/       # Multi-component workflow tests
│   ├── test_email_to_notion_flow.py
│   └── test_end_to_end.py
├── unit/              # Single-component tests
│   ├── test_email_receiver.py
│   ├── test_llm_adapters.py
│   └── test_notion_integrator.py
└── fixtures/          # Test data and mocks
    ├── sample_emails/
    │   ├── sample-001.txt
    │   └── sample-002.txt
    └── README.md
```

**Test File Naming Rules**:

1. **Test Files**:
   - Format: `test_<module_or_feature>.py`
   - Must start with `test_` for pytest discovery
   - Use snake_case for multi-word names
   - Mirror source structure: `src/email_receiver/` → `tests/unit/test_email_receiver.py`

2. **Fixture Files**:
   - Format: Descriptive name with appropriate extension
   - Keep original format when possible (`.txt` for emails, `.json` for API responses)
   - Number sequentially for series: `sample-001.txt`, `sample-002.txt` ✅
   - Use kebab-case for readability: `sample-emails/`, `mock-responses/`

3. **Test Documentation**:
   - `README.md` in each test directory explaining purpose and usage
   - `GROUND_TRUTH.md` for expected results in fixtures ✅

**Current CollabIQ Compliance**:
- ✅ Three-tier structure: contract/, integration/, unit/
- ✅ Fixtures organized: tests/fixtures/sample_emails/
- ✅ Sequential naming: sample-001.txt through sample-006.txt
- ✅ Documentation: GROUND_TRUTH.md and README.md present

**pytest Configuration**:
- pytest automatically discovers `test_*.py` and `*_test.py`
- Can run by directory: `pytest tests/unit/` (unit tests only)
- Can run by marker: `pytest -m integration` (requires `@pytest.mark.integration`)

**Alternatives Considered**:
- Flat test structure (rejected - harder to navigate as project grows)
- `*_test.py` suffix (rejected - less common in Python ecosystem)
- Separate test directories per module (rejected - duplicates source structure unnecessarily)

**Industry Standard**: pytest with three-tier structure is common in Python projects

---

### R5: SpecKit Framework Conventions

**Decision**: Document SpecKit conventions in constitution but DO NOT modify them

**Rationale**:
- SpecKit is an established framework with its own design decisions
- Conventions are already tested and working
- CollabIQ project depends on SpecKit's structure
- Consistency across all SpecKit projects is valuable

**SpecKit File Naming Conventions** (to be documented, not changed):

1. **Feature Directories**:
   - Format: `specs/###-feature-name/`
   - Pattern: `###` = zero-padded 3-digit number, `feature-name` = kebab-case
   - Examples: `001-feasibility-architecture`, `002-structure-standards` ✅
   - Rationale: Sequential numbering for ordering, kebab-case for readability

2. **Specification Files** (inside feature directory):
   - `spec.md` - Feature specification (user requirements, success criteria)
   - `plan.md` - Implementation plan (technical approach, architecture)
   - `research.md` - Research findings and decisions
   - `data-model.md` - Entity definitions and relationships
   - `tasks.md` - Dependency-ordered implementation tasks
   - `quickstart.md` - Step-by-step usage instructions
   - `completion-report.md` - Feature completion summary
   - Format: `lowercase-kebab-case.md` for all SpecKit documents
   - Rationale: Consistent, readable, no ambiguity

3. **SpecKit Subdirectories**:
   - `contracts/` - API/interface specifications
   - `checklists/` - Quality validation checklists
   - `scripts/` - Feature-specific automation
   - Format: `lowercase` directory names (single word preferred)

4. **SpecKit Framework Files** (`.specify/` directory):
   - `.specify/templates/` - Document templates
   - `.specify/scripts/` - Automation scripts
   - `.specify/memory/constitution.md` - Project governance
   - Format: Framework-defined, DO NOT CHANGE

**Current CollabIQ Compliance**:
- ✅ All feature directories follow `###-feature-name` pattern
- ✅ All spec files use lowercase kebab-case
- ✅ Subdirectories follow SpecKit conventions
- ✅ Framework files untouched

**Documentation Requirement**:
- Add "SpecKit Framework Conventions" subsection to constitution.md
- Explicitly state these conventions are inherited and not project-specific
- Reference SpecKit documentation for framework design rationale

**No Alternatives** - SpecKit conventions are fixed by the framework

---

## Summary of Decisions

### File Naming Standards to Document in Constitution

1. **Python Modules and Packages**: `lowercase_with_underscores` (PEP 8)
2. **Major Documentation**: `SCREAMING_SNAKE_CASE.md` (architectural, technical)
3. **Guides and Tutorials**: `descriptive-kebab-case.md` (instructional)
4. **Ecosystem Standards**: `README.md`, `LICENSE`, `CHANGELOG.md` (never change)
5. **Test Files**: `test_<name>.py` (pytest convention)
6. **Test Fixtures**: Descriptive names with appropriate extensions, sequential numbering
7. **SpecKit Conventions**: Inherited from framework (document but don't modify)

### Git Workflow Standards to Document

1. Use `git mv` for all tracked file renames
2. Separate rename commits from content changes
3. Include before/after paths in commit messages
4. Update imports in separate commits after renames
5. Verify history preservation with `git log --follow`

### Boundaries and Edge Cases Resolved

1. **Documentation Boundary**:
   - SCREAMING_SNAKE_CASE for high-importance reference docs
   - kebab-case for guides and tutorials
   - Rule of thumb: If it's in docs/ root and describes system architecture/design → SCREAMING

2. **Python Special Files**: Never rename `__init__.py`, `__main__.py`, `__version__.py`

3. **Ecosystem Config Files**: Never rename `pyproject.toml`, `Makefile`, `uv.lock`, `.gitignore`

4. **SpecKit Framework**: Document conventions but never modify `.specify/` structure

5. **Cross-Branch Files**: Only modify files on current branch (002-structure-standards)

---

## Research Validation

All research questions have been answered with concrete decisions:
- ✅ Python standards: PEP 8 snake_case for modules
- ✅ Documentation standards: Two-tier system (SCREAMING vs kebab-case)
- ✅ Git practices: `git mv` with separate commits
- ✅ Test organization: Three-tier structure with pytest naming
- ✅ SpecKit conventions: Document but don't modify

**No NEEDS CLARIFICATION items remain** - Ready to proceed to Phase 1 (Design).
