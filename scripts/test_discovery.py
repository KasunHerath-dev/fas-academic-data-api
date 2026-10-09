import sys
import os
sys.path.append(os.getcwd())
from crawler.source_discovery import SourceDiscovery

sd = SourceDiscovery()
print("=== TIMETABLES ===")
docs = sd.discover_documents("https://fas.wyb.ac.lk/timetables/")
for d in docs:
    print(f"Title: {d.title}")
    print(f"  PDF URL: {d.source_url}")
    print(f"  Source Post URL: {d.source_page_url}")
    print(f"  Doc Type: {d.document_type}")
    print(f"  Academic Year: {d.academic_year}")
    print(f"  Semester: {d.semester}")
    print(f"  Level: {d.levels}")
    print(f"  Revision: {d.revision}")
    print(f"  Published At: {d.published_at}")
print("\n=== CALENDARS ===")
docs = sd.discover_documents("https://fas.wyb.ac.lk/timetables/academic-calendar/")
for d in docs:
    print(f"Title: {d.title}")
    print(f"  PDF URL: {d.source_url}")
    print(f"  Source Post URL: {d.source_page_url}")
    print(f"  Doc Type: {d.document_type}")
    print(f"  Academic Year: {d.academic_year}")
    print(f"  Semester: {d.semester}")
    print(f"  Level: {d.levels}")
    print(f"  Revision: {d.revision}")
    print(f"  Published At: {d.published_at}")
