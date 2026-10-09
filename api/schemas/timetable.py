from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict

class TimetableSessionResponse(BaseModel):
    id: int
    document_id: int
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    level: Optional[str] = None
    major: Optional[str] = None
    programme: Optional[str] = None
    day: str
    start_time: str
    end_time: str
    module_code: Optional[str] = None
    module_name: Optional[str] = None
    session_type: Optional[str] = None
    group: Optional[str] = None
    room: Optional[str] = None
    raw_module_code: Optional[str] = None
    raw_room: Optional[str] = None
    verification_status: str
    warnings: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)
