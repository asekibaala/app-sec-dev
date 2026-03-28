from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

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

# Register all API routes
app.include_router(router)