"""URL adapter — stub.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3, §9. Fetching is the
backend's job (design §1.2); this adapter receives already-fetched
HTML/text, not a URL to fetch itself.
"""

from __future__ import annotations

from typing import Any

from memory_core.models import SourceInput


def load(source: SourceInput) -> tuple[str, dict[str, Any]]:
    raise NotImplementedError("URL adapter is stubbed — Docs/MEMORY_CORE_DESIGN.md §9")
