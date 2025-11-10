# Data Model: Enhanced Notion Field Mapping

**Feature**: 014-enhanced-field-mapping
**Date**: 2025-11-10
**Status**: Complete

## Overview

This document defines the data entities, relationships, and validation rules for the Enhanced Notion Field Mapping feature. The data model focuses on the result objects returned by matching services and the cached data structures.

## Entities

### 1. CompanyMatch

Represents the result of fuzzy matching a company name to the Companies database.

**Purpose**: Return matched company page_id with confidence metrics for relation field population.

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `page_id` | str \| None | Yes | Notion page ID format if present | Matched company's Notion page ID, None if no match |
| `company_name` | str | Yes | Non-empty string | Name of matched company from database |
| `similarity_score` | float | Yes | 0.0 ≤ score ≤ 1.0 | Jaro-Winkler similarity (0.0-1.0) |
| `match_type` | Enum | Yes | "exact" \| "fuzzy" \| "created" \| "none" | How the match was determined |
| `confidence_level` | Enum | Yes | "high" \| "medium" \| "low" \| "none" | Confidence in the match |
| `was_created` | bool | Yes | True if new entry created | Whether company was auto-created |

**Validation Rules**:
- If `page_id` is None, then `match_type` must be "none"
- If `was_created` is True, then `match_type` must be "created"
- If `match_type` is "exact", then `similarity_score` must be 1.0
- If `match_type` is "fuzzy", then 0.85 ≤ `similarity_score` < 1.0
- If `match_type` is "none", then `similarity_score` < 0.85

**Confidence Levels**:
- **high**: similarity_score ≥ 0.95 or exact match
- **medium**: 0.85 ≤ similarity_score < 0.95
- **low**: 0.70 ≤ similarity_score < 0.85 (below company threshold but logged)
- **none**: similarity_score < 0.70

**State Transitions**:
```
Input: Extracted company name
  → Search exact match → EXACT (similarity=1.0, high confidence)
  → Search fuzzy match → FUZZY (similarity≥0.85, medium/high confidence)
  → Auto-create → CREATED (new page_id, high confidence)
  → No match → NONE (page_id=None, no confidence)
```

**Example**:
```python
CompanyMatch(
    page_id="abc123def456",
    company_name="웨이크",
    similarity_score=0.87,
    match_type="fuzzy",
    confidence_level="medium",
    was_created=False
)
```

---

### 2. PersonMatch

Represents the result of matching a person name to Notion workspace users.

**Purpose**: Return user UUID(s) for people field population with ambiguity indicators.

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `user_id` | str \| None | Yes | Notion user UUID format if present | Matched user's Notion UUID, None if no match |
| `user_name` | str \| None | Yes | Non-empty if user_id present | Full name of matched user |
| `similarity_score` | float | Yes | 0.0 ≤ score ≤ 1.0 | Name similarity score |
| `match_type` | Enum | Yes | "exact" \| "fuzzy" \| "none" | How the match was determined |
| `confidence_level` | Enum | Yes | "high" \| "medium" \| "low" \| "none" | Confidence in the match |
| `is_ambiguous` | bool | Yes | - | Whether multiple users had similar scores |
| `alternative_matches` | List[Dict] | No | List of {user_id, user_name, score} | Other potential matches (if ambiguous) |

**Validation Rules**:
- If `user_id` is None, then `match_type` must be "none"
- If `match_type` is "exact", then `similarity_score` must be 1.0
- If `match_type` is "fuzzy", then 0.70 ≤ `similarity_score` < 1.0
- If `match_type` is "none", then `similarity_score` < 0.70
- If `is_ambiguous` is True, then `alternative_matches` must be non-empty

**Confidence Levels**:
- **high**: similarity_score ≥ 0.90 and not ambiguous
- **medium**: 0.80 ≤ similarity_score < 0.90 or ambiguous
- **low**: 0.70 ≤ similarity_score < 0.80
- **none**: similarity_score < 0.70

**Ambiguity Detection**:
- If multiple users have similarity ≥ 0.70 and difference between top 2 scores < 0.10, mark ambiguous
- Log ambiguous matches for manual review (per FR-012)

**Example**:
```python
PersonMatch(
    user_id="user-uuid-789",
    user_name="김철수 (Cheolsu Kim)",
    similarity_score=0.95,
    match_type="exact",
    confidence_level="high",
    is_ambiguous=False,
    alternative_matches=[]
)
```

---

### 3. NotionUser (Cached)

Represents a Notion workspace user stored in cache for person matching.

**Purpose**: Cache Notion workspace users to minimize API calls during person matching.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Notion user UUID |
| `name` | str | Yes | Full name as appears in Notion |
| `email` | str | No | Email address (if available) |
| `type` | str | Yes | User type: "person" or "bot" |

**Cache Structure**:
```json
{
  "version": "1.0",
  "cached_at": "2025-11-10T10:30:00Z",
  "ttl_seconds": 86400,
  "users": [
    {
      "id": "user-uuid-123",
      "name": "김철수 (Cheolsu Kim)",
      "email": "cheolsu@example.com",
      "type": "person"
    }
  ]
}
```

**Cache Location**: `data/notion_cache/users_list.json`

**Cache Invalidation**: TTL-based (24 hours)

---

### 4. CompanyDatabase (External)

Represents the existing Companies database in Notion (not created by this feature).

**Purpose**: Reference for understanding the source of truth for company data.

**Key Properties**:
- **Title**: Company name (primary key for exact matching)
- **Type**: Notion database
- **Access**: Read via NotionFetcher, Write via NotionWriter

