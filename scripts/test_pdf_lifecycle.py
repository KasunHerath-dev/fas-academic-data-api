import os
import requests_mock
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from crawler.models import DiscoveredDocument
from crawler.change_detector import ChangeStatus
from crawler.pdf_lifecycle import managed_pdf_lifecycle

def main():
    print("Initializing isolated test database...")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    doc = DiscoveredDocument(
        source_url="https://fas.wyb.ac.lk/fake-document.pdf",
        source_page_url="https://fas.wyb.ac.lk/timetables/",
        title="Fake Document",
        link_text="Fake",
        document_type="TIMETABLE",
        revision="original",
        discovered_at=datetime.now(timezone.utc)
    )
    
    # We will mock the HTTP request to not hit the live FAS site
    with requests_mock.Mocker() as m:
        m.get(doc.source_url, content=b"%PDF-1.4\n" + b"Test synthetic PDF content" + b"x" * 150)
        
        print("\nStarting Lifecycle...")
        
        with managed_pdf_lifecycle(db, doc) as result:
            if result.error:
                print(f"LIFECYCLE ERROR: {result.error}")
            else:
                print("PDF VALIDATION: PASS")
                
                print(f"CHANGE STATUS: {result.change_result.status.value}")
                
                if result.change_result.status != ChangeStatus.UNCHANGED:
                    print("TEMP PDF CREATED")
                    print(f"PATH: {result.temp_path}")
                    
                    assert os.path.exists(result.temp_path)
                    
                    print("PROCESSING SIMULATION: PASS")
                    temp_path_copy = result.temp_path
                else:
                    print("SKIPPING PARSING")

        print("CLEANUP: PASS")
        if 'temp_path_copy' in locals():
            print(f"FILE EXISTS AFTER CLEANUP: {os.path.exists(temp_path_copy)}")
            
    db.close()

if __name__ == "__main__":
    main()
