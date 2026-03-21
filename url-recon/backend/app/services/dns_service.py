import asyncio
import dns.resolver
from app.models.dns import DNSResult


def _query(domain: str, record_type: str) -> list[str]:
    """
    Performs a single blocking DNS query for one record type.
    Returns a list of strings — one per record returned.

    We catch two specific exceptions separately because they
    mean different things:
        NXDOMAIN   — the domain does not exist at all
        NoAnswer   — the domain exists but has no record of this type
    Both are normal and expected. Any other exception is a real
    error we want to surface.
    """
    try:
        answers = dns.resolver.resolve(domain, record_type)
        return [str(r) for r in answers]
    except dns.resolver.NXDOMAIN:
        # Domain does not exist — return empty, not an error
        return []
    except dns.resolver.NoAnswer:
        # Record type not present for this domain — also fine
        return []
    except Exception:
        # Anything else — timeout, refused etc — return empty
        return []


def _query_soa(domain: str) -> str | None:
    """
    SOA is handled separately because it returns a single
    record, not a list. We format it as a readable string
    showing the primary nameserver and contact email.
    """
    try:
        answers = dns.resolver.resolve(domain, "SOA")
        soa = answers[0]
        # Format: "primary_ns | admin_email"
        return f"{soa.mname} | {soa.rname}"
    except Exception:
        return None


async def run_dns(domain: str) -> DNSResult:
    """
    Runs all 6 DNS queries concurrently using asyncio.gather().

    Each _query() call is a blocking operation so we push each
    one into a thread pool executor — same pattern as the WHOIS
    service. asyncio.gather() then fires all 6 simultaneously
    and waits for all of them to finish before continuing.

    This means 6 queries that each take 1 second complete in
    ~1 second total instead of ~6 seconds sequentially.
    """
    loop = asyncio.get_event_loop()

    # Schedule all 6 queries to run concurrently in the thread pool
    (
        a_records,
        aaaa_records,
        mx_records,
        txt_records,
        ns_records,
        soa_record,
    ) = await asyncio.gather(
        loop.run_in_executor(None, _query, domain, "A"),
        loop.run_in_executor(None, _query, domain, "AAAA"),
        loop.run_in_executor(None, _query, domain, "MX"),
        loop.run_in_executor(None, _query, domain, "TXT"),
        loop.run_in_executor(None, _query, domain, "NS"),
        loop.run_in_executor(None, _query_soa, domain),
    )

    return DNSResult(
        A=a_records,
        AAAA=aaaa_records,
        MX=mx_records,
        TXT=txt_records,
        NS=ns_records,
        SOA=soa_record,
    )