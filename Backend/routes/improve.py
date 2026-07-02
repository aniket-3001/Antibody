"""POST /api/v1/improve — expand memory with a new source.

Spec reference: BACKEND_API_SPEC.md §5.2.

Semantically distinct from /remember (maps to Cognee's improve() lifecycle
operation) but the request/response contract is identical.  See spec §7 Q1 for
the design decision to keep these as two endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from Backend.config import (
    FILE_SIZE_LIMIT_BYTES,
    FILE_SIZE_LIMIT_MB,
    MAX_CONTENT_LENGTH,
    MAX_TITLE_LENGTH,
    VALID_CONTENT_TYPES,
)
from Backend.errors import ErrorCode, MemoryAPIError
from Backend.schemas.responses import IngestResponse
from Backend.services import improve_service

router = APIRouter(tags=["Memory"])


@router.post(
    "/improve",
    summary="Expand memory",
    description=(
        "Adds a new source to expand existing knowledge (Cognee improve() lifecycle). "
        "Request/response contract is identical to POST /remember. "
        "Use this endpoint when adding evidence AFTER initial ingestion — "
        "the demo narrative distinguishes 'Add to Memory' from 'Expand Memory'."
    ),
    responses={
        201: {"description": "Source ingested — graph grew"},
        200: {"description": "Duplicate or degraded ingest"},
        413: {"description": "File too large (> 20 MB)"},
        422: {"description": "Validation error"},
        502: {"description": "Provider or extraction error"},
        503: {"description": "Server misconfigured"},
    },
)
async def improve(
    content_type: str = Form(..., description="One of: pdf, text, markdown, url"),
    file: Optional[UploadFile] = File(None, description="Binary file — required when content_type=pdf"),
    content: Optional[str] = Form(None, description="Text content — required when content_type != pdf"),
    title: Optional[str] = Form(None, description="Human-readable label (max 255 chars)"),
    active_hypotheses: Optional[str] = Form(
        None, description="JSON-encoded string[] of active hypotheses (max 5)"
    ),
) -> JSONResponse:
    if content_type not in VALID_CONTENT_TYPES:
        raise MemoryAPIError(
            422,
            ErrorCode.VALIDATION_ERROR,
            f"content_type must be one of: {sorted(VALID_CONTENT_TYPES)!r}.",
        )

    if content_type == "pdf":
        if file is None:
            raise MemoryAPIError(422, ErrorCode.VALIDATION_ERROR, "file is required when content_type is 'pdf'.")
        raw_bytes = await file.read()
        if len(raw_bytes) > FILE_SIZE_LIMIT_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds {FILE_SIZE_LIMIT_MB} MB limit.", "detail": None}},
            )
        src_content: str | bytes = raw_bytes
    else:
        if content is None:
            raise MemoryAPIError(
                422,
                ErrorCode.VALIDATION_ERROR,
                "content is required when content_type is not 'pdf'.",
            )
        if len(content) > MAX_CONTENT_LENGTH:
            raise MemoryAPIError(
                422,
                ErrorCode.VALIDATION_ERROR,
                f"content exceeds {MAX_CONTENT_LENGTH:,} character limit.",
            )
        if content_type == "url" and not (content.startswith("http://") or content.startswith("https://")):
            raise MemoryAPIError(
                422,
                ErrorCode.VALIDATION_ERROR,
                "URL content must begin with http:// or https://.",
            )
        src_content = content

    if title is not None and len(title) > MAX_TITLE_LENGTH:
        raise MemoryAPIError(
            422,
            ErrorCode.VALIDATION_ERROR,
            f"title exceeds {MAX_TITLE_LENGTH} character limit.",
        )

    result = await improve_service.run_improve(src_content, content_type, title, active_hypotheses)

    status_code = 201 if result.status == "created" else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "source_id": result.source_id,
            "status": result.status,
            "nodes_created": result.nodes_created,
            "edges_created": result.edges_created,
            "duration_ms": result.duration_ms,
            "warnings": result.warnings,
        },
    )
