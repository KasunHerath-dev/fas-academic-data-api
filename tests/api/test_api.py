import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.dependencies.database import get_db
from database.database import Base
from database.models.models import AcademicYear, Semester, Level, Major, Programme, Module, Document, TimetableSession, AcademicCalendarPeriod, SyncRun

# Setup test DB
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db = TestingSessionLocal()
    # Add dummy data
    db.add(AcademicYear(year_string="2024/2025"))
    db.add(Semester(semester_string="1"))
    db.add(Level(level_string="2"))
    db.add(Major(major_string="Computing"))
    db.add(Programme(programme_string="BSc"))
    db.add(Module(module_code="CMIS 2123", module_name="Object Oriented", level="2"))
    
    doc = Document(
        title="Test Timetable",
        document_type="TIMETABLE",
        source_url="http://test",
        academic_year="2024/2025",
        semester="1",
        level="2",
        revision="original",
        sha256="fake",
        status="processed",
        validation_status="SAFE"
    )
    db.add(doc)
    db.flush()
    
    db.add(TimetableSession(
        document_id=doc.id,
        academic_year="2024/2025",
        semester="1",
        level="2",
        day="Monday",
        start_time="08:30",
        end_time="10:30",
        module_code="CMIS 2123",
        verification_status="valid",
        time_source="explicit"
    ))
    
    db.add(AcademicCalendarPeriod(
        document_id=doc.id, # Mocking document_id for simplicity
        activity_name="Test Period",
        academic_year="2024/2025",
        semester="1",
        verification_status="verified"
    ))
    
    db.add(SyncRun(status="success"))
    
    db.commit()
    db.close()

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"

def test_academic_years():
    response = client.get("/api/v1/academic-years")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["year_string"] == "2024/2025"

def test_semesters():
    response = client.get("/api/v1/semesters")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_levels():
    response = client.get("/api/v1/levels")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_majors():
    response = client.get("/api/v1/majors")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_programmes():
    response = client.get("/api/v1/programmes")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_modules():
    response = client.get("/api/v1/modules?level=2")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_documents():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] > 0
    assert data["data"][0]["academic_year"] == "2024/2025"

def test_timetables():
    response = client.get("/api/v1/timetables?academic_year=2024/2025&semester=1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    assert data["data"][0]["day"] == "Monday"

def test_timetables_latest():
    response = client.get("/api/v1/timetables/latest?academic_year=2024/2025&semester=1&level=2")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0

def test_timetables_latest_not_found():
    response = client.get("/api/v1/timetables/latest?academic_year=9999/9999")
    assert response.status_code == 404

def test_calendar():
    response = client.get("/api/v1/calendar")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0

def test_calendar_latest():
    response = client.get("/api/v1/calendar/latest")
    assert response.status_code == 404 # No calendar document inserted in setup, we used TIMETABLE

def test_sync_runs():
    response = client.get("/api/v1/sync-runs")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0

def test_sync_runs_latest():
    response = client.get("/api/v1/sync-runs/latest")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_404():
    response = client.get("/api/v1/invalid")
    assert response.status_code == 404
