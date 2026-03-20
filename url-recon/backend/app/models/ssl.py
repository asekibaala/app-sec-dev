from pydantic import BaseModel
from typing import Optional, List

class SSLResult(BaseModel):
    """
    SSL/TLS certificate analysis for the target domain on port 443.
    'grade' is computed by our service, not fetched from any external API:
        A+ = valid, 30+ days remaining, strong protocols only
        A  = valid, 30+ days remaining
        B  = valid but weak protocol detected (TLS 1.0/1.1)
        C  = expiring within 30 days
        F  = expired, self-signed, or connection failed
    'protocols' lists what the server accepts e.g. ["TLSv1.2", "TLSv1.3"]
    """
    grade: Optional[str] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    expiry_date: Optional[str] = None
    expiry_days: Optional[int] = None
    expired: bool = False
    self_signed: bool = False
    protocols: List[str] = []
    error: Optional[str] = None