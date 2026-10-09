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
    mock_crawler.discover_documents.return_value = []
    
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
    mock_crawler.discover_documents.return_value = []
    
    run_sync(dry_run=True)
    
    db = TestingSessionLocal()
    runs = db.query(SyncRun).all()
    assert len(runs) == 0  # No records written in dry-run
