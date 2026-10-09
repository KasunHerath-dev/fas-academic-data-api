import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.models import Document, TimetableSession, AcademicYear, Semester, Level, Major, Programme
from parser.src.api import parse_timetable
from parser.src.validator import TimetableValidator, DocumentGateStatus

logger = logging.getLogger(__name__)

class IngestionResult:
    def __init__(self, success: bool, document_id: int = None, validation_result=None, error: str = None):
        self.success = success
        self.document_id = document_id
        self.validation_result = validation_result
        self.error = error


def get_or_create_lookup(db, model, field, value):
    if not value: return None
    obj = db.query(model).filter(getattr(model, field) == value).first()
    if not obj:
        obj = model(**{field: value})
        db.add(obj)
        db.flush()
    return obj

def ingest_timetable_pdf(db: Session, temp_pdf_path: str, document_metadata: dict) -> IngestionResult:
    """
    Ingests a timetable PDF into the database using the provided metadata.
    The document_metadata dict must contain:
    - source_url
    - title
    - document_type
    - academic_year
    - semester
    - level
    - major
    - programme
    - revision
    - sha256
    """
    # 1. Parse PDF
    try:
        parsed_timetable = parse_timetable(temp_pdf_path)
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return IngestionResult(success=False, error=f"Parser error: {e}")

    # 2. Validate Document
    validator = TimetableValidator()
    validation_result = validator.validate_timetable(parsed_timetable)

    # 3. Apply Quality Gate
    if validation_result.status == DocumentGateStatus.REJECT:
        logger.warning(f"Document ingestion REJECTED: {validation_result.errors}")
        return IngestionResult(success=False, validation_result=validation_result, error="Document rejected by Quality Gate")

    # 4. Ingest via Transaction
    try:
        # Create Document record
        doc = Document(
            source_url=document_metadata.get("source_url"),
            title=document_metadata.get("title"),
            document_type=document_metadata.get("document_type"),
            academic_year=document_metadata.get("academic_year"),
            semester=document_metadata.get("semester"),
            level=document_metadata.get("level"),
            major=document_metadata.get("major"),
            programme=document_metadata.get("programme"),
            revision=document_metadata.get("revision", "original"),
            sha256=document_metadata.get("sha256"),
            status="processed",
            validation_status=validation_result.status.value,
            validation_metadata={
                "total_sessions": validation_result.total_sessions,
                "valid_sessions": validation_result.valid_sessions,
                "uncertain_sessions": validation_result.uncertain_sessions,
                "invalid_sessions": validation_result.invalid_sessions,
                "warnings": validation_result.warnings,
                "errors": validation_result.errors
            }
        )
        db.add(doc)
        db.flush() # get doc.id

        get_or_create_lookup(db, AcademicYear, "year_string", doc.academic_year)
        get_or_create_lookup(db, Semester, "semester_string", doc.semester)
        get_or_create_lookup(db, Level, "level_string", doc.level)
        get_or_create_lookup(db, Major, "major_string", doc.major)
        get_or_create_lookup(db, Programme, "programme_string", doc.programme)


        # Insert TimetableSessions
        for parsed_session, session_val_res in zip(parsed_timetable.sessions, validation_result.session_results):
            if session_val_res.status.value == "INVALID":
                # We skip totally invalid sessions unless they cause a document REJECT
                # But since document is SAFE or REVIEW_REQUIRED, we might just drop the individual invalid ones
                # actually, prompt says: "if REJECT: abort ... else: convert parsed sessions to DB records... all 27 may be stored"
                continue

            session_record = TimetableSession(
                document_id=doc.id,
                academic_year=doc.academic_year,
                semester=doc.semester,
                level=doc.level,
                major=parsed_session.major or doc.major,
                programme=parsed_session.programme or doc.programme,
                module_code=parsed_session.module_code,
                raw_module_code=parsed_session.raw_evidence.get("rawText"), # Preserve raw where appropriate
                day=parsed_session.day,
                start_time=parsed_session.start_time,
                end_time=parsed_session.end_time,
                duration_minutes=parsed_session.raw_evidence.get("durationMinutes"), # Will be None if missing, can also calc
                class_type=parsed_session.session_type,
                group=parsed_session.group,
                room=parsed_session.room,
                time_source=parsed_session.time_source,
                verification_status=session_val_res.status.value.lower(),
                raw_evidence=parsed_session.raw_evidence,
                warnings=session_val_res.warnings
            )
            db.add(session_record)

        db.commit()
        return IngestionResult(success=True, document_id=doc.id, validation_result=validation_result)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database transaction failed: {e}")
        return IngestionResult(success=False, validation_result=validation_result, error=f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected ingestion failure: {e}")
        return IngestionResult(success=False, validation_result=validation_result, error=f"Unexpected error: {e}")
