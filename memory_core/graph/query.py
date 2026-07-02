"""Deterministic, LLM-free graph reads + shared normalization helpers.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.5, §3 ("graph/").

The normalization helpers below are ported from Milestone 1's validated
spike (prototype/memory_core_spike/main.py's normalize_node/normalize_edge/
node_label/node_type/norm_rel) — already exercised against real Cognee
output shapes, per design §7's Tier 1 testing plan. get_graph()/
get_stats()/list_sources() are not implemented yet.
"""

from __future__ import annotations

from typing import Any

from memory_core.errors import CapabilityUnavailableError
from memory_core.models import EntityType, ForgetResult, MemoryEdge, MemoryGraph, MemoryNode, MemoryStats, RelationshipType, SourceRecord
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


async def get_graph(*, project_id: str, provider: MemoryProvider) -> MemoryGraph:
    if not provider.capabilities().supports_deterministic_evidence:
        raise CapabilityUnavailableError(
            "Active provider cannot produce a local graph — see design §4.5"
        )
    raise NotImplementedError("Milestone 2.2: wire provider.fetch_graph() + normalization")


async def get_stats(*, project_id: str, provider: MemoryProvider) -> MemoryStats:
    raise NotImplementedError("Milestone 2.2: wire provider.list_data()/fetch_graph()")


async def list_sources(*, project_id: str, provider: MemoryProvider) -> list[SourceRecord]:
    raise NotImplementedError("Milestone 2.2: wire provider.list_data()")


async def forget_source(
    source_id: str, *, project_id: str, hard: bool, provider: MemoryProvider
) -> ForgetResult:
    """forget() orchestration — design §2.4.

    Placed here (not a dedicated forget.py, which the design doc's §3 tree
    doesn't name) because it needs the same source_id -> data_id resolution
    via provider.list_data() that list_sources() already owns.
    """
    raise NotImplementedError("Milestone 2.2: wire list_data() lookup + provider.delete_source()")


async def reset_project(*, project_id: str, provider: MemoryProvider) -> None:
    """Wipe one project's memory. Added in the pre-2.2 architecture review —
    the Milestone 1 spike's reset() step had no public-API equivalent.

    Deliberately scoped to one project's dataset (provider.reset_dataset()),
    not a global wipe — an intentional improvement over the spike, which
    used cognee.prune.prune_data()/prune_system(), both global with no
    dataset argument. See design review notes for the verification.
    """
    raise NotImplementedError("Milestone 2.2: wire provider.reset_dataset()")
