# Gemini 2.5 Flash API Integration Research

Entity Extraction from Korean/English Emails with Confidence Scores

> **Note (2025-11-08)**: This document contains the original research and manual retry implementation from Phase 1b. The retry logic has been superseded by the unified error handling system in **Phase 010 (Error Handling & Retry Logic)**. For current retry/error handling, see [src/error_handling/README.md](../../src/error_handling/README.md). This document is preserved for historical context and API research reference.

---

## Table of Contents

1. [Gemini API Authentication & Setup](#gemini-api-authentication--setup)
2. [Rate Limits & Pricing](#rate-limits--pricing)
3. [Prompt Engineering for Entity Extraction](#prompt-engineering-for-entity-extraction)
4. [Error Handling](#error-handling)
5. [Implementation Recommendations](#implementation-recommendations)

---

## Gemini API Authentication & Setup

### Installation

The Gemini API for Python is available through the `google-genai` package (latest SDK).

**Requirements:**
- Python 3.9 or later (Project uses Python 3.12)
- Valid Google API key

**Installation Command:**
```bash
pip install -U google-genai
```

### API Key Setup

1. **Obtain API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Store securely (use environment variable or secrets management)

2. **Environment Variable:**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

### Basic Client Initialization

The `google-genai` SDK automatically detects the `GEMINI_API_KEY` environment variable:

```python
from google import genai

# Auto-detect API key from GEMINI_API_KEY environment variable
client = genai.Client()

# Or explicitly pass the API key
client = genai.Client(api_key="your-api-key-here")
```

### Basic Content Generation Example

```python
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Extract entities from this email: [email content]"
)

print(response.text)
```

### Key Points

- The SDK handles authentication automatically via the API key header (`x-goog-api-key`)
- All requests use the same authentication mechanism
- API key is required for all operations
- No credential files or OAuth flows needed for basic usage

---

## Rate Limits & Pricing

### Free Tier Limits (Google AI Studio)

| Metric | Limit |
|--------|-------|
| **Input Requests** | 10 requests/minute |
| **Token Rate** | 250,000 tokens/minute |
| **Daily Requests** | 250-500 requests/day |
| **Cost** | Free |
| **Content Usage** | Content may be used to improve Google products |
| **Context Caching** | Not available |
| **Batch API** | Not available |

### Important Notes on Free Tier

**Automatic Model Switching:**
- Free tier users get Gemini 2.5 Pro access for the first 10-15 prompts
- After quota exhaustion, the API automatically switches to Gemini 2.5 Flash
- This is a built-in safety mechanism to balance performance with capacity

**Daily Reset:**
- Request quotas reset at midnight Pacific Time
- Per-project limits (multiple projects = separate quotas)

**Commercial Usage:**
- Free tier explicitly permits commercial usage
- No restrictions on using extracted data commercially

### Rate Limit Exceeded Behavior

When rate limits are exceeded, the API returns:

**HTTP 429 Error (Resource Exhausted)**
```
Error Code: RESOURCE_EXHAUSTED
Message: "Rate limit exceeded for [model]"
```

**Retry Strategy:**
- Implement exponential backoff
- Wait times: Initial delay → doubling with each retry
- Maximum recommended wait: 60 seconds

### Quota Considerations for Production

For sustained or production use:
- Daily request limits become a bottleneck
- Token limits (250k/min) may constrain batch processing
- Consider paid tier for:
  - Higher rate limits
  - Context caching (reduces repeated token costs)
  - Batch API (50% cost reduction)
  - Data privacy (content not used to improve products)

### Pricing (Paid Tier)

Gemini 2.5 Flash pricing:
- **Input:** Varies by token count
- **Output:** Varies by token count
- **Context caching:** Additional cost but reduces repeated processing
- **Batch API:** 50% discount on input tokens

Refer to [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing) for current rates.

---

## Prompt Engineering for Entity Extraction

### Structured Output Overview

Gemini 2.5 Flash can generate JSON structured output using `response_mime_type` and `response_schema`:

```python
from google import genai
import json

client = genai.Client()

# Define the response schema
schema = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string"},
                    "value": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "source_text": {"type": "string"}
                },
                "required": ["entity_type", "value", "confidence"]
            }
        }
    },
    "required": ["entities"]
}

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Extract entities from the email...",
    config={
        "response_mime_type": "application/json",
        "response_schema": schema
    }
)

entities = json.loads(response.text)
```

### Requesting Confidence Scores

**Native Approach:**
- Include `confidence` field in your schema (0.0 to 1.0 scale)
- Prompt the model to evaluate confidence based on:
  - Text clarity
  - Context definiteness
  - Extraction certainty

**Validation Approach:**
- Gemini assesses if extracted data is meaningful vs "N/A" or empty
- Returns boolean confidence (meaningful or not)
- Less granular but reliable for binary validity checks

**Recommended for this project:**
- Use the native confidence float (0.0-1.0) for granular scoring
- Include explicit instructions in the prompt
- Example prompt instruction:
  ```
  For each entity, provide:
  - entity_type: The type of entity (name, email, phone, company, date)
  - value: The extracted value
  - confidence: Your confidence (0.0 to 1.0) based on text clarity
  - source_text: The exact text from the email
  ```

### Zero-Shot vs Few-Shot Prompting

**Zero-Shot Prompting:**
- No examples provided
- Works for basic tasks
- Less reliable for structured extraction
- Not recommended for entity extraction

**Few-Shot Prompting (Recommended):**
- Include 2-5 examples of expected input/output
- Show the exact format and structure you want
- Provides 30-50% accuracy improvement
- **Official guidance:** "Always include few-shot examples in your prompts"

### Few-Shot Example for Entity Extraction

```python
system_prompt = """You are an expert entity extractor specializing in Korean and English emails.

Extract exactly 5 entity types:
1. PERSON_NAME - Names of individuals (Korean or English)
2. EMAIL_ADDRESS - Email addresses
3. PHONE_NUMBER - Phone numbers (Korean +82 or other formats)
4. COMPANY_NAME - Company or organization names
5. DATE - Important dates mentioned

For each entity:
- Provide the exact value as it appears
- Confidence: How certain you are (0.0 = not confident, 1.0 = very confident)
- Source text: The exact substring from the email"""

few_shot_examples = [
    {
        "input": "안녕하세요, 저는 김철수입니다. 제 이메일은 kim.chulsu@company.com이고 전화번호는 +82-10-1234-5678입니다. 2025년 1월 15일에 만날 수 있습니다.",
        "output": {
            "entities": [
                {
                    "entity_type": "PERSON_NAME",
                    "value": "김철수",
                    "confidence": 0.98,
                    "source_text": "저는 김철수입니다"
                },
                {
                    "entity_type": "EMAIL_ADDRESS",
                    "value": "kim.chulsu@company.com",
                    "confidence": 0.99,
                    "source_text": "kim.chulsu@company.com"
                },
                {
                    "entity_type": "PHONE_NUMBER",
                    "value": "+82-10-1234-5678",
                    "confidence": 0.99,
                    "source_text": "+82-10-1234-5678"
                },
                {
                    "entity_type": "COMPANY_NAME",
                    "value": "company",
                    "confidence": 0.85,
                    "source_text": "kim.chulsu@company.com"
                },
                {
                    "entity_type": "DATE",
                    "value": "2025-01-15",
                    "confidence": 0.95,
                    "source_text": "2025년 1월 15일"
                }
            ]
        }
    },
    {
        "input": "Hi, I'm Sarah Johnson. You can reach me at sarah@techcorp.io or call (555) 123-4567. Let's schedule a meeting for March 20, 2025.",
        "output": {
            "entities": [
                {
                    "entity_type": "PERSON_NAME",
                    "value": "Sarah Johnson",
                    "confidence": 0.98,
                    "source_text": "I'm Sarah Johnson"
                },
                {
                    "entity_type": "EMAIL_ADDRESS",
                    "value": "sarah@techcorp.io",
                    "confidence": 0.99,
                    "source_text": "sarah@techcorp.io"
                },
                {
                    "entity_type": "PHONE_NUMBER",
                    "value": "(555) 123-4567",
                    "confidence": 0.99,
                    "source_text": "(555) 123-4567"
                },
                {
                    "entity_type": "COMPANY_NAME",
                    "value": "techcorp",
                    "confidence": 0.90,
                    "source_text": "sarah@techcorp.io"
                },
                {
                    "entity_type": "DATE",
                    "value": "2025-03-20",
                    "confidence": 0.98,
                    "source_text": "March 20, 2025"
                }
            ]
        }
    }
]
```

### Bilingual Content Handling

**Gemini 2.5 Flash Multilingual Support:**
- Supports 100+ languages including Korean and English
- Performs well on multilingual tasks
- Can handle mixed-language content in single email

**Best Practices for Bilingual Extraction:**

1. **Explicit Language Awareness:**
   ```python
   system_prompt += """
   Handle both Korean (한글) and English text seamlessly.
   - Korean names may follow 성명 format (family name + given name)
   - English names follow given name + family name format
   - Phone numbers: Korean uses +82 country code, US uses +1
   - Date formats: Korean typically uses YYYY년 M월 D일, English uses various formats
   """
   ```

2. **Mixed-Language Examples:**
   - Include few-shot examples with Korean-only text
   - Include few-shot examples with English-only text
   - Include few-shot examples with mixed Korean-English content

3. **Entity Type Normalization:**
   - Normalize Korean date formats to ISO 8601 (YYYY-MM-DD)
   - Normalize Korean phone numbers to international format (+82-XX-XXXX-XXXX)
   - Keep original names in their native format, but ensure extraction is accurate

4. **Field Descriptions:**
   - Add language-specific notes in source_text
   - Example: "Korean: 김철수" or "English: John Smith"

### Complete Implementation Example

```python
from google import genai
import json
from typing import List, Dict, Any

client = genai.Client()

def extract_entities_from_email(email_text: str) -> List[Dict[str, Any]]:
    """Extract entities from bilingual Korean/English email."""

    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "enum": ["PERSON_NAME", "EMAIL_ADDRESS", "PHONE_NUMBER", "COMPANY_NAME", "DATE"]
                        },
                        "value": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "source_text": {"type": "string"}
                    },
                    "required": ["entity_type", "value", "confidence", "source_text"]
                },
                "minItems": 0,
                "maxItems": 5
            }
        },
        "required": ["entities"]
    }

    system_prompt = """You are an expert entity extractor for Korean and English emails.
Extract up to 5 entities with these types:
1. PERSON_NAME - Individual names (Korean or English)
2. EMAIL_ADDRESS - Email addresses
3. PHONE_NUMBER - Phone numbers
4. COMPANY_NAME - Company/organization names
5. DATE - Important dates

Return exactly this structure for each entity:
- entity_type: The category
- value: The normalized value
- confidence: 0.0 to 1.0 certainty level
- source_text: The exact text from the email

Bilingual handling:
- Korean dates: Convert YYYY년 M월 D일 to YYYY-MM-DD
- Korean phones: Keep +82 country code format
- Names: Keep in original language and capitalization
- Email/phone confidence should be very high (0.95+)
- Name/date/company confidence depends on context clarity"""

    # Format with few-shot examples
    few_shot = """
Example 1 - Korean email:
Input: "안녕하세요, 김철수입니다. kim.chulsu@company.com 010-1234-5678 2025년 1월 15일"
Output: {
  "entities": [
    {"entity_type": "PERSON_NAME", "value": "김철수", "confidence": 0.98, "source_text": "김철수"},
    {"entity_type": "EMAIL_ADDRESS", "value": "kim.chulsu@company.com", "confidence": 0.99, "source_text": "kim.chulsu@company.com"},
    {"entity_type": "PHONE_NUMBER", "value": "+82-10-1234-5678", "confidence": 0.99, "source_text": "010-1234-5678"},
    {"entity_type": "COMPANY_NAME", "value": "company", "confidence": 0.85, "source_text": "company.com"},
    {"entity_type": "DATE", "value": "2025-01-15", "confidence": 0.98, "source_text": "2025년 1월 15일"}
  ]
}

Example 2 - English email:
Input: "Hi, Sarah Johnson here. sarah@techcorp.io (555) 123-4567 Meeting on March 20, 2025"
Output: {
  "entities": [
    {"entity_type": "PERSON_NAME", "value": "Sarah Johnson", "confidence": 0.98, "source_text": "Sarah Johnson"},
    {"entity_type": "EMAIL_ADDRESS", "value": "sarah@techcorp.io", "confidence": 0.99, "source_text": "sarah@techcorp.io"},
    {"entity_type": "PHONE_NUMBER", "value": "+1-555-123-4567", "confidence": 0.99, "source_text": "(555) 123-4567"},
    {"entity_type": "COMPANY_NAME", "value": "techcorp", "confidence": 0.88, "source_text": "techcorp.io"},
    {"entity_type": "DATE", "value": "2025-03-20", "confidence": 0.97, "source_text": "March 20, 2025"}
  ]
}"""

    combined_prompt = f"{system_prompt}\n\n{few_shot}\n\nNow extract entities from this email:\n\n{email_text}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=combined_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": schema
        }
    )

    result = json.loads(response.text)
    return result.get("entities", [])
```

### Prompt Engineering Best Practices

1. **Be Explicit About Structure:**
   - Clearly define entity types
   - Specify required vs optional fields
   - Show exact JSON format in examples

2. **Use Consistent Formatting:**
   - Keep example input/output structure identical
   - Maintain same field order across examples
   - Use consistent date/phone formats in examples

3. **Provide Context:**
   - Explain why entities matter
   - Mention domain-specific rules (Korean phone format, date conversions)
   - Note confidence level expectations

4. **Balance Examples:**
   - Include 2-5 few-shot examples
   - Vary the complexity
   - Cover edge cases (mixed language, informal formatting)

5. **Handle Ambiguity:**
   - Provide default behavior for unclear entities
   - Explain when to set confidence low (0.5-0.7)
   - Clarify what should be normalized vs kept original

---

## Error Handling

### Common Error Types from Gemini API

| Error Code | Status | Meaning | Cause |
|-----------|--------|---------|-------|
| **429** | RESOURCE_EXHAUSTED | Rate limit exceeded | Too many requests or tokens in short time |
| **500** | INTERNAL_ERROR | Internal server error | Temporary service issue |
| **503** | SERVICE_UNAVAILABLE | Service overloaded | Server temporarily unavailable |
| **400** | INVALID_ARGUMENT | Invalid request | Malformed JSON, invalid model, bad schema |
| **401** | UNAUTHENTICATED | Invalid API key | Missing or expired API key |
| **403** | PERMISSION_DENIED | Access denied | API key lacks permissions |
| **408** | DEADLINE_EXCEEDED | Request timeout | Processing took too long |

### API Error Exception Hierarchy

```python
from google.api_core import exceptions

# Error types you may encounter:
# exceptions.ResourceExhausted - HTTP 429
# exceptions.InternalServerError - HTTP 500
# exceptions.ServiceUnavailable - HTTP 503
# exceptions.InvalidArgument - HTTP 400
# exceptions.Unauthenticated - HTTP 401
# exceptions.PermissionDenied - HTTP 403
# exceptions.DeadlineExceeded - HTTP 408
```

### Recommended Retry Strategy

**Exponential Backoff with Jitter:**

```python
import time
import random
from google.api_core import exceptions
from google import genai

def call_gemini_with_retry(
    client: genai.Client,
    model: str,
    contents: str,
    config: dict = None,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: int = 30
) -> str:
    """
    Call Gemini API with exponential backoff retry strategy.

    Args:
        client: Initialized Gemini client
        model: Model identifier (e.g., "gemini-2.5-flash")
        contents: Prompt/contents to send
        config: Response config (mime type, schema, etc.)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (1 second)
        max_delay: Maximum delay in seconds (60 seconds)
        timeout: Request timeout in seconds

    Returns:
        Response text from the model

    Raises:
        Exception: If all retries exhausted or unrecoverable error
    """

    attempt = 0
    delay = initial_delay

    while attempt < max_retries:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response.text

        except exceptions.ResourceExhausted:
            attempt += 1
            if attempt >= max_retries:
                raise Exception(f"Rate limit exceeded after {max_retries} retries")

            # Add jitter (randomness) to prevent thundering herd
            jitter = random.uniform(0, delay * 0.1)
            wait_time = min(delay + jitter, max_delay)

            print(f"Rate limited. Attempt {attempt}/{max_retries}. "
                  f"Waiting {wait_time:.2f}s before retry...")
            time.sleep(wait_time)

            # Exponential backoff: double delay for next attempt
            delay = min(delay * 2, max_delay)

        except exceptions.InternalServerError:
            attempt += 1
            if attempt >= max_retries:
                raise Exception(f"Internal server error after {max_retries} retries")

            jitter = random.uniform(0, delay * 0.1)
            wait_time = min(delay + jitter, max_delay)

            print(f"Internal server error. Attempt {attempt}/{max_retries}. "
                  f"Waiting {wait_time:.2f}s before retry...")
            time.sleep(wait_time)
            delay = min(delay * 2, max_delay)

        except exceptions.ServiceUnavailable:
            attempt += 1
            if attempt >= max_retries:
                raise Exception(f"Service unavailable after {max_retries} retries")

            jitter = random.uniform(0, delay * 0.1)
            wait_time = min(delay + jitter, max_delay)

            print(f"Service unavailable. Attempt {attempt}/{max_retries}. "
                  f"Waiting {wait_time:.2f}s before retry...")
            time.sleep(wait_time)
            delay = min(delay * 2, max_delay)

        except exceptions.DeadlineExceeded:
            # Timeout - should not retry, likely a slow request
            print(f"Request timeout exceeded {timeout}s")
            raise Exception("Request processing timeout - check model availability")

        except exceptions.InvalidArgument as e:
            # Invalid request - no point retrying
            print(f"Invalid request: {e}")
            raise

        except exceptions.Unauthenticated:
            # API key issue - no point retrying
            print("Authentication failed - check API key")
            raise

        except exceptions.PermissionDenied:
            # Access denied - no point retrying
            print("Permission denied - check API key permissions")
            raise

    raise Exception("Maximum retries exceeded")
```

### Timeout Handling

```python
from google.api_core.exceptions import DeadlineExceeded
import signal

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Request processing timeout")

# Method 1: Using signal (Unix/Linux/macOS only)
def call_with_signal_timeout(call_fn, timeout_seconds=30):
    """Call function with timeout using signal handler."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        result = call_fn()
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError:
        print(f"API call timed out after {timeout_seconds}s")
        raise

# Method 2: Using threading (cross-platform)
import threading

def call_with_thread_timeout(call_fn, timeout_seconds=30):
    """Call function with timeout using threading."""
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = call_fn()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        raise TimeoutError(f"API call timed out after {timeout_seconds}s")

    if exception[0]:
        raise exception[0]

    return result[0]

# Recommended approach for entity extraction:
def extract_with_timeout(email_text: str, timeout_seconds: int = 30):
    """Extract entities with timeout protection."""

    def extract_fn():
        return extract_entities_from_email(email_text)

    try:
        return call_with_thread_timeout(extract_fn, timeout_seconds)
    except TimeoutError as e:
        print(f"Entity extraction timed out: {e}")
        # Return empty entities or use fallback
        return {"entities": []}
```

### Full Error Handling Example

```python
from google.api_core import exceptions
from google import genai
import time
import random
import json

class GeminiEntityExtractor:
    """Robust entity extractor with comprehensive error handling."""

    def __init__(self, api_key: str = None, max_retries: int = 5):
        self.client = genai.Client(api_key=api_key)
        self.max_retries = max_retries
        self.model = "gemini-2.5-flash"

    def extract_entities(self, email_text: str) -> dict:
        """Extract entities with full error handling."""

        schema = {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity_type": {"type": "string"},
                            "value": {"type": "string"},
                            "confidence": {"type": "number"},
                            "source_text": {"type": "string"}
                        }
                    }
                }
            }
        }

        config = {
            "response_mime_type": "application/json",
            "response_schema": schema
        }

        attempt = 0
        delay = 1.0

        while attempt < self.max_retries:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=f"Extract entities from: {email_text}",
                    config=config
                )

                # Parse and validate response
                result = json.loads(response.text)
                return result

            except exceptions.ResourceExhausted:
                attempt += 1
                print(f"Rate limited (attempt {attempt}/{self.max_retries})")

                if attempt >= self.max_retries:
                    return {"error": "Rate limit exceeded", "entities": []}

                wait_time = min(delay + random.uniform(0, delay * 0.1), 60)
                time.sleep(wait_time)
                delay = min(delay * 2, 60)

            except exceptions.InvalidArgument as e:
                return {"error": f"Invalid request: {str(e)}", "entities": []}

            except exceptions.Unauthenticated:
                return {"error": "Authentication failed - invalid API key", "entities": []}

            except json.JSONDecodeError as e:
                return {"error": f"Failed to parse response: {str(e)}", "entities": []}

            except Exception as e:
                attempt += 1
                print(f"Error on attempt {attempt}: {str(e)}")

                if attempt >= self.max_retries:
                    return {"error": f"Failed after {self.max_retries} attempts: {str(e)}", "entities": []}

                wait_time = min(delay + random.uniform(0, delay * 0.1), 60)
                time.sleep(wait_time)
                delay = min(delay * 2, 60)

        return {"error": "Max retries exceeded", "entities": []}
```

---

## Implementation Recommendations

### 1. Architecture Recommendations

**Caching Strategy:**
- Implement TTL-based cache for extracted entities (existing in-memory cache from 003-infisical-secrets)
- Cache key: hash of email content
- TTL: 24-48 hours (entities unlikely to change)
- Reduces API calls and cost

**Batch Processing:**
- For multiple emails, consider using Batch API (when available on paid tier)
- 50% cost reduction on input tokens
- Suitable for background processing of old emails

**Rate Limit Management:**
- Monitor daily request counts
- Implement queue with rate limiting
- Prioritize urgent extractions (fresh emails)
- Queue older emails for off-peak processing

### 2. Configuration Recommendations

**Environment Setup:**
```bash
# .env or environment variables
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_RETRIES=5
GEMINI_INITIAL_DELAY=1.0
GEMINI_MAX_DELAY=60.0
GEMINI_ENTITY_CONFIDENCE_THRESHOLD=0.7  # Minimum confidence to include
```

**Schema Configuration:**
```python
ENTITY_TYPES = ["PERSON_NAME", "EMAIL_ADDRESS", "PHONE_NUMBER", "COMPANY_NAME", "DATE"]
MAX_ENTITIES = 5
CONFIDENCE_THRESHOLD = 0.7  # Filter low-confidence extractions
```

### 3. Performance Considerations

**Token Counting:**
- Entity extraction prompts typically use 500-1000 tokens
- Each email adds variable tokens (200-2000 depending on length)
- With rate limit of 250k tokens/minute, expect significant throughput

**Cost Optimization:**
- Free tier: Approximately 250-500 emails per day (at ~500 tokens each)
- Paid tier: Significantly higher capacity
- Use validation to reject obviously invalid emails early

**Latency:**
- Expect 2-5 seconds per API call
- Network latency: ~500ms
- Model inference: ~1-4 seconds
- Implement async calls for better throughput

### 4. Testing Strategy

**Unit Tests:**
- Test schema validation
- Test few-shot prompt formatting
- Test error handling paths
- Mock Gemini responses

**Integration Tests:**
- Real API calls with test emails
- Bilingual (Korean/English) test cases
- Edge cases (malformed emails, special characters)
- Rate limit simulation

**Example Test Cases:**
```python
# Korean-only email
test_korean = "안녕하세요, 김철수입니다. kim.chulsu@example.com 010-1234-5678"

# English-only email
test_english = "Hi Sarah, reach me at sarah@example.com or (555) 123-4567"

# Mixed language email
test_mixed = "Hi, 이름은 Michael 입니다. michael@example.com 010-9999-8888"

# Email with multiple occurrences
test_multiple = "Contact 김철수 or 박민준 at company@example.com"

# Email with dates
test_dates = "일정: 2025년 1월 15일, Meeting on March 20, 2025"
```

### 5. Logging & Monitoring

**Log Events:**
- Successful extractions with confidence scores
- Failed extractions with error details
- Rate limit hits and retry counts
- Timeout occurrences

**Metrics to Track:**
- Average confidence score per entity type
- Extraction success rate
- Average retry count
- API call latency

### 6. Security Considerations

**API Key Management:**
- Never commit API keys to version control
- Use environment variables or secrets manager (Infisical)
- Rotate keys periodically
- Monitor API usage for suspicious activity

**Data Privacy:**
- Free tier: Content used to improve Google products
- Consider paid tier for sensitive data
- Don't extract PII unnecessarily
- Implement data retention policies

**Input Validation:**
- Sanitize email text before sending to API
- Validate schema compliance
- Check for suspicious prompts (prompt injection)

---

## Quick Start Implementation

### Step 1: Install SDK
```bash
pip install -U google-genai
```

### Step 2: Set API Key
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Step 3: Basic Usage
```python
from google import genai
import json

client = genai.Client()

schema = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string"},
                    "value": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        }
    }
}

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Extract entities from: 안녕하세요, 저는 김철수입니다. kim@example.com",
    config={"response_mime_type": "application/json", "response_schema": schema}
)

entities = json.loads(response.text)
print(entities)
```

### Step 4: Add Error Handling
- Use the retry strategy from [Error Handling](#error-handling) section
- Implement exponential backoff
- Handle common error codes

### Step 5: Add Few-Shot Examples
- Include 2-5 examples in your prompt
- Cover Korean, English, and mixed-language cases
- Follow the format from [Prompt Engineering](#prompt-engineering-for-entity-extraction)

---

## References

- [Gemini API Documentation](https://ai.google.dev)
- [Gemini API Quickstart](https://ai.google.dev/tutorials/python_quickstart)
- [Structured Output Guide](https://ai.google.dev/gemini-api/docs/structured-output)
- [Prompting Strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- [Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [LangExtract Library](https://github.com/google/langextract) - Google's official extraction library
