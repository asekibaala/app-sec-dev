from pydantic import BaseModel
from typing import List, Optional

class HeaderFinding(BaseModel):
    """
    A single security header check result.
    'status' uses a four-level severity scale:
        PASS = header present and correctly configured
        INFO = header present, noting its value for awareness
        WARN = header missing but not critical
        FAIL = header missing and poses a real security risk
    'value' is None when the header is absent entirely.
    'message' is a human-readable explanation shown in the UI.
    """
    header: str
    status: str             # "PASS" | "WARN" | "FAIL" | "INFO"
    value: Optional[str] = None
    message: str

class HeadersResult(BaseModel):
    """
    Aggregated HTTP security header analysis.
    'findings' is a list of individual header checks —
    one entry per security header we evaluate.
    Headers we check: CSP, HSTS, X-Frame-Options,
    X-Content-Type-Options, Referrer-Policy, Permissions-Policy.
    """
    url: Optional[str] = None
    status_code: Optional[int] = None
    findings: List[HeaderFinding] = []
    error: Optional[str] = None