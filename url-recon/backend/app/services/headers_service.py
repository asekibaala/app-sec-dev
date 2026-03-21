import httpx
import asyncio
from urllib.parse import urlparse
from app.models.headers import HeadersResult, HeaderFinding


SECURITY_HEADERS = [
    {
        "header": "Content-Security-Policy",
        "missing_status": "FAIL",
        "missing_message": "CSP is missing — browsers will load resources "
                           "from any origin, enabling XSS attacks.",
        "present_message": "CSP header is present.",
    },
    {
        "header": "Strict-Transport-Security",
        "missing_status": "FAIL",
        "missing_message": "HSTS is missing — the browser may connect over "
                           "HTTP, enabling downgrade attacks.",
        "present_message": "HSTS header is present.",
    },
    {
        "header": "X-Frame-Options",
        "missing_status": "WARN",
        "missing_message": "X-Frame-Options is missing — the page can be "
                           "embedded in an iframe, enabling clickjacking.",
        "present_message": "X-Frame-Options header is present.",
    },
    {
        "header": "X-Content-Type-Options",
        "missing_status": "WARN",
        "missing_message": "X-Content-Type-Options is missing — browsers may "
                           "sniff the content type and execute unexpected code.",
        "present_message": "X-Content-Type-Options header is present.",
    },
    {
        "header": "Referrer-Policy",
        "missing_status": "WARN",
        "missing_message": "Referrer-Policy is missing — full URLs may leak "
                           "to third parties via the Referer header.",
        "present_message": "Referrer-Policy header is present.",
    },
    {
        "header": "Permissions-Policy",
        "missing_status": "INFO",
        "missing_message": "Permissions-Policy is missing — browser features "
                           "like camera and microphone are not explicitly restricted.",
        "present_message": "Permissions-Policy header is present.",
    },
]


def _normalise_url(target: str) -> tuple[str, str | None]:
    """
    Takes whatever the user gave us and returns two URLs:
        root_url  — always the scheme + domain root e.g. https://example.com
        path_url  — the full URL with path if one was provided, else None

    Handles all three input formats:
        "example.com"              -> root="https://example.com", path=None
        "https://example.com"      -> root="https://example.com", path=None
        "example.com/online"       -> root="https://example.com", path="https://example.com/online"
        "https://example.com/online" -> root="https://example.com", path="https://example.com/online"
    """
    # If no scheme is present, add one so urlparse works correctly
    if not target.startswith("http"):
        target = f"https://{target}"

    parsed = urlparse(target)

    # Root is always just scheme + netloc — no path
    root_url = f"{parsed.scheme}://{parsed.netloc}"

    # Path URL is only set if the user gave us an actual path
    has_path = parsed.path not in ("", "/")
    path_url = target if has_path else None

    return root_url, path_url


def _analyse_headers(headers: dict) -> list[HeaderFinding]:
    """
    Checks each security header definition against the
    response headers dict. Returns one HeaderFinding per header.
    Headers are normalised to lowercase for consistent lookup
    since HTTP headers are case-insensitive.
    """
    findings = []
    for definition in SECURITY_HEADERS:
        header_name = definition["header"].lower()
        value = headers.get(header_name)

        if value:
            findings.append(HeaderFinding(
                header=definition["header"],
                status="PASS",
                value=value,
                message=definition["present_message"],
            ))
        else:
            findings.append(HeaderFinding(
                header=definition["header"],
                status=definition["missing_status"],
                value=None,
                message=definition["missing_message"],
            ))
    return findings


async def _fetch(client: httpx.AsyncClient, url: str) -> dict:
    """
    Makes a single GET request and returns the response headers
    as a plain dict. Returns empty dict on failure so the caller
    can still continue with whatever it has.
    """
    try:
        response = await client.get(url)
        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }
    except Exception as e:
        return {"url": url, "status_code": None, "headers": {}, "error": str(e)}


async def run_headers(target: str) -> HeadersResult:
    """
    Checks security headers for the target.

    If only a domain or root URL was given — checks the root only.
    If a path was given e.g. example.com/online — checks BOTH the
    root and the path URL, then merges the findings:
        - If the root has a header the path is missing, flag it
        - If the path has a header the root is missing, flag it
        - PASS only if BOTH URLs return the header correctly

    This matters because some servers set headers globally at the
    root but strip them on specific routes — a real misconfiguration
    a security analyst needs to know about.
    """
    root_url, path_url = _normalise_url(target)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0 (URL Recon Security Scanner)"},
        verify=False,
    ) as client:

        # Always fetch the root
        root_data = await _fetch(client, root_url)

        # Only fetch the path if one was provided
        path_data = await _fetch(client, path_url) if path_url else None

    # If no path was given — simple single-URL analysis
    if path_data is None:
        findings = _analyse_headers(root_data["headers"])
        return HeadersResult(
            url=root_data["url"],
            status_code=root_data["status_code"],
            findings=findings,
            error=root_data.get("error"),
        )

    # Both root and path were fetched — merge findings.
    # A header only counts as PASS if it is present on BOTH URLs.
    # If it differs between root and path we flag it as WARN
    # so the analyst knows there is an inconsistency.
    merged_findings = []
    root_headers = root_data["headers"]
    path_headers = path_data["headers"]

    for definition in SECURITY_HEADERS:
        header_name = definition["header"].lower()
        root_value = root_headers.get(header_name)
        path_value = path_headers.get(header_name)

        if root_value and path_value:
            # Present on both — PASS, show both values if they differ
            if root_value == path_value:
                message = definition["present_message"]
                value = root_value
            else:
                # Same header, different values — flag the inconsistency
                message = (
                    f"Header present on both URLs but values differ. "
                    f"Root: {root_value[:60]} | "
                    f"Path: {path_value[:60]}"
                )
                value = root_value
            merged_findings.append(HeaderFinding(
                header=definition["header"],
                status="PASS" if root_value == path_value else "WARN",
                value=value,
                message=message,
            ))

        elif root_value and not path_value:
            # Present on root but missing on the specific path — real issue
            merged_findings.append(HeaderFinding(
                header=definition["header"],
                status="WARN",
                value=root_value,
                message=(
                    f"Header present on root ({root_url}) but MISSING "
                    f"on path ({path_url}). Path-level misconfiguration."
                ),
            ))

        elif path_value and not root_value:
            # Present on path but missing on root — also flag it
            merged_findings.append(HeaderFinding(
                header=definition["header"],
                status="WARN",
                value=path_value,
                message=(
                    f"Header present on path ({path_url}) but MISSING "
                    f"on root ({root_url}). Root-level misconfiguration."
                ),
            ))

        else:
            # Missing on both — use the standard missing severity
            merged_findings.append(HeaderFinding(
                header=definition["header"],
                status=definition["missing_status"],
                value=None,
                message=definition["missing_message"],
            ))

    return HeadersResult(
        url=f"{root_url} + {path_url}",
        status_code=root_data["status_code"],
        findings=merged_findings,
    )