# Data Model: Project Cleanup & Refactoring

**Branch**: `016-project-cleanup-refactor` | **Date**: 2025-11-18 | **Spec**: [spec.md](./spec.md)
**Purpose**: Define organization schemas and taxonomies for cleanup operations
**Input**: Research findings from [research.md](./research.md)

## Overview

This document defines the structural frameworks for organizing documentation, tests, and CLI components during Phase 016 cleanup. These schemas guide consolidation decisions and establish patterns for future development.

---

## 1. Documentation Organization Schema

### 1.1 Directory Structure

```text
docs/
├── README.md                      # Primary entry point - navigation index
├── architecture/                  # System design and structure
│   ├── README.md                  # Architecture overview index
│   ├── ROADMAP.md                 # Project phases and milestones
│   ├── CONSTITUTION.md            # Development principles
│   └── ARCHITECTURE.md            # System design document
├── setup/                         # Installation and configuration
│   ├── README.md                  # Setup guide index
│   ├── QUICKSTART.md              # Fast start guide
│   └── INSTALLATION.md            # Detailed installation
├── cli/                           # CLI usage and reference
│   ├── README.md                  # CLI documentation index
│   ├── ADMIN_GUIDE.md             # Admin command reference
│   └── COMMANDS.md                # Command-line interface guide
├── testing/                       # Testing documentation
│   ├── README.md                  # Testing guide index
│   ├── TEST_STRATEGY.md           # Testing approach and coverage
│   ├── E2E_TESTING.md             # End-to-end test guide
│   └── PERFORMANCE_TESTING.md     # Performance test guide
└── validation/                    # Quality and validation
    ├── README.md                  # Validation guide index
    └── VALIDATION_METHODOLOGY.md  # Quality assurance processes

specs/                             # Feature specifications (unchanged)
├── 001-feasibility-architecture/  # Historical phase docs
├── 002-email-reception/
├── ...
└── 016-project-cleanup-refactor/  # Current phase
```

### 1.2 Documentation Types

| Type | Purpose | Location | Lifecycle |
|------|---------|----------|-----------|
| **Architecture** | System design, principles, roadmap | `docs/architecture/` | Long-term (rarely changes) |
| **Setup** | Installation, configuration, quickstart | `docs/setup/` | Stable (update on version changes) |
| **CLI** | Command reference, admin guides | `docs/cli/` | Active (update with CLI changes) |
| **Testing** | Test strategy, guides for test types | `docs/testing/` | Active (evolves with testing practices) |
| **Validation** | Quality processes, checklists | `docs/validation/` | Stable (established patterns) |
| **Feature Specs** | Phase-specific design artifacts | `specs/{phase}/` | Immutable after phase completion |

### 1.3 README Index Pattern

Each directory README follows this structure:

```markdown
# [Category] Documentation

**Purpose**: [One-sentence category description]

## Quick Links

- **[Primary Doc Name]**: [One-sentence description] - [relative/path.md](relative/path.md)
- **[Secondary Doc Name]**: [One-sentence description] - [relative/path.md](relative/path.md)

## Document Overview

### [Document Category 1]

- [doc-name.md](doc-name.md): [Brief description of content and when to use it]

### [Document Category 2]

- [doc-name.md](doc-name.md): [Brief description of content and when to use it]

## Related Documentation

- See [../other-category/](../other-category/) for [related content]
```

### 1.4 Cross-Reference Conventions

**Internal References** (within docs/):
```markdown
See [Architecture Overview](../architecture/ARCHITECTURE.md) for system design.
```

**Spec References** (to specs/):
```markdown
Implementation details: [Phase 015 Spec](../../specs/015-test-suite-improvements/spec.md)
```

**Code References** (to src/):
```markdown
Implementation: [email_receiver.py](../../src/email_receiver/receiver.py:42-67)
```

### 1.5 Consolidation Rules

**Merge documents when**:
- Two documents cover >70% overlapping content
- Documents serve the same user need/scenario
- Combined document would be <500 lines
- No loss of important detail from merging

**Keep separate when**:
- Documents serve different user personas (developer vs. admin)
- Documents cover different lifecycle stages (setup vs. maintenance)
- Content complexity requires focused treatment
- Documents have different update frequencies

**Archive rather than delete when**:
- Document is outdated but has historical value
- Document describes deprecated but still-present code
- Uncertainty about future relevance

### 1.6 Update/Archive Decision Matrix

