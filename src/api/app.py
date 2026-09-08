"""FastAPI main application setup."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Rapidfolio SOP Pre-Flight Linter & Deterministic Graph Compiler",
    description="Enterprise tool for auditing financial back-office SOPs and compiling deterministic DAG workflows.",
    version="1.0.0"
)

# CORS middleware for local frontend dev or embeds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints
app.include_router(api_router)

# Mount static files directory if present
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def serve_spa():
        """Serves the single page application HTML."""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Rapidfolio SOP Pre-Flight Linter API is running. View /docs for API documentation."}
