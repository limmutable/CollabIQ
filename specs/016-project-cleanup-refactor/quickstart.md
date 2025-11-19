# Quickstart Guide: Project Cleanup & Refactoring

**Branch**: `016-project-cleanup-refactor` | **Date**: 2025-11-18 | **Spec**: [spec.md](./spec.md)
**Purpose**: Step-by-step execution guide for Phase 016 cleanup operations
**Prerequisites**: [research.md](./research.md) and [data-model.md](./data-model.md) complete

---

## Overview

This guide provides the execution sequence for Phase 016 cleanup operations. Follow the phases in order, validating after each phase before proceeding.

**Estimated Total Time**: 8-12 hours (spread over 4-5 days)
**Risk Level**: Low (all operations backed up, regression tests validate)

---

## Pre-Cleanup Checklist

Before starting any cleanup operations:

- [ ] **Current branch**: Verify on `016-project-cleanup-refactor` branch
  ```bash
  git branch --show-current
  # Expected: 016-project-cleanup-refactor
  ```

- [ ] **Clean working directory**: No uncommitted changes
  ```bash
  git status
  # Expected: nothing to commit, working tree clean
  ```

- [ ] **Baseline tests passing**: Establish current test state
  ```bash
  uv run pytest --tb=short -v
  # Record: X tests passed, Y skipped
  # Expected pass rate: ≥98.9%
  ```

- [ ] **Baseline coverage**: Record current coverage
  ```bash
  uv run pytest --cov=collabiq --cov-report=term-missing
  # Record: Coverage percentage (expected ≥90%)
  ```

- [ ] **Create backup branch**: Safety net for rollback
  ```bash
  git branch 016-cleanup-backup
  ```

- [ ] **Create cleanup tracking directory**:
  ```bash
  mkdir -p .cleanup_backup
  echo ".cleanup_backup/" >> .gitignore
  ```

---

## Phase 1: Documentation Cleanup (Priority: P1)

**Estimated Time**: 3-4 hours
**Risk**: Low (documentation-only changes)

### 1.1 Quick Wins (30 minutes)

Execute low-risk, high-impact deletions:

#### Delete Meta-Documentation (5 minutes)
```bash
# Backup first
cp docs/PROJECT_STRUCTURE.md .cleanup_backup/
cp docs/REPOSITORY_OVERVIEW.md .cleanup_backup/

# Delete
rm docs/PROJECT_STRUCTURE.md
rm docs/REPOSITORY_OVERVIEW.md

# Verify
ls docs/*.md | wc -l
# Expected: 2 fewer files
```

**Rationale**: These are duplicates of specs/001-feasibility-architecture/ content.

#### Delete CLI Demo Doc (5 minutes)
```bash
# Backup first
cp docs/cli/CLI_DEMO_WALKTHROUGH.md .cleanup_backup/

# Delete
rm docs/cli/CLI_DEMO_WALKTHROUGH.md

# Verify
ls docs/cli/*.md
# Expected: Only ADMIN_GUIDE.md remains
```

**Rationale**: Outdated demo script, superseded by ADMIN_GUIDE.md.

#### Consolidate Test Results (10 minutes)
```bash
# Backup first
cp docs/testing/test-results-* .cleanup_backup/

# Keep only the consolidated report
mv docs/testing/test-results-consolidated.md docs/testing/TEST_RESULTS.md

# Delete duplicates
rm docs/testing/test-results-*.md

# Verify
ls docs/testing/*.md
# Expected: Only TEST_RESULTS.md for results
```

**Rationale**: 5 test result files → 1 consolidated file.

#### Streamline Root README (10 minutes)
```bash
# Backup first
cp README.md .cleanup_backup/

# Edit README.md to focus on quick links only
# Remove expanded content (defer to docs/)
```

**Edit target**: Reduce from 50+ lines to ~10 lines:
```markdown
# CollabIQ

AI-powered email processor that extracts structured data and syncs to Notion databases.

## Quick Links
- [Architecture & Roadmap](docs/architecture/ROADMAP.md)
- [Setup & Installation](docs/setup/QUICKSTART.md)
- [CLI Admin Guide](docs/cli/ADMIN_GUIDE.md)
- [Testing Guide](docs/testing/TEST_STRATEGY.md)

For detailed documentation, see [docs/](docs/).
```

