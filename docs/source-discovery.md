# Source Discovery

## Official Source URLs
The FAS Academic Data API relies strictly on the official Wayamba University FAS website:
- **Timetables:** `https://fas.wyb.ac.lk/timetables/`
- **Academic Calendars:** `https://fas.wyb.ac.lk/timetables/academic-calendar/`

## Discovery Flow
1. Fetch the source HTML page via standard HTTP GET (with reasonable timeouts and a standard user-agent).
2. Parse the HTML for `<a>` tags with `href` attributes ending in `.pdf`.
3. Normalize the URLs (make absolute, remove fragments).
4. Deduplicate links using the normalized URL.
5. Extract metadata from the link text (which acts as the document title).

## Metadata Extraction Rules
Metadata extraction relies on regex parsing of the document title. We strictly do not invent metadata. If a field cannot be derived deterministically, it is set to `null`/unknown, leaving the raw title as evidence.

### Supported Title Patterns
- **Timetables:** Look for keywords like "Time Table" or "Timetable" (case-insensitive).
- **Academic Calendars:** Look for "Calendar".
- **Academic Year:** Extracted from formats like "2024/2025" or "2024-2025".
- **Semester:** Extracted looking for "Semester I", "Semester II", etc.
- **Levels:** Extracts digits trailing the word "Level" (e.g., "Level 1,2,3 & 4").
- **Revision:** "Re-revised" or "Revised". Defaults to "original".

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
