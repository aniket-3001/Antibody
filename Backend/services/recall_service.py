"""Recall service — wraps memory_core.recall().

Spec reference: BACKEND_API_SPEC.md §5.3, §8.2.
Called by POST /api/v1/recall.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import memory_core
from memory_core.errors import (
    CapabilityUnavailableError,
    ConfigurationError,
    RecallError,
)

from Backend.config import PROJECT_ID
from Backend.errors import ErrorCode, MemoryAPIError
from Backend.schemas.cytoscape import to_cytoscape


async def run_recall(query: str, strategy: str | None) -> dict:
    """Run the recall pipeline and return a serialisable dict.

    The evidence_graph is converted to Cytoscape.js format here.
    Returns None for evidence_graph when no evidence edges were found.
    """
    try:
        result = await memory_core.recall(
            query,
            project_id=PROJECT_ID,
            strategy=strategy,
        )
    except CapabilityUnavailableError as exc:
        raise MemoryAPIError(501, ErrorCode.CAPABILITY_UNAVAILABLE, "Capability not available.", str(exc)) from exc
    except RecallError as exc:
        raise MemoryAPIError(502, ErrorCode.RECALL_FAILED, "Recall pipeline failed.", str(exc)) from exc
    except ConfigurationError as exc:
        raise MemoryAPIError(503, ErrorCode.CONFIGURATION_ERROR, "Server is misconfigured.", str(exc)) from exc
    except MemoryAPIError:
        raise
    except Exception as exc:
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    # Serialise evidence graph to Cytoscape.js format (spec §6.4).
    evidence_graph = None
    if result.evidence_graph is not None and (
        result.evidence_graph.nodes or result.evidence_graph.edges
    ):
        evidence_ids = {n.id for n in result.evidence_graph.nodes}
        evidence_graph = to_cytoscape(result.evidence_graph, evidence_node_ids=evidence_ids)

    return {
        "query": query,
        "answer": result.answer,
        "strategy_used": result.strategy_used,
        "evidence_graph": evidence_graph,
        "degraded": result.degraded,
        "duration_ms": result.duration_ms,
    }
