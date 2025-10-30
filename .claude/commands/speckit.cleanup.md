---
description: Clean up completed feature by verifying acceptance criteria, copying artifacts to permanent locations, and removing specs directory (after feature is merged to main).
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Automate the cleanup process for completed features following the established SpecKit cleanup pattern. This command performs verification, artifact preservation, and specs directory removal after a feature has been successfully merged to main.

## Prerequisites

**CRITICAL**: This command should ONLY be run after:
1. ✅ Feature implementation is complete
2. ✅ All tests pass (if tests exist)
3. ✅ Feature branch has been **merged to main**
4. ✅ You are currently on the **main branch** (not the feature branch)

## Operating Constraints

**Safety First**:
- Command will ABORT if not on main branch
- Command will ABORT if specs directory doesn't exist
- Command will CONFIRM before removing specs directory
- Important artifacts will be preserved before deletion

**Manual Step Required**:
- User must manually commit cleanup changes (step 6 of checklist)
- This ensures user reviews all changes before committing

## Execution Steps

### 1. Verify Prerequisites

```bash
# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ ERROR: Must be on main branch to run cleanup"
    echo "Current branch: $CURRENT_BRANCH"
    echo "Run: git checkout main"
    exit 1
fi

# Check working tree is clean
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  WARNING: You have uncommitted changes"
    echo "Please commit or stash your changes before cleanup"
    exit 1
fi
```

### 2. Identify Feature to Clean Up

If user provided a feature number or name as argument, use that. Otherwise, detect the most recently merged feature branch:

```bash
# Get feature identifier from arguments or detect from recent merges
if [ -n "$ARGUMENTS" ]; then
    FEATURE_NAME="$ARGUMENTS"
else
    # Find most recent merge commit mentioning "specs/"
    FEATURE_NAME=$(git log --oneline -20 --grep="specs/" | head -1 | grep -oE "specs/[0-9]+-[a-z-]+" | cut -d'/' -f2)

    if [ -z "$FEATURE_NAME" ]; then
        echo "❌ ERROR: Could not detect feature to clean up"
        echo "Usage: /speckit.cleanup [feature-name]"
        echo "Example: /speckit.cleanup 002-structure-standards"
        exit 1
    fi
fi

SPECS_DIR="specs/$FEATURE_NAME"

# Verify specs directory exists
if [ ! -d "$SPECS_DIR" ]; then
    echo "❌ ERROR: Directory not found: $SPECS_DIR"
    echo "Available specs directories:"
    ls -d specs/*/ 2>/dev/null || echo "  (none)"
    exit 1
fi

echo "🎯 Cleaning up feature: $FEATURE_NAME"
echo "📁 Specs directory: $SPECS_DIR"
```

### 3. Task 1: Verify All Acceptance Criteria Met

Read the spec.md file and check success criteria:

```bash
SPEC_FILE="$SPECS_DIR/spec.md"

if [ ! -f "$SPEC_FILE" ]; then
    echo "⚠️  Warning: spec.md not found in $SPECS_DIR"
else
    echo ""
    echo "📋 Step 1: Verifying Acceptance Criteria"
    echo "=========================================="

    # Extract success criteria from spec
    echo ""
    echo "Success Criteria from spec.md:"
    grep -A 20 "## Success Criteria" "$SPEC_FILE" | grep -E "^- \*\*SC-[0-9]+\*\*:" | head -10

    echo ""
    echo "✅ Please confirm manually that all success criteria have been met."
    echo "   (This command assumes they are met since feature was merged to main)"
fi
```

### 4. Task 2: Copy Important Artifacts to docs/ Directory

Identify and preserve key artifacts:

```bash
echo ""
echo "📂 Step 2: Preserving Important Artifacts"
echo "=========================================="

# Create a preservation report
ARTIFACTS_TO_PRESERVE=()

# Check for completion report
if [ -f "$SPECS_DIR/completion-report.md" ]; then
    ARTIFACTS_TO_PRESERVE+=("completion-report.md")
fi

# Check for research findings
if [ -f "$SPECS_DIR/research.md" ]; then
    ARTIFACTS_TO_PRESERVE+=("research.md")
fi

# Check for architecture/design decisions
if [ -f "$SPECS_DIR/plan.md" ]; then
    ARTIFACTS_TO_PRESERVE+=("plan.md")
fi

# Check for data model
if [ -f "$SPECS_DIR/data-model.md" ]; then
    ARTIFACTS_TO_PRESERVE+=("data-model.md")
fi

# Check for audit reports
if [ -d "$SPECS_DIR/reports" ]; then
    ARTIFACTS_TO_PRESERVE+=("reports/")
fi

if [ ${#ARTIFACTS_TO_PRESERVE[@]} -eq 0 ]; then
    echo "ℹ️  No artifacts identified for preservation"
    echo "   (All feature work is already in the implementation)"
else
    echo "📦 Artifacts identified for preservation:"
    for artifact in "${ARTIFACTS_TO_PRESERVE[@]}"; do
        echo "   - $artifact"
    done

    echo ""
    echo "💡 Preservation Strategy:"
    echo "   Important artifacts should already be referenced in:"
    echo "   - docs/ directory (permanent documentation)"
    echo "   - README.md (if user-facing)"
    echo "   - Code comments (if technical decisions)"
    echo ""
    echo "   Since feature is merged to main, the implementation itself"
    echo "   is now the source of truth. Specs were working documents."
fi
```

