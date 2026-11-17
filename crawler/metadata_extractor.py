import re

_REVISION_NUMBER_RE = re.compile(r"\brevised\s*[-–(]?\s*(?:no\.?\s*)?0*(\d{1,2})\b", re.IGNORECASE)
_ORDINAL_REVISION_RE = re.compile(r"\b(\d)(?:st|nd|rd|th)\s+revised\b", re.IGNORECASE)


def extract_levels(text: str):
    """Return the sorted levels named in text ('Level 1,2,3 & 4' -> [1, 2, 3, 4]), or None."""
    matches = list(re.finditer(r"\bLevels?\s*[-–:]?\s*([1-4](?:\s*(?:,|&|and|/|-|–)\s*[1-4])*)", text, re.IGNORECASE))
    if not matches:
        return None
    levels = set()
    for m in matches:
        levels.update(int(d) for d in re.findall(r"[1-4]", m.group(1)))
    return sorted(levels) or None


def extract_revision(text: str) -> str:
    """
    'original', 'revised', 're-revised', or a numbered revision such as 'revised-2'
    for titles like 'Revised 02' / '2nd Revised'. database.versioning ranks them.
    """
    lower = text.lower()
    if re.search(r"\bre[\s-]?revised\b", lower):
        return "re-revised"
    if "revised" in lower:
        m = _REVISION_NUMBER_RE.search(text) or _ORDINAL_REVISION_RE.search(text)
        if m and int(m.group(1)) > 1:
            return f"revised-{int(m.group(1))}"
        return "revised"
    return "original"


def extract_metadata(title: str):
    """
    Extract metadata deterministically from a FAS document title.
    Returns a dict with document_type, academic_year, semester, levels, major, programme, revision.
    document_type is None when the title is neither a timetable nor a calendar.
    """
    meta = {
        "document_type": None,
        "academic_year": None,
        "semester": None,
        "levels": None,
        "major": None,
        "programme": None,
        "revision": extract_revision(title),
    }

    title_lower = title.lower()

    # Document Type
    if re.search(r"time[\s-]?table", title_lower):
        meta["document_type"] = "TIMETABLE"
    elif "calendar" in title_lower:
        meta["document_type"] = "ACADEMIC_CALENDAR"

    # Academic Year: 2024/2025, 2024-2025, 2024/25
    ay_match = re.search(r"(20\d{2})\s*[/-]\s*(20\d{2}|\d{2})\b", title)
    if ay_match:
        start, end = ay_match.group(1), ay_match.group(2)
        if len(end) == 2:
            end = start[:2] + end
        meta["academic_year"] = f"{start}/{end}"

    # Semester: "Semester I", "Semester 1", "1st Semester"
    sem_match = re.search(r"\bSemester\s+(I{1,2}|[12])\b", title, re.IGNORECASE)
    if sem_match:
        sem = sem_match.group(1).upper()
        meta["semester"] = {"1": "I", "2": "II"}.get(sem, sem)
    else:
        ord_match = re.search(r"\b([12])(?:st|nd)\s+Semester\b", title, re.IGNORECASE)
        if ord_match:
            meta["semester"] = "I" if ord_match.group(1) == "1" else "II"

    meta["levels"] = extract_levels(title)
    return meta
