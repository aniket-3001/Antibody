"""Deterministic evidence-subgraph extraction.

Design reference: Docs/MEMORY_CORE_DESIGN.md §1.1, §3 ("retrieval/").

Generalizes Milestone 1's validated find_contradiction_evidence()
(prototype/memory_core_spike/main.py) from a hardcoded CONTRADICTS-only
traversal to any relationship type. Pure graph traversal, no LLM and no
provider calls — the trust property design §1.1 names as the reason
structural claims are never asserted by an LLM.
"""

from __future__ import annotations

from memory_core.models import Evidence, MemoryEdge, MemoryGraph, RelationshipType


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
    """Resolve full Evidence objects (with Hypothesis/SourceRecord attached).

    Not implemented yet — requires cross-referencing Hypothesis and
    SourceRecord lookups beyond a pure graph filter (Milestone 2.2, as
    part of recall() orchestration).
    """
    raise NotImplementedError("Milestone 2.2: resolve Hypothesis/SourceRecord for each edge")
