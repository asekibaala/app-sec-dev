from datetime import datetime
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.limiter import limiter
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
from app.storage.scan_store import list_scans, load_scan, save_scan

router = APIRouter(prefix="/api")


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


@router.post("/scan", status_code=202)
async def start_scan(
    request: Request,
    body: ScanRequest,
    background_tasks: BackgroundTasks,
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
    save_scan(ScanResult(meta=meta))

    background_tasks.add_task(_run_scan_task, scan_id, domain)

    return {
        "scan_id": scan_id,
        "domain": domain,
        "status": "running",
        "message": f"Scan started. Poll GET /api/scan/{scan_id} for results.",
    }


async def _run_scan_task(scan_id: str, domain: str):
    try:
        await run_scan(domain, scan_id=scan_id)
    except Exception as exc:
        existing = load_scan(scan_id)
        if existing:
            existing.meta.status = "failed"
            existing.meta.completed_at = datetime.utcnow()
            save_scan(existing)
        print(f"[routes] Scan {scan_id} failed: {exc}")


@router.get("/scan/{scan_id}")
async def get_scan(scan_id: str):
    result = load_scan(scan_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scan {scan_id} not found.",
        )
    return result


@router.get("/scans")
async def get_all_scans():
    return {"scans": list_scans()}


@router.get("/scan/{scan_id}/report/html")
async def download_html_report(scan_id: str):
    result = load_scan(scan_id)
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
async def download_pdf_report(scan_id: str):
    result = load_scan(scan_id)
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
