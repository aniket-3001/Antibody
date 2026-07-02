"""PDF adapter — stub.

Design reference: Docs/MEMORY_CORE_DESIGN.md §3, §9. Not needed until a
real (non-synthetic-fixture) corpus is ingested; PyMuPDF is the chosen
library (ARCHITECTURE.md §9).
"""

from __future__ import annotations

from typing import Any

from memory_core.models import SourceInput


def load(source: SourceInput) -> tuple[str, dict[str, Any]]:
    raise NotImplementedError("PDF adapter is stubbed — Docs/MEMORY_CORE_DESIGN.md §9")
