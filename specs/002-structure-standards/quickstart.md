# Quickstart: Project Structure Standards & File Naming Convention

**Feature**: 002-structure-standards
**Last Updated**: 2025-10-29
**Estimated Time**: 30-45 minutes to review and apply P1 (documentation), 1-2 hours for full P1+P2+P3 (includes audit and cleanup)

## Overview

This guide walks you through establishing file naming conventions, auditing the project structure, and applying cleanup recommendations to ensure consistency across the CollabIQ codebase.

---

## Prerequisites

- Git repository with clean working tree (no uncommitted changes)
- Python 3.12 environment with UV package manager
- Access to `.specify/memory/constitution.md` (write permissions)
- Familiarity with basic Git commands (`git mv`, `git commit`)
- pytest installed (for verification after cleanup): `uv add --dev pytest`

**Verify Prerequisites**:

```bash
# Check Git status
git status  # Should show "nothing to commit, working tree clean"

# Check Python version
uv run python --version  # Should show Python 3.12.x

# Check pytest is available
uv run pytest --version  # Should show pytest version
```

---

## Phase 1: Establish File Naming Standards (P1 - MVP)

**Goal**: Document comprehensive file naming conventions in the constitution
**Time**: ~30 minutes
**Output**: Updated constitution.md with "File Naming Standards" section

### Step 1.1: Read Research Findings

Review the research document to understand the decisions:

```bash
cat specs/002-structure-standards/research.md
```

