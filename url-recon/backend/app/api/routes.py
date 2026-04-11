"""
routes.py — HTTP endpoints for URL Recon.

Key change from the old version:
  BEFORE: imported from app.storage.scan_store (JSON files)
  AFTER:  imports from app.database.db_store   (PostgreSQL)

Session injection pattern:
  Route handlers that READ from the DB use:
      db: AsyncSession = Depends(get_db)
  FastAPI calls get_db(), gets a fresh session, passes it to the route,
  then closes it automatically when the response is sent.

  Background tasks (the actual scan) CANNOT use the route's session —
  that session closes the moment the HTTP response is sent back to the
  frontend, but the background task keeps running for 30+ seconds.
  So _run_scan_task() creates its OWN fresh session via AsyncSessionLocal.
"""

from datetime import datetime
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.limiter import limiter
from app.database.db_store import delete_scan, list_scans, load_scan, save_scan
from app.database.engine import AsyncSessionLocal, get_db
from app.models.result import ScanResult
from app.models.scan import ScanMeta
from app.models.validators import ScanRequest
from app.reports.generator import (
    PdfGenerationUnavailableError,
    generate_html_report,
    generate_pdf_report,
    get_pdf_generation_status,
)
from app.services.scanner import run_scan

router = APIRouter(prefix="/api")


# ─── Health ──────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    pdf_reports_available, pdf_reports_error = get_pdf_generation_status()
    response = {
        "status": "ok",
        "message": "URL Recon API is running",
        "pdf_reports_available": pdf_reports_available,
    }
    if pdf_reports_error:
        response["pdf_reports_error"] = pdf_reports_error
    return response


# ─── Start a scan ─────────────────────────────────────────────────────────────

@router.post("/scan", status_code=202)
async def start_scan(
    request: Request,
    body: ScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    # Depends(get_db) tells FastAPI: "before calling this function, run
    # get_db() and give me the session it yields". FastAPI handles the
    # entire lifecycle — open, pass in, close — automatically.
):
    domain = body.domain
    limiter.enforce_scan_limits(request, domain)

    scan_id = str(uuid.uuid4())
    meta = ScanMeta(
        id=scan_id,
        domain=domain,
        started_at=datetime.utcnow(),
        status="running",
    )

    # Write the initial "running" row to Postgres immediately so the
    # frontend can start polling before the scan finishes.
    await save_scan(ScanResult(meta=meta), db)

    # Schedule the actual scan to run AFTER the HTTP response is sent.
    # BackgroundTasks is FastAPI's built-in task queue for fire-and-forget work.
    # We pass scan_id and domain as plain values — NOT the db session,
    # because that session closes when this route function returns.
    background_tasks.add_task(_run_scan_task, scan_id, domain)

    return {
        "scan_id": scan_id,
        "domain": domain,
        "status": "running",
        "message": f"Scan started. Poll GET /api/scan/{scan_id} for results.",
    }


async def _run_scan_task(scan_id: str, domain: str) -> None:
    """
    Runs in the background after the HTTP 202 response is sent.

    Creates its OWN database session because the route's session is
    already closed by the time this function gets to do serious work.

    `async with AsyncSessionLocal() as session:` — opens a fresh session,
    runs the scan (which saves progress to Postgres), then closes cleanly.
    If run_scan() raises, we catch it and mark the scan as failed in the DB.
    """
    async with AsyncSessionLocal() as session:
        try:
            await run_scan(domain, scan_id=scan_id, db=session)
        except Exception as exc:
            # If the scan crashes, update the row to status="failed" so the
            # frontend stops polling and shows an error state.
            existing = await load_scan(scan_id, session)
            if existing:
                existing.meta.status = "failed"
                existing.meta.completed_at = datetime.utcnow()
                await save_scan(existing, session)
            print(f"[routes] Scan {scan_id} failed: {exc}")


# ─── Fetch a single scan ──────────────────────────────────────────────────────

@router.get("/scan/{scan_id}")
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the full ScanResult for one scan ID.
    The frontend polls this every 2 seconds until status = "complete".
    load_scan() does a primary-key lookup — O(1), instant regardless of
    how many scans are stored.
    """
    result = await load_scan(scan_id, db)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scan {scan_id} not found.",
        )
    return result


# ─── List all scans ───────────────────────────────────────────────────────────

@router.get("/scans")
async def get_all_scans(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a lightweight list of all scans (meta only, not full results).
    Used by the frontend's history sidebar.
    list_scans() returns only the columns needed for the list view —
    no heavy result_json loaded into memory.
    """
    return {"scans": await list_scans(db)}


# ─── Delete a scan ────────────────────────────────────────────────────────────

@router.delete("/scan/{scan_id}", status_code=200)
async def remove_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a scan from the database by ID.
    Returns 404 if the scan doesn't exist.
    This is a new endpoint — the old file-based store had no delete support.
    """
    deleted = await delete_scan(scan_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return {"message": f"Scan {scan_id} deleted."}


# ─── Reports ──────────────────────────────────────────────────────────────────

@router.get("/scan/{scan_id}/report/html")
async def download_html_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await load_scan(scan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if result.meta.status != "complete":
        raise HTTPException(status_code=400, detail="Scan not complete yet.")

    path = generate_html_report(result)
    return FileResponse(
        path=str(path),
        media_type="text/html",
        filename=f"recon-{result.meta.domain}-{scan_id[:8]}.html",
    )


@router.get("/scan/{scan_id}/report/pdf")
async def download_pdf_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await load_scan(scan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if result.meta.status != "complete":
        raise HTTPException(status_code=400, detail="Scan not complete yet.")

    try:
        path = generate_pdf_report(result)
    except PdfGenerationUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"recon-{result.meta.domain}-{scan_id[:8]}.pdf",
    )
