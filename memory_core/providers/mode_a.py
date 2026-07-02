"""Mode A — local Cognee pipeline + direct LLM/embedding provider.

Design reference: Docs/MEMORY_CORE_DESIGN.md §4.3.

Wraps exactly the pattern Milestone 1's spike validated: cognee.add() +
cognee.cognify() with the OWL ontology resolver and a custom_prompt,
get_graph_engine().get_graph_data() for graph reads,
cognee.search(SearchType.GRAPH_COMPLETION) for recall,
cognee.datasets.delete_data()/empty_dataset() for forget/reset.

Known v1 limitation, stated plainly rather than silently assumed: Cognee's
get_graph_engine().get_graph_data() has no dataset-scoping parameter this
review could find. The Milestone 1 spike worked around this by isolating
an entire storage root (data_root_directory/system_root_directory) per
run — i.e. one project per process. Mode A v1 inherits that exact same
assumption: this provider is correct for a single project per configured
storage root, not yet verified for multiple concurrent projects sharing
one local Cognee installation. True multi-project isolation is future
work, not a Milestone 2.2 claim.
"""

from __future__ import annotations

import json
import pathlib
import uuid

from dotenv import load_dotenv

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

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")

import cognee  # noqa: E402  (import after dotenv so config picks up env)
from cognee import SearchType  # noqa: E402
from cognee.infrastructure.databases.exceptions.exceptions import (  # noqa: E402
    DatabaseNotCreatedError,
)
from cognee.infrastructure.databases.graph import get_graph_engine  # noqa: E402
from cognee.modules.ontology.rdf_xml.RDFLibOntologyResolver import (  # noqa: E402
    RDFLibOntologyResolver,
)

_DATA_DIR = _REPO_ROOT / ".cognee_data"
_SYSTEM_DIR = _REPO_ROOT / ".cognee_system"
_DATA_DIR.mkdir(exist_ok=True)
_SYSTEM_DIR.mkdir(exist_ok=True)
cognee.config.data_root_directory(str(_DATA_DIR))
cognee.config.system_root_directory(str(_SYSTEM_DIR))

# All Cognee search types map through GRAPH_COMPLETION today. gap_analysis
# is specified in ARCHITECTURE.md §6 as a candidate for a dedicated CYPHER
# traversal, deferred until a query actually needs it — not implemented
# speculatively.
_STRATEGY_TO_SEARCH_TYPE: dict[RecallStrategy, SearchType] = {
    "relationship": SearchType.GRAPH_COMPLETION,
    "contradiction": SearchType.GRAPH_COMPLETION,
    "gap_analysis": SearchType.GRAPH_COMPLETION,
    "factual": SearchType.GRAPH_COMPLETION,
}


def _extract_search_text(results) -> str:
    return "\n".join(str(getattr(r, "search_result", r)) for r in results)


class ModeAProvider:
    """Implements MemoryProvider against a local Cognee instance."""

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_deterministic_evidence=True,
            supports_ontology_resolver=True,
            supports_hard_delete=True,
        )

    async def _resolve_dataset_id(self, dataset: str) -> uuid.UUID | None:
        try:
            datasets = await cognee.datasets.list_datasets()
        except DatabaseNotCreatedError:
            # cognee.add() bootstraps the relational schema on first use;
            # nothing has been ingested into this storage root yet, so
            # "no dataset found" is the correct answer, not an error.
            return None
        for d in datasets:
            if d.name == dataset:
                return d.id
        return None

    async def ingest_source(
        self,
        text: str,
        *,
        dataset: str,
        node_set: list[str],
        ontology: OntologyBundle,
        custom_prompt: str,
    ) -> ProviderIngestReceipt:
        before = await self.fetch_graph(dataset=dataset)
        before_nodes = len(before.nodes) if before else 0
        before_edges = len(before.edges) if before else 0

        await cognee.add(text, dataset_name=dataset, node_set=node_set)

        cognify_kwargs: dict = {"datasets": dataset}
        if custom_prompt:
            cognify_kwargs["custom_prompt"] = custom_prompt
        if ontology.owl_path:
            resolver = RDFLibOntologyResolver(ontology_file=ontology.owl_path)
            cognify_kwargs["config"] = {"ontology_config": {"ontology_resolver": resolver}}
        await cognee.cognify(**cognify_kwargs)

        after = await self.fetch_graph(dataset=dataset)
        after_nodes = len(after.nodes) if after else 0
        after_edges = len(after.edges) if after else 0

        dataset_id = await self._resolve_dataset_id(dataset)
        data_id = ""
        if dataset_id is not None:
            items = await cognee.datasets.list_data(dataset_id)
            matches = [i for i in items if json.loads(i.node_set or "[]") == node_set]
            if matches:
                data_id = str(max(matches, key=lambda i: i.created_at).id)

        return ProviderIngestReceipt(
            data_id=data_id,
            nodes_created=max(0, after_nodes - before_nodes),
            edges_created=max(0, after_edges - before_edges),
        )

    async def query(
        self,
        query_text: str,
        *,
        dataset: str,
        strategy: RecallStrategy,
    ) -> ProviderQueryResult:
        search_type = _STRATEGY_TO_SEARCH_TYPE[strategy]
        answers = await cognee.search(
            query_text=query_text, query_type=search_type, datasets=dataset
        )
        context = await cognee.search(
            query_text=query_text,
            query_type=search_type,
            datasets=dataset,
            only_context=True,
        )
        return ProviderQueryResult(
            answer=_extract_search_text(answers),
            raw_context=_extract_search_text(context),
        )

    async def fetch_graph(self, *, dataset: str) -> RawGraph | None:
        eng = await get_graph_engine()
        nodes, edges = await eng.get_graph_data()
        return RawGraph(nodes=nodes, edges=edges)

    async def list_data(self, *, dataset: str) -> list[ProviderDataItem]:
        dataset_id = await self._resolve_dataset_id(dataset)
        if dataset_id is None:
            return []
        items = await cognee.datasets.list_data(dataset_id)
        return [
            ProviderDataItem(
                data_id=str(item.id),
                node_set=(json.loads(item.node_set)[0] if item.node_set else item.name),
                title=None,
                ingested_at=item.created_at,
                raw={"name": item.name},
            )
            for item in items
        ]

    async def delete_source(
        self,
        *,
        dataset: str,
        data_id: str,
        hard: bool,
    ) -> ProviderDeleteReceipt:
        dataset_id = await self._resolve_dataset_id(dataset)
        if dataset_id is None:
            return ProviderDeleteReceipt(deleted=False, already_absent=True)

        items = await cognee.datasets.list_data(dataset_id)
        if not any(str(i.id) == data_id for i in items):
            return ProviderDeleteReceipt(deleted=False, already_absent=True)

        # `hard` is accepted for API-contract stability (design §2.4) but
        # deliberately not forwarded as mode="hard": Cognee 1.2.2's own
        # source marks that value as legacy/dangerous, and doesn't appear
        # to branch on it — graph-consistent node/edge cleanup happens
        # automatically (has_data_related_nodes check), independent of
        # this flag. Always request the sanctioned "soft" mode.
        await cognee.datasets.delete_data(
            dataset_id=dataset_id, data_id=uuid.UUID(data_id), mode="soft"
        )
        return ProviderDeleteReceipt(deleted=True, already_absent=False)

    async def reset_dataset(self, *, dataset: str) -> None:
        dataset_id = await self._resolve_dataset_id(dataset)
        if dataset_id is None:
            return  # nothing to reset — a fresh project with no dataset yet
        await cognee.datasets.empty_dataset(dataset_id)
