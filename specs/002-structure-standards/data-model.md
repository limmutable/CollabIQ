# Data Model: Project Structure Standards & File Naming Convention

**Feature**: 002-structure-standards
**Date**: 2025-10-29
**Purpose**: Define entities and their relationships for managing file naming standards and project structure audits

## Overview

This feature involves four primary entities that work together to establish, audit, and enforce file naming conventions:

1. **Naming Convention Rule** - Defines a single naming standard
2. **File Category** - Groups files by type with associated rules
3. **Audit Finding** - Documents a deviation from standards
4. **Migration Task** - Describes a file operation to fix a deviation

These entities are conceptual and used for organizing documentation and audit reports. No database or persistence layer is required.

---

## Entity Definitions

### Naming Convention Rule

**Purpose**: Represents a single, concrete naming standard with examples and rationale

**Attributes**:

| Attribute | Type | Description | Required | Example |
|-----------|------|-------------|----------|---------|
| rule_id | String | Unique identifier for the rule | Yes | `NC-001` |
| category | String | File category this rule applies to | Yes | `python_modules`, `documentation`, `tests` |
| pattern_name | String | Short descriptive name | Yes | "Python Module Names" |
| format_spec | String | Technical format description | Yes | `lowercase_with_underscores (snake_case)` |
| regex_pattern | String (optional) | Validation regex if applicable | No | `^[a-z][a-z0-9_]*\.py$` |
| examples_valid | List[String] | Valid examples following this rule | Yes | `["email_receiver.py", "llm_adapters.py"]` |
| examples_invalid | List[String] | Invalid examples violating this rule | Yes | `["emailReceiver.py", "llm-adapters.py"]` |
| rationale | String | Why this convention was chosen | Yes | "PEP 8 standard, importable in Python, widely recognized" |
| source | String | Authority or reference | No | "PEP 8 - Style Guide for Python Code" |
| exceptions | List[String] | Files explicitly exempted | No | `["__init__.py", "__main__.py"]` |

**Validation Rules**:
- At least one valid example must be provided
- Format spec must be unambiguous
- Rationale must explain the decision

**Relationships**:
- Belongs to exactly one File Category
- Referenced by zero or more Audit Findings (when violated)

**Example**:
```yaml
rule_id: NC-001
category: python_modules
pattern_name: "Python Module Names"
format_spec: "lowercase_with_underscores (snake_case)"
regex_pattern: "^[a-z][a-z0-9_]*\\.py$"
examples_valid:
  - "email_receiver.py"
  - "llm_adapters.py"
  - "notion_integrator.py"
examples_invalid:
  - "emailReceiver.py"  # camelCase not allowed
  - "llm-adapters.py"    # hyphens not importable
  - "LLMAdapters.py"     # PascalCase not allowed
rationale: "PEP 8 standard for module naming ensures consistency with Python ecosystem and allows imports without special handling"
source: "PEP 8 - Style Guide for Python Code (https://peps.python.org/pep-0008/)"
exceptions:
  - "__init__.py"
  - "__main__.py"
  - "__version__.py"
```

---

### File Category

**Purpose**: Groups related files with shared naming conventions

**Attributes**:

| Attribute | Type | Description | Required | Example |
|-----------|------|-------------|----------|---------|
| category_id | String | Unique identifier | Yes | `CAT-001` |
| category_name | String | Human-readable name | Yes | "Python Modules" |
| directory_paths | List[String] | Directories where these files live | Yes | `["src/", "config/"]` |
| file_patterns | List[String] | Glob patterns to identify files | Yes | `["*.py", "!__*__.py"]` |
| naming_rules | List[String] | Rule IDs that apply to this category | Yes | `["NC-001", "NC-002"]` |
| description | String | Purpose and scope of this category | Yes | "Python source code modules and packages" |
| modifiable | Boolean | Can files in this category be renamed? | Yes | `true` |
| rationale_for_immutability | String | Why files can't be renamed (if false) | Conditional | "Ecosystem standard, required by tools" |

**Validation Rules**:
- If `modifiable` is false, `rationale_for_immutability` must be provided
- At least one directory path must be specified
- At least one naming rule must be associated

**Relationships**:
- Contains many Naming Convention Rules
- Has many Audit Findings (for files in this category)

**Example**:
```yaml
category_id: CAT-002
category_name: "Major Documentation"
directory_paths:
  - "docs/"
file_patterns:
  - "*.md"
  - "!README.md"  # Excluded - ecosystem standard
naming_rules:
  - "NC-003"  # SCREAMING_SNAKE_CASE for major docs
description: "High-importance technical and architectural documentation"
modifiable: true
```

