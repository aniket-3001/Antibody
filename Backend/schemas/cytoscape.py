"""Cytoscape.js serialiser.

Spec reference: BACKEND_API_SPEC.md §6 — converts a memory_core MemoryGraph
into the flat elements array that Cytoscape.js expects.

This module is presentation logic only — no memory_core writes, no business
logic.  It is the single place responsible for the node/edge format, class
naming, and evidence highlighting conventions.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on path so memory_core is importable from here.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from memory_core.models import EntityType, MemoryGraph, RelationshipType


def _type_slug(raw: str) -> str:
    """Convert entity type string to CSS class slug.

    "Paper"        → "paper"
    "ResearchNote" → "research-note"
    """
    import re
    # Insert hyphen before each uppercase letter that follows a lowercase
    slug = re.sub(r"(?<=[a-z])(?=[A-Z])", "-", raw)
    return slug.lower().replace("_", "-").replace(" ", "-")


def _rel_slug(raw: str) -> str:
    """WRITTEN_BY → written-by"""
    return raw.lower().replace("_", "-")


def to_cytoscape(
    graph: MemoryGraph,
    evidence_node_ids: set[str] | None = None,
) -> dict:
    """Serialise a MemoryGraph to the Cytoscape.js elements format.

    Parameters
    ----------
    graph:
        The MemoryGraph to serialise (full graph or evidence subgraph).
    evidence_node_ids:
        Node IDs that should receive the additional "evidence-node" CSS class
        (spec §6.4).  Pass ``{n.id for n in evidence_graph.nodes}`` from the
        recall service.

    Returns
    -------
    dict with keys:
        elements  — flat list of Cytoscape node/edge dicts
        node_count
        edge_count
    """
    evidence_node_ids = evidence_node_ids or set()
    elements: list[dict] = []

    for node in graph.nodes:
        type_str = node.type.value if isinstance(node.type, EntityType) else str(node.type)
        slug = _type_slug(type_str)
        classes = f"entity-{slug}"
        if node.id in evidence_node_ids:
            classes += " evidence-node"

        elements.append(
            {
                "data": {
                    "id": f"node-{node.id}",
                    "label": node.label,
                    "type": type_str,
                    "source_ids": node.source_ids,
                    "attributes": node.attributes,
                },
                "classes": classes,
            }
        )

    for i, edge in enumerate(graph.edges):
        rel = (
            edge.relationship.value
            if isinstance(edge.relationship, RelationshipType)
            else str(edge.relationship)
        )
        elements.append(
            {
                "data": {
                    "id": f"edge-{i}",
                    "source": f"node-{edge.source_id}",
                    "target": f"node-{edge.target_id}",
                    "label": rel,
                    "relationship": rel,
                },
                "classes": f"rel-{_rel_slug(rel)}",
            }
        )

    return {
        "elements": elements,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
    }
