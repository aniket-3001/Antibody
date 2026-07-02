"""GET /api/v1/graph — full knowledge graph in Cytoscape.js format.

Spec reference: BACKEND_API_SPEC.md §5.6, §6.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from Backend.schemas.responses import CytoscapeGraph
from Backend.services import graph_service

router = APIRouter(tags=["Graph"])


@router.get(
    "/graph",
    response_model=CytoscapeGraph,
    summary="Full knowledge graph",
    description=(
        "Returns the complete knowledge graph as a Cytoscape.js elements array. "
        "Includes ontology-typed nodes/edges AND Cognee scaffolding nodes "
        "(BELONGS_TO_SET, IS_A, etc.) — the frontend should de-emphasise "
        "type=unknown elements. Returns an empty elements array when no sources "
        "have been ingested."
    ),
    responses={
        200: {"description": "Graph returned (may be empty)"},
        501: {"description": "Graph access unavailable (CapabilityUnavailableError)"},
        502: {"description": "Provider error"},
        503: {"description": "Server misconfigured"},
    },
)
async def graph() -> JSONResponse:
    data = await graph_service.get_graph()
    return JSONResponse(status_code=200, content=data)
