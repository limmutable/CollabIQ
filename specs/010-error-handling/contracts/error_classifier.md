# Contract: Error Classifier

**Component**: `src/error_handling/error_classifier.py`
**Purpose**: Classify exceptions into TRANSIENT, PERMANENT, or CRITICAL categories

---

## Interface

### `class ErrorClassifier`

Classifies exceptions to determine retry behavior and error handling strategy.

**Methods**:

```python
@staticmethod
def classify(exception: Exception) -> ErrorCategory:
    """Classify exception into TRANSIENT, PERMANENT, or CRITICAL."""
    pass

@staticmethod
def is_retryable(exception: Exception) -> bool:
    """Check if exception should be retried."""
    pass

@staticmethod
def extract_retry_after(exception: Exception) -> Optional[float]:
    """Extract Retry-After header value (in seconds) if present."""
    pass

@staticmethod
def get_http_status(exception: Exception) -> Optional[int]:
    """Extract HTTP status code from exception if available."""
    pass
```

---

## Contract Specifications

### 1. **Classify Network Timeout (TRANSIENT)**

**Given**: Exception is `socket.timeout` or `ConnectionError`
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.TRANSIENT`
- `is_retryable()` returns `True`

**Test**:
```python
classifier = ErrorClassifier()

timeout_error = socket.timeout("Connection timed out")
assert classifier.classify(timeout_error) == ErrorCategory.TRANSIENT
assert classifier.is_retryable(timeout_error) is True
```

---

### 2. **Classify Rate Limit (TRANSIENT with Retry-After)**

**Given**: Exception is `APIResponseError` with 429 status code and `Retry-After` header
**When**: `classify()` and `extract_retry_after()` are called
**Then**:
- Returns `ErrorCategory.TRANSIENT`
- `is_retryable()` returns `True`
- `extract_retry_after()` returns seconds from header

**Test**:
```python
rate_limit_error = APIResponseError(
    status_code=429,
    headers={"Retry-After": "120"}
)

assert classifier.classify(rate_limit_error) == ErrorCategory.TRANSIENT
assert classifier.is_retryable(rate_limit_error) is True
assert classifier.extract_retry_after(rate_limit_error) == 120.0
```

---

### 3. **Classify Authentication Error (CRITICAL)**

**Given**: Exception is `HttpError` with 401 status code
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.CRITICAL`
- `is_retryable()` returns `False`
- Logs with severity ERROR

**Test**:
```python
auth_error = HttpError(resp={"status": "401"}, content=b"Unauthorized")

assert classifier.classify(auth_error) == ErrorCategory.CRITICAL
assert classifier.is_retryable(auth_error) is False
assert classifier.get_http_status(auth_error) == 401
```

---

### 4. **Classify Permission Error (PERMANENT)**

**Given**: Exception is `HttpError` with 403 status code
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.PERMANENT`
- `is_retryable()` returns `False`

**Test**:
```python
permission_error = HttpError(resp={"status": "403"}, content=b"Forbidden")

assert classifier.classify(permission_error) == ErrorCategory.PERMANENT
assert classifier.is_retryable(permission_error) is False
```

---

### 5. **Classify Server Error (TRANSIENT)**

**Given**: Exception is `HttpError` with 503 status code
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.TRANSIENT`
- `is_retryable()` returns `True`

**Test**:
```python
server_error = HttpError(resp={"status": "503"}, content=b"Service Unavailable")

assert classifier.classify(server_error) == ErrorCategory.TRANSIENT
assert classifier.is_retryable(server_error) is True
```

---

### 6. **Classify Resource Not Found (PERMANENT)**

**Given**: Exception is `HttpError` with 404 status code
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.PERMANENT`
- `is_retryable()` returns `False`

**Test**:
```python
not_found_error = HttpError(resp={"status": "404"}, content=b"Not Found")

