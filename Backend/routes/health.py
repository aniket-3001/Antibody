"""GET /api/v1/health — liveness and readiness probe.

Spec reference: BACKEND_API_SPEC.md §5.8.

Implementation: calls memory_core.config.get_provider() (synchronous — env-var
validation only, no live Cognee API call) and maps ConfigurationError → 503.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from memory_core.config import get_provider
from memory_core.errors import ConfigurationError

from Backend.config import VERSION

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description=(
        "Returns server liveness and whether memory_core is correctly configured. "
        "Does NOT make a live Cognee/LLM API call — env-var validation only. "
        "200 = healthy, 503 = misconfigured."
    ),
    responses={
        200: {"description": "Server is healthy"},
        503: {"description": "Server is misconfigured (ConfigurationError)"},
    },
)
async def health() -> JSONResponse:
    mode = os.environ.get("MEMORY_CORE_MODE", "local")
    try:
        provider = get_provider()
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "memory_core_mode": mode,
                "provider": type(provider).__name__,
                "version": VERSION,
            },
        )
    except ConfigurationError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "memory_core_mode": mode,
                "error": {
                    "code": "CONFIGURATION_ERROR",
                    "message": str(exc),
                },
            },
        )
