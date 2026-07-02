"""Ingest service — wraps memory_core.ingest().

Spec reference: BACKEND_API_SPEC.md §5.1, §8.2.
Called by POST /api/v1/remember.
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
    CapabilityUnavailableError,
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


def _parse_active_hypotheses(raw: str | None) -> list[str] | None:
    """Validate and parse the JSON-encoded active_hypotheses form field."""
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MemoryAPIError(
            422,
            ErrorCode.VALIDATION_ERROR,
            "active_hypotheses must be valid JSON encoding a string array.",
            str(exc),
        ) from exc
    if not isinstance(parsed, list) or not all(isinstance(h, str) for h in parsed):
        raise MemoryAPIError(
            422,
            ErrorCode.VALIDATION_ERROR,
            "active_hypotheses must be a JSON array of strings.",
        )
    if len(parsed) > MAX_ACTIVE_HYPOTHESES:
        raise MemoryAPIError(
            422,
            ErrorCode.VALIDATION_ERROR,
            f"active_hypotheses must contain at most {MAX_ACTIVE_HYPOTHESES} items.",
        )
    for h in parsed:
        if len(h) > MAX_HYPOTHESIS_LENGTH:
            raise MemoryAPIError(
                422,
                ErrorCode.VALIDATION_ERROR,
                f"Each hypothesis must not exceed {MAX_HYPOTHESIS_LENGTH} characters.",
            )
    return parsed


async def run_ingest(
    content: str | bytes,
    content_type: str,
    title: str | None,
    active_hypotheses_json: str | None,
) -> object:
    """Run the ingest pipeline and return an IngestResult.

    All memory_core exceptions are mapped to MemoryAPIError here (spec §8.2).
    """
    active_hypotheses = _parse_active_hypotheses(active_hypotheses_json)

    source = SourceInput(
        content=content,
        source_type=content_type,
        title=title,
        metadata={},
    )

    try:
        result = await memory_core.ingest(
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
        import traceback, sys
        print("=== INGEST 500 ===", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    return result
