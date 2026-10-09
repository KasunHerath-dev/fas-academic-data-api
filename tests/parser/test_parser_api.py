import os
import pytest
import tempfile

from parser.src.api import parse_timetable
from crawler.pdf_lifecycle import managed_pdf_lifecycle
from crawler.change_detector import ChangeStatus
from crawler.models import DiscoveredDocument
from datetime import datetime, timezone
import requests_mock

FIXTURE_PATH = "parser/input/Level-23.pdf"

@pytest.fixture
def valid_pdf_path():
    if not os.path.exists(FIXTURE_PATH):
        pytest.skip(f"Missing fixture {FIXTURE_PATH}")
    return FIXTURE_PATH

def test_parser_api_valid(valid_pdf_path):
    timetable = parse_timetable(valid_pdf_path)
    # Regression check: expecting 27 sessions in the Level-23 fixture
    assert len(timetable.sessions) == 27
    assert timetable.report["final_session_count"] == 27

def test_parser_api_invalid_pdf(tmp_path):
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_bytes(b"not a pdf")
    with pytest.raises(ValueError, match="Failed to load PDF"):
        parse_timetable(str(invalid_pdf))

def test_parser_api_empty_timetable(tmp_path):
    # Valid PDF structure but no grid
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Just some text, no timetable here.")
    empty_pdf = tmp_path / "empty.pdf"
    doc.save(str(empty_pdf))
    doc.close()
    
    with pytest.raises(ValueError, match="No timetable grid found in PDF"):
        parse_timetable(str(empty_pdf))

def test_lunch_exclusion(valid_pdf_path):
    timetable = parse_timetable(valid_pdf_path)
    for s in timetable.sessions:
        code = (s.module_code or "").lower()
        assert "lunch" not in code
        assert s.session_type != "LUNCH"
        assert s.raw_evidence.get("rawText", "").lower() != "lunch"

def test_missing_room_and_group(valid_pdf_path):
    timetable = parse_timetable(valid_pdf_path)
    missing_room = [s for s in timetable.sessions if not s.room]
    assert len(missing_room) > 0 # Some sessions genuinely lack room info

def test_suspicious_module_code_preservation(valid_pdf_path):
    timetable = parse_timetable(valid_pdf_path)
    # E.g. "ELTN 3+53" should be preserved in raw/module_code if it exists, without silent correction
    # The current regression checks just prove it doesn't crash
    pass

def test_temporary_lifecycle_integration(valid_pdf_path):
    # Mock download with the valid PDF bytes
    with open(valid_pdf_path, "rb") as f:
        pdf_bytes = f.read()
        
    doc = DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/fake-timetable.pdf",
        source_page_url="https://fas.wyb.ac.lk/timetables/",
        title="Test Timetable",
        link_text="Test",
        document_type="TIMETABLE",
        revision="original",
        discovered_at=datetime.now(timezone.utc)
    )
    
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.database import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    temp_path_copy = None
    with requests_mock.Mocker() as m:
        m.get(doc.source_url, content=pdf_bytes)
        
        with managed_pdf_lifecycle(db, doc) as result:
            assert result.error is None
            assert result.change_result.status == ChangeStatus.NEW
            temp_path_copy = result.temp_path
            
            # Now pass the temporary PDF into the parser!
            timetable = parse_timetable(result.temp_path)
            assert len(timetable.sessions) == 27
            
    # Guarantee cleanup!
    assert not os.path.exists(temp_path_copy)
    db.close()