---

### Audit Finding

**Purpose**: Documents a specific deviation from naming standards detected during audit

**Attributes**:

| Attribute | Type | Description | Required | Example |
|-----------|------|-------------|----------|---------|
| finding_id | String | Unique identifier | Yes | `AUD-001` |
| file_path | String | Absolute or relative path to file | Yes | `docs/quickstart.md` |
| category_id | String | File category this belongs to | Yes | `CAT-002` (Major Documentation) |
| violated_rule_id | String | Rule that was violated | Yes | `NC-003` |
| current_name | String | Current file name | Yes | `quickstart.md` |
| expected_pattern | String | What the name should follow | Yes | `SCREAMING_SNAKE_CASE.md or kebab-case.md` |
| recommended_name | String | Suggested new name | Yes | `QUICKSTART.md` or keep as `quickstart.md` |
| severity | Enum | Impact level | Yes | `Critical`, `High`, `Medium`, `Low` |
| impact_description | String | Why this matters | Yes | "Inconsistent with other major docs, reduces visual hierarchy" |
| migration_complexity | Enum | Effort to fix | Yes | `Simple`, `Moderate`, `Complex` |
| complexity_rationale | String | Why this complexity level | Yes | "No imports to update, simple git mv" |
| affected_references | List[String] | Files that reference this file | No | `["README.md:15", "docs/ARCHITECTURE.md:42"]` |
| created_date | Date | When finding was identified | Yes | `2025-10-29` |
| resolved | Boolean | Has this been fixed? | Yes | `false` |

**Validation Rules**:
- Severity must be one of: `Critical`, `High`, `Medium`, `Low`
- Migration complexity must be one of: `Simple`, `Moderate`, `Complex`
- If complexity is `Complex`, must have non-empty affected_references

**Severity Guidelines**:
- **Critical**: Blocks developer productivity or violates hard constraints (e.g., file not importable, breaks builds)
- **High**: Creates significant confusion or inconsistency (e.g., major doc not following SCREAMING_SNAKE_CASE)
- **Medium**: Aesthetic inconsistency that doesn't impact functionality (e.g., minor docs not following kebab-case)
- **Low**: Minor deviation with negligible impact (e.g., test fixture with unclear name)

**Relationships**:
- References one File Category
- References one Naming Convention Rule (that was violated)
- May generate one Migration Task (to fix the issue)

**Example**:
```yaml
finding_id: AUD-001
file_path: "docs/quickstart.md"
category_id: CAT-002
violated_rule_id: NC-003
current_name: "quickstart.md"
expected_pattern: "SCREAMING_SNAKE_CASE.md"
recommended_name: "QUICKSTART.md"
severity: Medium
impact_description: "SpecKit standard guide file; might be exempt as framework convention rather than major doc"
migration_complexity: Simple
complexity_rationale: "No Python imports, minimal references in README.md"
affected_references:
  - "README.md:12"
  - "docs/ARCHITECTURE.md:8"
created_date: 2025-10-29
resolved: false
```

---

### Migration Task

**Purpose**: Describes a specific file operation to resolve an audit finding

**Attributes**:

| Attribute | Type | Description | Required | Example |
|-----------|------|-------------|----------|---------|
| task_id | String | Unique identifier | Yes | `MIG-001` |
| finding_id | String | Audit finding this resolves | Yes | `AUD-001` |
| operation_type | Enum | Type of operation | Yes | `Rename`, `Move`, `Rename+Move` |
| source_path | String | Current file path | Yes | `docs/quickstart.md` |
| target_path | String | New file path | Yes | `docs/QUICKSTART.md` |
| git_command | String | Command to execute | Yes | `git mv docs/quickstart.md docs/QUICKSTART.md` |
| references_to_update | List[Object] | Files needing reference updates | No | See example below |
| test_verification | String | How to verify no breakage | Yes | "Run pytest, verify all tests pass" |
| rollback_command | String | How to undo if needed | Yes | `git mv docs/QUICKSTART.md docs/quickstart.md` |
| estimated_effort | String | Time estimate | No | "5 minutes" |
| dependencies | List[String] | Other tasks that must complete first | No | `["MIG-002"]` |
| completed | Boolean | Has this been executed? | Yes | `false` |
| completion_date | Date (optional) | When this was executed | No | - |

**References to Update** (nested object):
```yaml
- file_path: "README.md"
  line_number: 12
  old_text: "See [quickstart.md](docs/quickstart.md)"
  new_text: "See [QUICKSTART.md](docs/QUICKSTART.md)"

- file_path: "docs/ARCHITECTURE.md"
  line_number: 8
  old_text: "refer to quickstart.md"
  new_text: "refer to QUICKSTART.md"
```

