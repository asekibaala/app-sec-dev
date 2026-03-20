from pydantic import BaseModel
from typing import Optional, List

class WhoisResult(BaseModel):
    """
    WHOIS registry data for the target domain.
    All fields are Optional — WHOIS responses vary
    wildly by registrar and TLD. Never assume a field exists.
    'error' is populated if the lookup times out or fails,
    so the rest of the scan can still continue.
    """
    registrar: Optional[str] = None
    created: Optional[str] = None
    expires: Optional[str] = None
    updated: Optional[str] = None
    status: Optional[List[str]] = []
    nameservers: Optional[List[str]] = []
    error: Optional[str] = None