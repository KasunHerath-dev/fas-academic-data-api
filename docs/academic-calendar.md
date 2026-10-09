# Academic Calendar Ingestion Pipeline

## Format Differences
Unlike the purely vector-based text PDFs of the FAS Timetables, the FAS Academic Calendars (such as `COD-2024-2025.pdf`) are completely scanned/image-based. Because they lack a reliable text layer, the ingestion pipeline takes an entirely separate OCR-based path:
```
PDF -> pdf2image -> Tesseract OCR -> Layout Reconstruction -> Quality Gate -> Database
```

## OCR and Extraction Method
1. **Rendering**: The PDF is temporarily rendered to an image in-memory using `pdf2image`. We do not permanently save images.
2. **Text Extraction**: We utilize `pytesseract` in dictionary output mode (`image_to_data`), capturing raw text, bounding box coordinates, and confidence scores.
3. **Table/Column Detection**: We reconstruct lines dynamically using the Y-coordinates (top). Because Tesseract might return boxes out of order, sorting them by X-coordinate within stable Y-bands guarantees correct column sequencing.
4. **Semester Sections**: "FIRST SEMESTER" and "SECOND SEMESTER" headers are explicitly captured and passed down to subsequent rows.

## Data Parsing
- **Dates**: We extract dates in the format `DD-MM-YYYY` (or variants with `.`). We never guess dates.
- **Duration**: Extracted via `\b\d{2}\s*Weeks?\b`. If an academic period lasts "08 Weeks", the string is stored securely in `duration_text` and integer-parsed to `duration_weeks`.
- **Period Name**: Determined contextually by extracting text preceding the dates. Normalization strips trailing punctuation (e.g. `Academic Session contd.....` becomes `Academic Session contd`).

## Validation and Quality Gates
We rely on the standard 3-tier Quality Gate (SAFE, REVIEW_REQUIRED, REJECT):
- **SAFE**: Calendar structure parsed perfectly, all dates are valid and logically sequenced.
- **REVIEW_REQUIRED**: Some words scored < 50% confidence in Tesseract, triggering an "OCR uncertainty flagged by extractor" warning, or dates look structurally ambiguous. The data is saved but flagged.
- **REJECT**: More than 50% of the rows completely failed date formatting, or dates flow backward (end < start). The atomic transaction rolls back fully.

## Versioning
This pipeline integrates seamlessly with Phase 9 versioning rules. A re-revised calendar simply creates a new `Document` row (version), and points its newly extracted `AcademicCalendarPeriod` rows to the new `document_id`.

## Known Limitations
- The accuracy relies completely on Tesseract OCR. Very low-DPI scans will heavily degrade the data and push the document into the `REJECT` state.
- Columns are currently inferred via regex matching (2 consecutive dates = From/To, "Weeks" = Duration). Advanced geometric boundaries are not strictly required since the calendar structure is extremely uniform horizontally.
