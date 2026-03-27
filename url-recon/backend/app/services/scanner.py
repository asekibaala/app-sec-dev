import asyncio
import uuid
from datetime import datetime
from app.models.scan import ScanMeta
from app.models.result import ScanResult
from app.services.whois_service import run_whois
from app.services.dns_service import run_dns
from app.services.ssl_service import run_ssl
from app.services.headers_service import run_headers
from app.services.subdomain_service import run_subdomains
from app.storage.scan_store import save_scan


async def run_scan(domain: str) -> ScanResult:
    """
    The main scan orchestrator. This is the single function
    the API layer calls — it owns the entire scan lifecycle:

        1. Generate a unique scan ID
        2. Record the start time
        3. Fire all 5 modules simultaneously
        4. Collect results — partial results are acceptable
        5. Record end time and compute duration
        6. Save the complete result to disk
        7. Return the result to the API layer

    Each module is wrapped in its own try/except inside
    _safe_run() so a failure in one module never prevents
    the others from completing or the result from being saved.
    """

    # Generate a unique ID for this scan
    # uuid4() is random — no two scans will ever share an ID
    scan_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    # Write a 'running' record immediately so the frontend
    # can poll for status as soon as the scan is triggered
    meta = ScanMeta(
        id=scan_id,
        domain=domain,
        started_at=started_at,
        status="running",
    )

    # Save immediately with running status so the frontend
    # has something to poll against straight away
    save_scan(ScanResult(meta=meta))

    async def _safe_run(coro, module_name: str):
        """
        Wraps any coroutine in a try/except.
        If a module raises an unhandled exception we log it
        and return None — the orchestrator treats None as
        'module failed' and stores it as null in the result.
        One bad module should never kill the whole scan.
        """
        try:
            return await coro
        except Exception as e:
            print(f"[scanner] {module_name} failed: {e}")
            return None

    # Fire all 5 modules simultaneously — this is the core of the
    # performance design. Total scan time ≈ slowest single module,
    # not the sum of all modules.
    print(f"[scanner] Starting scan {scan_id} for {domain}")

    (
        whois_result,
        dns_result,
        ssl_result,
        headers_result,
        subdomains_result,
    ) = await asyncio.gather(
        _safe_run(run_whois(domain),       "WHOIS"),
        _safe_run(run_dns(domain),         "DNS"),
        _safe_run(run_ssl(domain),         "SSL"),
        _safe_run(run_headers(domain),     "Headers"),
        _safe_run(run_subdomains(domain),  "Subdomains"),
    )

    completed_at = datetime.utcnow()

    # Compute duration in milliseconds for the UI to display
    duration_ms = int(
        (completed_at - started_at).total_seconds() * 1000
    )

    # Update meta with completion info
    meta.completed_at = completed_at
    meta.duration_ms = duration_ms
    meta.status = "complete"

    # Assemble the final result
    result = ScanResult(
        meta=meta,
        whois=whois_result,
        dns=dns_result,
        ssl=ssl_result,
        headers=headers_result,
        subdomains=subdomains_result,
    )

    # Persist to disk — overwrites the 'running' placeholder
    save_scan(result)

    print(f"[scanner] Scan {scan_id} complete in {duration_ms}ms")

    return result