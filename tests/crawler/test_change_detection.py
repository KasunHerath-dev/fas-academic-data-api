import os
import tempfile
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document, TimetableSession
from crawler.models import DiscoveredDocument
from crawler.change_detector import ChangeDetector, ChangeStatus
from crawler.hasher import calculate_sha256, calculate_sha256_from_bytes

def test_hasher():
    data = b"fake pdf content"
    hash1 = calculate_sha256_from_bytes(data)
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(data)
        temp_path = f.name
        
    try:
        hash2 = calculate_sha256(temp_path)
        assert hash1 == hash2
        assert len(hash1) == 64
    finally:
        os.remove(temp_path)

def test_change_detection_flow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    detector = ChangeDetector(db)
    
    # 1. New document
    doc_info = DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/fake-timetable/",
        source_page_url="https://fas.wyb.ac.lk/timetables/",
        title="Time Table",
        link_text="Time Table",
        document_type="TIMETABLE",
        revision="original",
        discovered_at=datetime.now(timezone.utc)
    )
    
    sha1 = calculate_sha256_from_bytes(b"content v1")
    result1 = detector.detect(doc_info, sha1)
    assert result1.status == ChangeStatus.NEW
    
    # Simulate DB insert
    db_doc1 = Document(
        source_url=doc_info.source_url,
        title=doc_info.title,
        document_type=doc_info.document_type,
        revision=doc_info.revision,
        sha256=sha1,
        status="processed"
    )
    db.add(db_doc1)
    db.commit()
    
    # 2. Existing unchanged (Same URL, same SHA)
    result2 = detector.detect(doc_info, sha1)
    assert result2.status == ChangeStatus.UNCHANGED
    assert result2.previous_document.id == db_doc1.id
    
    # 3. Same URL but different SHA -> CHANGED
    sha2 = calculate_sha256_from_bytes(b"content v2")
    result3 = detector.detect(doc_info, sha2)
    assert result3.status == ChangeStatus.CHANGED
    assert result3.previous_document.id == db_doc1.id
    
    # Simulate DB insert of new version
    db_doc2 = Document(
        source_url=doc_info.source_url,
        title=doc_info.title,
        document_type=doc_info.document_type,
        revision=doc_info.revision,
        sha256=sha2,
        status="processed"
    )
    db.add(db_doc2)
    db.commit()
    
    # Add a TimetableSession linked to original doc (Lineage test)
    ts = TimetableSession(
        document_id=db_doc1.id,
        day="Monday",
        start_time="08:00",
        end_time="10:00",
        time_source="explicit",
        verification_status="verified"
    )
    db.add(ts)
    db.commit()
    
    # 4. Old document remains unchanged, lineage preserved
    assert ts.document_id == db_doc1.id
    assert db_doc1.sha256 == sha1 # Old sha is preserved
    
    # 5. Original + Revised coexist
    doc_info_revised = DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/fake-timetable/",
        source_page_url="https://fas.wyb.ac.lk/timetables/",
        title="Revised Time Table",
        link_text="Revised",
        document_type="TIMETABLE",
        revision="revised",
        discovered_at=datetime.now(timezone.utc)
    )
    sha3 = calculate_sha256_from_bytes(b"content v3 revised")
    result4 = detector.detect(doc_info_revised, sha3)
    assert result4.status == ChangeStatus.NEW # Since revision is 'revised', no matching URL+revision found yet
    
    db_doc3 = Document(
        source_url=doc_info_revised.source_url,
        title=doc_info_revised.title,
        document_type=doc_info_revised.document_type,
        revision=doc_info_revised.revision,
        sha256=sha3,
        status="processed"
    )
    db.add(db_doc3)
    db.commit()
    
    # 6. Re-revised coexistence
    doc_info_rerevised = doc_info_revised.model_copy(update={"revision": "re-revised", "title": "Re-Revised"})
    sha4 = calculate_sha256_from_bytes(b"content v4 re-revised")
    result5 = detector.detect(doc_info_rerevised, sha4)
    assert result5.status == ChangeStatus.NEW
    
    db_doc4 = Document(
        source_url=doc_info_rerevised.source_url,
        title=doc_info_rerevised.title,
        document_type=doc_info_rerevised.document_type,
        revision=doc_info_rerevised.revision,
        sha256=sha4,
        status="processed"
    )
    db.add(db_doc4)
    db.commit()
    
    # Ensure they all coexist safely
    all_docs = db.query(Document).all()
    assert len(all_docs) == 4
    
    db.close()
