from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from academic.modules import list_modules, match_module_code
from api.schemas.module_catalogue import CatalogueModuleResponse, ModuleResolutionResponse

router = APIRouter(tags=["Module Catalogue"])


@router.get(
    "/catalogue/modules",
    response_model=List[CatalogueModuleResponse],
    summary="List catalogue modules",
    description="""
    Module titles and credits from the FAS module catalogue (WUSL Prospectus 2020/2021
    tracker), plus modules seen in current timetables that the tracker does not list
    (`confirmed: false`, title may be null until the faculty confirms it).

    Year-long modules use `†` in the semester position (e.g. `CMIS 4†18`) and have
    `semester: "both"`; they are included when filtering by either semester.

    The catalogue says which modules exist, not which modules a given student takes.
    Use the timetable endpoints for what is actually scheduled.
    """,
)
def get_catalogue_modules(
    level: Optional[int] = Query(None, ge=1, le=4, description="Level 1-4"),
    semester: Optional[str] = Query(None, description="'1', '2', 'I' or 'II'"),
    subject: Optional[str] = Query(None, description="Subject prefix, e.g. 'CMIS'"),
    include_unconfirmed: bool = Query(True, description="Include entries not yet confirmed by the faculty"),
):
    return [m.to_dict() for m in list_modules(level, semester, subject, include_unconfirmed)]


@router.get(
    "/catalogue/modules/resolve",
    response_model=ModuleResolutionResponse,
    summary="Resolve a module code",
    description="""
    Resolve raw module-code text (as printed or as mis-read from a PDF) to the
    closest valid module. Examples: `MIS 4142` → `CMIS 4142`, `IMGT 3+34` →
    `IMGT 3†34`, `cmis2123` → `CMIS 2123`.

    A well-formed code that is missing from the catalogue is returned unchanged
    with `status: "unlisted"` and the nearest catalogue entry in `closest_match`.
    """,
)
def resolve_module_code(code: str = Query(..., min_length=1, max_length=64, description="Raw module code text")):
    match = match_module_code(code)
    if match.status == "unresolved":
        raise HTTPException(status_code=404, detail=f"Could not resolve '{code}' to a module code: {'; '.join(match.notes)}")
    return match.to_dict()
