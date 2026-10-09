import sys
import os
import json
sys.path.append(os.getcwd())
from parser.src.api import parse_timetable
from parser.src.validator import TimetableValidator

result = parse_timetable("parser/input/Level-23.pdf")

validator = TimetableValidator()
val_result = validator.validate_timetable(result)

print("VALIDATION:", val_result.status.value if hasattr(val_result.status, 'value') else val_result.status)
print("SESSIONS EXTRACTED:", len(result.sessions))
for s in result.sessions[:5]:
    print(s.day, s.start_time, s.end_time, s.module_code, s.room)
