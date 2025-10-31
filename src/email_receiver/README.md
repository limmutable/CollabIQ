# Email Receiver Component

**Purpose**: Retrieve emails from Gmail API and save them as structured RawEmail objects.

## Overview

The Email Receiver component implements email retrieval from Gmail using OAuth2 authentication. It handles:

- Gmail API authentication and connection
- Email batch retrieval with configurable batch sizes
- Duplicate detection using message IDs
- Rate limit handling with exponential backoff
- Structured storage of raw emails in monthly directories

## Architecture

```
GmailReceiver
    ↓
Gmail API (OAuth2)
    ↓
RawEmail models
    ↓
data/raw/YYYY/MM/YYYYMMDD_HHMMSS_{message_id}.json
```

## Core Components

### GmailReceiver

Main class for Gmail API interaction.

**Key Methods**:
- `connect()`: Establish Gmail API connection with OAuth2
- `fetch_emails(max_results: int)`: Retrieve emails from inbox
- `save_raw_email(raw_email: RawEmail)`: Save email to file storage

**Features**:
- Automatic OAuth2 token refresh
- Batch processing support (1-500 emails)
- Duplicate detection via DuplicateTracker
- Rate limit handling (3 retries with exponential backoff)

### DuplicateTracker

Tracks processed message IDs to prevent reprocessing.

**Key Methods**:
- `is_duplicate(message_id: str) -> bool`: Check if message already processed
- `mark_processed(message_id: str)`: Mark message as processed
- `save()`: Persist state to disk
- `load()`: Load state from disk

**Storage**: `data/duplicate_tracker.json` (JSON format)

## Usage

### Basic Usage

```python
from src.email_receiver.gmail_receiver import GmailReceiver
from src.email_receiver.duplicate_tracker import DuplicateTracker
from src.config.settings import get_settings

# Initialize components
settings = get_settings()
settings.create_directories()

tracker = DuplicateTracker()
receiver = GmailReceiver(duplicate_tracker=tracker)

# Connect to Gmail
receiver.connect()

# Fetch emails
raw_emails = receiver.fetch_emails(max_results=50)
print(f"Fetched {len(raw_emails)} new emails")

# Save to disk
for email in raw_emails:
    file_path = receiver.save_raw_email(email)
    print(f"Saved: {file_path}")

# Persist duplicate tracker state
tracker.save()
```

### With Configuration

```python
from src.config.settings import get_settings
from src.config.logging_config import setup_logging

# Load settings from .env
settings = get_settings()

# Setup logging
setup_logging(
    level=settings.log_level,
    log_dir=settings.log_dir,
)

# Use settings in receiver
receiver = GmailReceiver(
    credentials_path=settings.gmail_credentials_path,
    token_path=settings.gmail_token_path,
)
```

## Data Models

### RawEmail

Represents an unprocessed email retrieved from Gmail.

```python
from src.models.raw_email import RawEmail, EmailMetadata

email = RawEmail(
    metadata=EmailMetadata(
        message_id="<abc123@gmail.com>",
        sender="sender@example.com",
        subject="Portfolio Update",
        received_at=datetime(2025, 10, 30, 14, 30, 0),
    ),
    body="Email content here...",
)
```

**Fields**:
- `metadata`: EmailMetadata with message ID, sender, subject, timestamp
- `body`: Raw email body text (signatures, quotes, disclaimers included)

## File Storage Structure

```
data/raw/
├── 2025/
│   ├── 10/
│   │   ├── 20251030_143000_abc123_at_gmail.com.json
│   │   ├── 20251030_143015_def456_at_gmail.com.json
│   │   └── 20251030_143030_ghi789_at_gmail.com.json
│   └── 11/
│       └── 20251101_090000_jkl012_at_gmail.com.json
└── duplicate_tracker.json
```

**Filename Format**: `YYYYMMDD_HHMMSS_{sanitized_message_id}.json`

