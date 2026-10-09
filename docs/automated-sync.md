# Automated Data Synchronization

## Architecture
The repository uses GitHub Actions as its background data ingestion worker. The ingestion flow connects directly to the production Neon PostgreSQL database using environment variables. 
The FastAPI application remains strictly a read-only consumer and does not perform any data extraction or scraping.

**Ingestion Flow:**
1. Discover latest official timetables and academic calendars from FAS.
2. Check existing database records (via `SHA-256` hashing) and identify new/changed PDFs.
3. Download PDFs to a secure, temporary workspace.
4. Process PDFs (Parsing, OCR).
5. Apply validation quality gates (`SAFE`, `REVIEW_REQUIRED`, `REJECT`).
6. Atomically persist validated records in Neon PostgreSQL, preserving previous version history.
7. Record the sync activity in `SyncRun`.
8. Clean up all temporary PDFs and artifacts.

## Workflow Triggers
- **Scheduled:** Automatically runs daily at 02:00 UTC using a cron trigger (`0 2 * * *`).
- **Manual:** Can be triggered via the GitHub Actions UI using `workflow_dispatch`.

## Required GitHub Secrets
The following secret MUST be added to the GitHub repository environments or action secrets:
- `DATABASE_URL`: Connection string to the production Neon PostgreSQL database.

*Note: Never include secrets in any PRs, issues, logs, or codebase.*

## SyncRun Statuses and Counters
Each orchestration run tracks its state inside the `sync_runs` database table:
- **`running`**: In progress. Should clear upon exit.
- **`success`**: All documents processed without fatal exceptions.
- **`partial`**: Some documents succeeded, but others encountered parsing or ingestion failures.
- **`failed`**: Entire process crashed or no documents successfully completed.

Counters track:
- `documents_checked`: Total PDFs discovered on source pages.
- `documents_changed`: PDFs that were new or had modified SHA-256 signatures.
- `documents_skipped`: PDFs matching exact `source_url` and `sha256` in the DB.
- `documents_processed`: New/changed PDFs successfully validated and ingested.
- `documents_failed`: PDFs rejected by quality gates or facing extraction errors.

## Dry-Run Mode
Both GitHub Actions (via a boolean toggle) and the local script support `--dry-run` mode.
A dry run:
- Downloads and analyzes documents.
- Hashes and parses the PDFs.
- Identifies new or changed documents.
- Avoids writing the `SyncRun` or parsed data to the database.
- Completely deletes the PDFs after inspection.

## Error Handling
Failures inside individual documents will NOT halt the entire synchronization process. The failure will increment `documents_failed` and transition the final outcome to `partial` (or `failed`). All temporary files are safely detached from the pipeline to preserve instance resources.
A fatal DB outage prevents `SyncRun` recording and triggers a nonzero UNIX exit code.

## Known Limitations
- The sync engine respects the layout of current FAS documents. Large upstream layout changes may result in `documents_failed` until the parsers are updated.
- Validation `REVIEW_REQUIRED` is stored but does not abort ingestion for Timetables or Calendars. This allows upstream reviewers to manually correct metadata when OCR confidence drops.
