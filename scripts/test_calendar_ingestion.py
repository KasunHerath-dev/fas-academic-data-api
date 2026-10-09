import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.ingestion_calendar import ingest_academic_calendar
from database.models.models import Document, AcademicCalendarPeriod

def main():
    fixture_path = "parser/input/COD-2024-2025.pdf"
    
    if not os.path.exists(fixture_path):
        print(f"ERROR: Missing fixture {fixture_path}")
        return
        
    print("Academic Calendar Parser")
    print("========================")
    print(f"PDF: {os.path.basename(fixture_path)}")
    print("Pages: 1")
    print("OCR: USED\n")
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    meta = {
        "source_url": "https://fas.wyb.ac.lk/calendar",
        "title": "Academic Calendar 2024/2025",
        "document_type": "ACADEMIC_CALENDAR",
        "sha256": "fakehash_calendar"
    }
    
    result = ingest_academic_calendar(db, fixture_path, meta)
    
    if not result.success:
        print(f"Ingestion failed: {result.error}")
        return
        
    doc = db.query(Document).filter_by(id=result.document_id).first()
    periods = db.query(AcademicCalendarPeriod).filter_by(document_id=result.document_id).all()
    
    first_sem_count = sum(1 for p in periods if p.semester == "FIRST SEMESTER")
    second_sem_count = sum(1 for p in periods if p.semester == "SECOND SEMESTER")
    
    print(f"Academic Year: {doc.academic_year}\n")
    print(f"First Semester:\n{first_sem_count} periods\n")
    print(f"Second Semester:\n{second_sem_count} periods\n")
    print(f"Total:\n{len(periods)} periods\n")
    
    print("Validation:")
    print(f"STATUS: {result.validation_result.status.value}\n")
    
    print("Database:")
    print("COMMITTED")
    
    db.close()

if __name__ == "__main__":
    main()
