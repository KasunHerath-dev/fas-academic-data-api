# Parser Integration

## Architecture
The system integrates an already-existing, highly specialized PDF parser explicitly tuned for FAS WUSL timetables. 

1. **`pdf_loader.py`**: Wraps PyMuPDF to load raw pages.
2. **`text_extractor.py`**: Extracts geometric words/blocks.
3. **`table_detector.py`**: Finds the grid geometrically.
4. **`cell_parser.py`**: Assigns text boundaries to the grid.
5. **`session_parser.py`**: Extracts session attributes (module, type, room, group).
6. **`session_merger.py`**: Safely collapses adjacent sessions only when evidence strongly warrants it.
7. **`api.py`**: The production entry point (`parse_timetable`) converting the parser's loose dictionary output into strict Pydantic `ParsedTimetable` structures.

## Production Entry Point
```python
from parser.src.api import parse_timetable, ParsedTimetable

# Only feed it a local file path
timetable: ParsedTimetable = parse_timetable("/tmp/temporary.pdf")
```

## Validation States
Every parsed session is tagged with a `verification_status`:
- **`verified`**: The parser encountered no warnings, ambiguity, or missing fundamental values.
- **`uncertain`**: The parser successfully extracted the session, but flagged an OCR warning (e.g. suspicious module code like `ELTN 3+53`), an ambiguous merge, or a missing core attribute.
- **`invalid`**: The row completely failed basic timeline validation (e.g., negative duration) and is flagged in the report failures (though these are often skipped at the parse stage).

## Supported / Unverified Layouts
- **Verified**: Level 2 & 3 (via the `Level-23.pdf` fixture).
- **Designed to Support**: Level 1, Level 4, combined Level 1/2, combined 3/4, revised, and re-revised timetables.
- **Not Yet Tested**: Any PDFs outside of the Level-23 fixture (as the actual PDFs for other levels haven't been provided yet).

## Temporary PDF Integration
The parser takes an absolute file path. By designing the Phase 5 `managed_pdf_lifecycle` to yield a temporary path, we pass that string directly to `parse_timetable()`. When `parse_timetable()` returns, the context manager automatically deletes the PDF from disk. The parser never writes to permanent storage.

## Known Limitations
- The parser cannot definitively correct broken OCR (e.g., distinguishing `1` from `l` in groups) without an external dictionary. It preserves the raw evidence instead.
- If the timetable lacks a physical grid (e.g., it is a purely text-based memo), it will be cleanly rejected with a `ValueError` rather than crashing randomly.

## Future Database Mapping
The `ParsedSession` model is fully compatible with the `TimetableSession` SQLAlchemy model. 
1. Future ingestion will map `ParsedSession.day` to `TimetableSession.day`.
2. `ParsedSession.time_source` maps cleanly to explicit/inferred flags.
3. Foreign keys will attach to the newly created `Document` version to preserve lineage.
