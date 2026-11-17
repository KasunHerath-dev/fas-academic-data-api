"""
Regenerate academic/data/module_catalogue.json from the module tracker document.

    PYTHONPATH=. python scripts/build_module_catalogue.py

The tracker (docs/acadamic/wusl_module_tracker.md) is the source of truth for
module titles and credits. Run this script whenever that file changes and
commit the regenerated JSON. Manually curated entries (non-credit courses and
timetable codes whose titles are not yet confirmed) live in
academic/data/module_overrides.json and are never touched by this script.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "docs" / "acadamic" / "wusl_module_tracker.md"
OUTPUT = ROOT / "academic" / "data" / "module_catalogue.json"

LEVEL_RE = re.compile(r"^##\s+\*\*LEVEL\s+(\d)\*\*")
SEMESTER_RE = re.compile(r"^###\s+Semester\s+(I{1,2})\b")
ROW_RE = re.compile(r"^\|\s*([A-Z]{4}\s+\d[\d†]\d{2})\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|")


def parse_tracker(text: str) -> list[dict]:
    modules = []
    level = None
    semester = None
    for line in text.splitlines():
        if m := LEVEL_RE.match(line):
            level, semester = int(m.group(1)), None
            continue
        if m := SEMESTER_RE.match(line):
            semester = m.group(1)
            continue
        if level is None or semester is None:
            continue
        if m := ROW_RE.match(line):
            code = re.sub(r"\s+", " ", m.group(1))
            modules.append({
                "code": code,
                "title": m.group(2).strip(),
                "credits": int(m.group(3)),
                "level": level,
                "semester": semester,
                "subject": code.split(" ")[0],
                "source": "wusl_module_tracker.md (Prospectus 2020/2021)",
            })
    return modules


def main() -> int:
    modules = parse_tracker(TRACKER.read_text(encoding="utf-8"))
    if not modules:
        print(f"No modules parsed from {TRACKER}", file=sys.stderr)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"modules": modules}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(modules)} modules to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
