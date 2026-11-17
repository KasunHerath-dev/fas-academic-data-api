"""
Read-time module enrichment for timetable sessions.

Sessions stored before the module matcher existed may still hold OCR-damaged
codes (``MIS 4142``, ``IMGT 3+34``). The API resolves them on the way out so
consumers always see the canonical code, catalogue title and credits, while
``raw_module_code`` keeps exactly what was read from the PDF.
``scripts/normalize_module_codes.py`` persists the same repair in the database.
"""
from typing import Optional

from academic.modules import is_valid_module_code, load_catalogue, match_module_code

# Stored codes are repaired at read time whenever they resolve to a catalogue code.
READ_TIME_REPAIR_MIN_CONFIDENCE = 0.0


def resolve_query_code(module_code: Optional[str]) -> list[str]:
    """Codes to match for a ?module_code= filter: the input as typed plus its canonical form."""
    if not module_code:
        return []
    typed = " ".join(module_code.split())
    codes = {typed, typed.upper()}
    match = match_module_code(typed)
    if match.code and is_valid_module_code(match.code):
        code = match.code
        codes.add(code)
        # Rows ingested before the matcher existed may still hold OCR variants.
        if "†" in code:
            codes.update(code.replace("†", v) for v in ("+", "ᵻ"))
        if " " in code and code.split(" ")[1][:1].isdigit():
            codes.add(code[1:])  # dropped first prefix letter, e.g. "MIS 4142"
        # Codes as printed in timetables, and their dagger variants (ELPC 1+10, ELPC 1†10).
        module = load_catalogue().get(code)
        for printed in (module.timetable_codes if module else []):
            codes.update(printed.replace("+", v) for v in ("+", "†", "ᵻ"))
    return sorted(codes)


def enrich_session(session) -> dict:
    stored_code = session.module_code
    raw_code = session.raw_module_code or stored_code
    match = match_module_code(stored_code) if stored_code else None

    module_code = stored_code
    if (match and match.code and match.code != stored_code
            and match.confidence >= READ_TIME_REPAIR_MIN_CONFIDENCE
            and is_valid_module_code(match.code)):
        module_code = match.code

    module = match.module if match else None
    return {
        "id": session.id,
        "document_id": session.document_id,
        "academic_year": session.academic_year,
        "semester": session.semester,
        "level": session.level,
        "major": session.major,
        "programme": session.programme,
        "day": session.day,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "duration_minutes": session.duration_minutes,
        "module_code": module_code,
        "raw_module_code": raw_code,
        "module_name": module.title if module else None,
        "timetable_codes": module.timetable_codes if module else [],
        "credits": module.credits if module else None,
        "subject": module_code.split(" ")[0] if module_code and " " in module_code else None,
        "year_long": bool(module_code and "†" in module_code) or bool(module and module.semester == "both"),
        "non_credit": bool(module.non_credit) if module else (match.status == "named_course" if match else False),
        "module_match": {
            "status": match.status,
            "confidence": match.confidence,
            "in_catalogue": module is not None,
            "catalogue_confirmed": module.confirmed if module else None,
            "closest_match": match.closest_match,
            "notes": match.notes,
        } if match else None,
        "session_type": session.class_type,
        "group": session.group,
        "raw_group": session.raw_group,
        "room": session.room,
        "raw_room": session.raw_room,
        "time_source": session.time_source,
        "verification_status": session.verification_status,
        "confidence": session.confidence,
        "warnings": session.warnings,
    }
