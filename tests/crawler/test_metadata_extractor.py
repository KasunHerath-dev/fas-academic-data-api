import pytest
from crawler.metadata_extractor import extract_metadata

def test_extract_metadata_single_level():
    title = "Revised – Academic Time Table – Level 1 Semester I (Academic Year 2024/2025)"
    meta = extract_metadata(title)
    assert meta["document_type"] == "TIMETABLE"
    assert meta["revision"] == "revised"
    assert meta["academic_year"] == "2024/2025"
    assert meta["semester"] == "I"
    assert meta["levels"] == [1]

def test_extract_metadata_multiple_levels_revised():
    title = "Revised – Academic Time Table – Level 1,2,3 & 4 Semester I (Academic Year 2024/2025)"
    meta = extract_metadata(title)
    assert meta["document_type"] == "TIMETABLE"
    assert meta["revision"] == "revised"
    assert meta["academic_year"] == "2024/2025"
    assert meta["semester"] == "I"
    assert meta["levels"] == [1, 2, 3, 4]

def test_extract_metadata_multiple_levels_original():
    title = "Academic Time Table – Level 1,2,3 & 4 Semester I (Academic Year 2024/2025)"
    meta = extract_metadata(title)
    assert meta["document_type"] == "TIMETABLE"
    assert meta["revision"] == "original"
    assert meta["academic_year"] == "2024/2025"
    assert meta["semester"] == "I"
    assert meta["levels"] == [1, 2, 3, 4]

def test_extract_metadata_calendar():
    title = "Calendar of Dates for Academic Year 2024/2025"
    meta = extract_metadata(title)
    assert meta["document_type"] == "ACADEMIC_CALENDAR"
    assert meta["revision"] == "original"
    assert meta["academic_year"] == "2024/2025"
    assert meta["semester"] is None

def test_extract_metadata_rerevised():
    title = "Re-revised Academic Time Table – Level 2 Semester II (Academic Year 2022/2023)"
    meta = extract_metadata(title)
    assert meta["document_type"] == "TIMETABLE"
    assert meta["revision"] == "re-revised"
    assert meta["academic_year"] == "2022/2023"
    assert meta["semester"] == "II"
    assert meta["levels"] == [2]

def test_extract_metadata_draft():
    title = "Draft Calendar of Dates for Academic Year 2024/2025"
    meta = extract_metadata(title)
    assert meta["document_type"] == "ACADEMIC_CALENDAR"
    # Although draft wasn't specified to be a revision, it stays original or we could add draft. Let's keep original for now based on spec.
    assert meta["revision"] == "original" 
