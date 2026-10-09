from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from api.dependencies.database import get_db
from api.schemas.academic_structure import (
    AcademicYearResponse,
    SemesterResponse,
    LevelResponse,
    MajorResponse,
    ProgrammeResponse,
    ModuleResponse
)
from database.models.models import (
    AcademicYear,
    Semester,
    Level,
    Major,
    Programme,
    Module
)

router = APIRouter(tags=["Academic Structure"])

@router.get("/academic-years", response_model=List[AcademicYearResponse], summary="List academic years", description="Returns available academic years.")
def get_academic_years(db: Session = Depends(get_db)):
    stmt = select(AcademicYear).order_by(AcademicYear.year_string.desc())
    return db.execute(stmt).scalars().all()

@router.get("/semesters", response_model=List[SemesterResponse], summary="List semesters", description="Returns structured semester information.")
def get_semesters(db: Session = Depends(get_db)):
    stmt = select(Semester).order_by(Semester.semester_string)
    return db.execute(stmt).scalars().all()

@router.get("/levels", response_model=List[LevelResponse], summary="List levels", description="Returns academic levels (e.g., Level 1, Level 2).")
def get_levels(db: Session = Depends(get_db)):
    stmt = select(Level).order_by(Level.level_string)
    return db.execute(stmt).scalars().all()

@router.get("/majors", response_model=List[MajorResponse], summary="List majors", description="Returns majors available in the curriculum.")
def get_majors(db: Session = Depends(get_db)):
    stmt = select(Major).order_by(Major.major_string)
    return db.execute(stmt).scalars().all()

@router.get("/programmes", response_model=List[ProgrammeResponse], summary="List programmes", description="Returns academic programmes.")
def get_programmes(db: Session = Depends(get_db)):
    stmt = select(Programme).order_by(Programme.programme_string)
    return db.execute(stmt).scalars().all()

@router.get("/modules", response_model=List[ModuleResponse], summary="List modules", description="Returns modules with optional filtering.")
def get_modules(
    level: Optional[str] = Query(None, description="Filter by level"),
    major: Optional[str] = Query(None, description="Filter by major"),
    programme: Optional[str] = Query(None, description="Filter by programme"),
    module_code: Optional[str] = Query(None, description="Filter by module code (e.g., 'CMIS')"),
    db: Session = Depends(get_db)
):
    stmt = select(Module).order_by(Module.module_code)
    if level:
        stmt = stmt.where(Module.level == level)
    if major:
        stmt = stmt.where(Module.major == major)
    if programme:
        stmt = stmt.where(Module.programme == programme)
    if module_code:
        stmt = stmt.where(Module.module_code.ilike(f"%{module_code}%"))
    return db.execute(stmt).scalars().all()

