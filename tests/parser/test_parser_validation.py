import pytest
from parser.src.validator import (
    TimetableValidator, ValidationStatus, DocumentGateStatus
)
from parser.src.api import ParsedSession, ParsedTimetable

@pytest.fixture
def validator():
    return TimetableValidator()

def create_session(**kwargs) -> ParsedSession:
    defaults = {
        "day": "Monday",
        "start_time": "08:30",
        "end_time": "10:30",
        "module_code": "CMIS 1113",
        "time_source": "explicit",
        "verification_status": "verified",
        "raw_evidence": {},
        "warnings": []
    }
    defaults.update(kwargs)
    return ParsedSession(**defaults)

def test_valid_session(validator):
    s = create_session()
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.VALID

def test_invalid_time_range(validator):
    s = create_session(start_time="14:30", end_time="13:30")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.INVALID
    assert any("Invalid time range" in e for e in res.errors)

def test_zero_duration(validator):
    s = create_session(start_time="08:30", end_time="08:30")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.INVALID
    assert any("Zero duration" in e for e in res.errors)

def test_malformed_time(validator):
    s = create_session(start_time="invalid", end_time="10:30")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.INVALID
    assert any("Malformed start time" in e for e in res.errors)

def test_valid_weekday(validator):
    s = create_session(day="Friday")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.VALID

def test_unknown_weekday(validator):
    s = create_session(day="Funday")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.INVALID
    assert any("Invalid or unknown day" in e for e in res.errors)

def test_lunch_exclusion(validator):
    s = create_session(module_code="L U N C H")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.INVALID
    assert any("Lunch row incorrectly parsed" in e for e in res.errors)

def test_missing_room_allowed(validator):
    s = create_session(room=None)
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.VALID

def test_missing_group_allowed(validator):
    s = create_session(group=None)
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.VALID

def test_suspicious_module_code(validator):
    s = create_session(module_code="ELTN 3+53")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.UNCERTAIN
    assert any("Suspicious module code OCR" in w for w in res.warnings)
    # Ensure original evidence is untouched
    assert s.module_code == "ELTN 3+53"

def test_ambiguous_group_ocr(validator):
    s = create_session(group="Gp. ll")
    res = validator.validate_session(s)
    assert res.status == ValidationStatus.UNCERTAIN
    assert any("Ambiguous lowercase 'L'" in w for w in res.warnings)

def test_duplicate_detection(validator):
    s1 = create_session()
    s2 = create_session()
    timetable = ParsedTimetable(sessions=[s1, s2], diagnostics=[], report={})
    res = validator.validate_timetable(timetable)
    assert any("Likely duplicate session detected" in w for w in res.warnings)
    assert res.status == DocumentGateStatus.REVIEW_REQUIRED

def test_overlap_warning(validator):
    s1 = create_session(room="LR-08", start_time="08:30", end_time="10:30")
    s2 = create_session(room="LR-08", start_time="09:30", end_time="11:30", module_code="MATH 1113")
    timetable = ParsedTimetable(sessions=[s1, s2], diagnostics=[], report={})
    res = validator.validate_timetable(timetable)
    assert any("Room overlap detected" in w for w in res.warnings)
    assert res.status == DocumentGateStatus.REVIEW_REQUIRED

def test_document_quality_gate(validator):
    # SAFE
    s1 = create_session()
    t_safe = ParsedTimetable(sessions=[s1], diagnostics=[], report={})
    assert validator.validate_timetable(t_safe).status == DocumentGateStatus.SAFE
    
    # REVIEW_REQUIRED
    s2 = create_session(module_code="ELTN 3+53")
    t_review = ParsedTimetable(sessions=[s1, s2], diagnostics=[], report={})
    assert validator.validate_timetable(t_review).status == DocumentGateStatus.REVIEW_REQUIRED
    
    # REJECT
    s3 = create_session(day="Funday")
    t_reject = ParsedTimetable(sessions=[s3], diagnostics=[], report={})
    assert validator.validate_timetable(t_reject).status == DocumentGateStatus.REJECT
    
    # REJECT no sessions
    t_empty = ParsedTimetable(sessions=[], diagnostics=[], report={})
    assert validator.validate_timetable(t_empty).status == DocumentGateStatus.REJECT
