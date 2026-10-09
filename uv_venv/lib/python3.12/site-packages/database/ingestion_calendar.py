import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.models import Document, AcademicCalendarPeriod
from parser.calendar.api import parse_academic_calendar
from parser.calendar.validator import CalendarValidator
from parser.src.validator import DocumentGateStatus
from database.ingestion import IngestionResult

logger = logging.getLogger(__name__)

def ingest_academic_calendar(db: Session, temp_pdf_path: str, document_metadata: dict) -> IngestionResult:
    try:
        parsed_calendar = parse_academic_calendar(temp_pdf_path)
    except Exception as e:
        logger.error(f"Failed to parse Calendar PDF: {e}")
        return IngestionResult(success=False, error=f"Parser error: {e}")

    validator = CalendarValidator()
    validation_result = validator.validate_calendar(parsed_calendar)

    if validation_result.status == DocumentGateStatus.REJECT:
        logger.warning(f"Calendar ingestion REJECTED: {validation_result.errors}")
        return IngestionResult(success=False, validation_result=validation_result, error="Document rejected by Quality Gate")

    try:
        doc = Document(
            source_url=document_metadata.get("source_url"),
            title=document_metadata.get("title"),
            document_type="ACADEMIC_CALENDAR",
            academic_year=parsed_calendar.academic_year or document_metadata.get("academic_year"),
            semester=document_metadata.get("semester"),
            level=parsed_calendar.applicable_levels or document_metadata.get("level"),
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
        db.flush() 

        for parsed_period, session_val_res in zip(parsed_calendar.periods, validation_result.session_results):
            if session_val_res.status.value == "INVALID":
                continue
                
            # Extract duration_weeks if possible
            duration_weeks = None
            if parsed_period.duration_text:
                import re
                m = re.search(r'\d+', parsed_period.duration_text)
                if m:
                    duration_weeks = int(m.group(0))

            period_record = AcademicCalendarPeriod(
                document_id=doc.id,
                activity_name=parsed_period.period_name,
                start_date=validator._parse_date(parsed_period.start_date),
                end_date=validator._parse_date(parsed_period.end_date),
                duration_weeks=duration_weeks,
                duration_text=parsed_period.duration_text,
                academic_year=doc.academic_year,
                semester=parsed_period.semester,
                verification_status="verified" if session_val_res.status.value == "VALID" else "uncertain",
                warnings=session_val_res.warnings,
                raw_evidence=parsed_period.raw_evidence,
                source_page=parsed_period.source_page
            )
            db.add(period_record)

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
