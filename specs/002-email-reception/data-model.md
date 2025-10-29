# Data Model: Email Reception and Normalization

**Feature**: `002-email-reception`
**Created**: 2025-10-30
**Status**: Design Phase

---

## Overview

This document defines the data structures for email reception and normalization. All models use Pydantic for type-safe validation and serialization.

---

## Core Entities

### 1. RawEmail

Represents an unprocessed email retrieved from the portfolioupdates@signite.co inbox.

**Purpose**: Store complete original email data before any processing or cleaning.

**Storage**: Saved to `data/raw/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json`

**Lifecycle**: Created by EmailReceiver when email is fetched from inbox, consumed by ContentNormalizer for cleaning.

```python
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List
from pathlib import Path

class EmailAttachment(BaseModel):
    """Email attachment metadata (file content stored separately)."""
    filename: str = Field(..., description="Original filename of attachment")
    content_type: str = Field(..., description="MIME type (e.g., 'application/pdf')")
    size_bytes: int = Field(..., description="File size in bytes", ge=0)
    storage_path: Optional[Path] = Field(None, description="Path to stored attachment file")

class EmailMetadata(BaseModel):
    """Email metadata fields."""
    message_id: str = Field(..., description="Unique email message ID from email server")
    sender: EmailStr = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject line")
    received_at: datetime = Field(..., description="Timestamp when email was received by server")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when email was retrieved by EmailReceiver")
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
    """
    metadata: EmailMetadata = Field(..., description="Email metadata")
    body: str = Field(..., description="Full email body including signatures, quotes, disclaimers", min_length=1)
    attachments: List[EmailAttachment] = Field(default_factory=list, description="List of attachment metadata")

    @field_validator('body')
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Ensure body is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Email body cannot be empty")
        return v

    class Config:
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
```

**Field Mappings to Requirements**:
- `metadata.message_id` → FR-003, FR-011 (unique identifier, duplicate detection)
- `metadata.sender` → FR-002, FR-003 (email tracking)
- `metadata.subject` → FR-003 (context for LLM)
- `body` → FR-003 (raw content for cleaning)
- `metadata.received_at` → FR-002 (chronological ordering)
- `attachments` → Edge case handling (Phase 1a logs but does not process)

---

### 2. CleanedEmail

Represents a processed email with signatures, quoted threads, and disclaimers removed.

**Purpose**: Provide clean collaboration content ready for LLM entity extraction in Phase 1b.

**Storage**: Saved to `data/cleaned/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json`

**Lifecycle**: Created by ContentNormalizer after processing RawEmail, consumed by LLMProvider in Phase 1b.

```python
from enum import Enum

class CleaningStatus(str, Enum):
    """Cleaning operation outcome."""
    SUCCESS = "success"  # Content remains after cleaning
    EMPTY = "empty"      # No content remains after cleaning (FR-012)
    FAILED = "failed"    # Cleaning process failed
    SKIPPED = "skipped"  # Email was skipped (duplicate, invalid, etc.)

class RemovedContent(BaseModel):
    """Summary of content removed during cleaning."""
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

    class Config:
        json_schema_extra = {
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
```

**Field Mappings to Requirements**:
- `cleaned_body` → FR-007, FR-008 (cleaned content output)
- `removed_content.signature_removed` → FR-004 (signature removal tracking)
- `removed_content.quoted_thread_removed` → FR-005 (quote removal tracking)
- `removed_content.disclaimer_removed` → FR-006 (disclaimer removal tracking)
- `is_empty` → FR-012 (empty email edge case)
- `status` → FR-009 (logging and monitoring)
- `processed_at` → FR-009 (activity logging)

---

## Supporting Types

### 3. ProcessingLog

Tracks all email processing activities for observability and debugging.

**Purpose**: Provide audit trail for email ingestion and cleaning pipeline (FR-009).

**Storage**: Saved to `data/logs/processing_log_YYYYMMDD.json` (daily log file)