**Checkpoint**:
```bash
# Count deleted files
echo "Deleted: 7 files (PROJECT_STRUCTURE.md, REPOSITORY_OVERVIEW.md, CLI_DEMO_WALKTHROUGH.md, 4 test-results-*.md)"

# Verify git status
git status
# Expected: 7 deletions, 1 modification (README.md)

# Commit
git add -A
git commit -m "Phase 016: Quick wins - delete 7 duplicate/obsolete docs, streamline README

- Delete PROJECT_STRUCTURE.md (duplicate of specs/001)
- Delete REPOSITORY_OVERVIEW.md (duplicate of specs/001)
- Delete CLI_DEMO_WALKTHROUGH.md (outdated)
- Consolidate 5 test result docs → 1 TEST_RESULTS.md
- Streamline README.md (50→10 lines, defer to docs/)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 1.2 Directory Restructure (60 minutes)

Create organized directory structure per [data-model.md](./data-model.md#11-directory-structure):

#### Create Directory Structure (5 minutes)
```bash
# Create category directories
mkdir -p docs/architecture
mkdir -p docs/setup
mkdir -p docs/cli
mkdir -p docs/testing
mkdir -p docs/validation

# Verify
tree docs/ -L 1
# Expected: 5 category directories
```

#### Move Files to Category Directories (20 minutes)
```bash
# Architecture (already in place)
ls docs/architecture/
# Expected: ROADMAP.md, CONSTITUTION.md, ARCHITECTURE.md

# Setup
mv docs/QUICKSTART.md docs/setup/ 2>/dev/null || true
mv docs/INSTALLATION.md docs/setup/ 2>/dev/null || true

# CLI
mv docs/ADMIN_GUIDE.md docs/cli/ 2>/dev/null || true
mv docs/COMMANDS.md docs/cli/ 2>/dev/null || true

# Testing
mv docs/testing/E2E_TESTING.md docs/testing/ 2>/dev/null || true
mv docs/testing/PERFORMANCE_TESTING.md docs/testing/ 2>/dev/null || true
mv docs/TEST_STRATEGY.md docs/testing/ 2>/dev/null || true

# Validation
mv docs/VALIDATION_METHODOLOGY.md docs/validation/ 2>/dev/null || true

# Verify
find docs/ -name "*.md" -type f | sort
# Expected: All docs in category directories
```

#### Create README Indexes (30 minutes)

**docs/README.md** (main index):
```markdown
# CollabIQ Documentation

**Purpose**: Comprehensive documentation for CollabIQ AI-powered email processor

## Quick Navigation

- **[Architecture & Design](architecture/)**: System design, principles, project roadmap
- **[Setup & Installation](setup/)**: Getting started, installation, configuration
- **[CLI Reference](cli/)**: Command-line interface and admin tools
- **[Testing](testing/)**: Test strategy, E2E testing, performance testing
- **[Validation](validation/)**: Quality assurance and validation methodology

## Getting Started

1. **New to CollabIQ?** Start with [Setup Quickstart](setup/QUICKSTART.md)
2. **Understanding the system?** Read [Architecture Overview](architecture/ARCHITECTURE.md)
3. **Running tests?** See [Testing Guide](testing/TEST_STRATEGY.md)
4. **Admin tasks?** Use [CLI Admin Guide](cli/ADMIN_GUIDE.md)

## Document Categories

### Architecture & Design
High-level system design, development principles, and project planning.

- [ARCHITECTURE.md](architecture/ARCHITECTURE.md): System design and component overview
- [ROADMAP.md](architecture/ROADMAP.md): Project phases, milestones, timeline
- [CONSTITUTION.md](architecture/CONSTITUTION.md): Development principles and standards

### Setup & Installation
Installation guides, configuration, and getting started.

- [QUICKSTART.md](setup/QUICKSTART.md): Fast setup guide (15 minutes)
- [INSTALLATION.md](setup/INSTALLATION.md): Detailed installation instructions

### CLI Reference
Command-line interface documentation and admin tools.

- [ADMIN_GUIDE.md](cli/ADMIN_GUIDE.md): Admin command reference
- [COMMANDS.md](cli/COMMANDS.md): Complete CLI command documentation

### Testing
Testing strategy, guides, and best practices.

- [TEST_STRATEGY.md](testing/TEST_STRATEGY.md): Overall testing approach
- [E2E_TESTING.md](testing/E2E_TESTING.md): End-to-end testing with Gmail/Notion
- [PERFORMANCE_TESTING.md](testing/PERFORMANCE_TESTING.md): Performance testing guide
- [TEST_RESULTS.md](testing/TEST_RESULTS.md): Latest test execution results

### Validation
Quality assurance processes and validation methodology.

- [VALIDATION_METHODOLOGY.md](validation/VALIDATION_METHODOLOGY.md): QA processes