**Validation Rules**:
- `source_path` must match the file path from referenced audit finding
- `target_path` must follow the recommended pattern from audit finding
- If `operation_type` is `Rename+Move`, paths must differ in both name and directory
- Git command must use `git mv` for tracked files

**Relationships**:
- Resolves exactly one Audit Finding
- May depend on zero or more other Migration Tasks

**Example**:
```yaml
task_id: MIG-001
finding_id: AUD-001
operation_type: Rename
source_path: "docs/quickstart.md"
target_path: "docs/QUICKSTART.md"
git_command: "git mv docs/quickstart.md docs/QUICKSTART.md"
references_to_update:
  - file_path: "README.md"
    line_number: 12
    old_text: "[quickstart.md](docs/quickstart.md)"
    new_text: "[QUICKSTART.md](docs/QUICKSTART.md)"
  - file_path: "docs/ARCHITECTURE.md"
    line_number: 8
    old_text: "quickstart.md"
    new_text: "QUICKSTART.md"
test_verification: "Run pytest, verify all tests pass (no pytest-specific changes expected)"
rollback_command: "git mv docs/QUICKSTART.md docs/quickstart.md"
estimated_effort: "5 minutes"
dependencies: []
completed: false
```

---

## Entity Relationships

```text
File Category (1) ──────< (N) Naming Convention Rule
      │
      │
      └──────< (N) Audit Finding ────── (1) Migration Task
                       │
                       │
                       └──────> (1) Naming Convention Rule (violated rule)
```

**Relationship Descriptions**:

1. **File Category → Naming Convention Rules** (One-to-Many)
   - Each category has multiple rules defining allowed patterns
   - A rule belongs to exactly one category
   - Example: "Python Modules" category has rules for module names, package names, special files

2. **File Category → Audit Findings** (One-to-Many)
   - Each category may have multiple findings for files in that category
   - A finding belongs to exactly one category
   - Example: "Major Documentation" category has findings for docs not following SCREAMING_SNAKE_CASE

3. **Audit Finding → Naming Convention Rule** (Many-to-One)
   - Each finding references the specific rule that was violated
   - A rule may be violated by multiple findings
   - Example: Multiple Python modules violating snake_case rule

4. **Audit Finding → Migration Task** (One-to-One)
   - Each finding may generate one migration task to resolve it
   - A migration task resolves exactly one finding
   - Example: Finding AUD-001 generates Migration Task MIG-001 to rename the file

5. **Migration Task → Migration Task** (Many-to-Many via Dependencies)
   - Tasks may depend on other tasks completing first
   - Example: Must rename module before updating imports

---

## Data Flow

### Phase 1: Standards Documentation (User Story P1)

**Input**: Research findings + existing project structure
**Process**: Create Naming Convention Rules and File Categories
**Output**: Constitution.md with documented standards

```text
Research Findings
      │
      ├──> Create Naming Convention Rules
      │         │
      │         └──> Group into File Categories
      │                   │
      └───────────────────┴──> Document in Constitution.md
```

### Phase 2: Structure Audit (User Story P2)

**Input**: File Categories + Naming Convention Rules + Current file system
**Process**: Scan project, compare to rules, generate findings
**Output**: Audit report with findings

```text
Current File System + File Categories + Naming Convention Rules
      │
      ├──> Scan each directory
      │         │
      │         ├──> Match files to categories
      │         │         │
      │         │         └──> Check against category rules
      │         │                   │
      │         │                   ├──> [Compliant] → No finding
      │         │                   └──> [Violation] → Create Audit Finding
      │         │
      └─────────┴──> Generate Audit Report
                           │
                           └──> Sort by severity (Critical → Low)
```

### Phase 3: Cleanup Execution (User Story P3)

**Input**: Audit Findings (Critical + High priority)
**Process**: Generate migration tasks, execute in dependency order
**Output**: Renamed files + updated references

```text
Audit Findings (Critical & High)
      │
      ├──> Generate Migration Tasks
      │         │
      │         ├──> Identify dependencies (imports, references)
      │         │         │
      │         │         └──> Order tasks by dependencies
      │         │
      ├──> Execute tasks in order
      │         │
      │         ├──> Run git mv
      │         ├──> Update references
      │         ├──> Commit changes
      │         └──> Run tests
      │
      └──> Re-audit to verify (0 Critical/High remaining)
```

---

## State Transitions

### Audit Finding States

