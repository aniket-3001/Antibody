"""Adapter Protocol.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3 ("ingestion/adapters/"), §9.

Every new source type (PDF, URL, GitHub, Slack, transcripts, ...) is a new
module implementing this Protocol — the entire integration cost for
anything reducible to text, per design §9.
"""

from __future__ import annotations

from typing import Any, Protocol

from memory_core.models import SourceInput


class Adapter(Protocol):
    """raw SourceInput -> (plain text, enriched metadata)."""

    def load(self, source: SourceInput) -> tuple[str, dict[str, Any]]: ...