## Related Documentation

- **Feature Specifications**: See [specs/](../specs/) for phase-specific design artifacts
- **Source Code**: See [src/](../src/) for implementation details

---

*Documentation Version: 2.0 (Phase 016 reorganization)*
*Last Updated: 2025-11-18*
```

**Create this file**:
```bash
cat > docs/README.md << 'EOF'
[paste content above]
EOF
```

**Repeat for each category directory**:
- `docs/architecture/README.md`
- `docs/setup/README.md`
- `docs/cli/README.md`
- `docs/testing/README.md`
- `docs/validation/README.md`

**Templates**: Follow [data-model.md § 1.3](./data-model.md#13-readme-index-pattern) for structure.

#### Update Cross-References (5 minutes)

Run link checker and fix broken references:
```bash
# Find all markdown files
find docs/ -name "*.md" -type f > /tmp/docs_files.txt

# Check for common broken link patterns
grep -r "docs/[A-Z]" docs/ || echo "No absolute links to fix"

# Update links to use new structure
# Example: docs/TEST_STRATEGY.md → docs/testing/TEST_STRATEGY.md
```

**Checkpoint**:
```bash
# Verify structure
tree docs/ -L 2

# Expected structure:
# docs/
# ├── README.md (new main index)
# ├── architecture/
# │   ├── README.md (new)
# │   ├── ARCHITECTURE.md
# │   ├── CONSTITUTION.md
# │   └── ROADMAP.md
# ├── setup/
# │   ├── README.md (new)
# │   ├── QUICKSTART.md
# │   └── INSTALLATION.md
# ├── cli/
# │   ├── README.md (new)
# │   ├── ADMIN_GUIDE.md
# │   └── COMMANDS.md
# ├── testing/
# │   ├── README.md (new)
# │   ├── TEST_STRATEGY.md
# │   ├── E2E_TESTING.md
# │   ├── PERFORMANCE_TESTING.md
# │   └── TEST_RESULTS.md
# └── validation/
#     ├── README.md (new)
#     └── VALIDATION_METHODOLOGY.md

# Commit
git add docs/
git commit -m "Phase 016: Restructure documentation with category directories and indexes

- Create 5 category directories (architecture, setup, cli, testing, validation)
- Move 17 docs to appropriate categories
- Create README index for each category
- Create master docs/README.md with navigation
- Update cross-references to new structure

Target: Find any doc in <1 minute via clear navigation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 1.3 Validation (15 minutes)

```bash
# Check documentation links
find docs/ -name "*.md" -exec grep -H "\[.*\](.*/.*)" {} \; > /tmp/doc_links.txt
# Manually verify no broken links

# Count final files
find docs/ -name "*.md" -type f | wc -l
# Expected: ≤27 files (target met)

# Git status
git status
# Expected: Clean working tree (all changes committed)
```

**Success Criteria** (from [spec.md](./spec.md)):
- ✅ Documentation audit complete with clear categorization
- ✅ No duplicate documentation remains (7 deleted)
- ✅ Documentation hierarchy established (5 categories + indexes)
- ✅ Navigation time: <1 minute to find any doc (via indexes)

**If validation fails**: Rollback to 016-cleanup-backup branch and review.

---

## Phase 2: Test Suite Reorganization (Priority: P2)

**Estimated Time**: 4-5 hours
**Risk**: Medium (affects test execution, but regression tests validate)

### 2.1 Baseline Test Execution (15 minutes)

```bash
# Run all tests and record results
uv run pytest --tb=short -v --duration=20 > .cleanup_backup/baseline_tests.txt 2>&1

# Record key metrics
grep "passed" .cleanup_backup/baseline_tests.txt
# Expected: ~727 passed (98.9%+ pass rate)

# Record slowest tests
grep "slowest" .cleanup_backup/baseline_tests.txt
# Note: Use this to prioritize test consolidation
```

---

### 2.2 Content Normalizer Consolidation (60 minutes)

**Target**: 4 files → 2 files, 30 tests → 20 tests (-33%)

#### Create Consolidated Test Files

**Step 1**: Create `tests/unit/content_normalizer/test_signature.py`
```bash
# Backup originals
cp tests/unit/content_normalizer/test_signature_detection.py .cleanup_backup/
cp tests/unit/content_normalizer/test_signature_accuracy.py .cleanup_backup/

# Create new consolidated file
cat > tests/unit/content_normalizer/test_signature.py << 'EOF'
"""
Consolidated signature detection and accuracy tests.

Combines:
- test_signature_detection.py (14 tests, 313 lines)
- test_signature_accuracy.py (3 tests, 356 lines)

Result: 12 tests (~400 lines) - removed 5 redundant tests
"""
import pytest
from collabiq.content_normalizer import SignatureDetector

# [Copy non-redundant test cases from both files]
# [Merge accuracy checks into detection tests where logical]
EOF
```

