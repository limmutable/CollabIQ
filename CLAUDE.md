# CollabIQ Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-30

## Active Technologies
- Local in-memory cache for secrets (TTL-based), existing file-based .env fallback (003-infisical-secrets)
- Python 3.12+ (established in project) (004-gemini-extraction)
- File-based JSON output (`data/extractions/{email_id}.json`) (004-gemini-extraction)
- Python 3.12 (established in project) + `notion-client` (official Notion Python SDK), `pydantic` (data validation), `tenacity` (retry logic with exponential backoff) (006-notion-read)
- File-based JSON cache in `data/notion_cache/` directory (schema cache + data cache with separate TTLs) (006-notion-read)
- Python 3.12+ (established in project, using UV package manager) (007-llm-matching)
- Python 3.12 (established in project, using UV package manager) (008-classification-summarization)
- File-based JSON output (`data/extractions/{email_id}.json`) - no schema changes (008-classification-summarization)
- Python 3.12 (established in project) + pytest (testing framework), existing MVP components (email_receiver, llm_adapters, notion_integrator, content_normalizer), Gmail/Gemini/Notion APIs (008-mvp-e2e-test)
- File-based (JSON files for error reports, performance metrics, test results in data/e2e_test/ directory) (008-mvp-e2e-test)

- Python 3.12 (established in project) + Git (for file operations and history preservation), markdown (for documentation) (002-structure-standards)
- Python 3.12 (002-email-reception)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12 (established in project): Follow standard conventions

## Recent Changes
- 010-error-handling: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
- 008-mvp-e2e-test: Added Python 3.12 (established in project) + pytest (testing framework), existing MVP components (email_receiver, llm_adapters, notion_integrator, content_normalizer), Gmail/Gemini/Notion APIs
- 009-notion-write: Added Python 3.12+ (established in project)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