## Error Handling

### Connection Failures

Handled by exponential backoff with 3 retries (FR-010):

```python
try:
    receiver.connect()
except Exception as e:
    logger.error(f"Connection failed after 3 retries: {e}")
```

### Rate Limiting

Automatically retries with exponential backoff:
- Retry 1: Wait 1 second
- Retry 2: Wait 2 seconds
- Retry 3: Wait 4 seconds

### Duplicate Emails

Silently skipped using message ID tracking (FR-011):

```python
if tracker.is_duplicate(message_id):
    logger.debug(f"Skipping duplicate: {message_id}")
    continue
```

## Configuration

### Environment Variables (.env)

```env
# Gmail API
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_BATCH_SIZE=50

# Data Storage
DATA_DIR=data
RAW_EMAIL_DIR=data/raw

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Rate Limiting
RATE_LIMIT_MAX_RETRIES=3
RATE_LIMIT_BASE_DELAY=1.0
```

### Gmail API Setup

1. **Enable Gmail API** in Google Cloud Console
2. **Create OAuth2 credentials** (Desktop application)
3. **Download credentials** as `credentials.json`
4. **Run authentication** flow on first use (creates `token.json`)

See [quickstart.md](../../specs/002-email-reception/quickstart.md) for detailed setup instructions.

## Testing

### Unit Tests

```bash
# Test Gmail receiver
uv run pytest tests/unit/test_gmail_receiver.py -v

# Test duplicate tracker
uv run pytest tests/unit/test_duplicate_tracker.py -v

# Test all email receiver components
uv run pytest tests/unit/test_gmail_receiver.py tests/unit/test_duplicate_tracker.py -v
```

### Integration Tests

```bash
# Test with real Gmail API (requires credentials)
uv run pytest tests/integration/test_gmail_integration.py -v
```

## Logging

All email processing activities are logged (FR-009):

```
2025-10-30 14:30:00 | INFO     | email_receiver.gmail_receiver:123 | Connected to Gmail API
2025-10-30 14:30:05 | INFO     | email_receiver.gmail_receiver:145 | Fetched 15 emails
2025-10-30 14:30:06 | DEBUG    | email_receiver.duplicate_tracker:67 | Skipping duplicate: <abc@gmail.com>
2025-10-30 14:30:07 | INFO     | email_receiver.gmail_receiver:178 | Saved raw email: data/raw/2025/10/20251030_143007_def_at_gmail.com.json
```

## Performance

- **Target**: 50 emails within 10 minutes (SC-006)
- **Average**: ~12 seconds per email (includes fetch + save + duplicate check)
- **Batch size**: 50 emails per API call (configurable)

## Related Components

- **[Content Normalizer](../content_normalizer/README.md)**: Cleans raw emails by removing noise
- **[Models](../models/)**: Data models for RawEmail and CleanedEmail
- **[Configuration](../config/)**: Settings and logging configuration

## Troubleshooting

### "credentials.json not found"

Ensure Gmail API credentials are downloaded to project root:
```bash
ls -la credentials.json
```

### "Token expired or invalid"

Delete token cache and re-authenticate:
```bash
rm token.json
python -c "from src.email_receiver.gmail_receiver import GmailReceiver; GmailReceiver().connect()"
```

### "Rate limit exceeded"

Reduce batch size in settings:
```env
GMAIL_BATCH_SIZE=20
```

### "Duplicate tracker corrupted"

Reset duplicate tracker:
```bash
rm data/duplicate_tracker.json
```

## References

- **Specification**: [specs/002-email-reception/spec.md](../../specs/002-email-reception/spec.md)
- **Technical Plan**: [specs/002-email-reception/plan.md](../../specs/002-email-reception/plan.md)
- **Quickstart Guide**: [specs/002-email-reception/quickstart.md](../../specs/002-email-reception/quickstart.md)
- **Gmail API Docs**: https://developers.google.com/gmail/api
