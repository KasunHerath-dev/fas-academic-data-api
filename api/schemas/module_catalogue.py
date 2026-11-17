from typing import List, Optional

from pydantic import BaseModel, Field


class CatalogueModuleResponse(BaseModel):
    code: str
    title: Optional[str] = None
    credits: Optional[int] = None
    level: Optional[int] = None
    semester: Optional[str] = Field(None, description="'I', 'II', or 'both' for year-long modules")
    subject: str
    subject_name: Optional[str] = None
    year_long: bool = False
    non_credit: bool = False
    confirmed: bool = True
    source: str = ""
    timetable_codes: List[str] = Field(
        default_factory=list,
        description="How this module is printed in timetable PDFs, e.g. ['ELPC 1+10'] for ELPC I")


class ModuleResolutionResponse(BaseModel):
    raw: str
    code: Optional[str] = None
    status: str = Field(description="exact | normalized | closest_match | unlisted | named_course")
    confidence: float
    closest_match: Optional[str] = None
    notes: List[str] = []
    module: Optional[CatalogueModuleResponse] = None
