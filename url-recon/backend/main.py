from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.database.engine import engine
from app.database.models import Base
from app.database.user_store import ensure_default_admin
from app.database.engine import AsyncSessionLocal

app = FastAPI(
    title="URL Recon API",
    description="Domain security intelligence platform",
    version="1.0.0",
)

# Allow the React frontend on port 5173 to call this API.
# In production this would be locked to your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    """
    Runs once when the FastAPI server boots up — before any request is handled.

    engine.begin() opens a special connection for DDL (Data Definition Language)
    commands — the SQL that creates/alters tables rather than reads/writes data.

    conn.run_sync(Base.metadata.create_all) — looks at every class that inherits
    from Base (our ScanRecord), and creates its table in Postgres IF it doesn't
    already exist. It never drops or alters an existing table, so this is safe
    to run every single time the server starts. Old data is never touched.

    Think of it like: "build the shelves if they aren't there yet, otherwise
    just walk in and get to work."
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[db] PostgreSQL tables verified / created ✓")

    # Seed the default admin account after the tables exist. This keeps the
    # first-run experience simple while still storing the password as a hash.
    async with AsyncSessionLocal() as session:
        await ensure_default_admin(session)
    print("[auth] Default admin account verified / created ✓")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[error] Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal error occurred.",
            "path": str(request.url),
        },
    )


# Register all API routes
app.include_router(router)
