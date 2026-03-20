from pydantic import BaseModel
from typing import Optional

# Import each module's result model
from .scan import ScanMeta
from .whois import WhoisResult
from .dns import DNSResult
from .ssl import SSLResult
from .headers import HeadersResult
from .subdomains import SubdomainsResult

class ScanResult(BaseModel):
    """
    The complete output of one domain scan.
    This is what gets written to scans/{id}.json
    and what the frontend receives in the API response.

    Each module field is Optional — if a module crashes,
    we store None for that field and still return the
    rest of the scan. Partial results beat no results.
    """
    meta: ScanMeta                              # Always present
    whois: Optional[WhoisResult] = None
    dns: Optional[DNSResult] = None
    ssl: Optional[SSLResult] = None
    headers: Optional[HeadersResult] = None
    subdomains: Optional[SubdomainsResult] = None