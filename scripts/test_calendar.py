import sys
import os
sys.path.append(os.getcwd())
from parser.calendar.ocr_extractor import extract_calendar_data
from parser.calendar.validator import CalendarValidator

result = extract_calendar_data("parser/input/COD-2024-2025.pdf")

validator = CalendarValidator()
val_result = validator.validate_calendar(result)

print("ACADEMIC YEAR:", result.academic_year)
print("LEVELS:", result.applicable_levels)
print("VALIDATION:", val_result.status.value if hasattr(val_result.status, 'value') else val_result.status)
for p in result.periods:
    print(f"Period: {p.period_name} | {p.start_date} -> {p.end_date} | {p.semester} | warnings: {p.warnings}")
