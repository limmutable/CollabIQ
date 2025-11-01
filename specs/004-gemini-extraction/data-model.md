# Data Model: Gemini Entity Extraction

**Feature**: 004-gemini-extraction
**Date**: 2025-11-01
**Phase**: Phase 1 - Design

## Overview

This document defines the data models for entity extraction from collaboration emails. All models use Pydantic for validation and are designed to be serializable to JSON for storage and API responses.

---

## Core Entities

### 1. ExtractedEntities

Represents the 5 key pieces of information extracted from a collaboration email.

**Purpose**: Store extraction results with confidence scores for each field.

**Fields**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `person_in_charge` | `Optional[str]` | No | 담당자 - Person responsible for collaboration | Max length: 100 chars |
| `startup_name` | `Optional[str]` | No | 스타트업명 - Name of startup company | Max length: 200 chars |
| `partner_org` | `Optional[str]` | No | 협업기관 - Partner organization | Max length: 200 chars |
| `details` | `Optional[str]` | No | 협업내용 - Collaboration description (original text) | Max length: 2000 chars |
| `date` | `Optional[datetime]` | No | 날짜 - Collaboration date | Must be valid date, can be past or future |
| `confidence` | `ConfidenceScores` | Yes | Per-field confidence scores (0.0-1.0) | See ConfidenceScores model |
| `email_id` | `str` | Yes | Unique identifier from email source | Non-empty string |
| `extracted_at` | `datetime` | Yes | Timestamp when extraction occurred | Auto-set to current UTC time |

**Relationships**:
- Has one `ConfidenceScores` object (embedded)
- Belongs to one `ExtractionBatch` (if processed in batch)

**Pydantic Model**:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ExtractedEntities(BaseModel):
    """Entity extraction results from a single email."""

    person_in_charge: Optional[str] = Field(
        None,
        max_length=100,
        description="담당자 - Person responsible for collaboration"
    )
    startup_name: Optional[str] = Field(
        None,
        max_length=200,
        description="스타트업명 - Name of startup company"
    )
    partner_org: Optional[str] = Field(
        None,
        max_length=200,
        description="협업기관 - Partner organization"
    )
    details: Optional[str] = Field(
        None,
        max_length=2000,
        description="협업내용 - Collaboration description (original text preserved)"
    )
    date: Optional[datetime] = Field(
        None,
        description="날짜 - Collaboration date (parsed to datetime)"
    )
    confidence: ConfidenceScores = Field(
        ...,
        description="Confidence scores (0.0-1.0) for each extracted field"
    )
    email_id: str = Field(
        ...,
        min_length=1,
        description="Unique email identifier (from Phase 1a duplicate tracker)"
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="UTC timestamp when extraction occurred"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_scores(cls, v: ConfidenceScores) -> ConfidenceScores:
        """Ensure all confidence scores are 0.0-1.0."""
        # Validation handled by ConfidenceScores model
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "person_in_charge": "김철수",
                "startup_name": "본봄",
                "partner_org": "신세계인터내셔널",
                "details": "11월 1주 PoC 시작 예정, 파일럿 킥오프 완료",
                "date": "2025-11-01T00:00:00Z",
                "confidence": {
                    "person": 0.95,
                    "startup": 0.92,
                    "partner": 0.88,
                    "details": 0.90,
                    "date": 0.85
                },
                "email_id": "msg_abc123",
                "extracted_at": "2025-11-01T10:30:00Z"
            }
        }
