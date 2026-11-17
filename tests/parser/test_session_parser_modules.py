"""SessionParser must anchor and repair OCR-damaged module codes inside timetable cells."""
from parser.src.session_parser import SessionParser
from parser.src.validator import TimetableValidator, ValidationStatus
from parser.src.api import ParsedSession


def _words(*lines):
    """Build word dicts; each line is (y, [(x, text), ...])."""
    words = []
    for y, items in lines:
        for x, text in items:
            words.append({"x0": x, "y0": y, "x1": x + 8 * len(text), "y1": y + 8, "word": text})
    return words


def _cell(words):
    return {
        "day": "Monday", "startTime": "08:30", "endTime": "09:30", "isLunch": False,
        "timeSource": "explicit", "timeInferenceReason": None,
        "rawText": [], "words": words,
    }


def _parse(words):
    sessions, _ = SessionParser().parse_sessions([_cell(words)])
    return sessions


def test_dropped_prefix_letter_is_repaired_and_kept_as_raw():
    sessions = _parse(_words((100, [(10, "MIS"), (45, "4142"), (90, "(L)")]), (112, [(10, "LR-05")])))
    assert len(sessions) == 1
    s = sessions[0]
    assert s["moduleCode"] == "CMIS 4142"
    assert s["rawModuleCode"] == "MIS 4142"
    assert s["moduleName"] == "Image Processing"
    assert s["classType"] == "L"
    assert s["rawEvidence"]["moduleMatch"]["status"] == "normalized"
    # prefix repair is not certain: flagged for review
    assert any("matched to 'CMIS 4142'" in w for w in s["warnings"])


def test_dagger_variants_become_one_canonical_code_without_warning():
    for token in ("3+34", "3ᵻ34"):
        sessions = _parse(_words((100, [(10, "IMGT"), (50, token), (95, "(P)")])))
        assert len(sessions) == 1
        assert sessions[0]["moduleCode"] == "IMGT 3†34"
        assert sessions[0]["warnings"] == []


def test_dagger_code_from_pdf_is_anchored():
    sessions = _parse(_words((100, [(10, "CMIS"), (50, "4†18")])))
    assert [s["moduleCode"] for s in sessions] == ["CMIS 4†18"]


def test_unlisted_valid_code_is_kept_and_flagged():
    sessions = _parse(_words((100, [(10, "CMIS"), (50, "3125"), (95, "(L)")])))
    assert sessions[0]["moduleCode"] == "CMIS 3125"
    assert any("not in the module catalogue" in w for w in sessions[0]["warnings"])


def test_non_code_tokens_do_not_create_sessions():
    assert _parse(_words((100, [(10, "LR"), (30, "01/02/03"), (100, "Mini"), (140, "Auditorium")]))) == []


def test_validator_accepts_canonical_dagger_codes():
    v = TimetableValidator()
    base = dict(day="Monday", start_time="08:30", end_time="10:30", time_source="explicit",
                verification_status="verified", raw_evidence={}, warnings=[])
    assert v.validate_session(ParsedSession(module_code="IMGT 3†34", **base)).status == ValidationStatus.VALID
    assert v.validate_session(ParsedSession(module_code="Business English", **base)).status == ValidationStatus.VALID
    res = v.validate_session(ParsedSession(module_code="ELTN 3+53", **base))
    assert res.status == ValidationStatus.UNCERTAIN
