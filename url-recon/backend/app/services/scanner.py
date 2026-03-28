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


async def run_scan(domain: str, scan_id: str | None = None) -> ScanResult:
    """
    Main scan orchestrator. Accepts an optional scan_id —
    if one is provided by the API layer we use it, otherwise
    we generate a new one. This lets the API return the scan_id
    to the frontend before the scan starts running.
    """
    scan_id = scan_id or str(uuid.uuid4())
    started_at = datetime.utcnow()

    meta = ScanMeta(
        id=scan_id,
        domain=domain,
        started_at=started_at,
        status="running",
    )

    async def _safe_run(coro, module_name: str):
        """
        Wraps any module coroutine in a try/except.
        Returns None on failure so one broken module never
        prevents the rest of the scan from completing.
        """
        try:
            return await coro
        except Exception as e:
            print(f"[scanner] {module_name} failed: {e}")
            return None

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
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    meta.completed_at = completed_at
    meta.duration_ms = duration_ms
    meta.status = "complete"

    result = ScanResult(
        meta=meta,
        whois=whois_result,
        dns=dns_result,
        ssl=ssl_result,
        headers=headers_result,
        subdomains=subdomains_result,
    )

    save_scan(result)
    print(f"[scanner] Scan {scan_id} complete in {duration_ms}ms")
    return result