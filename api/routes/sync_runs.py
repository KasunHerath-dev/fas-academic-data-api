from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from typing import List, Optional

from api.dependencies.database import get_db
from api.schemas.sync_run import SyncRunResponse
from api.schemas.common import PaginatedResponse
from database.models.models import SyncRun

router = APIRouter(tags=["Sync Runs"])

@router.get(
    "/sync-runs", 
    response_model=PaginatedResponse[SyncRunResponse],
    summary="List synchronization runs",
    description="""
    Returns the history of ingestion activity.
    The API only reads SyncRun information; it does not start synchronization jobs.
    """
)
def get_sync_runs(
    status: Optional[str] = Query(None, description="Sync status (e.g., 'success', 'failed')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    stmt = select(SyncRun).order_by(desc(SyncRun.started_at))
    
    if status:
        stmt = stmt.where(SyncRun.status == status)
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()
    
    stmt = stmt.offset(skip).limit(limit)
    runs = db.execute(stmt).scalars().all()
    
    return {"data": runs, "count": total}

@router.get(
    "/sync-runs/latest", 
    response_model=SyncRunResponse,
    summary="Get latest synchronization run",
    description="Yields the success/failure state and modified document counts of the most recent scraping job."
)
def get_latest_sync_run(db: Session = Depends(get_db)):
    stmt = select(SyncRun).order_by(desc(SyncRun.started_at)).limit(1)
    run = db.execute(stmt).scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="No sync runs found.")
    return run
