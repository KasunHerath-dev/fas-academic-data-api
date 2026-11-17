from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class DiscoveredDocument(BaseModel):
    source_url: str
    notice_url: str
    title: str
    document_type: str
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    levels: Optional[List[str]] = None
    revision: Optional[str] = None
    published_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
