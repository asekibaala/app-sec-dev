from pydantic import BaseModel
from typing import List, Optional

class Subdomain(BaseModel):
    """
    A single discovered subdomain.
    'ip' can be None if the subdomain resolves but
    returns no A record (e.g. CNAME-only entries).
    """
    name: str
    ip: Optional[str] = None

class SubdomainsResult(BaseModel):
    """
    All subdomains discovered via DNS bruteforce.
    'total' is a convenience count so the frontend
    doesn't have to compute len(subdomains) itself.
    """
    subdomains: List[Subdomain] = []
    total: int = 0
    error: Optional[str] = None