**Usage Pattern**:
1. Fetch all companies: `NotionFetcher.fetch_all_companies()`
2. Fuzzy match against titles
3. Create new entry if no match: `NotionWriter.create_company_entry()`

---

## Relationships

```
┌─────────────────────┐
│ Extracted Company   │
│ Name (LLM Output)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│ FuzzyCompanyMatcher │─────>│ CompanyMatch     │
│                     │      │ (Result Object)  │
└──────────┬──────────┘      └──────────────────┘
           │
           │ queries
           ▼
┌─────────────────────┐
│ Companies Database  │
│ (Notion)            │
└─────────────────────┘

┌─────────────────────┐
│ Extracted Person    │
│ Name (LLM Output)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│ PersonMatcher       │─────>│ PersonMatch      │
│                     │      │ (Result Object)  │
└──────────┬──────────┘      └──────────────────┘
           │
           │ uses cache
           ▼
┌─────────────────────┐      ┌──────────────────┐
│ Users List (Cache)  │<─────│ Notion API       │
│ (File-based JSON)   │      │ (list users)     │
└─────────────────────┘      └──────────────────┘
```

---

## Validation Rules Summary

### Company Matching Thresholds

| Threshold | Action | Confidence |
|-----------|--------|------------|
| 1.0 | Exact match | High |
| ≥ 0.95 | Fuzzy match, use page_id | High |
| 0.85-0.94 | Fuzzy match, use page_id | Medium |
| < 0.85 | Auto-create new company | High (new entry) |

### Person Matching Thresholds

| Threshold | Action | Confidence |
|-----------|--------|------------|
| 1.0 | Exact match, use user_id | High |
| ≥ 0.90 | Fuzzy match, use user_id (if not ambiguous) | High |
| 0.80-0.89 | Fuzzy match, use user_id, log if ambiguous | Medium |
| 0.70-0.79 | Fuzzy match, use user_id, log warning | Low |
| < 0.70 | No match, leave field empty | None |

### Ambiguity Detection

```
is_ambiguous = (
    len(matches_above_threshold) > 1
    AND (top_score - second_score) < 0.10
)
```

---

## Data Flow

### Company Field Population Flow

```
1. LLM extracts company name: "웨이크(산스)"
2. FieldMapper calls FuzzyCompanyMatcher.match(company_name)
3. FuzzyCompanyMatcher:
   a. Search exact match in Companies DB → Not found
   b. Compute similarity for all companies → "웨이크" = 0.87
   c. Best match ≥ 0.85? → Yes
   d. Return CompanyMatch(page_id="abc123", similarity=0.87, match_type="fuzzy")
4. FieldMapper uses page_id to populate relation field
5. NotionWriter creates CollabIQ entry with populated relation
```

### Person Field Population Flow

```
1. LLM extracts person name: "김철수"
2. FieldMapper calls PersonMatcher.match(person_name)
3. PersonMatcher:
   a. Load cached user list (or fetch if stale)
   b. Compute similarity for all users
   c. Best match: "김철수 (Cheolsu Kim)" = 1.0 (exact)
   d. Check ambiguity → No other high matches
   e. Return PersonMatch(user_id="user-789", similarity=1.0, match_type="exact")
4. FieldMapper uses user_id to populate people field
5. NotionWriter creates CollabIQ entry with populated people field
```

---

## Pydantic Models (Implementation Reference)

```python
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class CompanyMatch(BaseModel):
    """Result of fuzzy company matching."""
    page_id: Optional[str] = Field(None, description="Notion page ID of matched company")
    company_name: str = Field(..., description="Name of matched company")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Jaro-Winkler similarity")
    match_type: Literal["exact", "fuzzy", "created", "none"]
    confidence_level: Literal["high", "medium", "low", "none"]
    was_created: bool = Field(False, description="Whether company was auto-created")

    @field_validator("similarity_score")
    def validate_similarity(cls, v, info):
        match_type = info.data.get("match_type")
        if match_type == "exact" and v != 1.0:
            raise ValueError("Exact match must have similarity 1.0")
        if match_type == "fuzzy" and not (0.85 <= v < 1.0):
            raise ValueError("Fuzzy match must have similarity 0.85-0.99")
        return v

class PersonMatch(BaseModel):
    """Result of person name matching."""
    user_id: Optional[str] = Field(None, description="Notion user UUID")
    user_name: Optional[str] = Field(None, description="Full name of matched user")
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    match_type: Literal["exact", "fuzzy", "none"]
    confidence_level: Literal["high", "medium", "low", "none"]
    is_ambiguous: bool = Field(False, description="Multiple similar matches found")
    alternative_matches: List[Dict[str, str]] = Field(default_factory=list)

class NotionUser(BaseModel):
    """Cached Notion workspace user."""
    id: str
    name: str
    email: Optional[str] = None
    type: str = Field(..., pattern="^(person|bot)$")

class UserListCache(BaseModel):
    """Cached user list with metadata."""
    version: str = "1.0"
    cached_at: datetime
    ttl_seconds: int = 86400  # 24 hours
    users: List[NotionUser]
```

---

## Migration Notes

**No database migrations required** - This feature works with existing Notion databases:
- Companies database (already exists)
- CollabIQ database (already exists with relation fields)

**Cache initialization**:
- User list cache will be created on first PersonMatcher invocation
- Cache location: `data/notion_cache/users_list.json`

---

**Document Status**: ✅ COMPLETE
**Next Step**: Generate contracts/ directory with API specifications
