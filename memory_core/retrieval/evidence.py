"""Deterministic evidence-subgraph extraction.

Design reference: Docs/MEMORY_CORE_DESIGN.md §1.1, §3 ("retrieval/").

Generalizes Milestone 1's validated find_contradiction_evidence()
(prototype/memory_core_spike/main.py) from a hardcoded CONTRADICTS-only
traversal to any relationship type. Pure graph traversal, no LLM and no
provider calls — the trust property design §1.1 names as the reason
structural claims are never asserted by an LLM.
"""

from __future__ import annotations

from memory_core.graph.query import get_graph
from memory_core.models import Evidence, Hypothesis, MemoryEdge, MemoryGraph, RelationshipType
from memory_core.providers.base import MemoryProvider


def find_edges_by_relationship(
    graph: MemoryGraph, relationship: RelationshipType
) -> list[MemoryEdge]:
    """Pure filter — the deterministic core of the spike's validated traversal."""
    return [e for e in graph.edges if e.relationship == relationship]


def subgraph_for_edges(graph: MemoryGraph, edges: list[MemoryEdge]) -> MemoryGraph:
    """The minimal node/edge set touched by `edges` — the "evidence subgraph"
    Milestone 1 produced (3 nodes / 2 edges for the CONTRADICTS case)."""
    node_ids = {e.source_id for e in edges} | {e.target_id for e in edges}
    by_id = {n.id: n for n in graph.nodes}
    return MemoryGraph(
        nodes=[by_id[nid] for nid in node_ids if nid in by_id],
        edges=list(edges),
    )


def build_evidence(graph: MemoryGraph, relationship: RelationshipType) -> list[Evidence]:
    """Resolve Evidence objects for every edge of `relationship` type.

    `source: SourceRecord | None` is always None here — resolving the full
    anchored SourceRecord (project_id, ingested_at, node_set) needs a
    provider round-trip (list_data()), which would break this function's
    pure/no-provider-calls contract (design §1.1's determinism guarantee).
    Callers that need it can cross-reference `evidence_node.source_ids`
    against list_sources() themselves.
    """
    edges = find_edges_by_relationship(graph, relationship)
    by_id = {n.id: n for n in graph.nodes}
    evidence: list[Evidence] = []
    for e in edges:
        evidence_node = by_id.get(e.source_id)
        hypothesis_node = by_id.get(e.target_id)
        if evidence_node is None or hypothesis_node is None:
            continue
        status = str(hypothesis_node.attributes.get("status", "active")).lower()
        hypothesis = Hypothesis(
            id=hypothesis_node.id,
            statement=hypothesis_node.label,
            status="retired" if status == "retired" else "active",
        )
        evidence.append(
            Evidence(
                evidence_node=evidence_node,
                hypothesis=hypothesis,
                relationship=relationship,
                source=None,
            )
        )
    return evidence


async def find_evidence(
    *,
    project_id: str,
    relationship: RelationshipType = RelationshipType.CONTRADICTS,
    hypothesis_id: str | None = None,
    provider: MemoryProvider,
) -> list[Evidence]:
    """Deterministic, LLM-free evidence lookup — added in the pre-2.2
    architecture review to close a real gap: recall() always requires a
    query and always calls the LLM, but the Milestone 1 spike's
    find_contradiction_evidence() step (and design §1.1's own trust
    principle) needs a path with neither. Defaults match the spike's exact
    behavior: an unfiltered CONTRADICTS lookup across the whole project.

    Depends on graph.query.get_graph() (design's established dependency
    direction: retrieval depends on graph, never the reverse) plus
    build_evidence() above. Not implemented until both of those are.
    """
    graph = await get_graph(project_id=project_id, provider=provider)
    evidence = build_evidence(graph, relationship)
    if hypothesis_id is not None:
        evidence = [e for e in evidence if e.hypothesis.id == hypothesis_id]
    return evidence
