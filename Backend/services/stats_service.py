"""Stats service — wraps memory_core.get_stats().

Spec reference: BACKEND_API_SPEC.md §5.7, §8.2.
Called by GET /api/v1/stats.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import memory_core
from memory_core.errors import ConfigurationError, ProviderError
from memory_core.models import EntityType

from Backend.config import PROJECT_ID
from Backend.errors import ErrorCode, MemoryAPIError
from Backend.services._helpers import fmt_dt


async def get_stats() -> dict:
    """Return memory stats as a serialisable dict.

    entity_counts keys are EntityType string values, not enum objects
    (spec §5.7).  When entity_counts is None (Mode B without graph access),
    it is returned as null — not an error.
    """
    try:
        result = await memory_core.get_stats(project_id=PROJECT_ID)
    except ProviderError as exc:
        raise MemoryAPIError(502, ErrorCode.PROVIDER_ERROR, "Memory provider failed.", str(exc)) from exc
    except ConfigurationError as exc:
        raise MemoryAPIError(503, ErrorCode.CONFIGURATION_ERROR, "Server is misconfigured.", str(exc)) from exc
    except MemoryAPIError:
        raise
    except Exception as exc:
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    entity_counts: dict[str, int] | None = None
    if result.entity_counts is not None:
        entity_counts = {
            (k.value if isinstance(k, EntityType) else str(k)): v
            for k, v in result.entity_counts.items()
        }

    return {
        "total_sources": result.source_counts.get("total", 0),
        "active_hypotheses": result.active_hypotheses,
        "entity_counts": entity_counts,
        "last_ingest_at": fmt_dt(result.last_ingest_at),
    }
