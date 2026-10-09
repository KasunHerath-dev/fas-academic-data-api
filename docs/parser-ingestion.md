# Parser to Database Ingestion Flow

## Ingestion Architecture
The ingestion service bridges the Parser/Validator layer and the Database. 
The flow runs entirely inside a database transaction ensuring atomic guarantees:
```
PDF -> parse_timetable -> TimetableValidator -> validate_timetable
```
If validation passes the Quality Gate, the system:
1. Maps `ParsedTimetable` into the database models (`Document` and `TimetableSession`).
2. Opens a PostgreSQL transaction.
3. Inserts the `Document` and `TimetableSession` records.
4. Commits (or rollbacks entirely on failure).

## Transaction Guarantees
- **Atomic Operations**: A document and all its sessions are inserted together. If the database crashes mid-way, the transaction rolls back, leaving no orphaned data.
- **Rollback on Error**: If any step raises an exception (e.g. `SQLAlchemyError`), the transaction is aborted.

## Quality Gate Behaviors
1. **SAFE**: The document validation result has 0 invalid sessions and 0 uncertain sessions/warnings. Ingestion commits the records with `validation_status="SAFE"`.
2. **REVIEW_REQUIRED**: Some sessions have warnings (e.g., suspicious OCR) or there are document warnings (e.g., duplicate detection). **Ingestion still proceeds**, but the `Document` is marked `validation_status="REVIEW_REQUIRED"`. The uncertain sessions preserve their exact OCR warnings in the database.
3. **REJECT**: Document contains mathematically impossible values (negative times, unknown days). **Ingestion aborts immediately** before touching the database.

## Validation Metadata Preservation
The `Document` model stores a `validation_metadata` JSON column containing:
- Counts of valid, uncertain, and invalid sessions.
- Document-level warnings and errors.

The `TimetableSession` model stores:
- `verification_status`: e.g. "valid" or "uncertain".
- `warnings`: The exact OCR warnings from the Validator.
- `raw_evidence`: The raw text blocks the Parser saw.

## Duplicate and Re-import Handling
Duplicates are safely avoided through the Phase 4 `ChangeDetector`. We do not blindly re-ingest PDFs. Only PDFs that are flagged as `NEW` or `CHANGED` by the Change Detector reach the ingestion phase. If a changed PDF arrives, a NEW `Document` row is created, preserving historical sessions on the old `Document` row.
