from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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