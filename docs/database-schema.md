# Database Schema

## Overview
The FAS Academic Data API uses Neon PostgreSQL as its central data store. The database serves as the access point for the Web App / API. Original PDF binaries are **NEVER** stored in the database.

## Ingestion vs Access
- **GitHub Actions (Ingestion):** Writes heavily to the database during its scheduled tasks. It manages `SyncRun` tracking, normalizes `TimetableSessions`, and computes `sha256` versions.
- **Web App/API (Access):** Reads cleanly from the database. It does not perform OCR or scrape PDFs.

## Tables
- `academic_years`, `semesters`, `levels`, `majors`, `programmes`: Core academic lookup tables.
- `modules`: Central store of validated courses.
- `documents`: Stores information on discovered academic source material.
- `timetable_sessions`: Extracted individual timetable blocks, directly linked to `documents`.
- `academic_calendar_periods`: Extracted academic term schedules.
- `sync_runs`: Audit logging for scheduled GitHub Actions executions.

## Important Fields and Relationships

### 1. Document Versioning (`documents`)
The `documents` table is strictly versioned by `sha256` and `revision` strings.
- **Important Columns:** `sha256`, `document_type`, `status`, `revision`.
- Revisions (e.g., "original", "revised") coexist independently.
- No binary PDF blob storage exists.

### 2. Session Lineage (`timetable_sessions`)
- **Foreign Key:** `document_id` links directly to the `documents` table.
- This ensures any given parsed session can be traced back to its exact originating PDF source and hash.
- **Nullable Data:** Columns like `room`, `group`, `major`, `programme` are nullable by design, accommodating ambiguities in FAS WUSL timetables.
- **Raw Evidence:** `raw_module_code`, `raw_room`, `time_source` preserve the original OCR output.

### 3. SyncRun Tracking (`sync_runs`)
- Represents one complete execution of the GitHub Actions ingestion pipeline.
- Currently, there is NO hard foreign key linking a `SyncRun` directly to `Document`. A sync run might parse multiple documents or skip them entirely. If we need per-document tracking, a bridge table (`sync_run_documents`) can be introduced later.