assert classifier.classify(not_found_error) == ErrorCategory.PERMANENT
assert classifier.is_retryable(not_found_error) is False
```

---

### 7. **Classify Validation Error (PERMANENT)**

**Given**: Exception is `ValidationError` from Pydantic
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.PERMANENT`
- `is_retryable()` returns `False`
- Error logged with field-level validation details

**Test**:
```python
validation_error = ValidationError([{
    "loc": ("company_id",),
    "msg": "field required",
    "type": "value_error.missing"
}])

assert classifier.classify(validation_error) == ErrorCategory.PERMANENT
assert classifier.is_retryable(validation_error) is False
```

---

### 8. **Classify Gemini Resource Exhausted (TRANSIENT)**

**Given**: Exception is `google.api_core.exceptions.ResourceExhausted` (429)
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.TRANSIENT`
- `is_retryable()` returns `True`

**Test**:
```python
from google.api_core.exceptions import ResourceExhausted

quota_error = ResourceExhausted("Quota exceeded")

assert classifier.classify(quota_error) == ErrorCategory.TRANSIENT
assert classifier.is_retryable(quota_error) is True
```

---

### 9. **Classify Gemini Unauthenticated (CRITICAL)**

**Given**: Exception is `google.api_core.exceptions.Unauthenticated` (401)
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.CRITICAL`
- `is_retryable()` returns `False`

**Test**:
```python
from google.api_core.exceptions import Unauthenticated

unauth_error = Unauthenticated("Invalid API key")

assert classifier.classify(unauth_error) == ErrorCategory.CRITICAL
assert classifier.is_retryable(unauth_error) is False
```

---

### 10. **Parse Retry-After as Seconds**

**Given**: Exception has `Retry-After: 120` header (seconds format)
**When**: `extract_retry_after()` is called
**Then**:
- Returns `120.0` (float seconds)

**Test**:
```python
rate_limit_error = APIResponseError(
    status_code=429,
    headers={"Retry-After": "120"}
)

assert classifier.extract_retry_after(rate_limit_error) == 120.0
```

---

### 11. **Parse Retry-After as HTTP Date**

**Given**: Exception has `Retry-After: Wed, 21 Oct 2025 07:28:00 GMT` header (date format)
**When**: `extract_retry_after()` is called
**Then**:
- Parses date, calculates seconds from now
- Returns seconds as float

**Test**:
```python
future_time = (datetime.utcnow() + timedelta(minutes=5)).strftime("%a, %d %b %Y %H:%M:%S GMT")
rate_limit_error = APIResponseError(
    status_code=429,
    headers={"Retry-After": future_time}
)

retry_seconds = classifier.extract_retry_after(rate_limit_error)
assert 295 <= retry_seconds <= 305  # ~5 minutes (with timing variance)
```

---

### 12. **Fallback Classification (Unknown Exception)**

**Given**: Exception is unknown type (e.g., `KeyError`)
**When**: `classify()` is called
**Then**:
- Returns `ErrorCategory.PERMANENT` (safer default)
- `is_retryable()` returns `False`
- Logs warning about unknown exception type

**Test**:
```python
unknown_error = KeyError("missing_key")

assert classifier.classify(unknown_error) == ErrorCategory.PERMANENT
assert classifier.is_retryable(unknown_error) is False

# Check warning log
assert "Unknown exception type" in error_logs[-1]["message"]
```

---

## Classification Decision Tree

```
Exception caught
│
├─ Check exception type first
│  ├─ socket.timeout, ConnectionError, TimeoutError, OSError → TRANSIENT
│  ├─ google.api_core.exceptions.ResourceExhausted → TRANSIENT
│  ├─ google.api_core.exceptions.DeadlineExceeded → TRANSIENT
│  ├─ google.api_core.exceptions.Unauthenticated → CRITICAL
│  ├─ google.api_core.exceptions.PermissionDenied → PERMANENT
│  ├─ ValidationError → PERMANENT
│  └─ Continue to HTTP status check
│
├─ Check HTTP status (if available via get_http_status)
│  ├─ 401 → CRITICAL
│  ├─ 429 → TRANSIENT (extract Retry-After)
│  ├─ 400, 403, 404, 501 → PERMANENT
│  └─ 500-504 → TRANSIENT
│
└─ Fallback → PERMANENT (safer default)
```

