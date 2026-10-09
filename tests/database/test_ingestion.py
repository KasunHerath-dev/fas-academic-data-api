import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document, TimetableSession
from database.ingestion import ingest_timetable_pdf
from parser.src.validator import DocumentGateStatus
import fitz

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()

def create_mock_pdf(tmp_path, empty=False):
    pdf_path = tmp_path / "mock.pdf"
    doc = fitz.open()
    page = doc.new_page()
    if empty:
        page.insert_text((50, 50), "Empty timetable no grid")
    else:
        # Just create something that parses. Actually, the parser needs a real timetable grid.
        # For testing, we can mock `parse_timetable` inside `database.ingestion`.
        pass
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

def test_ingestion_safe(db_session, monkeypatch, tmp_path):
    from parser.src.api import ParsedTimetable, ParsedSession
    
    def mock_parse(path):
        return ParsedTimetable(
            sessions=[
                ParsedSession(
                    day="Monday",
                    start_time="08:30",
                    end_time="10:30",
                    module_code="CMIS 1113",
                    time_source="explicit",
                    verification_status="verified",
                    raw_evidence={},
                    warnings=[]
                )
            ],
            diagnostics=[],
            report={}
        )
    monkeypatch.setattr("database.ingestion.parse_timetable", mock_parse)
    
    meta = {
        "source_url": "http://test",
        "title": "Test Title",
        "document_type": "TIMETABLE",
        "sha256": "fakehash"
    }
    
    res = ingest_timetable_pdf(db_session, create_mock_pdf(tmp_path), meta)
    assert res.success is True
    assert res.validation_result.status == DocumentGateStatus.SAFE
    
    doc = db_session.query(Document).filter_by(id=res.document_id).first()
    assert doc.validation_status == "SAFE"
    
    sessions = db_session.query(TimetableSession).filter_by(document_id=res.document_id).all()
    assert len(sessions) == 1
    assert sessions[0].verification_status == "valid"

def test_ingestion_review_required(db_session, monkeypatch, tmp_path):
    from parser.src.api import ParsedTimetable, ParsedSession
    
    def mock_parse(path):
        return ParsedTimetable(
            sessions=[
                ParsedSession(
                    day="Monday",
                    start_time="08:30",
                    end_time="10:30",
                    module_code="ELTN 3+53", # triggers uncertain
                    time_source="explicit",
                    verification_status="uncertain",
                    raw_evidence={},
                    warnings=[]
                )
            ],
            diagnostics=[],
            report={}
        )
    monkeypatch.setattr("database.ingestion.parse_timetable", mock_parse)
    
    meta = {
        "title": "Test Title", "document_type": "TIMETABLE", "sha256": "fakehash"
    }
    
    res = ingest_timetable_pdf(db_session, create_mock_pdf(tmp_path), meta)
    assert res.success is True
    assert res.validation_result.status == DocumentGateStatus.REVIEW_REQUIRED
    
    doc = db_session.query(Document).filter_by(id=res.document_id).first()
    assert doc.validation_status == "REVIEW_REQUIRED"
    
    sessions = db_session.query(TimetableSession).filter_by(document_id=res.document_id).all()
    assert len(sessions) == 1
    assert sessions[0].verification_status == "uncertain"
    assert "Suspicious module code" in sessions[0].warnings[0]

def test_ingestion_reject(db_session, monkeypatch, tmp_path):
    from parser.src.api import ParsedTimetable, ParsedSession
    
    def mock_parse(path):
        return ParsedTimetable(
            sessions=[
                ParsedSession(
                    day="Funday", # triggers invalid
                    start_time="08:30",
                    end_time="10:30",
                    module_code="CMIS 1113",
                    time_source="explicit",
                    verification_status="verified",
                    raw_evidence={},
                    warnings=[]
                )
            ],
            diagnostics=[],
            report={}
        )
    monkeypatch.setattr("database.ingestion.parse_timetable", mock_parse)
    
    meta = {
        "title": "Test Title", "document_type": "TIMETABLE", "sha256": "fakehash"
    }
    
    res = ingest_timetable_pdf(db_session, create_mock_pdf(tmp_path), meta)
    assert res.success is False
    assert res.validation_result.status == DocumentGateStatus.REJECT
    assert "Document rejected" in res.error
    
    docs = db_session.query(Document).all()
    assert len(docs) == 0

def test_ingestion_db_error_rollback(db_session, monkeypatch, tmp_path):
    from parser.src.api import ParsedTimetable, ParsedSession
    
    def mock_parse(path):
        return ParsedTimetable(
            sessions=[
                ParsedSession(day="Monday", start_time="08:30", end_time="10:30", module_code="CMIS 1113", time_source="explicit", verification_status="verified", raw_evidence={}, warnings=[])
            ],
            diagnostics=[], report={}
        )
    monkeypatch.setattr("database.ingestion.parse_timetable", mock_parse)
    
    # Force DB error
    def mock_commit():
        raise Exception("DB Failure")
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    meta = {"title": "Test Title", "document_type": "TIMETABLE", "sha256": "fakehash"}
    
    res = ingest_timetable_pdf(db_session, create_mock_pdf(tmp_path), meta)
    assert res.success is False
    assert "Unexpected error" in res.error
    
    docs = db_session.query(Document).all()
    assert len(docs) == 0

def test_ingestion_missing_values(db_session, monkeypatch, tmp_path):
    from parser.src.api import ParsedTimetable, ParsedSession
    def mock_parse(path):
        return ParsedTimetable(
            sessions=[
                ParsedSession(day="Monday", start_time="08:30", end_time="10:30", module_code="CMIS 1113", time_source="explicit", verification_status="verified", raw_evidence={}, warnings=[], room=None, group=None)
            ],
            diagnostics=[], report={}
        )
    monkeypatch.setattr("database.ingestion.parse_timetable", mock_parse)
    meta = {"title": "Test", "document_type": "TIMETABLE", "sha256": "hash"}
    res = ingest_timetable_pdf(db_session, create_mock_pdf(tmp_path), meta)
    
    s = db_session.query(TimetableSession).first()
    assert s.room is None
    assert s.group is None
