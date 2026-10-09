# Parser Validation & Quality Gate

## Architecture
The system employs a strict validation layer (`TimetableValidator`) immediately after the PDF parser and before database ingestion. Its goal is to analyze the `ParsedTimetable` output, checking both session-level sanity (e.g. valid days, time ranges, suspicious OCR) and document-level correctness (e.g. duplicate sessions, overlapping classes in the same room).

## Validation Categories
1. **VALID (Verified)**: The session meets all requirements. There are no suspicious values, no OCR ambiguities, and times are strictly well-formed.
2. **UNCERTAIN (Warning)**: The session was extracted, but contains a warning. For instance, `ELTN 3+53` instead of a standard module code, or `Gp. ll` instead of `Gp. II`. The raw evidence is preserved and the session is flagged for review.
3. **INVALID (Error)**: The session violates the laws of physics or strict definitions (e.g., negative duration, `end_time` before `start_time`, or an unknown day).

## Quality Gate Policy
The document-level validation returns one of three statuses:
- **`SAFE`**: The timetable is perfectly parsed. All sessions are valid.
- **`REVIEW_REQUIRED`**: Some sessions have `UNCERTAIN` statuses or document-level warnings (like room overlaps). The data can optionally be ingested but must be marked as requiring human review.
- **`REJECT`**: At least one session is completely `INVALID`, the timetable is entirely empty, or parser corruption is too high (>50% invalid sessions). This document **will not** proceed to database ingestion.

## Crucial Rule: OCR Honesty
The quality gate **NEVER** silently repairs uncertain OCR. If a module code is read as `ELPC 2+20`, the gate flags it as `UNCERTAIN` with a `suspicious_module_code` warning. It does not blindly overwrite the data with guesses.

## Additional Capabilities
- **Lunch Exclusion**: Checks against "L U N C H" slipping through.
- **Duplicate & Overlap Detection**: Warns if two identical classes exist, or if two different modules overlap in the same room at the same time.
- **Missing Information**: `room`, `group`, and `major` are allowed to be `NULL` (Missing data alone does not make a session invalid).
