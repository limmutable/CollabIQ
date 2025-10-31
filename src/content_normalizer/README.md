# Content Normalizer Component

**Purpose**: Clean raw emails by removing signatures, quoted threads, and disclaimers.

## Overview

The Content Normalizer component implements a three-stage email cleaning pipeline that:

- Removes legal disclaimers and confidentiality notices
- Removes quoted thread content (reply chains)
- Removes email signatures
- Tracks all removed content for audit purposes
- Handles empty emails gracefully

The cleaned emails are ready for downstream LLM processing.

## Architecture

```
RawEmail
    ↓
ContentNormalizer (3-stage pipeline)
    ↓
Stage 1: Remove disclaimers
Stage 2: Remove quoted threads
Stage 3: Remove signatures
    ↓
CleanedEmail
    ↓
data/cleaned/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json
```

## Core Components

### ContentNormalizer

Main class for email content cleaning.

**Key Methods**:
- `clean(body: str) -> CleaningResult`: Execute three-stage cleaning pipeline
- `process_raw_email(raw_email: RawEmail) -> CleanedEmail`: Convert RawEmail → CleanedEmail
- `save_cleaned_email(cleaned_email: CleanedEmail) -> Path`: Save to file storage

**Three-Stage Pipeline** (executed in order):
1. **Disclaimers**: Remove legal/confidentiality notices
2. **Quoted Threads**: Remove reply chains and forwarded content
3. **Signatures**: Remove email signatures

### Pattern Library

Comprehensive pattern matching for noise detection.

**Signature Patterns** (FR-004):
- Best regards / Sincerely / Thanks
- Sent from my iPhone / Sent from Gmail
- Phone numbers and email addresses
- LinkedIn profile URLs
- Separator-based heuristics

**Quote Patterns** (FR-005):
- Gmail reply headers: "On [date] wrote:"
- Outlook reply headers: "From:/Sent:/To:"
- Korean date formats: "2025년 10월 30일"
- Angle bracket quotes: "> Previous message"
- Nested quotes: "> > > Earlier message"

**Disclaimer Patterns** (FR-006):
- CONFIDENTIALITY NOTICE
- LEGAL DISCLAIMER
- "intended only for"
- Privileged communication
- Unauthorized use warnings

## Usage

### Basic Usage

```python
from src.content_normalizer.normalizer import ContentNormalizer
from src.models.raw_email import RawEmail

# Initialize normalizer
normalizer = ContentNormalizer()

# Clean email body
email_body = """
Project update for Q4.

Best regards,
Alice Smith
Senior PM

CONFIDENTIALITY NOTICE: This email is confidential.
"""

result = normalizer.clean(email_body)
print(result.cleaned_body)  # "Project update for Q4."
print(result.removed_content.signature_removed)  # True
print(result.removed_content.disclaimer_removed)  # True
```

### Full Pipeline

```python
from src.content_normalizer.normalizer import ContentNormalizer
from src.email_receiver.gmail_receiver import GmailReceiver

# Fetch raw emails
receiver = GmailReceiver()
receiver.connect()
raw_emails = receiver.fetch_emails(max_results=10)

# Clean and save
normalizer = ContentNormalizer()
for raw_email in raw_emails:
    # Process raw email → cleaned email
    cleaned_email = normalizer.process_raw_email(raw_email)

    # Save to disk
    file_path = normalizer.save_cleaned_email(cleaned_email)
    print(f"Cleaned: {file_path}")

    # Check if email became empty
    if cleaned_email.is_empty:
        print(f"Warning: Email {cleaned_email.original_message_id} is empty after cleaning")
```

### Custom Cleaning Options

```python
# Disable specific cleaning stages
result = normalizer.clean(
    body=email_body,
    remove_signatures=True,
    remove_quotes=False,  # Keep quoted content
    remove_disclaimers=True,
)
```

## Data Models

### CleaningResult

Result of the cleaning pipeline.

```python
from src.models.cleaned_email import CleaningResult, RemovedContent

result = CleaningResult(
    cleaned_body="Just the collaboration content",
    removed_content=RemovedContent(
        signature_removed=True,
        quoted_thread_removed=True,
        disclaimer_removed=False,
    ),
)
```

### CleanedEmail

Final cleaned email with metadata.

```python
from src.models.cleaned_email import CleanedEmail, CleaningStatus

cleaned = CleanedEmail(
    original_message_id="<abc123@gmail.com>",
    cleaned_body="Project update content",
    removed_content=RemovedContent(...),
    processed_at=datetime.utcnow(),
    status=CleaningStatus.SUCCESS,
    is_empty=False,
)
```

**CleaningStatus Values**:
- `SUCCESS`: Email cleaned successfully
- `EMPTY`: Email became empty after cleaning (FR-012)
- `FAILED`: Cleaning failed with error
- `SKIPPED`: Email skipped (duplicate or invalid)

## File Storage Structure

```
data/cleaned/
├── 2025/
│   ├── 10/
│   │   ├── 20251030_143000_abc123_at_gmail.com.json
│   │   ├── 20251030_143015_def456_at_gmail.com.json (empty: true)
│   │   └── 20251030_143030_ghi789_at_gmail.com.json
│   └── 11/
│       └── 20251101_090000_jkl012_at_gmail.com.json
```

**Filename Format**: `YYYYMMDD_HHMMSS_{sanitized_message_id}.json`

## Pattern Detection Examples

### Signature Detection

```python
from src.content_normalizer.patterns import detect_signature

email = """
Great work on the project!

Best regards,
Alice Smith
"""

position = detect_signature(email)
# Returns: 26 (position of "Best regards")
```

### Quote Detection

