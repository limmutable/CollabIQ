# Validation Scripts

**Purpose**: Scripts for validating system accuracy and quality against ground truth data.

These scripts are used to:
- Validate entity extraction accuracy against known ground truth
- Compare system output to expected results
- Generate accuracy reports and metrics
- Identify regression issues

---

## Available Scripts

### validate_accuracy.py
**Purpose**: Validate entity extraction accuracy against ground truth data

**Usage**:
```bash
# Validate extraction accuracy
uv run python tests/validation/validate_accuracy.py
```

**What it validates**:
1. Reads ground truth from `tests/fixtures/ground_truth/GROUND_TRUTH.md`
2. Runs entity extraction on test emails
3. Compares extracted entities to ground truth
4. Calculates accuracy metrics:
   - Field-level accuracy (담당자, 스타트업명, 협업기관, 날짜)
   - Overall accuracy across all test cases
   - False positive/negative rates

**Output**:
- Console output with accuracy report
- Detailed comparison of expected vs actual entities
- Highlights any mismatches or errors

**Prerequisites**:
- Ground truth file exists: `tests/fixtures/ground_truth/GROUND_TRUTH.md`
- Test email fixtures available in `tests/fixtures/emails/`
- Gemini API key configured (GEMINI_API_KEY in .env)

---

## Ground Truth Format

Ground truth data is stored in `tests/fixtures/ground_truth/GROUND_TRUTH.md` with the following format:

```markdown
## Email 1: [Description]

**Expected Entities**:
- 담당자: [Expected value]
- 스타트업명: [Expected value]
- 협업기관: [Expected value]
- 날짜: [Expected date in YYYY-MM-DD format]

**Notes**: [Any special considerations]
```

---

## Adding New Validation Scripts

When creating new validation scripts:

1. **Naming convention**: `validate_*.py`
2. **Place in**: `tests/validation/`
3. **Add shebang**: `#!/usr/bin/env python3`
4. **Add docstring**: Clear description of what is being validated
5. **Output format**: Consistent with existing validation scripts
6. **Update this README**: Add entry to Available Scripts section

---

## Success Criteria

**Phase 1b (Entity Extraction)**:
- ✅ **SC-001**: ≥95% accuracy for 담당자 extraction
- ✅ **SC-002**: ≥95% accuracy for 스타트업명 extraction
- ✅ **SC-003**: ≥90% accuracy for 협업기관 extraction
- ✅ **SC-004**: ≥90% accuracy for 날짜 extraction

**Phase 2b (Company Matching)**:
- ✅ **SC-001**: ≥90% accuracy for exact company name matches
- ✅ **SC-002**: ≥80% accuracy for normalized name variations
- ✅ **SC-003**: ≥70% accuracy for typo/abbreviation handling
- ✅ **SC-004**: No false positives with confidence ≥0.90

---

## Validation Workflow

### During Development
```bash
# Run validation after making changes to extraction logic
uv run python tests/validation/validate_accuracy.py
```

### Before Commit
```bash
# Ensure accuracy hasn't regressed
uv run python tests/validation/validate_accuracy.py

# Only commit if accuracy meets success criteria
```

### CI/CD Pipeline (Future)
```yaml
# Add to GitHub Actions workflow
- name: Validate Extraction Accuracy
  run: uv run python tests/validation/validate_accuracy.py
```

---

## Troubleshooting

### Error: "Ground truth file not found"
**Solution**: Ensure `tests/fixtures/ground_truth/GROUND_TRUTH.md` exists

### Error: "Test email fixtures not found"
**Solution**: Ensure test emails exist in `tests/fixtures/emails/`

### Low Accuracy Results
**Possible causes**:
1. Ground truth data is outdated
2. LLM prompt has changed
3. Test emails have edge cases not covered
4. Gemini model behavior changed

**Solution**: Review failing test cases, update ground truth or prompts as needed

---

## Related Documentation

- [Phase 1b Testing Strategy](../../docs/features/004-gemini-extraction/testing.md)
- [Phase 2b Testing Strategy](../../docs/features/007-llm-matching/testing.md)
- [Ground Truth Guide](../../docs/testing/ground_truth_guide.md)
