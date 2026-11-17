"""Keep the `modules` table in step with academic/data (the module catalogue)."""
from sqlalchemy.orm import Session

from academic.modules import load_catalogue
from database.models.models import Module


def sync_module_catalogue(db: Session) -> int:
    """
    Insert catalogue modules missing from the `modules` table and fill in empty
    titles/levels. Existing non-empty values are never overwritten, so manual
    corrections in the database survive. Returns the number of inserted rows.
    """
    existing = {m.module_code: m for m in db.query(Module).all()}
    added = 0
    for entry in load_catalogue().values():
        row = existing.get(entry.code)
        level = str(entry.level) if entry.level is not None else None
        if row is None:
            db.add(Module(module_code=entry.code, module_name=entry.title, level=level))
            added += 1
            continue
        if not row.module_name and entry.title:
            row.module_name = entry.title
        if not row.level and level:
            row.level = level
    db.commit()
    return added
