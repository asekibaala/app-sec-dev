import json
import os
from pathlib import Path
from app.models.result import ScanResult

# All scan results live under backend/scans/
# Each scan gets its own folder named after its UUID
SCANS_DIR = Path(__file__).parent.parent.parent / "scans"


def _ensure_dir(scan_id: str) -> Path:
    """
    Creates the scan directory if it doesn't exist yet.
    Returns the path so callers can use it immediately.
    Path.mkdir(parents=True, exist_ok=True) is safe to call
    even if the directory already exists — no error is raised.
    """
    path = SCANS_DIR / scan_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_scan(result: ScanResult) -> None:
    """
    Serialises the entire ScanResult to a single JSON file.
    model_dump() converts the Pydantic model to a plain dict.
    mode='json' ensures datetime objects become ISO strings
    rather than Python datetime objects which aren't JSON serialisable.
    """
    path = _ensure_dir(result.meta.id)
    output = path / "result.json"
    with open(output, "w") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2)


def load_scan(scan_id: str) -> ScanResult | None:
    """
    Loads a scan result from disk by its ID.
    Returns None if the scan doesn't exist — callers
    should handle None as a 404 response.
    """
    path = SCANS_DIR / scan_id / "result.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return ScanResult(**data)


def list_scans() -> list[dict]:
    """
    Returns a lightweight summary list of all scans on disk.
    We only read the meta fields — not the full module results —
    so the response stays fast even with hundreds of scans stored.
    """
    if not SCANS_DIR.exists():
        return []

    summaries = []
    for scan_dir in sorted(SCANS_DIR.iterdir(), reverse=True):
        result_file = scan_dir / "result.json"
        if not result_file.exists():
            continue
        with open(result_file) as f:
            data = json.load(f)
        # Return only the meta block — lightweight for list views
        summaries.append(data.get("meta", {}))

    return summaries