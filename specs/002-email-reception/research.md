# Research Findings: Email Reception and Normalization

**Branch**: 002-email-reception
**Date**: 2025-10-30
**Purpose**: Resolve technical unknowns identified in plan.md

---

## 1. Email Infrastructure Choice

### Decision: Gmail API with Webhook (Push Notifications via Cloud Pub/Sub)

**Rationale**:
1. **Real-Time Performance**: Push notifications deliver within seconds, far exceeding the 5-minute latency requirement
2. **Cloud Run Native**: Stateless HTTP webhooks align perfectly with serverless architecture (can scale to zero)
3. **Reliability**: 99.9% SLA from Google, automatic retries via Pub/Sub, fallback polling ensures no emails missed
4. **GCP Ecosystem**: All components on GCP (Cloud Run + Pub/Sub + Gmail API) with unified billing/monitoring
5. **Cost-Effective**: Gmail API free (within 1B quota), Pub/Sub free tier covers usage (~$5-15/month total)

**Implementation Approach**:
- **Primary**: Webhook push notifications (99%+ of emails processed in real-time)
- **Fallback**: Gmail API polling every 15 minutes (catches any missed notifications)
- **Watch Renewal**: Daily Cloud Scheduler job to renew Gmail watch (expires every 7 days)

**Alternatives Rejected**:
- **IMAP**: Persistent connection incompatible with Cloud Run scale-to-zero; requires always-on instance ($10-15/month); complex keep-alive logic (NOOP every 15 min); not truly real-time
- **Standalone Webhook**: Gmail warns notifications may be dropped in extreme cases; no fallback = risk of missed emails

### Implementation Steps

1. **Enable Gmail API** (5 min):
   ```bash
   gcloud services enable gmail.googleapis.com pubsub.googleapis.com
   ```

2. **OAuth2 Setup** (15 min):
   - Create OAuth 2.0 credentials in GCP Console
   - Run initial OAuth flow locally to generate `token.json`
   - Store token in GCP Secret Manager

3. **Pub/Sub Setup** (10 min):
   ```bash
   gcloud pubsub topics create gmail-watch
   gcloud pubsub topics add-iam-policy-binding gmail-watch \
     --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
     --role=roles/pubsub.publisher
   gcloud pubsub subscriptions create gmail-webhook \
     --topic=gmail-watch \
     --push-endpoint=https://collabiq-[hash].run.app/webhook \
     --ack-deadline=60 \
     --min-retry-delay=10s \
     --max-retry-delay=600s
   ```

4. **Application Code** (3-4 hours):
   - Webhook endpoint (`/webhook`) to receive Pub/Sub notifications
   - Gmail client to fetch emails via `history.list()` and `messages.get()`
   - Watch setup call: `users().watch()` pointing to Pub/Sub topic
   - Idempotency: Track processed `historyId` to handle duplicate deliveries
   - Fallback polling job (Cloud Scheduler, every 15 min)

**Configuration** (`.env`):
```bash
# Gmail API
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Pub/Sub
PUBSUB_PROJECT_ID=your-project-id
PUBSUB_TOPIC=gmail-watch
PUBSUB_SUBSCRIPTION=gmail-webhook

# Fallback
FALLBACK_SYNC_INTERVAL_MINUTES=15
```

---

## 2. Signature Detection Patterns

### Decision: Custom Pattern-Based Implementation with Comprehensive Regex

**Rationale**:
- Existing libraries (Talon, email-reply-parser) are English-focused with limited Korean support
- CollabIQ sample emails show consistent Korean patterns (드림, 감사합니다, etc.)
- Can achieve 95%+ accuracy with well-tuned regex + heuristics
- Full control over Korean/English patterns; easier to debug and maintain

### Korean Signature Patterns

**Closing Phrases**:
```python
KOREAN_SIGNATURE_REGEX = re.compile(
    r'(?:'
    r'감사(?:\s*드리며|\s*드립니다)?\.?'  # 감사합니다/감사드립니다
    r'|고맙습니다\.?'
    r'|좋은\s*하루\s*보내세요\.?'
    r')\s*'
    r'(?:\n[가-힣]{2,5}\s+(?:드림|올림|드립니다|배상)\.?)?',  # Name + 드림/올림
    re.MULTILINE | re.IGNORECASE
)
```

