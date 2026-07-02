"""Plain text adapter.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3. Validated pattern: this is
exactly how Milestone 1's spike fed fixtures to cognee.add() — no special
parsing, just decoded text plus whatever metadata the caller attached.
"""

from __future__ import annotations

from typing import Any

from memory_core.models import SourceInput


def load(source: SourceInput) -> tuple[str, dict[str, Any]]:
    content = source.content
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    metadata = {**source.metadata, "title": source.title}
    return text, metadata
