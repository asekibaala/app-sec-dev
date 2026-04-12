"""
routes.py — HTTP endpoints for Bugbounty hut.

The scan/report routes still use PostgreSQL-backed persistence, but
authentication is now handled by FastAPI Users with a JWT bearer backend.
"""

from datetime import datetime
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.limiter import limiter
from app.auth.schemas import (
    AuthenticatedUserResponse,
    LoginRequest,
    LoginResponse,
)
from app.auth.users import (
    current_active_user,
    get_jwt_strategy,
    get_user_manager,
)
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


@router.get("/health")
async def health():
    """
    Public health endpoint used by the frontend and monitoring checks.
    """
    pdf_reports_available, pdf_reports_error = get_pdf_generation_status()
    response = {
        "status": "ok",
        "message": "URL Recon API is running",
        "pdf_reports_available": pdf_reports_available,
    }
    if pdf_reports_error:
        response["pdf_reports_error"] = pdf_reports_error
    return response


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    user_manager=Depends(get_user_manager),
):
    """
    Authenticate a local user through FastAPI Users and return a bearer token.

    We keep a JSON username/password contract for the frontend, but the
    password verification and token issuance are framework-managed.
    """
    user = await user_manager.authenticate_username_password(
        body.username,
        body.password,
    )
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    strategy = get_jwt_strategy()
    token = await strategy.write_token(user)
    await user_manager.on_after_login(user, request)
    return LoginResponse(access_token=token, token_type="bearer")


@router.get("/auth/me", response_model=AuthenticatedUserResponse)
async def get_authenticated_user(user=Depends(current_active_user)):
    """
    Return the currently authenticated user for session bootstrap.
    """
    return AuthenticatedUserResponse(username=user.username)


@router.post("/scan", status_code=202)
async def start_scan(
    request: Request,
    body: ScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    """
    Queue a new scan after auth, validation, rate limiting, and cooldown checks.
    """
    _ = user
    scan_name = body.scan_name
    domain = body.domain
    limiter.enforce_scan_limits(request, domain)

    scan_id = str(uuid.uuid4())
    meta = ScanMeta(
        id=scan_id,
        scan_name=scan_name,
        domain=domain,
        started_at=datetime.utcnow(),
        status="running",
    )

    await save_scan(ScanResult(meta=meta), db)
    background_tasks.add_task(_run_scan_task, scan_id, scan_name, domain)

    return {
        "scan_id": scan_id,
        "scan_name": scan_name,
        "domain": domain,
        "status": "running",
        "message": f"Scan started. Poll GET /api/scan/{scan_id} for results.",
    }


async def _run_scan_task(scan_id: str, scan_name: str, domain: str) -> None:
    """
    Run the scan in the background using a fresh database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            await run_scan(domain, scan_name=scan_name, scan_id=scan_id, db=session)
        except Exception as exc:
            existing = await load_scan(scan_id, session)
            if existing:
                existing.meta.status = "failed"
                existing.meta.completed_at = datetime.utcnow()
                await save_scan(existing, session)
            print(f"[routes] Scan {scan_id} failed: {exc}")


@router.get("/scan/{scan_id}")
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    """
    Return one complete scan result for the authenticated user.
    """
    _ = user
    result = await load_scan(scan_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found.")
    return result


@router.get("/scans")
async def get_all_scans(
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    """
    Return the history list used by the sidebar.
    """
    _ = user
    return {"scans": await list_scans(db)}


@router.delete("/scan/{scan_id}", status_code=200)
async def remove_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    """
    Delete a stored scan for the authenticated user.
    """
    _ = user
    deleted = await delete_scan(scan_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return {"message": f"Scan {scan_id} deleted."}


@router.get("/scan/{scan_id}/report/html")
async def download_html_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(current_active_user),
):
    """
    Generate and return the HTML report for a completed scan.
    """
    _ = user
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
    user=Depends(current_active_user),
):
    """
    Generate and return the PDF report for a completed scan.
    """
    _ = user
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
