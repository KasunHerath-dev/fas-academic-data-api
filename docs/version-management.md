# Version & Revision Management

## Document Identity
In this system, a document is fundamentally identified by its **SHA-256 hash** combined with its **source_url** and **revision label**.
If a timetable is published, we parse it and store it as a historical document record along with its extracted sessions.

## Same SHA vs Changed SHA
- **Same SHA, Same Revision**: The `ChangeDetector` identifies this as `UNCHANGED`. No new `Document` row is created, saving processing time and avoiding duplicate session records.
- **Changed SHA**: If the PDF content changes (even slightly) but keeps the same URL and revision label, it is flagged as `CHANGED`. A completely new `Document` row is created, preserving the old row entirely.
- **Different Revision**: A distinct revision ("original", "revised", "re-revised") intrinsically creates a distinct Document track. 

## Historical Preservation
When a new revision or a changed PDF is ingested:
- Old `Document` rows are **NEVER** deleted.
- Old `TimetableSession` rows are **NEVER** modified.
- Every `TimetableSession` preserves an immutable foreign key (`document_id`) to the exact Document version from which it was extracted.
- If a document disappears from the FAS website entirely, its historical `Document` record in the database remains intact permanently.

## Latest Version Resolution
The system determines the "active" or "latest" timetable using deterministic `get_latest_document()` rules rather than blindly trusting database insertion order.

### Resolution Priority:
1. **Revision Label Priority**:
   - `re-revised` > `revised` > `original`
2. **First Seen Timestamp**:
   - If two documents have the same revision label (e.g. both are "original" but one replaced the other), the one with the newer `first_seen_at` timestamp takes precedence.
3. **Database ID**:
   - Finally, the highest `id` acts as a fallback tie-breaker.

### Unknown Revisions
If an unknown revision label is encountered (e.g., "DRAFT" or "FINAL"), its priority defaults to 0 (lower than "original"). However, the timestamp tie-breaker ensures that a newer unknown revision will still correctly override an older unknown revision.
