import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database.models.models import Document

logger = logging.getLogger(__name__)

# Predefined priority for known revision labels
# Higher number = higher priority
REVISION_PRIORITY = {
    "original": 10,
    "revised": 20,
    "re-revised": 30
}
DEFAULT_REVISION_PRIORITY = 0

def get_revision_score(revision: Optional[str]) -> int:
    """
    Returns a deterministic integer score for a revision string.
    Unknown strings default to 0.
    """
    if not revision:
        return DEFAULT_REVISION_PRIORITY
    return REVISION_PRIORITY.get(revision.lower(), DEFAULT_REVISION_PRIORITY)

def get_latest_document(
    db: Session,
    document_type: str,
    academic_year: str,
    semester: Optional[str] = None,
    level: Optional[str] = None,
    major: Optional[str] = None,
    programme: Optional[str] = None
) -> Optional[Document]:
    """
    Resolves the latest official document for a given academic context.
    
    Resolution strategy:
    1. Filter by exact academic context (type, year, semester, level, major, programme).
    2. Sort results in Python (or DB if possible, but Python is safer for custom logic) by:
       - Revision priority (Re-Revised > Revised > Original)
       - first_seen_at timestamp (newest first)
       - id (newest first, fallback tie-breaker)
    """
    query = db.query(Document).filter(
        Document.document_type == document_type,
        Document.academic_year == academic_year,
        Document.validation_status.in_(["SAFE", "REVIEW_REQUIRED"]) # Only consider documents that survived Quality Gate
    )
    
    if semester:
        query = query.filter(Document.semester == semester)
    if level:
        query = query.filter(Document.level == level)
    if major:
        query = query.filter(Document.major == major)
    if programme:
        query = query.filter(Document.programme == programme)
        
    documents = query.all()
    
    if not documents:
        return None
        
    # Sort with custom key
    # Higher tuple values appear at the end, so we want the maximum
    documents.sort(key=lambda d: (
        get_revision_score(d.revision),
        d.first_seen_at.timestamp() if d.first_seen_at else 0,
        d.id
    ), reverse=True)
    
    return documents[0]

def get_document_versions(
    db: Session,
    document_type: str,
    academic_year: str,
    semester: Optional[str] = None,
    level: Optional[str] = None,
    major: Optional[str] = None,
    programme: Optional[str] = None
) -> List[Document]:
    """
    Returns all historical versions of documents for a given academic context, 
    sorted from newest (latest resolved) to oldest.
    """
    query = db.query(Document).filter(
        Document.document_type == document_type,
        Document.academic_year == academic_year
    )
    
    if semester:
        query = query.filter(Document.semester == semester)
    if level:
        query = query.filter(Document.level == level)
    if major:
        query = query.filter(Document.major == major)
    if programme:
        query = query.filter(Document.programme == programme)
        
    documents = query.all()
    
    documents.sort(key=lambda d: (
        get_revision_score(d.revision),
        d.first_seen_at.timestamp() if d.first_seen_at else 0,
        d.id
    ), reverse=True)
    
    return documents
