import sys
import os
sys.path.append(os.getcwd())
import json

from parser.src.api import parse_timetable
from parser.src.validator import TimetableValidator
from parser.calendar.ocr_extractor import extract_calendar_data
from parser.calendar.validator import CalendarValidator

timetables = ["Level-13.pdf", "Level-23.pdf", "Level-34.pdf", "Level-45.pdf"]
calendar = "COD-2024-2025.pdf"

tt_val = TimetableValidator()
cal_val = CalendarValidator()

print("================ TIMETABLE VERIFICATION ================")
for tt in timetables:
    path = f"docs/{tt}"
    print(f"\\n--- Processing {tt} ---")
    try:
        res = parse_timetable(path)
        vr = tt_val.validate_timetable(res)

        status = vr.status.value if hasattr(vr.status, 'value') else vr.status
        print(f"Extraction count: {len(res.sessions)}")
        print(f"Verified: {vr.valid_sessions}, Uncertain: {vr.uncertain_sessions}, Rejected: {vr.invalid_sessions}")
        print(f"Detected levels: {getattr(res, 'levels', 'N/A')}")
        print(f"Validation Status: {status}")

        # Check extraction details
        groups = sum(1 for s in res.sessions if s.group)
        modules = sum(1 for s in res.sessions if s.module_code)
        rooms = sum(1 for s in res.sessions if s.room)
        print(f"Groups correctly extracted: {groups}/{len(res.sessions)}")
        print(f"Modules correctly extracted: {modules}/{len(res.sessions)}")
        print(f"Rooms correctly extracted: {rooms}/{len(res.sessions)}")

        print("Warnings:")
        for w in vr.warnings:
            print("  -", w)
        if vr.errors:
            print("Errors:")
            for e in vr.errors:
                print("  -", e)
    except Exception as e:
        print(f"FAILED to parse {tt}: {e}")

print("\\n================ CALENDAR VERIFICATION ================")
print(f"\\n--- Processing {calendar} ---")
try:
    c_res = extract_calendar_data(f"docs/{calendar}")
    c_vr = cal_val.validate_calendar(c_res)

    status = c_vr.status.value if hasattr(c_vr.status, 'value') else c_vr.status
    print(f"Extraction count: {len(c_res.periods)}")
    print(f"Printed Academic Year: {c_res.academic_year}")
    print(f"Validation Status: {status}")
    print("Periods:")
    for p in c_res.periods:
        print(f"  {p.period_name} | {p.start_date} to {p.end_date} | {p.semester} | warnings: {p.warnings}")
    print("Warnings:")
    for w in c_vr.warnings:
        print("  -", w)
except Exception as e:
    print(f"FAILED to parse {calendar}: {e}")
