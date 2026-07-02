"""Markdown adapter.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3. Validated in Milestone 1:
the spike's fixture corpus (prototype/memory_core_spike/fixtures/*.md) was
fed to cognee.add() as decoded UTF-8 text with no markdown-specific
parsing — Cognee's own chunking handles markdown structure. This adapter
formalizes that pattern; identical to text.load() today by design, kept as
a distinct module (not an alias) because markdown-specific normalization
(e.g. stripping front-matter) is a plausible near-term addition that
should not require touching text.py.
"""

from __future__ import annotations

from typing import Any

from memory_core.models import SourceInput


def load(source: SourceInput) -> tuple[str, dict[str, Any]]:
    content = source.content
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    metadata = {**source.metadata, "title": source.title}
    return text, metadata
