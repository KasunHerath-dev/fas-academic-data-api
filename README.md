# FAS Academic Data API

## Project Purpose
The Faculty of Applied Sciences, Wayamba University of Sri Lanka (FAS WUSL) publishes academic information such as timetables and academic calendars. The purpose of this project is to automatically collect the latest official academic documents from the FAS website, extract structured academic information, validate it, store the structured data in Neon PostgreSQL, and expose the data through a reusable REST API.

## Project Independence
This project is **completely independent** from AttendTrack. It does not contain any AttendTrack-specific business logic, nor does it share a database. The final API will serve as a generalized public API for AttendTrack, other university applications, and external developers.

## Final Responsibility Architecture

The architecture relies on two **strictly separated flows**: Data Ingestion and Data Access.

### FLOW A — INGESTION (GitHub Actions = Data Ingestion Engine)
The GitHub Actions workflow acts as the scheduled background worker. Its responsibilities are:
1. Discover latest documents from the official FAS Website.
2. Check existing database records and compare SHA-256 to skip unchanged documents.
3. Download new/changed PDFs temporarily.
4. Run heavy Python PDF parsing, OCR, validation, and normalization.
5. Store structured data and update `SyncRun` status in Neon PostgreSQL.
6. Delete temporary PDFs.

### FLOW B — ACCESS (Web App = Data Access / Viewer)
The Web App is strictly an API consumer and viewer. It does **not**:
- Scrape the FAS website.
- Download PDFs.
- Run heavy parsing or OCR.
- Trigger data extraction synchronously.

It simply connects to the API/Service Layer to view and filter already-processed data residing in Neon PostgreSQL.

## Technology Stack
- **Backend/API:** Python, FastAPI
- **Database:** Neon PostgreSQL, SQLAlchemy 2.x, Alembic
- **Validation:** Pydantic
- **PDF Processing:** PyMuPDF, pdfplumber
- **Image/OCR:** OpenCV, numpy (PaddleOCR as fallback)
- **Testing:** pytest

## Document Lifecycle and PDF Temporary-Storage Policy
The ingestion engine detects a new or changed document and downloads it to a temporary workspace. A SHA-256 hash is calculated for deduplication and version control. The PDF is parsed, structured data is extracted and stored, and then the PDF is permanently deleted from the local system. PDFs are never stored in the database or cloud blob storage.

## Revision Handling
The FAS website often publishes revised timetables. The system utilizes document versioning (Original, Revised, Re-revised) alongside SHA-256 hashing to track revisions without overwriting historical metadata.

## Database
We use Neon PostgreSQL for scalable storage. The central database holds structured records (e.g., `Documents`, `TimetableSessions`, `SyncRuns`) and serves them efficiently via the API.

### Environment setup
Create a `.env` file based on `.env.example`:
```
DATABASE_URL=postgresql://user:password@host/dbname
ENVIRONMENT=development
API_CORS_ORIGINS=http://localhost:3000
```
Never commit real credentials.

## REST API
The system provides a read-only REST API built with **FastAPI** to access the structured data.
- **Base URL:** `/api/v1`
- **Documentation:** Interactive OpenAPI docs are available at `/docs` (Swagger) and `/redoc` (ReDoc) when the server is running.
- **Detailed Guide:** See [docs/api.md](docs/api.md) for full endpoint specifications, architecture rules, and client examples.
- **Developer Start:** See [docs/developer-quickstart.md](docs/developer-quickstart.md) to set up and run the API locally.

### Migrations
Initialize and run migrations via Alembic:
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## Testing
To run the automated tests:
```bash
PYTHONPATH=. pytest
```

## Future Roadmap
- Phase 1: Project foundation (Current)
- Phase 2: Neon database connection & migrations
- Phase 3: FAS source discovery
- Phase 4: Document metadata & SHA-256 change detection
- Phase 5: Temporary PDF download lifecycle
- ...
- Phase 11: REST API implementation
- Phase 14: Production deployment
