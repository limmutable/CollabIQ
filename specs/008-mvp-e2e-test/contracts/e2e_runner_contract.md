# Contract: E2ERunner

**Module**: `src/e2e_test/runner.py`
**Purpose**: Orchestrate end-to-end test execution, coordinate test harness components

## Interface

###  Method: `run_tests`

**Description**: Execute E2E tests with a set of emails, collect errors and metrics

**Signature**:
```python
def run_tests(
    email_ids: list[str],
    test_mode: bool = True,
    output_dir: str = "data/e2e_test"
) -> TestRun
```

**Parameters**:
- `email_ids` (list[str]): Gmail message IDs to process
- `test_mode` (bool): If True, use test Notion database; if False, use production database
- `output_dir` (str): Directory to write test results, errors, and metrics

**Returns**:
- `TestRun`: Complete test run metadata with results

**Raises**:
- `ValueError`: If `email_ids` is empty or invalid
- `EnvironmentError`: If test database not configured when `test_mode=True`
- `RuntimeError`: If test run fails to initialize

**Behavior**:
1. Validate environment configuration (API keys, database IDs)
2. Create Test Run with unique `run_id` (timestamp-based)
3. For each email in `email_ids`:
   - Execute full pipeline (reception → extraction → matching → classification → write)
   - Collect errors via ErrorCollector
   - Track performance via PerformanceTracker
   - Validate data integrity via Validator
4. Aggregate results and generate Test Run summary
5. Write Test Run, errors, and metrics to `output_dir`
6. Return completed Test Run object

**Success Criteria**:
- All emails processed (success or failure logged)
- Test Run status set to "completed" (or "failed" if unhandled exception)
- Errors categorized by severity and persisted to disk
- Performance metrics collected for each pipeline stage

**Example Usage**:
```python
runner = E2ERunner()
test_run = runner.run_tests(
    email_ids=["msg_001", "msg_002", "msg_003"],
    test_mode=True,
    output_dir="data/e2e_test"
)

print(f"Processed {test_run.emails_processed} emails")
print(f"Success rate: {test_run.success_count / test_run.emails_processed:.1%}")
print(f"Errors: {test_run.error_summary}")
```

---

### Method: `resume_test_run`

**Description**: Resume an interrupted test run from last successful email

**Signature**:
```python
def resume_test_run(run_id: str) -> TestRun
```

**Parameters**:
- `run_id` (str): ID of test run to resume (ISO 8601 timestamp)

**Returns**:
- `TestRun`: Updated test run metadata with resumed results

**Raises**:
- `FileNotFoundError`: If test run with `run_id` not found
- `ValueError`: If test run is already completed

**Behavior**:
1. Load existing Test Run from `data/e2e_test/runs/{run_id}.json`
2. Verify test run status is "interrupted" or "running"
3. Identify last successfully processed email
4. Resume processing from next email in `test_email_ids`
5. Update Test Run with new results
6. Return updated Test Run

**Success Criteria**:
- Test run successfully resumes from interruption point
- No duplicate processing of already-completed emails
- Final Test Run reflects combined results (original + resumed)

---

### Method: `validate_test_database`

**Description**: Verify test Notion database exists and has matching schema to production

**Signature**:
```python
def validate_test_database() -> bool
```

**Returns**:
- `bool`: True if test database is valid, False otherwise

**Raises**:
- `EnvironmentError`: If `NOTION_DATABASE_ID_COLLABIQ_TEST` not set

**Behavior**:
1. Fetch schema from production database (`NOTION_DATABASE_ID_COLLABIQ`)
2. Fetch schema from test database (`NOTION_DATABASE_ID_COLLABIQ_TEST`)
3. Compare field names and types
4. Return True if schemas match, False if mismatch detected

**Success Criteria**:
- Schema comparison detects field name mismatches
- Schema comparison detects field type mismatches (text vs select, etc.)
- Returns True only if 100% schema match

---

## Dependencies

- `ErrorCollector`: Capture and categorize errors
- `PerformanceTracker`: Measure timing and resource usage
- `ReportGenerator`: Generate test summary reports
- `Validator`: Verify data integrity
- Existing MVP components: `EmailReceiver`, `GeminiAdapter`, `ContentNormalizer`, `NotionIntegrator`, `NotionWriter`

---

## Contract Tests

**Test 1: run_tests with valid email_ids**
- **Given**: 3 valid email IDs
- **When**: `run_tests(["msg_001", "msg_002", "msg_003"], test_mode=True)`
- **Then**: Test Run created with `email_count=3`, status="completed"

**Test 2: run_tests with empty email_ids**
- **Given**: Empty list
- **When**: `run_tests([], test_mode=True)`
- **Then**: Raises `ValueError`

**Test 3: run_tests without test database configured**
- **Given**: `NOTION_DATABASE_ID_COLLABIQ_TEST` not set
- **When**: `run_tests(["msg_001"], test_mode=True)`
- **Then**: Raises `EnvironmentError`

**Test 4: resume_test_run for non-existent run**
- **Given**: Invalid `run_id`
- **When**: `resume_test_run("invalid-id")`
- **Then**: Raises `FileNotFoundError`

**Test 5: validate_test_database with matching schemas**
- **Given**: Test and production databases have identical schemas
- **When**: `validate_test_database()`
- **Then**: Returns `True`

**Test 6: validate_test_database with schema mismatch**
- **Given**: Test database missing a required field
- **When**: `validate_test_database()`
- **Then**: Returns `False`
