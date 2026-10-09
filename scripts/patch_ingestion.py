import sys
import os
sys.path.append(os.getcwd())

with open("database/ingestion.py", "r") as f:
    content = f.read()

import_statement = "from database.models.models import Document, TimetableSession, AcademicYear, Semester, Level, Major, Programme"
content = content.replace("from database.models.models import Document, TimetableSession", import_statement)

get_or_create = """
def get_or_create_lookup(db, model, field, value):
    if not value: return None
    obj = db.query(model).filter(getattr(model, field) == value).first()
    if not obj:
        obj = model(**{field: value})
        db.add(obj)
        db.flush()
    return obj
"""

if "def get_or_create_lookup" not in content:
    content = content.replace("def ingest_timetable_pdf", get_or_create + "\ndef ingest_timetable_pdf")

insert_lookups = """
        get_or_create_lookup(db, AcademicYear, "year_string", doc.academic_year)
        get_or_create_lookup(db, Semester, "semester_string", doc.semester)
        get_or_create_lookup(db, Level, "level_string", doc.level)
        get_or_create_lookup(db, Major, "major_string", doc.major)
        get_or_create_lookup(db, Programme, "programme_string", doc.programme)
"""

if "get_or_create_lookup(db, AcademicYear" not in content:
    content = content.replace("db.add(doc)\n        db.flush() # get doc.id", "db.add(doc)\n        db.flush() # get doc.id\n" + insert_lookups)

with open("database/ingestion.py", "w") as f:
    f.write(content)
