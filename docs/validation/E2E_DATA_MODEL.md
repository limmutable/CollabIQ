# Data Model: MVP End-to-End Testing & Error Resolution

**Feature**: 008-mvp-e2e-test
**Date**: 2025-11-04
**Purpose**: Define entities for tracking test runs, errors, and performance metrics

## Overview

This feature introduces three primary entities for end-to-end testing: **Test Run** (metadata about a test execution), **Error Record** (captured errors with context), and **Performance Metric** (timing and resource data). These entities are persisted as JSON files in `data/e2e_test/`.

---

## Entity: Test Run

**Purpose**: Represents a single execution of the E2E test suite with a set of emails

**Persistence**: `data/e2e_test/runs/{run_id}.json`

### Fields

| Field Name | Type | Required | Description | Validation Rules |
|------------|------|----------|-------------|------------------|
| `run_id` | string | Yes | Unique identifier (ISO 8601 timestamp) | Format: `YYYY-MM-DDTHH:MM:SS` |
| `start_time` | datetime | Yes | When test run started | ISO 8601 format |
| `end_time` | datetime | No | When test run completed (null if still running) | ISO 8601 format, must be after start_time |
| `status` | enum | Yes | Current status of run | One of: "running", "completed", "failed", "interrupted" |
| `email_count` | integer | Yes | Total number of emails to process | Positive integer |
| `emails_processed` | integer | Yes | Number of emails processed so far | 0 to email_count |
| `success_count` | integer | Yes | Number of emails successfully processed | 0 to emails_processed |
| `failure_count` | integer | Yes | Number of emails that failed | 0 to emails_processed |
| `stage_success_rates` | dict | Yes | Success rate by pipeline stage | Keys: "reception", "extraction", "matching", "classification", "write"; Values: 0.0-1.0 |
| `total_duration_seconds` | float | No | Total elapsed time (null if still running) | Positive float |
| `average_time_per_email` | float | No | Average processing time per email (null if incomplete) | Positive float |
| `error_summary` | dict | Yes | Error counts by severity | Keys: "critical", "high", "medium", "low"; Values: non-negative integers |
| `test_email_ids` | list[string] | Yes | List of Gmail message IDs being tested | Non-empty list |
| `config` | dict | Yes | Configuration used for this run | Keys: "test_mode", "database_id", "confidence_threshold", etc. |

### Relationships

- **Has many** Error Records (linked via `run_id`)
- **Has many** Performance Metrics (linked via `run_id`)

### State Transitions

```
[created] → "running" → "completed" (success)
                     → "failed" (unhandled error)
                     → "interrupted" (user cancellation, system crash)
```

### Example

```json
{
  "run_id": "2025-11-04T14:30:00",
  "start_time": "2025-11-04T14:30:00Z",
  "end_time": "2025-11-04T14:45:23Z",
  "status": "completed",
  "email_count": 50,
  "emails_processed": 50,
  "success_count": 48,
  "failure_count": 2,
  "stage_success_rates": {
    "reception": 1.0,
    "extraction": 0.98,
    "matching": 0.96,
    "classification": 0.96,
    "write": 0.96
  },
  "total_duration_seconds": 923.45,
  "average_time_per_email": 18.47,
  "error_summary": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 3
  },
  "test_email_ids": ["msg_001", "msg_002", "..."],
  "config": {
    "test_mode": true,
    "database_id": "abc123-test",
    "confidence_threshold": 0.70
  }
}
```

---

## Entity: Error Record

**Purpose**: Represents a single error or unexpected behavior discovered during testing

**Persistence**: `data/e2e_test/errors/{severity}/{run_id}_{email_id}_{error_index}.json`

### Fields

| Field Name | Type | Required | Description | Validation Rules |
|------------|------|----------|-------------|------------------|
| `error_id` | string | Yes | Unique identifier for this error | Format: `{run_id}_{email_id}_{error_index}` |
| `run_id` | string | Yes | Reference to parent Test Run | Must match existing run_id |
| `email_id` | string | Yes | Gmail message ID where error occurred | Non-empty string |
| `severity` | enum | Yes | Severity level | One of: "critical", "high", "medium", "low" |
| `stage` | enum | Yes | Pipeline stage where error occurred | One of: "reception", "extraction", "matching", "classification", "write", "validation" |
| `error_type` | string | Yes | Type of error | Examples: "APIError", "ValidationError", "EncodingError", "TimeoutError" |
| `error_message` | string | Yes | Human-readable error description | Non-empty string |
| `stack_trace` | string | No | Full stack trace (if available) | Multiline string |
| `input_data_snapshot` | dict | No | Relevant input data that caused error | Sanitized (no sensitive info) |
| `timestamp` | datetime | Yes | When error occurred | ISO 8601 format |
| `resolution_status` | enum | Yes | Current status of error | One of: "open", "fixed", "deferred", "wont_fix" |
| `fix_commit` | string | No | Git commit hash where error was fixed | 40-character SHA-1 hash |
| `notes` | string | No | Additional context or investigation notes | Optional text |