```python
class ProcessingEvent(str, Enum):
    """Types of processing events."""
    EMAIL_RETRIEVED = "email_retrieved"
    EMAIL_CLEANED = "email_cleaned"
    EMAIL_SKIPPED = "email_skipped"
    EMAIL_FAILED = "email_failed"
    DUPLICATE_DETECTED = "duplicate_detected"
    CONNECTION_FAILED = "connection_failed"
    CONNECTION_RETRY = "connection_retry"

class ProcessingLogEntry(BaseModel):
    """Single processing log entry."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When event occurred")
    event: ProcessingEvent = Field(..., description="Type of processing event")
    message_id: Optional[str] = Field(None, description="Email message ID if applicable")
    details: str = Field(..., description="Human-readable event description")
    error_message: Optional[str] = Field(None, description="Error message if event is failure")
    retry_count: Optional[int] = Field(None, description="Retry attempt number if applicable", ge=0, le=3)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-30T14:36:00Z",
                "event": "email_retrieved",
                "message_id": "<CABc123@mail.gmail.com>",
                "details": "Successfully retrieved email from portfolioupdates@signite.co",
                "error_message": None,
                "retry_count": None
            }
        }
```

**Field Mappings to Requirements**:
- `event` → FR-009 (log processing activities)
- `timestamp` → FR-009 (activity timestamps)
- `retry_count` → FR-010 (exponential backoff tracking)
- `error_message` → FR-010 (failure logging)

---

### 4. DuplicateTracker

Tracks processed message IDs to prevent reprocessing.

**Purpose**: Implement duplicate detection (FR-011).

**Storage**: Single file `data/metadata/processed_ids.json`

```python
class DuplicateTracker(BaseModel):
    """Tracks processed email message IDs."""
    processed_message_ids: set[str] = Field(default_factory=set, description="Set of processed message IDs")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last time tracker was updated")

    def is_duplicate(self, message_id: str) -> bool:
        """Check if message ID has been processed."""
        return message_id in self.processed_message_ids

    def mark_processed(self, message_id: str) -> None:
        """Mark message ID as processed."""
        self.processed_message_ids.add(message_id)
        self.last_updated = datetime.utcnow()

    class Config:
        # Custom JSON encoder for set type
        json_encoders = {
            set: list
        }
```

**Field Mappings to Requirements**:
- `processed_message_ids` → FR-011 (duplicate detection)
- `is_duplicate()` → FR-011 (skip reprocessing)

---

## State Transitions

### Email Processing State Machine

```
[Email in Inbox]
       ↓
   Retrieved → [RawEmail created]
       ↓
   Cleaning → [ContentNormalizer processing]
       ↓
    ├─→ Success → [CleanedEmail with status=SUCCESS]
    ├─→ Empty → [CleanedEmail with status=EMPTY, is_empty=True]
    ├─→ Failed → [CleanedEmail with status=FAILED]
    └─→ Skipped → [ProcessingLog entry only, no CleanedEmail]
```

**Valid Transitions**:
1. `Retrieved` → `Cleaning`: Always when RawEmail is created
2. `Cleaning` → `Success`: When cleaned_body has content after removal
3. `Cleaning` → `Empty`: When entire email was signature/disclaimer/quote (FR-012)
4. `Cleaning` → `Failed`: When cleaning process raises exception
5. `Cleaning` → `Skipped`: When duplicate detected (FR-011)

**Invalid Transitions**:
- Cannot skip `Retrieved` state (must always create RawEmail first)
- Cannot retry `Cleaning` after `Success` (cleaning is idempotent but not retried)
- Cannot transition from `Empty` to `Success` (immutable once processed)

---

## Relationships

```
RawEmail (1) ←→ (1) CleanedEmail
   ↓
   message_id links via original_message_id

RawEmail (1) ←→ (0..*) EmailAttachment
   ↓
   attachments list (Phase 1a logs but does not process)

RawEmail (1) ←→ (1..*) ProcessingLogEntry
   ↓
   message_id field links to log entries

DuplicateTracker (1) ←→ (0..*) RawEmail
   ↓
   processed_message_ids set contains message_id values
```

---

## Validation Rules Summary

### RawEmail Validation
- ✅ `message_id` must be non-empty string
- ✅ `sender` must be valid email address (Pydantic EmailStr)
- ✅ `body` must have at least 1 character
- ✅ `received_at` must be valid ISO 8601 datetime
- ⚠️ Duplicate `message_id` detected by DuplicateTracker (not Pydantic)

