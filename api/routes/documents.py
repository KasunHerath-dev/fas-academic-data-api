from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List, Optional

from api.dependencies.database import get_db
from api.schemas.document import DocumentResponse
from database.models.models import Document
from api.schemas.common import PaginatedResponse

router = APIRouter(tags=["Documents"])

@router.get(
    "/documents", 
    response_model=PaginatedResponse[DocumentResponse],
    summary="List source documents metadata",
    description="""
    Returns source metadata for scraped FAS documents.
    
    A Document does NOT represent a permanently stored PDF file. 
    The API stores and returns source URLs, revisions, SHA-256 hashes, and validation status, but does not provide PDF binary downloads.
    """
)
def get_documents(
    document_type: Optional[str] = Query(None, description="Type of document (e.g., 'TIMETABLE', 'ACADEMIC_CALENDAR')"),
    academic_year: Optional[str] = Query(None, description="Academic year (e.g., '2024/2025')"),
    semester: Optional[str] = Query(None, description="Semester filter"),
    level: Optional[str] = Query(None, description="Level filter"),
    revision: Optional[str] = Query(None, description="Revision (e.g., 'original', 'revised')"),
    status: Optional[str] = Query(None, description="Processing status (e.g., 'PROCESSED')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    stmt = select(Document).order_by(desc(Document.first_seen_at))
    
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    if academic_year:
        stmt = stmt.where(Document.academic_year == academic_year)
    if semester:
        stmt = stmt.where(Document.semester == semester)
    if level:
        stmt = stmt.where(Document.level == level)
    if revision:
        stmt = stmt.where(Document.revision == revision)
    if status:
        stmt = stmt.where(Document.status == status)

    total = len(db.execute(stmt).scalars().all())
    
    stmt = stmt.offset(skip).limit(limit)
    documents = db.execute(stmt).scalars().all()
    
    return {"data": documents, "count": total}