**Step 2**: Create `tests/unit/content_normalizer/test_quoted_thread.py`
```bash
# Backup originals
cp tests/unit/content_normalizer/test_quoted_thread_detection.py .cleanup_backup/
cp tests/unit/content_normalizer/test_quoted_thread_accuracy.py .cleanup_backup/

# Create new consolidated file
cat > tests/unit/content_normalizer/test_quoted_thread.py << 'EOF'
"""
Consolidated quoted thread detection and accuracy tests.

Combines:
- test_quoted_thread_detection.py (10 tests, 256 lines)
- test_quoted_thread_accuracy.py (3 tests, 348 lines)

Result: 8 tests (~400 lines) - removed 5 redundant tests
"""
import pytest
from collabiq.content_normalizer import QuotedThreadDetector

# [Copy non-redundant test cases from both files]
# [Merge accuracy checks into detection tests where logical]
EOF
```

**Step 3**: Delete Original Files
```bash
# Delete originals (already backed up)
rm tests/unit/content_normalizer/test_signature_detection.py
rm tests/unit/content_normalizer/test_signature_accuracy.py
rm tests/unit/content_normalizer/test_quoted_thread_detection.py
rm tests/unit/content_normalizer/test_quoted_thread_accuracy.py

# Verify
ls tests/unit/content_normalizer/
# Expected: test_signature.py, test_quoted_thread.py, test_core.py
```

**Step 4**: Run Tests to Validate
```bash
# Run content_normalizer tests
uv run pytest tests/unit/content_normalizer/ -v

# Expected: ~20 tests passed (down from 30)
# Verify: No new failures introduced
```

**Checkpoint**:
```bash
# Commit
git add tests/unit/content_normalizer/
git commit -m "Phase 016: Consolidate content_normalizer tests (4→2 files, 30→20 tests)

- Merge test_signature_detection + test_signature_accuracy → test_signature.py
- Merge test_quoted_thread_detection + test_quoted_thread_accuracy → test_quoted_thread.py
- Remove 10 redundant tests while maintaining coverage
- Result: 33% test reduction, 98.9%+ pass rate maintained

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 2.3 Delete Obsolete Test Files (30 minutes)

**Target**: Remove 51 obsolete files identified in research.md

#### Validation Prototype Tests (5 files)
```bash
# Backup
cp -r tests/validation/prototypes/ .cleanup_backup/

# Delete
rm -rf tests/validation/prototypes/

# Verify
ls tests/validation/
# Expected: No prototypes/ directory
```

#### Notion Sandbox Tests (12 files)
```bash
# Backup
cp -r tests/integration/notion_sandbox/ .cleanup_backup/

# Delete
rm -rf tests/integration/notion_sandbox/

# Verify
ls tests/integration/
# Expected: No notion_sandbox/ directory
```

#### Duplicate Email Receiver Tests (6 files)
```bash
# Backup
cp tests/unit/email_receiver/test_gmail_*.py .cleanup_backup/

# Delete (keep only test_gmail_receiver.py)
rm tests/unit/email_receiver/test_gmail_auth.py
rm tests/unit/email_receiver/test_gmail_fetch.py
rm tests/unit/email_receiver/test_gmail_parse.py
# [repeat for other duplicates]

# Verify
ls tests/unit/email_receiver/
# Expected: Only consolidated test files remain
```

#### Continue for Remaining Obsolete Tests

Follow research.md Section 2.3 for complete list of 51 files to delete.

**Checkpoint**:
```bash
# Count deleted files
find .cleanup_backup/tests/ -type f | wc -l
# Expected: 51 files backed up

# Run full test suite
uv run pytest --tb=short -v

# Expected: ~580 tests passed (down from 735, -21%)
# Verify: Pass rate ≥98.9%

# Commit
git add tests/
git commit -m "Phase 016: Delete 51 obsolete test files

Categories deleted:
- Validation prototypes (5 files)
- Notion sandbox tests (12 files)
- Duplicate email receiver tests (6 files)
- Legacy LLM adapter tests (8 files)
- [etc. - list all categories]

Result: 735→580 tests (-21%), maintaining 98.9%+ pass rate

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 2.4 Reorganize Test Directory Structure (90 minutes)