```

**Business Rules**:
1. Missing entities MUST have `None` value with confidence 0.0 (FR-004)
2. `details` field MUST preserve original text without summarization (FR-007)
3. `email_id` MUST be unique per extraction (no duplicates)
4. `date` MUST be parsed to UTC datetime (time component optional, defaults to 00:00:00)

---

### 2. ConfidenceScores

Stores confidence scores (0.0-1.0) for each extracted entity field.

**Purpose**: Enable filtering of low-confidence extractions for manual review (User Story P3).

**Fields**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `person` | `float` | Yes | Confidence for person_in_charge | 0.0 ≤ value ≤ 1.0 |
| `startup` | `float` | Yes | Confidence for startup_name | 0.0 ≤ value ≤ 1.0 |
| `partner` | `float` | Yes | Confidence for partner_org | 0.0 ≤ value ≤ 1.0 |
| `details` | `float` | Yes | Confidence for details | 0.0 ≤ value ≤ 1.0 |
| `date` | `float` | Yes | Confidence for date | 0.0 ≤ value ≤ 1.0 |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, field_validator

class ConfidenceScores(BaseModel):
    """Confidence scores (0.0-1.0) for each extracted entity."""

    person: float = Field(..., ge=0.0, le=1.0, description="Confidence for person_in_charge")
    startup: float = Field(..., ge=0.0, le=1.0, description="Confidence for startup_name")
    partner: float = Field(..., ge=0.0, le=1.0, description="Confidence for partner_org")
    details: float = Field(..., ge=0.0, le=1.0, description="Confidence for details")
    date: float = Field(..., ge=0.0, le=1.0, description="Confidence for date")

    @field_validator("person", "startup", "partner", "details", "date")
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure confidence scores are in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence score must be 0.0-1.0, got {v}")
        return v

    def has_low_confidence(self, threshold: float = 0.85) -> bool:
        """Check if any field has confidence below threshold."""
        return any(score < threshold for score in [
            self.person, self.startup, self.partner, self.details, self.date
        ])

    class Config:
        json_schema_extra = {
            "example": {
                "person": 0.95,
                "startup": 0.92,
                "partner": 0.88,
                "details": 0.90,
                "date": 0.85
            }
        }
```

**Business Rules**:
1. Confidence 0.0 indicates missing/not found entity (FR-004)
2. Confidence <0.85 flags extraction for manual review (User Story P3)
3. Confidence ≥0.85 indicates high-confidence extraction (SC-003)

---

### 3. ExtractionBatch

Represents a batch processing job for multiple emails.

**Purpose**: Support batch processing (User Story P2) with summary statistics.

**Fields**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `batch_id` | `str` | Yes | Unique batch identifier | UUID format or timestamp-based |
| `emails` | `List[str]` | Yes | List of email texts to process | Non-empty list |
| `results` | `List[ExtractedEntities]` | Yes | Extraction results (one per email) | Length matches emails length |
| `summary` | `BatchSummary` | Yes | Processing metadata and statistics | See BatchSummary model |

**Pydantic Model**:
```python
from typing import List
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4

class ExtractionBatch(BaseModel):
    """Batch processing job for multiple emails."""

    batch_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique batch identifier (UUID)"
    )
    emails: List[str] = Field(
        ...,
        min_length=1,
        description="List of email texts to process"
    )
    results: List[ExtractedEntities] = Field(
        default_factory=list,
        description="Extraction results (populated after processing)"
    )
    summary: BatchSummary = Field(
        ...,
        description="Processing summary statistics"
    )

    @field_validator("results")
    @classmethod
    def validate_results_length(cls, v: List[ExtractedEntities], info) -> List[ExtractedEntities]:
        """Ensure results length matches emails length (after processing)."""
        if "emails" in info.data and len(v) > 0:
            if len(v) != len(info.data["emails"]):
                raise ValueError(f"Results length ({len(v)}) must match emails length ({len(info.data['emails'])})")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "emails": ["email text 1", "email text 2", "..."],
                "results": [
                    {"email_id": "msg_001", "person_in_charge": "김철수", "...": "..."},
                    {"email_id": "msg_002", "person_in_charge": "이영희", "...": "..."}
                ],
                "summary": {
                    "total_count": 20,
                    "success_count": 18,
                    "failure_count": 2,
                    "processing_time_seconds": 45.3
                }
            }
        }
```

