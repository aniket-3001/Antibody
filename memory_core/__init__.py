"""memory_core — the isolated Cognee integration for MemoryOS.

Design reference: Docs/MEMORY_CORE_DESIGN.md (the full spec this package
implements against). This is the only module in MemoryOS that imports
`cognee` (via providers/) — every other layer (backend, frontend) talks to
the seven public functions below, never to Cognee directly (design §1.1).

Status: Milestone 2.1 — module skeleton. Types, interfaces, and pure
helpers (ontology vocabulary/prompts, id hashing, graph normalization,
evidence-subgraph filtering) are implemented; provider-calling
orchestration (the actual cognee.add()/cognify()/search()/delete_data()
wiring) is stubbed with NotImplementedError, to be filled in Milestone 2.2.
"""

from __future__ import annotations

from memory_core.config import get_provider
from memory_core.errors import (
    CapabilityUnavailableError,
    ConfigurationError,
    ExtractionError,
    MemoryCoreError,
    OntologyError,
    ProviderError,
    RecallError,
)
from memory_core.graph.query import forget_source, get_graph as _get_graph, get_stats as _get_stats, list_sources as _list_sources
from memory_core.ingestion.pipeline import run_ingest
from memory_core.models import (
    ForgetResult,
    IngestResult,
    MemoryGraph,
    MemoryStats,
    RecallResult,
    SourceInput,
    SourceRecord,
)
from memory_core.providers.base import RecallStrategy
from memory_core.retrieval.router import classify_intent

__all__ = [
    "ingest",
    "improve",
    "recall",
    "forget",
    "get_graph",
    "get_stats",
    "list_sources",
    "MemoryCoreError",
    "ConfigurationError",
    "OntologyError",
    "ProviderError",
    "ExtractionError",
    "RecallError",
    "CapabilityUnavailableError",
]


async def ingest(
    source: SourceInput,
    *,
    project_id: str,
    active_hypotheses: list[str] | None = None,
) -> IngestResult:
    """Design §2.1."""
    provider = get_provider()
    return await run_ingest(
        source, project_id=project_id, active_hypotheses=active_hypotheses, provider=provider
    )


async def improve(
    source: SourceInput,
    *,
    project_id: str,
    active_hypotheses: list[str] | None = None,
) -> IngestResult:
    """Design §2.2. Delegates entirely to the same orchestration as ingest()."""
    provider = get_provider()
    return await run_ingest(
        source, project_id=project_id, active_hypotheses=active_hypotheses, provider=provider
    )


async def recall(
    query: str,
    *,
    project_id: str,
    strategy: RecallStrategy | None = None,
) -> RecallResult:
    """Design §2.3."""
    provider = get_provider()
    resolved_strategy = strategy or classify_intent(query)
    raise NotImplementedError(
        "Milestone 2.2: wire provider.query() + retrieval.evidence.build_evidence()"
    )


async def forget(
    source_id: str,
    *,
    project_id: str,
    hard: bool = True,
) -> ForgetResult:
    """Design §2.4."""
    provider = get_provider()
    return await forget_source(source_id, project_id=project_id, hard=hard, provider=provider)


async def get_graph(*, project_id: str) -> MemoryGraph:
    """Design §2.5."""
    provider = get_provider()
    return await _get_graph(project_id=project_id, provider=provider)


async def get_stats(*, project_id: str) -> MemoryStats:
    """Design §2.5."""
    provider = get_provider()
    return await _get_stats(project_id=project_id, provider=provider)


async def list_sources(*, project_id: str) -> list[SourceRecord]:
    """Design §2.5."""
    provider = get_provider()
    return await _list_sources(project_id=project_id, provider=provider)
