import re
import socket
from pydantic import BaseModel, field_validator


# RFC 1035 — a valid domain label is 1-63 characters,
# starts and ends with alphanumeric, allows hyphens in between.
# The full domain is up to 253 characters with dot separators.
DOMAIN_LABEL_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$')

# Private and reserved hostnames we refuse to scan.
# Scanning these would either be useless or a security risk —
# an attacker could use the tool to probe internal infrastructure.
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "broadcasthost",
}

# Private and reserved IP prefixes we refuse to scan.
BLOCKED_IP_PREFIXES = (
    "127.",    # loopback
    "0.",      # unspecified
    "10.",     # RFC1918 private
    "172.16.", # RFC1918 private
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.", # RFC1918 private
    "169.254.", # link-local
    "::1",     # IPv6 loopback
    "fc00:",   # IPv6 unique local
    "fe80:",   # IPv6 link-local
)


def _is_ip_address(value: str) -> bool:
    """
    Returns True if the value is a raw IP address.
    We use socket.inet_pton which handles both IPv4 and IPv6.
    We reject raw IPs because our WHOIS, SSL and subdomain
    modules are domain-oriented — they produce meaningless
    or misleading results when given an IP directly.
    """
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(family, value)
            return True
        except socket.error:
            pass
    return False


def _is_private_ip(value: str) -> bool:
    """
    Returns True if the value is a private, loopback,
    or link-local IP address we should refuse to scan.
    """
    return any(value.startswith(prefix) for prefix in BLOCKED_IP_PREFIXES)


def _validate_domain_labels(domain: str) -> bool:
    """
    Validates each label (segment between dots) of the domain
    against RFC 1035 rules. A domain like 'sub.example.com'
    has three labels: 'sub', 'example', 'com'.

    Rules per label:
      - 1 to 63 characters
      - Only alphanumeric and hyphens
      - Cannot start or end with a hyphen
    """
    labels = domain.split(".")
    for label in labels:
        if not label:
            # Empty label means double dot — e.g. "example..com"
            return False
        if not DOMAIN_LABEL_RE.match(label):
            return False
    return True


def sanitise_domain(raw: str) -> str:
    """
    Cleans up common user input patterns before validation.
    Strips whitespace, lowercases, removes scheme and path.
    Returns a bare domain string ready for validation.

    Examples:
        "  HTTPS://Example.COM/path " -> "example.com"
        "http://example.com"          -> "example.com"
        "example.com/some/path"       -> "example.com"
    """
    domain = raw.strip().lower()
    # Remove scheme if present
    domain = re.sub(r'^https?://', '', domain)
    # Remove path, query string, and fragment
    domain = domain.split("/")[0]
    domain = domain.split("?")[0]
    domain = domain.split("#")[0]
    # Remove port number if present — e.g. example.com:8080
    domain = domain.split(":")[0]
    return domain


class ScanRequest(BaseModel):
    """
    Validated scan request model.
    Pydantic calls the field_validator automatically when
    this model is instantiated — if validation fails,
    FastAPI returns a 422 response with a clear error message
    before our code ever runs.

    Replaces the original ScanRequest in scan.py —
    all validation is centralised here.
    """
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, raw: str) -> str:
        """
        Full validation pipeline for the domain field.
        Each check is a separate condition with its own
        error message so the analyst knows exactly what
        went wrong rather than getting a generic error.
        """
        # Step 1 — sanitise raw input
        domain = sanitise_domain(raw)

        # Step 2 — check it's not empty after sanitising
        if not domain:
            raise ValueError("Domain cannot be empty.")

        # Step 3 — enforce maximum domain length (RFC 1035)
        if len(domain) > 253:
            raise ValueError(
                f"Domain is too long ({len(domain)} chars). "
                "Maximum is 253 characters."
            )

        # Step 4 — reject raw IP addresses
        if _is_ip_address(domain):
            if _is_private_ip(domain):
                raise ValueError(
                    "Scanning private or loopback IP addresses is not permitted."
                )
            raise ValueError(
                "Please enter a domain name, not an IP address. "
                "Example: example.com"
            )

        # Step 5 — reject blocked hostnames
        if domain in BLOCKED_HOSTNAMES or domain.endswith(".local"):
            raise ValueError(
                f"'{domain}' is a private hostname and cannot be scanned."
            )

        # Step 6 — validate each label against RFC 1035
        if not _validate_domain_labels(domain):
            raise ValueError(
                f"'{domain}' is not a valid domain name. "
                "Use format: example.com or sub.example.com"
            )

        # Step 7 — must have at least one dot (TLD required)
        if "." not in domain:
            raise ValueError(
                f"'{domain}' is missing a TLD. "
                "Use format: example.com"
            )

        return domain