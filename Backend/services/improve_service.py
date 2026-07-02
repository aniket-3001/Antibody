"""Improve service — wraps memory_core.improve().

Spec reference: BACKEND_API_SPEC.md §5.2, §8.2.
Called by POST /api/v1/improve.

memory_core.improve() and memory_core.ingest() share the same run_ingest()
pipeline internally, but they are distinct public API names (spec §7 Q1).
This service mirrors ingest_service.py but calls memory_core.improve().
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import memory_core
from memory_core.errors import (
    ConfigurationError,
    ExtractionError,
    OntologyError,
    ProviderError,
)
from memory_core.models import SourceInput

from Backend.config import (
    MAX_ACTIVE_HYPOTHESES,
    MAX_HYPOTHESIS_LENGTH,
    PROJECT_ID,
)
from Backend.errors import ErrorCode, MemoryAPIError
from Backend.services.ingest_service import _parse_active_hypotheses


async def run_improve(
    content: str | bytes,
    content_type: str,
    title: str | None,
    active_hypotheses_json: str | None,
) -> object:
    """Run the improve pipeline and return an IngestResult."""
    active_hypotheses = _parse_active_hypotheses(active_hypotheses_json)

    source = SourceInput(
        content=content,
        source_type=content_type,
        title=title,
        metadata={},
    )

    try:
        result = await memory_core.improve(
            source,
            project_id=PROJECT_ID,
            active_hypotheses=active_hypotheses,
        )
    except ConfigurationError as exc:
        raise MemoryAPIError(503, ErrorCode.CONFIGURATION_ERROR, "Server is misconfigured.", str(exc)) from exc
    except OntologyError as exc:
        raise MemoryAPIError(500, ErrorCode.ONTOLOGY_ERROR, "Internal ontology error.", str(exc)) from exc
    except ProviderError as exc:
        raise MemoryAPIError(502, ErrorCode.PROVIDER_ERROR, "Memory provider failed.", str(exc)) from exc
    except ExtractionError as exc:
        raise MemoryAPIError(502, ErrorCode.EXTRACTION_FAILED, "Graph extraction pipeline failed.", str(exc)) from exc
    except MemoryAPIError:
        raise
    except Exception as exc:
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    return result
