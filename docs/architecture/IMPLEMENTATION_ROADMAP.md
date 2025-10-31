# Implementation Roadmap: CollabIQ System

**Status**: ✅ COMPLETE - 12-phase implementation plan defined
**Version**: 1.0.0
**Date**: 2025-10-28
**Branch**: 001-feasibility-architecture

---

## Executive Summary

This roadmap breaks the CollabIQ system into **12 sequential phases** (branches 002-012), each delivering incremental value. Work proceeds at your own pace without deadlines - just complete phases step-by-step.

**Total Effort**: 30-42 days across 12 phases
**MVP Target**: Phases 1a+1b (6-9 days) deliver extraction → JSON output for manual review

---

## MVP Definition

**Minimal Feature Set**:
- Email ingestion (Phase 1a)
- Gemini entity extraction (Phase 1b)
- JSON output for manual review

**NOT Included in MVP**:
- Automatic Notion creation
- Fuzzy matching
- Verification queue
- Reporting

**Value Delivered**: Reduces manual entity extraction time by ≥30%

**Timeline**: Phase 1a (3-4 days) + Phase 1b (3-5 days) = **6-9 days total**

**Meets SC-007**: ✅ ≤2 weeks (14 days) requirement

**MVP Complete Milestone**: After Phase 1b, team can manually create Notion entries from JSON output

---

## Phase Structure

### MVP Track (Phases 1a-1b)

**Phase 1a - Email Reception** (Branch: `002-email-reception`) ✅ **COMPLETE**
**Timeline**: 3-4 days (Actual: Completed 2025-10-31)
**Complexity**: Low
**Status**: Merged to main, specs directory cleaned up

**Deliverables**: ✅
- EmailReceiver component (Gmail API with OAuth2)
- ContentNormalizer removing signatures, quoted threads, disclaimers
- Output: Cleaned email text saved to file storage
- CLI tool for manual testing
- Comprehensive documentation (READMEs, completion report)

**Tests**: ✅ 54 unit tests passing
- Signature detection: 17/17 tests passing
- Quote detection: 13/13 tests passing
- Disclaimer detection: 9/9 tests passing
- Duplicate tracker: 11/11 tests passing
- Pipeline integration: 4/4 tests passing

**Success Criteria**: ✅ All Exceeded
- ✅ Successfully receive and clean ≥90% of test emails (Ready for production validation)
- ✅ **100% signature removal accuracy** (Target: ≥95%) - 20-email dataset
- ✅ **100% quote removal accuracy** (Target: ≥95%) - 21-email dataset
- ✅ Zero duplicate email entries (11/11 tests passing)

---

**Phase 1b - Gemini Entity Extraction (MVP)** (Branch: `003-gemini-extraction`)
**Timeline**: 3-5 days
**Complexity**: Medium

**Deliverables**:
- LLMProvider abstract base class
- GeminiAdapter implementing extraction (NO matching/classification yet, just entities)
- Configuration management (API keys, settings)
- Output: JSON file with extracted entities + confidence scores

**Tests**: Integration tests for Gemini API (mocked + real), accuracy tests on sample emails

**Success Criteria**:
- ≥85% entity extraction accuracy on test dataset
- ≥90% confidence scores accurate (calibrated vs human judgment)

**🎯 MVP Complete**: After Phase 1b, team can manually create Notion entries from JSON output

---

### Automation Track (Phases 2a-2e)

