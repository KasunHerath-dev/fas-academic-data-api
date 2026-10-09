from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional

from api.dependencies.database import get_db
from api.schemas.calendar import CalendarPeriodResponse
from api.schemas.common import PaginatedResponse
from database.models.models import AcademicCalendarPeriod
from database.versioning import get_latest_document

router = APIRouter(tags=["Calendar"])

@router.get(
    "/calendar", 
    response_model=PaginatedResponse[CalendarPeriodResponse],
    summary="List calendar periods",
    description="""
    Returns structured academic calendar periods (e.g., teaching weeks, exams, vacations).
    
    Academic calendar data is extracted from official FAS calendar documents.
    Some source PDFs are image-based and therefore OCR is used during ingestion.
    OCR validation may result in a verification status of `REVIEW_REQUIRED`. 
    This does not mean the API failed; it means the data should be manually verified if high confidence is strictly required.
    """
)
def get_calendar(
    academic_year: Optional[str] = Query(None, description="Academic year (e.g., '2024/2025')"),
    semester: Optional[str] = Query(None, description="Semester number"),
    document_id: Optional[int] = Query(None, description="Filter by a specific source document ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    stmt = select(AcademicCalendarPeriod)
    
    if document_id:
        stmt = stmt.where(AcademicCalendarPeriod.document_id == document_id)
    if academic_year:
        stmt = stmt.where(AcademicCalendarPeriod.academic_year == academic_year)
    if semester:
        stmt = stmt.where(AcademicCalendarPeriod.semester == semester)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()
    
    stmt = stmt.order_by(AcademicCalendarPeriod.id).offset(skip).limit(limit)
    periods = db.execute(stmt).scalars().all()
    
    return {"data": periods, "count": total}

@router.get(
    "/calendar/latest", 
    response_model=PaginatedResponse[CalendarPeriodResponse],
    summary="Get latest calendar periods",
    description="Resolves the active calendar based on versioning rules."
)
def get_latest_calendar(
    academic_year: Optional[str] = Query(None, description="Academic year"),
    semester: Optional[str] = Query(None, description="Semester filter"),
    level: Optional[str] = Query(None, description="Level filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    # If academic_year is not provided, we could optionally find the absolute latest document
    # For now, require academic year or find the newest calendar document if not provided.
    if not academic_year:
        from database.models.models import Document
        from sqlalchemy import desc
        latest_doc = db.query(Document).filter(
            Document.document_type == "ACADEMIC_CALENDAR",
            Document.validation_status.in_(["SAFE", "REVIEW_REQUIRED"])
        ).order_by(desc(Document.first_seen_at), desc(Document.id)).first()
    else:
        latest_doc = get_latest_document(
            db,
            document_type="ACADEMIC_CALENDAR",
            academic_year=academic_year,
            semester=semester,
            level=level
        )
    
    if not latest_doc:
        raise HTTPException(status_code=404, detail="No calendar found for the given criteria.")
        
    stmt = select(AcademicCalendarPeriod).where(AcademicCalendarPeriod.document_id == latest_doc.id)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()
    
    stmt = stmt.order_by(AcademicCalendarPeriod.id).offset(skip).limit(limit)
    periods = db.execute(stmt).scalars().all()
    
    return {"data": periods, "count": total}
