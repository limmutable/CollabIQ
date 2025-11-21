# Data Model: Production Readiness Fixes

**Phase**: 017-production-readiness-fixes
**Date**: 2025-11-19
**Status**: Phase 1 Design

## Overview

Phase 017 introduces six new entities and enhances existing models to support person matching, token management, daemon operation, and comprehensive testing. All entities follow Pydantic validation patterns established in earlier phases.

---

## Entity Definitions

### 1. Notion Workspace User

**Purpose**: Represents a person in the Notion workspace for 담당자 (person-in-charge) field matching.

**Location**: `src/collabiq/models/notion_user.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotionWorkspaceUser(BaseModel):
    """Notion workspace user for person matching."""

    id: str = Field(
        ...,
        description="Notion user UUID (32-character hexadecimal)",
        regex=r"^[0-9a-f]{32}$"
    )

    name: str = Field(
        ...,
        description="User's display name (Korean or English)",
        min_length=1
    )

    email: Optional[str] = Field(
        None,
        description="User's email address (if available)"
    )

    type: str = Field(
        ...,
        description="User type: 'person' or 'bot'"
    )

    avatar_url: Optional[str] = Field(
        None,
        description="URL to user's avatar image"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "name": "김철수",
                "email": "kim@example.com",
                "type": "person",
                "avatar_url": "https://..."
            }
        }
```

**Relationships**:
- **Many-to-One** with Notion entries via `담당자` field
- Cached in `WorkspaceUserCache` (see Entity 7)

**Validation Rules**:
- `id` must be 32-character hexadecimal UUID (Notion format)
- `name` must not be empty
- `type` must be 'person' (filter out bots)

**State Transitions**: N/A (read-only from Notion API)

---

### 2. Collaboration Summary

**Purpose**: Represents a concise 1-4 line summary of collaboration content stored in the "협업내용" field.

**Location**: `src/collabiq/models/summary.py`

**Schema**:
```python
from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime
from enum import Enum

class OrchestrationStrategy(str, Enum):
    CONSENSUS = "consensus"
    BEST_MATCH = "best_match"
    SINGLE_LLM = "single_llm"

class CollaborationSummary(BaseModel):
    """Multi-LLM generated collaboration summary."""

    summary_text: str = Field(
        ...,
        description="1-4 line summary of collaboration content",
        max_length=400
    )

    strategy: OrchestrationStrategy = Field(
        ...,
        description="Orchestration strategy used to generate summary"
    )

    llm_models: List[str] = Field(
        ...,
        description="List of LLM models that contributed to this summary",
        min_items=1
    )

    quality_score: float = Field(
        ...,
        description="Quality score (0.0-1.0) based on clarity, completeness, conciseness",
        ge=0.0,
        le=1.0
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when summary was generated"
    )

    generation_duration_ms: int = Field(
        ...,
        description="Time taken to generate summary (milliseconds)",
        ge=0
    )

    @validator('summary_text')
    def validate_line_count(cls, v):
        """Ensure summary is 1-4 lines."""
        lines = [line for line in v.split('\n') if line.strip()]
        if not (1 <= len(lines) <= 4):
            raise ValueError(f"Summary must be 1-4 lines, got {len(lines)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "summary_text": "웨이크와 신세계푸드 간 식품 유통 파트너십 논의\nAI 기반 재고 관리 시스템 도입 검토\n3개월 파일럿 프로젝트 제안",
                "strategy": "consensus",
                "llm_models": ["gemini-1.5-pro", "claude-3-sonnet", "gpt-4"],
                "quality_score": 0.92,
                "generated_at": "2025-11-19T10:30:00Z",
                "generation_duration_ms": 7500
            }
        }
```

**Relationships**:
- **One-to-One** with email extraction result
- **Many-to-Many** with LLM providers (via `llm_models` list)

**Validation Rules**:
- `summary_text` must be 1-4 lines (enforced by validator)
- `summary_text` max 400 characters
- `quality_score` must be 0.0-1.0
- `llm_models` must have at least 1 model

**State Transitions**:
```
Draft → Generating → Generated → Validated → Written to Notion
```

---

### 3. Gmail Token Pair

**Purpose**: Represents OAuth2 access token and refresh token for Gmail API access with encryption support.

**Location**: `src/collabiq/models/gmail_token.py`

