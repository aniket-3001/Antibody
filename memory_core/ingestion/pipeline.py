"""ingest()/improve() orchestration.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.1, §2.2, §3.

One internal function backs both public wrappers (memory_core.ingest and
memory_core.improve) — see design §10.2 for why two names share one
implementation.
"""

from __future__ import annotations

import hashlib
import pathlib
import time

from memory_core.errors import MemoryCoreError, ProviderError
from memory_core.models import EntityType, IngestResult, RelationshipType, SourceInput
from memory_core.ontology.prompts import build_custom_prompt
from memory_core.providers.base import MemoryProvider, OntologyBundle

_OWL_PATH = str(pathlib.Path(__file__).resolve().parents[1] / "ontology" / "research_ontology.owl")
_ENTITY_TYPES = [e.value for e in EntityType]
_RELATIONSHIP_TYPES = [r.value for r in RelationshipType]


def compute_source_id(project_id: str, source: SourceInput, normalized_text: str) -> str:
    """Deterministic content-hash identity for a source.

    Design §2.1: `hash(project_id, source.source_type, normalized(content))`.
    Same content -> same id -> ingest()/improve() short-circuit as a
    duplicate, never a second cognify() call. Different content -> a new
    id, even if it's an edited version of a previously-ingested source
    (design §10.7's named open question, not solved here).
    """
    digest_input = f"{project_id}:{source.source_type}:{normalized_text}".encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()[:32]


async def run_ingest(
    source: SourceInput,
    *,
    project_id: str,
    active_hypotheses: list[str] | None,
    provider: MemoryProvider,
) -> IngestResult:
    """Shared orchestration: adapter dispatch -> dedup check -> provider.ingest_source()."""
    from memory_core.ingestion.adapters import ADAPTERS

    adapter = ADAPTERS[source.source_type]
    text, _metadata = adapter.load(source)

    source_id = compute_source_id(project_id, source, text)

    existing = await provider.list_data(dataset=project_id)
    if any(item.node_set == source_id for item in existing):
        return IngestResult(
            source_id=source_id,
            project_id=project_id,
            status="skipped_duplicate",
            nodes_created=0,
            edges_created=0,
            duration_ms=0,
            warnings=[],
        )

    ontology = OntologyBundle(
        entity_types=_ENTITY_TYPES,
        relationship_types=_RELATIONSHIP_TYPES,
        owl_path=_OWL_PATH,
    )
    custom_prompt = build_custom_prompt(_ENTITY_TYPES, _RELATIONSHIP_TYPES, active_hypotheses)

    started = time.monotonic()
    try:
        receipt = await provider.ingest_source(
            text,
            dataset=project_id,
            node_set=[source_id],
            ontology=ontology,
            custom_prompt=custom_prompt,
            title=source.title,
        )
    except MemoryCoreError:
        # The provider (mode_a.py) already typed this correctly —
        # ExtractionError for a cognify() fault, OntologyError for a bad
        # OWL file, ProviderError for everything else. Re-raise as-is;
        # re-wrapping here would collapse that distinction right back into
        # one generic type, which is the exact bug this fix closes.
        raise
    except Exception as exc:
        # Defense in depth only: something the provider itself failed to
        # type (a bug in the provider, not an expected Cognee failure mode).
        raise ProviderError(f"ingest failed for source_id={source_id}: {exc}") from exc
    duration_ms = int((time.monotonic() - started) * 1000)

    status = "created" if (receipt.nodes_created or receipt.edges_created) else "degraded"
    warnings = list(receipt.warnings)
    if status == "degraded":
        warnings.append("cognify() completed but produced no new nodes/edges for this source")

    return IngestResult(
        source_id=source_id,
        project_id=project_id,
        status=status,
        nodes_created=receipt.nodes_created,
        edges_created=receipt.edges_created,
        duration_ms=duration_ms,
        warnings=warnings,
    )
