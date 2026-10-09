import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document, AcademicCalendarPeriod
from database.ingestion_calendar import ingest_academic_calendar
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

def create_mock_pdf(tmp_path):
    pdf_path = tmp_path / "mock_calendar.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Mock Calendar")
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

def test_calendar_ingestion_safe(db_session, monkeypatch, tmp_path):
    from parser.calendar.api import ParsedAcademicCalendar, ParsedCalendarPeriod
    
    def mock_parse(path):
        return ParsedAcademicCalendar(
            academic_year="2024/2025",
            applicable_levels="1,2,3,4",
            raw_title=None,
            periods=[
                ParsedCalendarPeriod(
                    semester="FIRST SEMESTER",
                    period_name="Academic Session",
                    start_date="03-08-2026",
                    end_date="27-09-2026",
                    duration_text="08 Weeks",
                    source_page=1,
                    raw_evidence={},
                    verification_status="verified",
                    warnings=[]
                )
            ],
            diagnostics=[],
            report={}
        )
    monkeypatch.setattr("database.ingestion_calendar.parse_academic_calendar", mock_parse)
    
    meta = {
        "source_url": "http://test",
        "title": "Test Title",
        "document_type": "ACADEMIC_CALENDAR",
        "sha256": "fakehash"
    }
    
    res = ingest_academic_calendar(db_session, create_mock_pdf(tmp_path), meta)
    assert res.success is True
    assert res.validation_result.status == DocumentGateStatus.SAFE
    
    doc = db_session.query(Document).filter_by(id=res.document_id).first()
    assert doc.validation_status == "SAFE"
    assert doc.academic_year == "2024/2025"
    assert doc.level == "1,2,3,4"
    
    periods = db_session.query(AcademicCalendarPeriod).filter_by(document_id=res.document_id).all()
    assert len(periods) == 1
    assert periods[0].verification_status == "verified"
    assert periods[0].duration_text == "08 Weeks"
    assert periods[0].duration_weeks == 8

def test_calendar_ingestion_reject(db_session, monkeypatch, tmp_path):
    from parser.calendar.api import ParsedAcademicCalendar, ParsedCalendarPeriod
    
    def mock_parse(path):
        return ParsedAcademicCalendar(
            academic_year="2024/2025",
            applicable_levels="1,2,3,4",
            raw_title=None,
            periods=[
                ParsedCalendarPeriod(
                    semester="FIRST SEMESTER",
                    period_name="Academic Session",
                    start_date="27-09-2026",
                    end_date="03-08-2026", # invalid
                    duration_text="08 Weeks",
                    source_page=1,
                    raw_evidence={},
                    verification_status="verified",
                    warnings=[]
                )
            ],
            diagnostics=[],
            report={}
        )
    monkeypatch.setattr("database.ingestion_calendar.parse_academic_calendar", mock_parse)
    
    meta = {
        "title": "Test Title", "document_type": "ACADEMIC_CALENDAR", "sha256": "fakehash"
    }
    
    res = ingest_academic_calendar(db_session, create_mock_pdf(tmp_path), meta)
    assert res.success is False
    assert res.validation_result.status == DocumentGateStatus.REJECT
    assert "Document rejected" in res.error
    
    docs = db_session.query(Document).all()
    assert len(docs) == 0