**Schema**:
```python
from pydantic import BaseModel, Field, SecretStr
from datetime import datetime, timedelta
from typing import Optional

class GmailTokenPair(BaseModel):
    """OAuth2 tokens for Gmail API with encryption metadata."""

    access_token: SecretStr = Field(
        ...,
        description="Gmail API access token (expires in 1 hour)"
    )

    refresh_token: SecretStr = Field(
        ...,
        description="Gmail API refresh token (long-lived)"
    )

    token_type: str = Field(
        default="Bearer",
        description="OAuth2 token type"
    )

    expires_at: datetime = Field(
        ...,
        description="UTC timestamp when access token expires"
    )

    scopes: List[str] = Field(
        ...,
        description="Gmail API scopes granted"
    )

    encrypted: bool = Field(
        default=False,
        description="Whether tokens are encrypted at rest"
    )

    encryption_algorithm: Optional[str] = Field(
        None,
        description="Encryption algorithm used (e.g., 'Fernet-AES128')"
    )

    last_refreshed_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp of last token refresh"
    )

    def is_expired(self) -> bool:
        """Check if access token is expired."""
        return datetime.utcnow() >= self.expires_at

    def expires_soon(self, threshold_minutes: int = 60) -> bool:
        """Check if access token expires within threshold."""
        threshold = datetime.utcnow() + timedelta(minutes=threshold_minutes)
        return self.expires_at <= threshold

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "********",
                "refresh_token": "********",
                "token_type": "Bearer",
                "expires_at": "2025-11-19T11:30:00Z",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
                "encrypted": True,
                "encryption_algorithm": "Fernet-AES128",
                "last_refreshed_at": "2025-11-19T10:30:00Z"
            }
        }
```

**Relationships**:
- **One-to-One** with Gmail client instance
- Persisted in `data/tokens/gmail_tokens.enc`

**Validation Rules**:
- `access_token` and `refresh_token` must not be empty
- `expires_at` must be future timestamp
- If `encrypted=True`, `encryption_algorithm` must be specified

**State Transitions**:
```
Fresh → Active → Expiring Soon → Expired → Refreshing → Fresh
```

---

### 4. UUID Extraction Result

**Purpose**: Represents the outcome of LLM company UUID extraction with validation status.

**Location**: `src/collabiq/models/extraction.py` (enhance existing)

**Schema**:
```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum

class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_LENGTH = "invalid_length"
    NON_HEXADECIMAL = "non_hexadecimal"

class UUIDExtractionResult(BaseModel):
    """LLM-extracted company UUID with validation metadata."""

    extracted_value: str = Field(
        ...,
        description="UUID string extracted by LLM"
    )

    validation_status: ValidationStatus = Field(
        ...,
        description="Result of UUID format validation"
    )

    retry_count: int = Field(
        default=0,
        description="Number of retry attempts (max 2)",
        ge=0,
        le=2
    )

    confidence_score: Optional[float] = Field(
        None,
        description="LLM confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

    error_message: Optional[str] = Field(
        None,
        description="Error message if validation failed"
    )

    @validator('extracted_value')
    def validate_uuid_format(cls, v, values):
        """Validate UUID is 32 hexadecimal characters."""
        if len(v) != 32:
            values['validation_status'] = ValidationStatus.INVALID_LENGTH
            values['error_message'] = f"Expected 32 characters, got {len(v)}"
            return v

        if not all(c in '0123456789abcdef' for c in v.lower()):
            values['validation_status'] = ValidationStatus.NON_HEXADECIMAL
            values['error_message'] = "UUID contains non-hexadecimal characters"
            return v

        values['validation_status'] = ValidationStatus.VALID
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "extracted_value": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "validation_status": "valid",
                "retry_count": 0,
                "confidence_score": 0.95,
                "error_message": None
            }
        }
```

**Relationships**:
- **One-to-One** with company mention in email
- **Many-to-One** with Notion Companies database

**Validation Rules**:
- `extracted_value` must be 32 characters
- `extracted_value` must be hexadecimal
- `retry_count` capped at 2 (FR-023)

**State Transitions**:
```
Extracted → Validating → [Valid|Invalid] → Retrying (if invalid) → Final Result
```

---

### 5. Daemon Process State

**Purpose**: Represents autonomous background operation state with restart resilience.

