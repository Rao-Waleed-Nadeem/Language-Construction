"""Vela Studio FastAPI Application.

Serves compiler API endpoints, educational grammar lab, and static frontend in demo mode.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import compiler, docs, grammar

app = FastAPI(
    title="Vela Studio API",
    version="0.1.0",
    description="Compiler Construction workbench and educational tool API",
)

# CORS configuration per doc 02 §10
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request size limiter (HTTP 413 if payload > 100,000 characters) per doc 02 §10
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 100_000:
        return Response(
            content="Payload Too Large: source size exceeds 100,000 characters", status_code=413
        )
    return await call_next(request)


# Health check
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# Include API Routers
app.include_router(compiler.router)
app.include_router(grammar.router)
app.include_router(docs.router)

# Mount frontend/dist if built (SPA fallback)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
