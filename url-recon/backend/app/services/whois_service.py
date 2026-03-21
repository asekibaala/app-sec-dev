import whois
import asyncio
from datetime import datetime
from app.models.whois import WhoisResult


def _format_date(value) -> str | None:
    """
    WHOIS dates are wildly inconsistent across registrars.
    They can come back as a datetime object, a list of datetimes,
    or a plain string. This helper normalises all three cases
    into a single consistent ISO format string.
    """
    if value is None:
        return None
    # Some registrars return a list of dates — take the first one
    if isinstance(value, list):
        value = value[0]
    # If it's already a datetime object, format it directly
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    # Otherwise treat it as a string and return as-is
    return str(value)


def _format_list(value) -> list[str]:
    """
    Nameservers and status fields can come back as a single
    string or a list of strings depending on the registrar.
    This normalises both into a clean list of lowercase strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).lower() for v in value]
    return [str(value).lower()]


def _run_whois(domain: str) -> WhoisResult:
    """
    The actual blocking WHOIS query.
    We isolate this in its own function because python-whois
    is a synchronous library — it blocks the thread while it
    waits for the registry response. We'll run it in a thread
    pool from the async wrapper below so it doesn't block
    the FastAPI event loop.
    """
    try:
        data = whois.whois(domain)

        return WhoisResult(
            registrar=data.registrar,
            created=_format_date(data.creation_date),
            expires=_format_date(data.expiration_date),
            updated=_format_date(data.updated_date),
            status=_format_list(data.status),
            nameservers=_format_list(data.name_servers),
        )

    except Exception as e:
        # Never let one module crash the whole scan.
        # Capture the error and return it as data instead.
        return WhoisResult(error=str(e))


async def run_whois(domain: str) -> WhoisResult:
    """
    Async wrapper around the blocking WHOIS query.

    asyncio.get_event_loop().run_in_executor() moves the
    blocking _run_whois() call into a background thread pool.
    This means FastAPI's event loop stays free to handle
    other requests while we wait for the WHOIS registry
    to respond — which can take several seconds.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_whois, domain)
    return result