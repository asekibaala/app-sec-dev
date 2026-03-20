from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScanRequest(BaseModel):
    """
    What the frontend sends us.
    Pydantic will reject the request automatically
    if 'domain' is missing or not a string.
    """
    domain: str

class ScanMeta(BaseModel):
    """
    Attached to every scan. Tracks identity and lifecycle.
    'status' moves through: running -> complete | failed
    'duration_ms' is None until the scan finishes.
    """
    id: str
    domain: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str  # "running" | "complete" | "failed"