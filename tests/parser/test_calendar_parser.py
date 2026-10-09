import pytest
from parser.calendar.api import ParsedCalendarPeriod, ParsedAcademicCalendar
from parser.calendar.validator import CalendarValidator
from parser.src.validator import ValidationStatus, DocumentGateStatus

def test_calendar_period_validation():
    validator = CalendarValidator()
    
    p = ParsedCalendarPeriod(
        semester="FIRST SEMESTER",
        period_name="Academic Session",
        start_date="03-08-2026",
        end_date="27-09-2026",
        duration_text="08 Weeks",
        source_page=1,
        raw_evidence={},
        verification_status="verified",
        warnings=[]
    )
    
    res = validator.validate_period(p)
    assert res.status == ValidationStatus.VALID
    
def test_calendar_period_invalid_date():
    validator = CalendarValidator()
    
    p = ParsedCalendarPeriod(
        semester="FIRST SEMESTER",
        period_name="Academic Session",
        start_date="27-09-2026",
        end_date="03-08-2026", # end before start
        duration_text="08 Weeks",
        source_page=1,
        raw_evidence={},
        verification_status="verified",
        warnings=[]
    )
    
    res = validator.validate_period(p)
    assert res.status == ValidationStatus.INVALID
    
def test_calendar_missing_date_warning():
    validator = CalendarValidator()
    
    p = ParsedCalendarPeriod(
        semester="FIRST SEMESTER",
        period_name="Academic Session",
        start_date="03-08-2026",
        end_date=None,
        duration_text="08 Weeks",
        source_page=1,
        raw_evidence={},
        verification_status="verified",
        warnings=[]
    )
    
    res = validator.validate_period(p)
    assert res.status == ValidationStatus.UNCERTAIN
    assert any("Missing start or end date" in w for w in res.warnings)

def test_calendar_document_validation_safe():
    validator = CalendarValidator()
    
    p = ParsedCalendarPeriod(
        semester="FIRST SEMESTER",
        period_name="Academic Session",
        start_date="03-08-2026",
        end_date="27-09-2026",
        duration_text="08 Weeks",
        source_page=1,
        raw_evidence={},
        verification_status="verified",
        warnings=[]
    )
    
    cal = ParsedAcademicCalendar(
        academic_year="2024/2025",
        applicable_levels="1,2,3,4",
        raw_title=None,
        periods=[p],
        diagnostics=[],
        report={}
    )
    
    res = validator.validate_calendar(cal)
    assert res.status == DocumentGateStatus.SAFE

def test_calendar_document_validation_reject():
    validator = CalendarValidator()
    
    p = ParsedCalendarPeriod(
        semester="FIRST SEMESTER",
        period_name="Academic Session",
        start_date="27-09-2026",
        end_date="03-08-2026", # Invalid
        duration_text="08 Weeks",
        source_page=1,
        raw_evidence={},
        verification_status="verified",
        warnings=[]
    )
    
    cal = ParsedAcademicCalendar(
        academic_year="2024/2025",
        applicable_levels="1,2,3,4",
        raw_title=None,
        periods=[p],
        diagnostics=[],
        report={}
    )
    
    res = validator.validate_calendar(cal)
    assert res.status == DocumentGateStatus.REJECT