#### Create Category Structure
```bash
# Create unit test component directories
mkdir -p tests/unit/content_normalizer
mkdir -p tests/unit/email_receiver
mkdir -p tests/unit/llm_adapters
mkdir -p tests/unit/notion_integrator

# Verify
tree tests/ -L 2
```

#### Move Files to Component Directories

**Note**: Most files are already in place. Focus on stragglers:

```bash
# Find misplaced files
find tests/unit/ -maxdepth 1 -name "*.py" -type f

# Move to appropriate component directories
# (Example - adjust based on actual misplacements)
mv tests/unit/test_email_*.py tests/unit/email_receiver/ 2>/dev/null || true
mv tests/unit/test_notion_*.py tests/unit/notion_integrator/ 2>/dev/null || true
```

#### Create Test README Files

**tests/README.md**:
```markdown
# CollabIQ Test Suite

**Purpose**: Comprehensive test suite for CollabIQ components

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific category
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/

# Run with coverage
uv run pytest --cov=collabiq --cov-report=html

# Run performance tests
uv run pytest tests/performance/ --benchmark-only
```

## Test Organization

- [unit/](unit/): Isolated component tests (fast, no external deps)
- [integration/](integration/): Multi-component interaction tests
- [e2e/](e2e/): End-to-end scenarios with real APIs
- [performance/](performance/): Load, stress, latency benchmarks
- [fuzz/](fuzz/): Randomized input testing
- [contract/](contract/): External API contract validation
- [manual/](manual/): Manual test scripts and procedures

## Test Utilities

Shared test utilities are in `src/collabiq/test_utils/`:
- `fixtures.py`: Pytest fixtures for test data
- `mocks.py`: Mock implementations of external services
- `assertions.py`: Custom assertion helpers

See [Testing Guide](../docs/testing/TEST_STRATEGY.md) for detailed information.
```

**Create this file**:
```bash
cat > tests/README.md << 'EOF'
[paste content above]
EOF
```

**Repeat for each category**: Create README.md in tests/unit/, tests/integration/, tests/e2e/, etc. following [data-model.md § 2.1](./data-model.md#21-test-directory-structure).

#### Clean Up Test Utilities

```bash
# Move test utilities from tests/ to src/collabiq/test_utils/
# (If any are misplaced in tests/ directory)

# Verify final structure
tree src/collabiq/test_utils/
# Expected:
# src/collabiq/test_utils/
# ├── __init__.py
# ├── fixtures.py
# ├── mocks.py
# └── assertions.py
```

**Checkpoint**:
```bash
# Run full test suite
uv run pytest --tb=short -v

# Expected: All tests pass, organized structure
# Verify: Test discovery works correctly

# Commit
git add tests/
git commit -m "Phase 016: Reorganize test directory structure

- Create component-specific directories under tests/unit/
- Create README indexes for each test category
- Move test utilities to src/collabiq/test_utils/ (if needed)
- Establish clear separation: unit/integration/e2e/performance/fuzz

Result: Clear test hierarchy, easier navigation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 2.5 Validation (30 minutes)

```bash
# Run full test suite
uv run pytest --tb=short -v -x > .cleanup_backup/phase2_final_tests.txt 2>&1

# Check test count
grep "passed" .cleanup_backup/phase2_final_tests.txt
# Expected: ≤580 tests passed (target: ≥20% reduction from 735)

# Check pass rate
# Expected: ≥98.9%

# Check coverage
uv run pytest --cov=collabiq --cov-report=term-missing
# Expected: ≥90% coverage maintained

# Compare execution time
# Baseline: (from 2.1 baseline_tests.txt)
# Current: (from phase2_final_tests.txt)
# Expected: ≥15% faster for unit/integration suites
```

**Success Criteria** (from [spec.md](./spec.md)):
- ✅ Test suite reduced by ≥20% (735→580 tests = 21%)
- ✅ All tests pass after reorganization (98.9%+ pass rate)
- ✅ Test organization clear (unit/integration/e2e/performance/fuzz)
- ✅ Test coverage maintained (≥90%)

**If validation fails**: Review test failures, restore from .cleanup_backup/, fix issues, re-run validation.

---

## Phase 3: CLI Application Polish (Priority: P3)

**Estimated Time**: 2-3 hours
**Risk**: Low (UX improvements, no breaking changes)

### 3.1 Startup Optimization (45 minutes)

#### Remove Eager Imports

Edit `src/collabiq/cli/__init__.py`:

**Before**:
```python
# Current (SLOW): Eager imports
from collabiq import date_parser
from collabiq import llm_benchmarking
from collabiq import test_utils
```

