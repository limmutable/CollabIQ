# API Contracts

This document consolidates all API contracts for CollabIQ components. Each contract defines the interface, methods, inputs/outputs, error conditions, and performance expectations.

**Contract Version**: 1.0.0
**Last Updated**: 2025-10-28

---

## Table of Contents

1. [LLMProvider Interface](#llmprovider-interface)
2. [EmailReceiver Component](#emailreceiver-component)
3. [NotionIntegrator Component](#notionintegrator-component)

---

## LLMProvider Interface

**Type**: Abstract Interface
**Purpose**: Enable swapping between different LLM providers (Gemini, GPT, Claude) without rewriting system logic.

### Methods

#### `extract_entities(email_text: str, company_context: ClassificationContext) -> (ExtractedEntities, list[MatchedCompany])`

Extracts key entities from email text and matches to existing companies.

**Inputs**:
- `email_text` (str, required): Normalized email body (Korean/English, signatures removed)
  - Example: `"어제 신세계인터와 본봄 파일럿 킥오프, 11월 1주 PoC 시작 예정"`
- `company_context` (ClassificationContext, optional): Portfolio companies and SSG affiliates for fuzzy matching

**Outputs**:
- `entities` (ExtractedEntities): Extracted entities with confidence scores
  ```python
  ExtractedEntities(
      person_in_charge="김철수",      # 담당자
      startup_name="본봄",            # 스타트업명
      partner_org="신세계인터내셔널",  # 협업기관
      details="11월 1주 PoC 시작 예정...",  # 협업내용
      date=datetime(2025, 10, 27),   # 날짜
      confidence={
          "person": 0.95,
          "startup": 0.92,
          "partner": 0.88,
          "date": 0.85
      }
  )
  ```
- `matched_companies` (list[MatchedCompany]): Companies matched to Notion database entries
  ```python
  [
      MatchedCompany(
          original_name="신세계인터",
          matched_name="신세계인터내셔널",
          notion_page_id="abc123def456",
          confidence=0.87
      ),
      MatchedCompany(
          original_name="본봄",
          matched_name="본봄",
          notion_page_id="xyz789ghi012",
          confidence=1.0
      )
  ]
  ```

**Errors**:
- `LLMAPIError`: LLM API call failed after retries
- `LLMRateLimitError`: Rate limit exceeded
- `LLMTimeoutError`: Request timed out
- `LLMParsingError`: Failed to parse LLM response

**Performance**:
- Expected latency: 1-3 seconds
- Retry strategy: Exponential backoff (1s, 2s, 4s, 8s, max 3 retries)

#### `classify(entities: ExtractedEntities, context: ClassificationContext) -> Classification`

Classifies collaboration type and intensity.

**Inputs**:
- `entities` (ExtractedEntities, required): Extracted entities from `extract_entities()`
- `context` (ClassificationContext, required): Portfolio status and SSG affiliation lookup results

**Outputs**:
- `classification` (Classification):
  ```python
  Classification(
      collab_type="[A]",    # [A] PortCo×SSG, [B] Non-PortCo×SSG, [C] PortCo×PortCo, [D] Other
      intensity="협력",      # 이해, 협력, 투자, 인수
      confidence={
          "type": 0.91,
          "intensity": 0.89
      }
  )
  ```

**Classification Rules**:
- **Type**:
  - `[A]`: startup_name in portfolio_companies AND partner_org in ssg_affiliates
  - `[B]`: startup_name NOT in portfolio_companies AND partner_org in ssg_affiliates
  - `[C]`: startup_name in portfolio_companies AND partner_org in portfolio_companies
  - `[D]`: All other combinations
- **Intensity**:
  - `이해` (Understand): Keywords - meeting, discussion, introduction, 미팅, 소개, 논의
  - `협력` (Cooperate): Keywords - pilot, PoC, partnership, collaboration, 파일럿, 협업, 협력
  - `투자` (Invest): Keywords - investment, funding, financing, 투자, 펀딩, 유치
  - `인수` (Acquire): Keywords - acquisition, M&A, takeover, 인수, 합병

**Errors**:
- `LLMAPIError`: LLM API call failed after retries

#### `summarize(text: str, max_sentences: int = 5) -> str`

Generates 3-5 sentence summary preserving key details.

**Inputs**:
- `text` (str, required): Full collaboration details text
- `max_sentences` (int, optional, default=5): Maximum sentences in summary (3-5)

**Outputs**:
- `summary` (str): Summary string (Korean or English matching input)
  - Example: `"본봄과 신세계인터내셔널이 파일럿 킥오프를 진행하고 11월 1주에 PoC를 시작할 예정입니다. 협력은 제품 테스트와 시장 검증에 초점을 맞추고 있습니다."`

**Errors**:
- `LLMAPIError`: LLM API call failed after retries

### Implementations

| Implementation | Status | Phase | Description |
|----------------|--------|-------|-------------|
| **GeminiAdapter** | Planned | Phase 1a | Gemini API implementation (extraction + matching + classification + summarization in one call) |
| **GPTAdapter** | Future | TBD | OpenAI GPT-4 implementation (if Gemini accuracy insufficient) |
| **ClaudeAdapter** | Future | TBD | Anthropic Claude implementation (if Gemini accuracy insufficient) |
| **MultiLLMOrchestrator** | Future | TBD | Consensus-based multi-LLM voting for higher accuracy |

### Example Usage

```python
from src.llm_provider import LLMProvider
from src.llm_adapters import GeminiAdapter
from src.llm_provider.types import ClassificationContext

# Initialize provider
llm: LLMProvider = GeminiAdapter(api_key=settings.gemini_api_key)

# Prepare context
context = ClassificationContext(
    portfolio_companies=["본봄", "테이블매니저"],
    ssg_affiliates=["신세계인터내셔널", "신세계푸드"]
)

# Extract entities
entities, matched_companies = llm.extract_entities(
    email_text="어제 신세계인터와 본봄 파일럿 킥오프...",
    company_context=context
)

# Classify collaboration
classification = llm.classify(entities, context)

# Generate summary
summary = llm.summarize(entities.details, max_sentences=5)

print(f"Startup: {entities.startup_name}")
print(f"Partner: {entities.partner_org}")
print(f"Type: {classification.collab_type}")
print(f"Intensity: {classification.intensity}")
print(f"Summary: {summary}")
```

### Swapping Providers

```python
# Swapping from Gemini to GPT is trivial:
# llm: LLMProvider = GeminiAdapter(api_key=settings.gemini_api_key)
llm: LLMProvider = GPTAdapter(api_key=settings.openai_api_key)
# All downstream code remains unchanged!
```

**Swap time**: ~30 minutes to implement new adapter + change configuration

---

## EmailReceiver Component

**Type**: Component
**Purpose**: Ingest emails from `radar@signite.co` inbox via Gmail API, IMAP, or webhook.

### Methods

#### `fetch_emails(since: datetime, limit: Optional[int] = None) -> list[RawEmail]`

Fetches new emails since given timestamp.

**Inputs**:
- `since` (datetime, required): Fetch emails received after this timestamp
  - Example: `datetime(2025, 10, 27, 0, 0, 0)`
- `limit` (Optional[int], optional): Maximum number of emails to fetch (null = no limit)

**Outputs**:
- `emails` (list[RawEmail]): List of raw email objects
  ```python
  [
      RawEmail(
          message_id="CABc123xyz789",
          subject="본봄 파일럿 킥오프",
          body="어제 신세계인터와 본봄 파일럿 킥오프...",
          sender="kim@signite.co",
          recipient="radar@signite.co",
          received_at=datetime(2025, 10, 27, 14, 30, 0),
          attachments=[]
      )
  ]
  ```

**Errors**:
- `EmailAuthError`: Authentication failed (invalid credentials)
- `EmailConnectionError`: Failed to connect to email server
- `EmailRateLimitError`: Rate limit exceeded (Gmail API)

**Performance**:
- Expected latency: 1-5 seconds for 10 emails
- Retry strategy: Exponential backoff (2s, 4s, 8s, max 3 retries)

### Implementations

| Implementation | Pros | Cons | Status |
|----------------|------|------|--------|
| **GmailAPIReceiver** | Official API, rich filtering, reliable uptime | OAuth setup complexity, quota limits (250 req/day free tier) | Option |
| **IMAPReceiver** | Simple username/password auth, no API quotas, works with any provider | Connection drops common, requires manual reconnection logic | Option |
| **WebhookReceiver** | Push-based (no polling), reliable delivery with retries, scales easily | Requires domain/subdomain setup, external service dependency | Option |

**Note**: Selected implementation depends on feasibility study findings (Task T008).

### Example Usage

```python
from src.email_receiver import EmailReceiver, GmailAPIReceiver
from datetime import datetime, timedelta

# Initialize receiver
receiver: EmailReceiver = GmailAPIReceiver(credentials_path="credentials.json")

# Fetch emails from last 24 hours
since = datetime.now() - timedelta(days=1)
emails = receiver.fetch_emails(since=since, limit=50)

for email in emails:
    print(f"From: {email.sender}")
    print(f"Subject: {email.subject}")
    print(f"Body: {email.body[:100]}...")
```

---

## NotionIntegrator Component

**Type**: Component
**Purpose**: Handle all interactions with Notion databases (fetching company lists, creating collaboration entries, managing relations).

### Methods

#### `fetch_company_lists() -> ClassificationContext`

Fetches existing company names from 스타트업 and 계열사 databases.

**Inputs**: None

**Outputs**:
- `companies` (ClassificationContext):
  ```python
  ClassificationContext(
      portfolio_companies=["본봄", "테이블매니저", "어라운드"],
      ssg_affiliates=["신세계인터내셔널", "신세계푸드", "이마트"]
  )
  ```

**Errors**:
- `NotionAuthError`: Invalid API token
- `NotionRateLimitError`: Rate limit exceeded (3 req/s)
- `NotionAPIError`: API request failed

**Performance**:
- Expected latency: 1-2 seconds
- Caching strategy: Cache for 1 hour, refresh on expiry
- Rate limit: 3 requests/second

#### `create_entry(entry: NotionEntry) -> (str, str)`

Creates new entry in "레이더 활동" database.

**Inputs**:
- `entry` (NotionEntry, required): Entry data with all required fields
  ```python
  NotionEntry(
      person_in_charge="김철수",
      startup_name="본봄",
      startup_page_id="abc123",
      partner_org="신세계인터내셔널",
      partner_page_id="def456",
      collab_subject="본봄-신세계인터내셔널",
      details="11월 1주 PoC 시작 예정...",
      collab_type="[A]",
      intensity="협력",
      date=datetime(2025, 10, 27),
      summary="본봄과 신세계인터내셔널이 파일럿 킥오프..."
  )
  ```

**Outputs**:
- `page_id` (str): Notion page ID of created entry
  - Example: `"ghi789jkl012"`
- `url` (str): Direct URL to created Notion page
  - Example: `"https://notion.so/ghi789jkl012"`

**Errors**:
- `NotionAuthError`: Invalid API token
- `NotionRateLimitError`: Rate limit exceeded
- `NotionValidationError`: Invalid field values
- `NotionRelationError`: Failed to create relation link

**Performance**:
- Expected latency: 1-3 seconds
- Retry strategy: Exponential backoff (5s, 10s, 20s, max 5 retries)

#### `find_company_page(company_name: str, database_id: str) -> (Optional[str], Optional[str], float)`

Finds Notion page ID for a company name (fuzzy matching).

**Inputs**:
- `company_name` (str, required): Company name to search for
  - Example: `"신세계인터"`
- `database_id` (str, required): Notion database ID (스타트업 or 계열사)

**Outputs**:
- `page_id` (Optional[str]): Notion page ID if found, None if no match
  - Example: `"abc123def456"`
- `matched_name` (Optional[str]): Actual company name from Notion database
  - Example: `"신세계인터내셔널"`
- `confidence` (float): Match confidence score (0.0-1.0)
  - Example: `0.87`

**Errors**:
- `NotionAPIError`: API request failed

**Performance**:
- Expected latency: 1-2 seconds
- Caching strategy: Cache company list for fuzzy matching (refresh hourly)

### Example Usage

```python
from src.notion_integrator import NotionIntegrator
from src.notion_integrator.types import NotionEntry
from datetime import datetime

# Initialize integrator
integrator = NotionIntegrator(api_key=settings.notion_api_key)

# Fetch company lists for LLM context
context = integrator.fetch_company_lists()
print(f"Portfolio companies: {context.portfolio_companies}")

# Create new collaboration entry
entry = NotionEntry(
    person_in_charge="김철수",
    startup_name="본봄",
    startup_page_id="abc123",
    partner_org="신세계인터내셔널",
    partner_page_id="def456",
    collab_subject="본봄-신세계인터내셔널",
    details="11월 1주 PoC 시작 예정...",
    collab_type="[A]",
    intensity="협력",
    date=datetime(2025, 10, 27),
    summary="본봄과 신세계인터내셔널이 파일럿..."
)

page_id, url = integrator.create_entry(entry)
print(f"Created: {url}")
```

### Rate Limit Handling

**Notion API Limits**: 3 requests/second

**Strategy 1**: Local queue with rate limiting
- Queue requests locally
- Process at max 3 req/s
- Blocks until rate limit window resets

**Strategy 2**: Exponential backoff on 429 errors
- Catch `NotionRateLimitError`
- Wait and retry: 5s, 10s, 20s
- Move to Dead Letter Queue after max retries

**Notes**:
- Company list caching reduces API calls from 50 emails × 2 fetches = 100 req/day to 24 req/day (hourly refresh)
- Rate limit (3 req/s) = 259,200 req/day >> 50 emails × 3 operations = 150 req/day
- Relation links require page IDs from 스타트업/계열사 databases
- Auto-generate 협력주체 field as: `{startup_name}-{partner_org}`

---

## Contract Files

For the full YAML specification of each contract, see:
- [specs/001-feasibility-architecture/contracts/llm_provider.yaml](../specs/001-feasibility-architecture/contracts/llm_provider.yaml)
- [specs/001-feasibility-architecture/contracts/email_receiver.yaml](../specs/001-feasibility-architecture/contracts/email_receiver.yaml)
- [specs/001-feasibility-architecture/contracts/notion_integrator.yaml](../specs/001-feasibility-architecture/contracts/notion_integrator.yaml)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-28
**Next Review**: After Phase 1a-1c implementation