```python
from src.content_normalizer.patterns import detect_quoted_thread

email = """
Thanks for the update.

On Oct 30, 2025, Bob wrote:
> Here's the original message
"""

result = detect_quoted_thread(email)
# Returns: (23, "gmail_reply_header")
```

### Disclaimer Detection

```python
from src.content_normalizer.patterns import detect_disclaimer

email = """
See the attached report.

CONFIDENTIALITY NOTICE: This email is confidential.
"""

result = detect_disclaimer(email)
# Returns: (23, "confidentiality_notice")
```

## Accuracy Results

### Signature Removal (FR-004, SC-002)
- **Target**: 95% accuracy
- **Achieved**: 100% accuracy on 20-email test dataset
- **Test dataset**: [tests/unit/test_signature_accuracy.py](../../tests/unit/test_signature_accuracy.py)

### Quote Removal (FR-005, SC-003)
- **Target**: 95% accuracy
- **Achieved**: 100% accuracy on 21-email test dataset
- **Test dataset**: [tests/unit/test_quoted_thread_accuracy.py](../../tests/unit/test_quoted_thread_accuracy.py)

### Coverage
- Gmail reply headers: 100%
- Outlook reply headers: 100%
- Korean date formats: 100%
- Angle bracket quotes: 100%
- Nested quotes (3+ levels): 100%
- Standard signatures: 100%
- Phone/email signatures: 100%
- Mixed language content: 100%

## Error Handling

### Empty Content (FR-012)

Emails that become empty after cleaning are flagged:

```python
cleaned = normalizer.process_raw_email(raw_email)

if cleaned.is_empty:
    logger.warning(f"Email {cleaned.original_message_id} resulted in empty content")
    # Email is still saved with is_empty=True for review
```

### Invalid Input

```python
# Empty or None body
result = normalizer.clean("")
# Returns: CleaningResult(cleaned_body="", removed_content=RemovedContent(...))

result = normalizer.clean(None)
# Returns: CleaningResult(cleaned_body="", removed_content=RemovedContent(...))
```

## Configuration

### Environment Variables (.env)

```env
# Data Storage
CLEANED_EMAIL_DIR=data/cleaned

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

## Testing

### Unit Tests

```bash
# Test signature detection
uv run pytest tests/unit/test_signature_detection.py -v

# Test quote detection
uv run pytest tests/unit/test_quoted_thread_detection.py -v

# Test disclaimer detection
uv run pytest tests/unit/test_disclaimer_detection.py -v

# Test accuracy
uv run pytest tests/unit/test_signature_accuracy.py -v
uv run pytest tests/unit/test_quoted_thread_accuracy.py -v
```

### Integration Tests

```bash
# Test three-stage pipeline
uv run pytest tests/unit/test_content_normalizer_pipeline.py -v

# Test all normalizer components
uv run pytest tests/unit/test_content_normalizer*.py -v
```

## Logging

All cleaning operations are logged (FR-009):

```
2025-10-30 14:30:00 | INFO     | content_normalizer.normalizer:87 | Disclaimer removed using pattern 'confidentiality_notice'
2025-10-30 14:30:00 | INFO     | content_normalizer.normalizer:134 | Quoted thread removed using pattern 'gmail_reply_header'
2025-10-30 14:30:00 | INFO     | content_normalizer.normalizer:164 | Signature removed using pattern 'best_regards'
2025-10-30 14:30:00 | INFO     | content_normalizer.normalizer:51 | Email cleaned: 450 → 42 chars
2025-10-30 14:30:01 | WARNING  | content_normalizer.normalizer:223 | Email <abc@gmail.com> resulted in empty content
```

## Performance

- **Average**: ~12 seconds per email (combined fetch + clean + save)
- **Cleaning only**: <100ms per email
- **Target**: 50 emails within 10 minutes (SC-006) ✓

## Pipeline Execution Order

The three-stage pipeline MUST execute in this order (per contracts):

1. **Disclaimers first**: Remove legal notices at end of email
2. **Quotes second**: Remove reply chains (may contain signatures)
3. **Signatures last**: Remove sender's signature block

**Rationale**: Quoted content often contains signatures from previous senders. Removing quotes first would miss these signatures in the removal tracking.

## Edge Cases Handled

- **Empty content after cleaning**: Flagged with `is_empty=True` (FR-012)
- **Nested quotes (3+ levels)**: Detected via nested quote pattern
- **Mixed language content**: Korean + English signatures/quotes
- **No noise content**: Returns original body unchanged
- **Multiple signatures**: All detected and removed
- **Signature-like content**: Preserved if in middle of email

## Related Components

- **[Email Receiver](../email_receiver/README.md)**: Fetches raw emails from Gmail
- **[Models](../models/)**: Data models for RawEmail and CleanedEmail
- **[Configuration](../config/)**: Settings and logging configuration

## Troubleshooting

### Pattern not detected

Check pattern library for similar patterns:
```python
from src.content_normalizer import patterns
print(patterns.SIGNATURE_PATTERNS)
```

### False positives

Signatures detected in email body content - check pattern specificity in [patterns.py](patterns.py).

### Poor accuracy

Run accuracy tests to identify specific failing cases:
```bash
uv run pytest tests/unit/test_signature_accuracy.py -v --tb=short
```

## References

- **Specification**: [specs/002-email-reception/spec.md](../../specs/002-email-reception/spec.md)
- **Technical Plan**: [specs/002-email-reception/plan.md](../../specs/002-email-reception/plan.md)
- **Contracts**: [specs/002-email-reception/contracts/content_normalizer.yaml](../../specs/002-email-reception/contracts/content_normalizer.yaml)
- **Data Model**: [specs/002-email-reception/data-model.md](../../specs/002-email-reception/data-model.md)
