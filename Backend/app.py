"""MemoryOS FastAPI application.

Spec reference: BACKEND_API_SPEC.md §1, §2, §8.

Run from the repo root:
    uvicorn Backend.app:app --reload --port 8000

Or:
    python -m uvicorn Backend.app:app --reload --port 8000

The repo root must be on sys.path so both `memory_core` and `Backend` are
importable.  This file ensures that by inserting the parent directory of
Backend/ onto sys.path before any local imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── Repo root on sys.path ────────────────────────────────────────────────────
# Ensures memory_core is importable regardless of the CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from Backend.config import VERSION
from Backend.errors import MemoryAPIError
from Backend.routes import forget, graph, health, improve, recall, remember, sources, stats

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="MemoryOS API",
    description=(
        "Persistent memory operating system for researchers, powered by Cognee. "
        "Exposes the four Cognee lifecycle operations — remember, recall, improve, "
        "forget — as a thin HTTP translation layer over memory_core."
    ),
    version=VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS (spec §1.5) ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handlers (spec §2, §8.3) ─────────────────────────────────

@app.exception_handler(MemoryAPIError)
async def memory_api_error_handler(request: Request, exc: MemoryAPIError) -> JSONResponse:
    """Serialise MemoryAPIError into the standard error envelope (spec §2)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Wrap FastAPI's built-in validation errors in the standard envelope."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "detail": str(exc),
            }
        },
    )


# ── Routers (spec §1.2: all prefixed /api/v1) ─────────────────────────────────
app.include_router(health.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(recall.router, prefix="/api/v1")
app.include_router(remember.router, prefix="/api/v1")
app.include_router(improve.router, prefix="/api/v1")
app.include_router(forget.router, prefix="/api/v1")
