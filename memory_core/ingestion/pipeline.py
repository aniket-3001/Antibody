"""ingest()/improve() orchestration.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.1, §2.2, §3.

One internal function backs both public wrappers (memory_core.ingest and
memory_core.improve) — see design §10.2 for why two names share one
implementation.
"""

from __future__ import annotations

import hashlib

from memory_core.models import IngestResult, SourceInput
from memory_core.providers.base import MemoryProvider


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
    """Shared orchestration: adapter dispatch -> dedup check -> provider.ingest_source().

    Not implemented yet (Milestone 2.1 is skeleton only). Milestone 2.2
    wires: adapter lookup via ingestion.adapters.ADAPTERS[source.source_type],
    compute_source_id() + a provider.list_data() dedup check, ontology
    bundle construction, ontology.prompts.build_custom_prompt(), and
    provider.ingest_source() — mapping ProviderIngestReceipt /
    provider-level exceptions into IngestResult / the errors.py hierarchy
    per design §2.1's error-handling spec.
    """
    raise NotImplementedError("Milestone 2.2: wire adapter dispatch + provider.ingest_source()")
