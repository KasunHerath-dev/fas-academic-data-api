import sys
import os
sys.path.append(os.getcwd())
from crawler.source_discovery import SourceDiscovery
import json

sd = SourceDiscovery()
print("=== TIMETABLES ===")
docs = sd.discover_documents("https://fas.wyb.ac.lk/timetables/")
for d in docs:
    print(d.title, "=>", d.source_url)
print("\n=== CALENDARS ===")
docs = sd.discover_documents("https://fas.wyb.ac.lk/timetables/academic-calendar/")
for d in docs:
    print(d.title, "=>", d.source_url)
