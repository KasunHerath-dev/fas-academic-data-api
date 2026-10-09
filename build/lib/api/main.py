import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import health, academic_structure, timetables, calendar, documents, sync_runs

tags_metadata = [
    {"name": "Health", "description": "System and database health checks."},
    {"name": "Academic Structure", "description": "Core academic hierarchy (years, semesters, levels, modules, etc.)."},
    {"name": "Timetables", "description": "Structured timetable sessions retrieved from official documents."},
    {"name": "Academic Calendar", "description": "Academic calendar periods (exams, vacations, etc.)."},
    {"name": "Documents", "description": "Metadata for source PDFs (source URLs, hashes, revisions). Does not provide PDF binaries."},
    {"name": "Synchronization", "description": "Ingestion job history and status."}
]

description = """
A read-only API providing structured academic data from the Faculty of Applied Sciences, Wayamba University of Sri Lanka.

* Academic data is collected from official FAS sources.
* Source documents are processed by the ingestion pipeline.
* Structured validated data is stored in PostgreSQL.
* The REST API provides read access to structured data.
* Production PDFs are not permanently stored.
* The API does not perform PDF processing during requests.
"""

app = FastAPI(
    title="FAS Academic Data API",
    version="1.0.0",
    description=description,
    openapi_tags=tags_metadata
)

origins_str = os.environ.get("API_CORS_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(academic_structure.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(timetables.router, prefix="/api/v1")
app.include_router(calendar.router, prefix="/api/v1")
app.include_router(sync_runs.router, prefix="/api/v1")