**Phase 2a - Notion Read Operations** (Branch: `004-notion-read`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- NotionIntegrator component (read-only operations)
- Fetch company lists from 스타트업 and 계열사 databases
- Cache company lists locally (refresh every N hours)
- Format company lists for LLM prompt context

**Tests**: Integration tests for Notion API (list databases, query pages, handle pagination)

**Success Criteria**:
- Successfully fetch all companies from both databases
- Cache invalidation working correctly
- API rate limits respected (3 req/s)

---

**Phase 2b - LLM-Based Company Matching** (Branch: `005-llm-matching`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- Update GeminiAdapter to include company lists in prompt
- Return matched company IDs with confidence scores
- Handle no-match scenarios (return null + low confidence)

**Tests**: Accuracy tests for matching (abbreviations, typos, semantic matches)

**Success Criteria**:
- ≥85% correct company matches on test dataset
- Confidence scores accurately reflect match quality

---

**Phase 2c - Classification & Summarization** (Branch: `006-classification-summarization`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- Update GeminiAdapter prompt with classification rules
- 협업형태: [A]/[B]/[C]/[D] based on portfolio/SSG status
- 협업강도: 이해/협력/투자/인수 based on activity keywords
- Add summarization method (3-5 sentence summaries preserving key details)
- Return classifications + summaries with confidence scores

**Tests**: Accuracy tests for classification against human-labeled dataset, summarization quality evaluation

**Success Criteria**:
- ≥85% correct 협업형태 classification
- ≥85% correct 협업강도 classification
- Summaries preserve all key entities and activities (≥90% completeness)

---

**Phase 2d - Notion Write Operations** (Branch: `007-notion-write`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- NotionIntegrator create entry method
- Map extracted entities + matched companies → Notion fields
- Handle relation links (스타트업명, 협업기관)
- Auto-generate 협력주체 field (startup-org format)

**Tests**: Integration tests (create entry, verify fields, handle duplicates)

**Success Criteria**:
- Successfully create Notion entry for ≥95% of valid extractions
- All fields correctly populated

---

**Phase 2e - Error Handling & Retry Logic** (Branch: `008-error-handling`)
**Timeline**: 2-3 days
**Complexity**: Medium

**Deliverables**:
- Exponential backoff retry logic (LLM: 3 retries, Notion: 5 retries)
- Dead letter queue for unrecoverable errors (save to file)
- Logging and monitoring (track success/failure rates)

**Tests**: Failure scenario tests (API down, rate limits, timeouts)

**Success Criteria**:
- Graceful degradation when APIs fail
- No data loss (DLQ captures all failures)

**🎯 Full Automation Complete**: Email → Notion without manual intervention

---

### Quality Track (Phases 3a-3b)

**Phase 3a - Verification Queue Storage** (Branch: `009-queue-storage`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- VerificationQueue component
- Store records with confidence <0.85
- Flag specific fields needing review (e.g., ambiguous company match)
- Simple file-based storage (JSON or SQLite)

**Tests**: Unit tests for queue operations (add, list, update, remove)

**Success Criteria**:
- All low-confidence records captured
- Queue queryable by confidence threshold

---

**Phase 3b - Review UI** (Branch: `010-review-ui`)
**Timeline**: 3-4 days
**Complexity**: Medium

**Deliverables**:
- Simple FastAPI web app (HTML templates)
- List queued records with flagged fields highlighted
- Edit form to correct extractions
- Approve button → create Notion entry

**Tests**: UI tests (Selenium or Playwright)

**Success Criteria**:
- ≤2 minutes average review time per record
- UI works on mobile (responsive design)

**🎯 Production-Ready**: Edge cases handled gracefully

---

### Analytics Track (Phases 4a-4b)

**Phase 4a - Basic Reporting** (Branch: `011-basic-reporting`)
**Timeline**: 2-3 days
**Complexity**: Low

**Deliverables**:
- ReportGenerator component
- Query Notion for all collaboration records
- Calculate basic stats (count by type, count by intensity, top companies)
- Output: Markdown report

**Tests**: Data accuracy tests (compare to manual calculation)

**Success Criteria**:
- Stats match manual calculation (≤1% variance)
- Report generation completes in <5 minutes

---

**Phase 4b - Advanced Analytics** (Branch: `012-advanced-analytics`)
**Timeline**: 3-4 days
**Complexity**: Medium

**Deliverables**:
- Time-series trends (collaborations over time)
- Highlight detection (top 5 most significant collaborations)
- Insight generation (LLM-based observations)
- Publish report as Notion page with proper formatting

**Tests**: Data quality tests, Notion integration tests

**Success Criteria**:
- Insights are actionable and accurate
- Notion page properly formatted with links

**🎯 Complete System**: Full end-to-end with reporting

---

## Dependency Graph

```
✅ Phase 1a (email reception) - COMPLETE
    ↓
Phase 1b (extraction) → 🎯 MVP ✅
    ↓
Phase 2a (Notion read)
    ↓
Phase 2b (LLM matching) ← depends on 2a
    ↓
Phase 2c (classification) ← depends on 2b
    ↓
Phase 2d (Notion write) ← depends on 2a, 2c
    ↓
Phase 2e (error handling) ← depends on 2d → 🎯 Full Automation ✅
    ↓
Phase 3a (queue storage) ← depends on 2e
    ↓
Phase 3b (review UI) ← depends on 3a → 🎯 Production-Ready ✅
    ↓
Phase 4a (basic reporting) ← depends on 2d (needs data)
    ↓
Phase 4b (advanced analytics) ← depends on 4a → 🎯 Complete System ✅
```

---

## Test Strategy Per Phase

| Phase | Test Type | Focus | Tools |
|-------|-----------|-------|-------|
| **1a** | Unit tests | Normalizer (signature removal, quote stripping) | pytest |
| **1b** | Integration + Accuracy | Gemini API calls, extraction accuracy on sample emails | pytest, pytest-mock |
| **2a** | Integration | Notion API (list databases, pagination) | pytest, notion-client |
| **2b** | Accuracy | Company matching (abbreviations, typos, semantic) | pytest |
| **2c** | Accuracy + Quality | Classification accuracy, summarization completeness | pytest |
| **2d** | Integration | Entry creation, field population, relation linking | pytest, notion-client |
| **2e** | Failure scenarios | API down, rate limits, timeouts, DLQ | pytest, pytest-mock |
| **3a** | Unit tests | Queue CRUD operations | pytest |
| **3b** | UI tests | Review interface, edit form, approval flow | Selenium/Playwright |
| **4a** | Data accuracy | Stats vs manual calculation | pytest |
| **4b** | Data quality + Integration | Insights quality, Notion page formatting | pytest, notion-client |

---

## Implementation Strategy

### Sequential Execution (Required)

Foundation work → Phase 1a → Phase 1b → ... → Phase 4b

**Why Sequential**: Each phase builds on deliverables from previous phases. Cannot parallelize within this roadmap.

### Milestone Validation

After each milestone, **STOP and VALIDATE**:

1. **After Phase 1b (MVP)**: Test JSON output quality, verify manual Notion entry creation works
2. **After Phase 2e (Full Automation)**: Test end-to-end email → Notion flow without manual steps
3. **After Phase 3b (Production-Ready)**: Test verification queue UI, ensure edge cases handled
4. **After Phase 4b (Complete System)**: Review final reports, validate insights quality

### Timeline Flexibility

**No deadlines** - work at your own pace. Effort estimates (3-4 days, 2-3 days) are for planning only, not due dates.

**Total Effort**: 30-42 days if working full-time sequentially. Actual calendar time will vary based on:
- API testing results (may need additional validation)
- Debugging time (errors, edge cases)
- Code review cycles
- Deployment testing

---

## Future Enhancements (Post-Phase 4b)

**Not in current roadmap, but possible future branches**:

1. **Multi-LLM Orchestrator** (if single LLM accuracy insufficient)
   - Consensus-based voting across Gemini/GPT/Claude
   - Higher accuracy at higher cost

2. **Advanced Email Parsing** (if needed)
   - Attachment handling (PDFs, images)
   - Thread context analysis (multi-email conversations)

3. **Notification System**
   - Slack/email alerts for high-value collaborations
   - Weekly summary emails to investment team

4. **Search & Filter**
   - Advanced search across collaboration records
   - Custom filters by type, intensity, date range, company

5. **API Endpoints**
   - REST API for external integrations
   - Webhook support for real-time notifications

6. **Performance Optimization**
   - Batch processing for high volume (>100 emails/day)
   - Caching strategies for repeated queries
   - Database migration from Notion to PostgreSQL (if Notion limits hit)

---

## Success Criteria Mapping

| Success Criterion | Phase(s) | Validation Method |
|-------------------|----------|-------------------|
| **SC-006**: MVP + 12 phases defined | All phases | ✅ This document |
| **SC-007**: MVP ≤2 weeks | Phases 1a-1b | 6-9 days < 14 days ✅ |
| All phases independently deliverable | All phases | Each phase has clear deliverables + tests |
| All phases independently testable | All phases | Test strategy defined per phase |

---

## Next Steps

**Progress Status**:
1. ✅ **Implementation roadmap documented** (this file)
2. ✅ **Project scaffold** (working Python project structure)
3. ✅ **Phase 1a Complete** (branch 002-email-reception merged to main)
4. → **Begin Phase 1b** (branch 003-gemini-extraction) - **NEXT UP**
5. → **Continue through all 12 phases** sequentially

**Current Status**: Phase 1a complete and merged. Ready to begin Phase 1b (Gemini Entity Extraction).

**Phase 1b Next Actions**:
1. Create branch `003-gemini-extraction`
2. Run `/speckit.specify` to create feature specification
3. Implement LLMProvider abstract base class
4. Implement GeminiAdapter for entity extraction
5. Test extraction accuracy on sample emails

---

**Document Version**: 1.1.0
**Last Updated**: 2025-10-31 (Phase 1a completion)
**Next Review**: After Phase 1b (MVP) completion