**After**:
```python
# Optimized (FAST): Lazy imports
# Import only when needed in specific commands
# date_parser imported in date-related commands
# llm_benchmarking imported in benchmark commands
# test_utils imported in test commands
```

**Measure improvement**:
```bash
# Before
time uv run collabiq --version
# Expected: 260-620ms

# After optimization
time uv run collabiq --version
# Target: 150-300ms (50% improvement)
```

#### Implement Minimal Startup Checks

Edit `src/collabiq/cli/main.py`:

```python
@app.callback()
def main(ctx: typer.Context):
    """
    CollabIQ CLI - AI-powered email processor

    Run 'collabiq --help' for available commands.
    """
    # Minimal startup check (only if command requires it)
    if ctx.invoked_subcommand not in ["version", "help", "--help", "-h"]:
        # Defer heavy checks to command execution
        pass
```

**Checkpoint**:
```bash
# Test startup time
time uv run collabiq --version
time uv run collabiq status
time uv run collabiq admin list-commands

# Expected: All <300ms

# Commit
git add src/collabiq/cli/
git commit -m "Phase 016: Optimize CLI startup time (260-620ms → 150-300ms)

- Remove eager imports (date_parser, llm_benchmarking, test_utils)
- Use lazy imports in specific commands
- Defer heavy checks to command execution
- Keep --version and --help fast

Result: 50% startup improvement, <2s target achieved

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 3.2 Error Message Standardization (60 minutes)

Implement error taxonomy from [data-model.md § 3](./data-model.md#3-cli-error-taxonomy):

#### Create Error Module

```bash
# Create error handling module
cat > src/collabiq/cli/errors.py << 'EOF'
"""
CLI error handling and standardized error messages.

Error codes follow taxonomy:
- AUTH_XXX: Authentication/authorization
- CONFIG_XXX: Configuration errors
- INPUT_XXX: Invalid user input
- STATE_XXX: Invalid system state
- API_XXX: External API failures
- DATA_XXX: Data validation errors
- SYSTEM_XXX: System-level errors
"""
from enum import Enum
from typing import List, Optional
from rich.console import Console

console = Console()

class ErrorCode(str, Enum):
    """Standard error codes."""
    AUTH_001 = "AUTH_001"  # Missing credentials
    AUTH_002 = "AUTH_002"  # Invalid API key
    CONFIG_001 = "CONFIG_001"  # Invalid configuration
    # [Add remaining error codes per data-model.md]

def show_error(
    code: ErrorCode,
    message: str,
    details: Optional[str] = None,
    fixes: Optional[List[str]] = None,
    docs_link: Optional[str] = None
) -> None:
    """
    Display standardized error message.

    Args:
        code: Error code from ErrorCode enum
        message: Brief error description
        details: Detailed explanation
        fixes: List of remediation steps
        docs_link: Link to relevant documentation
    """
    console.print(f"\n[bold red]❌ {code}: {message}[/bold red]\n")

    if details:
        console.print(f"{details}\n")

    if fixes:
        console.print("[bold cyan]💡 Suggested fixes:[/bold cyan]")
        for i, fix in enumerate(fixes, 1):
            console.print(f"  {i}. {fix}")
        console.print()

    if docs_link:
        console.print(f"[dim]📚 Documentation: {docs_link}[/dim]\n")

# Example usage:
# show_error(
#     ErrorCode.AUTH_001,
#     "Missing credentials",
#     "Could not find .env file with required API credentials.",
#     fixes=[
#         "Copy .env.example to .env: cp .env.example .env",
#         "Add your API keys to .env (see setup guide)",
#         "Verify .env is in project root (not in src/)"
#     ],
#     docs_link="docs/setup/QUICKSTART.md#credentials"
# )
EOF
```

#### Update Commands to Use Standard Errors

Edit CLI commands to use `show_error()`:

```python
# Before
if not api_key:
    print("Error: Missing API key")
    sys.exit(1)

# After
if not api_key:
    from collabiq.cli.errors import show_error, ErrorCode
    show_error(
        ErrorCode.AUTH_002,
        "Invalid API key",
        "The provided API key could not authenticate with the service.",
        fixes=[
            "Check .env file for correct API key format",
            "Verify API key is active in provider dashboard",
            "Regenerate API key if expired"
        ],
        docs_link="docs/setup/QUICKSTART.md#api-keys"
    )
    raise typer.Exit(1)
```

**Checkpoint**:
```bash
# Test error messages
uv run collabiq admin status
# (Trigger various errors to see formatted output)

