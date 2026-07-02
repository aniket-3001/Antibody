"""Mode B — Cognee Cloud (managed backend).

Design reference: Docs/MEMORY_CORE_DESIGN.md §4.4.

Scaffolded only, per the approved design: implementing a working Cognee
Cloud backend is not required for the hackathon submission. This class
exists so the MemoryProvider Protocol contract is real and type-checkable,
and so selecting Mode B is a one-line config.py change, not a rearchitecture,
whenever this is actually implemented.

The capabilities() values below are what was verified against Cognee 1.2.2
at design time (Docs/MEMORY_CORE_DESIGN.md §4.1) — re-check them against
whatever Cognee Cloud SDK is current before implementing this class for
real; they are a snapshot, not a permanent specification.
"""

from __future__ import annotations

from memory_core.providers.base import (
    OntologyBundle,
    ProviderCapabilities,
    ProviderDataItem,
    ProviderDeleteReceipt,
    ProviderIngestReceipt,
    ProviderQueryResult,
    RawGraph,
    RecallStrategy,
)


class ModeBProvider:
    """Implements MemoryProvider against a Cognee Cloud tenant. Not implemented."""

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_deterministic_evidence=False,
            supports_ontology_resolver=False,
            supports_hard_delete=False,
        )

    async def ingest_source(
        self,
        text: str,
        *,
        dataset: str,
        node_set: list[str],
        ontology: OntologyBundle,
        custom_prompt: str,
    ) -> ProviderIngestReceipt:
        raise NotImplementedError("Mode B is not implemented — Docs/MEMORY_CORE_DESIGN.md §4.4")

    async def query(
        self,
        query_text: str,
        *,
        dataset: str,
        strategy: RecallStrategy,
    ) -> ProviderQueryResult:
        raise NotImplementedError("Mode B is not implemented — Docs/MEMORY_CORE_DESIGN.md §4.4")

    async def fetch_graph(self, *, dataset: str) -> RawGraph | None:
        return None  # honest per capabilities(); never fabricate an empty graph elsewhere

    async def list_data(self, *, dataset: str) -> list[ProviderDataItem]:
        raise NotImplementedError("Mode B is not implemented — Docs/MEMORY_CORE_DESIGN.md §4.4")

    async def delete_source(
        self,
        *,
        dataset: str,
        data_id: str,
        hard: bool,
    ) -> ProviderDeleteReceipt:
        raise NotImplementedError("Mode B is not implemented — Docs/MEMORY_CORE_DESIGN.md §4.4")

    async def reset_dataset(self, *, dataset: str) -> None:
        raise NotImplementedError("Mode B is not implemented — Docs/MEMORY_CORE_DESIGN.md §4.4")
