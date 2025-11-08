# Contract: LLM Provider Interface

**Feature**: Multi-LLM Provider Support
**Branch**: `011-multi-llm`
**Date**: 2025-11-08

## Overview

This contract defines the interface that all LLM provider implementations (Gemini, Claude, OpenAI) must adhere to. This ensures consistent behavior across different providers and enables the orchestrator to treat all providers uniformly.

---

## Interface Definition

### Class: `LLMProvider` (Abstract Base Class)

**Module**: `src/llm_provider/base.py` (existing)

**Purpose**: Abstract interface for LLM-based entity extraction

**Implementation Requirement**: All concrete providers MUST inherit from this class and implement all abstract methods

---

## Method: `extract_entities`

### Signature

```python
@abstractmethod
def extract_entities(self, email_text: str) -> ExtractedEntities:
    pass
```

### Purpose
Extract 5 key entities from email text with confidence scores.

### Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `email_text` | str | Yes | Cleaned email body (Korean/English/mixed) | Non-empty string, max 10,000 characters |

**Pre-conditions**:
- `email_text` must not be empty
- `email_text` must not exceed 10,000 characters
- `email_text` should have signatures, disclaimers, and quoted text already removed (by content normalizer)

### Return Value

**Type**: `ExtractedEntities` (Pydantic model)

**Structure**:
```python
class ExtractedEntities(BaseModel):
    person_in_charge: str | None      # 담당자 (or None if missing)
    startup_name: str | None           # 스타트업명 (or None if missing)
    partner_org: str | None            # 협업기관 (or None if missing)
    details: str                       # 협업내용 (original text preserved)
    date: datetime | None              # 날짜 (parsed to datetime, or None)
    confidence: ConfidenceScores       # Confidence scores (0.0-1.0 per field)
    email_id: str                      # Unique email identifier
    extracted_at: datetime             # UTC timestamp of extraction
```

**ConfidenceScores Structure**:
```python
class ConfidenceScores(BaseModel):
    person: float    # 0.0-1.0
    startup: float   # 0.0-1.0
    partner: float   # 0.0-1.0
    details: float   # 0.0-1.0
    date: float      # 0.0-1.0
```

**Validation Rules**:
- All confidence scores MUST be in range [0.0, 1.0]
- Missing entities (None values) MUST have confidence 0.0
- `details` is always required (cannot be None)
- `extracted_at` MUST be UTC timezone

### Exceptions

All provider implementations MUST raise these exceptions for specific error conditions:

| Exception | When to Raise | HTTP Status Equivalent | Retry Recommended? |
|-----------|---------------|------------------------|-------------------|
| `LLMRateLimitError` | Rate limit exceeded | 429 | Yes (with exponential backoff) |
| `LLMTimeoutError` | Request timeout | 408 | Yes (with increased timeout) |
| `LLMAuthenticationError` | Authentication failed | 401 / 403 | No (requires API key fix) |
| `LLMValidationError` | Malformed API response | N/A | No (provider bug or schema mismatch) |
| `LLMAPIError` | Generic API error | 500 / 502 / 503 / 504 | Yes (for 5xx errors) |

**Exception Hierarchy**:
```
LLMAPIError (base)
├── LLMRateLimitError
├── LLMTimeoutError
├── LLMAuthenticationError
└── LLMValidationError
```

**Exception Attributes**:
- All exceptions MUST include descriptive error message
- Rate limit errors SHOULD include `retry_after` seconds if available from API
- Validation errors SHOULD include the malformed response snippet

### Behavior Contracts

#### Contract 1: Method Signature
```python
def test_extract_entities_accepts_email_text():
    provider = ConcreteProvider()
    result = provider.extract_entities("sample email text")
    assert isinstance(result, ExtractedEntities)
```

#### Contract 2: Return Type
```python
def test_extract_entities_returns_extracted_entities():
    provider = ConcreteProvider()
    result = provider.extract_entities("collaboration update email")

    # Verify all required attributes exist
    assert hasattr(result, "person_in_charge")
    assert hasattr(result, "startup_name")
    assert hasattr(result, "partner_org")
    assert hasattr(result, "details")
    assert hasattr(result, "date")
    assert hasattr(result, "confidence")
    assert hasattr(result, "email_id")
    assert hasattr(result, "extracted_at")
```

#### Contract 3: Exception Handling
```python
def test_extract_entities_raises_llm_api_error_on_failure():
    provider = ConcreteProvider(should_fail=True)

    with pytest.raises(LLMAPIError):
        provider.extract_entities("email text")
```

#### Contract 4: Confidence Score Range
```python
def test_confidence_scores_are_0_to_1():
    provider = ConcreteProvider()
    result = provider.extract_entities("sample email")

    assert 0.0 <= result.confidence.person <= 1.0
    assert 0.0 <= result.confidence.startup <= 1.0
    assert 0.0 <= result.confidence.partner <= 1.0
    assert 0.0 <= result.confidence.details <= 1.0
    assert 0.0 <= result.confidence.date <= 1.0
```

