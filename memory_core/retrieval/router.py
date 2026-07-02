"""Recall intent -> RecallStrategy selection.

Design reference: Docs/MEMORY_CORE_DESIGN.md §2.3, §3 ("retrieval/").
Mirrors ARCHITECTURE.md §6's recall router table (relationship/"why",
contradiction, gap-analysis, factual).

Simple keyword classification for v1 — no LLM call, a Tier 1 unit test
target per design §7. Not tuned beyond the demo-critical contradiction
query Milestone 1 validated; broaden as real queries surface gaps.
"""

from __future__ import annotations

from memory_core.models import RecallStrategy

_CONTRADICTION_KEYWORDS = ("contradict", "disagree", "refute", "conflict")
_GAP_KEYWORDS = ("never evaluated", "never been evaluated", "gap", "missing", "not yet")
_RELATIONSHIP_KEYWORDS = ("why", "support", "because", "evidence for")


def classify_intent(query: str) -> RecallStrategy:
    q = query.lower()
    if any(kw in q for kw in _CONTRADICTION_KEYWORDS):
        return "contradiction"
    if any(kw in q for kw in _GAP_KEYWORDS):
        return "gap_analysis"
    if any(kw in q for kw in _RELATIONSHIP_KEYWORDS):
        return "relationship"
    return "factual"