### Severity Definitions

- **Critical**: Blocks pipeline from completing or causes data loss
- **High**: Causes incorrect data in Notion or frequent failures (>10% of emails)
- **Medium**: Causes occasional failures (<10% of emails) or degrades experience
- **Low**: Minor issues that don't affect correctness

### Relationships

- **Belongs to** Test Run (via `run_id`)
- **References** email (via `email_id`)

### Example

```json
{
  "error_id": "2025-11-04T14:30:00_msg_042_001",
  "run_id": "2025-11-04T14:30:00",
  "email_id": "msg_042",
  "severity": "high",
  "stage": "extraction",
  "error_type": "EncodingError",
  "error_message": "Korean text corrupted during JSON serialization: '한글' → 'í•œê¸€'",
  "stack_trace": "Traceback (most recent call last):\n  File \"src/llm_adapters/gemini_adapter.py\", line 123...",
  "input_data_snapshot": {
    "original_text": "담당자: 김철수\n스타트업명: 브레이크앤컴퍼니",
    "corrupted_text": "ë‹´ë‹¹ìž: ê¹€ì²ì\nì íƒì…: ë¸ë ì´ë¬¸ì»´í¼ë‹ˆ"
  },
  "timestamp": "2025-11-04T14:37:45Z",
  "resolution_status": "open",
  "fix_commit": null,
  "notes": "Likely caused by missing encoding='utf-8' in json.dumps(). Need to verify all JSON write operations."
}
```

---

## Entity: Performance Metric

**Purpose**: Represents timing and resource usage data for a pipeline stage

**Persistence**: `data/e2e_test/metrics/{run_id}/{email_id}_{stage}.json`

### Fields

| Field Name | Type | Required | Description | Validation Rules |
|------------|------|----------|-------------|------------------|
| `metric_id` | string | Yes | Unique identifier for this metric | Format: `{run_id}_{email_id}_{stage}` |
| `run_id` | string | Yes | Reference to parent Test Run | Must match existing run_id |
| `email_id` | string | Yes | Gmail message ID being processed | Non-empty string |
| `stage` | enum | Yes | Pipeline stage being measured | One of: "reception", "extraction", "matching", "classification", "write" |
| `start_time` | datetime | Yes | When stage started | ISO 8601 format |
| `end_time` | datetime | Yes | When stage completed | ISO 8601 format, must be after start_time |
| `duration_seconds` | float | Yes | Elapsed time for this stage | Positive float, derived from end_time - start_time |
| `api_calls` | dict | No | Count of API calls by service | Keys: "gemini", "notion", "gmail"; Values: non-negative integers |
| `gemini_tokens` | dict | No | Token usage for Gemini calls (if applicable) | Keys: "input_tokens", "output_tokens"; Values: non-negative integers |
| `memory_mb` | float | No | Peak memory consumption during stage | Positive float (optional, not critical for MVP) |
| `status` | enum | Yes | Whether stage succeeded or failed | One of: "success", "failure" |
| `notes` | string | No | Additional performance observations | Optional text |

### Relationships

- **Belongs to** Test Run (via `run_id`)
- **References** email (via `email_id`)

### Aggregation

Performance metrics are aggregated across all emails in a test run to produce:
- Average/median/p95/p99 duration per stage
- Total API call counts
- Total token usage and estimated cost

### Example

```json
{
  "metric_id": "2025-11-04T14:30:00_msg_010_extraction",
  "run_id": "2025-11-04T14:30:00",
  "email_id": "msg_010",
  "stage": "extraction",
  "start_time": "2025-11-04T14:32:15Z",
  "end_time": "2025-11-04T14:32:18Z",
  "duration_seconds": 3.42,
  "api_calls": {
    "gemini": 1,
    "notion": 0,
    "gmail": 0
  },
  "gemini_tokens": {
    "input_tokens": 1250,
    "output_tokens": 180
  },
  "memory_mb": null,
  "status": "success",
  "notes": "Normal execution, no anomalies"
}
```

---

## Entity: Test Email Metadata

**Purpose**: Metadata about emails selected for testing (to enable stratified sampling validation)

**Persistence**: `data/e2e_test/test_email_ids.json` (single file with array of email metadata)

### Fields

