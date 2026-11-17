import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import Base
from database.models.models import SyncRun
from scripts.run_academic_data_sync import run_sync, initialize_sync_run, finalize_sync_run

# Setup test DB
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@patch("scripts.run_academic_data_sync.SessionLocal", return_value=TestingSessionLocal())
@patch("scripts.run_academic_data_sync.SourceDiscovery")
def test_sync_no_documents(mock_crawler_class, mock_session_local):
    mock_crawler = mock_crawler_class.return_value
    mock_crawler.discover_all.return_value = []
    
    run_sync(dry_run=False)
    
    db = TestingSessionLocal()
    runs = db.query(SyncRun).all()
    assert len(runs) == 1
    assert runs[0].status == "success"
    assert runs[0].documents_checked == 0
    assert runs[0].documents_changed == 0
    assert runs[0].documents_skipped == 0
    assert runs[0].documents_processed == 0
    assert runs[0].documents_failed == 0

@patch("scripts.run_academic_data_sync.SessionLocal", return_value=TestingSessionLocal())
@patch("scripts.run_academic_data_sync.SourceDiscovery")
def test_sync_dry_run_no_writes(mock_crawler_class, mock_session_local):
    mock_crawler = mock_crawler_class.return_value
    mock_crawler.discover_all.return_value = []
    
    run_sync(dry_run=True)
    
    db = TestingSessionLocal()
    runs = db.query(SyncRun).all()
    assert len(runs) == 0  # No records written in dry-run


@patch("scripts.run_academic_data_sync.ingest_timetable_pdf")
@patch("scripts.run_academic_data_sync.managed_pdf_lifecycle")
@patch("scripts.run_academic_data_sync.SessionLocal", return_value=TestingSessionLocal())
@patch("scripts.run_academic_data_sync.SourceDiscovery")
def test_sync_processes_real_discovered_document(mock_crawler_class, mock_session_local, mock_lifecycle, mock_ingest):
    """
    Regression: run_sync read doc.url and doc.level, which DiscoveredDocument does not
    have, so every real sync crashed before ingesting anything.
    """
    from contextlib import contextmanager
    from datetime import datetime, timezone
    from crawler.models import DiscoveredDocument
    from crawler.change_detector import ChangeStatus, ChangeResult
    from crawler.pdf_lifecycle import LifecycleResult
    from database.models.models import Module

    doc = DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/wp-content/uploads/L23.pdf",
        source_page_url="https://fas.wyb.ac.lk/notice/",
        title="Revised – Academic Time Table – Level 2 & 3 Semester I (2024/2025)",
        link_text="Level 2 & 3",
        document_type="TIMETABLE",
        academic_year="2024/2025",
        semester="I",
        levels=[2, 3],
        revision="revised",
        discovered_at=datetime.now(timezone.utc),
    )
    mock_crawler_class.return_value.discover_all.return_value = [doc]

    @contextmanager
    def fake_lifecycle(db, d):
        yield LifecycleResult(temp_path="/tmp/x.pdf", change_result=ChangeResult(ChangeStatus.NEW), sha256="abc")

    mock_lifecycle.side_effect = fake_lifecycle
    mock_ingest.return_value = MagicMock(success=True, document_id=1)

    run_sync(dry_run=False)

    metadata = mock_ingest.call_args[0][2]
    assert metadata["source_url"] == doc.source_url
    assert metadata["level"] == "2,3"
    assert metadata["sha256"] == "abc"

    db = TestingSessionLocal()
    run = db.query(SyncRun).one()
    assert run.status == "success"
    assert run.documents_processed == 1
    # the module catalogue is synced into the modules table
    assert db.query(Module).filter_by(module_code="CMIS 4142").one().module_name == "Image Processing"
