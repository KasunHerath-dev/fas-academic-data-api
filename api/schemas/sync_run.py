from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SyncRunResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    documents_checked: int
    documents_changed: int
    documents_processed: int
    documents_skipped: int
    documents_failed: int
    error_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
