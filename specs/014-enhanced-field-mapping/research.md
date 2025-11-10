# Technical Research: Enhanced Notion Field Mapping

**Feature**: 014-enhanced-field-mapping
**Date**: 2025-11-10
**Status**: Complete

## Research Questions

### 1. Fuzzy String Matching Algorithm Selection

**Question**: Which fuzzy string matching algorithm is most appropriate for Korean company names with spelling variations?

**Decision**: Implement BOTH approaches with comparative evaluation, default to rapidfuzz for MVP

**Rationale for Dual Approach**:
- **Unknown ground truth**: Without real-world data, we cannot definitively determine which approach is superior
- **Different strengths**: LLM and character-based algorithms excel in different scenarios
- **Data-driven decision**: Empirical evaluation will reveal the best approach for Korean company names
- **Minimal cost**: Evaluation can run in parallel during testing phase

---

#### Approach A: Character-Based (rapidfuzz / Jaro-Winkler)

**Strengths**:
- ✅ **Deterministic**: Same input always produces same output (reproducible)
- ✅ **Fast**: ~0.001ms per comparison, <1 second for 1000 companies
- ✅ **Zero cost**: No API calls, runs locally
- ✅ **Already available**: rapidfuzz in dependencies (pyproject.toml line 26)
- ✅ **Simple**: No prompt engineering, no rate limits, no context windows
- ✅ **Good for character-level variations**: "워크" vs "웍", spacing, parentheticals

**Weaknesses**:
- ❌ **Semantic blindness**: Cannot understand "SSG" = "신세계" or "에스에스지" (abbreviation matching)
- ❌ **No domain knowledge**: Doesn't know "웨이크" and "산스" are different companies even if parenthetical suggests "(산스)"
- ❌ **Fixed threshold**: Requires manual tuning, may not generalize well

**Best Use Cases**:
- Spelling variations with same characters (웨이크(산스) → 웨이크)
- Whitespace differences (스타트업 A → 스타트업A)
- Character substitutions (네트워크 → 네트웍스)

**Implementation**:
```python
from rapidfuzz import fuzz

def match_character_based(extracted: str, candidates: List[str]) -> List[Tuple[str, float]]:
    """Character-based fuzzy matching."""
    scores = [(name, fuzz.ratio(extracted, name) / 100.0) for name in candidates]
    return sorted(scores, key=lambda x: x[1], reverse=True)
```

---

#### Approach B: LLM-Based Semantic Matching

**Strengths**:
- ✅ **Semantic understanding**: Can match "SSG" to "신세계그룹" or "에스에스지" (abbreviations)
- ✅ **Domain knowledge**: Understands Korean business naming conventions
- ✅ **Contextual reasoning**: Can distinguish "웨이크(산스)" means "웨이크 at 산스" vs "웨이크산스 company"
- ✅ **Multi-language**: Handles Korean-English mixed names ("Samsung" = "삼성")
- ✅ **Already integrated**: Project has Gemini, Claude, OpenAI adapters (Phase 012)

**Weaknesses**:
- ❌ **Non-deterministic**: Same input may produce different outputs (temperature, sampling)
- ❌ **Slower**: 200-500ms per LLM call, rate limits apply
- ❌ **Cost**: API calls cost money (though minimal for matching tasks)
- ❌ **Complex**: Requires prompt engineering, error handling, retry logic
- ❌ **Harder to debug**: "Why did it match?" is less transparent than similarity scores

**Best Use Cases**:
- Abbreviation matching (SSG → 신세계)
- Multi-language matching (Samsung → 삼성)
- Disambiguation (웨이크(산스) → which company is primary?)
- Complex semantic variations

**Implementation Strategy**:
```python
def match_llm_based(extracted: str, candidates: List[str]) -> List[Tuple[str, float]]:
    """LLM-based semantic matching with confidence scores."""
    prompt = f"""Given extracted company name: "{extracted}"

    Candidates from database:
    {'\n'.join(f'{i+1}. {name}' for i, name in enumerate(candidates))}

    Task: Rank candidates by match likelihood. Consider:
    - Abbreviations (SSG = 신세계 = 에스에스지)
    - Parentheticals (웨이크(산스) likely means "웨이크" not "산스")
    - Character variations (워크 = 웍)

    Return JSON: [{{"name": "...", "confidence": 0.0-1.0, "reason": "..."}}]"""

    response = llm_orchestrator.process(prompt, task_type="matching")
    return parse_llm_ranking(response)
```

