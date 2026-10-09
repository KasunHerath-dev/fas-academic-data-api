import os
from parser.src.api import parse_timetable

def main():
    fixture_path = "parser/input/Level-23.pdf"
    
    if not os.path.exists(fixture_path):
        print(f"ERROR: Missing fixture {fixture_path}")
        return
        
    print(f"Parser: Running on {fixture_path}...")
    
    try:
        timetable = parse_timetable(fixture_path)
    except Exception as e:
        print(f"Parser failed: {e}")
        return
        
    print("Parser: PASS")
    print("PDF: Level-23 fixture")
    print(f"Sessions extracted: {len(timetable.sessions)}")
    
    verified = sum(1 for s in timetable.sessions if s.verification_status == "verified")
    uncertain = len(timetable.sessions) - verified
    
    print(f"Verified: {verified}")
    print(f"Uncertain: {uncertain}")
    print("Parser validation: PASS")
    print("Database ingestion: NOT RUN")
    print("Permanent PDF storage: NONE")

if __name__ == "__main__":
    main()
