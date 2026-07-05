"""Confidence fusion — the strength-based comparison (spec §6, §7).

Noisy-OR evidence fusion over five independent signals. Two properties at once:
  • one strong signal is enough (a known-bad URL alone → high confidence);
  • many weak signals corroborate (semantic + structural + several independent
    reporters → also high confidence).

    Confidence = 1 − Π_i (1 − w_i · S_i)

Why noisy-OR and not a weighted average: an average dilutes one decisive signal
(a known-bad wallet) among weak ones. Noisy-OR treats each as independent
evidence — which is what these signals actually are — and stays explainable:
"94% because the domain is known-bad AND 5 people reported it."

Then the ASYMMETRIC gate (spec §7): the CONFIRMED "do not engage" verdict needs
a HARD signal (indicator or strong structural), never semantic-only, so a legit
bank fraud text can never be hard-accused. When unsure we caution and educate.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# Per-signal weights (importance of each channel of evidence)
WEIGHTS = {
    "indicator": 0.98,   # a known-bad IOC is nearly decisive
    "semantic": 0.75,
    "structural": 0.72,
    "corroboration": 0.70,
    "family": 0.55,      # prior/recency, weakest on its own
}


@dataclass
class Signals:
    indicator: float = 0.0     # S_ind — best indicator match strength
    semantic: float = 0.0      # S_sem — rescaled best semantic similarity
    structural: float = 0.0    # S_struct — fraction of family signature matched
    corroboration: float = 0.0 # S_corr — 1 − exp(−k · trust_weighted_reporters)
    family: float = 0.0        # S_fam — prevalence × recency prior
    # provenance for the explanation / UI badges
    detail: dict = field(default_factory=dict)


def corroboration_strength(trust_weighted_reporters: float, k: float = 0.4) -> float:
    """S_corr = 1 − exp(−k·n) over trust-weighted distinct reporters (spec §6/§9)."""
    return 1.0 - math.exp(-k * max(0.0, trust_weighted_reporters))


def family_prior(report_count: int, days_since_last: float | None) -> float:
    """S_fam = prevalence × recency. A dormant campaign shouldn't fire at full
    strength on a lookalike (spec §6 recency prior, fed by memify decay §9)."""
    prevalence = 1.0 - math.exp(-0.15 * max(0, report_count))
    # Fresh sightings fire near full strength; a dormant campaign decays on a
    # ~30-day half-life. Unknown recency gets a neutral 0.6.
    recency = 0.6 if days_since_last is None else 0.5 ** (days_since_last / 30.0)
    return prevalence * max(0.15, recency)


def fuse(sig: Signals) -> float:
    """Weighted noisy-OR over the five signals."""
    prod = 1.0
    for name, weight in WEIGHTS.items():
        s = max(0.0, min(1.0, getattr(sig, name)))
        prod *= (1.0 - weight * s)
    return 1.0 - prod


# Band thresholds (overridable from settings)
CONFIRMED = 0.85
LIKELY = 0.60
SUSPICIOUS = 0.35


@dataclass
class Verdict:
    band: str            # confirmed | likely | suspicious | unrecognized
    confidence: float
    signals: Signals
    reasons: list[str]


def decide(
    sig: Signals,
    *,
    confirmed_th: float = CONFIRMED,
    likely_th: float = LIKELY,
    suspicious_th: float = SUSPICIOUS,
    min_corroboration_reporters: float = 3.0,
) -> Verdict:
    """Fuse, then apply the asymmetric gate.

    CONFIRMED requires (confidence ≥ th) AND a hard signal AND that a single
    low-trust report alone can't reach it (corroboration floor, spec §9).
    Semantic-only evidence is capped at SUSPICIOUS — caution, never accuse.
    """
    conf = fuse(sig)
    has_hard = sig.indicator >= 0.9 or sig.structural >= 0.7
    reasons: list[str] = []

    if sig.indicator >= 0.9:
        reasons.append(sig.detail.get("indicator_reason", "matched a known-bad indicator"))
    if sig.semantic >= 0.5:
        reasons.append(sig.detail.get("semantic_reason", "closely matches prior reports by meaning"))
    if sig.structural >= 0.4:
        reasons.append(sig.detail.get("structural_reason", "shares this family's signature tactics"))
    if sig.corroboration >= 0.4:
        reasons.append(sig.detail.get("corroboration_reason", "independently reported by multiple people"))

    corr_reporters = sig.detail.get("reporter_weight", 0.0)

    # Asymmetric gate
    if conf >= confirmed_th and has_hard and (
        sig.indicator >= 0.9 or corr_reporters >= min_corroboration_reporters
    ):
        band = "confirmed"
    elif conf >= likely_th:
        band = "likely"
    elif conf >= suspicious_th:
        band = "suspicious"
    else:
        band = "unrecognized"

    # Safety cap: semantic-only (no hard signal) never hard-accuses
    if band == "confirmed" and not has_hard:
        band = "likely"

    if not reasons:
        reasons.append("no strong match to any known scam family")

    return Verdict(band=band, confidence=round(conf, 4), signals=sig, reasons=reasons)
