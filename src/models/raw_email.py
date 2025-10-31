"""
Raw email data models for email reception.

This module defines Pydantic models for representing unprocessed emails
retrieved from the portfolioupdates@signite.co inbox.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailAttachment(BaseModel):
    """
    Email attachment metadata (file content stored separately).

    Attributes:
        filename: Original filename of the attachment
        content_type: MIME type (e.g., 'application/pdf', 'image/png')
        size_bytes: File size in bytes
        storage_path: Optional path to stored attachment file
    """

    filename: str = Field(..., description="Original filename of attachment")
    content_type: str = Field(..., description="MIME type (e.g., 'application/pdf')")
    size_bytes: int = Field(..., description="File size in bytes", ge=0)
    storage_path: Optional[Path] = Field(None, description="Path to stored attachment file")


class EmailMetadata(BaseModel):
    """
    Email metadata fields.

    Attributes:
        message_id: Unique email message ID from email server
        sender: Sender email address
        subject: Email subject line
        received_at: Timestamp when email was received by server
        retrieved_at: Timestamp when email was retrieved by EmailReceiver
        has_attachments: Whether email contains attachments
    """

    message_id: str = Field(..., description="Unique email message ID from email server")
    sender: EmailStr = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject line")
    received_at: datetime = Field(..., description="Timestamp when email was received by server")
    retrieved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when email was retrieved by EmailReceiver"
    )
    has_attachments: bool = Field(default=False, description="Whether email contains attachments")

    @field_validator('message_id')
    @classmethod
    def validate_message_id(cls, v: str) -> str:
        """Ensure message ID is not empty."""
        if not v or not v.strip():
            raise ValueError("message_id cannot be empty")
        return v.strip()


class RawEmail(BaseModel):
    """
    Complete unprocessed email data.

    Validation Rules (from FR-003):
    - message_id must be unique (enforced by duplicate detection)
    - body cannot be empty
    - received_at must be valid datetime

    Attributes:
        metadata: Email metadata (message ID, sender, subject, timestamps)
        body: Full email body including signatures, quotes, disclaimers
        attachments: List of attachment metadata
    """

    metadata: EmailMetadata = Field(..., description="Email metadata")
    body: str = Field(
        ...,
        description="Full email body including signatures, quotes, disclaimers",
        min_length=1
    )
    attachments: List[EmailAttachment] = Field(
        default_factory=list,
        description="List of attachment metadata"
    )

    @field_validator('body')
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Ensure body is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Email body cannot be empty")
        return v

    class Config:
        """Pydantic model configuration with example."""
        json_schema_extra = {
            "example": {
                "metadata": {
                    "message_id": "<CABc123@mail.gmail.com>",
                    "sender": "partner@example.com",
                    "subject": "CollabIQ 협업 업데이트",
                    "received_at": "2025-10-30T14:35:22Z",
                    "retrieved_at": "2025-10-30T14:36:00Z",
                    "has_attachments": False
                },
                "body": "안녕하세요,\n\n지난주 회의에서 논의한 프로젝트 진행 상황을 공유드립니다.\n\n감사합니다.\n김철수 드림",
                "attachments": []
            }
        }