**Location**: `src/collabiq/models/daemon_state.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class DaemonStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class DaemonProcessState(BaseModel):
    """Persistent state for daemon mode operation."""

    daemon_start_time: datetime = Field(
        ...,
        description="UTC timestamp when daemon started"
    )

    last_check_time: Optional[datetime] = Field(
        None,
        description="UTC timestamp of last email check cycle"
    )

    check_interval_seconds: int = Field(
        ...,
        description="Configured check interval in seconds",
        ge=300  # Minimum 5 minutes
    )

    total_cycles: int = Field(
        default=0,
        description="Total number of processing cycles completed",
        ge=0
    )

    emails_processed: int = Field(
        default=0,
        description="Total emails processed since daemon start",
        ge=0
    )

    error_count: int = Field(
        default=0,
        description="Number of errors encountered",
        ge=0
    )

    current_status: DaemonStatus = Field(
        ...,
        description="Current daemon status"
    )

    last_processed_email_id: Optional[str] = Field(
        None,
        description="Gmail message ID of last successfully processed email"
    )

    pid: Optional[int] = Field(
        None,
        description="Process ID of daemon (for health checks)"
    )

    def mark_cycle_complete(self, emails_count: int, has_error: bool = False):
        """Update state after completing a processing cycle."""
        self.total_cycles += 1
        self.emails_processed += emails_count
        self.last_check_time = datetime.utcnow()
        if has_error:
            self.error_count += 1

    def should_shutdown(self, max_consecutive_errors: int = 5) -> bool:
        """Determine if daemon should shutdown due to errors."""
        return self.error_count >= max_consecutive_errors

    class Config:
        json_schema_extra = {
            "example": {
                "daemon_start_time": "2025-11-19T08:00:00Z",
                "last_check_time": "2025-11-19T10:15:00Z",
                "check_interval_seconds": 900,
                "total_cycles": 9,
                "emails_processed": 47,
                "error_count": 1,
                "current_status": "running",
                "last_processed_email_id": "18c3a2b1d4e5f6g7",
                "pid": 12345
            }
        }
```

**Relationships**:
- **One-to-One** with daemon controller instance
- Persisted in `data/daemon/state.json`

**Validation Rules**:
- `check_interval_seconds` minimum 300 (5 minutes)
- `total_cycles`, `emails_processed`, `error_count` must be non-negative

**State Transitions**:
```
Starting → Running ⇄ Paused
Running → Stopping → Stopped
Running → Error → Stopping → Stopped
```

---

### 6. Test Execution Report

**Purpose**: Represents comprehensive test results with quality metrics comparison.

**Location**: `src/collabiq/models/test_report.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Optional

class TestCategoryResult(BaseModel):
    """Results for a specific test category."""
    category: str  # unit, integration, e2e, contract, performance, fuzz
    total: int = Field(..., ge=0)
    passed: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    skipped: int = Field(..., ge=0)
    duration_seconds: float = Field(..., ge=0.0)

class TestExecutionReport(BaseModel):
    """Comprehensive test execution report for Markdown generation."""

    report_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of report generation"
    )

    branch_name: str = Field(
        ...,
        description="Git branch where tests were executed"
    )

    total_tests: int = Field(
        ...,
        description="Total number of tests executed",
        ge=0
    )

    passed_count: int = Field(
        ...,
        description="Number of tests that passed",
        ge=0
    )

    failed_count: int = Field(
        ...,
        description="Number of tests that failed",
        ge=0
    )

    skipped_count: int = Field(
        ...,
        description="Number of tests that were skipped",
        ge=0
    )

    duration_seconds: float = Field(
        ...,
        description="Total test execution duration",
        ge=0.0
    )

    coverage_percentage: float = Field(
        ...,
        description="Code coverage percentage",
        ge=0.0,
        le=100.0
    )

    category_results: List[TestCategoryResult] = Field(
        ...,
        description="Breakdown by test category"
    )

    failure_logs: List[str] = Field(
        default_factory=list,
        description="Detailed failure messages for failed tests"
    )

    quality_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Phase 017 quality metrics (person assignment, summary quality, UUID errors)"
    )

    baseline_comparison: Optional[Dict[str, str]] = Field(
        None,
        description="Comparison with baseline metrics (before Phase 017)"
    )

    def pass_rate(self) -> float:
        """Calculate overall pass rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_count / self.total_tests) * 100

    def meets_baseline(self, baseline_pass_rate: float = 86.5) -> bool:
        """Check if pass rate meets or exceeds baseline."""
        return self.pass_rate() >= baseline_pass_rate

    class Config:
        json_schema_extra = {
            "example": {
                "report_date": "2025-11-19T14:35:22Z",
                "branch_name": "017-production-readiness-fixes",
                "total_tests": 1015,
                "passed_count": 901,
                "failed_count": 12,
                "skipped_count": 102,
                "duration_seconds": 222.5,
                "coverage_percentage": 84.2,
                "category_results": [...],
                "failure_logs": [...],
                "quality_metrics": {
                    "person_assignment_success_rate": 96.2,
                    "summary_quality_rating": 91.5,
                    "uuid_validation_error_rate": 3.8
                },
                "baseline_comparison": {
                    "pass_rate": "+2.3%",
                    "coverage": "+2.1%"
                }
            }
        }
```

**Relationships**:
- **Many-to-One** with test execution runs
- Persisted in `data/test_reports/*.md` (Markdown format)

**Validation Rules**:
- `coverage_percentage` must be 0-100
- `passed_count + failed_count + skipped_count` should equal `total_tests`
- `pass_rate()` must be ≥86.5% (baseline)

**State Transitions**:
```
Collecting → Analyzing → Generating → Persisted
```

---

### 7. Workspace User Cache (Derived Entity)

