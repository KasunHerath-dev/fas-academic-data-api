import os
import json
from parser.src.api import parse_timetable
from parser.src.validator import TimetableValidator

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
        
    validator = TimetableValidator()
    doc_result = validator.validate_timetable(timetable)
    
    print("\nDocument validation:")
    print(f"STATUS: {doc_result.status.value}\n")
    
    print(f"Total sessions: {doc_result.total_sessions}")
    print(f"Valid: {doc_result.valid_sessions}")
    print(f"Uncertain: {doc_result.uncertain_sessions}")
    print(f"Invalid: {doc_result.invalid_sessions}\n")
    
    if doc_result.warnings:
        print("Warnings:")
        for w in doc_result.warnings:
            print(f"  - {w}")
            
    if doc_result.errors:
        print("\nErrors:")
        for e in doc_result.errors:
            print(f"  - {e}")

if __name__ == "__main__":
    main()