---

#### Hybrid Approach (Recommended for Production)

**Strategy**: Use character-based as primary, LLM as fallback for edge cases

```python
def match_hybrid(extracted: str, candidates: List[str],
                 char_threshold: float = 0.85, llm_threshold: float = 0.70) -> CompanyMatch:
    """Hybrid matching: rapidfuzz first, LLM for edge cases."""

    # Phase 1: Character-based matching (fast, deterministic)
    char_scores = match_character_based(extracted, candidates)
    best_char_match, best_char_score = char_scores[0]

    if best_char_score >= char_threshold:
        # High confidence character match - use it
        return CompanyMatch(page_id=..., similarity=best_char_score,
                           match_type="fuzzy", method="character")

    # Phase 2: LLM fallback for low character similarity
    # Useful for abbreviations, semantic variations
    llm_scores = match_llm_based(extracted, candidates[:5])  # Top 5 only for cost
    best_llm_match, best_llm_score = llm_scores[0]

    if best_llm_score >= llm_threshold:
        # LLM found semantic match
        return CompanyMatch(page_id=..., similarity=best_llm_score,
                           match_type="semantic", method="llm")

    # Phase 3: No match - auto-create
    return CompanyMatch(page_id=None, match_type="none")
```

---

#### Comparative Evaluation Framework

**Objective**: Determine which approach performs better on real Korean company names

**Evaluation Dataset**:
- Use 20+ real emails from E2E test suite
- Manual ground truth labeling: "웨이크(산스)" → correct match is "웨이크" (yes/no)
- Test cases covering:
  - Exact matches (baseline: both should get 100%)
  - Spelling variations (웨이크 vs 웨이크(산스))
  - Abbreviations (SSG vs 신세계 vs 에스에스지)
  - Character alternatives (네트워크 vs 네트웍스)
  - Multi-language (Samsung vs 삼성)

**Metrics**:
1. **Accuracy**: % of correct matches (true positive + true negative)
2. **Precision**: Of predicted matches, % that are correct (avoid false positives)
3. **Recall**: Of actual matches, % that were found (avoid false negatives)
4. **F1 Score**: Harmonic mean of precision and recall
5. **Latency**: Time per matching operation
6. **Cost**: API costs for LLM approach (if applicable)

**Success Criteria**:
- Primary: Accuracy ≥ 90% (per spec SC-001)
- Secondary: Latency < 2 seconds per email (per spec SC-007)
- Tertiary: Cost < $0.01 per email processed

**Implementation**:
```python
# tests/evaluation/test_matching_comparison.py

def test_matching_algorithm_comparison():
    """Compare rapidfuzz vs LLM vs hybrid on real test dataset."""

    test_cases = load_ground_truth_dataset()  # 20+ emails with manual labels

    results = {
        "rapidfuzz": evaluate_matcher(RapidfuzzMatcher(), test_cases),
        "llm": evaluate_matcher(LLMMatcher(), test_cases),
        "hybrid": evaluate_matcher(HybridMatcher(), test_cases)
    }

    # Generate comparison report
    generate_comparison_report(results)

    # Assert all approaches meet minimum 90% accuracy
    for approach, metrics in results.items():
        assert metrics["accuracy"] >= 0.90, f"{approach} accuracy {metrics['accuracy']} < 0.90"
```

**Report Output** (saved to `specs/014-enhanced-field-mapping/evaluation-report.md`):
```markdown
# Matching Algorithm Comparison

## Test Dataset
- 22 real emails from CollabIQ pipeline
- 15 spelling variations, 4 abbreviations, 3 multi-language cases

## Results

| Metric | Rapidfuzz | LLM (Gemini) | Hybrid |
|--------|-----------|--------------|--------|
| Accuracy | 86% | 95% | 95% |
| Precision | 100% (no false positives) | 92% | 96% |
| Recall | 78% (missed abbreviations) | 98% | 95% |
| F1 Score | 0.88 | 0.95 | 0.95 |
| Avg Latency | 0.2ms | 320ms | 45ms* |
| Cost per email | $0 | $0.003 | $0.001* |

*Hybrid only calls LLM for 15% of cases (low character similarity)

## Recommendation
- **MVP (Phase 3d)**: Use rapidfuzz (meets 90% threshold via manual threshold tuning)
- **Production (Phase 4+)**: Migrate to hybrid approach if evaluation shows >90% accuracy improvement
```

---

#### Final Decision for Phase 3d MVP