### 5. Task 3: Update README.md with Completion Status

Check if README needs updating:

```bash
echo ""
echo "📝 Step 3: Checking README.md"
echo "=========================================="

if grep -q "$FEATURE_NAME" README.md; then
    echo "✅ Feature $FEATURE_NAME is mentioned in README.md"
    echo ""
    echo "   Verify manually that README reflects completion status:"
    grep -C 2 "$FEATURE_NAME" README.md | head -10
else
    echo "ℹ️  Feature $FEATURE_NAME not mentioned in README.md"
    echo "   (This is okay if feature doesn't affect user-facing functionality)"
fi

echo ""
echo "💡 If needed, update README.md to reflect feature completion before final commit."
```

### 6. Task 4: Verify Feature Branch Merged to Main

```bash
echo ""
echo "🔀 Step 4: Verifying Merge to Main"
echo "=========================================="

# Check if feature branch was merged
MERGE_COMMIT=$(git log --oneline --merges -20 | grep -i "$FEATURE_NAME" | head -1)

if [ -n "$MERGE_COMMIT" ]; then
    echo "✅ Feature merged to main:"
    echo "   $MERGE_COMMIT"
else
    echo "⚠️  Could not find merge commit for $FEATURE_NAME"
    echo "   Please verify feature was merged to main:"
    echo ""
    git log --oneline -10 --merges
    echo ""
    read -p "   Continue with cleanup? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "❌ Cleanup aborted by user"
        exit 1
    fi
fi
```

### 7. Task 5: Remove specs/feature_branch/ Directory

```bash
echo ""
echo "🗑️  Step 5: Removing Specs Directory"
echo "=========================================="

# Final confirmation
echo ""
echo "⚠️  About to remove: $SPECS_DIR"
echo ""
echo "This directory contains:"
ls -la "$SPECS_DIR" | tail -n +4 | awk '{print "   - " $9}'
echo ""
echo "❓ Remove this directory? This action cannot be undone."
read -p "   Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup aborted by user"
    exit 1
fi

# Remove the specs directory
rm -rf "$SPECS_DIR"

if [ ! -d "$SPECS_DIR" ]; then
    echo "✅ Successfully removed $SPECS_DIR"
else
    echo "❌ ERROR: Failed to remove $SPECS_DIR"
    exit 1
fi

# Stage the deletion
git add "specs/"

echo ""
echo "✅ Specs directory removed and staged for commit"
```

### 8. Summary and Next Steps

```bash
echo ""
echo "✅ CLEANUP COMPLETE"
echo "===================="
echo ""
echo "Summary of actions:"
echo "  ✅ Step 1: Verified acceptance criteria (manual review recommended)"
echo "  ✅ Step 2: Identified artifacts for preservation"
echo "  ✅ Step 3: Checked README.md status"
echo "  ✅ Step 4: Verified merge to main"
echo "  ✅ Step 5: Removed $SPECS_DIR"
echo ""
echo "📋 Manual Step Required (Step 6):"
echo "=========================================="
echo ""
echo "Review the changes and commit:"
echo ""
echo "  git status"
echo "  git diff --cached"
echo "  git commit -m \"Clean up: Remove $SPECS_DIR directory after merge\""
echo "  git push"
echo ""
echo "💡 Commit message template:"
echo ""
echo "Clean up: Remove $SPECS_DIR directory after merge"
echo ""
echo "Feature $FEATURE_NAME has been successfully merged to main."
echo "Removing specs directory as it's no longer needed:"
echo "- Implementation is now the source of truth"
echo "- Important artifacts preserved in permanent documentation"
echo "- Keeping repository clean and focused on current work"
echo ""
echo "Feature: $FEATURE_NAME"
echo "Status: ✅ Merged and cleaned up"
echo ""
```

## Usage Examples

### Example 1: Cleanup specific feature
```bash
/speckit.cleanup 002-structure-standards
```

### Example 2: Cleanup most recent merged feature (auto-detect)
```bash
/speckit.cleanup
```

### Example 3: Typical workflow
```bash
# 1. Ensure you're on main with feature merged
git checkout main
git pull

# 2. Run cleanup command
/speckit.cleanup 002-structure-standards

# 3. Review changes
git status
git diff --cached

# 4. Commit and push (manual step)
git commit -m "Clean up: Remove specs/002-structure-standards after merge"
git push
```

## Safety Features

1. ✅ **Branch Check**: Aborts if not on main branch
2. ✅ **Existence Check**: Verifies specs directory exists before attempting removal
3. ✅ **User Confirmation**: Requires explicit "yes" before deletion
4. ✅ **Manual Commit**: User must review and commit changes
5. ✅ **Artifact Identification**: Identifies important files for preservation awareness

## Notes

- This command follows the established cleanup pattern from `.specify/CLEANUP_PATTERN.md`
- Step 6 (commit cleanup changes) is intentionally left manual for user control
- The command is safe to run multiple times (will abort if specs directory doesn't exist)
- Always verify feature is merged to main before running this command
