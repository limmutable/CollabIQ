"""Pydantic models for LLM entity extraction.

This module defines the data models used for entity extraction:
- ExtractedEntities: 5 key entities extracted from email
- ConfidenceScores: Per-field confidence scores (0.0-1.0)
- ExtractionBatch: Batch processing job
- BatchSummary: Processing metadata and statistics
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
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

    person: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence for person_in_charge"
    )
    startup: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence for startup_name"
    )
    partner: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence for partner_org"
    )
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
            for score in [
                self.person,
                self.startup,
                self.partner,
                self.details,
                self.date,
            ]
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


class ExtractedEntitiesWithClassification(ExtractedEntities):
    """Extended model with Phase 2c classification and summarization.

    Extends ExtractedEntities with:
    - Collaboration type classification (dynamically fetched from Notion)
    - Collaboration intensity classification (LLM-based Korean semantic analysis)
    - Collaboration summary (3-5 sentences preserving 5 key entities)
    - Confidence scores for auto-acceptance vs manual review

    All Phase 2c fields are optional for backward compatibility.

    Attributes:
        collaboration_type: Exact Notion field value from 협업형태 property
        collaboration_intensity: Intensity level (이해/협력/투자/인수)
        type_confidence: Type classification confidence (0.0-1.0)
        intensity_confidence: Intensity classification confidence (0.0-1.0)
        collaboration_summary: 3-5 sentence summary (50-150 words)
        summary_word_count: Summary word count for validation
        key_entities_preserved: Which key entities are in summary
        classification_timestamp: ISO 8601 timestamp of classification
    """

    # Phase 2c classification fields
    collaboration_type: Optional[str] = Field(
        None,
        description="Exact Notion field value from 협업형태 property (e.g., '[A]PortCoXSSG')",
    )

    collaboration_intensity: Optional[str] = Field(
        None,
        description="Intensity level: 이해, 협력, 투자, 인수",
        pattern=r"^(이해|협력|투자|인수)$",
    )

    type_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Type classification confidence (0.0-1.0)",
    )

    intensity_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Intensity classification confidence (0.0-1.0)",
    )

    intensity_reasoning: Optional[str] = Field(
        None,
        max_length=500,
        description="1-2 sentence explanation for intensity classification",
    )

    # Phase 2c summary fields
    collaboration_summary: Optional[str] = Field(
        None,
        min_length=50,
        max_length=750,  # ~150 words * 5 chars/word
        description="3-5 sentence summary (50-150 words)",
    )

    summary_word_count: Optional[int] = Field(
        None,
        ge=50,
        le=150,
        description="Summary word count for validation",
    )

    key_entities_preserved: Optional[dict] = Field(
        None,
        description="Boolean flags for which key entities are in summary",
    )

    classification_timestamp: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of classification",
    )

    # Phase 3 person matching field (US3)
    matched_person_id: Optional[str] = Field(
        None,
        min_length=32,
        max_length=36,
        description="Notion user UUID for matched person_in_charge (32 or 36 chars)",
    )

    @field_validator("collaboration_type")
    @classmethod
    def validate_type_format(cls, v: Optional[str]) -> Optional[str]:
        """Ensure type follows [X]* pattern."""
        if v is not None:
            if not re.match(r"^\[([A-Z0-9]+)\]", v):
                raise ValueError(f"Invalid collaboration_type format: {v}")
        return v

    @field_validator("collaboration_intensity")
    @classmethod
    def validate_intensity(cls, v: Optional[str]) -> Optional[str]:
        """Ensure intensity is one of 4 valid values."""
        if v is not None:
            valid = ["이해", "협력", "투자", "인수"]
            if v not in valid:
                raise ValueError(
                    f"Invalid collaboration_intensity: {v}, must be one of {valid}"
                )
        return v

    def needs_manual_review(self, threshold: float = 0.85) -> bool:
        """Check if classification needs manual review based on confidence threshold.

        Args:
            threshold: Minimum confidence threshold (default: 0.85)

        Returns:
            True if any classification confidence is below threshold, False otherwise
        """
        if self.type_confidence is not None and self.type_confidence < threshold:
            return True
        if (
            self.intensity_confidence is not None
            and self.intensity_confidence < threshold
        ):
            return True
        return False

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                # Phase 1b fields
                "person_in_charge": "김주영",
                "startup_name": "브레이크앤컴퍼니",
                "partner_org": "신세계푸드",
                "details": "AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅",
                "date": "2025-10-28T00:00:00Z",
                "confidence": {
                    "person": 0.95,
                    "startup": 0.92,
                    "partner": 0.88,
                    "details": 0.90,
                    "date": 0.85,
                },
                "email_id": "msg_abc123",
                "extracted_at": "2025-11-03T10:30:00Z",
                # Phase 2b fields
                "matched_company_id": "abc123def456ghi789jkl012mno345pq",
                "matched_partner_id": "stu901vwx234yz056abc123def456ghi",
                "startup_match_confidence": 0.95,
                "partner_match_confidence": 0.98,
                # Phase 2c fields
                "collaboration_type": "[A]PortCoXSSG",
                "collaboration_intensity": "협력",
                "type_confidence": 0.95,
                "intensity_confidence": 0.88,
                "collaboration_summary": "브레이크앤컴퍼니와 신세계푸드가 AI 기반 재고 최적화 솔루션 PoC 킥오프 미팅을 진행했습니다. 11월 첫째 주부터 2개월간 파일럿 테스트 예정입니다. 김주영 담당자가 프로젝트를 주도합니다.",
                "summary_word_count": 42,
                "key_entities_preserved": {
                    "startup": True,
                    "partner": True,
                    "activity": True,
                    "date": True,
                    "person": True,
                },
                "classification_timestamp": "2025-11-03T10:30:00Z",
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
    processing_time_seconds: float = Field(
        ..., ge=0.0, description="Total processing time"
    )

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
    def validate_results_length(
        cls, v: List[ExtractedEntities], info
    ) -> List[ExtractedEntities]:
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


class WriteResult(BaseModel):
    """Result of a Notion write operation.

    Attributes:
        success: Whether the write operation succeeded
        page_id: Notion page ID if created successfully
        email_id: Email identifier for tracking
        error_type: Exception class name if failed
        error_message: Human-readable error message if failed
        status_code: HTTP status code from Notion API if failed
        retry_count: Number of retry attempts made
        is_duplicate: Whether write was skipped due to duplicate
        existing_page_id: Page ID of existing duplicate entry
    """

    success: bool = Field(..., description="Whether write operation succeeded")
    page_id: Optional[str] = Field(None, description="Notion page ID if created")
    email_id: str = Field(..., description="Email identifier for tracking")
    error_type: Optional[str] = Field(
        None, description="Exception class name if failed"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    status_code: Optional[int] = Field(None, description="HTTP status code if failed")
    retry_count: int = Field(0, ge=0, le=3, description="Number of retry attempts")
    is_duplicate: bool = Field(False, description="Whether duplicate was detected")
    existing_page_id: Optional[str] = Field(
        None, description="Existing duplicate page ID"
    )


class DLQEntry(BaseModel):
    """Dead letter queue entry for failed Notion writes.

    Attributes:
        email_id: Email identifier for reference
        failed_at: When the write operation failed (UTC)
        retry_count: Number of automatic retries attempted
        error: Error details (type, message, status, response)
        extracted_data: Full extracted entity data
        original_email_content: Optional original email text
        dlq_file_path: Path to DLQ JSON file
    """

    email_id: str = Field(..., description="Email identifier")
    failed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Failure timestamp"
    )
    retry_count: int = Field(0, ge=0, description="Number of retries attempted")
    error: Dict[str, Any] = Field(..., description="Error details")
    extracted_data: "ExtractedEntitiesWithClassification" = Field(
        ..., description="Full extracted data"
    )
    original_email_content: Optional[str] = Field(
        None, description="Original email text"
    )
    dlq_file_path: Optional[str] = Field(None, description="DLQ file path")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
