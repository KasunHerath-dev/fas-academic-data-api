"""
Repair OCR-damaged module codes already stored in timetable_sessions.

    PYTHONPATH=. python scripts/normalize_module_codes.py           # report only
    PYTHONPATH=. python scripts/normalize_module_codes.py --apply   # write changes

For each session whose module_code resolves to a different canonical code with
enough confidence (e.g. 'MIS 4142' -> 'CMIS 4142', 'IMGT 3+34' -> 'IMGT 3†34'),
the original text is copied to raw_module_code (if empty) and module_code is
updated. Nothing else is touched. Low-confidence matches are only reported.
"""
import argparse
import sys
from collections import Counter

from academic.modules import is_valid_module_code, match_module_code
from api.services.module_enrichment import READ_TIME_REPAIR_MIN_CONFIDENCE


def plan_repairs(sessions):
    repairs, skipped = [], []
    for s in sessions:
        if not s.module_code:
            continue
        match = match_module_code(s.module_code)
        if not match.code or match.code == s.module_code or not is_valid_module_code(match.code):
            continue
        if match.confidence >= READ_TIME_REPAIR_MIN_CONFIDENCE:
            repairs.append((s, match))
        else:
            skipped.append((s, match))
    return repairs, skipped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Write the repairs to the database")
    args = parser.parse_args(argv)

    from database.database import SessionLocal
    from database.models.models import TimetableSession

    db = SessionLocal()
    try:
        repairs, skipped = plan_repairs(db.query(TimetableSession).all())
        for (old, new), n in sorted(Counter((s.module_code, m.code) for s, m in repairs).items()):
            print(f"repair  {old!r:>14} -> {new!r:<14} ({n} sessions)")
        for (old, new), n in sorted(Counter((s.module_code, m.code) for s, m in skipped).items()):
            print(f"review  {old!r:>14} ?> {new!r:<14} ({n} sessions, low confidence, not changed)")

        if not args.apply:
            print(f"\n{len(repairs)} sessions would be repaired. Re-run with --apply to write.")
            return 0
        for s, m in repairs:
            if not s.raw_module_code:
                s.raw_module_code = s.module_code
            s.module_code = m.code
        db.commit()
        print(f"\nRepaired {len(repairs)} sessions.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