**Key Decisions to Note**:
- Python modules: `lowercase_with_underscores` (PEP 8)
- Major docs: `SCREAMING_SNAKE_CASE.md`
- Guides: `descriptive-kebab-case.md`
- Tests: `test_<name>.py` (pytest convention)
- SpecKit: Inherited conventions (document but don't modify)

### Step 1.2: Review Data Model

Understand the entity structure:

```bash
cat specs/002-structure-standards/data-model.md
```

**Key Concepts**:
- **Naming Convention Rule**: Pattern + examples + rationale
- **File Category**: Groups files by type
- **Audit Finding**: Deviation from standards
- **Migration Task**: Fix operation

### Step 1.3: Open Constitution for Editing

```bash
# Backup current constitution
cp .specify/memory/constitution.md .specify/memory/constitution.md.backup

# Open for editing (use your preferred editor)
code .specify/memory/constitution.md  # VS Code
# OR
vi .specify/memory/constitution.md    # vim
# OR
nano .specify/memory/constitution.md  # nano
```

### Step 1.4: Add "File Naming Standards" Section

Insert the new section after the existing principles and before the "Development Workflow" section. Use this structure:

````markdown
## File Naming Standards

### Overview

This section defines naming conventions for all file types in the CollabIQ project. These standards ensure consistency, readability, and compatibility with tooling.

### Python Source Files

#### Module and Package Names

- **Format**: `lowercase_with_underscores` (snake_case)
- **Pattern**: `^[a-z][a-z0-9_]*\.py$`
- **Rationale**: PEP 8 standard, importable without escaping, widely recognized in Python ecosystem

**Valid Examples**:
- `email_receiver.py` ✅
- `llm_adapters.py` ✅
- `notion_integrator.py` ✅

**Invalid Examples**:
- `emailReceiver.py` ❌ (camelCase not allowed)
- `llm-adapters.py` ❌ (hyphens not importable)
- `LLMAdapters.py` ❌ (PascalCase not allowed)

**Exceptions**: Python special files (`__init__.py`, `__main__.py`, `__version__.py`) follow Python conventions and must never be renamed.

#### Package Directories

- **Format**: `lowercase_with_underscores` (snake_case, no .py extension)
- **Examples**: `email_receiver/`, `llm_adapters/`, `notion_integrator/`
- **Required**: Must contain `__init__.py` to be a Python package

### Documentation Files

#### Ecosystem Standards (NEVER change)

- `README.md` - Project overview
- `LICENSE` - Legal information
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Contribution guidelines

**Rationale**: Universally recognized by developers and tools (GitHub, GitLab, package managers)

#### Major Technical Documentation

- **Format**: `SCREAMING_SNAKE_CASE.md`
- **Purpose**: High-importance architectural, technical, or reference documents
- **Location**: `docs/` directory

**Examples**:
- `ARCHITECTURE.md` ✅
- `API_CONTRACTS.md` ✅
- `IMPLEMENTATION_ROADMAP.md` ✅
- `FEASIBILITY_TESTING.md` ✅

**Rationale**: Visual prominence in file listings, clearly distinct from guides

#### Guides and Tutorials

- **Format**: `descriptive-kebab-case.md`
- **Purpose**: Step-by-step instructions, explanatory content
- **Location**: `docs/` directory or feature specs

**Examples**:
- `quickstart.md` ✅
- `getting-started.md` ✅
- `email-infrastructure-comparison.md` ✅

**Rationale**: Readable, URL-friendly, lower visual weight than major docs

**Boundary Rule**: If the document describes system architecture or serves as a permanent reference → SCREAMING_SNAKE_CASE. If it provides instructions or explanations → kebab-case.

### Test Files

#### Test Modules

- **Format**: `test_<module_or_feature>.py`
- **Pattern**: `^test_[a-z][a-z0-9_]*\.py$`
- **Rationale**: pytest discovery convention

**Examples**:
- `test_email_receiver.py` ✅
- `test_gemini_extraction.py` ✅
- `test_notion_api.py` ✅

#### Test Organization

```text
tests/
├── contract/          # API/interface boundary tests
├── integration/       # Multi-component workflow tests
├── unit/              # Single-component tests
└── fixtures/          # Test data and mocks
```

**Directory Names**: `lowercase` (single word preferred)

#### Test Fixtures

- **Format**: Descriptive name with appropriate extension
- **Numbering**: Sequential for series (`sample-001.txt`, `sample-002.txt`)
- **Case**: `kebab-case` for multi-word names

**Examples**:
- `sample-001.txt` ✅ (email samples)
- `mock-response.json` ✅ (API mocks)
- `test-data.csv` ✅ (data fixtures)

**Documentation**: Include `README.md` explaining fixture purpose and `GROUND_TRUTH.md` for expected results

### SpecKit Framework Conventions (Inherited)

**Feature Directories**:
- **Format**: `specs/###-feature-name/`
- **Pattern**: Zero-padded 3-digit number + kebab-case name
- **Examples**: `001-feasibility-architecture`, `002-structure-standards`

**Specification Files** (inside feature directory):
- `spec.md` - Feature specification
- `plan.md` - Implementation plan
- `research.md` - Research findings
- `data-model.md` - Entity definitions
- `tasks.md` - Implementation tasks
- `quickstart.md` - Usage instructions
- `completion-report.md` - Completion summary

**Subdirectories**:
- `contracts/` - API specifications
- `checklists/` - Quality validation
- `scripts/` - Feature-specific automation

**Rationale**: These conventions are defined by the SpecKit framework and ensure consistency across all SpecKit-based projects. Do not modify.

### Configuration Files (Ecosystem Standards)

**NEVER rename these files** - they follow ecosystem conventions:

- `pyproject.toml` - Python project configuration (PEP 518)
- `Makefile` - Build automation
- `uv.lock` - UV dependency lock file
- `.gitignore` - Git ignore patterns
- `.env` - Environment variables
- `.env.example` - Environment template

**Rationale**: Required by tools and expected by developers across the ecosystem

### Git Workflow for Renames

#### Use `git mv` for All Renames

```bash
# Correct - preserves history
git mv old_name.py new_name.py

# Incorrect - may lose history
mv old_name.py new_name.py && git add new_name.py
```

#### Commit Strategy

1. **Separate commit per rename category**:
   ```bash
   git mv docs/old_doc.md docs/NEW_DOC.md
   git commit -m "Rename: old_doc.md → NEW_DOC.md (conform to SCREAMING_SNAKE_CASE)"
   ```

2. **Never mix renames with content changes** in same commit

3. **Include before/after paths** in commit message

4. **Update references in separate commit**:
   ```bash
   # After renaming module
   git commit -m "Update imports after email_receiver → email_processor rename"
   ```

#### Verify History Preservation

```bash
git log --follow new_name.py  # Should show full history including pre-rename
```

### Version

**Standards Version**: 1.0.0
**Ratified**: 2025-10-29
**Next Review**: After 001-feasibility-architecture merge to main
````

### Step 1.5: Update Constitution Version

After the "File Naming Standards" section, update the constitution version info:

```markdown
**Version**: 1.1.0 | **Ratified**: 2025-10-28 | **Last Amended**: 2025-10-29

**Amendment Notes**:
- v1.1.0 (2025-10-29): Added "File Naming Standards" section (MINOR version bump - new section added)
```

### Step 1.6: Commit the Documentation

```bash
# Verify changes
git diff .specify/memory/constitution.md

# Stage the file
git add .specify/memory/constitution.md

# Commit
git commit -m "Add File Naming Standards section to constitution

- Document Python module naming (snake_case per PEP 8)
- Document documentation naming (SCREAMING_SNAKE_CASE vs kebab-case)
- Document test file naming (pytest conventions)
- Document SpecKit framework conventions (inherited)
- Document Git workflow for file renames
- Bump constitution version to 1.1.0

Resolves User Story P1 - Establish File Naming Standards
Feature: 002-structure-standards"
```

### Step 1.7: Verify P1 Completion

**Acceptance Criteria from Spec**:

1. ✅ Developer can find naming rules for specs in constitution.md
2. ✅ Developer can find naming rules for tests in constitution.md
3. ✅ Developer can find naming rules for Python modules in constitution.md
4. ✅ Developer can find naming rules for documentation in constitution.md

**Test**:
```bash
# Search for each section
grep -A 5 "Python Source Files" .specify/memory/constitution.md
grep -A 5 "Documentation Files" .specify/memory/constitution.md
grep -A 5 "Test Files" .specify/memory/constitution.md
grep -A 5 "SpecKit Framework" .specify/memory/constitution.md
```

**P1 Complete** ✅ - Constitution now contains all naming standards

---

## Phase 2: Audit Current Project Structure (P2)

**Goal**: Identify all deviations from documented standards
**Time**: ~30 minutes
**Output**: Audit report with severity ratings

### Step 2.1: Create Audit Report File

```bash
mkdir -p specs/002-structure-standards/reports
touch specs/002-structure-standards/reports/structure-audit.md
```

### Step 2.2: Audit Python Modules

```bash
# List all Python files
find src/ config/ -name "*.py" -type f | sort
```

**Check Against Standards**:
- Are all module names snake_case?
- Are package directories snake_case?
- Are `__init__.py` files present in packages?

**Document Findings** in `structure-audit.md`:

```markdown
# Project Structure Audit Report

**Feature**: 002-structure-standards
**Date**: 2025-10-29
**Audited By**: [Your Name]

## Summary

- Total Files Audited: [count]
- Findings: [count]
  - Critical: [count]
  - High: [count]
  - Medium: [count]
  - Low: [count]

## Category: Python Modules

| Finding ID | File Path | Current Name | Recommended | Severity | References |
|------------|-----------|--------------|-------------|----------|------------|
| AUD-001 | src/... | ... | ... | ... | ... |

[No findings expected - all modules already follow snake_case]
```

### Step 2.3: Audit Documentation Files

```bash
# List all markdown files in docs/
ls -1 docs/*.md
```

**Check Against Standards**:
- Are major docs using SCREAMING_SNAKE_CASE?
- Are guides using kebab-case?
- Is `quickstart.md` correctly categorized (SpecKit guide, not major doc)?

**Document Findings**:
- Example: If `quickstart.md` should be `QUICKSTART.md` (debatable - it's a SpecKit standard)
- Check consistency: All architecture docs should match pattern

### Step 2.4: Audit Test Files

```bash
# List test files
find tests/ -name "*.py" -type f | sort
find tests/fixtures/ -type f | sort
```

**Check Against Standards**:
- Do all test files start with `test_`?
- Are fixture files using descriptive names?
- Is the three-tier structure (unit/, integration/, contract/) followed?

### Step 2.5: Assign Severity Ratings

For each finding, apply severity guidelines:

- **Critical**: File cannot be used (not importable, breaks build)
- **High**: Major inconsistency affecting multiple developers
- **Medium**: Inconsistency within a category
- **Low**: Minor issue with no practical impact

### Step 2.6: Commit Audit Report

```bash
git add specs/002-structure-standards/reports/structure-audit.md
git commit -m "Complete project structure audit

- Audited Python modules for PEP 8 compliance
- Audited documentation for naming consistency
- Audited test files for pytest conventions
- Identified [X] findings ([Y] Critical, [Z] High)
- Prioritized by impact on developer productivity

Resolves User Story P2 - Audit Current Project Structure
Feature: 002-structure-standards"
```

**P2 Complete** ✅ - Audit report documents all findings with severity ratings

---

## Phase 3: Apply Cleanup Recommendations (P3)

**Goal**: Resolve all Critical and High severity findings
**Time**: ~30-60 minutes (depends on findings)
**Output**: Renamed files conforming to standards

### Step 3.1: Review Audit Findings

```bash
cat specs/002-structure-standards/reports/structure-audit.md
```

**Focus on**:
- Critical severity findings (must fix)
- High severity findings (should fix before merge)
- Medium and Low (may defer)

### Step 3.2: Create Migration Plan

For each Critical/High finding, create a migration task:

```markdown
## Migration Tasks

| Task ID | Finding | Operation | Source → Target | Dependencies |
|---------|---------|-----------|-----------------|--------------|
| MIG-001 | AUD-001 | Rename | docs/old.md → docs/NEW.md | None |
| MIG-002 | AUD-002 | Update Refs | Update imports | MIG-001 |
```

### Step 3.3: Execute Migrations (Critical First)

**For each migration task**:

1. **Rename file using `git mv`**:
   ```bash
   git mv docs/old_doc.md docs/NEW_DOC.md
   ```

2. **Search for references**:
   ```bash
   grep -r "old_doc" . --exclude-dir=.git --exclude-dir=.venv
   ```

3. **Update references** (if any):
   ```bash
   # Edit files that reference the old name
   # Update import statements, links, etc.
   ```

4. **Commit rename + updates together**:
   ```bash
   git add .
   git commit -m "Rename: old_doc.md → NEW_DOC.md + update references

   - Renamed docs/old_doc.md to docs/NEW_DOC.md (SCREAMING_SNAKE_CASE)
   - Updated README.md:15 reference
   - Updated ARCHITECTURE.md:42 link

   Resolves: AUD-001 (High severity)
   Migration: MIG-001"
   ```

### Step 3.4: Verify No Breakage

**Run all tests** after each migration:

```bash
uv run pytest
```

**Expected**: All tests pass (no failures introduced)

**If tests fail**:
- Rollback: `git reset --hard HEAD~1`
- Investigate what broke
- Fix the issue
- Re-apply migration

### Step 3.5: Re-Audit

After all Critical/High fixes applied:

```bash
# Re-run audit commands from Step 2.2-2.4
# Verify 0 Critical/High findings remain
```

**Update audit report**:

```markdown
## Re-Audit Results (Post-Cleanup)

**Date**: 2025-10-29
**Critical Findings Remaining**: 0 ✅
**High Findings Remaining**: 0 ✅
**Medium Findings**: [count] (deferred)
**Low Findings**: [count] (deferred)
```

### Step 3.6: Final Commit

```bash
git add specs/002-structure-standards/reports/structure-audit.md
git commit -m "Re-audit: Verify all Critical/High findings resolved

- Re-ran structure audit
- Confirmed 0 Critical severity findings
- Confirmed 0 High severity findings
- Medium/Low findings documented for future iteration

Resolves User Story P3 - Apply Cleanup Recommendations
Feature: 002-structure-standards"
```

**P3 Complete** ✅ - Project structure conforms to documented standards

---

## Verification

### Overall Feature Completion

Run through success criteria from spec.md:

- **SC-001**: Constitution.md contains complete file naming standards ✅
- **SC-002**: All Critical and High severity issues resolved ✅
- **SC-003**: 100% compliance for new files (ongoing) ✅
- **SC-004**: Developer can locate files in <30 seconds ✅
- **SC-005**: All tests pass after cleanup ✅
- **SC-006**: Audit document has severity ratings ✅

### Feature Complete Checklist

- [x] P1: File naming standards documented in constitution
- [x] P2: Audit report created with severity ratings
- [x] P3: Critical and High findings resolved
- [x] All tests passing
- [x] Git history preserved (verified with `git log --follow`)
- [x] No uncommitted changes

---

## Troubleshooting

### Issue: Git mv not preserving history

**Symptom**: `git log --follow` doesn't show pre-rename history

**Solution**:
```bash
# Ensure you used git mv, not mv + git add
# If you used mv, undo and use git mv:
git reset HEAD~1
git checkout -- .
git mv old_name.py new_name.py
git commit -m "Rename: ..."
```

### Issue: Tests failing after rename

**Symptom**: pytest shows import errors or missing modules

**Solution**:
```bash
# Search for old module name in imports
grep -r "old_module_name" src/ tests/

# Update all imports
# Re-run tests
uv run pytest
```

### Issue: References in documentation outdated

**Symptom**: Links to renamed files are broken

**Solution**:
```bash
# Search for old file references
grep -r "old_doc.md" docs/ README.md

# Update all markdown links
# Verify links work
```

---

## Next Steps

After completing this feature:

1. **Merge to main**:
   ```bash
   git checkout main
   git merge 002-structure-standards
   git push origin main
   ```

2. **Apply standards to future work**:
   - Consult constitution.md before creating new files
   - Use naming patterns in code reviews
   - Enforce via pre-commit hooks (future enhancement)

3. **Re-audit periodically**:
   - After major feature merges
   - Before releases
   - Quarterly reviews

---

## Support

**Questions or Issues?**
- Review [spec.md](spec.md) for requirements
- Review [research.md](research.md) for rationale
- Check [data-model.md](data-model.md) for entity definitions
- Consult `.specify/memory/constitution.md` for final standards

**Feature Branch**: `002-structure-standards`
**Related Docs**: [plan.md](plan.md), [tasks.md](tasks.md)
