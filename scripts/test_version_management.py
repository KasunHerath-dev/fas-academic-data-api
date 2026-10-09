import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models.models import Document
from database.versioning import get_latest_document, get_document_versions

def main():
    print("Testing Version Management Resolution Strategy...\n")
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 1. Insert Original
    doc1 = Document(
        title="Timetable", document_type="TIMETABLE", academic_year="2023",
        semester="II", level="2", sha256="hash1", status="processed",
        validation_status="SAFE", revision="original",
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=5)
    )
    db.add(doc1)
    
    # 2. Insert Revised
    doc2 = Document(
        title="Timetable", document_type="TIMETABLE", academic_year="2023",
        semester="II", level="2", sha256="hash2", status="processed",
        validation_status="SAFE", revision="revised",
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=3)
    )
    db.add(doc2)
    
    # 3. Insert Re-Revised
    doc3 = Document(
        title="Timetable", document_type="TIMETABLE", academic_year="2023",
        semester="II", level="2", sha256="hash3", status="processed",
        validation_status="SAFE", revision="re-revised",
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.add(doc3)
    db.commit()
    
    # 4. Resolve Latest
    latest = get_latest_document(db, "TIMETABLE", "2023", "II", "2")
    
    print(f"Latest Resolved Revision: {latest.revision} (Expected: re-revised)")
    
    # 5. List all versions
    versions = get_document_versions(db, "TIMETABLE", "2023", "II", "2")
    print(f"Total historical versions preserved: {len(versions)}")
    
    print("\nHistorical Lineage:")
    for v in versions:
        print(f" - Revision: {v.revision}, SHA: {v.sha256}, ID: {v.id}")
        
    db.close()

if __name__ == "__main__":
    main()
