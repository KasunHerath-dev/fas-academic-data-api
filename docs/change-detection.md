# Document Change Detection

## Overview
The Change Detection layer sits between Source Discovery and the PDF Parser. Its primary job is to prevent the scheduled ingestion worker from parsing identical documents repeatedly.

## Why SHA-256?
Relying purely on the `source_url` or document title is insufficient because the FAS WUSL website often replaces the PDF file at the exact same URL without updating the webpage metadata.
To guarantee we catch updates, we temporarily download the PDF bytes into a temporary file and calculate its `SHA-256` digest (a 64-character hex string). The `SHA-256` represents the exact content identity.

## Source URL vs Content Identity
- **Source URL / Revision:** Represents the structural identity of the post on the website (e.g. The "Revised Level 1 Timetable").
- **SHA-256:** Represents the strict content identity of the payload.

## NEW / CHANGED / UNCHANGED Behaviors
1. **NEW:** If a document is discovered with a specific `source_url` and `revision` that does not exist in the database, it is marked as `NEW`.
2. **UNCHANGED:** If the document exists and the newly calculated `sha256` matches the `sha256` of the latest database record, it is `UNCHANGED`. The worker will skip PDF parsing.
3. **CHANGED:** If the document exists but the `sha256` is different, the content has been silently updated on the website. It is marked as `CHANGED`.

## Historical Version Preservation
We do **not** blindly UPDATE existing database records. When a `CHANGED` document is detected, the ingestion worker creates a brand new `Document` row with the new `sha256`. 
This guarantees that old `TimetableSession` extraction records strictly maintain their foreign-key lineage to the exact `sha256` hash of the PDF they were parsed from.

## Interaction with Document and TimetableSession
- `Document`: A new version spawns a new `Document` row.
- `TimetableSession`: The old sessions remain untouched and securely linked to the old `Document` ID. The new `Document` ID will receive fresh `TimetableSession` extractions after parsing.

## Temporary File Lifecycle
1. The GitHub Actions worker discovers the URL.
2. It downloads the bytes to a local Python `tempfile`.
3. It passes the `tempfile` path to `hasher.py` to calculate the `sha256`.
4. It queries `change_detector.py`.
5. If `UNCHANGED`, the tempfile is immediately deleted.
6. If `NEW` or `CHANGED`, the tempfile is passed to the parser, then deleted.
7. *No PDF binaries are ever permanently stored.*

## Future Integration
This system integrates directly with the upcoming **GitHub Actions Data Ingestion Engine**, placing a highly robust checkpoint immediately after source discovery.

---

## Future Web App UI Direction
As a reminder, the future Web App (the data viewer) will strictly adhere to:
- Light theme only, white/light-gray background.
- Simple, smooth, modern professional appearance.
- One primary color, minimal shadows, subtle single-color gradient.
- Responsive design.
