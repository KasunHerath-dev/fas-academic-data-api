from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class DiscoveredDocument(BaseModel):
    source_url: str
    source_page_url: str
    title: str
    link_text: str
    document_type: Optional[str] = None # TIMETABLE or ACADEMIC_CALENDAR
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    levels: Optional[List[int]] = None
    major: Optional[str] = None
    programme: Optional[str] = None
    revision: Optional[str] = None # original, revised, re-revised
    published_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    discovered_at: datetime
