import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from database.database import Base
from database.models.models import Document, TimetableSession, SyncRun

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)

def verify():
    # 3. VERIFY NEON ACTUAL SCHEMA
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Actual Tables:", tables)
    
    expected = [
        "academic_years", "semesters", "levels", "majors", "programmes",
        "modules", "documents", "timetable_sessions", "academic_calendar_periods", "sync_runs"
    ]
    for e in expected:
        if e not in tables:
            print(f"MISSING TABLE: {e}")
            
    # 5. VERIFY DOCUMENT MODEL
    doc_cols = {c['name']: c for c in inspector.get_columns('documents')}
    print("\nDocument Columns:")
    for name in ["source_url", "title", "document_type", "academic_year", "semester", "level", "major", "programme", "published_at", "revision", "sha256", "status", "first_seen_at", "last_seen_at", "processed_at"]:
        print(f"  {name}: {doc_cols.get(name, {}).get('type')}")
        
    # 4. VERIFY SyncRun
    sync_cols = {c['name']: c for c in inspector.get_columns('sync_runs')}
    print("\nSyncRun Columns:")
    for name in ["id", "started_at", "completed_at", "status", "documents_checked", "documents_changed", "documents_processed", "documents_skipped", "documents_failed", "error_summary"]:
        print(f"  {name}: {sync_cols.get(name, {}).get('type')}")

    # 6. VERIFY DOCUMENT VERSIONING & 7. VERIFY SHA-256 & 8. VERIFY SESSION LINEAGE & 9. VERIFY NULLABLE ACADEMIC DATA
    session = SessionLocal()
    
    try:
        # Document A
        docA = Document(
            title="Test Doc A",
            document_type="TIMETABLE",
            revision="original",
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="processed"
        )
        
        # Document B
        docB = Document(
            title="Test Doc B",
            document_type="TIMETABLE",
            revision="revised",
            sha256="test_hash_B_full_size_64_characters_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            status="processed"
        )
        
        session.add(docA)
        session.add(docB)
        session.commit()
        
        # Lineage & Nullable Data
        sessA = TimetableSession(
            document_id=docA.id,
            day="Monday",
            start_time="08:30",
            end_time="10:30",
            time_source="explicit",
            verification_status="uncertain"
        )
        sessB = TimetableSession(
            document_id=docB.id,
            day="Tuesday",
            start_time="10:30",
            end_time="12:30",
            time_source="inferred",
            verification_status="verified",
            room=None,
            group=None,
            major=None
        )
        
        session.add(sessA)
        session.add(sessB)
        session.commit()
        
        print(f"\nDocument A ID: {docA.id}, SHA: {docA.sha256}")
        print(f"Document B ID: {docB.id}, SHA: {docB.sha256}")
        print(f"Session A linked to Doc: {sessA.document_id}")
        print(f"Session B linked to Doc: {sessB.document_id}")
        
    except Exception as e:
        print("Error during test inserts:", e)
    finally:
        # Cleanup
        session.execute(text("DELETE FROM timetable_sessions WHERE document_id IN (SELECT id FROM documents WHERE title LIKE 'Test Doc%')"))
        session.execute(text("DELETE FROM documents WHERE title LIKE 'Test Doc%'"))
        session.commit()
        print("\nCleanup completed.")
        session.close()

if __name__ == '__main__':
    verify()
