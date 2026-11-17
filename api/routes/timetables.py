from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from typing import List, Optional

from api.dependencies.database import get_db
from api.schemas.timetable import TimetableSessionResponse
from api.schemas.common import PaginatedResponse
from database.models.models import TimetableSession
from database.versioning import get_latest_document, level_filter, semester_values
from api.services.module_enrichment import enrich_session, resolve_query_code


def _apply_module_filters(stmt, module_code: Optional[str], subject: Optional[str]):
    if module_code:
        codes = resolve_query_code(module_code)
        stmt = stmt.where(
            TimetableSession.module_code.in_(codes) | TimetableSession.raw_module_code.in_(codes)
        )
    if subject:
        stmt = stmt.where(TimetableSession.module_code.like(f"{subject.strip().upper()} %"))
    return stmt


_DAY_ORDER = {d: i for i, d in enumerate(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], start=1)}


def _ordered(stmt):
    return stmt.order_by(
        case(_DAY_ORDER, value=TimetableSession.day, else_=99),
        # Ingestion inserts sessions in time order; start_time strings ("1:00" = 1 PM)
        # do not sort correctly, so the insertion id is the reliable time order.
        TimetableSession.id,
    )

router = APIRouter(tags=["Timetables"])

@router.get(
    "/timetables", 
    response_model=PaginatedResponse[TimetableSessionResponse],
    summary="List timetable sessions",
    description="""
    Returns structured timetable sessions from stored academic data.

    Filtering can be applied by:
    - academic year
    - semester
    - level
    - major
    - programme
    - module code
    - day
    
    Nullable values may occur because the source document may not contain a deterministic value (e.g. missing room names).
    """
)
def get_timetables(
    academic_year: Optional[str] = Query(None, description="Academic year (e.g., '2024/2025')"),
    semester: Optional[str] = Query(None, description="Semester ('1', '2', 'I' or 'II')"),
    level: Optional[str] = Query(None, description="Academic level (e.g., '2'). Matches combined timetables such as '2,3'."),
    major: Optional[str] = Query(None, description="Major (if applicable)"),
    programme: Optional[str] = Query(None, description="Programme (if applicable)"),
    module_code: Optional[str] = Query(None, description="Module code (e.g., 'CMIS 2123'). OCR variants such as 'MIS 4142' or 'IMGT 3+34' are resolved to the canonical code."),
    subject: Optional[str] = Query(None, description="Subject prefix (e.g., 'CMIS', 'STAT')"),
    day_of_week: Optional[str] = Query(None, description="Day of the week (e.g., 'Monday')"),
    document_id: Optional[int] = Query(None, description="Filter by a specific source document ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    stmt = select(TimetableSession)
    
    if document_id:
        stmt = stmt.where(TimetableSession.document_id == document_id)
    if academic_year:
        stmt = stmt.where(TimetableSession.academic_year == academic_year)
    if semester:
        stmt = stmt.where(TimetableSession.semester.in_(semester_values(semester)))
    if level:
        stmt = stmt.where(level_filter(TimetableSession.level, level))
    if major:
        stmt = stmt.where(TimetableSession.major == major)
    if programme:
        stmt = stmt.where(TimetableSession.programme == programme)
    stmt = _apply_module_filters(stmt, module_code, subject)
    if day_of_week:
        stmt = stmt.where(TimetableSession.day.ilike(day_of_week))

    # Basic total count (using func.count for efficiency rather than len(all()))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()
    
    stmt = _ordered(stmt).offset(skip).limit(limit)
    sessions = db.execute(stmt).scalars().all()

    return {"data": [enrich_session(s) for s in sessions], "count": total}

@router.get(
    "/timetables/latest", 
    response_model=PaginatedResponse[TimetableSessionResponse],
    summary="Get latest timetable sessions",
    description="""
    Resolves the latest applicable timetable using the existing version-management rules.
    
    Version Priority:
    1. re-revised
    2. revised
    3. original
    4. unknown/draft
    
    Tie-breaking:
    5. newest first_seen_at
    6. highest document ID
    """
)
def get_latest_timetables(
    academic_year: str = Query(..., description="Required academic year (e.g., '2024/2025')"),
    semester: Optional[str] = Query(None, description="Semester number"),
    level: Optional[str] = Query(None, description="Academic level"),
    major: Optional[str] = Query(None, description="Major (if applicable)"),
    programme: Optional[str] = Query(None, description="Programme (if applicable)"),
    module_code: Optional[str] = Query(None, description="Module code filter (OCR variants are resolved)"),
    subject: Optional[str] = Query(None, description="Subject prefix (e.g., 'CMIS')"),
    day_of_week: Optional[str] = Query(None, description="Day of the week filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    latest_doc = get_latest_document(
        db,
        document_type="TIMETABLE",
        academic_year=academic_year,
        semester=semester,
        level=level,
        major=major,
        programme=programme
    )
    
    if not latest_doc:
        raise HTTPException(status_code=404, detail="No timetable found for the given criteria.")
        
    stmt = select(TimetableSession).where(TimetableSession.document_id == latest_doc.id)
    
    stmt = _apply_module_filters(stmt, module_code, subject)
    if day_of_week:
        stmt = stmt.where(TimetableSession.day.ilike(day_of_week))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()
    
    stmt = _ordered(stmt).offset(skip).limit(limit)
    sessions = db.execute(stmt).scalars().all()

    return {"data": [enrich_session(s) for s in sessions], "count": total}