**Business Rules**:
1. Batch processing continues on errors (FR-006)
2. Failed extractions marked with error status in results
3. Summary counts MUST sum to total_count

---

### 4. BatchSummary

Processing metadata and statistics for a batch job.

**Purpose**: Report batch processing outcomes (User Story P2, Acceptance Scenario 3).

**Fields**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| `total_count` | `int` | Yes | Total number of emails in batch | Must be ≥ 1 |
| `success_count` | `int` | Yes | Number of successful extractions | 0 ≤ value ≤ total_count |
| `failure_count` | `int` | Yes | Number of failed extractions | 0 ≤ value ≤ total_count |
| `processing_time_seconds` | `float` | Yes | Total processing time | Must be ≥ 0.0 |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, field_validator

class BatchSummary(BaseModel):
    """Processing summary for a batch job."""

    total_count: int = Field(..., ge=1, description="Total emails in batch")
    success_count: int = Field(..., ge=0, description="Successful extractions")
    failure_count: int = Field(..., ge=0, description="Failed extractions")
    processing_time_seconds: float = Field(..., ge=0.0, description="Total processing time")

    @field_validator("success_count", "failure_count")
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """Ensure counts don't exceed total_count."""
        if "total_count" in info.data and v > info.data["total_count"]:
            raise ValueError(f"Count ({v}) cannot exceed total_count ({info.data['total_count']})")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 20,
                "success_count": 18,
                "failure_count": 2,
                "processing_time_seconds": 45.3
            }
        }
```

**Business Rules**:
1. `success_count + failure_count = total_count` (always)
2. Processing time includes Gemini API latency
3. Average time per email = processing_time_seconds / total_count

---

## State Transitions

**Note**: This is a stateless extraction system (no workflow states).

Entities are created once and not modified. If re-extraction is needed, create a new `ExtractedEntities` instance with updated `extracted_at` timestamp.

---

## Validation Summary

### Field Constraints

| Model | Field | Constraint | Error Message |
|-------|-------|-----------|---------------|
| `ExtractedEntities` | `person_in_charge` | max_length=100 | "Person name too long (max 100 chars)" |
| `ExtractedEntities` | `startup_name` | max_length=200 | "Startup name too long (max 200 chars)" |
| `ExtractedEntities` | `partner_org` | max_length=200 | "Partner org name too long (max 200 chars)" |
| `ExtractedEntities` | `details` | max_length=2000 | "Details text too long (max 2000 chars)" |
| `ExtractedEntities` | `email_id` | min_length=1 | "Email ID cannot be empty" |
| `ConfidenceScores` | all fields | 0.0 ≤ value ≤ 1.0 | "Confidence must be 0.0-1.0, got {value}" |
| `ExtractionBatch` | `emails` | min_length=1 | "Batch must contain at least 1 email" |
| `BatchSummary` | `total_count` | ≥ 1 | "Total count must be at least 1" |

### Cross-Field Validation

1. **ConfidenceScores**: If entity field is `None`, confidence MUST be 0.0
2. **ExtractionBatch**: `len(results) == len(emails)` after processing
3. **BatchSummary**: `success_count + failure_count == total_count`

---

## JSON Serialization

All models support JSON serialization for:
- File storage (`data/extractions/{email_id}.json`)
- API responses (future)
- Manual review interface (User Story P3)

**Example JSON Output** (single extraction):
```json
{
  "person_in_charge": "김철수",
  "startup_name": "본봄",
  "partner_org": "신세계인터내셔널",
  "details": "11월 1주 PoC 시작 예정, 파일럿 킥오프 완료",
  "date": "2025-11-01T00:00:00Z",
  "confidence": {
    "person": 0.95,
    "startup": 0.92,
    "partner": 0.88,
    "details": 0.90,
    "date": 0.85
  },
  "email_id": "msg_abc123",
  "extracted_at": "2025-11-01T10:30:00Z"
}
```

---

**Data Model Complete**: ✅
**Next Step**: Create API contracts (contracts/llm_provider.yaml)
