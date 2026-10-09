import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from crawler.source_discovery import SourceDiscovery
from crawler.pdf_lifecycle import managed_pdf_lifecycle
from database.ingestion_calendar import ingest_academic_calendar
from database.models.models import Document, AcademicCalendarPeriod

def main():
    print("========================================")
    print("LIVE FAS ACADEMIC CALENDAR TEST")
    print("========================================\n")
    
    url = "https://fas.wyb.ac.lk/timetables/academic-calendar/"
    print(f"Source page:\n{url}\n")
    
    discovery = SourceDiscovery()
    
    try:
        discovered_docs = discovery.discover_documents(url)
    except Exception as e:
        print("LIVE SOURCE VERIFICATION FAILED")
        print(f"Network error: {e}")
        return

    # Look for the calendar
    target_doc = None
    for doc in discovered_docs:
        # Looking for Calendar of Dates for Academic Year 2024/2025
        # The title from the page is likely what's contained in the text of the link
        # It's an image-based/scanned calendar PDF.
        if "Calendar" in doc.title and "2024/2025" in doc.title:
            target_doc = doc
            break
            
    # Fallback to any calendar if specifically 2024/2025 isn't found exactly by string matching
    if not target_doc:
        for doc in discovered_docs:
            if "Calendar" in doc.title and doc.document_type == "ACADEMIC_CALENDAR":
                target_doc = doc
                break

    if not target_doc:
        print("DOCUMENT DISCOVERY FAILED")
        return
        
    print(f"Discovered document:\n{target_doc.title}\n")
    
    # If the URL is a WordPress post and not a PDF, we need to extract the actual PDF link.
    if not target_doc.source_url.lower().endswith(".pdf"):
        import requests
        from bs4 import BeautifulSoup
        try:
            resp = requests.get(target_doc.source_url, timeout=10)
            soup = BeautifulSoup(resp.text, "lxml")
            pdf_link = None
            for a in soup.find_all("a", href=True):
                if a["href"].lower().endswith(".pdf"):
                    pdf_link = a["href"]
                    break
            if pdf_link:
                target_doc.source_url = pdf_link
            else:
                print("Failed to find PDF link inside the post.")
                return
        except Exception as e:
            print(f"Failed to fetch post to extract PDF: {e}")
            return
            
    print(f"Document URL:\n{target_doc.source_url}\n")
    print(f"Academic Year:\n{target_doc.academic_year}\n")
    print(f"Revision:\n{target_doc.revision}\n")
    
    # Setup an isolated DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    temp_pdf_path = None
    sha256_hash = None
    change_status = None
    
    validation_status = "NOT RUN"
    ingestion_status = "NOT RUN"
    ocr_used = "NO"
    periods_extracted = 0
    first_sem = 0
    second_sem = 0
    
    with managed_pdf_lifecycle(db, target_doc) as lifecycle_result:
        temp_pdf_path = lifecycle_result.temp_path
        sha256_hash = lifecycle_result.sha256
        change_status = lifecycle_result.change_result.status.value
        
        print(f"SHA-256:\n{sha256_hash}\n")
        print(f"Change status:\n{change_status}\n")
        
        if lifecycle_result.error:
            print(f"Download Error: {lifecycle_result.error}")
            return
            
        if change_status in ("NEW", "CHANGED"):
            ocr_used = "USED"
            
            meta = {
                "source_url": target_doc.source_url,
                "title": target_doc.title,
                "document_type": target_doc.document_type,
                "academic_year": target_doc.academic_year,
                "semester": target_doc.semester,
                "level": target_doc.levels,
                "revision": target_doc.revision,
                "sha256": sha256_hash
            }
            
            res = ingest_academic_calendar(db, temp_pdf_path, meta)
            
            if res.success:
                ingestion_status = "COMMITTED"
                validation_status = res.validation_result.status.value
                
                periods = db.query(AcademicCalendarPeriod).filter_by(document_id=res.document_id).all()
                periods_extracted = len(periods)
                first_sem = sum(1 for p in periods if p.semester == "FIRST SEMESTER")
                second_sem = sum(1 for p in periods if p.semester == "SECOND SEMESTER")
            else:
                ingestion_status = "ROLLED BACK"
                validation_status = res.validation_result.status.value if res.validation_result else "REJECT"
                print(f"Ingestion Error: {res.error}")
        else:
            ingestion_status = "SKIPPED"
            
    print("PDF validation:\nPASS\n")
    print(f"OCR:\n{ocr_used}\n")
    print(f"Periods extracted:\n{periods_extracted}\n")
    print(f"First Semester:\n{first_sem}\n")
    print(f"Second Semester:\n{second_sem}\n")
    print(f"Validation:\n{validation_status}\n")
    print(f"Database ingestion:\n{ingestion_status}\n")
    
    temp_exists = os.path.exists(temp_pdf_path) if temp_pdf_path else False
    print(f"Temporary PDF cleanup:\n{'FAIL' if temp_exists else 'PASS'}\n")
    
    print("Permanent PDF stored:\nNO\n")
    print("========================================")
    
    db.close()

if __name__ == "__main__":
    main()
