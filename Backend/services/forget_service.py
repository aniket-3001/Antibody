"""Forget service — wraps memory_core.forget().

Spec reference: BACKEND_API_SPEC.md §5.4, §8.2.
Called by POST /api/v1/forget.
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


async def run_forget(source_id: str) -> dict:
    """Run the forget pipeline and return a serialisable dict.

    Returns a 404 MemoryAPIError when the source is already absent
    (spec §5.4: ForgetResult.already_absent → 404).
    """
    try:
        result = await memory_core.forget(
            source_id,
            project_id=PROJECT_ID,
            hard=True,
        )
    except ProviderError as exc:
        raise MemoryAPIError(502, ErrorCode.PROVIDER_ERROR, "Memory provider failed.", str(exc)) from exc
    except ConfigurationError as exc:
        raise MemoryAPIError(503, ErrorCode.CONFIGURATION_ERROR, "Server is misconfigured.", str(exc)) from exc
    except MemoryAPIError:
        raise
    except Exception as exc:
        raise MemoryAPIError(500, ErrorCode.INTERNAL_ERROR, "Unexpected error.", str(exc)) from exc

    if result.already_absent:
        raise MemoryAPIError(
            404,
            ErrorCode.SOURCE_NOT_FOUND,
            f"Source '{source_id}' was not found in project memory.",
        )

    return {
        "source_id": source_id,
        "deleted": result.deleted,
        "orphans_pruned": result.orphans_pruned,
    }
