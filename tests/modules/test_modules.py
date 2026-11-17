import json

import pytest

from academic.modules import (
    find_module_codes,
    is_named_course,
    list_modules,
    load_catalogue,
    match_module_code,
    normalize_semester,
)
from scripts.build_module_catalogue import OUTPUT, TRACKER, parse_tracker


def test_catalogue_json_matches_tracker_document():
    """academic/data/module_catalogue.json must be regenerated when the tracker changes."""
    expected = parse_tracker(TRACKER.read_text(encoding="utf-8"))
    stored = json.loads(OUTPUT.read_text(encoding="utf-8"))["modules"]
    assert stored == expected
    assert len(stored) == 99


@pytest.mark.parametrize("raw, code, status", [
    # Exact catalogue codes are untouched
    ("CMIS 2123", "CMIS 2123", "exact"),
    ("CMIS 4†18", "CMIS 4†18", "exact"),
    # Review B: prefix lost its first letter
    ("MIS 4142", "CMIS 4142", "normalized"),
    # Review A: dagger read as + or ᵻ
    ("IMGT 3+34", "IMGT 3†34", "normalized"),
    ("IMGT 3ᵻ34", "IMGT 3†34", "normalized"),
    ("ELPC 1+10", "ELPC 1†10", "normalized"),
    ("ELPC 2+20", "ELPC 2†20", "normalized"),
    ("ELTN 3+53", "ELTN 3†53", "normalized"),
    ("ELTN 4+78", "ELTN 4†78", "normalized"),
    ("IMGT 4+06", "IMGT 4†06", "normalized"),
    ("CMIS 4+26", "CMIS 4†26", "normalized"),
    # Spacing, case and letter/digit confusions
    ("CMIS4123", "CMIS 4123", "normalized"),
    ("cmis 2123", "CMIS 2123", "normalized"),
    ("CMIS 2l23", "CMIS 2123", "normalized"),
    ("5TAT 1113", "STAT 1113", "normalized"),
    ("CMIS 1123 (L)", "CMIS 1123", "exact"),
])
def test_match_repairs_known_ocr_damage(raw, code, status):
    match = match_module_code(raw)
    assert match.code == code
    assert match.status == status


def test_both_dagger_variants_resolve_to_one_module():
    """Review A2: IMGT 3+34 and IMGT 3ᵻ34 were two modules; they must be one."""
    assert match_module_code("IMGT 3+34").code == match_module_code("IMGT 3ᵻ34").code


def test_repaired_prefix_carries_catalogue_title():
    match = match_module_code("MIS 4142")
    assert match.module.title == "Image Processing"
    assert match.module.credits == 2
    assert match.confidence < 0.9  # prefix repairs are flagged for review


def test_well_formed_code_missing_from_catalogue_is_not_rewritten():
    """Doc §6: never silently rewrite a valid code; only suggest the closest module."""
    match = match_module_code("MATH 1113")
    assert match.code == "MATH 1113"
    assert match.status == "unlisted"
    assert match.closest_match == "MATH 1112"
    assert match.module is None


def test_new_subject_prefix_is_kept():
    match = match_module_code("GNCT 1112")
    assert match.code == "GNCT 1112"
    assert match.status == "unlisted"


@pytest.mark.parametrize("raw", ["LR 0102", "2024 2025", "XYZ 1234", "Room 22", "", "CMIS 5123", "CMIS 1323"])
def test_non_codes_are_unresolved(raw):
    assert match_module_code(raw).code is None


def test_named_courses():
    assert match_module_code("Business English").status == "named_course"
    assert is_named_course("Orientation")
    assert not is_named_course("CMIS 1113")


def test_unconfirmed_timetable_codes_are_in_catalogue_but_flagged():
    catalogue = load_catalogue()
    assert catalogue["CMIS 3124"].confirmed is False
    assert catalogue["CMIS 3124"].title is None
    # The tracker wins over curated entries
    assert catalogue["CMIS 4†18"].confirmed is True


def test_list_modules_filters():
    l4s1 = {m.code for m in list_modules(level=4, semester="1")}
    assert "CMIS 4142" in l4s1
    assert "CMIS 4†18" in l4s1  # year-long modules appear in both semesters
    assert "CMIS 4216" not in l4s1
    assert all(m.subject == "STAT" for m in list_modules(subject="stat"))
    assert all(m.confirmed for m in list_modules(include_unconfirmed=False))


@pytest.mark.parametrize("value, expected", [("1", "I"), ("I", "I"), ("Semester II", "II"), ("2", "II")])
def test_normalize_semester(value, expected):
    assert normalize_semester(value) == expected


def test_find_module_codes_does_not_split_inside_a_code():
    found = [t for t, _, _ in find_module_codes("CMIS 4142 (L) LR-05 MIS 4142 IMGT 3ᵻ34")]
    assert found == ["CMIS 4142", "MIS 4142", "IMGT 3ᵻ34"]


def test_backfill_plan_repairs_only_confident_matches():
    from types import SimpleNamespace
    from scripts.normalize_module_codes import plan_repairs

    rows = [SimpleNamespace(module_code=c) for c in
            ["MIS 4142", "IMGT 3+34", "CMIS 2123", "MATH 1113", None, "CMLS 9999"]]
    repairs, _ = plan_repairs(rows)
    assert {(s.module_code, m.code) for s, m in repairs} == {("MIS 4142", "CMIS 4142"), ("IMGT 3+34", "IMGT 3†34")}