```text
[Created] ──────────────────────> [Assessed]
                                       │
                                       ├──> [Accepted] ──> [Resolved]
                                       ├──> [Deferred]
                                       └──> [Won't Fix]
```

**State Descriptions**:
- **Created**: Finding identified during audit
- **Assessed**: Severity and migration complexity evaluated
- **Accepted**: Approved for remediation
- **Deferred**: Will fix in future iteration (e.g., after other branches merge)
- **Won't Fix**: Explicitly exempted (e.g., SpecKit framework file)
- **Resolved**: Migration task completed successfully

### Migration Task States

```text
[Pending] ──> [Ready] ──> [In Progress] ──> [Completed]
                │                                │
                └──> [Blocked]                   └──> [Verified]
                          │
                          └──> [Failed] ──> [Rollback]
```

**State Descriptions**:
- **Pending**: Task created, waiting for dependencies
- **Ready**: All dependencies met, can be executed
- **Blocked**: Dependency failed or external blocker
- **In Progress**: Git mv command executed
- **Completed**: References updated, committed
- **Verified**: Tests pass, no functionality broken
- **Failed**: Operation encountered error
- **Rollback**: Changes reverted to previous state

---

## Usage Examples

### Example 1: Document Python Module Naming Rule

```yaml
# Naming Convention Rule
rule_id: NC-001
category: python_modules
pattern_name: "Python Module Names"
format_spec: "lowercase_with_underscores (snake_case)"
examples_valid: ["email_receiver.py", "llm_adapters.py"]
examples_invalid: ["emailReceiver.py", "llm-adapters.py"]
rationale: "PEP 8 standard for Python module naming"
```

### Example 2: Audit Finding for Inconsistent Doc Name

```yaml
# Audit Finding
finding_id: AUD-005
file_path: "docs/email-infrastructure-comparison.md"
category_id: CAT-002  # Major Documentation
violated_rule_id: NC-003  # SCREAMING_SNAKE_CASE rule
current_name: "email-infrastructure-comparison.md"
recommended_name: "EMAIL_INFRASTRUCTURE_COMPARISON.md"
severity: Medium
impact_description: "Technical comparison document in kebab-case; other major docs use SCREAMING_SNAKE_CASE"
migration_complexity: Simple
affected_references: []  # No references found
```

### Example 3: Migration Task to Fix Module Name

```yaml
# Migration Task
task_id: MIG-015
finding_id: AUD-015
operation_type: Rename
source_path: "src/emailReceiver/processor.py"
target_path: "src/email_receiver/processor.py"
git_command: "git mv src/emailReceiver/processor.py src/email_receiver/processor.py"
references_to_update:
  - file_path: "src/collabiq/__init__.py"
    line_number: 3
    old_text: "from emailReceiver import processor"
    new_text: "from email_receiver import processor"
test_verification: "Run pytest tests/unit/test_email_receiver.py"
estimated_effort: "10 minutes"
dependencies: []
```

---

## Validation and Constraints

### Cross-Entity Validations

1. **Naming Convention Rule → File Category**:
   - Every rule must be assigned to exactly one category
   - A category must have at least one rule

2. **Audit Finding → Naming Convention Rule**:
   - `violated_rule_id` must reference an existing rule
   - The violated rule must belong to the same category as the finding

3. **Migration Task → Audit Finding**:
   - `finding_id` must reference an existing finding
   - `target_path` must satisfy the rule that was violated

4. **Migration Task Dependencies**:
   - Cyclic dependencies are invalid (A depends on B depends on A)
   - All dependency task_ids must reference existing tasks

### Business Rules

1. **Severity Assignment**:
   - Critical: File cannot be used (not importable, breaks build)
   - High: Major inconsistency affecting multiple developers
   - Medium: Inconsistency within a category
   - Low: Minor issue with no practical impact

2. **Migration Complexity**:
   - Simple: No imports, <3 references, single git mv
   - Moderate: Python imports affected, 3-10 references
   - Complex: Cross-module imports, >10 references, potential breakage

3. **Resolution Priority**:
   - Must fix Critical before High
   - Must fix High before merging to main
   - Medium and Low may be deferred

---

## Notes

This data model is **conceptual** and used for organizing documentation. No database implementation is required. The entities will be represented as:

- **Naming Convention Rules**: Sections in constitution.md with structured content
- **File Categories**: Headings in constitution.md organizing rules
- **Audit Findings**: Markdown tables in audit report
- **Migration Tasks**: Checklist items in tasks.md

The data model provides a structured way to think about the problem domain and ensures consistency across documentation artifacts.