**Purpose**: Cached collection of Notion workspace users with TTL management.

**Location**: `src/collabiq/notion_integrator/user_cache.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timedelta

class WorkspaceUserCache(BaseModel):
    """TTL-based cache for Notion workspace users."""

    users: List[NotionWorkspaceUser] = Field(
        ...,
        description="List of cached workspace users"
    )

    cached_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when cache was populated"
    )

    ttl_hours: int = Field(
        default=24,
        description="Cache time-to-live in hours",
        ge=1
    )

    workspace_id: str = Field(
        ...,
        description="Notion workspace ID this cache belongs to"
    )

    def is_expired(self) -> bool:
        """Check if cache has expired."""
        expiry_time = self.cached_at + timedelta(hours=self.ttl_hours)
        return datetime.utcnow() >= expiry_time

    def get_user_by_name(self, name: str) -> Optional[NotionWorkspaceUser]:
        """Find user by exact name match."""
        for user in self.users:
            if user.name == name:
                return user
        return None

    class Config:
        json_schema_extra = {
            "example": {
                "users": [...],
                "cached_at": "2025-11-19T08:00:00Z",
                "ttl_hours": 24,
                "workspace_id": "abc123def456"
            }
        }
```

**Relationships**:
- **One-to-Many** with `NotionWorkspaceUser`
- Persisted in `data/notion_cache/workspace_users.json`

**Validation Rules**:
- `ttl_hours` minimum 1 hour
- `users` list should only contain `type='person'` (filter out bots)

**State Transitions**:
```
Empty → Populating → Fresh → Stale → Expired → Refreshing → Fresh
```

---

## Entity Relationship Diagram

```
┌─────────────────────────┐
│  NotionWorkspaceUser    │
│  (Person in workspace)  │
└────────────┬────────────┘
             │
             │ Many-to-One (담당자 field)
             ▼
┌─────────────────────────┐       ┌──────────────────────┐
│   Email Extraction      │──────▶│ CollaborationSummary │
│   (Existing entity)     │       │ (1-4 line summary)   │
└────────────┬────────────┘       └──────────────────────┘
             │
             │ One-to-One
             ▼
┌─────────────────────────┐
│  UUIDExtractionResult   │
│  (Company UUID)         │
└─────────────────────────┘

┌─────────────────────────┐       ┌──────────────────────┐
│    GmailTokenPair       │──────▶│   Gmail Client       │
│  (OAuth2 tokens)        │       │  (Existing entity)   │
└─────────────────────────┘       └──────────────────────┘

┌─────────────────────────┐       ┌──────────────────────┐
│  DaemonProcessState     │──────▶│  Daemon Controller   │
│  (Autonomous operation) │       │  (New component)     │
└─────────────────────────┘       └──────────────────────┘

┌─────────────────────────┐
│  TestExecutionReport    │
│  (Markdown test report) │
└─────────────────────────┘

┌─────────────────────────┐       ┌──────────────────────┐
│  WorkspaceUserCache     │──────▶│ NotionWorkspaceUser  │
│  (TTL: 24 hours)        │  1:N  │                      │
└─────────────────────────┘       └──────────────────────┘
```

---

## Persistence Strategy

| Entity | Storage | Format | TTL | Encryption |
|--------|---------|--------|-----|------------|
| NotionWorkspaceUser | Cache file | JSON | 24 hours | No |
| CollaborationSummary | Extraction file | JSON | Permanent | No |
| GmailTokenPair | Token file | Encrypted binary | Until refresh | Yes (Fernet) |
| UUIDExtractionResult | Extraction file | JSON | Permanent | No |
| DaemonProcessState | State file | JSON | Until stopped | No |
| TestExecutionReport | Report file | Markdown | Permanent | No |
| WorkspaceUserCache | Cache file | JSON | 24 hours | No |

**File Paths**:
- `data/notion_cache/workspace_users.json` (WorkspaceUserCache)
- `data/extractions/{email_id}.json` (CollaborationSummary, UUIDExtractionResult)
- `data/tokens/gmail_tokens.enc` (GmailTokenPair, encrypted)
- `data/daemon/state.json` (DaemonProcessState)
- `data/test_reports/phase_017_report.md` (TestExecutionReport)

---

## Migration Notes

**No database migrations required.** All entities use file-based storage consistent with existing patterns.

**Breaking Changes**: None. All new entities, existing entities remain unchanged.

**Backward Compatibility**: Existing extraction files will not have `CollaborationSummary` metadata until regenerated. This is acceptable (FR-252: Migration out of scope).

---

## Validation Summary

All entities follow CollabIQ validation patterns:
- ✅ Pydantic models with type hints
- ✅ Field validators for business rules
- ✅ Clear relationships and cardinality
- ✅ State transitions documented
- ✅ JSON serialization support
- ✅ Example data provided
