"""
Cleaned email data models for email normalization.

This module defines Pydantic models for representing processed emails
with signatures, quoted threads, and disclaimers removed.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CleaningStatus(str, Enum):
    """Cleaning operation outcome."""
    SUCCESS = "success"  # Content remains after cleaning
    EMPTY = "empty"      # No content remains after cleaning (FR-012)
    FAILED = "failed"    # Cleaning process failed
    SKIPPED = "skipped"  # Email was skipped (duplicate, invalid, etc.)


class RemovedContent(BaseModel):
    """
    Summary of content removed during cleaning.

    Attributes:
        signature_removed: Whether signature was detected and removed
        quoted_thread_removed: Whether quoted thread was detected and removed
        disclaimer_removed: Whether disclaimer was detected and removed
        signature_pattern: Pattern name that matched signature (e.g., 'korean_thanks')
        quote_pattern: Pattern name that matched quote (e.g., 'angle_bracket')
        disclaimer_pattern: Pattern name that matched disclaimer (e.g., 'confidentiality')
        original_length: Character count of original body
        cleaned_length: Character count of cleaned body
    """

    signature_removed: bool = Field(default=False, description="Whether signature was detected and removed")
    quoted_thread_removed: bool = Field(default=False, description="Whether quoted thread was detected and removed")
    disclaimer_removed: bool = Field(default=False, description="Whether disclaimer was detected and removed")

    signature_pattern: Optional[str] = Field(None, description="Pattern name that matched signature (e.g., 'korean_thanks')")
    quote_pattern: Optional[str] = Field(None, description="Pattern name that matched quote (e.g., 'angle_bracket')")
    disclaimer_pattern: Optional[str] = Field(None, description="Pattern name that matched disclaimer (e.g., 'confidentiality')")

    original_length: int = Field(..., description="Character count of original body", ge=0)
    cleaned_length: int = Field(..., description="Character count of cleaned body", ge=0)

    @property
    def removal_percentage(self) -> float:
        """Calculate percentage of content removed."""
        if self.original_length == 0:
            return 0.0
        return ((self.original_length - self.cleaned_length) / self.original_length) * 100


class CleanedEmail(BaseModel):
    """
    Processed email with noise removed.

    Validation Rules (from FR-007, FR-012):
    - original_message_id must link back to valid RawEmail
    - cleaned_body can be empty (edge case: entire email was signature/disclaimer)
    - is_empty flag must be True if cleaned_body is empty or whitespace-only

    Attributes:
        original_message_id: Links back to RawEmail.metadata.message_id
        cleaned_body: Email body with signatures, quotes, disclaimers removed
        removed_content: Summary of what was removed
        processed_at: Timestamp when cleaning occurred
        status: Outcome of cleaning operation
        is_empty: True if no content remains after cleaning (FR-012)
    """

    original_message_id: str = Field(..., description="Links back to RawEmail.metadata.message_id")
    cleaned_body: str = Field(..., description="Email body with signatures, quotes, disclaimers removed")
    removed_content: RemovedContent = Field(..., description="Summary of what was removed")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when cleaning occurred")
    status: CleaningStatus = Field(..., description="Outcome of cleaning operation")
    is_empty: bool = Field(..., description="True if no content remains after cleaning (FR-012)")

    @field_validator('is_empty', mode='before')
    @classmethod
    def validate_is_empty(cls, v: bool, info) -> bool:
        """Auto-set is_empty based on cleaned_body content."""
        cleaned_body = info.data.get('cleaned_body', '')
        # Override provided value if cleaned_body is actually empty
        if not cleaned_body or not cleaned_body.strip():
            return True
        return v

    @field_validator('status')
    @classmethod
    def validate_status_consistency(cls, v: CleaningStatus, info) -> CleaningStatus:
        """Ensure status matches is_empty flag."""
        is_empty = info.data.get('is_empty', False)
        if is_empty and v == CleaningStatus.SUCCESS:
            raise ValueError("status cannot be SUCCESS if is_empty is True")
        if not is_empty and v == CleaningStatus.EMPTY:
            raise ValueError("status cannot be EMPTY if is_empty is False")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "original_message_id": "<CABc123@mail.gmail.com>",
                "cleaned_body": "안녕하세요,\n\n지난주 회의에서 논의한 프로젝트 진행 상황을 공유드립니다.",
                "removed_content": {
                    "signature_removed": True,
                    "quoted_thread_removed": False,
                    "disclaimer_removed": False,
                    "signature_pattern": "korean_thanks_name",
                    "quote_pattern": None,
                    "disclaimer_pattern": None,
                    "original_length": 156,
                    "cleaned_length": 98
                },
                "processed_at": "2025-10-30T14:36:05Z",
                "status": "success",
                "is_empty": False
            }
        }
    }
