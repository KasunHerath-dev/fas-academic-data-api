import os
import sys
import tempfile
import asyncio

# Setup env for testing
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"

sys.path.append(os.getcwd())
from database.database import Base, engine, SessionLocal
from database.models.models import Document, AcademicYear, TimetableSession, AcademicCalendarPeriod, SyncRun
from crawler.pdf_lifecycle import managed_pdf_lifecycle
from database.ingestion import ingest_timetable_pdf
from database.ingestion_calendar import ingest_academic_calendar
from fastapi.testclient import TestClient
from api.main import app

# Create tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Timetable ingestion
metadata = {
    "source_url": "http://example.com/Level-23.pdf",
    "title": "Level-23 Timetable",
    "document_type": "TIMETABLE",
    "academic_year": "2024/2025",
    "semester": "Semester I",
    "level": "2,3",
    "major": "Unknown",
    "programme": "Unknown",
    "revision": "original",
    "sha256": "dummy-hash-1"
}
ingest_timetable_pdf(db, "parser/input/Level-23.pdf", metadata)

# 2. Calendar ingestion
metadata_cal = {
    "source_url": "http://example.com/COD-2024-2025.pdf",
    "title": "Calendar of Dates",
    "document_type": "ACADEMIC_CALENDAR",
    "academic_year": "2024/2025",
    "semester": "Semester I",
    "level": "1,2,3,4",
    "major": "Unknown",
    "programme": "Unknown",
    "revision": "original",
    "sha256": "dummy-hash-2"
}
ingest_academic_calendar(db, "parser/input/COD-2024-2025.pdf", metadata_cal)

print("DB Academic Years:", db.query(AcademicYear).count())
print("DB Documents:", db.query(Document).count())
print("DB Timetable Sessions:", db.query(TimetableSession).count())
print("DB Calendar Periods:", db.query(AcademicCalendarPeriod).count())

# 3. Test API
client = TestClient(app)
res_ay = client.get("/api/v1/academic-years")
print("API /academic-years:", res_ay.json())

res_tt = client.get("/api/v1/timetables/latest")
print("API /timetables/latest count:", len(res_tt.json()))

res_cal = client.get("/api/v1/calendar/latest")
print("API /calendar/latest count:", len(res_cal.json()))

