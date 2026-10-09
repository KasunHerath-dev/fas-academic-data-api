# FAS Academic Data API

## Overview
A read-only REST API providing structured academic data from the Faculty of Applied Sciences, Wayamba University of Sri Lanka.

## Architecture
- Academic data is collected from official FAS sources.
- Source documents are processed by an asynchronous ingestion pipeline.
- Structured validated data is stored in PostgreSQL.
- The REST API provides read-only access to this structured data.
- Production PDFs are not permanently stored.
- The API does not perform PDF processing or ingestion during requests.

## Base URL
Development: `http://localhost:8000/api/v1`
Production: `https://YOUR-API-DOMAIN/api/v1`

## API Versioning
The current API version is `/api/v1`.
- Breaking changes require a new API version.
- Non-breaking additions may remain in the same version.
- Existing clients should continue working during v1.
- Academic document revisions (e.g., revised timetables) are NOT API versions. They create a new document/version inside the academic data, not an `/api/v2` endpoint.

## Authentication
The Phase 12 API is **read-only** and currently does not require developer API keys or authentication for basic data access. Rate limiting and access controls may be implemented in future phases.

---

## Health
### `GET /api/v1/health`
Returns API service health status and database connection status.

---

## Academic Structure
Core academic hierarchy (years, semesters, levels, modules, etc.).

### `GET /api/v1/academic-years`
Returns available academic years.

### `GET /api/v1/semesters`
Returns structured semester information.

### `GET /api/v1/levels`
Returns academic levels (e.g., Level 1, Level 2).

### `GET /api/v1/majors`
Returns majors available in the curriculum.

### `GET /api/v1/programmes`
Returns academic programmes.

### `GET /api/v1/modules`
Returns modules with optional filtering by `level`, `major`, `programme`, and `module_code`.

---

## Timetables
Structured timetable sessions retrieved from official documents.

### `GET /api/v1/timetables`
Returns structured timetable sessions from stored academic data.

**Filtering:**
- `academic_year`
- `semester`
- `level`
- `major`
- `programme`
- `module_code`
- `day_of_week`

**Note:** Nullable values may occur because the source document may not contain a deterministic value (e.g., missing room names).

### `GET /api/v1/timetables/latest`
Resolves the active timetable using the existing version-management rules.

**Version Resolution Rules:**
1. `re-revised`
2. `revised`
3. `original`
4. `unknown`/draft
*Tie-breaking:* newest `first_seen_at`, then highest `document_id`.

**Document Lineage:**
Historical document versions remain available in the database, and timetable sessions retain document lineage (`document_id`).

---

## Academic Calendar
Academic calendar periods (exams, vacations, etc.).

### `GET /api/v1/calendar`
Returns structured academic calendar periods.

**Data Quality and OCR:**
Academic calendar data is extracted from official FAS calendar documents. Some source PDFs are image-based and therefore OCR is used during ingestion. OCR validation may result in a verification status of `REVIEW_REQUIRED`. This does not mean the API failed; it means the data should be manually verified if high confidence is strictly required.

### `GET /api/v1/calendar/latest`
Resolves the active calendar based on versioning rules.

---

## Documents
### `GET /api/v1/documents`
Returns source metadata for scraped FAS documents.

**Note:** A Document does NOT represent a permanently stored PDF file. The API stores and returns source URLs, revisions, SHA-256 hashes, and validation status, but does not provide PDF binary downloads.

---

## Synchronization Status
### `GET /api/v1/sync-runs`
Returns the history of ingestion activity.

### `GET /api/v1/sync-runs/latest`
Yields the success/failure state and modified document counts of the most recent scraping job.

**Note:** The API only reads SyncRun information; it does not start synchronization jobs.

---

## Error Handling
The API returns a consistent error format for standard application exceptions:
```json
{
  "detail": "Requested resource was not found."
}
```
Validation errors are returned using FastAPI's standard HTTP 422 Unprocessable Entity format.
The API does not expose SQL errors, stack traces, database strings, or internal credentials.

---

## Examples

### cURL
```bash
# Health check
curl http://localhost:8000/api/v1/health

# List academic years
curl "http://localhost:8000/api/v1/academic-years"

# List levels
curl "http://localhost:8000/api/v1/levels"

# List all timetables
curl "http://localhost:8000/api/v1/timetables"

# Get latest timetable for specific criteria
curl "http://localhost:8000/api/v1/timetables/latest?academic_year=2024/2025&semester=1&level=2"

# Get latest calendar periods
curl "http://localhost:8000/api/v1/calendar/latest?academic_year=2024/2025"

# List document metadata
curl "http://localhost:8000/api/v1/documents"

# Get latest sync run status
curl "http://localhost:8000/api/v1/sync-runs/latest"
```

### JavaScript
```javascript
async function getLatestTimetable() {
  const response = await fetch(
    "https://YOUR-API-DOMAIN/api/v1/timetables/latest?academic_year=2024/2025&semester=1&level=2"
  );
  const data = await response.json();
  console.log(data);
}
```

### Python
```python
import requests

response = requests.get(
    "https://YOUR-API-DOMAIN/api/v1/timetables/latest",
    params={
        "academic_year": "2024/2025",
        "semester": "1",
        "level": "2",
    },
)

data = response.json()
print(data)
```

### AttendTrack
AttendTrack is only a consumer of this API. It should request structured timetable data directly.
It should NOT:
- Scrape the FAS website.
- Download timetable PDFs.
- OCR timetable PDFs.
- Maintain its own FAS timetable scraper.

**Integration Flow:**
`AttendTrack` -> `GET /api/v1/timetables/latest` -> `FAS Academic Data API` -> `PostgreSQL`

---

## Future Developer Access
The API is currently configured for broad read-only access. Advanced rate limiting, API keys, and a developer dashboard may be introduced in future phases. No complex authentication is currently required.
