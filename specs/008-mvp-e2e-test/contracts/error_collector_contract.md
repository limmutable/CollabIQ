# Contract: ErrorCollector

**Module**: `src/e2e_test/error_collector.py`
**Purpose**: Capture, categorize, and persist errors discovered during E2E testing

## Interface

### Method: `collect_error`

**Description**: Capture an error with full context and categorize by severity

**Signature**:
```python
def collect_error(
    run_id: str,
    email_id: str,
    stage: str,
    exception: Exception | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    input_data: dict | None = None,
    severity: Severity | None = None
) -> ErrorRecord
```

**Parameters**:
- `run_id` (str): Test run ID where error occurred
- `email_id` (str): Email being processed when error occurred
- `stage` (str): Pipeline stage where error occurred ("reception", "extraction", etc.)
- `exception` (Exception | None): Python exception object (if available)
- `error_type` (str | None): Type of error (e.g., "APIError", "ValidationError"). If None, inferred from exception.
- `error_message` (str | None): Human-readable error description. If None, inferred from exception.
- `input_data` (dict | None): Relevant input data that caused error (sanitized, no sensitive info)
- `severity` (Severity | None): Severity level. If None, auto-categorized based on error type and stage.

**Returns**:
- `ErrorRecord`: Created error record with unique `error_id`

**Raises**:
- `ValueError`: If both `exception` and `error_message` are None

**Behavior**:
1. Generate unique `error_id` (format: `{run_id}_{email_id}_{error_index}`)
2. Extract error details from exception (if provided)
3. Auto-categorize severity if not provided:
   - API authentication failures → "critical"
   - Unhandled exceptions → "critical"
   - Data corruption (Korean text encoding) → "high"
   - Date parsing failures → "high"
   - Missing optional fields → "medium"
   - Verbose logging issues → "low"
4. Sanitize `input_data` to remove sensitive information (API keys, tokens)
5. Capture stack trace from exception
6. Set `resolution_status = "open"` and `timestamp = now()`
7. Return Error Record object

**Success Criteria**:
- Error record includes full context for reproduction
- Severity auto-categorization matches research definitions
- Sensitive data removed from input_data snapshot
- Stack trace captured if exception provided

**Example Usage**:
```python
collector = ErrorCollector(output_dir="data/e2e_test")

try:
    result = gemini_adapter.extract(email_body)
except EncodingError as e:
    error = collector.collect_error(
        run_id="2025-11-04T14:30:00",
        email_id="msg_042",
        stage="extraction",
        exception=e,
        input_data={"email_body": email_body[:500]}  # First 500 chars
    )
    # Error auto-categorized as "high" severity
```

---

### Method: `persist_error`

**Description**: Write error record to disk in appropriate severity directory

**Signature**:
```python
def persist_error(error: ErrorRecord) -> str
```

**Parameters**:
- `error` (ErrorRecord): Error record to persist

**Returns**:
- `str`: File path where error was written

**Raises**:
- `IOError`: If file write fails

**Behavior**:
1. Determine output path: `{output_dir}/errors/{severity}/{error_id}.json`
2. Create severity subdirectory if not exists
3. Serialize Error Record to JSON
4. Write to file with UTF-8 encoding
5. Return file path

**Success Criteria**:
- Error written to correct severity subdirectory
- JSON file is valid and can be loaded back
- Korean text in error preserved without corruption

---

### Method: `get_error_summary`

**Description**: Get error count breakdown by severity for a test run

**Signature**:
```python
def get_error_summary(run_id: str) -> dict[str, int]
```

**Parameters**:
- `run_id` (str): Test run ID to summarize

**Returns**:
- `dict[str, int]`: Error counts by severity
  - Keys: "critical", "high", "medium", "low"
  - Values: non-negative integers

**Raises**: None

**Behavior**:
1. Scan `{output_dir}/errors/` subdirectories
2. Count error files matching `{run_id}_*` in each severity directory
3. Return dictionary with counts