---

## Per-API Exception Mappings

### Gmail API (`google-api-python-client`)

| Exception | HTTP Status | Category | Retryable |
|-----------|------------|----------|-----------|
| `HttpError(401)` | 401 | CRITICAL | No |
| `HttpError(403)` | 403 | PERMANENT | No |
| `HttpError(404)` | 404 | PERMANENT | No |
| `HttpError(429)` | 429 | TRANSIENT | Yes |
| `HttpError(5xx)` | 500-504 | TRANSIENT | Yes |
| `socket.timeout` | - | TRANSIENT | Yes |
| `google.auth.exceptions.RefreshError` | - | CRITICAL | No |

### Gemini API (`google-generativeai`)

| Exception | HTTP Status | Category | Retryable |
|-----------|------------|----------|-----------|
| `ResourceExhausted` | 429 | TRANSIENT | Yes |
| `DeadlineExceeded` | 504 | TRANSIENT | Yes |
| `Unauthenticated` | 401 | CRITICAL | No |
| `PermissionDenied` | 403 | PERMANENT | No |
| `InvalidArgument` | 400 | PERMANENT | No |
| `json.JSONDecodeError` | - | PERMANENT | No |

### Notion API (`notion-client`)

| Exception | HTTP Status | Category | Retryable |
|-----------|------------|----------|-----------|
| `APIResponseError(unauthorized)` | 401 | CRITICAL | No |
| `APIResponseError(rate_limited)` | 429 | TRANSIENT | Yes |
| `APIResponseError(object_not_found)` | 404 | PERMANENT | No |
| `APIResponseError(restricted_resource)` | 403 | PERMANENT | No |
| `APIResponseError(5xx)` | 500-504 | TRANSIENT | Yes |

### Infisical API

| Exception | HTTP Status | Category | Retryable |
|-----------|------------|----------|-----------|
| `requests.exceptions.Timeout` | - | TRANSIENT | Yes |
| `requests.exceptions.ConnectionError` | - | TRANSIENT | Yes |
| `HTTPError(401)` | 401 | CRITICAL | No |

---

## Error Handling

| Scenario | Classification | Action |
|----------|---------------|--------|
| Network timeout | TRANSIENT | Retry with exponential backoff |
| Rate limit (429) | TRANSIENT | Retry with Retry-After header |
| Auth error (401) | CRITICAL | Fail immediately, log ERROR, escalate |
| Permission error (403) | PERMANENT | Fail immediately, log WARNING |
| Server error (5xx) | TRANSIENT | Retry with exponential backoff |
| Validation error | PERMANENT | Skip email, log validation details |
| Unknown exception | PERMANENT | Fail immediately, log WARNING |

---

## Performance Contracts

- Classification decision: < 1ms (in-memory check, no I/O)
- HTTP status extraction: < 1ms (attribute access)
- Retry-After parsing: < 1ms (string parsing)

---

## Dependencies

- `ErrorCategory` enum from `data-model.md`
- Standard library: `socket`, `http.client`
- External: `google.api_core.exceptions`, `notion_client.errors`
- Optional: `email.utils.parsedate_to_datetime` for HTTP date parsing

---

## Test Coverage Requirements

- ✅ Unit tests for all 12 contract scenarios
- ✅ Exception type mapping tests (Gmail, Gemini, Notion, Infisical)
- ✅ HTTP status extraction tests
- ✅ Retry-After parsing tests (seconds + HTTP date formats)
- ✅ Fallback classification tests
- ✅ Performance tests to verify < 1ms classification time
