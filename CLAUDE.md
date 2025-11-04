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
- 009-notion-write: Added Python 3.12+ (established in project)
- 008-classification-summarization: Added Python 3.12 (established in project, using UV package manager)
- 007-llm-matching: Added Python 3.12+ (established in project, using UV package manager)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
