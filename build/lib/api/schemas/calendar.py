from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class CalendarPeriodResponse(BaseModel):
    id: int
    document_id: int
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    activity_name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_weeks: Optional[int] = None
    duration_text: Optional[str] = None
    verification_status: str
    warnings: Optional[Any] = None
    source_page: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