| Condition | Action | Location |
|-----------|--------|----------|
| Current, canonical, well-maintained | Keep | `docs/{category}/` |
| Duplicate of existing content | Delete | (Remove) |
| Outdated but repairable | Update | `docs/{category}/` |
| Outdated, historical value | Archive | `docs/archive/` |
| Obsolete, no value | Delete | (Remove) |

---

## 2. Test Organization Schema

### 2.1 Test Directory Structure

```text
tests/
├── README.md                      # Test suite overview and running guide
├── unit/                          # Isolated component tests
│   ├── README.md                  # Unit testing conventions
│   ├── content_normalizer/        # Component-specific tests
│   │   ├── test_core.py           # Core functionality
│   │   ├── test_signature.py      # Signature detection + accuracy
│   │   └── test_quoted_thread.py  # Quoted thread detection + accuracy
│   ├── email_receiver/
│   ├── llm_adapters/
│   └── notion_integrator/
├── integration/                   # Multi-component interaction tests
│   ├── README.md                  # Integration testing guide
│   ├── test_email_to_extraction.py
│   ├── test_llm_to_notion.py
│   └── test_end_to_end_flow.py
├── e2e/                           # End-to-end user scenarios
│   ├── README.md                  # E2E testing setup and credentials
│   ├── test_gmail_notion_flow.py
│   └── conftest.py                # E2E fixtures
├── performance/                   # Load, stress, latency tests
│   ├── README.md                  # Performance testing guide
│   ├── test_notion_pagination.py
│   └── test_llm_batch_processing.py
├── fuzz/                          # Randomized input testing
│   ├── README.md                  # Fuzz testing methodology
│   └── test_email_content_fuzz.py
├── contract/                      # API contract validation
│   ├── README.md                  # Contract testing approach
│   ├── test_notion_api_contracts.py
│   └── test_gmail_api_contracts.py
├── manual/                        # Manual test scripts
│   ├── README.md                  # Manual testing procedures
│   └── [ad-hoc test scripts]
├── fixtures/                      # Shared test data
│   ├── emails/                    # Sample email data
│   ├── notion_responses/          # Mock Notion API responses
│   └── llm_responses/             # Mock LLM responses
└── conftest.py                    # Global pytest configuration

src/collabiq/test_utils/           # Test utilities (importable code)
├── __init__.py
├── fixtures.py                    # Pytest fixtures
├── mocks.py                       # Mock objects
└── assertions.py                  # Custom assertion helpers
```

### 2.2 Test Categorization Rules

| Test Type | Purpose | Characteristics | Execution |
|-----------|---------|-----------------|-----------|
| **Unit** | Test single function/class in isolation | Fast (<0.1s), no external deps, mocked I/O | Every commit |
| **Integration** | Test component interactions | Moderate speed (0.1-2s), may use test DB/APIs | Pre-push |
| **E2E** | Test complete user scenarios | Slow (2-10s), real APIs (Gmail/Notion), requires credentials | Pre-merge |
| **Performance** | Measure speed/throughput under load | Variable (10s-60s), benchmarking focus | Weekly/on-demand |
| **Fuzz** | Test with randomized/malformed inputs | Variable (5-30s), edge case discovery | Weekly/on-demand |
| **Contract** | Validate external API assumptions | Moderate (1-5s), real API calls | Weekly/API version changes |
| **Manual** | Human-executed validation scripts | Not automated, exploratory testing | As needed |

### 2.3 Test File Naming Conventions

**Unit tests**:
```
test_{module_name}.py              # General module tests
test_{feature}_core.py             # Core functionality
test_{feature}_{aspect}.py         # Specific aspect (detection, validation, etc.)
```

**Integration tests**:
```
test_{component1}_to_{component2}.py    # Two-component integration
test_{feature}_flow.py                  # Multi-component flow
```

**E2E tests**:
```
test_{service1}_{service2}_flow.py      # External service integration
test_{user_scenario}_e2e.py             # User-facing scenario
```

**Performance tests**:
```
test_{component}_{metric}.py            # Specific metric (latency, throughput)
test_{scenario}_load.py                 # Load testing scenario
```

### 2.4 Test Consolidation Criteria

**Redundant tests** (consolidate or delete):
- Two tests with identical setup and assertions
- "Detection" + "Accuracy" tests for same feature (merge → single file)
- Multiple tests of same edge case with minor input variations
- Overlapping integration tests covering same component interaction

