"""Mode A — local Cognee pipeline + direct LLM/embedding provider.

Design reference: Docs/MEMORY_CORE_DESIGN.md §4.3.

Not implemented yet (Milestone 2.1 is skeleton only). When implemented,
this wraps exactly the pattern Milestone 1's spike validated:
cognee.add(node_set=[...]), cognee.cognify(config={"ontology_config":
{"ontology_resolver": ...}}, custom_prompt=...),
get_graph_engine().get_graph_data(),
cognee.search(SearchType.GRAPH_COMPLETION, ...),
cognee.datasets.delete_data(...). All capabilities are True.
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


class ModeAProvider:
    """Implements MemoryProvider against a local Cognee instance."""

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_deterministic_evidence=True,
            supports_ontology_resolver=True,
            supports_hard_delete=True,
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
        raise NotImplementedError("Milestone 2.2: wire cognee.add() + cognee.cognify()")

    async def query(
        self,
        query_text: str,
        *,
        dataset: str,
        strategy: RecallStrategy,
    ) -> ProviderQueryResult:
        raise NotImplementedError("Milestone 2.2: wire cognee.search(SearchType.GRAPH_COMPLETION)")

    async def fetch_graph(self, *, dataset: str) -> RawGraph | None:
        raise NotImplementedError("Milestone 2.2: wire get_graph_engine().get_graph_data()")

    async def list_data(self, *, dataset: str) -> list[ProviderDataItem]:
        raise NotImplementedError("Milestone 2.2: wire cognee.datasets.list_data()")

    async def delete_source(
        self,
        *,
        dataset: str,
        data_id: str,
        hard: bool,
    ) -> ProviderDeleteReceipt:
        raise NotImplementedError("Milestone 2.2: wire cognee.datasets.delete_data()")

    async def reset_dataset(self, *, dataset: str) -> None:
        raise NotImplementedError("Milestone 2.2: wire cognee.datasets.empty_dataset() (dataset-scoped)")
