from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, nullable=True)
    title = Column(String, nullable=False)
    document_type = Column(String, nullable=False, index=True) # e.g. TIMETABLE, ACADEMIC_CALENDAR
    academic_year = Column(String, nullable=True, index=True)
    semester = Column(String, nullable=True)
    level = Column(String, nullable=True)
    major = Column(String, nullable=True)
    programme = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    # document_date deferred — no reliable end-to-end extraction implemented yet
    revision = Column(String, nullable=True) # e.g., original, revised, re-revised
    sha256 = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False) # e.g., processing, processed, failed, superseded
    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    validation_status = Column(String, nullable=True) # SAFE, REVIEW_REQUIRED, REJECT
    validation_metadata = Column(JSON, nullable=True) # stores document-level warnings and errors

    sessions = relationship("TimetableSession", back_populates="document")
    # periods = relationship("AcademicCalendarPeriod", back_populates="document")

class TimetableSession(Base):
    __tablename__ = "timetable_sessions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    academic_year = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    level = Column(String, nullable=True)
    major = Column(String, nullable=True)
    programme = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    module_code = Column(String, nullable=True, index=True)
    raw_module_code = Column(String, nullable=True)
    day = Column(String, nullable=False, index=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    class_type = Column(String, nullable=True) # L, P, T
    group = Column(String, nullable=True)
    raw_group = Column(String, nullable=True)
    room = Column(String, nullable=True)
    raw_room = Column(String, nullable=True)
    time_source = Column(String, nullable=False) # explicit, inferred
    time_inference_reason = Column(String, nullable=True)
    verification_status = Column(String, nullable=False) # verified, uncertain
    confidence = Column(Integer, nullable=True)
    source_page = Column(Integer, nullable=True)
    source_cells = Column(JSON, nullable=True)
    raw_evidence = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)

    document = relationship("Document", back_populates="sessions")

class AcademicCalendarPeriod(Base):
    __tablename__ = "academic_calendar_periods"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    activity_name = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    duration_weeks = Column(Integer, nullable=True)
    duration_text = Column(String, nullable=True)
    academic_year = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    verification_status = Column(String, nullable=False, default="verified")
    warnings = Column(JSON, nullable=True)
    raw_evidence = Column(JSON, nullable=True)
    source_page = Column(Integer, nullable=True)


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    module_code = Column(String, unique=True, nullable=False, index=True)
    module_name = Column(String, nullable=True)
    level = Column(String, nullable=True)
    major = Column(String, nullable=True)
    programme = Column(String, nullable=True)
    specialization = Column(String, nullable=True)

class AcademicYear(Base):
    __tablename__ = "academic_years"
    
    id = Column(Integer, primary_key=True, index=True)
    year_string = Column(String, unique=True, nullable=False)

class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    semester_string = Column(String, unique=True, nullable=False)

class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    level_string = Column(String, unique=True, nullable=False)

class Major(Base):
    __tablename__ = "majors"

    id = Column(Integer, primary_key=True, index=True)
    major_string = Column(String, unique=True, nullable=False)

class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    programme_string = Column(String, unique=True, nullable=False)

class SyncRun(Base):
    __tablename__ = "sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, index=True) # running, success, partial, failed
    documents_checked = Column(Integer, default=0, nullable=False)
    documents_changed = Column(Integer, default=0, nullable=False)
    documents_processed = Column(Integer, default=0, nullable=False)
    documents_skipped = Column(Integer, default=0, nullable=False)
    documents_failed = Column(Integer, default=0, nullable=False)
    error_summary = Column(Text, nullable=True)
