import re

def extract_metadata(title: str):
    """
    Extract metadata deterministically from a FAS document title.
    Returns a dict with document_type, academic_year, semester, levels, major, programme, revision.
    """
    meta = {
        "document_type": None,
        "academic_year": None,
        "semester": None,
        "levels": None,
        "major": None,
        "programme": None,
        "revision": "original" # default assumption unless specified
    }
    
    title_lower = title.lower()
    
    # 1. Revision detection
    if "re-revised" in title_lower:
        meta["revision"] = "re-revised"
    elif "revised" in title_lower:
        meta["revision"] = "revised"
        
    # 2. Document Type
    if "time table" in title_lower or "timetable" in title_lower:
        meta["document_type"] = "TIMETABLE"
    elif "calendar" in title_lower:
        meta["document_type"] = "ACADEMIC_CALENDAR"
        
    # 3. Academic Year
    # matches 2024/2025 or 2024-2025
    ay_match = re.search(r"(\d{4})[/-](\d{4})", title)
    if ay_match:
        meta["academic_year"] = f"{ay_match.group(1)}/{ay_match.group(2)}"
        
    # 4. Semester
    sem_match = re.search(r"\bSemester\s+([IVX]+)\b", title, re.IGNORECASE)
    if sem_match:
        meta["semester"] = sem_match.group(1).upper()
        
    # 5. Levels
    # Looks for "Level 1" or "Level 1,2,3 & 4" etc.
    level_match = re.search(r"\bLevel\s+([\d,\s&]+)", title, re.IGNORECASE)
    if level_match:
        level_str = level_match.group(1)
        levels = []
        for digit in re.findall(r"\d", level_str):
            levels.append(int(digit))
        if levels:
            meta["levels"] = sorted(list(set(levels)))
            
    return meta
