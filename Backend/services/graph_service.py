"""Graph service — wraps memory_core.get_graph().

Spec reference: BACKEND_API_SPEC.md §5.6, §8.2.
Called by GET /api/v1/graph.
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
    ProviderError,
)

from Backend.config import PROJECT_ID
from Backend.errors import ErrorCode, MemoryAPIError
from Backend.schemas.cytoscape import to_cytoscape


async def get_graph() -> dict:
    """Return the full knowledge graph as a Cytoscape.js dict."""
    try:
        graph = await memory_core.get_graph(project_id=PROJECT_ID)
    except CapabilityUnavailableError as exc:
        raise MemoryAPIError(501, ErrorCode.CAPABILITY_UNAVAILABLE, "Graph access not available.", str(exc)) from exc
    except ProviderError as exc:
        raise MemoryAPIError(502, ErrorCode.PROVIDER_ERROR, "Memory provider failed.", str(exc)) from exc
    except ConfigurationError as exc:
        raise MemoryAPIError(503, ErrorCode.CONFIGURATION_ERROR, "Server is misconfigured.", str(exc)) from exc
    except Exception as exc:
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    return to_cytoscape(graph)
