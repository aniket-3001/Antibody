"""Structured logging with a per-request correlation id.

Every request is stamped with a short id (either the caller's ``X-Request-ID``
header or a fresh one) that rides a ``ContextVar`` through the whole async call
stack. Because it lives on a ``ContextVar`` — not a thread-local — it survives
the ``await`` hops between the router, the memory layer, and Cognee, so a single
scam report's journey is greppable end-to-end in the logs.

Dependency-free on purpose: no ``asgi-correlation-id`` or ``loguru``. A ~40-line
ContextVar + ``logging.Filter`` does exactly what we need and keeps the runtime
image lean (which matters on the free Cloud Run / Render tiers Antibody targets).
"""
from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

# The id for the request currently being served. "-" outside a request (startup,
# background tasks that outlive their request, tests).
_request_id: ContextVar[str] = ContextVar("request_id", default="-")

REQUEST_ID_HEADER = "X-Request-ID"


def new_request_id() -> str:
    """A short, log-friendly correlation id (first 8 hex of a uuid4)."""
    return uuid.uuid4().hex[:8]


def set_request_id(value: str) -> None:
    _request_id.set(value or "-")


def get_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    """Inject the active request id onto every record so the formatter can show it.

    A filter (not a formatter) so the id is attached regardless of which handler
    or formatter is configured downstream — including uvicorn's own loggers.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Install a single console handler that prints the correlation id.

    Idempotent: re-running (e.g. across test app boots) replaces handlers rather
    than stacking duplicates. Third-party loggers that flood at INFO are pinned
    to WARNING so our own ``antibody.*`` logs stay readable.
    """
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(request_id)s] %(levelname)-7s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    # Antibody's own namespace: keep at the configured level.
    logging.getLogger("antibody").setLevel(level)

    # Chatty third parties that would otherwise bury our logs.
    for noisy in ("httpx", "httpcore", "cognee", "LiteLLM", "sqlalchemy", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
