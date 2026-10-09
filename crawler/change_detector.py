from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from crawler.models import DiscoveredDocument
from database.models.models import Document

class ChangeStatus(Enum):
    NEW = "NEW"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"

class ChangeResult:
    def __init__(self, status: ChangeStatus, previous_document: Optional[Document] = None):
        self.status = status
        self.previous_document = previous_document

class ChangeDetector:
    def __init__(self, db_session: Session):
        self.db = db_session

    def detect(self, discovered: DiscoveredDocument, file_sha256: str) -> ChangeResult:
        """
        Detects whether the discovered document is new, changed, or unchanged.
        Identity is primarily matched on source_url and revision.
        """
        stmt = select(Document).where(
            Document.source_url == discovered.source_url,
            Document.revision == discovered.revision
        ).order_by(desc(Document.id)).limit(1)

        latest_doc = self.db.execute(stmt).scalars().first()
        
        # If no document is found with this source URL and revision, it's new.
        if not latest_doc:
            return ChangeResult(ChangeStatus.NEW)
            
        # If it exists, compare the SHA-256 of the actual downloaded file content.
        if latest_doc.sha256 == file_sha256:
            return ChangeResult(ChangeStatus.UNCHANGED, previous_document=latest_doc)
        else:
            return ChangeResult(ChangeStatus.CHANGED, previous_document=latest_doc)