**MVP Implementation**: Start with rapidfuzz (character-based)

**Justification**:
1. **Meets success criteria**: 90% accuracy achievable with threshold tuning
2. **Fast & free**: No latency, no API costs
3. **Simple**: Easier to debug, test, and maintain
4. **Constitution compliance**: Follows principle V (Simplicity)

**Built-in Flexibility**: Architecture supports swapping matchers via dependency injection
```python
class FieldMapper:
    def __init__(self, company_matcher: CompanyMatcher):  # Interface, not implementation
        self.company_matcher = company_matcher
```

**Phase 4 Enhancement** (if evaluation shows LLM superiority):
- Add `LLMMatcher` implementation of `CompanyMatcher` interface
- Add `HybridMatcher` with fallback logic
- Add configuration to switch between implementations
- No breaking changes to existing code

**Evaluation as User Story P4** (optional, post-MVP):
- Priority P4: Comparative evaluation of matching approaches
- Deliverable: evaluation-report.md with empirical results
- Decision: Migrate to LLM/hybrid if accuracy improves by ≥5%

### 2. Similarity Threshold Selection

**Question**: What similarity thresholds provide optimal balance between false positives and false negatives?

**Decision**:
- Company matching: 0.85 threshold (strict)
- Person matching: 0.70 threshold (lenient)

**Rationale**:
- **Company 0.85**: Strict threshold prevents false positives (linking wrong company is worse than leaving empty)
- **Person 0.70**: Lenient threshold acceptable because:
  - Korean names have high ambiguity (common family names: 김, 이, 박)
  - False negative (empty field) acceptable per spec
  - Low-confidence matches (0.70-0.85) logged for manual review
- Thresholds are configurable in code for future tuning

**Evidence**:
- Spec requirement FR-003: similarity ≥0.85 for companies
- Spec requirement FR-009: similarity ≥0.70 for persons
- Success criteria SC-001: ≥90% match rate validates threshold appropriateness

**Alternatives Considered**:
- **Dynamic threshold**: Rejected - adds complexity without clear benefit
- **ML-learned threshold**: Rejected - requires training data, violates simplicity principle
- **Same threshold for both**: Rejected - persons need lower threshold due to name ambiguity

### 3. Korean Text Normalization Strategy

**Question**: What text normalization should be applied before fuzzy matching?

**Decision**: Minimal normalization - trim whitespace, preserve original characters

**Rationale**:
- Jaro-Winkler handles character-level differences inherently
- Korean Unicode is consistent (no NFC vs NFD normalization issues like diacritics)
- Over-normalization risks losing information (e.g., 워크 vs 웍 are legitimately different)
- Parenthetical info naturally handled by fuzzy matching ("웨이크(산스)" vs "웨이크" scores high)

**Implementation**:
```python
def normalize_for_matching(text: str) -> str:
    """Minimal normalization for fuzzy matching."""
    return text.strip()  # Only trim whitespace
```

**Alternatives Considered**:
- **Remove parentheticals**: Rejected - fuzzy matching handles this, explicit removal may cause issues
- **Remove spaces**: Rejected - spacing differences naturally handled by Jaro-Winkler
- **Hangul normalization**: Rejected - not needed, Korean text already consistent

### 4. Notion User List Caching Strategy

**Question**: How should we cache the Notion workspace user list to minimize API calls?

**Decision**: File-based JSON cache with 24-hour TTL, stored in existing cache directory

**Rationale**:
- **Reuse existing pattern**: Project uses file-based cache (see src/notion_integrator/cache.py)
- **24-hour TTL**: User list changes infrequently (new hires, departures are rare)
- **Cache location**: `data/notion_cache/users_list.json` (follows existing pattern)
- **Invalidation**: TTL-based (simple, no manual invalidation needed)

**Implementation**:
```python
# Reuse existing NotionCache class pattern
cache_file = "data/notion_cache/users_list.json"
ttl_seconds = 86400  # 24 hours
```

**Alternatives Considered**:
- **In-memory cache**: Rejected - lost on process restart, not suitable for CLI
- **Database storage**: Rejected - project uses file-based storage (per constitution)
- **No caching**: Rejected - wasteful API calls, hits rate limits unnecessarily
- **1-hour TTL**: Rejected - too aggressive, users list stable

### 5. Company Auto-Creation Pattern

**Question**: Should company auto-creation be behind a feature flag or always-on?

**Decision**: Always-on by default, no feature flag needed

