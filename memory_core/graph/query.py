"""Deterministic, LLM-free graph reads + shared normalization helpers.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.5, §3 ("graph/").

The normalization helpers below are ported from Milestone 1's validated
spike (prototype/memory_core_spike/main.py's normalize_node/normalize_edge/
node_label/node_type/norm_rel) — already exercised against real Cognee
output shapes, per design §7's Tier 1 testing plan.

Known v1 limitation: Cognee's stored data items don't currently expose a
recoverable `source_type` (paper/experiment/research_note/text) or a
human-readable `title` distinct from an internal hash-based name. This
module reads back what Cognee actually stores; it does not invent data.
`SourceRecord.source_type` defaults to "text" and `title` falls back to
Cognee's internal name when nothing better is available — documented here,
not silently faked.
"""

from __future__ import annotations

from typing import Any

from memory_core.errors import CapabilityUnavailableError
from memory_core.models import (
    EntityType,
    ForgetResult,
    MemoryEdge,
    MemoryGraph,
    MemoryNode,
    MemoryStats,
    RelationshipType,
    SourceRecord,
)
from memory_core.providers.base import MemoryProvider

_RELATIONSHIP_ALIASES = {
    "CONTRADICT": "CONTRADICTS",
    "CONTRADICTED_BY": "CONTRADICTS",
    "REFUTES": "CONTRADICTS",
    "DISAGREES_WITH": "CONTRADICTS",
    "SUPPORT": "SUPPORTS",
    "SUPPORTED_BY": "SUPPORTS",
    "CORROBORATES": "SUPPORTS",
    "USE": "USES",
    "AUTHORED_BY": "WRITTEN_BY",
    "WRITTEN": "WRITTEN_BY",
    "CITES": "REFERENCES",
    "REFERENCE": "REFERENCES",
    "EVALUATE": "EVALUATES",
    "DERIVES_FROM": "DERIVED_FROM",
}

_RELATIONSHIP_NAMES = {r.value for r in RelationshipType}


def normalize_relationship(raw: str) -> RelationshipType | str:
    """Map an extracted relationship label onto the closed vocabulary, or
    pass it through unchanged if it's genuinely off-vocabulary (e.g.
    Cognee's own scaffolding edges like BELONGS_TO_SET/CONTAINS/IS_A —
    see design §5.1 for why these are preserved, not dropped)."""
    r = (raw or "").strip().upper().replace(" ", "_").replace("-", "_")
    if r in _RELATIONSHIP_NAMES:
        return RelationshipType(r)
    if r in _RELATIONSHIP_ALIASES:
        return RelationshipType(_RELATIONSHIP_ALIASES[r])
    for canon in _RELATIONSHIP_NAMES:
        if canon.rstrip("S") in r:
            return RelationshipType(canon)
    return r


def node_label(attributes: dict[str, Any]) -> str:
    for key in ("name", "text", "title", "id"):
        if attributes.get(key):
            return str(attributes[key])[:120]
    return str(attributes)[:120]


def node_type(attributes: dict[str, Any]) -> EntityType | str:
    for key in ("type", "node_type", "label", "__type__"):
        raw = attributes.get(key)
        if raw:
            try:
                return EntityType(str(raw))
            except ValueError:
                return str(raw)
    return "unknown"


def _as_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {"value": obj}


def _normalize_raw_node(raw: Any) -> MemoryNode:
    if isinstance(raw, tuple) and len(raw) == 2:
        nid, props = raw
        d = _as_dict(props)
        d.setdefault("id", nid)
    else:
        d = _as_dict(raw)
    node_id = str(d.get("id", ""))
    raw_node_set = d.get("node_set")
    source_ids = [str(x) for x in raw_node_set] if isinstance(raw_node_set, (list, tuple)) else []
    return MemoryNode(
        id=node_id, type=node_type(d), label=node_label(d), attributes=d, source_ids=source_ids
    )