# Commit
git add src/collabiq/cli/
git commit -m "Phase 016: Standardize CLI error messages with error codes

- Create errors.py module with ErrorCode enum
- Implement show_error() with standard format
- Update commands to use standardized errors
- Add error codes: AUTH_001, AUTH_002, CONFIG_001, etc.

Result: Clear error messages with remediation steps

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 3.3 Interactive Prompts (45 minutes)

Add interactive prompts for common admin tasks:

#### Example: Interactive Credential Check

Edit `src/collabiq/cli/admin.py`:

```python
from rich.prompt import Confirm, Prompt

@app.command()
def check_credentials():
    """
    Interactively check and validate API credentials.
    """
    console.print("[bold cyan]🔍 Credential Validation[/bold cyan]\n")

    # Check .env file
    if not Path(".env").exists():
        create = Confirm.ask(
            "[yellow]⚠️  No .env file found. Create from template?[/yellow]"
        )
        if create:
            import shutil
            shutil.copy(".env.example", ".env")
            console.print("[green]✅ Created .env from template[/green]")
            console.print("[dim]Edit .env to add your API keys[/dim]\n")
        else:
            console.print("[dim]Operation cancelled[/dim]")
            return

    # Validate each credential
    from collabiq.cli.status import check_gmail_credentials, check_notion_credentials

    results = {}
    results["Gmail"] = check_gmail_credentials()
    results["Notion"] = check_notion_credentials()
    # [etc.]

    # Display results
    console.print("\n[bold]📊 Credential Status:[/bold]\n")
    for service, status in results.items():
        icon = "✅" if status else "❌"
        console.print(f"{icon} {service}: {'Valid' if status else 'Invalid'}")
```

**Checkpoint**:
```bash
# Test interactive features
uv run collabiq admin check-credentials
# (Follow prompts)

# Commit
git add src/collabiq/cli/
git commit -m "Phase 016: Add interactive prompts for admin commands

- Add Confirm prompts for destructive operations
- Add Prompt for user input collection
- Add progress indicators for long operations
- Enhance check-credentials with interactive flow

Result: Better admin UX with clear feedback

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 3.4 Enhanced Status Command (30 minutes)

Improve `collabiq admin status` output per [data-model.md § 3.5](./data-model.md#35-help-text-standards):

```python
@app.command()
def status():
    """
    Show comprehensive system health status with actionable feedback.
    """
    console.print("\n[bold cyan]🔍 CollabIQ Status Check[/bold cyan]\n")

    # Configuration
    config_status = check_configuration()
    console.print(f"{'✅' if config_status['valid'] else '❌'} [bold]Configuration:[/bold] {config_status['message']}")
    for detail in config_status['details']:
        console.print(f"   • {detail}")

    # Credentials
    cred_status = check_credentials()
    console.print(f"\n{'✅' if cred_status['valid'] else '❌'} [bold]Credentials:[/bold] {cred_status['message']}")
    for detail in cred_status['details']:
        console.print(f"   • {detail}")

    # Notion Schema
    schema_status = check_notion_schema()
    icon = "✅" if schema_status['valid'] else "⚠️"
    console.print(f"\n{icon} [bold]Notion Schema:[/bold] {schema_status['message']}")
    for detail in schema_status['details']:
        console.print(f"   • {detail}")

    # Suggested actions
    if schema_status['action']:
        console.print(f"\n[bold cyan]💡 Suggested action:[/bold cyan] {schema_status['action']}")

    # Overall health
    total_checks = 3
    passed_checks = sum([config_status['valid'], cred_status['valid'], schema_status['valid']])
    console.print(f"\n[bold]📊 System Health:[/bold] {passed_checks}/{total_checks} checks passed")
```

**Checkpoint**:
```bash
# Test enhanced status
uv run collabiq admin status
# Expected: Clear, actionable status output

# Commit
git add src/collabiq/cli/
git commit -m "Phase 016: Enhance status command with actionable feedback

- Add structured status output with icons
- Include suggested actions for issues
- Show overall health score
- Provide clear next steps

Result: Status command is informative and actionable

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### 3.5 Validation (15 minutes)

```bash
# Test CLI commands
uv run collabiq --version
# Expected: <300ms startup

uv run collabiq --help
# Expected: Clear help text

uv run collabiq admin status
# Expected: Enhanced status output with actionable feedback

uv run collabiq admin check-credentials
# Expected: Interactive prompt flow

# Verify no breaking changes
uv run pytest tests/unit/cli/ -v
# Expected: All CLI tests pass
```

