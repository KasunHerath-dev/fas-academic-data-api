from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, List


class ModuleMatchInfo(BaseModel):
    status: str = Field(description="exact | normalized | closest_match | unlisted | named_course | unresolved")
    confidence: float
    in_catalogue: bool
    catalogue_confirmed: Optional[bool] = Field(
        None, description="False when the catalogue entry comes from the code review and is not yet confirmed by the faculty")
    closest_match: Optional[str] = Field(None, description="Closest catalogue module when the code is not in the catalogue")
    notes: List[str] = []


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
    duration_minutes: Optional[int] = None
    module_code: Optional[str] = Field(None, description="Canonical module code, e.g. 'CMIS 4142' or 'CMIS 4†18' (year-long)")
    raw_module_code: Optional[str] = Field(None, description="Module code exactly as read from the PDF")
    module_name: Optional[str] = Field(None, description="Title from the module catalogue")
    credits: Optional[int] = None
    subject: Optional[str] = None
    year_long: bool = False
    non_credit: bool = False
    module_match: Optional[ModuleMatchInfo] = None
    session_type: Optional[str] = Field(None, description="L (lecture), T (tutorial) or P (practical)")
    group: Optional[str] = None
    raw_group: Optional[str] = None
    room: Optional[str] = None
    raw_room: Optional[str] = None
    time_source: Optional[str] = None
    verification_status: str
    confidence: Optional[int] = None
    warnings: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)
