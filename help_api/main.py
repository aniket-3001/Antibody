"""Help chatbot API — separate process from api/ on purpose (see config.py).

Run locally:   uvicorn help_api.main:app --host 127.0.0.1 --port 8010
Ingest docs:   python -m help_api.ingest ./help_docs
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from help_api.config import help_settings
from help_api.memory_service import help_memory_service

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("antibody.help")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Help API ready — LLM configured: %s", help_settings.has_llm)
    yield


app = FastAPI(title="Antibody Help", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[help_settings.help_web_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Turn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AskIn(BaseModel):
    question: str
    history: list[Turn] = []


def _compose_query(question: str, history: list[Turn]) -> str:
    """Fold recent turns into one query string — GRAPH_COMPLETION takes a
    single query_text, no native multi-turn message list, so prior turns are
    given as context ahead of the actual question."""
    if not history:
        return question
    recent = history[-6:]  # last few turns is plenty of context for a follow-up
    convo = "\n".join(f"{t.role}: {t.content}" for t in recent)
    return f"Earlier in this conversation:\n{convo}\n\nNow the user asks: {question}"


@app.post("/help/ask")
async def ask(body: AskIn) -> dict:
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(400, "empty question")
    result = await help_memory_service.ask(_compose_query(question, body.history))
    if not result.get("available"):
        return {
            "answer": (
                "The Help knowledge base isn't reachable right now (no docs "
                "ingested yet, or the LLM isn't configured). Try `python -m "
                "help_api.ingest ./help_docs` first, or check help_api's .env."
            ),
            "citations": [],
            "available": False,
        }
    return result


@app.get("/help/health")
async def health() -> dict:
    return {"status": "ok", "llm": help_settings.has_llm}