**Keep separate when**:
- Tests cover different aspects (happy path vs. error handling)
- Tests have different performance characteristics (fast unit vs. slow integration)
- Tests require different fixtures or credentials
- Tests belong to different categories (unit vs. integration)

**Merge criteria**:
```python
# Before: 2 files, 14 tests total
# test_signature_detection.py (14 tests, 313 lines)
# test_signature_accuracy.py (3 tests, 356 lines)

# After: 1 file, 12 tests total (-2 redundant tests)
# test_signature.py (12 tests, ~400 lines)
#   - Detection tests (12 tests: basic + edge cases)
#   - Accuracy measurement integrated with detection tests
```

### 2.5 Test Utility Organization

**Location**: `src/collabiq/test_utils/` (not `tests/`)

**Modules**:
- `fixtures.py`: Pytest fixtures for reusable test data/objects
- `mocks.py`: Mock implementations of external services
- `assertions.py`: Custom assertion helpers
- `factories.py`: Test data factories (if needed)

**Usage pattern**:
```python
# In test file
from collabiq.test_utils.fixtures import sample_email_data
from collabiq.test_utils.mocks import MockNotionClient
from collabiq.test_utils.assertions import assert_valid_extraction
```

---

## 3. CLI Error Taxonomy

### 3.1 Error Code Structure

**Format**: `{CATEGORY}_{SEQUENCE}`

**Categories**:
- `AUTH`: Authentication/authorization failures
- `CONFIG`: Configuration errors
- `INPUT`: Invalid user input
- `STATE`: Invalid system state
- `API`: External API failures
- `DATA`: Data validation/integrity errors
- `SYSTEM`: System-level errors (filesystem, network)

**Example codes**:
```
AUTH_001: Missing credentials (.env file not found)
AUTH_002: Invalid API key (authentication failed)
CONFIG_001: Invalid configuration value
CONFIG_002: Missing required configuration
INPUT_001: Invalid command-line argument
INPUT_002: Missing required parameter
STATE_001: Database not initialized
STATE_002: Service not running
API_001: Notion API rate limit exceeded
API_002: Gmail API authentication expired
DATA_001: Invalid email format
DATA_002: Schema validation failed
SYSTEM_001: Insufficient disk space
SYSTEM_002: Network connection failed
```

### 3.2 Error Message Format

**Standard structure**:
```
❌ {ERROR_CODE}: {Brief description}

{Detailed explanation of what went wrong}

💡 Suggested fixes:
  1. {First remediation step}
  2. {Second remediation step}
  3. {Third remediation step (if applicable)}

📚 Documentation: {Link to relevant docs}
```

**Example**:
```
❌ AUTH_001: Missing credentials

Could not find .env file with required API credentials. The CLI requires Gmail, Notion, and LLM API keys to function.

💡 Suggested fixes:
  1. Copy .env.example to .env: cp .env.example .env
  2. Add your API keys to .env (see setup guide)
  3. Verify .env is in project root (not in src/)

📚 Documentation: docs/setup/QUICKSTART.md#credentials
```

### 3.3 Error Severity Levels

| Level | Code Prefix | User Impact | Handling |
|-------|-------------|-------------|----------|
| **Critical** | `CRIT_` | Cannot proceed, data loss risk | Exit immediately, show error + docs |
| **Error** | `ERR_` | Command fails, no side effects | Show error + fixes, exit gracefully |
| **Warning** | `WARN_` | Suboptimal but functional | Show warning, continue execution |
| **Info** | `INFO_` | Informational only | Show info, continue execution |

### 3.4 Interactive Prompt Patterns

**Confirmation prompts**:
```python
# Pattern
confirm = Confirm.ask(f"[bold yellow]⚠️  {action_description}. Continue?[/bold yellow]")
if not confirm:
    console.print("[dim]Operation cancelled.[/dim]")
    return
```

**Selection prompts**:
```python
# Pattern
choices = ["Option 1", "Option 2", "Option 3"]
selection = Prompt.ask(
    "[bold cyan]Select an option[/bold cyan]",
    choices=choices,
    default=choices[0]
)
```

**Progress indicators**:
```python
# Pattern
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
) as progress:
    task = progress.add_task("[cyan]Processing...", total=total_items)
    for item in items:
        # ... process item
        progress.update(task, advance=1)
```

### 3.5 Help Text Standards

