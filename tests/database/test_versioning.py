import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document, TimetableSession
from database.versioning import get_latest_document, get_document_versions, get_revision_score

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()

def create_doc(db, **kwargs):
    defaults = {
        "title": "Timetable",
        "document_type": "TIMETABLE",
        "academic_year": "2023",
        "semester": "II",
        "level": "2",
        "sha256": "fakehash",
        "status": "processed",
        "validation_status": "SAFE",
        "first_seen_at": datetime.now(timezone.utc)
    }
    defaults.update(kwargs)
    doc = Document(**defaults)
    db.add(doc)
    db.commit()
    return doc

def test_revision_score():
    assert get_revision_score("original") == 10
    assert get_revision_score("revised") == 20
    assert get_revision_score("re-revised") == 30
    assert get_revision_score("DRAFT") == 0
    assert get_revision_score(None) == 0

def test_original_only(db_session):
    doc1 = create_doc(db_session, revision="original")
    latest = get_latest_document(db_session, "TIMETABLE", "2023", "II", "2")
    assert latest.id == doc1.id

def test_original_and_revised(db_session):
    doc1 = create_doc(db_session, revision="original", first_seen_at=datetime.now(timezone.utc) - timedelta(days=2))
    doc2 = create_doc(db_session, revision="revised", first_seen_at=datetime.now(timezone.utc) - timedelta(days=1))
    latest = get_latest_document(db_session, "TIMETABLE", "2023", "II", "2")
    assert latest.id == doc2.id

def test_original_revised_rerevised(db_session):
    doc1 = create_doc(db_session, revision="original")
    doc2 = create_doc(db_session, revision="revised")
    doc3 = create_doc(db_session, revision="re-revised")
    latest = get_latest_document(db_session, "TIMETABLE", "2023", "II", "2")
    assert latest.id == doc3.id

def test_original_and_rerevised(db_session):
    # What if "revised" is skipped?
    doc1 = create_doc(db_session, revision="original")
    doc2 = create_doc(db_session, revision="re-revised")
    latest = get_latest_document(db_session, "TIMETABLE", "2023", "II", "2")
    assert latest.id == doc2.id

def test_unknown_revision_behavior(db_session):
    # If there are two unknown revisions, the latest one by first_seen_at wins
    doc1 = create_doc(db_session, revision="DRAFT", first_seen_at=datetime.now(timezone.utc) - timedelta(days=2))
    doc2 = create_doc(db_session, revision="UNKNOWN", first_seen_at=datetime.now(timezone.utc) - timedelta(days=1))
    latest = get_latest_document(db_session, "TIMETABLE", "2023", "II", "2")
    assert latest.id == doc2.id

def test_historical_documents_remain_intact(db_session):
    doc1 = create_doc(db_session, revision="original")
    doc2 = create_doc(db_session, revision="revised")
    
    versions = get_document_versions(db_session, "TIMETABLE", "2023", "II", "2")
    assert len(versions) == 2
    assert versions[0].id == doc2.id
    assert versions[1].id == doc1.id

def test_historical_sessions_retain_document_id(db_session):
    doc1 = create_doc(db_session, revision="original")
    session = TimetableSession(
        document_id=doc1.id, day="Monday", start_time="08:30", end_time="10:30",
        time_source="explicit", verification_status="valid"
    )
    db_session.add(session)
    db_session.commit()
    
    # New revised document is created
    doc2 = create_doc(db_session, revision="revised")
    
    # Old session should STILL point to doc1
    db_session.refresh(session)
    assert session.document_id == doc1.id

def test_multiple_academic_contexts_independent(db_session):
    # Year 2023
    doc1 = create_doc(db_session, revision="original", academic_year="2023", level="2")
    doc2 = create_doc(db_session, revision="revised", academic_year="2023", level="2")
    
    # Year 2024
    doc3 = create_doc(db_session, revision="original", academic_year="2024", level="2")
    
    latest_2023 = get_latest_document(db_session, "TIMETABLE", "2023", "II", "2")
    assert latest_2023.id == doc2.id
    
    latest_2024 = get_latest_document(db_session, "TIMETABLE", "2024", "II", "2")
    assert latest_2024.id == doc3.id
