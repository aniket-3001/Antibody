"""The MemoryProvider interface — the execution-mode boundary.

Design reference: Docs/MEMORY_CORE_DESIGN.md §4.

This is the only seam in memory_core that is allowed to know about Cognee
specifics. `ModeAProvider` (mode_a.py) and `ModeBProvider` (mode_b.py)
implement this Protocol; nothing outside `providers/` (plus config.py,
which only *selects* a provider) may import `cognee` directly — see
design §3's "Module responsibilities" for why that boundary is structural,
not a convention.

The raw provider-level types below (ProviderIngestReceipt, RawGraph, etc.)
are intentionally not the same as memory_core's public models
(models.py) — they are the unnormalized shapes a provider hands back;
graph/query.py and retrieval/evidence.py normalize them into
MemoryNode/MemoryEdge/MemoryGraph. Keeping the two separate is what lets
Mode A and Mode B return differently-shaped raw data without the public
models ever needing to change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from memory_core.models import RecallStrategy


@dataclass
class OntologyBundle:
    """The ontology contract passed to ingest_source(). See design §3 (ontology/)."""

    entity_types: list[str]
    relationship_types: list[str]
    owl_path: str | None = None


@dataclass
class ProviderCapabilities:
    """What the active provider can currently do.

    Values are a snapshot to re-verify per SDK version at implementation
    time, not a permanent specification — see design §4.1 and §4.4 for why
    this is phrased as "current," not "forever."
    """

    supports_deterministic_evidence: bool
    supports_ontology_resolver: bool
    supports_hard_delete: bool


@dataclass
class ProviderIngestReceipt:
    data_id: str
    nodes_created: int
    edges_created: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class ProviderQueryResult:
    answer: str
    raw_context: str | None = None


@dataclass
class RawGraph:
    """Unnormalized graph payload straight from the provider. Normalized by graph/query.py."""

    nodes: list[Any]
    edges: list[Any]


@dataclass
class ProviderDataItem:
    data_id: str
    node_set: str
    title: str | None
    ingested_at: datetime
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderDeleteReceipt:
    deleted: bool
    already_absent: bool
    orphans_pruned: int = 0


class MemoryProvider(Protocol):
    """Design §4.2. Implemented by ModeAProvider and ModeBProvider."""

    def capabilities(self) -> ProviderCapabilities: ...

    async def ingest_source(
        self,
        text: str,
        *,
        dataset: str,
        node_set: list[str],
        ontology: OntologyBundle,
        custom_prompt: str,
        title: str | None = None,
    ) -> ProviderIngestReceipt: ...

    async def query(
        self,
        query_text: str,
        *,
        dataset: str,
        strategy: RecallStrategy,
    ) -> ProviderQueryResult: ...

    async def synthesize_answer(self, query_text: str, raw_context: str) -> str:
        """Synthesize a natural language answer from raw_context (optional, if query() didn't do it)."""
        ...

    async def fetch_graph(self, *, dataset: str) -> RawGraph | None:
        """None if this provider cannot produce a local graph (see capabilities())."""
        ...

    async def list_data(self, *, dataset: str) -> list[ProviderDataItem]: ...

    async def delete_source(
        self,
        *,
        dataset: str,
        data_id: str,
        hard: bool,
    ) -> ProviderDeleteReceipt: ...

    async def reset_dataset(self, *, dataset: str) -> None:
        """Wipe one project's dataset only — added in the pre-2.2 architecture
        review. Must be dataset-scoped (e.g. cognee.datasets.empty_dataset()),
        never a global wipe (e.g. cognee.prune.prune_data(), which takes no
        dataset argument and clears every project — confirmed by signature
        inspection, and what the Milestone 1 spike used, more destructively
        than it needed to)."""
        ...
