# System Architecture: CollabIQ

**Status**: ✅ COMPLETE - Foundation architecture defined
**Version**: 1.0.0
**Date**: 2025-10-28
**Branch**: 001-feasibility-architecture

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [LLM Provider Abstraction Layer](#llm-provider-abstraction-layer)
5. [Error Handling & Retry Strategy](#error-handling--retry-strategy)
6. [Edge Case Mitigation](#edge-case-mitigation)
7. [Deployment Architecture](#deployment-architecture)
8. [Scalability Design](#scalability-design)

---

## Executive Summary

CollabIQ is an email-based collaboration tracking system that extracts entities from Korean/English emails, creates Notion database entries, classifies collaborations, and generates reports.

**Key Architecture Decisions**:
- **Language**: Python 3.12 (excellent LLM/NLP ecosystem)
- **Primary LLM**: Gemini API with abstraction layer for swapping
- **Data Store**: Notion databases (레이더 활동, 스타트업, 계열사)
- **Deployment**: Google Cloud Platform (Cloud Run recommended)
- **Architecture Pattern**: Single-service monolith with component separation

---

## Component Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CollabIQ System                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  EmailReceiver   │  ← Ingest emails from portfolioupdates@signite.co
└────────┬─────────┘
         │ Raw email text
         ▼
┌──────────────────┐
│ ContentNormalizer│  ← Strip signatures, quoted threads, disclaimers
└────────┬─────────┘
         │ Cleaned email text
         ▼
┌──────────────────┐
│NotionIntegrator  │  ← Fetch existing company lists (스타트업, 협업기관)
└────────┬─────────┘
         │ Company lists for LLM context
         ▼
┌────────────────────────────────────────────────────────┐
│                  LLMProvider                            │
│              (Abstraction Layer)                        │
│                                                          │
│  ┌─────────────────────────────────────────────┐      │
│  │         GeminiAdapter                        │      │
│  │  (Extraction + Matching + Classification     │      │
│  │   + Summarization in one call)              │      │
│  └─────────────────────────────────────────────┘      │
│                                                          │
│  Future: GPTAdapter, ClaudeAdapter, MultiLLMOrchestrator│
└────────────────────┬───────────────────────────────────┘
                     │ ExtractedEntities + MatchedCompanies
                     │ + Classification + Summary
                     ▼
┌──────────────────┐
│NotionIntegrator  │  ← Create "레이더 활동" entry with matched relations
└────────┬─────────┘
         │
         ├─ High confidence → Entry created ✅
         │
         └─ Low confidence (<0.85) ──┐
                                      ▼
                            ┌──────────────────┐
                            │VerificationQueue │ ← Manual review for edge cases
                            └──────────────────┘

                            ┌──────────────────┐
                            │ ReportGenerator  │ ← Periodic analytics & insights
                            └──────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Phase Implemented |
|-----------|---------------|-------------------|
| **EmailReceiver** | Ingest emails from portfolioupdates@signite.co via Gmail API/IMAP/webhook | Phase 1a (branch 002) |
| **ContentNormalizer** | Remove signatures, quoted threads, disclaimers from email body | Phase 1a (branch 002) |
| **LLMProvider** | Abstract interface for entity extraction, classification, summarization | Phase 1b (branch 003) |
| **GeminiAdapter** | Concrete implementation using Gemini API for all NLP tasks | Phase 1b (branch 003) |
| **NotionIntegrator** | Fetch company lists, create/update Notion database entries | Phases 2a, 2d (branches 004, 007) |
| **VerificationQueue** | Store low-confidence extractions for manual review | Phase 3a (branch 009) |
| **ReportGenerator** | Generate periodic summary reports with trends and insights | Phases 4a-4b (branches 011-012) |

### Removed Components

**FuzzyMatcher** (originally planned) was **removed** and absorbed into `GeminiAdapter`. Rationale:
- Gemini can perform semantic company matching using provided company lists in prompt context
- Simpler architecture (one less component)
- Better handling of abbreviations and typos via LLM semantic understanding
- RapidFuzz library kept as optional fallback if LLM matching insufficient

---

## Data Flow

### Simplified Email-to-Notion Workflow

```
1. EmailReceiver
   ↓ Raw email
2. ContentNormalizer
   ↓ Cleaned text
3. NotionIntegrator.fetch_company_lists()
   ↓ Company lists (스타트업, 협업기관)
4. LLMProvider (GeminiAdapter)
   - Input: Cleaned email text + company lists
   - Output: ExtractedEntities + MatchedCompanies + Classification + Summary
   ↓
5. NotionIntegrator.create_entry()
   - Create "레이더 활동" entry
   - Link matched company relations
   ↓
6. If confidence < 0.85 → VerificationQueue
   Else → Complete ✅
```

### Error Paths

```
EmailReceiver failure
  ↓
  Retry with exponential backoff
  ↓
  If max retries exhausted → Log error, notify admin

ContentNormalizer failure (parse error)
  ↓
  Log warning, proceed with raw text
  (LLM can often handle unnormalized text)

LLM API failure (timeout, rate limit, 5xx error)
  ↓
  Exponential backoff: 1s, 2s, 4s, 8s (max 3 retries)
  ↓
  If still failing → Dead Letter Queue (DLQ)
  ↓
  Manual review of DLQ items

Notion API failure (fetch or create)
  ↓
  Exponential backoff: 5s, 10s, 20s (max 5 retries)
  ↓
  If rate limit error → Queue locally, process when limit resets
  ↓
  If still failing → DLQ

Company match confidence < 0.85
  ↓
  Flag for verification
  ↓
  Store in VerificationQueue with unmatched name
  ↓
  Manual review via Review UI (Phase 3b)
```

---

## LLM Provider Abstraction Layer

### Purpose

Enable swapping between Gemini, GPT, Claude, or multi-LLM orchestration without rewriting the entire system. This is critical if:
- Gemini accuracy is insufficient (<85%)
- Costs become prohibitive at scale
- Better models become available
- We need consensus from multiple LLMs for higher accuracy

### Interface Definition

```python
# src/llm_provider/base.py

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ExtractedEntities(BaseModel):
    """Entities extracted from email"""
    person_in_charge: Optional[str]  # 담당자
    startup_name: Optional[str]      # 스타트업명
    partner_org: Optional[str]       # 협업기관
    details: str                      # 협업내용
    date: Optional[datetime]          # 날짜
    confidence: dict[str, float]      # Per-field confidence scores

class Classification(BaseModel):
    """Collaboration classification"""
    collab_type: str  # [A] PortCo×SSG, [B] Non-PortCo×SSG, [C] PortCo×PortCo, [D] Other
    intensity: str    # 이해, 협력, 투자, 인수
    confidence: dict[str, float]  # Per-classification confidence

class ClassificationContext(BaseModel):
    """Context needed for classification"""
    portfolio_companies: list[str]  # List of portfolio company names
    ssg_affiliates: list[str]       # List of SSG affiliate names

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def extract_entities(self, email_text: str) -> ExtractedEntities:
        """Extract key entities from email text.

        Args:
            email_text: Normalized email body (Korean/English)

        Returns:
            ExtractedEntities with fields and confidence scores
        """
        pass

    @abstractmethod
    def classify(
        self,
        entities: ExtractedEntities,
        context: ClassificationContext
    ) -> Classification:
        """Classify collaboration type and intensity.

        Args:
            entities: Extracted entities from extract_entities()
            context: Portfolio status, SSG affiliation lookup results

        Returns:
            Classification with type, intensity, and confidence
        """
        pass

    @abstractmethod
    def summarize(self, text: str, max_sentences: int = 5) -> str:
        """Generate 3-5 sentence summary preserving key details.

        Args:
            text: Full collaboration details text
            max_sentences: Maximum sentences in summary (3-5)

        Returns:
            Summary string (Korean or English matching input)
        """
        pass
```

### GeminiAdapter Implementation Approach

**File**: `src/llm_adapters/gemini.py`

**Strategy**:
1. **All-in-One Prompt**: Single Gemini call performs extraction + matching + classification + summarization
   - Input: Cleaned email text + company lists from Notion
   - Output: Structured JSON with all fields

2. **Structured Output**: Use Gemini's JSON schema enforcement for reliable parsing

3. **Prompt Engineering**:
   ```python
   prompt = f"""
   You are an expert at extracting collaboration information from Korean/English emails.

   **Company Context**:
   Portfolio Companies: {portfolio_companies}
   SSG Affiliates: {ssg_affiliates}

   **Email**:
   {email_text}

   **Task**: Extract entities, match to existing companies, classify collaboration, and summarize.

   Return JSON:
   {{
     "person_in_charge": "담당자 name",
     "startup_name": "matched portfolio company (or extracted if no match)",
     "partner_org": "matched SSG affiliate (or extracted if no match)",
     "details": "original collaboration content",
     "date": "YYYY-MM-DD",
     "collab_type": "[A/B/C/D]",
     "intensity": "이해/협력/투자/인수",
     "summary": "3-5 sentence summary preserving key details",
     "confidence": {{"person": 0.95, "startup": 0.87, "partner": 0.92, "date": 0.88, "type": 0.91, "intensity": 0.89}}
   }}
   """
   ```

4. **Error Handling**:
   - Retry with exponential backoff (1s, 2s, 4s, 8s) for API failures
   - Fallback to null values with low confidence if JSON parsing fails
   - Cost tracking: Log token usage per request

5. **Swapping to GPT/Claude**:
   ```python
   # src/llm_adapters/gpt.py
   class GPTAdapter(LLMProvider):
       # Same interface, different API calls
       pass

   # src/llm_adapters/claude.py
   class ClaudeAdapter(LLMProvider):
       # Same interface, different API calls
       pass
   ```

**Swap Time**: ~30 minutes to implement new adapter and switch configuration

---

## Error Handling & Retry Strategy

### Retry Logic

| Failure Type | Backoff Strategy | Max Retries | Fallback |
|--------------|------------------|-------------|----------|
| **LLM API** (timeout, 5xx error) | Exponential: 1s, 2s, 4s, 8s | 3 | Dead Letter Queue (DLQ) |
| **Notion API** (timeout, 5xx error) | Exponential: 5s, 10s, 20s | 5 | DLQ |
| **Rate Limit** (429 error) | Queue locally, process when limit resets | ∞ | Wait until rate limit window expires |
| **Email Parsing** (malformed) | Log warning, proceed with raw text | 0 | LLM can often handle unnormalized text |

### Dead Letter Queue (DLQ)

**Purpose**: Capture unrecoverable errors for manual review

**Storage**: File-based (JSON) initially, can migrate to database if needed
- Location: `data/dlq/YYYY-MM-DD_HH-MM-SS_{error_type}.json`
- Format: Original email + error details + retry history

**DLQ Review Process**:
1. Admin reviews DLQ items daily
2. Identifies root cause (API outage, malformed email, etc.)
3. Fixes issue (e.g., update parsing logic, wait for API recovery)
4. Re-queues items for processing

### Monitoring & Logging

**Key Metrics**:
- Success rate per component (EmailReceiver, LLM, Notion)
- Average latency per component
- Retry count per error type
- DLQ item count and resolution time

**Logging Strategy**:
- **INFO**: Successful email processing
- **WARNING**: Retry triggered (with reason)
- **ERROR**: Max retries exhausted, item moved to DLQ
- **CRITICAL**: System-wide failure (e.g., all LLM calls failing)

---

## Edge Case Mitigation

**Mapping from spec.md Edge Cases to Architecture**:

| Edge Case | Mitigation Strategy | Architecture Component |
|-----------|---------------------|------------------------|
| **1. Gemini API fails to achieve ≥85% confidence on Korean text** | LLMProvider abstraction layer allows easy swapping to GPT-4 or Claude without rewriting system; OR implement multi-LLM voting/consensus for higher accuracy at higher cost | `LLMProvider` interface + multiple adapters (`GeminiAdapter`, `GPTAdapter`, `ClaudeAdapter`) |
| **2. Notion API rate limits (3 req/s) insufficient for 50 emails/day** | Calculate actual throughput requirements and design queuing/batching strategy to stay within limits (Phase 2e: error handling includes rate limit handling) | `NotionIntegrator` with local queue + rate limit respecting logic |
| **3. Selected technology stack has licensing issues** | Evaluate alternative libraries or negotiate licensing before proceeding; LLM APIs (Gemini, GPT, Claude) have commercial-friendly terms | License review in feasibility phase (Phase 0) |
| **4. Email infrastructure (Gmail API) has prohibitive cost at scale** | Compare with alternatives (IMAP self-hosted, SendGrid Inbound Parse, AWS SES) and switch if needed; abstraction in EmailReceiver component enables swapping | `EmailReceiver` interface with multiple implementations (`GmailAPIReceiver`, `IMAPReceiver`, `WebhookReceiver`) |
| **5. Architecture design reveals conflicting requirements** | LLM API calls (1-3 second latency) fit well with serverless constraints compared to loading large NLP models (10-30 second cold start); revise architecture accordingly if conflicts found | Cloud Run deployment with <3s response time, no cold start issues |
| **6. LLM API costs become prohibitive at scale** | Calculate break-even point (e.g., at 500+ emails/day, self-hosted NLP may be cheaper); LLMProvider abstraction allows swapping NLP backend without rewriting entire system | `LLMProvider` interface enables swapping to self-hosted models if needed |

---

## Deployment Architecture

### Google Cloud Platform (GCP) - Recommended

**Selected Option**: **Cloud Run** (containerized serverless)

### Deployment Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Google Cloud Platform                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Cloud Run Service                       │   │
│  │                                                       │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │         CollabIQ Container (Docker)          │  │   │
│  │  │                                               │  │   │
│  │  │  - Python 3.12                               │  │   │
│  │  │  - EmailReceiver                             │  │   │
│  │  │  - LLMProvider (Gemini)                      │  │   │
│  │  │  - NotionIntegrator                          │  │   │
│  │  │  - VerificationQueue                         │  │   │
│  │  │  - ReportGenerator                           │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  │  Auto-scaling: 0-10 instances                       │   │
│  │  Min instances: 1 (no cold starts)                  │   │
│  │  Memory: 512MB-1GB                                  │   │
│  │  CPU: 1 vCPU                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Gemini API (managed service)                │   │
│  │  - Entity extraction                                 │   │
│  │  - Classification                                    │   │
│  │  - Summarization                                     │   │
│  │  - Fuzzy matching                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────┘
                           │
                           ▼
                   External Services
                   ┌──────────────┐
                   │  Notion API  │
                   │  (External)  │
                   └──────────────┘
                   ┌──────────────┐
                   │  Email       │
                   │  (Gmail/etc) │
                   └──────────────┘
```

### Cloud Run vs Alternatives

| Option | Pros | Cons | Cost (50 emails/day) | Recommendation |
|--------|------|------|----------------------|----------------|
| **Cloud Run** ⭐ | ✅ No cold starts with min instances<br>✅ Custom containers<br>✅ Scales to zero<br>✅ Easy local dev with Docker<br>✅ Production-grade | ❌ Slightly higher cost than Functions<br>❌ Requires Dockerfile | ~$10-15/month (with min 1 instance) | **RECOMMENDED** |
| Cloud Functions (2nd gen) | ✅ Simpler than Cloud Run<br>✅ Native Python 3.12<br>✅ Pay-per-use | ❌ Cold starts (~1-2s)<br>❌ Execution time limits (60 min max) | ~$5-10/month | Good for low-volume |
| Compute Engine (VM) | ✅ Full control<br>✅ No cold starts<br>✅ Persistent state | ❌ Always-on costs<br>❌ Manual scaling<br>❌ More maintenance | ~$25-50/month (e2-micro/e2-small) | Only if >1000 emails/day |

### Cloud Run Deployment Strategy

**Configuration**:
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: collabiq
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"  # No cold starts
        autoscaling.knative.dev/maxScale: "10"  # Scale up to 10 instances
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/collabiq:latest
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: key
        - name: NOTION_API_KEY
          valueFrom:
            secretKeyRef:
              name: notion-api-key
              key: key
```

**Unified Billing**:
- Gemini API: ~$15-50/month (50 emails/day)
- Cloud Run: ~$10-15/month (min 1 instance)
- **Total**: ~$25-65/month on single GCP invoice

### Migration Path to Compute Engine

**If volume exceeds 500 emails/day**:
- Cloud Run becomes cost-ineffective at high constant load
- Migrate to e2-standard-2 VM (~$50/month) with always-on processing
- Break-even point: ~500 emails/day

---

## Scalability Design

### Current Scale (50 emails/day)

**Bottlenecks**: None expected
- Gemini API: Supports thousands of requests/minute
- Notion API: 3 req/s limit → 259,200 req/day >> 50 emails
- Cloud Run: Auto-scales to 10 instances if needed

### Future Scale (100+ emails/day)

**No architecture changes needed** ✅

**Capacity Analysis**:
- Gemini API: Still well within limits
- Notion API: 50 emails = ~150 API calls/day (fetch lists + create entry) → Still <1% of rate limit
- Cloud Run: Auto-scaling handles spikes

### Extreme Scale (1000+ emails/day)

**Potential Changes**:
1. **Caching**: Cache Notion company lists (refresh every hour instead of per email)
2. **Batching**: Batch Notion writes (create multiple entries in fewer API calls)
3. **Database**: Introduce PostgreSQL for local queueing and DLQ storage
4. **Message Queue**: Add Cloud Pub/Sub for asynchronous processing
5. **Compute Engine**: Migrate from Cloud Run to always-on VM (~$50/month)

---

## Security Considerations

### Secrets Management
- **API Keys**: Store in GCP Secret Manager, inject as environment variables
- **Never commit**: .env files excluded via .gitignore
- **Rotation**: Support key rotation without downtime (graceful secret reload)

### Data Privacy
- **Notion Data**: Store only business identifiers (company names, collaboration details)
- **Internal Data**: Team member names/emails (담당자 field) are internal only
- **No External PII**: Do not store external personal data (end-user emails, phone numbers)

### Authentication
- **Notion API**: OAuth token with workspace-level permissions (not full account access)
- **Gemini API**: API key restricted to specific GCP project
- **Email Access**: App-specific password (not main account password) if using Gmail API/IMAP

---

## Technology Stack Summary

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.12 | Excellent LLM/NLP ecosystem, async support, team expertise |
| **LLM** | Gemini API (via google-generativeai SDK) | Best Korean out-of-box, structured output, low cost |
| **LLM Abstraction** | Custom `LLMProvider` interface | Enable swapping to GPT/Claude if needed |
| **Data Store** | Notion databases (레이더 활동, 스타트업, 계열사) | Existing infrastructure, built-in UI for review |
| **Email** | Gmail API / IMAP / Webhook (TBD in feasibility) | Evaluated in Phase 0, selected based on research |
| **Deployment** | Google Cloud Run (containerized serverless) | Best balance of cost, scaling, unified GCP billing |
| **Testing** | pytest + pytest-asyncio + pytest-mock | Standard Python testing stack |
| **Code Quality** | ruff (linting/formatting) + mypy (type checking) | Fast, modern Python tooling |
| **Dependency Mgmt** | UV (modern Python package manager) | Faster than pip, reproducible builds |

---

## Next Steps

**After Architecture Design Complete**:
1. ✅ **Architecture documented** (this file)
2. → **Data model definition** (data-model.md - LLMProvider interface, entity schemas)
3. → **API contracts** (contracts/*.yaml - component interfaces)
4. → **Implementation roadmap** (implementation-roadmap.md - 12-phase plan)
5. → **Project scaffold** (working Python project structure)
6. → **Feature implementation** (branches 002-012 executing roadmap)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-28
**Next Review**: After feasibility study completion (Phase 0)
