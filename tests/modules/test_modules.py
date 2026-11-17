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
    ("CMIS 4+18", "CMIS 4+18", "exact"),
    ("CMIS 4†18", "CMIS 4+18", "normalized"),  # prospectus form
    # Review B: prefix lost its first letter
    ("MIS 4142", "CMIS 4142", "normalized"),
    # Review A: dagger read as + or ᵻ
    ("IMGT 3+34", "IMGT 3+34", "exact"),
    ("IMGT 3ᵻ34", "IMGT 3+34", "normalized"),
    # English Language Proficiency Course: identified by level, no numeric code in the tracker
    ("ELPC 1+10", "ELPC I", "normalized"),
    ("ELPC 2+20", "ELPC II", "normalized"),
    ("ELPC 1ᵻ10", "ELPC I", "normalized"),
    ("ELPC 2†20", "ELPC II", "normalized"),
    ("ELPC I", "ELPC I", "exact"),
    ("ELTN 3+53", "ELTN 3+53", "exact"),
    ("ELTN 3ᵻ53", "ELTN 3+53", "normalized"),
    ("ELTN 4+78", "ELTN 4+78", "exact"),
    ("IMGT 4+06", "IMGT 4+06", "exact"),
    ("CMIS 4+26", "CMIS 4+26", "exact"),
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


def test_code_missing_from_catalogue_resolves_to_closest_module():
    match = match_module_code("MATH 1113")
    assert match.code == "MATH 1112"
    assert match.status == "closest_match"
    assert match.module.title == "Introduction to Mathematics I"
    assert match.raw == "MATH 1113"


def test_closest_match_prefers_same_semester_then_confirmed_tracker_modules():
    # CMIS 3122 (tracker) and CMIS 3124 (unconfirmed timetable code) are equally close
    assert match_module_code("CMIS 3125").code == "CMIS 3122"
    # year-long codes match year-long modules
    assert match_module_code("ELTN 4+99").code == "ELTN 4+92"
    # no exact module number: still the closest module of that subject and level
    assert match_module_code("STAT 4199").code == "STAT 4114"


def test_timetable_codes_listed_in_overrides_match_exactly():
    """Review group D codes are real modules; they must not be pulled onto a neighbour."""
    for code in ("CMIS 3124", "IMGT 4163", "STAT 4124"):
        assert match_module_code(code).code == code


def test_subject_with_no_catalogue_module_at_that_level_is_kept():
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
    assert catalogue["CMIS 4+18"].confirmed is True


def test_list_modules_filters():
    l4s1 = {m.code for m in list_modules(level=4, semester="1")}
    assert "CMIS 4142" in l4s1
    assert "CMIS 4+18" in l4s1  # year-long modules appear in both semesters
    assert "CMIS 4216" not in l4s1
    assert all(m.subject == "STAT" for m in list_modules(subject="stat"))
    assert all(m.confirmed for m in list_modules(include_unconfirmed=False))


@pytest.mark.parametrize("value, expected", [("1", "I"), ("I", "I"), ("Semester II", "II"), ("2", "II")])
def test_normalize_semester(value, expected):
    assert normalize_semester(value) == expected


def test_find_module_codes_does_not_split_inside_a_code():
    found = [t for t, _, _ in find_module_codes("CMIS 4142 (L) LR-05 MIS 4142 IMGT 3ᵻ34")]
    assert found == ["CMIS 4142", "MIS 4142", "IMGT 3ᵻ34"]


def test_backfill_plan_repairs_every_resolvable_code():
    from types import SimpleNamespace
    from scripts.normalize_module_codes import plan_repairs

    rows = [SimpleNamespace(module_code=c) for c in
            ["MIS 4142", "IMGT 3ᵻ34", "IMGT 3+34", "CMIS 2123", "MATH 1113", None, "GNCT 1112"]]
    repairs, skipped = plan_repairs(rows)
    assert {(s.module_code, m.code) for s, m in repairs} == {
        ("MIS 4142", "CMIS 4142"), ("IMGT 3ᵻ34", "IMGT 3+34"), ("MATH 1113", "MATH 1112")}
    assert skipped == []


def test_english_course_is_never_mapped_to_another_subject():
    """The closest tracker code by spelling is Electronics (ELTN); English must stay ELPC."""
    for raw in ("ELPC 1+10", "ELPC 2+20"):
        match = match_module_code(raw)
        assert match.code.startswith("ELPC ")
        assert match.module.non_credit is True
        assert match.module.credits == 0
        assert match.module.title.startswith("English Language Proficiency Course")


def test_timetable_codes_link_catalogue_codes_to_printed_codes():
    catalogue = load_catalogue()
    assert catalogue["ELPC I"].timetable_codes == ["ELPC 1+10"]
    assert catalogue["ELPC II"].timetable_codes == ["ELPC 2+20"]
    assert catalogue["IMGT 3+34"].timetable_codes == ["IMGT 3+34"]
    assert catalogue["CMIS 2123"].timetable_codes == []
    # every printed code resolves back to its catalogue module
    for module in catalogue.values():
        for printed in module.timetable_codes:
            assert match_module_code(printed).code == module.code, printed
