# Validation Documentation

This directory contains API validation results, testing guides, and technical research documentation for the CollabIQ project.

---

## Current Validation Documents

### End-to-End Testing

- **[E2E_TESTING.md](E2E_TESTING.md)** (40K) - Comprehensive E2E testing guide
  - Setup and configuration
  - Running tests (mock, dry-run, full modes)
  - Module testing (Gmail, Gemini, Notion)
  - Success criteria and validation
  - Troubleshooting guide
  - Implementation status

- **[E2E_DATA_MODEL.md](E2E_DATA_MODEL.md)** (14K) - E2E test data model reference
  - Test run entity structure
  - Error record format
  - Performance metrics schema
  - JSON persistence format

### API Validation & Research

- **[GEMINI_API_REFERENCE.md](GEMINI_API_REFERENCE.md)** (31K) - Gemini API reference
  - **Current**: API authentication, rate limits, pricing, prompt engineering
  - **Deprecated**: Manual retry logic (see Phase 010 error handling instead)
  - Use this for: Understanding Gemini API capabilities and best practices
  - ⚠️ For error handling, see [src/error_handling/README.md](../../src/error_handling/README.md)

- **[NOTION_API_VALIDATION.md](NOTION_API_VALIDATION.md)** (12K) - Notion API validation results
  - API access verification (Oct 2025)
  - Database schema confirmation (15 fields in CollabIQ, 23 in Companies)
  - CRUD operations testing
  - Integration setup guide

- **[NOTION_SCHEMA_ANALYSIS.md](NOTION_SCHEMA_ANALYSIS.md)** (2.8K) - Notion database schema
  - CollabIQ database field structure
  - Company database field structure
  - Actual field types and samples from production

### Library Comparisons

- **[date-parsing-library-comparison.md](date-parsing-library-comparison.md)** (15K) - Date parsing library comparison
  - `python-dateutil` vs `dateparser` analysis
  - Korean date format support evaluation
  - Relative date parsing capabilities
  - **Decision**: Using `dateparser` for multi-language support

---

## Archived Documentation

Older documentation from Phase 0 has been moved to [`docs/archive/phase0/`](../archive/phase0/).

**Archived Phase 0 Docs**:
- `FEASIBILITY_TESTING.md` - Phase 0 feasibility template (completed)
- `FOUNDATION_WORK_REPORT.md` - Phase 0 completion report (outdated)
- `EMAIL_INFRASTRUCTURE.md` - Email infrastructure comparison (decision made: Gmail API)

See [docs/archive/README.md](../archive/README.md) for more details on archived documentation.

---

## How to Use This Documentation

### For New Developers

1. **Start here**: [E2E_TESTING.md](E2E_TESTING.md) - Understand the full testing workflow
2. **Understand APIs**: Read API validation docs to see what's been tested
3. **Reference**: Use data model and schema docs when working with test data

### For Testing

- **Run E2E tests**: Follow [E2E_TESTING.md](E2E_TESTING.md) Quick Start section
- **Validate APIs**: Check validation docs to confirm API capabilities
- **Debug issues**: Refer to schema analysis for data structure reference

### For API Research

- **Gemini API**: [GEMINI_API_REFERENCE.md](GEMINI_API_REFERENCE.md) (ignore error handling section)
- **Notion API**: [NOTION_API_VALIDATION.md](NOTION_API_VALIDATION.md) + [NOTION_SCHEMA_ANALYSIS.md](NOTION_SCHEMA_ANALYSIS.md)
- **Date Parsing**: [date-parsing-library-comparison.md](date-parsing-library-comparison.md)

---

## Documentation Status

| Document | Status | Last Updated | Purpose |
|----------|--------|--------------|---------|
| E2E_TESTING.md | ✅ Current | Nov 8, 2025 | E2E test guide |
| E2E_DATA_MODEL.md | ✅ Current | Nov 8, 2025 | Test data reference |
| GEMINI_API_REFERENCE.md | ⚠️ Partially current | Nov 8, 2025 | API reference (retry logic deprecated) |
| NOTION_API_VALIDATION.md | ✅ Current | Oct 29, 2025 | API validation results |
| NOTION_SCHEMA_ANALYSIS.md | ✅ Current | Oct 29, 2025 | Schema documentation |
| date-parsing-library-comparison.md | ✅ Current | Nov 2, 2025 | Library comparison |

---

## Related Documentation

- [Main Documentation Index](../README.md) - All project documentation
- [Setup Guides](../setup/) - Installation and configuration
- [Architecture Docs](../architecture/) - System design and patterns
- [Error Handling](../../src/error_handling/README.md) - Phase 010 unified retry system

---

## Contributing to Validation Docs

When adding new validation documentation:

1. **Follow naming convention**: Use descriptive, UPPERCASE_FILENAME.md format
2. **Add to this README**: Update the tables above with your new doc
3. **Include metadata**: Add date, status, and purpose at the top of your doc
4. **Link related docs**: Cross-reference other relevant documentation
5. **Update main docs**: Add link in [docs/README.md](../README.md) if appropriate

---

**Document Status**: ✅ Current
**Last Updated**: 2025-11-08
**Maintained By**: CollabIQ Development Team
