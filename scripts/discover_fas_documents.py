import sys
from crawler.source_discovery import SourceDiscovery

def main():
    urls = [
        "https://fas.wyb.ac.lk/timetables/",
        "https://fas.wyb.ac.lk/timetables/academic-calendar/"
    ]
    
    discovery = SourceDiscovery()
    
    all_documents = []
    
    for url in urls:
        print(f"Discovering documents from: {url}")
        docs = discovery.discover_documents(url)
        all_documents.extend(docs)
        
    print("\n--- Discovery Report ---\n")
    
    total = len(all_documents)
    timetables = sum(1 for d in all_documents if d.document_type == "TIMETABLE")
    calendars = sum(1 for d in all_documents if d.document_type == "ACADEMIC_CALENDAR")
    unknown = sum(1 for d in all_documents if not d.document_type)
    
    print(f"Total links discovered: {total}")
    print(f"Timetable documents: {timetables}")
    print(f"Academic calendar documents: {calendars}")
    print(f"Other/ignored links (no metadata): {unknown}\n")
    
    # Print the documents
    for d in all_documents:
        print(f"Title: {d.title}")
        print(f"  URL: {d.source_url}")
        print(f"  Type: {d.document_type}")
        print(f"  Academic Year: {d.academic_year}")
        print(f"  Semester: {d.semester}")
        print(f"  Levels: {d.levels}")
        print(f"  Revision: {d.revision}")
        print("-" * 50)
        
if __name__ == "__main__":
    main()