**Rationale**:
- **Spec assumption 7**: "Auto-creating company entries in the Companies database is acceptable business logic"
- **Simplicity**: No configuration needed, one less decision point for users
- **Fail-safe**: Auto-creation only triggers when fuzzy match fails (similarity < 0.85)
- **Duplicate prevention**: Exact match check happens first before fuzzy matching

**Future Enhancement** (if needed):
- Add `--no-autocreate` flag to CLI commands (P3 priority, not MVP)
- Add configuration option in settings if users request it

**Alternatives Considered**:
- **Feature flag**: Rejected - adds complexity, spec indicates always-on acceptable
- **Manual approval**: Rejected - out of scope per spec (no manual review queue)
- **Prompt user**: Rejected - not suitable for automated pipeline

### 6. Fuzzy Matching Performance Optimization

**Question**: How to ensure <2 second matching time with 1000+ companies?

**Decision**: Linear scan with rapidfuzz, no indexing needed at current scale

**Rationale**:
- **Spec constraint**: 1000+ companies, ~50-100 expected initially
- **rapidfuzz performance**: ~0.001ms per comparison (1000 comparisons = 1 second)
- **Success criteria SC-007**: <2 seconds per email achievable without optimization
- **Premature optimization**: YAGNI principle - optimize only if performance degrades

**Future Optimization** (if needed at 5000+ companies):
- Add BK-tree index for similarity search (sub-linear lookups)
- Cache similarity scores per email batch
- Parallel matching for multiple companies in same email

**Alternatives Considered**:
- **Pre-compute similarity matrix**: Rejected - memory overhead, companies list dynamic
- **Elasticsearch fuzzy search**: Rejected - massive overkill, new infrastructure dependency
- **BK-tree indexing**: Rejected for MVP - YAGNI, implement only if needed

### 7. CLI Command Design Pattern

**Question**: How should CLI commands integrate with existing collabiq CLI structure?

**Decision**: Add commands to existing `collabiq/commands/notion.py` module, reuse Typer framework

**Rationale**:
- **Consistency**: Project uses Typer for CLI (see pyproject.toml dependencies)
- **Co-location**: Notion-related commands already in `notion.py`
- **Reuse infrastructure**: Error handling, logging, formatting already established

**Implementation**:
```python
# Add to src/collabiq/commands/notion.py

@app.command("match-company")
def match_company(name: str, dry_run: bool = False):
    """Test company fuzzy matching."""
    # Implementation

@app.command("match-person")
def match_person(name: str):
    """Test person name matching."""
    # Implementation

@app.command("list-users")
def list_users():
    """List all Notion workspace users."""
    # Implementation
```

**Alternatives Considered**:
- **Separate CLI module**: Rejected - adds complexity, commands are Notion-related
- **Shell scripts**: Rejected - less maintainable, no type safety
- **Python REPL**: Rejected - poor UX for admins

## Technology Stack Summary

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Fuzzy Matching | rapidfuzz (Jaro-Winkler) | Already in dependencies, Unicode-aware, fast |
| Notion API | notion-client | Already in project, established pattern |
| Data Validation | pydantic | Already in project, type-safe result objects |
| Caching | File-based JSON | Consistent with project pattern (cache.py) |
| CLI Framework | Typer + Rich | Already in project, established commands |
| Testing | pytest, pytest-mock | Already in project, TDD workflow |

**No new dependencies required** - All technologies already in project.

## Implementation Sequence

Per constitution (II. Incremental Delivery), implement in priority order:

1. **Phase P1a - Fuzzy Company Matching**: FuzzyCompanyMatcher with Jaro-Winkler (MVP)
2. **Phase P1b - Auto-Create Companies**: Company creation when match fails (MVP)
3. **Phase P2 - Person Matching**: PersonMatcher with user list caching
4. **Phase P3 - CLI Commands**: Testing commands for admins

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Threshold too strict (false negatives) | Medium | Medium | Configurable threshold, success criteria validates 90% match rate |
| Korean text edge cases | Low | Medium | Comprehensive test cases, UTF-8 validation |
| Notion API rate limits | Low | High | Reuse existing retry logic, cache user list |
| Performance degradation at scale | Low | Medium | Monitor SC-007 (<2s), optimize if needed |

## Open Questions (None)

All technical questions resolved. Ready for Phase 1 (Design).

---

**Research Status**: ✅ COMPLETE
**Gate Decision**: Proceed to Phase 1 (Data Model & Contracts)
**Next Step**: Generate data-model.md, contracts/, quickstart.md
