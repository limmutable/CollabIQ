# Data Model: CollabIQ System

**Status**: ✅ COMPLETE - Foundation data model defined
**Version**: 1.0.0
**Date**: 2025-10-28
**Branch**: 001-feasibility-architecture

---

## Table of Contents

1. [Overview](#overview)
2. [LLMProvider Interface](#llmprovider-interface)
3. [Entity Schemas](#entity-schemas)
4. [Component Contracts](#component-contracts)
5. [Notion Database Schema](#notion-database-schema)

---

## Overview

This document defines the core data structures for the CollabIQ system, focusing on the **LLMProvider abstraction layer** that enables swapping between Gemini, GPT, Claude, or multi-LLM orchestration.

**Key Design Principles**:
- **Type Safety**: All entities use Pydantic models for validation
- **Abstraction**: LLMProvider interface hides implementation details
- **Extensibility**: Easy to add new LLM adapters without changing contracts
- **Confidence Tracking**: All extractions include per-field confidence scores

---

## LLMProvider Interface

### Abstract Base Class

**File**: `src/llm_provider/base.py`

```python
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ExtractedEntities(BaseModel):
    """Entities extracted from collaboration email"""

    person_in_charge: Optional[str] = Field(
        None,
        description="담당자 - Person who sent/received the collaboration update"
    )
    startup_name: Optional[str] = Field(
        None,
        description="스타트업명 - Name of the startup company involved"
    )
    partner_org: Optional[str] = Field(
        None,
        description="협업기관 - Partner organization (SSG affiliate or other company)"
    )
    details: str = Field(
        ...,
        description="협업내용 - Full collaboration details from email"
    )
    date: Optional[datetime] = Field(
        None,
        description="날짜 - Date of the collaboration activity"
    )
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Per-field confidence scores (0.0-1.0)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "person_in_charge": "김철수",
                "startup_name": "본봄",
                "partner_org": "신세계인터내셔널",
                "details": "11월 1주 PoC 시작 예정, 신세계인터와 본봄 파일럿 킥오프",
                "date": "2025-10-27T00:00:00",
                "confidence": {
                    "person": 0.95,
                    "startup": 0.92,
                    "partner": 0.88,
                    "date": 0.85
                }
            }
        }


class MatchedCompany(BaseModel):
    """Company matched to existing Notion database entry"""

    original_name: str = Field(
        ...,
        description="Original company name extracted from email"
    )
    matched_name: Optional[str] = Field(
        None,
        description="Matched company name from Notion database"
    )
    notion_page_id: Optional[str] = Field(
        None,
        description="Notion page ID for the matched company"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Matching confidence score (0.0-1.0)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_name": "신세계인터",
                "matched_name": "신세계인터내셔널",
                "notion_page_id": "abc123def456",
                "confidence": 0.87
            }
        }


class Classification(BaseModel):
    """Collaboration type and intensity classification"""

    collab_type: str = Field(
        ...,
        description="협업형태 - Collaboration type: [A], [B], [C], or [D]",
        pattern="^\\[(A|B|C|D)\\]$"
    )
    intensity: str = Field(
        ...,
        description="협업강도 - Collaboration intensity: 이해, 협력, 투자, or 인수"
    )
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Per-classification confidence scores"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "collab_type": "[A]",
                "intensity": "협력",
                "confidence": {
                    "type": 0.91,
                    "intensity": 0.89
                }
            }
        }


class ClassificationContext(BaseModel):
    """Context needed for collaboration classification"""

    portfolio_companies: list[str] = Field(
        default_factory=list,
        description="List of portfolio company names from 스타트업 database"
    )
    ssg_affiliates: list[str] = Field(
        default_factory=list,
        description="List of SSG affiliate names from 계열사 database"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_companies": ["본봄", "테이블매니저", "어라운드"],
                "ssg_affiliates": ["신세계인터내셔널", "신세계푸드", "이마트"]
            }
        }


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Enables swapping between Gemini, GPT, Claude, or multi-LLM orchestration
    without rewriting the entire system.
    """

    @abstractmethod
    def extract_entities(
        self,
        email_text: str,
        company_context: Optional[ClassificationContext] = None
    ) -> tuple[ExtractedEntities, list[MatchedCompany]]:
        """
        Extract key entities from email text and match to existing companies.

        Args:
            email_text: Normalized email body (Korean/English)
            company_context: Optional context with portfolio companies and SSG affiliates
                           for fuzzy matching

        Returns:
            Tuple of (ExtractedEntities, list of MatchedCompany objects)

        Raises:
            LLMAPIError: If LLM API call fails after retries
        """
        pass

    @abstractmethod
    def classify(
        self,
        entities: ExtractedEntities,
        context: ClassificationContext
    ) -> Classification:
        """
        Classify collaboration type and intensity.

        Classification Rules:
        - [A] PortCo × SSG: startup_name in portfolio_companies AND
                           partner_org in ssg_affiliates
        - [B] Non-PortCo × SSG: startup_name NOT in portfolio_companies AND
                                partner_org in ssg_affiliates
        - [C] PortCo × PortCo: startup_name in portfolio_companies AND
                              partner_org in portfolio_companies
        - [D] Other: All other combinations

        Intensity Mapping (based on keywords in details):
        - 이해 (Understand): mentions of meeting, discussion, introduction
        - 협력 (Cooperate): mentions of pilot, PoC, partnership, collaboration
        - 투자 (Invest): mentions of investment, funding, financing
        - 인수 (Acquire): mentions of acquisition, M&A, takeover

        Args:
            entities: Extracted entities from extract_entities()
            context: Portfolio status, SSG affiliation lookup results

        Returns:
            Classification with type, intensity, and confidence scores

        Raises:
            LLMAPIError: If LLM API call fails after retries
        """
        pass

    @abstractmethod
    def summarize(
        self,
        text: str,
        max_sentences: int = 5
    ) -> str:
        """
        Generate 3-5 sentence summary preserving key details.

        Args:
            text: Full collaboration details text
            max_sentences: Maximum sentences in summary (3-5)

        Returns:
            Summary string (Korean or English matching input)

        Raises:
            LLMAPIError: If LLM API call fails after retries
        """
        pass
```

### Type Definitions

**File**: `src/llm_provider/types.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Re-export all types for convenience
from .base import (
    ExtractedEntities,
    MatchedCompany,
    Classification,
    ClassificationContext,
    LLMProvider
)

__all__ = [
    "ExtractedEntities",
    "MatchedCompany",
    "Classification",
    "ClassificationContext",
    "LLMProvider"
]
```

---

## Entity Schemas

### RawEmail

**File**: `src/email_receiver/types.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RawEmail(BaseModel):
    """Raw email received from email infrastructure"""

    message_id: str = Field(..., description="Unique email message ID")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body (plain text)")
    sender: str = Field(..., description="Sender email address")
    recipient: str = Field(..., description="Recipient email address (radar@signite.co)")
    received_at: datetime = Field(..., description="Timestamp when email was received")
    attachments: list[str] = Field(
        default_factory=list,
        description="List of attachment filenames (if any)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "CABc123xyz789",
                "subject": "본봄 파일럿 킥오프",
                "body": "어제 신세계인터와 본봄 파일럿 킥오프...",
                "sender": "kim@signite.co",
                "recipient": "radar@signite.co",
                "received_at": "2025-10-27T14:30:00",
                "attachments": []
            }
        }
```

### CleanedEmail

**File**: `src/email_receiver/types.py`

```python
class CleanedEmail(BaseModel):
    """Email after content normalization"""

    message_id: str = Field(..., description="Original message ID")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Cleaned email body (signatures removed)")
    metadata: dict = Field(
        default_factory=dict,
        description="Original metadata (sender, recipient, timestamp)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "CABc123xyz789",
                "subject": "본봄 파일럿 킥오프",
                "body": "어제 신세계인터와 본봄 파일럿 킥오프, 11월 1주 PoC 시작 예정",
                "metadata": {
                    "sender": "kim@signite.co",
                    "received_at": "2025-10-27T14:30:00"
                }
            }
        }
```

### NotionEntry

**File**: `src/notion_integrator/types.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotionEntry(BaseModel):
    """Entry to be created in Notion CollabIQ database"""

    person_in_charge: str = Field(..., description="담당자 - Person field")
    startup_name: str = Field(..., description="스타트업명 - Relation to Company DB (CORP)")
    startup_page_id: Optional[str] = Field(None, description="Notion page ID for startup")
    partner_org: str = Field(..., description="협업기관 - Relation to Company DB (CORP)")
    partner_page_id: Optional[str] = Field(None, description="Notion page ID for partner")
    collab_subject: str = Field(..., description="협력주체 - Title (auto-generated)")
    details: str = Field(..., description="협업내용 - Text field")
    collab_type: str = Field(..., description="협업형태 - Select ([A], [B], [C], [D])")
    intensity: str = Field(..., description="협업강도 - Select (이해, 협력, 투자, 인수)")
    date: datetime = Field(..., description="날짜 - Date field")
    summary: Optional[str] = Field(None, description="3-5 sentence summary")
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores for each field"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "person_in_charge": "김철수",
                "startup_name": "본봄",
                "startup_page_id": "abc123",
                "partner_org": "신세계인터내셔널",
                "partner_page_id": "def456",
                "collab_subject": "본봄-신세계인터내셔널",
                "details": "11월 1주 PoC 시작 예정, 신세계인터와 본봄 파일럿 킥오프",
                "collab_type": "[A]",
                "intensity": "협력",
                "date": "2025-10-27T00:00:00",
                "summary": "본봄과 신세계인터내셔널이 파일럿 킥오프를 진행하고 11월 1주에 PoC를 시작할 예정입니다.",
                "confidence": {
                    "person": 0.95,
                    "startup": 0.92,
                    "partner": 0.88,
                    "date": 0.85,
                    "type": 0.91,
                    "intensity": 0.89
                }
            }
        }
```

### VerificationQueueItem

**File**: `src/verification_queue/types.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class VerificationQueueItem(BaseModel):
    """Item stored in verification queue for manual review"""

    queue_id: str = Field(..., description="Unique queue item ID")
    email_message_id: str = Field(..., description="Original email message ID")
    extracted_entities: dict = Field(..., description="Extracted entities (JSON)")
    matched_companies: list[dict] = Field(..., description="Matched companies (JSON)")
    classification: dict = Field(..., description="Classification (JSON)")
    low_confidence_fields: list[str] = Field(
        ...,
        description="Fields with confidence < 0.85 threshold"
    )
    flagged_reason: str = Field(..., description="Why this item was flagged")
    created_at: datetime = Field(..., description="When item was added to queue")
    reviewed_at: Optional[datetime] = Field(None, description="When item was reviewed")
    reviewer: Optional[str] = Field(None, description="Who reviewed this item")
    resolution: Optional[str] = Field(
        None,
        description="Resolution: approved, corrected, rejected"
    )
    corrected_data: Optional[dict] = Field(
        None,
        description="Manually corrected data (if resolution = corrected)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "queue_id": "q_2025_10_27_001",
                "email_message_id": "CABc123xyz789",
                "extracted_entities": {
                    "startup_name": "본봄",
                    "partner_org": "신세계인터"
                },
                "matched_companies": [
                    {
                        "original_name": "신세계인터",
                        "matched_name": "신세계인터내셔널",
                        "confidence": 0.82
                    }
                ],
                "classification": {"collab_type": "[A]", "intensity": "협력"},
                "low_confidence_fields": ["partner"],
                "flagged_reason": "Partner organization match confidence (0.82) below 0.85 threshold",
                "created_at": "2025-10-27T14:35:00",
                "reviewed_at": None,
                "reviewer": None,
                "resolution": None,
                "corrected_data": None
            }
        }
```

---

## Component Contracts

See `contracts/` directory for detailed YAML specifications:

- `contracts/llm_provider.yaml` - LLMProvider interface contract
- `contracts/email_receiver.yaml` - EmailReceiver component contract
- `contracts/notion_integrator.yaml` - NotionIntegrator component contract

---

## Notion Database Schema

### CollabIQ Database (formerly 레이더 활동)

**Purpose**: Main database storing all collaboration records

| Field Name (Korean) | Field Name (English) | Type | Description | Example |
|---------------------|----------------------|------|-------------|---------|
| 담당자 | Person in Charge | Person | Team member who reported | 김철수 |
| 스타트업명 | Startup Name | Relation (→Company DB) | Startup company involved | 본봄 |
| 협업기관 | Partner Organization | Relation (→Company DB) | Partner org (SSG or other) | 신세계인터내셔널 |
| 협력주체 | Collaboration Subject | Title | Auto-generated: {startup}-{partner} | 본봄-신세계인터내셔널 |
| 협업내용 | Collaboration Details | Text | Full details from email | 11월 1주 PoC 시작... |
| 협업형태 | Collaboration Type | Select | [A], [B], [C], [D] | [A] |
| 협업강도 | Collaboration Intensity | Select | 이해, 협력, 투자, 인수 | 협력 |
| 날짜 | Date | Date | Date of activity | 2025-10-27 |

### Company Database (NOTION_DATABASE_ID_CORP)

**Purpose**: Unified database containing ALL companies (startups, portfolio companies, and Shinsegate affiliates)

**Note**: This is a single database that consolidates what were previously separate databases. Company types are distinguished by fields within this database.

| Field | Type | Description |
|-------|------|-------------|
| 회사명 | Title | Company name |
| Company Type | Select/Multi-select | Distinguishes between: Startup, Portfolio Company, Shinsegate Affiliate |
| 포트폴리오 여부 | Checkbox | Is this a portfolio company? (if applicable) |
| SSG 계열사 여부 | Checkbox | Is this an SSG affiliate? (if applicable) |
| 투자 날짜 | Date | Investment date (for portfolio companies) |
| 비고 | Text | Notes |

**Important**: The actual field names and structure should be verified through database structure analysis (see Section 2.2 of research-template.md). This table shows the expected schema.

---

## Error Types

**File**: `src/llm_provider/exceptions.py`

```python
class LLMAPIError(Exception):
    """Base exception for LLM API errors"""
    pass

class LLMRateLimitError(LLMAPIError):
    """LLM API rate limit exceeded"""
    pass

class LLMTimeoutError(LLMAPIError):
    """LLM API request timed out"""
    pass

class LLMParsingError(LLMAPIError):
    """Failed to parse LLM response as expected format"""
    pass
```

---

## Configuration Schema

**File**: `config/settings.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    # Notion API
    notion_api_key: str
    notion_database_id_collabiq: str
    notion_database_id_corp: str

    # Email (optional - depends on selected infrastructure)
    gmail_credentials_path: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    webhook_secret: Optional[str] = None

    # Processing
    fuzzy_match_threshold: float = 0.85
    confidence_threshold: float = 0.85
    max_retries: int = 3
    retry_delay_seconds: int = 5

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## Next Steps

**After Data Model Complete**:
1. ✅ **Data model documented** (this file)
2. → **API contracts** (contracts/*.yaml - next task)
3. → **Implementation roadmap** (implementation-roadmap.md)
4. → **Project scaffold** (src/ structure with placeholder files)
5. → **Feature implementation** (branches 002-012)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-28
**Next Review**: After feasibility study completion (Phase 0)
