"""Semantic match — signal ② of the three-signal match (spec §5).

Catches the *reworded* variant that shares no exact indicator: "pay $2.99 to
reschedule delivery" vs "a small fee of £2 is required for redelivery". Keyword
search fails here; meaning-similarity is the vector half of the hybrid.

Cognee holds the real embedding index (LanceDB, fastembed). This module is a
dependency-free character/word n-gram cosine used as (a) a fast local pre-filter
and (b) a guaranteed-available fallback so the semantic signal never goes dark
if embeddings are unavailable. Cosine is mapped [0.55, 0.95] → [0, 1] per §6.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _features(text: str) -> Counter:
    low = text.lower()
    words = _TOKEN_RE.findall(low)
    feats: Counter = Counter()
    # unigrams + bigrams
    feats.update(words)
    feats.update(f"{a}_{b}" for a, b in zip(words, words[1:], strict=False))
    # char trigrams on the collapsed string (robust to spacing/rewording)
    collapsed = " ".join(words)
    feats.update(collapsed[i : i + 3] for i in range(max(0, len(collapsed) - 2)))
    return feats


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def rescale(cosine: float, lo: float = 0.35, hi: float = 0.85) -> float:
    """Map a raw cosine band to [0,1] strength (spec §6)."""
    if cosine <= lo:
        return 0.0
    if cosine >= hi:
        return 1.0
    return (cosine - lo) / (hi - lo)


class SemanticIndex:
    """In-memory index of prior report texts → nearest family by meaning.

    Legit control messages are indexed too (is_control=True). If an incoming
    message looks more like a known-legit control than any scam family, we say
    so — this is the asymmetric gate (spec §7) working through the control set:
    a real bank/shipping text is recognized as legit, never hard-accused.
    """

    def __init__(self) -> None:
        # (report_id, family, is_control, features)
        self._items: list[tuple[str, str, bool, Counter]] = []

    def add(self, report_id: str, family: str | None, text: str,
            is_control: bool = False) -> None:
        self._items.append((report_id, family or "", is_control, _features(text)))

    def clear(self) -> None:
        self._items = []

    def best(self, text: str, top_k: int = 5) -> list[dict]:
        q = _features(text)
        scored: list[dict[str, Any]] = [
            {"report_id": rid, "family": fam or None, "is_control": ctrl,
             "cosine": _cosine(q, feats)}
            for rid, fam, ctrl, feats in self._items
        ]
        scored.sort(key=lambda s: s["cosine"], reverse=True)
        return scored[:top_k]

    def best_family(self, text: str, legit_floor: float = 0.5) -> dict:
        """Return {family, cosine, strength, looks_legit} for the strongest match.

        family is None (and looks_legit True) when the message resembles a known
        legit control at least as much as any scam family.
        """
        hits = self.best(text, top_k=15)
        best_family_cos = 0.0
        best_family = None
        best_control_cos = 0.0
        for h in hits:
            if h["is_control"]:
                best_control_cos = max(best_control_cos, h["cosine"])
            elif h["family"] and h["cosine"] > best_family_cos:
                best_family_cos, best_family = h["cosine"], h["family"]

        if best_control_cos >= legit_floor and best_control_cos >= best_family_cos:
            return {"family": None, "cosine": best_control_cos, "strength": 0.0,
                    "looks_legit": True}
        if best_family is None:
            return {"family": None, "cosine": 0.0, "strength": 0.0, "looks_legit": False}
        return {"family": best_family, "cosine": best_family_cos,
                "strength": rescale(best_family_cos), "looks_legit": False}


# process-wide index, rebuilt from the ops store at startup / after seeding
semantic_index = SemanticIndex()