| Field Name | Type | Required | Description | Validation Rules |
|------------|------|----------|-------------|------------------|
| `email_id` | string | Yes | Gmail message ID | Non-empty string |
| `subject` | string | Yes | Email subject line | Non-empty string |
| `received_date` | date | Yes | When email was received | ISO 8601 date |
| `collaboration_type` | string | No | Detected type (if known) | One of: "[A]", "[B]", "[C]", "[D]", or null |
| `has_korean_text` | boolean | Yes | Whether email contains Korean characters | Boolean |
| `selection_reason` | enum | Yes | Why this email was selected | One of: "stratified_sample", "edge_case", "known_failure", "manual" |
| `notes` | string | No | Additional context about this email | Optional text |

### Example

```json
[
  {
    "email_id": "msg_001",
    "subject": "브레이크앤컴퍼니 x 신세계푸드 협력 안내",
    "received_date": "2025-10-28",
    "collaboration_type": "[A]",
    "has_korean_text": true,
    "selection_reason": "stratified_sample",
    "notes": "Typical Portfolio+SSG collaboration"
  },
  {
    "email_id": "msg_042",
    "subject": "Re: 협업 상담 요청",
    "received_date": "2025-09-15",
    "collaboration_type": null,
    "has_korean_text": true,
    "selection_reason": "edge_case",
    "notes": "Email thread with multiple quoted replies, tests content normalizer"
  }
]
```

---

## File Structure

```
data/e2e_test/
├── test_email_ids.json          # Selected emails for testing
├── runs/
│   ├── 2025-11-04T14:30:00.json # Test run metadata
│   └── 2025-11-04T16:45:00.json
├── errors/
│   ├── critical/                # Critical errors (empty directory if none)
│   ├── high/
│   │   ├── 2025-11-04T14:30:00_msg_042_001.json
│   │   └── 2025-11-04T14:30:00_msg_053_001.json
│   ├── medium/
│   │   └── [5 error files]
│   └── low/
│       └── [3 error files]
├── metrics/
│   ├── 2025-11-04T14:30:00/     # Metrics for one test run
│   │   ├── msg_001_reception.json
│   │   ├── msg_001_extraction.json
│   │   ├── msg_001_matching.json
│   │   ├── msg_001_classification.json
│   │   ├── msg_001_write.json
│   │   └── [more emails...]
│   └── 2025-11-04T16:45:00/     # Metrics for another test run
└── reports/
    ├── 2025-11-04T14:30:00_summary.json    # Aggregated test summary
    ├── 2025-11-04T14:30:00_summary.md      # Human-readable report
    └── [more reports...]
```

---

## Validation Rules

### Cross-Entity Consistency

1. **Error Record → Test Run**:
   - `error.run_id` must match an existing `run.run_id`
   - `error.email_id` must be in `run.test_email_ids`

2. **Performance Metric → Test Run**:
   - `metric.run_id` must match an existing `run.run_id`
   - `metric.email_id` must be in `run.test_email_ids`

3. **Test Run Invariants**:
   - `emails_processed = success_count + failure_count`
   - `emails_processed <= email_count`
   - `stage_success_rates[stage]` = (successful emails at stage) / (emails_processed)

4. **Error Summary Accuracy**:
   - Count of errors in `errors/{severity}/` must match `run.error_summary[severity]`

---

## Pydantic Models (Implementation Reference)

These entities will be implemented as Pydantic models in `src/e2e_test/models.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"

class TestRun(BaseModel):
    run_id: str
    start_time: datetime
    end_time: datetime | None = None
    status: RunStatus
    email_count: int = Field(gt=0)
    emails_processed: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    stage_success_rates: dict[str, float]
    total_duration_seconds: float | None = None
    average_time_per_email: float | None = None
    error_summary: dict[str, int]
    test_email_ids: list[str]
    config: dict

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ErrorRecord(BaseModel):
    error_id: str
    run_id: str
    email_id: str
    severity: Severity
    stage: str
    error_type: str
    error_message: str
    stack_trace: str | None = None
    input_data_snapshot: dict | None = None
    timestamp: datetime
    resolution_status: str = "open"
    fix_commit: str | None = None
    notes: str | None = None

class PerformanceMetric(BaseModel):
    metric_id: str
    run_id: str
    email_id: str
    stage: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float = Field(gt=0)
    api_calls: dict[str, int] | None = None
    gemini_tokens: dict[str, int] | None = None
    memory_mb: float | None = None
    status: str
    notes: str | None = None
```

---

## Summary

This data model supports the core requirements of Feature 008:
- **FR-003**: Collect and categorize errors with severity levels → Error Record entity
- **FR-008**: Measure performance metrics per stage → Performance Metric entity
- **FR-012**: Provide test summary report → Test Run entity with aggregation
- **SC-005**: Error logs with full context → Error Record includes stack trace, input snapshot, timestamps
- **SC-010**: Performance baselines per stage → Performance Metric enables per-stage analysis

All entities use JSON for persistence (simple, human-readable, no database required), and Pydantic models ensure type safety and validation.
