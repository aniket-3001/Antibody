"""memory_core — the isolated Cognee integration for MemoryOS.

Design reference: Docs/MEMORY_CORE_DESIGN.md (the full spec this package
implements against). This is the only module in MemoryOS that imports
`cognee` (via providers/) — every other layer (backend, frontend) talks to
the seven public functions below, never to Cognee directly (design §1.1).

Status: Milestone 2.1 — module skeleton, extended by a pre-2.2 architecture
review. Types, interfaces, and pure helpers (ontology vocabulary/prompts,
id hashing, graph normalization, evidence-subgraph filtering) are
implemented; provider-calling orchestration (the actual cognee.add()/
cognify()/search()/delete_data() wiring) is stubbed with NotImplementedError,
to be filled in Milestone 2.2.

find_evidence() and reset_project() were added during the architecture
review (not in the original design doc's §2) to close two gaps found by
tracing the Milestone 1 spike's steps against the API: there was no way to
get a deterministic evidence subgraph without going through an LLM-backed
recall() call, and no way to reset a single project's memory (only forget
one source at a time). Both are additive — nothing in ingest/improve/
recall/forget changed shape.
"""

from __future__ import annotations

import time

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
from memory_core.graph.query import (
    forget_source,
    get_graph as _get_graph,
    get_stats as _get_stats,
    list_sources as _list_sources,
    reset_project as _reset_project,
)
from memory_core.ingestion.pipeline import run_ingest
from memory_core.models import (
    Evidence,
    ForgetResult,
    IngestResult,
    MemoryGraph,
    MemoryStats,
    RecallResult,
    RecallStrategy,
    RelationshipType,
    SourceInput,
    SourceRecord,
)
from memory_core.retrieval.evidence import (
    build_evidence,
    find_edges_by_relationship,
    find_evidence as _find_evidence,
    subgraph_for_edges,
)
from memory_core.retrieval.router import classify_intent

__all__ = [
    "ingest",
    "improve",
    "recall",
    "forget",
    "get_graph",
    "get_stats",
    "list_sources",
    "find_evidence",
    "reset_project",
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
    """Design §2.3.

    v1 evidence-relationship mapping is deliberately simple, not a full
    router: "contradiction" strategy looks for CONTRADICTS evidence,
    everything else looks for SUPPORTS — matching the only two query
    shapes Milestone 1 actually validated. Broaden when a real query needs
    EVALUATES/DERIVED_FROM evidence attached.
    """
    provider = get_provider()
    resolved_strategy = strategy or classify_intent(query)

    started = time.monotonic()
    try:
        result = await provider.query(query, dataset=project_id, strategy=resolved_strategy)

        degraded = not provider.capabilities().supports_deterministic_evidence
        evidence: list[Evidence] = []
        evidence_graph: MemoryGraph | None = None
        if not degraded:
            relationship = (
                RelationshipType.CONTRADICTS
                if resolved_strategy == "contradiction"
                else RelationshipType.SUPPORTS
            )
            graph = await _get_graph(project_id=project_id, provider=provider)
            evidence = build_evidence(graph, relationship)
            if evidence:
                edges = find_edges_by_relationship(graph, relationship)
                evidence_graph = subgraph_for_edges(graph, edges)
    except CapabilityUnavailableError:
        # A distinct, meaningful signal ("this provider fundamentally can't
        # do this") — preserved as-is rather than collapsed into RecallError,
        # even though it's raised from inside recall()'s own pipeline.
        raise
    except Exception as exc:
        # Everything else — a failed search() call, a failed graph fetch
        # during evidence-building, anything unexpected — is "the recall
        # pipeline itself failed," which is exactly what RecallError means
        # (design §6). Recall gets one outward failure type, deliberately,
        # unlike ingest()'s three-way split — see mode_a.py's query() for
        # why that asymmetry is intentional, not an oversight.
        raise RecallError(f"recall failed for project_id={project_id}: {exc}") from exc
    duration_ms = int((time.monotonic() - started) * 1000)

    return RecallResult(
        query=query,
        answer=result.answer,
        evidence=evidence,
        evidence_graph=evidence_graph,
        degraded=degraded,
        strategy_used=resolved_strategy,
        duration_ms=duration_ms,
        raw_llm_context=result.raw_context,
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


async def find_evidence(
    *,
    project_id: str,
    relationship: RelationshipType = RelationshipType.CONTRADICTS,
    hypothesis_id: str | None = None,
) -> list[Evidence]:
    """Added in the pre-2.2 architecture review. Deterministic, LLM-free —
    no query text, no LLM call. Defaults reproduce the Milestone 1 spike's
    find_contradiction_evidence() step exactly (unfiltered CONTRADICTS
    lookup)."""
    provider = get_provider()
    return await _find_evidence(
        project_id=project_id,
        relationship=relationship,
        hypothesis_id=hypothesis_id,
        provider=provider,
    )


async def reset_project(*, project_id: str) -> None:
    """Added in the pre-2.2 architecture review. Reproduces the Milestone 1
    spike's reset() step, but scoped to one project's dataset rather than
    the spike's global prune (see providers.base.MemoryProvider.reset_dataset)."""
    provider = get_provider()
    await _reset_project(project_id=project_id, provider=provider)
