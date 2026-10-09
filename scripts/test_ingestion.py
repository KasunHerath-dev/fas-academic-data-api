import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.ingestion import ingest_timetable_pdf
from database.models.models import Document, TimetableSession

def main():
    fixture_path = "parser/input/Level-23.pdf"
    
    if not os.path.exists(fixture_path):
        print(f"ERROR: Missing fixture {fixture_path}")
        return
        
    print(f"Ingestion: Running on {fixture_path}...")
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    meta = {
        "source_url": "https://fas.wyb.ac.lk/level-23",
        "title": "Level-23 Timetable",
        "document_type": "TIMETABLE",
        "academic_year": "2023/2024",
        "semester": "II",
        "level": "2,3",
        "sha256": "fakehash_for_test"
    }
    
    result = ingest_timetable_pdf(db, fixture_path, meta)
    
    if not result.success:
        print(f"Ingestion failed: {result.error}")
        return
        
    print("\nIngestion Result:")
    print(f"STATUS: {result.validation_result.status.value}")
    
    doc = db.query(Document).filter_by(id=result.document_id).first()
    print(f"Database Document validation_status: {doc.validation_status}")
    
    sessions = db.query(TimetableSession).filter_by(document_id=result.document_id).all()
    print(f"Total sessions inserted: {len(sessions)}")
    
    valid_sessions = sum(1 for s in sessions if s.verification_status == "valid")
    uncertain_sessions = sum(1 for s in sessions if s.verification_status == "uncertain")
    
    print(f"Valid: {valid_sessions}")
    print(f"Uncertain: {uncertain_sessions}")
    
    print("\nSample Uncertain Session Warnings preserved in DB:")
    for s in sessions:
        if s.verification_status == "uncertain" and s.warnings:
            print(f"Module: {s.module_code} | Warnings: {s.warnings}")
            break
            
    db.close()

if __name__ == "__main__":
    main()
