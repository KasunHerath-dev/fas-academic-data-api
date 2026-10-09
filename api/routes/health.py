from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.dependencies.database import get_db

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    summary="Health check",
    description="Returns API service health status and database connection status."
)
def health_check(db: Session = Depends(get_db)):
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass
        
    return {
        "status": "ok",
        "service": "fas-academic-data-api",
        "database": db_status
    }