def _normalize_raw_edge(raw: Any) -> MemoryEdge:
    if isinstance(raw, tuple) and len(raw) >= 3:
        src, tgt, rel = raw[0], raw[1], raw[2]
        props = _as_dict(raw[3]) if len(raw) > 3 else {}
    else:
        d = _as_dict(raw)
        src = d.get("source_node_id", d.get("source", ""))
        tgt = d.get("target_node_id", d.get("target", ""))
        rel = d.get("relationship_name", d.get("relationship", d.get("label", "")))
        props = d
    return MemoryEdge(
        source_id=str(src),
        target_id=str(tgt),
        relationship=normalize_relationship(str(rel)),
        attributes=props,
    )


async def get_graph(*, project_id: str, provider: MemoryProvider) -> MemoryGraph:
    if not provider.capabilities().supports_deterministic_evidence:
        raise CapabilityUnavailableError(
            "Active provider cannot produce a local graph — see design §4.5"
        )
    raw = await provider.fetch_graph(dataset=project_id)
    if raw is None:
        raise CapabilityUnavailableError(
            "Active provider returned no graph despite claiming the capability"
        )
    return MemoryGraph(
        nodes=[_normalize_raw_node(n) for n in raw.nodes],
        edges=[_normalize_raw_edge(e) for e in raw.edges],
    )


async def get_stats(*, project_id: str, provider: MemoryProvider) -> MemoryStats:
    items = await provider.list_data(dataset=project_id)
    last_ingest_at = max((i.ingested_at for i in items), default=None)
    # source_type isn't recoverable from Cognee's stored data (see module
    # docstring) — reported as a single bucket rather than faked per-type.
    source_counts = {"total": len(items)}

    entity_counts = None
    active_hypotheses = 0
    if provider.capabilities().supports_deterministic_evidence:
        graph = await get_graph(project_id=project_id, provider=provider)
        entity_counts = {}
        for n in graph.nodes:
            if isinstance(n.type, EntityType):
                entity_counts[n.type] = entity_counts.get(n.type, 0) + 1
        active_hypotheses = sum(
            1
            for n in graph.nodes
            if n.type == EntityType.HYPOTHESIS
            and str(n.attributes.get("status", "active")).lower() == "active"
        )

    return MemoryStats(
        project_id=project_id,
        source_counts=source_counts,
        entity_counts=entity_counts,
        active_hypotheses=active_hypotheses,
        last_ingest_at=last_ingest_at,
    )


async def list_sources(*, project_id: str, provider: MemoryProvider) -> list[SourceRecord]:
    items = await provider.list_data(dataset=project_id)
    return [
        SourceRecord(
            id=item.data_id,
            project_id=project_id,
            source_type="text",  # best-effort — see module docstring
            title=item.title or str(item.raw.get("name", item.data_id)),
            ingested_at=item.ingested_at,
            node_set=item.node_set,
            raw_metadata=item.raw,
        )
        for item in items
    ]


async def forget_source(
    source_id: str, *, project_id: str, hard: bool, provider: MemoryProvider
) -> ForgetResult:
    """forget() orchestration — design §2.4.

    Placed here (not a dedicated forget.py, which the design doc's §3 tree
    doesn't name) because it needs the same source_id -> data_id resolution
    via provider.list_data() that list_sources() already owns.
    """
    items = await provider.list_data(dataset=project_id)
    match = next((i for i in items if i.node_set == source_id), None)
    if match is None:
        return ForgetResult(source_id=source_id, deleted=False, already_absent=True, orphans_pruned=0)

    receipt = await provider.delete_source(dataset=project_id, data_id=match.data_id, hard=hard)
    return ForgetResult(
        source_id=source_id,
        deleted=receipt.deleted,
        already_absent=receipt.already_absent,
        orphans_pruned=receipt.orphans_pruned,
    )


async def reset_project(*, project_id: str, provider: MemoryProvider) -> None:
    """Wipe one project's memory. Added in the pre-2.2 architecture review —
    the Milestone 1 spike's reset() step had no public-API equivalent.

    Deliberately scoped to one project's dataset (provider.reset_dataset()),
    not a global wipe — an intentional improvement over the spike, which
    used cognee.prune.prune_data()/prune_system(), both global with no
    dataset argument. See design §11 for the verification.
    """
    await provider.reset_dataset(dataset=project_id)