**Name + Title Patterns**:
```python
KOREAN_NAME_TITLE_PATTERN = re.compile(
    r'^[가-힣]{2,4}\s*'                           # Name (2-4 Korean chars)
    r'(?:'                                         # Optional title group
        r'(?:대표|이사|팀장|과장|부장|차장|상무|전무|본부장|실장)'
        r'(?:님)?'                                 # Optional 님 (honorific)
    r')?'
    r'\s*(?:드림|올림|배상)\.?$',                 # Signature marker
    re.MULTILINE
)
```

**Examples from Sample Emails**:
- `감사합니다.\n이기선 드림` (sample-001.txt)
- `감사합니다.\n김주영 드림.` (sample-002.txt)
- `감사합니다.\n이성범 이사` (sample-003.txt)

### English Signature Patterns

**Closing Phrases**:
```python
ENGLISH_CLOSINGS = [
    r'(?:sincerely|yours\s+sincerely|sincerely\s+yours)',
    r'(?:best\s+regards|kind\s+regards|warm\s+regards)',
    r'(?:best\s+wishes|thank\s+you|thanks)',
    r'(?:^best$|^regards$|^thanks$|^cheers$)',
]

ENGLISH_CLOSING_REGEX = re.compile(
    r'^\s*(' + '|'.join(ENGLISH_CLOSINGS) + r')\s*[,.]?\s*$',
    re.MULTILINE | re.IGNORECASE
)
```

### Quoted Thread Patterns

**Quote Prefix** (standard):
```python
QUOTE_PREFIX_PATTERN = re.compile(r'^>+\s*', re.MULTILINE)
```

**Quote Headers** (English):
```python
# "On [date], [person] wrote:"
GMAIL_QUOTE_HEADER = re.compile(
    r'^On\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\s+'
    r'at\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\s+'
    r'.+?<[^>]+>\s+wrote:',
    re.MULTILINE | re.IGNORECASE
)
```

**Quote Headers** (Korean):
```python
# [날짜]에 [사람]님이 작성:
KOREAN_QUOTE_HEADER_PATTERNS = [
    re.compile(
        r'^\d{4}[-./년]\s*\d{1,2}[-./월]\s*\d{1,2}일?\s+'
        r'.+?(?:님)?(?:이|가)\s+(?:작성|보낸\s+메시지):?\s*$',
        re.MULTILINE
    ),
]
```

### Disclaimer Patterns

**Confidentiality Notices**:
```python
CONFIDENTIALITY_PATTERNS = [
    re.compile(
        r'(?:CONFIDENTIAL|PROPRIETARY|PRIVILEGED)(?:\s+(?:AND|&)\s+(?:CONFIDENTIAL|PROPRIETARY|PRIVILEGED))*'
        r'[\s\S]{0,500}?'
        r'(?:intended\s+(?:solely\s+)?for|addressee|recipient)',
        re.IGNORECASE | re.MULTILINE
    ),
]
```

### Fallback Heuristics

**When standard patterns don't match**:

1. **Separator Line Detection**: Lines with 80%+ repeated chars (`-`, `_`, `=`)
2. **Contact Info Detection**: Lines containing email, phone, or URL patterns
3. **Signature Block Position**: Bottom 30% of email with 3+ disclaimer keywords
4. **Quote Density**: If 30%+ of lines start with `>`, likely quoted section

### Processing Pipeline

**Recommended order for 95%+ accuracy**:
1. Remove disclaimers (bottom of email)
2. Remove quoted threads (marked sections)
3. Remove signatures (closing + contact info)
4. Validate remaining content is not empty
5. Clean up excessive whitespace

**Confidence Scoring**:
- High (0.8-1.0): Multiple clear indicators found
- Medium (0.5-0.8): Some indicators, may need review
- Low (0.0-0.5): Weak indicators, flag for manual review

### Implementation Location

```
src/content_normalizer/
├── normalizer.py           # Main ContentNormalizer class
├── patterns/
│   ├── korean.py          # Korean signature/closing patterns
│   ├── english.py         # English signature/closing patterns
│   ├── quotes.py          # Quote detection patterns
│   ├── disclaimers.py     # Disclaimer patterns
│   └── separators.py      # Separator patterns
├── heuristics/
│   ├── signature.py       # Signature detection heuristics
│   ├── contact.py         # Contact info detection
│   └── empty.py           # Empty content detection
└── utils.py               # Helper functions
```

---

## 3. File Storage Structure

### Decision: Monthly Subdirectories with Timestamp + Message-ID Filenames

