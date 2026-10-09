import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import Base
from database.models.models import Document, TimetableSession

# Use in-memory SQLite for testing models
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_document(db_session):
    doc = Document(
        title="Test Timetable",
        document_type="TIMETABLE",
        sha256="fakehash123",
        status="processed"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    assert doc.id is not None
    assert doc.title == "Test Timetable"
    assert doc.sha256 == "fakehash123"

def test_create_timetable_session(db_session):
    doc = Document(
        title="Test Timetable",
        document_type="TIMETABLE",
        sha256="fakehash123",
        status="processed"
    )
    db_session.add(doc)
    db_session.commit()
    
    session = TimetableSession(
        document_id=doc.id,
        day="Monday",
        start_time="08:30",
        end_time="10:30",
        module_code="CMIS 1113",
        time_source="explicit",
        verification_status="verified"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    assert session.id is not None
    assert session.document_id == doc.id
    assert session.day == "Monday"
