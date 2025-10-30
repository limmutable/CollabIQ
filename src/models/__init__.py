"""
Data models for CollabIQ email reception.

This package contains Pydantic models for representing raw and cleaned email data.
"""

from .cleaned_email import CleanedEmail, CleaningStatus, RemovedContent
from .raw_email import EmailAttachment, EmailMetadata, RawEmail

__all__ = [
    # Raw email models
    "RawEmail",
    "EmailMetadata",
    "EmailAttachment",
    # Cleaned email models
    "CleanedEmail",
    "CleaningStatus",
    "RemovedContent",
]
