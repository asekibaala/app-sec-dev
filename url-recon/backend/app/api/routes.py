import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.scan import ScanRequest
from app.models.result import ScanResult
from app.services.scanner import run_scan
from app.storage.scan_store import load_scan, list_scans, save_scan
from app.models.scan import ScanMeta
from datetime import datetime
import uuid

# APIRouter lets us group related endpoints together.
# The prefix "/api" is applied to every route in this file.
# We register this router in main.py — keeping routing logic
# separate from the application setup is a FastAPI best practice.
router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    """
    Simple health check endpoint.
    The frontend and any monitoring tools call this first
    to confirm the API is reachable before doing anything else.
    """
    return {"status": "ok", "message": "URL Recon API is running"}


@router.post("/scan", status_code=202)
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
):
    """
    Triggers a new domain scan and returns immediately.

    HTTP 202 Accepted is the correct status code here —
    it means "we received your request and it is being processed"
    as opposed to 200 OK which implies the work is already done.

    BackgroundTasks is a FastAPI built-in that schedules work
    to run after the response has been sent to the client.
    This means the frontend gets the scan_id back in milliseconds
    while the actual scan runs in the background.

    The frontend uses the returned scan_id to poll
    GET /api/scan/{scan_id} until status is 'complete'.
    """
    # Sanitise the domain — strip whitespace, remove any
    # accidental scheme prefix the user might have included
    domain = request.domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.split("/")[0]  # Strip any path component

    # Generate the scan ID upfront so we can return it immediately
    # The background task will use this same ID when saving results
    scan_id = str(uuid.uuid4())

    # Write a 'running' placeholder immediately so the frontend
    # has something to poll against straight away
    meta = ScanMeta(
        id=scan_id,
        domain=domain,
        started_at=datetime.utcnow(),
        status="running",
    )
    save_scan(ScanResult(meta=meta))

    # Schedule the actual scan to run after this response returns
    background_tasks.add_task(_run_scan_task, scan_id, domain)

    return {
        "scan_id": scan_id,
        "domain": domain,
        "status": "running",
        "message": f"Scan started. Poll GET /api/scan/{scan_id} for results.",
    }


async def _run_scan_task(scan_id: str, domain: str):
    """
    The background scan task. Runs the full scan and saves
    the result. This function runs after the HTTP response
    has already been sent — the client never waits for it.

    We pass scan_id in so the scanner uses the same ID
    we already returned to the frontend.
    """
    try:
        await run_scan(domain, scan_id=scan_id)
    except Exception as e:
        # If the entire scan crashes, mark it as failed on disk
        # so the frontend knows to stop polling
        existing = load_scan(scan_id)
        if existing:
            existing.meta.status = "failed"
            existing.meta.completed_at = datetime.utcnow()
            save_scan(existing)
        print(f"[routes] Scan {scan_id} failed: {e}")


@router.get("/scan/{scan_id}")
async def get_scan(scan_id: str):
    """
    Returns the current state of a scan by its ID.

    If the scan is still running, this returns the partial
    result with status='running' — the frontend keeps polling.
    If the scan is complete, this returns the full result.
    If the scan ID doesn't exist, we return a 404.

    The frontend should poll this endpoint every 2–3 seconds
    until meta.status is 'complete' or 'failed'.
    """
    result = load_scan(scan_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scan {scan_id} not found.",
        )
    return result


@router.get("/scans")
async def get_all_scans():
    """
    Returns a lightweight list of all past scans — meta only,
    not the full module results. This powers the scan history
    view in the frontend without loading gigabytes of data.
    """
    return {"scans": list_scans()}