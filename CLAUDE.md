# CollabIQ Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-30

## Active Technologies
- Local in-memory cache for secrets (TTL-based), existing file-based .env fallback (003-infisical-secrets)
- Python 3.12+ (established in project) (004-gemini-extraction)
- File-based JSON output (`data/extractions/{email_id}.json`) (004-gemini-extraction)

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
- 005-gmail-setup: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
- 004-gemini-extraction: Added Python 3.12+ (established in project)
- 003-infisical-secrets: Added Python 3.12 (established in project)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