**Directory Structure**:
```
data/
├── raw/                          # Raw email files as received
│   ├── 2025/
│   │   ├── 10/                   # Month-based subdirectories
│   │   │   ├── 20251030_142156_CABc123xyz789.json
│   │   │   └── ...
│   │   └── 11/
│   └── 2026/
├── cleaned/                      # Cleaned email files after normalization
│   ├── 2025/
│   │   ├── 10/
│   │   │   ├── 20251030_142156_CABc123xyz789.json
│   │   │   └── ...
│   │   └── 11/
│   └── 2026/
├── archive/                      # Files older than retention period (90 days)
│   ├── raw/
│   └── cleaned/
├── dlq/                         # Dead Letter Queue for failed processing
└── metadata/
    └── processed_ids.json        # Track processed message IDs for deduplication
```

**Rationale**:
- **Monthly subdirectories**: Optimal for 50 emails/day (~1,500 files/month) - well within filesystem performance limits (10,000-50,000 files/dir optimal)
- **Separate raw/ and cleaned/**: Always preserve originals for debugging and reprocessing
- **Archive/**: Cost optimization - move old files to compressed storage after 90 days

### File Naming Convention

**Pattern**: `{timestamp}_{message_id}.json`

**Format**:
- **Timestamp**: `YYYYMMDD_HHMMSS` (ISO 8601 basic format, sortable)
- **Message ID**: Last 15 characters of email Message-ID header (sanitized)
- **Extension**: `.json` for structured data

**Examples**:
```
20251030_142156_CABc123xyz789.json
20251030_151203_CADe456abc012.json
```

**Filename Uniqueness**: Timestamp + Message-ID ensures uniqueness even if emails arrive in same second

### File Format (JSON Schema)

**RawEmail**:
```json
{
  "metadata": {
    "message_id": "CABc123xyz789@mail.gmail.com",
    "received_at": "2025-10-30T14:21:56+00:00",
    "fetched_at": "2025-10-30T14:25:03+00:00",
    "source": "gmail_api",
    "version": "1.0"
  },
  "headers": {
    "from": "Giseon Teddy.Lee <ks.lee@break.co.kr>",
    "to": "portfolioupdates@signite.co",
    "subject": "브레이크앤컴퍼니 x 신세계 PoC 킥오프 결과",
    "date": "2025-10-28T14:42:00+09:00"
  },
  "body": {
    "text": "안녕하세요, 안동훈 담당님,\n\n어제 신세계 유통...",
    "html": null,
    "content_type": "text/plain",
    "charset": "UTF-8"
  },
  "attachments": []
}
```

**CleanedEmail**:
```json
{
  "metadata": {
    "original_message_id": "CABc123xyz789@mail.gmail.com",
    "raw_file_path": "data/raw/2025/10/20251030_142156_CABc123xyz789.json",
    "cleaned_at": "2025-10-30T14:25:15+00:00",
    "normalizer_version": "1.0",
    "cleaning_status": "success"
  },
  "cleaned_body": {
    "text": "어제 신세계 유통 디지털 혁신팀과의 PoC 킥오프 미팅 요약...",
    "original_length": 856,
    "cleaned_length": 623,
    "reduction_percentage": 27.2
  },
  "removed_content": {
    "signature": "감사합니다.\n이기선 드림",
    "quoted_threads": [],
    "disclaimers": []
  },
  "validation": {
    "has_content": true,
    "min_length_met": true,
    "language_detected": "ko",
    "ready_for_llm": true
  }
}
```

### Python Implementation

**Pydantic Models**:
```python
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field

class RawEmailMetadata(BaseModel):
    message_id: str
    received_at: datetime
    fetched_at: datetime
    source: Literal["gmail_api", "webhook"]
    version: str = "1.0"

class RawEmail(BaseModel):
    metadata: RawEmailMetadata
    headers: EmailHeaders
    body: EmailBody
    attachments: list[Attachment] = []

class CleanedEmail(BaseModel):
    metadata: CleanedEmailMetadata
    cleaned_body: CleanedBody
    removed_content: RemovedContent
    validation: ValidationResult
```

**Storage Helper**:
```python
class EmailStorage:
    def __init__(self, base_path: Path = Path("data")):
        self.base_path = base_path
        self.raw_path = base_path / "raw"
        self.cleaned_path = base_path / "cleaned"

    def _get_monthly_path(self, timestamp: datetime, storage_type: str) -> Path:
        """Generate monthly directory path: data/raw/2025/10/"""
        base = self.raw_path if storage_type == "raw" else self.cleaned_path
        monthly_path = base / str(timestamp.year) / f"{timestamp.month:02d}"
        monthly_path.mkdir(parents=True, exist_ok=True)
        return monthly_path

    def save_raw_email(self, email: RawEmail) -> Path:
        """Save raw email to monthly directory."""
        monthly_path = self._get_monthly_path(email.metadata.received_at, "raw")
        filename = self._generate_filename(
            email.metadata.received_at,
            email.metadata.message_id
        )
        file_path = monthly_path / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(email.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

        return file_path

    @staticmethod
    def _generate_filename(received_at: datetime, message_id: str) -> str:
        """Generate filename: YYYYMMDD_HHMMSS_{message_id}.json"""
        timestamp = received_at.strftime('%Y%m%d_%H%M%S')
        msg_id_clean = re.sub(r'[^a-zA-Z0-9]', '', message_id.strip('<>').split('@')[0])[-15:]
        return f"{timestamp}_{msg_id_clean}.json"
```

### Retention and Archiving

**Policy**:
- **Active storage**: 90 days (raw + cleaned emails)
- **Archive storage**: 365 days (compressed, cold storage)
- **Permanent deletion**: After 1 year

**Archiving** (monthly cron job):
```python
class EmailArchiver:
    def archive_old_files(self) -> dict:
        """Archive files older than 90 days to compressed .tar.gz"""
        cutoff_date = datetime.now() - timedelta(days=90)

        # Compress monthly directories older than cutoff
        for month_dir in self.find_old_directories(cutoff_date):
            archive_file = self.archive_path / f"{year}/{year}{month:02d}.tar.gz"
            with tarfile.open(archive_file, 'w:gz') as tar:
                tar.add(month_dir, arcname=f"{year}{month:02d}")
            shutil.rmtree(month_dir)
```

**Automation**:
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=lambda: EmailArchiver().archive_old_files(),
    trigger='cron',
    day=1,
    hour=2,
    minute=0,
    id="archive_emails"
)
scheduler.start()
```

---

## 4. Duplicate Detection Strategy

### Decision: Message-ID Based Tracking with Lightweight JSON File

**Approach**: Maintain `data/metadata/processed_ids.json` tracking processed Message-IDs

**Implementation**:
```python
class DuplicateTracker:
    def __init__(self, metadata_path: Path = Path("data/metadata")):
        self.tracker_file = metadata_path / "processed_ids.json"
        self._processed_ids: Set[str] = self._load_tracker()

    def is_processed(self, message_id: str) -> bool:
        """O(1) lookup in set."""
        return message_id in self._processed_ids

    def mark_processed(self, message_id: str) -> None:
        """Add to set and persist to file."""
        self._processed_ids.add(message_id)
        self._save_tracker()

# Usage in EmailReceiver
tracker = DuplicateTracker()

if tracker.is_processed(message_id):
    logger.info(f"Skipping duplicate: {message_id}")
    return None  # Skip processing

# Process email...
tracker.mark_processed(message_id)
```

**Performance**:
- **Memory**: 50 emails/day × 365 days = 18,250 IDs/year = ~912 KB in-memory (negligible)
- **File size**: ~1.5 MB/year (acceptable)
- **Lookup**: O(1) average case, <1 microsecond per lookup

**Scalability**:
- File-based approach works up to 100,000 entries (~10 MB)
- If volume exceeds 1,000 emails/day, migrate to SQLite with indexed table

**Edge Cases**:
- **Duplicate Message-ID**: Skip reprocessing (log + return None)
- **Missing Message-ID**: Generate synthetic ID using content hash
- **Reprocessing after logic improvements**: Track `{message_id}:{version}` to enable selective reprocessing

---

## Implementation Priority

### Phase 0 Complete ✅

All unknowns resolved:
1. ✅ Email Infrastructure: Gmail API + Webhook
2. ✅ Signature Patterns: Custom regex + heuristics
3. ✅ File Storage: Monthly dirs + timestamp_messageid.json
4. ✅ Duplicate Detection: Message-ID tracking in JSON file

### Ready for Phase 1: Design & Contracts

Next steps:
1. Generate `data-model.md` (RawEmail, CleanedEmail Pydantic models)
2. Generate `contracts/email_receiver.yaml` (EmailReceiver interface)
3. Generate `contracts/content_normalizer.yaml` (ContentNormalizer interface)
4. Generate `quickstart.md` (setup and usage instructions)
5. Update agent context with new dependencies

---

**Research Complete**: 2025-10-30
**All Technical Unknowns Resolved**: ✅
**Constitution Check Status**: ✅ PASS - Proceed to Phase 1
