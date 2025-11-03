"""Pydantic models for LLM entity extraction.

This module defines the data models used for entity extraction:
- ExtractedEntities: 5 key entities extracted from email
- ConfidenceScores: Per-field confidence scores (0.0-1.0)
- ExtractionBatch: Batch processing job
- BatchSummary: Processing metadata and statistics
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ConfidenceScores(BaseModel):
    """Confidence scores (0.0-1.0) for each extracted entity.

    Attributes:
        person: Confidence for person_in_charge
        startup: Confidence for startup_name
        partner: Confidence for partner_org
        details: Confidence for details
        date: Confidence for date
    """

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
        """Check if any field has confidence below threshold.

        Args:
            threshold: Minimum confidence threshold (default: 0.85)

        Returns:
            True if any field has confidence below threshold, False otherwise
        """
        return any(
            score < threshold
            for score in [self.person, self.startup, self.partner, self.details, self.date]
        )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "person": 0.95,
                "startup": 0.92,
                "partner": 0.88,
                "details": 0.90,
                "date": 0.85,
            }
        }


class ExtractedEntities(BaseModel):
    """Entity extraction results from a single email.

    Attributes:
        person_in_charge: 담당자 - Person responsible for collaboration
        startup_name: 스타트업명 - Name of startup company
        partner_org: 협업기관 - Partner organization
        details: 협업내용 - Collaboration description (original text preserved)
        date: 날짜 - Collaboration date (parsed to datetime)
        confidence: Confidence scores (0.0-1.0) for each extracted field
        email_id: Unique email identifier
        extracted_at: UTC timestamp when extraction occurred
        matched_company_id: Notion page ID for matched startup (Phase 2b)
        matched_partner_id: Notion page ID for matched partner (Phase 2b)
        startup_match_confidence: Confidence score for startup match (Phase 2b)
        partner_match_confidence: Confidence score for partner match (Phase 2b)
    """

    # Phase 1b fields (existing)
    person_in_charge: Optional[str] = Field(
        None,
        max_length=100,
        description="담당자 - Person responsible for collaboration",
    )
    startup_name: Optional[str] = Field(
        None,
        max_length=200,
        description="스타트업명 - Name of startup company",
    )
    partner_org: Optional[str] = Field(
        None,
        max_length=200,
        description="협업기관 - Partner organization",
    )
    details: Optional[str] = Field(
        None,
        max_length=2000,
        description="협업내용 - Collaboration description (original text preserved)",
    )
    date: Optional[datetime] = Field(
        None,
        description="날짜 - Collaboration date (parsed to datetime)",
    )
    confidence: ConfidenceScores = Field(
        ...,
        description="Confidence scores (0.0-1.0) for each extracted field",
    )
    email_id: str = Field(
        ...,
        min_length=1,
        description="Unique email identifier (from Phase 1a duplicate tracker)",
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="UTC timestamp when extraction occurred",
    )

    # Phase 2b fields (new - optional, backward compatible)
    matched_company_id: Optional[str] = Field(
        None,
        min_length=32,
        max_length=36,
        description="Notion page ID for matched startup (32 or 36 chars)",
    )
    matched_partner_id: Optional[str] = Field(
        None,
        min_length=32,
        max_length=36,
        description="Notion page ID for matched partner organization (32 or 36 chars)",
    )
    startup_match_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) for startup company match",
    )
    partner_match_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) for partner organization match",
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_scores(cls, v: ConfidenceScores) -> ConfidenceScores:
        """Ensure all confidence scores are 0.0-1.0."""
        # Validation handled by ConfidenceScores model
        return v

    @field_validator("startup_match_confidence", "partner_match_confidence")
    @classmethod
    def validate_match_confidence_range(cls, v: Optional[float]) -> Optional[float]:
        """Ensure match confidence scores are 0.0-1.0 if provided."""
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError(f"Match confidence must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("matched_company_id", "matched_partner_id")
    @classmethod
    def validate_notion_page_id_format(cls, v: Optional[str]) -> Optional[str]:
        """Ensure Notion page IDs are 32 or 36 characters (UUID format)."""
        if v is not None:
            if len(v) not in (32, 36):
                raise ValueError(
                    f"Notion page ID must be 32 or 36 characters (UUID format), got {len(v)} characters"
                )
        return v

    class Config:
        """Pydantic configuration."""

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
                    "date": 0.85,
                },
                "email_id": "msg_abc123",
                "extracted_at": "2025-11-01T10:30:00Z",
                "matched_company_id": "abc123def456ghi789jkl012mno345pq",
                "matched_partner_id": "stu901vwx234yz056abc123def456ghi",
                "startup_match_confidence": 0.95,
                "partner_match_confidence": 0.92,
            }
        }


class BatchSummary(BaseModel):
    """Processing summary for a batch job.

    Attributes:
        total_count: Total number of emails in batch
        success_count: Number of successful extractions
        failure_count: Number of failed extractions
        processing_time_seconds: Total processing time
    """

    total_count: int = Field(..., ge=1, description="Total emails in batch")
    success_count: int = Field(..., ge=0, description="Successful extractions")
    failure_count: int = Field(..., ge=0, description="Failed extractions")
    processing_time_seconds: float = Field(..., ge=0.0, description="Total processing time")

    @field_validator("success_count", "failure_count")
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """Ensure counts don't exceed total_count."""
        if "total_count" in info.data and v > info.data["total_count"]:
            raise ValueError(
                f"Count ({v}) cannot exceed total_count ({info.data['total_count']})"
            )
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "total_count": 20,
                "success_count": 18,
                "failure_count": 2,
                "processing_time_seconds": 45.3,
            }
        }


class ExtractionBatch(BaseModel):
    """Batch processing job for multiple emails.

    Attributes:
        batch_id: Unique batch identifier (UUID)
        emails: List of email texts to process
        results: Extraction results (populated after processing)
        summary: Processing summary statistics
    """

    batch_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique batch identifier (UUID)",
    )
    emails: List[str] = Field(
        ...,
        min_length=1,
        description="List of email texts to process",
    )
    results: List[ExtractedEntities] = Field(
        default_factory=list,
        description="Extraction results (populated after processing)",
    )
    summary: BatchSummary = Field(
        ...,
        description="Processing summary statistics",
    )

    @field_validator("results")
    @classmethod
    def validate_results_length(cls, v: List[ExtractedEntities], info) -> List[ExtractedEntities]:
        """Ensure results length matches emails length (after processing)."""
        if "emails" in info.data and len(v) > 0:
            if len(v) != len(info.data["emails"]):
                raise ValueError(
                    f"Results length ({len(v)}) must match emails length ({len(info.data['emails'])})"
                )
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "emails": ["email text 1", "email text 2", "..."],
                "results": [
                    {"email_id": "msg_001", "person_in_charge": "김철수", "...": "..."},
                    {"email_id": "msg_002", "person_in_charge": "이영희", "...": "..."},
                ],
                "summary": {
                    "total_count": 20,
                    "success_count": 18,
                    "failure_count": 2,
                    "processing_time_seconds": 45.3,
                },
            }
        }
