"""Recall intent -> RecallStrategy selection.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.3, §3 ("retrieval/").
Mirrors ARCHITECTURE.md §6's recall router table (relationship/"why",
contradiction, gap-analysis, factual).
"""

from __future__ import annotations

from memory_core.models import RecallStrategy


def classify_intent(query: str) -> RecallStrategy:
    """Not implemented yet (Milestone 2.2).

    ARCHITECTURE.md §6 specifies the target mapping: contradiction-shaped
    queries -> "contradiction", structural/gap queries -> "gap_analysis",
    "why"/relationship queries -> "relationship", everything else ->
    "factual". A Tier 1 unit test target per design §7 once implemented.
    """
    raise NotImplementedError("Milestone 2.2: implement intent classification per ARCHITECTURE.md §6")
