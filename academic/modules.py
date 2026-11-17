"""
Module catalogue and module-code matching for FAS WUSL.

Timetable PDFs are read with text extraction / OCR, which damages some module
codes. Known failure modes (see docs/acadamic/module-code-review.md):

* The dagger ``†`` in the semester position (year-long modules such as
  ``CMIS 4†18``) is read as ``+``, ``ᵻ``, ``‡`` or ``t``.
* A prefix loses a letter: ``MIS 4142`` instead of ``CMIS 4142``.
* Letters and digits are confused: ``CMIS 2l23``, ``STAT 1O13``, ``5TAT 1113``.
* The space disappears: ``CMIS2123``.

``match_module_code`` repairs those cases and resolves the code against the
module catalogue (docs/acadamic/wusl_module_tracker.md plus curated overrides).
Rules it follows, from the academic-structure document §6:

* The raw text is always kept by the caller; this function never loses it.
* Every resolvable code is mapped onto the catalogue: a well-formed code that is
  missing from it resolves to the closest catalogue module of the same subject
  and level (status ``closest_match``). Codes seen in current timetables are
  listed in data/module_overrides.json so they match exactly instead.
* A code is kept as read only when the catalogue has no module for that subject
  and level (status ``unlisted``).
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "data"

DAGGER = "†"
# Characters OCR / text extraction produces for the dagger in the semester slot.
DAGGER_LOOKALIKES = set("+ᵻ‡⁺✝ł†tT*")
# OCR letter -> digit confusions, used only inside the 4-character number part.
DIGIT_LOOKALIKES = {"O": "0", "o": "0", "D": "0", "Q": "0", "I": "1", "l": "1", "i": "1", "|": "1",
                    "!": "1", "Z": "2", "z": "2", "S": "5", "s": "5", "B": "8", "G": "6", "g": "9"}
# OCR digit -> letter confusions, used only inside the subject prefix.
LETTER_LOOKALIKES = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z", "6": "G"}

SUBJECT_NAMES = {
    "CMIS": "Computing & Information Systems",
    "ELTN": "Electronics",
    "IMGT": "Industrial Management",
    "MATH": "Mathematics",
    "MMOD": "Mathematical Modelling",
    "STAT": "Statistics",
    "INDT": "Industrial Training",
    "ELPC": "English Language Proficiency Course",
}
KNOWN_PREFIXES = frozenset(SUBJECT_NAMES)

CANONICAL_CODE_RE = re.compile(r"^[A-Z]{4} [1-4][12†]\d{2}$")
# The English Language Proficiency Course has no numeric module code in the tracker
# or the academic-flow document; it is identified by level (paired with ELPT I / II).
ELPC_BY_LEVEL = {"1": "ELPC I", "2": "ELPC II"}
# Loose candidate: 3-5 prefix chars (letters or OCR digits), optional space/dash, 4 body chars.
_CANDIDATE_RE = re.compile(
    r"^(?P<prefix>[A-Za-z0158]{3,5})\s*[-–]?\s*(?P<body>[0-9OoDQIli|!ZzSsBGg+ᵻ‡⁺✝ł†tT*]{4})$"
)
# Used by the PDF parser to find code-like tokens inside cell text.
CODE_TOKEN_PATTERN = (
    r"(?<![A-Za-z0-9])[A-Z0-9]{3,4}\s?[0-9OIlSZB][0-9OIlSZB+ᵻ‡⁺✝†t][0-9OIlSZB]{2}(?![0-9A-Za-z])"
)


@dataclass
class CatalogueModule:
    code: str
    title: Optional[str]
    credits: Optional[int]
    level: Optional[int]
    semester: Optional[str]
    subject: str
    non_credit: bool = False
    confirmed: bool = True
    source: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["subject_name"] = SUBJECT_NAMES.get(self.subject)
        data["year_long"] = self.semester == "both"
        return data


@dataclass
class ModuleMatch:
    raw: str
    code: Optional[str]
    """Canonical code to use, or None when the text could not be resolved."""
    status: str
    """exact | normalized | closest_match | unlisted | named_course | unresolved"""
    confidence: float
    module: Optional[CatalogueModule] = None
    closest_match: Optional[str] = None
    notes: list[str] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.code is not None

    @property
    def changed(self) -> bool:
        return self.code is not None and self.code != self.raw

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "code": self.code,
            "status": self.status,
            "confidence": self.confidence,
            "closest_match": self.closest_match,
            "notes": list(self.notes),
            "module": self.module.to_dict() if self.module else None,
        }


@lru_cache(maxsize=1)
def load_catalogue() -> dict[str, CatalogueModule]:
    catalogue: dict[str, CatalogueModule] = {}
    tracker = json.loads((DATA_DIR / "module_catalogue.json").read_text(encoding="utf-8"))
    for m in tracker["modules"]:
        catalogue[m["code"]] = CatalogueModule(
            code=m["code"], title=m["title"], credits=m["credits"], level=m["level"],
            semester=m["semester"], subject=m["subject"], source=m.get("source", "tracker"),
        )
    overrides = json.loads((DATA_DIR / "module_overrides.json").read_text(encoding="utf-8"))
    for m in overrides["modules"]:
        if m["code"] in catalogue:
            continue  # the tracker wins over curated guesses
        catalogue[m["code"]] = CatalogueModule(
            code=m["code"], title=m.get("title"), credits=m.get("credits"), level=m.get("level"),
            semester=m.get("semester"), subject=m["subject"], non_credit=m.get("non_credit", False),
            confirmed=m.get("confirmed", False), source="module-code-review.md",
        )
    return catalogue


@lru_cache(maxsize=1)
def _named_courses() -> dict[str, dict]:
    overrides = json.loads((DATA_DIR / "module_overrides.json").read_text(encoding="utf-8"))
    return {c["name"].upper(): c for c in overrides.get("named_courses", [])}


def list_modules(level: Optional[int] = None, semester: Optional[str] = None,
                 subject: Optional[str] = None, include_unconfirmed: bool = True) -> list[CatalogueModule]:
    sem = normalize_semester(semester) if semester else None
    out = []
    for m in load_catalogue().values():
        if level is not None and m.level != level:
            continue
        if sem and m.semester not in (sem, "both"):
            continue
        if subject and m.subject != subject.upper():
            continue
        if not include_unconfirmed and not m.confirmed:
            continue
        out.append(m)
    return sorted(out, key=lambda m: (m.level or 0, m.semester or "", m.code))


def normalize_semester(value: Optional[str]) -> Optional[str]:
    """'1', 'I', 'Semester I', 'sem 1' -> 'I'; '2'/'II' -> 'II'."""
    if value is None:
        return None
    v = re.sub(r"(?i)^\s*(semester|sem)\.?\s*", "", str(value)).strip().upper()
    return {"1": "I", "I": "I", "2": "II", "II": "II"}.get(v, v or None)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _clean(raw: str) -> str:
    text = unicodedata.normalize("NFC", raw or "")
    text = re.sub(r"\(\s*[LPT]\s*\)", " ", text)  # drop "(L)" etc.
    return re.sub(r"\s+", " ", text).strip()


def _repair_body(body: str, notes: list[str]) -> Optional[str]:
    chars = list(body)
    for i, ch in enumerate(chars):
        if ch.isdigit():
            continue
        if i == 1 and ch in DAGGER_LOOKALIKES:
            if ch != DAGGER:
                notes.append(f"'{ch}' in the semester position read as '†' (year-long module)")
            chars[i] = DAGGER
            continue
        if ch in DIGIT_LOOKALIKES:
            notes.append(f"'{ch}' read as '{DIGIT_LOOKALIKES[ch]}'")
            chars[i] = DIGIT_LOOKALIKES[ch]
            continue
        return None
    out = "".join(chars)
    if out[0] not in "1234":
        return None
    if out[1] not in "12" + DAGGER:
        return None
    return out


def _repair_prefix(prefix: str, body: str, notes: list[str]) -> tuple[Optional[str], float]:
    """Return (prefix, confidence) or (None, 0)."""
    p = "".join(LETTER_LOOKALIKES.get(c, c) for c in prefix).upper()
    if p != prefix.upper():
        notes.append(f"prefix '{prefix}' read as '{p}'")
    if p in KNOWN_PREFIXES:
        return p, 1.0 if p == prefix else 0.9

    candidates = sorted(k for k in KNOWN_PREFIXES if _levenshtein(p, k) == 1)
    if not candidates and not (len(p) == 4 and p.isalpha()):
        return None, 0.0
    catalogue = load_catalogue()
    in_catalogue = [k for k in candidates if f"{k} {body}" in catalogue]
    if len(in_catalogue) == 1:
        notes.append(f"prefix '{p}' repaired to '{in_catalogue[0]}' (only match in catalogue)")
        return in_catalogue[0], 0.85
    if len(candidates) == 1 and not in_catalogue and len(p) != 4:
        notes.append(f"prefix '{p}' repaired to '{candidates[0]}' (only known prefix one letter away)")
        return candidates[0], 0.6
    if len(p) == 4 and p.isalpha() and not in_catalogue:
        # A well-formed but unknown 4-letter prefix may be a new subject: keep it, flag it.
        notes.append(f"unknown subject prefix '{p}'")
        return p, 0.5
    return None, 0.0


def _closest(code: str) -> Optional[str]:
    """
    Closest catalogue module for a well-formed code that is not in the catalogue.

    Candidates share the subject prefix and level; the same semester is preferred
    (falling back to any semester of that level). Ranking: fewest differing digits,
    then same module number, then faculty-confirmed tracker entries, then code order.
    Returns None when the catalogue has no module for that subject and level.
    """
    prefix, body = code.split(" ")
    catalogue = load_catalogue()
    same_level = [c for c in catalogue if c.split(" ")[0] == prefix and c.split(" ")[1][0] == body[0]]
    same_semester = [c for c in same_level if c.split(" ")[1][1] == body[1]]
    candidates = same_semester or same_level
    if not candidates:
        return None

    def rank(other: str):
        ob = other.split(" ")[1]
        return (_levenshtein(body, ob), ob[2] != body[2], not catalogue[other].confirmed, other)

    return min(candidates, key=rank)


def match_module_code(raw: Optional[str]) -> ModuleMatch:
    """Resolve raw timetable text to the best matching module code."""
    raw = raw or ""
    text = _clean(raw)
    catalogue = load_catalogue()

    if not text:
        return ModuleMatch(raw=raw, code=None, status="unresolved", confidence=0.0, notes=["empty"])

    named = _named_courses().get(text.upper())
    if named:
        return ModuleMatch(raw=raw, code=named["name"], status="named_course", confidence=1.0,
                           notes=["non-credit course" if named.get("non_credit") else "named course"])

    if text.upper() in catalogue:
        code = text.upper()
        return ModuleMatch(raw=raw, code=code, status="exact" if code == text else "normalized",
                           confidence=1.0, module=catalogue[code])

    m = _CANDIDATE_RE.match(text)
    if not m:
        return ModuleMatch(raw=raw, code=None, status="unresolved", confidence=0.0,
                           notes=["not a module code pattern"])

    notes: list[str] = []
    body = _repair_body(m.group("body"), notes)
    if body is None:
        return ModuleMatch(raw=raw, code=None, status="unresolved", confidence=0.0,
                           notes=[f"number part '{m.group('body')}' is not a valid level/semester/module"])
    prefix, prefix_conf = _repair_prefix(m.group("prefix"), body, notes)
    if prefix is None:
        return ModuleMatch(raw=raw, code=None, status="unresolved", confidence=0.0,
                           notes=[f"unknown subject prefix '{m.group('prefix')}'"])

    code = f"{prefix} {body}"
    confidence = round(prefix_conf * (0.95 if notes else 1.0), 2)
    if prefix == "ELPC" and body[0] in ELPC_BY_LEVEL:
        english = ELPC_BY_LEVEL[body[0]]
        notes.append(f"English Language Proficiency Course code '{code}' identified as {english} (level {body[0]})")
        return ModuleMatch(raw=raw, code=english, status="normalized", confidence=confidence,
                           module=catalogue[english], notes=notes)
    if code in catalogue:
        status = "exact" if code == text else "normalized"
        return ModuleMatch(raw=raw, code=code, status=status, confidence=confidence if status != "exact" else 1.0,
                           module=catalogue[code], notes=notes)

    # Well formed but not in the catalogue: resolve to the closest catalogue module
    # (same subject and level) so every scraped code maps onto the tracker.
    closest = _closest(code)
    if closest:
        notes.append(f"'{code}' is not in the module catalogue; matched to closest module {closest}")
        distance = _levenshtein(code, closest)
        return ModuleMatch(raw=raw, code=closest, status="closest_match",
                           confidence=round(min(confidence, 0.8 if distance <= 1 else 0.6), 2),
                           module=catalogue[closest], closest_match=closest, notes=notes)
    notes.append(f"no catalogue module for {prefix} level {body[0]}; code kept as read")
    return ModuleMatch(raw=raw, code=code, status="unlisted" if code == text else "normalized",
                       confidence=round(min(confidence, 0.5), 2), notes=notes)


def find_module_codes(text: str) -> list[tuple[str, int, int]]:
    """Return (matched_text, start, end) for code-like tokens in a line of cell text."""
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(CODE_TOKEN_PATTERN, text)]


def is_named_course(text: Optional[str]) -> bool:
    """True for non-code timetable entries such as 'Orientation' or 'Business English'."""
    return bool(text) and _clean(text).upper() in _named_courses()


def is_valid_module_code(code: Optional[str]) -> bool:
    """A canonical numeric code (CMIS 4142, CMIS 4†18) or a catalogue / named-course identifier (ELPC I)."""
    return bool(code) and (bool(CANONICAL_CODE_RE.fullmatch(code)) or code in load_catalogue() or is_named_course(code))
