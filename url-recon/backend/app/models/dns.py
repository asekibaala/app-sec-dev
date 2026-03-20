from pydantic import BaseModel
from typing import List, Optional

class DNSResult(BaseModel):
    """
    DNS records enumerated for the target domain.
    Each field maps directly to a DNS record type.
    Empty list means the record type exists but returned
    no results — None would mean we never queried it.
    SOA is a single string because only one SOA record
    can exist per zone.
    """
    A: List[str] = []       # IPv4 addresses
    AAAA: List[str] = []    # IPv6 addresses
    MX: List[str] = []      # Mail exchange servers
    TXT: List[str] = []     # SPF, DKIM, verification tokens
    NS: List[str] = []      # Authoritative nameservers
    SOA: Optional[str] = None  # Start of authority record
    error: Optional[str] = None  # If the DNS query fails, we can still return other scan results.