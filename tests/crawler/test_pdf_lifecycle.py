import os
import pytest
import requests_mock
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document
from crawler.models import DiscoveredDocument
from crawler.change_detector import ChangeStatus
from crawler.downloader import validate_pdf_magic_bytes, download_temporary_pdf, DownloadException
from crawler.pdf_lifecycle import managed_pdf_lifecycle

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()

@pytest.fixture
def sample_discovered():
    return DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/test.pdf",
        source_page_url="https://fas.wyb.ac.lk/timetables/",
        title="Test Document",
        link_text="Test",
        document_type="TIMETABLE",
        revision="original",
        discovered_at=datetime.now(timezone.utc)
    )

def test_validate_magic_bytes(tmp_path):
    pdf_file = tmp_path / "valid.pdf"
    # Provide enough bytes to pass the size check as well for testing
    pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 150)
    assert validate_pdf_magic_bytes(str(pdf_file)) is True

    bad_file = tmp_path / "invalid.pdf"
    bad_file.write_bytes(b"<!DOCTYPE html>\n<html>" + b"x" * 150)
    assert validate_pdf_magic_bytes(str(bad_file)) is False

def test_download_html_rejection():
    with requests_mock.Mocker() as m:
        m.get("https://test.com/bad.pdf", text="<html><body>fake pdf</body></html>", headers={"Content-Type": "text/html"})
        with pytest.raises(DownloadException, match="HTML instead of PDF"):
            download_temporary_pdf("https://test.com/bad.pdf")

def test_download_empty_rejection():
    with requests_mock.Mocker() as m:
        m.get("https://test.com/empty.pdf", content=b"")
        with pytest.raises(DownloadException, match="PDF magic-bytes"):
            download_temporary_pdf("https://test.com/empty.pdf")

def test_download_non_pdf_rejection():
    with requests_mock.Mocker() as m:
        m.get("https://test.com/image.pdf", content=b"fake image data that is large enough" + b"x" * 150)
        with pytest.raises(DownloadException, match="magic-bytes"):
            download_temporary_pdf("https://test.com/image.pdf")

def test_download_size_limit():
    with requests_mock.Mocker() as m:
        # Simulate a 21MB response
        m.get("https://test.com/large.pdf", content=b"0" * (21 * 1024 * 1024))
        with pytest.raises(DownloadException, match="size exceeded"):
            download_temporary_pdf("https://test.com/large.pdf")

def test_download_http_error():
    with requests_mock.Mocker() as m:
        m.get("https://test.com/404.pdf", status_code=404)
        with pytest.raises(DownloadException, match="404 Client Error"):
            download_temporary_pdf("https://test.com/404.pdf")

def test_managed_lifecycle_new_document(db_session, sample_discovered):
    with requests_mock.Mocker() as m:
        m.get(sample_discovered.source_url, content=b"%PDF-1.4\n" + b"x" * 150)
        
        with managed_pdf_lifecycle(db_session, sample_discovered) as result:
            assert result.error is None
            assert result.change_result.status == ChangeStatus.NEW
            assert result.temp_path is not None
            assert os.path.exists(result.temp_path)
            temp_path_copy = result.temp_path
            
        # Ensure cleanup happened after processing
        assert not os.path.exists(temp_path_copy)

def test_managed_lifecycle_unchanged_document(db_session, sample_discovered):
    from crawler.hasher import calculate_sha256_from_bytes
    pdf_content = b"%PDF-1.4\n" + b"x" * 150
    sha256 = calculate_sha256_from_bytes(pdf_content)
    
    # Pre-populate db
    doc = Document(
        source_url=sample_discovered.source_url,
        title=sample_discovered.title,
        document_type=sample_discovered.document_type,
        revision=sample_discovered.revision,
        sha256=sha256,
        status="processed"
    )
    db_session.add(doc)
    db_session.commit()
    
    with requests_mock.Mocker() as m:
        m.get(sample_discovered.source_url, content=pdf_content)
        
        with managed_pdf_lifecycle(db_session, sample_discovered) as result:
            assert result.error is None
            assert result.change_result.status == ChangeStatus.UNCHANGED
            assert result.temp_path is None # Deleted immediately

def test_managed_lifecycle_exception_during_processing_cleans_up(db_session, sample_discovered):
    temp_path_copy = None
    with requests_mock.Mocker() as m:
        m.get(sample_discovered.source_url, content=b"%PDF-1.4\n" + b"x" * 150)
        
        try:
            with managed_pdf_lifecycle(db_session, sample_discovered) as result:
                assert result.temp_path is not None
                assert os.path.exists(result.temp_path)
                temp_path_copy = result.temp_path
                raise ValueError("Simulated parsing error")
        except ValueError:
            pass
            
    # Cleanup should still happen
    assert temp_path_copy is not None
    assert not os.path.exists(temp_path_copy)
