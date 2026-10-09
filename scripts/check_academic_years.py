import sys
import os
from sqlalchemy import create_engine, select
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from database.database import SessionLocal
from database.models.models import AcademicYear, Document, TimetableSession
db = SessionLocal()
print("Academic Years count:", db.query(AcademicYear).count())
print("Documents count:", db.query(Document).count())
print("Sessions count:", db.query(TimetableSession).count())
