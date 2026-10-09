import os
import sys
import tempfile

temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"

sys.path.append(os.getcwd())
from database.database import Base, engine, SessionLocal
from database.models.models import Document, AcademicYear, TimetableSession, AcademicCalendarPeriod, Level
from crawler.pdf_lifecycle import managed_pdf_lifecycle
from database.ingestion import ingest_timetable_pdf
from database.ingestion_calendar import ingest_academic_calendar
from fastapi.testclient import TestClient
from api.main import app

Base.metadata.create_all(bind=engine)
db = SessionLocal()

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
ingest_timetable_pdf(db, "docs/Level-23.pdf", metadata)

print("Levels:", [l.level_string for l in db.query(Level).all()])

client = TestClient(app)
res_levels = client.get("/api/v1/levels")
print("API /levels:", res_levels.json())

# Need to pass academic_year for timetables/latest
res_tt = client.get("/api/v1/timetables/latest?academic_year=2024/2025")
print("API /timetables/latest status:", res_tt.status_code)
if res_tt.status_code == 200:
    print("API /timetables/latest count:", len(res_tt.json().get('data', [])))
else:
    print("API /timetables/latest error:", res_tt.json())

res_cal = client.get("/api/v1/calendar/latest?academic_year=2024/2025")
print("API /calendar/latest status:", res_cal.status_code)

EOF