**Success Criteria** (from [spec.md](./spec.md)):
- ✅ CLI startup time <2 seconds (achieved: <300ms)
- ✅ Admin commands have clear help text
- ✅ Error messages include remediation steps
- ✅ Interactive prompts for common tasks
- ✅ Status command provides actionable feedback

---

## Final Validation

**Before merging to main**, run comprehensive validation:

### Regression Testing
```bash
# Run full test suite
uv run pytest --tb=short -v

# Expected results:
# - ≤580 tests (down from 735, -21%)
# - ≥98.9% pass rate (maintained)
# - ≥90% coverage (maintained)
```

### Documentation Validation
```bash
# Count documentation files
find docs/ -name "*.md" -type f | wc -l
# Expected: ≤27 files (down from 34, -21%)

# Verify no duplicate docs
# Manual audit: Check that no duplicate content remains

# Test documentation navigation
# Manual test: Find 3 random docs using indexes
# Expected: <1 minute per doc
```

### CLI Validation
```bash
# Test startup time
for i in {1..5}; do time uv run collabiq --version; done
# Expected: All runs <300ms

# Test all admin commands
uv run collabiq admin --help
# Manual test: Try each command, verify help text and functionality
```

### Git Status
```bash
# Verify clean state
git status
# Expected: All changes committed

# Review commit history
git log --oneline 016-cleanup-backup..HEAD
# Expected: Clear commit messages documenting each phase
```

---

## Success Criteria Checklist

From [spec.md](./spec.md) Success Criteria:

- [ ] **SC-001**: Documentation findable in <1 minute via indexes
- [ ] **SC-002**: Zero duplicate documentation (7 duplicates removed)
- [ ] **SC-003**: Clear documentation hierarchy (5 categories + indexes)
- [ ] **SC-004**: Test suite reduced ≥20% (735→580 tests = 21%)
- [ ] **SC-005**: All tests pass (≥98.9% pass rate maintained)
- [ ] **SC-006**: CLI startup <2 seconds (achieved <300ms)
- [ ] **SC-007**: Error messages include remediation steps (standardized)
- [ ] **SC-008**: Admin commands have clear help text
- [ ] **SC-009**: Status check provides actionable feedback
- [ ] **SC-010**: Test coverage maintained (≥90%)

**All criteria must pass before merging to main.**

---

## Merge to Main

Once all validation passes:

```bash
# Switch to main
git checkout main

# Pull latest changes
git pull origin main

# Merge cleanup branch
git merge --no-ff 016-project-cleanup-refactor -m "Phase 016: Project Cleanup & Refactoring

Comprehensive cleanup across documentation, tests, and CLI:

Documentation (34→27 files, -21%):
- Deleted 7 duplicate/obsolete docs
- Restructured into 5 categories with README indexes
- Navigation time: <1 minute to find any doc

Test Suite (735→580 tests, -21%):
- Consolidated redundant tests (content_normalizer: 4→2 files)
- Deleted 51 obsolete test files
- Maintained 98.9%+ pass rate and ≥90% coverage
- Organized: unit/integration/e2e/performance/fuzz

CLI (260-620ms → <300ms startup):
- Removed eager imports for 50% startup improvement
- Standardized error messages with error codes
- Added interactive prompts for admin tasks
- Enhanced status command with actionable feedback

All success criteria met. Ready for Phase 017.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin main

# Delete cleanup branch (optional)
git branch -d 016-project-cleanup-refactor
git push origin --delete 016-project-cleanup-refactor

# Delete backup branch
git branch -D 016-cleanup-backup
```

---

## Rollback Procedure

If validation fails and cleanup must be rolled back:

```bash
# Switch to backup branch
git checkout 016-cleanup-backup

# Create new branch from backup
git checkout -b 016-project-cleanup-refactor-v2

# Review what went wrong
git diff 016-cleanup-backup 016-project-cleanup-refactor

# Restore specific files if needed
git checkout 016-cleanup-backup -- [file-path]

# Re-apply cleanup operations with fixes
# [Follow quickstart guide again with corrections]
```

---

## Post-Cleanup Tasks

After merging to main:

1. **Update ROADMAP.md**: Mark Phase 016 as complete
2. **Clean up .cleanup_backup/**: Archive or delete backup directory
3. **Update team documentation**: Notify team of new structure
4. **Phase 017 Planning**: Begin next phase planning

---

**Guide Version**: 1.0
**Last Updated**: 2025-11-18
**Estimated Total Time**: 8-12 hours over 4-5 days
**Status**: Ready for execution

