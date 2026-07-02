"""Adapter dispatch table.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3, §9. ingestion/pipeline.py
dispatches on SourceInput.source_type through this table — adding a new
source type is adding one entry plus one module, per design §9.
"""

from __future__ import annotations

from memory_core.ingestion.adapters import markdown, pdf, text, url

ADAPTERS = {
    "paper": markdown,
    "experiment": markdown,
    "research_note": markdown,
    "markdown": markdown,
    "text": text,
    "pdf": pdf,
    "url": url,
}

__all__ = ["ADAPTERS"]
