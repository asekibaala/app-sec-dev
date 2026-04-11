"""
db_store.py — PostgreSQL-backed replacement for storage/scan_store.py.

This is the ONLY file allowed to talk to the `scans` table.
All three functions do exactly what the old file-based versions did —
same names, same return types — but now data lives in Postgres instead
of JSON files on disk.

Function map (old → new):
  scan_store.save_scan(result)          →  db_store.save_scan(result, session)
  scan_store.load_scan(scan_id)         →  db_store.load_scan(scan_id, session)
  scan_store.list_scans()               →  db_store.list_scans(session)

Why do all functions take a `session` parameter?
  A session is a live workspace with the database. Passing it in (instead
  of creating a new one inside each function) means the caller controls
  the session's lifetime — which is important for transactions and testing.
  Routes use FastAPI's Depends(get_db). Background tasks create their own
  session using `async with AsyncSessionLocal() as session:`.
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ScanRecord
from app.models.result import ScanResult


async def save_scan(result: ScanResult, session: AsyncSession) -> None:
    """
    Insert a new scan row OR update an existing one.

    We call this twice per scan:
      1. At the START  → status="running", no results yet (row created)
      2. At the END    → status="complete", full result_json saved (row updated)

    session.get(Model, primary_key) — fastest possible lookup by ID.
    Like going straight to shelf number 42 in a library instead of
    searching every shelf. Returns the existing row or None.

    If the row already exists we UPDATE it in place (called an "upsert"
    pattern — update if exists, insert if not).

    model_dump_json() — Pydantic's built-in serialiser. Converts the
    entire ScanResult Python object into a JSON string in one shot.
    It handles datetime objects, nested models, Optionals — everything.

    session.add(record) — stages the new row, like writing on a
    sticky note before filing it.

    await session.commit() — permanently saves everything staged in this
    session to Postgres. Without commit, changes vanish when session closes.
    """
    existing: ScanRecord | None = await session.get(ScanRecord, result.meta.id)

    if existing:
        # Row already in DB — update the fields that change over a scan's life
        existing.status       = result.meta.status
        existing.completed_at = result.meta.completed_at
        existing.duration_ms  = result.meta.duration_ms
        existing.result_json  = result.model_dump_json()
        # No session.add() needed — SQLAlchemy tracks changes to existing rows
    else:
        # First time we've seen this scan_id — create a fresh row
        record = ScanRecord(
            id           = result.meta.id,
            domain       = result.meta.domain,
            status       = result.meta.status,
            started_at   = result.meta.started_at,
            completed_at = result.meta.completed_at,
            duration_ms  = result.meta.duration_ms,
            result_json  = result.model_dump_json(),
        )
        session.add(record)

    await session.commit()


async def load_scan(scan_id: str, session: AsyncSession) -> ScanResult | None:
    """
    Fetch one complete scan by its UUID. Returns None if not found.

    session.get(Model, pk) — Postgres index lookup by primary key.
    This is O(1) — constant time — no matter how many rows exist.

    ScanResult.model_validate_json() — Pydantic's deserialiser.
    Takes the raw JSON string from Postgres and rebuilds the full
    ScanResult Python object with all nested models intact.
    The reverse of model_dump_json().

    Callers should treat None as a 404 (scan doesn't exist yet or
    was never created).
    """
    record: ScanRecord | None = await session.get(ScanRecord, scan_id)

    if record is None:
        return None

    return ScanResult.model_validate_json(record.result_json)


async def list_scans(session: AsyncSession) -> list[dict]:
    """
    Return a lightweight summary list of all scans, newest first.

    We deliberately do NOT return full ScanResult objects here —
    the frontend's history sidebar only needs the meta fields.
    Sending the full result_json for every scan would be slow and wasteful.

    select(ScanRecord) — builds a SQL SELECT statement as Python.
    .order_by(desc(...)) — ORDER BY started_at DESC (newest first).
    await session.execute(stmt) — sends the query to Postgres.
    result.scalars().all() — unwraps the rows into a plain Python list.

    .isoformat() converts Python datetime objects to ISO 8601 strings
    e.g. "2024-01-15T10:30:00" — the format the frontend expects.
    We guard with `if r.started_at` because completed_at can be None
    for in-progress scans.
    """
    stmt = select(ScanRecord).order_by(desc(ScanRecord.started_at))
    result = await session.execute(stmt)
    rows: list[ScanRecord] = result.scalars().all()

    return [
        {
            "id":           r.id,
            "domain":       r.domain,
            "status":       r.status,
            "started_at":   r.started_at.isoformat()   if r.started_at   else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "duration_ms":  r.duration_ms,
        }
        for r in rows
    ]


async def delete_scan(scan_id: str, session: AsyncSession) -> bool:
    """
    Delete a scan row by ID. Returns True if deleted, False if not found.

    Useful for a future "clear history" or "delete scan" feature.
    session.delete(record) — marks the row for deletion.
    await session.commit() — executes the DELETE in Postgres.
    """
    record: ScanRecord | None = await session.get(ScanRecord, scan_id)

    if record is None:
        return False

    await session.delete(record)
    await session.commit()
    return True
