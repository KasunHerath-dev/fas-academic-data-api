from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    title: str
    document_type: str
    source_url: str
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    level: Optional[str] = None
    major: Optional[str] = None
    programme: Optional[str] = None
    published_at: Optional[datetime] = None
    revision: Optional[str] = None
    sha256: str
    status: str
    validation_status: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