**Command help structure**:
```python
@app.command()
def command_name(
    param: str = typer.Option(..., help="Parameter description with example: 'value'")
):
    """
    Brief one-line command description.

    Detailed explanation of what the command does, when to use it,
    and any important considerations.

    Examples:
        $ collabiq command-name --param value
        $ collabiq command-name --param "multi word value"

    See also: related-command, other-command
    """
```

**Status check output**:
```
🔍 CollabIQ Status Check

✅ Configuration: Valid
   • Gmail API: Configured
   • Notion API: Configured
   • LLM Provider: Gemini (healthy)

✅ Credentials: Present
   • .env file: Found
   • API keys: All present

⚠️  Notion Schema: Schema drift detected
   • Expected: 12 fields
   • Actual: 13 fields
   • New field: "Priority" (not in mapping)

💡 Suggested action: Run 'collabiq admin sync-schema' to update field mappings

📊 System Health: 2/3 checks passed (1 warning)
```

---

## 4. State Management

### 4.1 Cleanup State Tracking

Track cleanup operations to enable rollback if needed:

```json
{
  "cleanup_session": {
    "id": "016-cleanup-2025-11-18",
    "started_at": "2025-11-18T10:00:00Z",
    "phase": "documentation",
    "operations": [
      {
        "operation": "delete",
        "path": "docs/OLD_README.md",
        "backup": ".cleanup_backup/docs/OLD_README.md",
        "timestamp": "2025-11-18T10:05:00Z"
      },
      {
        "operation": "merge",
        "sources": ["docs/test_guide.md", "docs/testing_strategy.md"],
        "destination": "docs/testing/TEST_STRATEGY.md",
        "backup": ".cleanup_backup/merge_001/",
        "timestamp": "2025-11-18T10:10:00Z"
      }
    ],
    "completed_at": null
  }
}
```

### 4.2 Validation Checkpoints

**After each cleanup phase**:
1. Run regression test suite (all tests must pass)
2. Verify documentation links (no broken references)
3. Check test coverage (maintain ≥90%)
4. Validate CLI commands (all commands functional)

**Rollback triggers**:
- Any test fails after cleanup
- Documentation links broken
- CLI commands no longer functional
- Coverage drops below 90%

---

## 5. Success Metrics

### 5.1 Documentation Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Total files** | 34 | ≤27 | File count in docs/ |
| **Duplicate docs** | 7 identified | 0 | Manual audit |
| **Broken links** | Unknown | 0 | Link checker |
| **Time to find doc** | ~3-5 min | <1 min | User testing |

### 5.2 Test Suite Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Total tests** | 735 | ≤580 | pytest --collect-only |
| **Test files** | 103 | ≤85 | File count in tests/ |
| **Test pass rate** | 98.9% | ≥98.9% | pytest --tb=short |
| **Coverage** | 90%+ | ≥90% | pytest --cov |
| **Execution time** | Baseline | -15% | pytest --durations=0 |

### 5.3 CLI Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Startup time** | 260-620ms | <300ms | time collabiq --version |
| **Error clarity** | Subjective | 90% helpful | User feedback |
| **Help completeness** | Partial | 100% | Manual audit |
| **Interactive UX** | Limited | Enhanced | Feature checklist |

---

## 6. Data Model Relationships

```
Documentation
├─ Organization Schema → Directory structure + README indexes
├─ Cross-references → Internal/external linking patterns
└─ Lifecycle Rules → Update/archive/delete criteria

Tests
├─ Categorization → Unit/integration/E2E/performance/fuzz
├─ Consolidation Rules → Merge/delete criteria
└─ Naming Conventions → File/module/function patterns

CLI
├─ Error Taxonomy → Error codes + message format
├─ Interactive Patterns → Prompts + progress + confirmations
└─ Help Standards → Command help + status output

State Management
├─ Cleanup Tracking → Operation log + backup locations
├─ Validation Checkpoints → Test/link/coverage checks
└─ Rollback Triggers → Failure conditions

Metrics
├─ Documentation Metrics → File count, duplicates, find time
├─ Test Metrics → Count, pass rate, coverage, speed
└─ CLI Metrics → Startup, error clarity, help completeness
```

---

## Version History

**Version**: 1.0
**Created**: 2025-11-18
**Status**: Complete - Ready for quickstart.md generation
**Next**: Generate [quickstart.md](./quickstart.md) with step-by-step execution guide
