# Source Discovery

## Official Source URLs
The FAS Academic Data API relies strictly on the official Wayamba University FAS website:
- **Timetables:** `https://fas.wyb.ac.lk/timetables/`
- **Academic Calendars:** `https://fas.wyb.ac.lk/timetables/academic-calendar/`

## Discovery Flow
`SourceDiscovery.discover_all()` is the entry point used by the sync job.

1. **WordPress REST API (preferred).** `GET /wp-json/wp/v2/posts?categories=<ids>&orderby=modified`,
   paginated via `X-WP-TotalPages`. Every PDF link in a notice becomes one document. The notice
   title gives type/year/semester/revision; the link text (e.g. "Level 2 & 3") overrides the levels.
   Post `date_gmt` → `published_at`, `modified_gmt` → `source_updated_at`.
   Category IDs default to `54` (timetables) and `57` (calendars); override with
   `FAS_TIMETABLE_CATEGORY_IDS` / `FAS_CALENDAR_CATEGORY_IDS`. `FAS_BASE_URL` overrides the site.
2. **HTML fallback.** If the API returns nothing, the listing pages below are scraped as before:
   follow each notice link, take the first PDF and the `<time>` / `article:modified_time` dates.
3. Deduplicate by PDF URL and return newest first, so the latest documents are processed first.
4. Exam timetables and titles that are neither a timetable nor a calendar are skipped.

## Metadata Extraction Rules
Metadata extraction relies on regex parsing of the document title. We strictly do not invent metadata. If a field cannot be derived deterministically, it is set to `null`/unknown, leaving the raw title as evidence.

### Supported Title Patterns
- **Timetables:** Look for keywords like "Time Table" or "Timetable" (case-insensitive).
- **Academic Calendars:** Look for "Calendar".
- **Academic Year:** Extracted from formats like "2024/2025" or "2024-2025".
- **Semester:** Extracted looking for "Semester I", "Semester II", etc.
- **Levels:** Extracts digits trailing the word "Level" (e.g., "Level 1,2,3 & 4").
- **Revision:** "Re-revised", "Revised", or numbered ("Revised 02", "2nd Revised" → `revised-2`). Defaults to "original".

### Unknown Metadata Behavior
If metadata cannot be identified, fields remain `None` and the raw link text is preserved in `title`.

## Error Handling
- Safe timeouts (10 seconds default).
- Catches `requests.RequestException` and logs errors gracefully.
- Prevents script termination on a single bad HTTP response.

## Future Integration Point
The current `SourceDiscovery` module acts as step 1 in the ingestion pipeline. In the future, the GitHub Actions worker will invoke this module, extract the `DiscoveredDocument` objects, and pass them to the **Change Detection** module (which compares them against existing database records via `source_url` and `sha256`).

---

## Future Web App UI Direction
The frontend data access application will feature a distinct visual design:
- **Theme:** Light theme only. Simple and smooth.
- **Background:** White / very light gray background.
- **Coloring:** One primary color with a subtle gradient.
- **Vibe:** Modern academic/professional appearance.
- **Elements:** Minimal shadows, clean cards, responsive layout.
- **Usability:** Easy timetable/calendar navigation, no unnecessary visual complexity.
