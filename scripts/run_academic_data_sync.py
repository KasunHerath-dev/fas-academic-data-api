import argparse
import sys
import logging
from datetime import datetime, timezone
import traceback

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models.models import SyncRun
from crawler.source_discovery import SourceDiscovery
from crawler.pdf_lifecycle import managed_pdf_lifecycle
from crawler.change_detector import ChangeStatus
from database.ingestion import ingest_timetable_pdf
from database.ingestion_calendar import ingest_academic_calendar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TIMETABLE_URL = "https://fas.wyb.ac.lk/timetables/"
CALENDAR_URL = "https://fas.wyb.ac.lk/timetables/academic-calendar/"

def initialize_sync_run(db: Session, dry_run: bool) -> SyncRun:
    sync_run = SyncRun(
        status="running",
        documents_checked=0,
        documents_changed=0,
        documents_processed=0,
        documents_skipped=0,
        documents_failed=0
    )
    if not dry_run:
        db.add(sync_run)
        db.commit()
        db.refresh(sync_run)
    return sync_run

def finalize_sync_run(db: Session, sync_run: SyncRun, dry_run: bool, status: str, error_summary: str = None):
    sync_run.status = status
    sync_run.completed_at = datetime.now(timezone.utc)
    if error_summary:
        sync_run.error_summary = error_summary
        
    if not dry_run:
        db.add(sync_run)
        db.commit()

def run_sync(dry_run: bool = False):
    db = SessionLocal()
    sync_run = initialize_sync_run(db, dry_run)
    
    crawler = SourceDiscovery()
    discovered_documents = []
    
    try:
        logger.info(f"Discovering timetables from {TIMETABLE_URL}")
        discovered_documents.extend(crawler.discover_documents(TIMETABLE_URL))
        
        logger.info(f"Discovering academic calendars from {CALENDAR_URL}")
        discovered_documents.extend(crawler.discover_documents(CALENDAR_URL))
        
    except Exception as e:
        logger.error(f"Source discovery failed: {e}")
        finalize_sync_run(db, sync_run, dry_run, status="failed", error_summary="Source discovery failed.")
        db.close()
        sys.exit(1)

    sync_run.documents_checked = len(discovered_documents)
    
    for doc in discovered_documents:
        logger.info(f"Processing document: {doc.title} ({doc.url})")
        
        try:
            with managed_pdf_lifecycle(db, doc) as lifecycle_result:
                if lifecycle_result.error:
                    logger.error(f"Lifecycle error for {doc.title}: {lifecycle_result.error}")
                    sync_run.documents_failed += 1
                    continue
                    
                change_result = lifecycle_result.change_result
                if not change_result:
                    logger.error(f"No change result for {doc.title}")
                    sync_run.documents_failed += 1
                    continue
                    
                if change_result.status == ChangeStatus.UNCHANGED:
                    logger.info(f"Document unchanged: {doc.title}")
                    sync_run.documents_skipped += 1
                    continue
                
                sync_run.documents_changed += 1
                
                if dry_run:
                    logger.info(f"[DRY-RUN] Would process {change_result.status.name} document: {doc.title}")
                    sync_run.documents_processed += 1
                    continue
                
                # Ingestion
                metadata = {
                    "source_url": doc.url,
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "academic_year": doc.academic_year,
                    "semester": doc.semester,
                    "level": doc.level,
                    "revision": doc.revision,
                    "sha256": lifecycle_result.sha256
                }
                
                if doc.document_type == "TIMETABLE":
                    ingest_result = ingest_timetable_pdf(db, lifecycle_result.temp_path, metadata)
                elif doc.document_type == "ACADEMIC_CALENDAR":
                    ingest_result = ingest_academic_calendar(db, lifecycle_result.temp_path, metadata)
                else:
                    logger.error(f"Unknown document type {doc.document_type} for {doc.title}")
                    sync_run.documents_failed += 1
                    continue
                
                if ingest_result.success:
                    logger.info(f"Successfully processed {doc.title} (Doc ID: {ingest_result.document_id})")
                    sync_run.documents_processed += 1
                else:
                    logger.error(f"Failed to process {doc.title}: {ingest_result.error}")
                    sync_run.documents_failed += 1
                    
        except Exception as e:
            logger.error(f"Unexpected error processing {doc.title}: {e}")
            sync_run.documents_failed += 1

    final_status = "success"
    if sync_run.documents_failed > 0:
        if sync_run.documents_processed > 0 or sync_run.documents_skipped > 0:
            final_status = "partial"
        else:
            final_status = "failed"
            
    error_summary = None
    if sync_run.documents_failed > 0:
        error_summary = f"{sync_run.documents_failed} documents failed processing."

    finalize_sync_run(db, sync_run, dry_run, status=final_status, error_summary=error_summary)
    
    
    logger.info(f"Sync complete. Status: {final_status}")
    logger.info(f"Checked: {sync_run.documents_checked}, Changed: {sync_run.documents_changed}, Processed: {sync_run.documents_processed}, Skipped: {sync_run.documents_skipped}, Failed: {sync_run.documents_failed}")
    
    # Write summary for GitHub Actions
    summary = f"""
### Sync Run: {final_status.upper()}
- **Documents Discovered/Checked:** {sync_run.documents_checked}
- **Documents Changed:** {sync_run.documents_changed}
- **Documents Skipped:** {sync_run.documents_skipped}
- **Successfully Processed:** {sync_run.documents_processed}
- **Parse/Validation Failures:** {sync_run.documents_failed}
"""
    if error_summary:
        summary += f"\n**Error Summary:** {error_summary}\n"
        
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a") as sf:
                sf.write(summary)
        except:
            pass

    
    db.close()
    
    if final_status == "failed":
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize FAS Academic Data")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to the database")
    args = parser.parse_args()
    
    run_sync(dry_run=args.dry_run)