#### Contract 5: Missing Entities
```python
def test_missing_entities_return_none_with_zero_confidence():
    provider = ConcreteProvider()
    result = provider.extract_entities("email with missing person")

    # If person_in_charge is None, confidence.person must be 0.0
    if result.person_in_charge is None:
        assert result.confidence.person == 0.0

    # Same for other optional fields
    if result.date is None:
        assert result.confidence.date == 0.0
```

#### Contract 6: Non-Instantiable Base Class
```python
def test_interface_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        LLMProvider()
```

---

## Provider Implementation Requirements

### Mandatory Implementations
All concrete provider classes (GeminiAdapter, ClaudeAdapter, OpenAIAdapter) MUST:

1. **Inherit from LLMProvider**
   ```python
   class ClaudeAdapter(LLMProvider):
       pass
   ```

2. **Implement `extract_entities` method**
   - Accept `email_text: str` parameter
   - Return `ExtractedEntities` instance
   - Raise appropriate `LLM*Error` exceptions

3. **Handle authentication**
   - Read API key from environment variable
   - Validate API key on initialization or first use
   - Raise `LLMAuthenticationError` if invalid

4. **Handle timeouts**
   - Implement configurable timeout (default: 60 seconds)
   - Raise `LLMTimeoutError` if exceeded

5. **Handle rate limiting**
   - Detect rate limit errors from provider API
   - Raise `LLMRateLimitError` with retry_after if available
   - Support retry with exponential backoff (via decorator)

6. **Validate responses**
   - Check API response format matches expected schema
   - Raise `LLMValidationError` if malformed
   - Convert provider-specific response to `ExtractedEntities` format

7. **Generate confidence scores**
   - Prompt the LLM to provide confidence scores (0.0-1.0)
   - Use logprobs if available (OpenAI), otherwise prompt-based
   - Set confidence = 0.0 for missing/None entities

8. **Track token usage**
   - Extract input/output token counts from API response
   - Make available for cost tracking (via instance variables or return metadata)

### Optional Implementations
Providers MAY:

1. **Support custom models**
   ```python
   class ClaudeAdapter(LLMProvider):
       def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
           ...
   ```

2. **Support custom prompts**
   - Allow prompt template customization
   - Maintain default prompt that works well

3. **Provide health check method**
   ```python
   def health_check(self) -> bool:
       # Lightweight API call to verify connectivity
       pass
   ```

4. **Expose provider metadata**
   ```python
   @property
   def provider_name(self) -> str:
       return "claude"

   @property
   def model_id(self) -> str:
       return self._model
   ```

---

## Testing Requirements

### Contract Tests
Every provider implementation MUST pass the contract test suite located at:
`tests/contract/test_llm_provider_interface.py`

**Required test cases**:
1. `test_extract_entities_accepts_email_text` ✅
2. `test_extract_entities_returns_extracted_entities` ✅
3. `test_extract_entities_raises_llm_api_error_on_failure` ✅
4. `test_confidence_scores_are_0_to_1` ✅
5. `test_missing_entities_return_none_with_zero_confidence` ✅
6. `test_interface_cannot_be_instantiated_directly` ✅

### Provider-Specific Contract Tests
Each provider MUST have its own contract test file:
- `tests/contract/test_gemini_adapter_contract.py` (existing)
- `tests/contract/test_claude_adapter_contract.py` (new)
- `tests/contract/test_openai_adapter_contract.py` (new)

**Test pattern**:
```python
import pytest
from src.llm_adapters.claude_adapter import ClaudeAdapter
from src.llm_provider.types import ExtractedEntities
from src.llm_provider.exceptions import LLMAPIError

def test_claude_adapter_implements_llm_provider():
    """Verify ClaudeAdapter inherits from LLMProvider"""
    adapter = ClaudeAdapter(api_key="test_key")
    assert hasattr(adapter, 'extract_entities')
    assert callable(adapter.extract_entities)

def test_claude_adapter_contract():
    """Run all contract tests against ClaudeAdapter"""
    # Run standard contract test suite
    pass
```

---

## Usage Example

```python
from src.llm_adapters.claude_adapter import ClaudeAdapter
from src.llm_provider.exceptions import LLMAPIError, LLMRateLimitError

# Initialize provider
adapter = ClaudeAdapter(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Extract entities
try:
    email_text = "어제 신세계와 본봄 파일럿 킥오프"
    entities = adapter.extract_entities(email_text)

    print(f"Startup: {entities.startup_name}")
    print(f"Confidence: {entities.confidence.startup}")

except LLMRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")

except LLMAPIError as e:
    print(f"API error: {e}")
```

---

## Backward Compatibility

### Existing Code
The existing `GeminiAdapter` already implements this interface and MUST continue to work without modifications.

### Migration Path
1. Existing `LLMProvider` interface remains unchanged
2. New providers (Claude, OpenAI) implement same interface
3. Existing code using `GeminiAdapter` continues to work
4. Orchestrator layer uses `LLMProvider` interface without knowing specific provider

---

## Summary

This contract ensures:
- ✅ All providers behave consistently
- ✅ Orchestrator can treat providers uniformly
- ✅ Error handling is standardized
- ✅ Confidence scores are comparable across providers
- ✅ Testing is systematic and comprehensive
- ✅ Backward compatibility with existing GeminiAdapter
