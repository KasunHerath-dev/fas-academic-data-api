import os
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from parser.calendar.ocr_extractor import extract_calendar_data

class ParsedCalendarPeriod(BaseModel):
    semester: str
    period_name: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_text: Optional[str]
    source_page: int
    raw_evidence: Dict[str, Any]
    verification_status: str
    warnings: List[str]

class ParsedAcademicCalendar(BaseModel):
    academic_year: Optional[str]
    applicable_levels: Optional[str]
    raw_title: Optional[str]
    periods: List[ParsedCalendarPeriod]
    diagnostics: List[Dict[str, Any]]
    report: Dict[str, Any]

def parse_academic_calendar(pdf_path: str) -> ParsedAcademicCalendar:
    """
    Public entry point for the production Calendar PDF parser.
    Takes a path to a temporary PDF file and returns a structured ParsedAcademicCalendar.
    Raises ValueError if parsing fails due to malformed PDF or unsupported layout.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")
        
    return extract_calendar_data(pdf_path)
