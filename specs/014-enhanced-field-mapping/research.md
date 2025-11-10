# Technical Research: Enhanced Notion Field Mapping

**Feature**: 014-enhanced-field-mapping
**Date**: 2025-11-10
**Status**: Complete

## Research Questions

### 1. Fuzzy String Matching Algorithm Selection

**Question**: Which fuzzy string matching algorithm is most appropriate for Korean company names with spelling variations?

**Decision**: Use Jaro-Winkler similarity via `rapidfuzz` library

**Rationale**:
- **rapidfuzz** is already in project dependencies (pyproject.toml line 26), no new dependency needed
- Jaro-Winkler is specifically designed for short strings (company names typically <50 characters)
- Handles character-level differences well (워크 vs 웍, spacing differences)
- Provides normalized similarity score 0.0-1.0, enabling threshold-based matching
- Performs well on Korean text (Unicode-aware, no special preprocessing needed)
- Fast: O(n*m) complexity acceptable for <1000 companies

**Alternatives Considered**:
- **Levenshtein distance**: Rejected - absolute distance not normalized, harder to set universal threshold
- **Cosine similarity**: Rejected - overkill for short strings, requires tokenization
- **Soundex/Metaphone**: Rejected - designed for English phonetics, not Korean text
- **ML-based matching**: Rejected per constitution (V. Simplicity) - deterministic approach sufficient

**Implementation**:
```python
from rapidfuzz import fuzz

# Jaro-Winkler similarity (0.0-1.0)
similarity = fuzz.ratio(extracted_name, db_name) / 100.0
```

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
