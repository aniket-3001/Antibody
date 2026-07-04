"""Antibody API entrypoint — a collective immune system against scams.

Boots the ops store, loads the seed graph if empty, rebuilds the semantic index,
and mounts the report + feed routers. Cognee is loaded lazily on first use so
the API comes up instantly even before models/keys are configured.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings

logging.basicConfig(level=logging.INFO)
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

from api.feed.router import router as feed_router  # noqa: E402
from api.intake.router import router as report_router  # noqa: E402

app.include_router(report_router)
app.include_router(feed_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env, "llm": settings.has_llm}


# Serve the built frontend (so `uvicorn api.main:app` is the whole demo). In dev,
# run Vite separately (npm run dev) — it proxies the API paths back here.
from pathlib import Path  # noqa: E402

_dist = Path(__file__).resolve().parent.parent / "Frontend" / "dist"
if _dist.exists():
    from fastapi.staticfiles import StaticFiles  # noqa: E402

    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
