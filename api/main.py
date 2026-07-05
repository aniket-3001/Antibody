"""Antibody API entrypoint — a collective immune system against scams.

Boots the ops store, loads the seed graph if empty, rebuilds the semantic index,
and mounts the report + feed routers. Cognee is loaded lazily on first use so the
API comes up instantly even before models/keys are configured.

Cross-cutting concerns are wired here once: structured logging with a per-request
correlation id, and a single set of error handlers that render every failure as a
stable JSON envelope (see ``api/core/``).
"""
from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import settings
from api.core.error_handlers import register_error_handlers
from api.core.logging import (
    REQUEST_ID_HEADER,
    configure_logging,
    new_request_id,
    set_request_id,
)

configure_logging()
log = logging.getLogger("antibody")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.intake.ingest import rebuild_semantic_index
    from api.memory import store
    from seed.load_seed import load_seed_if_empty

    store.init_db(settings.data_dir)
    n = load_seed_if_empty()
    if n:
        log.info("seeded %d reports across the shared graph", n)
    rebuild_semantic_index()
    log.info("Antibody ready — LLM configured: %s", settings.has_llm)
    yield


app = FastAPI(title="Antibody", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Stamp every request with a correlation id that rides the whole call stack.

    Honours a caller-supplied ``X-Request-ID`` (so a load balancer / frontend can
    thread its own trace id through) and otherwise mints one. The id is echoed
    back on the response header and appears on every log line for the request.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
    set_request_id(request_id)
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


register_error_handlers(app)

from api.feed.router import router as feed_router  # noqa: E402
from api.intake.router import router as report_router  # noqa: E402

app.include_router(report_router)
app.include_router(feed_router)


# ---- Help chatbot proxy ------------------------------------------------------
# The Help chatbot deliberately runs as a separate process — Cognee's config is
# a process-wide singleton, so the docs graph and the scam graph must not share
# a process (see help_api/config.py). In the single-container deployment,
# docker-entrypoint.sh starts help_api on 127.0.0.1:8010 and this route fronts
# it, so the frontend can call /help/* on the same origin it was served from.
_HELP_UPSTREAM = os.environ.get("HELP_API_URL", "http://127.0.0.1:8010")


@app.api_route("/help/{path:path}", methods=["GET", "POST"], tags=["help"])
async def help_proxy(path: str, request: Request) -> Response:
    import httpx

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
            upstream = await client.request(
                request.method,
                f"{_HELP_UPSTREAM}/help/{path}",
                content=await request.body(),
                headers={
                    "content-type": request.headers.get("content-type", "application/json")
                },
            )
    except httpx.HTTPError:
        return JSONResponse(
            status_code=503,
            content={
                "error": "help_unavailable",
                "message": (
                    "The Help service isn't running. Locally, start it with "
                    "`uvicorn help_api.main:app --port 8010`."
                ),
            },
        )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )


@app.get("/health", tags=["ops"])
async def health() -> dict:
    """Liveness probe + whether an LLM is configured (used by Cloud Run / Render)."""
    return {
        "status": "ok",
        "env": settings.app_env,
        "llm": settings.has_llm,
        "version": app.version,
    }


# Serve the built frontend (so `uvicorn api.main:app` is the whole demo). In dev,
# run Vite separately (npm run dev) — it proxies the API paths back here.
_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _dist.exists():
    from fastapi.staticfiles import StaticFiles  # noqa: E402

    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
