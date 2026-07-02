"""POST /api/v1/forget — remove a source from memory.

Spec reference: BACKEND_API_SPEC.md §5.4.

Uses POST (not DELETE) to match Cognee's forget() lifecycle naming and to
avoid HTTP client inconsistencies with DELETE + body — see spec §7 Q3.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from Backend.schemas.requests import ForgetRequest
from Backend.schemas.responses import ForgetResponse
from Backend.services import forget_service

router = APIRouter(tags=["Memory"])


@router.post(
    "/forget",
    response_model=ForgetResponse,
    summary="Forget a source",
    description=(
        "Removes a previously-ingested source from project memory "
        "(Cognee forget() lifecycle). source_id must be the 32-character hex "
        "string returned by POST /remember or GET /sources. "
        "Returns 404 when the source is already absent."
    ),
    responses={
        200: {"description": "Source deleted"},
        404: {"description": "Source not found"},
        422: {"description": "Invalid source_id format"},
        502: {"description": "Provider error"},
        503: {"description": "Server misconfigured"},
    },
)
async def forget(body: ForgetRequest) -> JSONResponse:
    data = await forget_service.run_forget(body.source_id)
    return JSONResponse(status_code=200, content=data)
