"""One place that turns exceptions into a stable JSON error envelope.

Every error — a typed :class:`AntibodyError`, a validation failure, or an
unexpected 500 — leaves the API in the same shape::

    {"error": "<machine_code>", "message": "<human text>",
     "request_id": "<correlation id>", "path": "/report"}

so a client only ever writes one parser. The ``request_id`` echoes the one in
the logs, so a user-reported failure is one grep away from its stack trace.

Why the unhandled-exception handler mirrors CORS headers itself: Starlette runs
the catch-all ``Exception`` handler in ``ServerErrorMiddleware``, which sits
*outside* ``CORSMiddleware``. A bare 500 would therefore reach the browser with
no ``Access-Control-Allow-Origin`` header, and the browser would report a
misleading "CORS error" that hides the real server fault. We re-attach the
allowed origin so a 500 surfaces as clean, readable JSON in the console. (4xx
handlers run inside CORSMiddleware and already carry these headers.)
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import settings
from api.core.exceptions import AntibodyError
from api.core.logging import REQUEST_ID_HEADER, get_request_id

log = logging.getLogger("antibody.errors")


def _envelope(status_code: int, code: str, message: str, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": code,
            "message": message,
            "request_id": get_request_id(),
            "path": request.url.path,
        },
        headers={REQUEST_ID_HEADER: get_request_id()},
    )


def _cors_headers_for(request: Request) -> dict[str, str]:
    """CORS headers to re-attach to a 500 (see module docstring)."""
    origin = request.headers.get("origin")
    if not origin:
        return {}
    allowed = {settings.web_origin, "http://localhost:5173", "http://127.0.0.1:5173"}
    if origin in allowed:
        return {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}
    return {}


def register_error_handlers(app: FastAPI) -> None:
    """Wire every handler onto the app. Called once at startup from ``main``."""

    @app.exception_handler(AntibodyError)
    async def _handle_antibody_error(request: Request, exc: AntibodyError) -> JSONResponse:
        # Expected, client-facing errors: log at INFO, no stack trace.
        log.info("%s: %s", exc.code, exc.detail)
        return _envelope(exc.status_code, exc.code, exc.detail, request)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        message = first.get("msg", "Invalid request.")
        detail = f"{field}: {message}" if field else message
        return _envelope(422, "validation_error", detail, request)

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # Covers 404-on-unknown-route and any bare HTTPException still in flight.
        return _envelope(exc.status_code, "http_error", str(exc.detail), request)

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        message = str(exc) if settings.app_env == "dev" else "Internal server error."
        response = _envelope(500, "internal_error", message, request)
        for key, value in _cors_headers_for(request).items():
            response.headers[key] = value
        return response