**Success Criteria**:
- Counts match actual number of error files
- Returns zero for severities with no errors

**Example**:
```python
summary = collector.get_error_summary("2025-11-04T14:30:00")
# Returns: {"critical": 0, "high": 2, "medium": 5, "low": 3}
```

---

### Method: `update_error_status`

**Description**: Update resolution status of an error after fix is applied

**Signature**:
```python
def update_error_status(
    error_id: str,
    resolution_status: str,
    fix_commit: str | None = None,
    notes: str | None = None
) -> ErrorRecord
```

**Parameters**:
- `error_id` (str): Error to update
- `resolution_status` (str): New status ("open", "fixed", "deferred", "wont_fix")
- `fix_commit` (str | None): Git commit hash where fix was applied
- `notes` (str | None): Additional context about resolution

**Returns**:
- `ErrorRecord`: Updated error record

**Raises**:
- `FileNotFoundError`: If error with `error_id` not found

**Behavior**:
1. Load existing Error Record from disk
2. Update `resolution_status`, `fix_commit`, and `notes` fields
3. Write updated Error Record back to disk
4. Return updated Error Record

**Success Criteria**:
- Error status updated correctly
- Original error data preserved (only status/fix_commit/notes changed)

---

## Auto-Categorization Rules (Severity)

### Critical
- API authentication failures (Gmail, Gemini, Notion)
- Unhandled exceptions that crash the pipeline
- Data loss or corruption that persists to Notion
- Notion API schema mismatches

### High
- Korean text encoding errors (mojibake)
- Date parsing failures for required fields
- Company matching returning wrong company IDs
- Frequent failures (>10% of emails)

### Medium
- Edge case date formats not handled
- Ambiguous company names not resolved (fallback to text)
- Classification confidence below threshold (routes to manual review correctly)
- Occasional failures (<10% of emails)

### Low
- Verbose logging creating noise
- Suboptimal error messages (not actionable)
- Missing progress indicators
- Minor performance issues (<10s vs <5s)

---

## Dependencies

- `data_model.ErrorRecord`: Pydantic model for error data
- `data_model.Severity`: Enum for severity levels
- Python `traceback` module: Extract stack traces
- Python `json` module: Serialize/deserialize errors

---

## Contract Tests

**Test 1: collect_error with exception**
- **Given**: Python exception with stack trace
- **When**: `collect_error(..., exception=e)`
- **Then**: Error Record created with extracted error_type, error_message, stack_trace

**Test 2: collect_error with manual error_message**
- **Given**: No exception, manual error description
- **When**: `collect_error(..., error_message="Manual error")`
- **Then**: Error Record created with manual message, no stack trace

**Test 3: collect_error without exception or message**
- **Given**: Neither exception nor error_message provided
- **When**: `collect_error(...)`
- **Then**: Raises `ValueError`

**Test 4: Auto-categorization for API auth failure**
- **Given**: Exception type is `AuthenticationError`
- **When**: `collect_error(..., exception=AuthenticationError(...))`
- **Then**: Severity auto-set to "critical"

**Test 5: Auto-categorization for encoding error**
- **Given**: Exception type is `EncodingError`
- **When**: `collect_error(..., exception=EncodingError(...))`
- **Then**: Severity auto-set to "high"

**Test 6: persist_error to correct directory**
- **Given**: Error with severity="high"
- **When**: `persist_error(error)`
- **Then**: File written to `errors/high/{error_id}.json`

**Test 7: get_error_summary with multiple errors**
- **Given**: 2 high, 5 medium, 3 low errors for run_id
- **When**: `get_error_summary(run_id)`
- **Then**: Returns `{"critical": 0, "high": 2, "medium": 5, "low": 3}`

**Test 8: update_error_status to fixed**
- **Given**: Error with resolution_status="open"
- **When**: `update_error_status(error_id, "fixed", fix_commit="abc123")`
- **Then**: Error record updated, resolution_status="fixed", fix_commit="abc123"