### CleanedEmail Validation
- ✅ `original_message_id` must be non-empty string
- ✅ `cleaned_body` can be empty (edge case)
- ✅ `is_empty` auto-computed from `cleaned_body` content
- ✅ `status` must match `is_empty` flag (SUCCESS ↔ False, EMPTY ↔ True)
- ✅ `removed_content.original_length` >= `removed_content.cleaned_length`

### ProcessingLogEntry Validation
- ✅ `retry_count` must be 0-3 (FR-010: max 3 retries)
- ✅ `event` must be valid ProcessingEvent enum value

---

## Example Usage

### Creating RawEmail from Gmail API Response

```python
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.utils import parsedate_to_datetime

# Gmail API response
message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

# Extract metadata
headers = {h['name']: h['value'] for h in message['payload']['headers']}
body = message['snippet']  # Or extract from payload parts

# Create RawEmail
raw_email = RawEmail(
    metadata=EmailMetadata(
        message_id=headers.get('Message-ID', ''),
        sender=headers.get('From', ''),
        subject=headers.get('Subject', ''),
        received_at=parsedate_to_datetime(headers.get('Date', '')),
        has_attachments=len(message['payload'].get('parts', [])) > 1
    ),
    body=body,
    attachments=[]  # Phase 1a logs but does not process
)

# Validate and save
raw_email.model_validate(raw_email.model_dump())
```

### Creating CleanedEmail from ContentNormalizer

```python
from content_normalizer import ContentNormalizer

normalizer = ContentNormalizer()
raw_email = RawEmail.model_validate_json(raw_json)

# Clean email
cleaned_body, removed = normalizer.clean(raw_email.body)

# Create CleanedEmail
cleaned_email = CleanedEmail(
    original_message_id=raw_email.metadata.message_id,
    cleaned_body=cleaned_body,
    removed_content=RemovedContent(
        signature_removed=removed['signature_removed'],
        quoted_thread_removed=removed['quoted_thread_removed'],
        disclaimer_removed=removed['disclaimer_removed'],
        signature_pattern=removed.get('signature_pattern'),
        quote_pattern=removed.get('quote_pattern'),
        disclaimer_pattern=removed.get('disclaimer_pattern'),
        original_length=len(raw_email.body),
        cleaned_length=len(cleaned_body)
    ),
    status=CleaningStatus.SUCCESS if cleaned_body.strip() else CleaningStatus.EMPTY,
    is_empty=not bool(cleaned_body.strip())
)

# Validate and save
cleaned_email.model_validate(cleaned_email.model_dump())
```

### Duplicate Detection

```python
tracker = DuplicateTracker.model_validate_json(tracker_json)

if tracker.is_duplicate(raw_email.metadata.message_id):
    # Log and skip
    log_entry = ProcessingLogEntry(
        event=ProcessingEvent.DUPLICATE_DETECTED,
        message_id=raw_email.metadata.message_id,
        details=f"Email {raw_email.metadata.message_id} already processed"
    )
else:
    # Process and mark
    # ... process email ...
    tracker.mark_processed(raw_email.metadata.message_id)
    # Save tracker
```

---

## File Storage Schema

### Directory Structure

```
data/
├── raw/
│   ├── 2025/
│   │   └── 10/
│   │       └── 20251030_143622_CABc123.json  # RawEmail
├── cleaned/
│   ├── 2025/
│   │   └── 10/
│   │       └── 20251030_143625_CABc123.json  # CleanedEmail
├── logs/
│   └── processing_log_20251030.json  # ProcessingLogEntry list
└── metadata/
    └── processed_ids.json  # DuplicateTracker
```

### File Naming Convention

- **Raw emails**: `YYYYMMDD_HHMMSS_{sanitized_message_id}.json`
  - Example: `20251030_143622_CABc123.json`
- **Cleaned emails**: Same as raw email (matching message ID)
- **Processing logs**: `processing_log_YYYYMMDD.json` (daily file)
- **Duplicate tracker**: `processed_ids.json` (single file)

---

## Pydantic Configuration

All models use these common Pydantic settings:

```python
class Config:
    # Strict type validation
    validate_assignment = True

    # Allow extra fields for future extensibility
    extra = 'forbid'

    # Use enum values in JSON
    use_enum_values = False

    # Serialize datetime as ISO 8601
    json_encoders = {
        datetime: lambda v: v.isoformat()
    }
```

---

**Document Status**: Complete - Ready for contract generation
