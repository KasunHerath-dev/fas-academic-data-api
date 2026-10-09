from pydantic import BaseModel, ConfigDict
from typing import Optional

class AcademicYearResponse(BaseModel):
    id: int
    year_string: str

    model_config = ConfigDict(from_attributes=True)

class SemesterResponse(BaseModel):
    id: int
    semester_string: str

    model_config = ConfigDict(from_attributes=True)

class LevelResponse(BaseModel):
    id: int
    level_string: str

    model_config = ConfigDict(from_attributes=True)

class MajorResponse(BaseModel):
    id: int
    major_string: str

    model_config = ConfigDict(from_attributes=True)

class ProgrammeResponse(BaseModel):
    id: int
    programme_string: str

    model_config = ConfigDict(from_attributes=True)

class ModuleResponse(BaseModel):
    id: int
    module_code: str
    module_name: Optional[str] = None
    level: Optional[str] = None
    major: Optional[str] = None
    programme: Optional[str] = None
    specialization: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

