import os
import tempfile
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document
from crawler.models import DiscoveredDocument
from crawler.change_detector import ChangeDetector
from crawler.hasher import calculate_sha256

def main():
    print("Initializing isolated test database for demonstration...")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    detector = ChangeDetector(db)
    
    # Fake discovered document
    doc_info = DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/test-url/",
        source_page_url="https://fas.wyb.ac.lk/timetables/",
        title="Test Time Table",
        link_text="Test",
        document_type="TIMETABLE",
        revision="original",
        discovered_at=datetime.now(timezone.utc)
    )
    
    def simulate_temp_pdf(content: bytes):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            return f.name
            
    print("\n--- TEST 1: NEW DOCUMENT ---")
    temp1 = simulate_temp_pdf(b"PDF Content Version 1")
    sha1 = calculate_sha256(temp1)
    os.remove(temp1)
    
    result1 = detector.detect(doc_info, sha1)
    print(f"URL: {doc_info.source_url}")
    print(f"SHA: {sha1}")
    print(f"Result: {result1.status.value}")
    
    # Ingest it
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
    print("-> Document saved to database.")

    print("\n--- TEST 2: UNCHANGED DOCUMENT ---")
    temp2 = simulate_temp_pdf(b"PDF Content Version 1") # Exact same content
    sha2 = calculate_sha256(temp2)
    os.remove(temp2)
    
    result2 = detector.detect(doc_info, sha2)
    print(f"URL: {doc_info.source_url}")
    print(f"SHA: {sha2}")
    print(f"Result: {result2.status.value}")
    print("-> Document unchanged. Skip processing.")

    print("\n--- TEST 3: CHANGED DOCUMENT ---")
    temp3 = simulate_temp_pdf(b"PDF Content Version 2") # Content changed!
    sha3 = calculate_sha256(temp3)
    os.remove(temp3)
    
    result3 = detector.detect(doc_info, sha3)
    print(f"URL: {doc_info.source_url}")
    print(f"SHA: {sha3}")
    print(f"Result: {result3.status.value}")
    
    # Ingest new version
    db_doc2 = Document(
        source_url=doc_info.source_url,
        title=doc_info.title,
        document_type=doc_info.document_type,
        revision=doc_info.revision,
        sha256=sha3,
        status="processed"
    )
    db.add(db_doc2)
    db.commit()
    print("-> New Document version saved to database.")
    
    print("\n--- TEST 4: PRESERVED HISTORY ---")
    docs = db.query(Document).filter_by(source_url=doc_info.source_url).all()
    print(f"Total historical versions retained for URL: {len(docs)}")
    for d in docs:
        print(f"ID: {d.id} | SHA: {d.sha256} | Revision: {d.revision}")
        
    db.close()
    print("\nDemonstration complete. No actual PDFs were kept.")

if __name__ == "__main__":
    main()
