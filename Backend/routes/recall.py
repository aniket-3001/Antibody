"""POST /api/v1/recall — answer a question about project memory.

Spec reference: BACKEND_API_SPEC.md §5.3.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from Backend.schemas.requests import RecallRequest
from Backend.schemas.responses import RecallResponse
from Backend.services import recall_service

router = APIRouter(tags=["Memory"])


@router.post(
    "/recall",
    response_model=RecallResponse,
    summary="Recall from memory",
    description=(
        "Answers a natural-language question using graph-backed memory. "
        "Returns a prose answer + an evidence_graph in Cytoscape.js format "
        "for UI highlighting. evidence_graph is null when no typed evidence "
        "edges match the query strategy — the prose answer is still returned. "
        "strategy is auto-detected from query keywords when null."
    ),
    responses={
        200: {"description": "Recall completed (evidence_graph may be null)"},
        422: {"description": "Validation error"},
        501: {"description": "Capability unavailable"},
        502: {"description": "Recall pipeline failed"},
        503: {"description": "Server misconfigured"},
    },
)
async def recall(body: RecallRequest) -> JSONResponse:
    data = await recall_service.run_recall(body.query, body.strategy)
    return JSONResponse(status_code=200, content=data)
