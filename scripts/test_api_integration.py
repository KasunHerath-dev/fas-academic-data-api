import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.dependencies.database import get_db
from database.database import Base
from database.models.models import Document, TimetableSession, AcademicCalendarPeriod, SyncRun

def main():
    print("========================================")
    print("API INTEGRATION TEST")
    print("========================================\n")
    
    # Setup isolated test DB
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    # Insert some dummy data reflecting successful ingestions
    doc = Document(
        title="Timetable 2024",
        document_type="TIMETABLE",
        source_url="http://test/time.pdf",
        academic_year="2024/2025",
        revision="original",
        sha256="fakehash",
        status="processed",
        validation_status="SAFE"
    )
    db.add(doc)
    
    cal_doc = Document(
        title="Calendar 2024",
        document_type="ACADEMIC_CALENDAR",
        source_url="http://test/cal.pdf",
        academic_year="2024/2025",
        revision="original",
        sha256="fakehash2",
        status="processed",
        validation_status="SAFE"
    )
    db.add(cal_doc)
    db.flush()
    
    db.add(TimetableSession(
        document_id=doc.id,
        academic_year="2024/2025",
        semester="1",
        day="Monday",
        start_time="08:00",
        end_time="10:00",
        module_code="CS 101",
        verification_status="valid",
        time_source="explicit"
    ))
    
    db.add(AcademicCalendarPeriod(
        document_id=cal_doc.id,
        activity_name="Mid-Term",
        academic_year="2024/2025",
        semester="1",
        verification_status="verified"
    ))
    
    db.add(SyncRun(status="success", documents_processed=2))
    
    db.commit()
    
    # Override Dependency
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    print("1. Testing Health Endpoint:")
    r = client.get("/api/v1/health")
    print(f"Status: {r.status_code}, Response: {r.json()}\n")
    
    print("2. Testing Documents:")
    r = client.get("/api/v1/documents")
    print(f"Status: {r.status_code}, Count: {r.json().get('count')}\n")
    
    print("3. Testing Timetables:")
    r = client.get("/api/v1/timetables")
    print(f"Status: {r.status_code}, Count: {r.json().get('count')}\n")
    
    print("4. Testing Latest Timetables:")
    r = client.get("/api/v1/timetables/latest?academic_year=2024/2025")
    print(f"Status: {r.status_code}, Count: {r.json().get('count')}\n")
    
    print("5. Testing Calendar:")
    r = client.get("/api/v1/calendar")
    print(f"Status: {r.status_code}, Count: {r.json().get('count')}\n")
    
    print("6. Testing Latest Calendar:")
    r = client.get("/api/v1/calendar/latest")
    print(f"Status: {r.status_code}, Count: {r.json().get('count')}\n")
    
    print("7. Testing Latest Sync Run:")
    r = client.get("/api/v1/sync-runs/latest")
    print(f"Status: {r.status_code}, Response: {r.json()}\n")
    
    print("INTEGRATION SUCCESSFUL")
    print("========================================")
    
if __name__ == "__main__":
    main()
