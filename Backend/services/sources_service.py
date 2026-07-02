"""Sources service — wraps memory_core.list_sources().

Spec reference: BACKEND_API_SPEC.md §5.5, §8.2.
Called by GET /api/v1/sources.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import memory_core
from memory_core.errors import ConfigurationError, ProviderError

from Backend.config import PROJECT_ID
from Backend.errors import ErrorCode, MemoryAPIError
from Backend.services._helpers import fmt_dt


async def list_sources() -> dict:
    """Return the sources list as a serialisable dict."""
    try:
        records = await memory_core.list_sources(project_id=PROJECT_ID)
    except ProviderError as exc:
        raise MemoryAPIError(502, ErrorCode.PROVIDER_ERROR, "Memory provider failed.", str(exc)) from exc
    except ConfigurationError as exc:
        raise MemoryAPIError(503, ErrorCode.CONFIGURATION_ERROR, "Server is misconfigured.", str(exc)) from exc
    except Exception as exc:
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    sources = [
        {
            # spec §5.5: source_id = SourceRecord.node_set (content-hash id)
            "source_id": r.node_set,
            "title": r.title or str(r.id),
            "source_type": r.source_type,
            "ingested_at": fmt_dt(r.ingested_at) or "",
        }
        for r in records
    ]

    return {"sources": sources, "total": len(sources)}
