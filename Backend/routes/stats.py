"""GET /api/v1/stats — memory summary counts.

Spec reference: BACKEND_API_SPEC.md §5.7.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from Backend.schemas.responses import StatsResponse
from Backend.services import stats_service

router = APIRouter(tags=["Memory"])


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Memory statistics",
    description=(
        "Returns total sources, active hypothesis count, entity type breakdown, "
        "and last ingest timestamp.  entity_counts is null when the active "
        "provider cannot produce a deterministic graph (Mode B)."
    ),
)
async def stats() -> JSONResponse:
    data = await stats_service.get_stats()
    return JSONResponse(status_code=200, content=data)
