"""GET /api/v1/sources — list ingested sources.

Spec reference: BACKEND_API_SPEC.md §5.5.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from Backend.schemas.responses import SourcesResponse
from Backend.services import sources_service

router = APIRouter(tags=["Memory"])


@router.get(
    "/sources",
    response_model=SourcesResponse,
    summary="List ingested sources",
    description=(
        "Returns all source documents currently in project memory. "
        "source_type is always 'text' (known limitation: Cognee 1.2.2 does "
        "not store the original source_type). title may be an internal Cognee "
        "name when no title was provided at ingest time."
    ),
)
async def sources() -> JSONResponse:
    data = await sources_service.list_sources()
    return JSONResponse(status_code=200, content=data)
